"""Detector preentrenado sobre el mosaico (paso C y punto 6 del anexo de la spec).

Pasa yolo26s-obb.pt (Ultralytics, preentrenado en DOTAv1, sin ajustar) por
data/fase-1b/mosaico.tif en teselas de 1024 px con solape del 20 %, a la resolución del
mosaico (0,25 m) y remuestreado a 0,5 m. Solo clase avión («plane»), confianza 0,25.
Las detecciones repetidas en los solapes se unen (ver unir_duplicados).

Salidas, con el polígono de la caja orientada en EPSG:25830, la confianza y la longitud
y anchura de la caja en metros:
    data/fase-1b/detecciones_nativa.geojson
    data/fase-1b/detecciones_05m.geojson

IMPORTANTE: el autor cuenta los aviones a mano sin conocer este resultado. El guion no
escribe en pantalla cuántas detecciones hay; no abras las salidas antes de contar.

Uso:
    uv run --group geo --group vision python scripts/fase_1b/detector.py
"""

import hashlib
import json
import os
import time
import urllib.request

os.environ.setdefault("YOLO_OFFLINE", "1")  # sin telemetría ni comprobaciones en línea

import numpy as np
import rasterio
from comun import CRS, DATOS, MOSAICO, RAIZ
from rasterio.enums import Resampling
from rasterio.windows import Window

URL_PESOS = (
    "https://huggingface.co/Ultralytics/YOLO26/resolve/"
    "070ac3c51435984d992ba92eb3f234daf4e4500d/yolo26s-obb.pt"
)
SHA256_PESOS = "38dbd72ef6804f9bbbea7ad20f486e6ca6e093c8cd9bc857207a846565bd6e0b"
PESOS = RAIZ / "data" / "pesos" / "yolo26s-obb.pt"

TESELA = 1024
SOLAPE = 0.20
CONFIANZA = 0.25  # fijada en la spec (paso C)
CLASE = "plane"
LOTE = 4
# Unión de duplicados de los solapes (elección de Opus, anotada en fase-1b-dudas.md):
# se descarta una caja si solapa con otra de más confianza con IoU > 0,3 o si más del
# 70 % de la más pequeña cae dentro de la otra (caja cortada por el borde de la tesela).
IOU_MAX = 0.3
CONTENIDA_MAX = 0.7
# Cajas degeneradas (casi sin área) que a veces devuelve el modelo: se descartan antes
# de unir, porque con área 0 los cocientes de arriba no están definidos.
AREA_MIN_M2 = 1.0


def sha256(ruta) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while bloque := f.read(1 << 22):
            h.update(bloque)
    return h.hexdigest()


def obtener_pesos() -> None:
    if not PESOS.exists():
        PESOS.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL_PESOS, PESOS)
    if sha256(PESOS) != SHA256_PESOS:
        raise SystemExit(f"El SHA-256 de {PESOS} no coincide con el publicado.")


def area(p: np.ndarray) -> float:
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def _cruz(u, v) -> float:
    """Componente z del producto vectorial de dos vectores del plano."""
    return float(u[0] * v[1] - u[1] * v[0])


def interseccion(p: np.ndarray, q: np.ndarray) -> float:
    """Área común de dos cuadriláteros convexos (recorte de Sutherland-Hodgman)."""
    sentido = 1.0 if _cruz(q[1] - q[0], q[2] - q[1]) > 0 else -1.0
    poligono = [tuple(v) for v in p]
    for i in range(len(q)):
        a, b = q[i], q[(i + 1) % len(q)]
        entrada, poligono = poligono, []
        if not entrada:
            break

        def dentro(v, a=a, b=b):
            return sentido * _cruz(b - a, np.asarray(v) - a) >= 0

        for j, v in enumerate(entrada):
            w = entrada[(j + 1) % len(entrada)]
            dv, dw = dentro(v), dentro(w)
            if dv:
                poligono.append(v)
            if dv != dw:
                v_, w_ = np.asarray(v), np.asarray(w)
                d1 = _cruz(b - a, v_ - a)
                d2 = _cruz(b - a, w_ - a)
                poligono.append(tuple(v_ + (w_ - v_) * d1 / (d1 - d2)))
    return area(np.array(poligono)) if len(poligono) >= 3 else 0.0


def unir_duplicados(cajas: list[np.ndarray], conf: list[float]) -> list[int]:
    """Índices que se quedan: de mayor a menor confianza, se descarta la caja que solapa
    demasiado con una ya aceptada (IOU_MAX o CONTENIDA_MAX)."""
    orden = np.argsort(conf)[::-1]
    centros = np.array([c.mean(axis=0) for c in cajas]) if cajas else np.zeros((0, 2))
    radios = np.array([np.linalg.norm(c - c.mean(axis=0), axis=1).max() for c in cajas])
    aceptadas: list[int] = []
    for i in orden:
        ai = area(cajas[i])
        repetida = False
        if aceptadas:
            k = np.array(aceptadas)
            cerca = k[np.linalg.norm(centros[k] - centros[i], axis=1) < radios[k] + radios[i]]
            for j in cerca:
                aj = area(cajas[j])
                # Con bordes casi paralelos y coincidentes el recorte puede salir
                # inestable; la intersección nunca supera el área de la menor.
                inter = min(interseccion(cajas[i], cajas[j]), ai, aj)
                if inter / (ai + aj - inter) > IOU_MAX or inter / min(ai, aj) > CONTENIDA_MAX:
                    repetida = True
                    break
        if not repetida:
            aceptadas.append(int(i))
    return aceptadas


def origenes(total: int, tesela: int, paso: int) -> list[int]:
    """Posiciones de inicio de las teselas; la última se ajusta al borde."""
    if total <= tesela:
        return [0]
    pos = list(range(0, total - tesela, paso))
    return [*pos, total - tesela]


def detectar(modelo, clase: int, factor: int) -> tuple[list, list, int]:
    """Cajas en EPSG:25830 y confianzas. factor = 1 (resolución del mosaico) o 2
    (remuestreado a la mitad: 0,5 m)."""
    lado = TESELA * factor  # píxeles del mosaico que cubre cada tesela
    paso = round(TESELA * (1 - SOLAPE)) * factor
    cajas, confs = [], []
    with rasterio.open(MOSAICO) as src:
        t = src.transform
        ventanas = [
            Window(c, f, lado, lado)
            for f in origenes(src.height, lado, paso)
            for c in origenes(src.width, lado, paso)
        ]
        for i in range(0, len(ventanas), LOTE):
            lote = ventanas[i : i + LOTE]
            imagenes = []
            for v in lote:
                rgb = src.read(
                    window=v,
                    out_shape=(3, TESELA, TESELA),
                    resampling=Resampling.average,
                    boundless=True,
                    fill_value=0,
                )
                imagenes.append(np.ascontiguousarray(rgb.transpose(1, 2, 0)[:, :, ::-1]))  # BGR
            resultados = modelo.predict(
                imagenes, imgsz=TESELA, conf=CONFIANZA, classes=[clase], verbose=False
            )
            for v, r in zip(lote, resultados, strict=True):
                if r.obb is None or len(r.obb) == 0:
                    continue
                esquinas = r.obb.xyxyxyxy.cpu().numpy()  # (n, 4, 2) en píxeles de la tesela
                for e, c in zip(esquinas, r.obb.conf.cpu().numpy(), strict=True):
                    col = v.col_off + e[:, 0] * factor
                    fila = v.row_off + e[:, 1] * factor
                    x = t.c + col * t.a + fila * t.b
                    y = t.f + col * t.d + fila * t.e
                    cajas.append(np.column_stack([x, y]))
                    confs.append(float(c))
    return cajas, confs, len(ventanas)


def guardar(ruta, cajas, confs, metadatos) -> None:
    validas = [i for i, c in enumerate(cajas) if area(c) >= AREA_MIN_M2]
    cajas, confs = [cajas[i] for i in validas], [confs[i] for i in validas]
    rasgos = []
    for i in unir_duplicados(cajas, confs):
        p = cajas[i]
        lados = [float(np.linalg.norm(p[1] - p[0])), float(np.linalg.norm(p[2] - p[1]))]
        rasgos.append(
            {
                "type": "Feature",
                "properties": {
                    "confianza": round(confs[i], 4),
                    "longitud_m": round(max(lados), 2),
                    "anchura_m": round(min(lados), 2),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[*p.round(3).tolist(), p[0].round(3).tolist()]],
                },
            }
        )
    coleccion = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": CRS}},
        "metadatos": metadatos,
        "features": rasgos,
    }
    ruta.write_text(json.dumps(coleccion, ensure_ascii=False, indent=1))


def main() -> None:
    import torch
    import ultralytics
    from ultralytics import YOLO

    obtener_pesos()
    torch.manual_seed(0)
    modelo = YOLO(str(PESOS))
    clase = next(i for i, n in modelo.names.items() if n == CLASE)
    for factor, nombre in ((1, "detecciones_nativa.geojson"), (2, "detecciones_05m.geojson")):
        inicio = time.time()
        cajas, confs, n_teselas = detectar(modelo, clase, factor)
        segundos = time.time() - inicio
        guardar(
            DATOS / nombre,
            cajas,
            confs,
            {
                "modelo": "yolo26s-obb.pt (Ultralytics/YOLO26, Hugging Face)",
                "sha256_pesos": SHA256_PESOS,
                "ultralytics": ultralytics.__version__,
                "torch": torch.__version__,
                "gsd_m": 0.25 * factor,
                "tesela_px": TESELA,
                "solape": SOLAPE,
                "confianza_min": CONFIANZA,
                "clase": CLASE,
                "union_duplicados": {
                    "iou_max": IOU_MAX,
                    "contenida_max": CONTENIDA_MAX,
                    "area_min_m2": AREA_MIN_M2,
                },
                "teselas": n_teselas,
                "segundos": round(segundos),
            },
        )
        print(f"{nombre}: {n_teselas} teselas en {segundos / 60:.1f} min")


if __name__ == "__main__":
    main()
