"""Huellas de los fotogramas del 28/07/2023, subconjunto mínimo y descarga.

1. Lee solo la cabecera de cada fotograma de fotogramas_28jul2023.csv con una petición
   HTTP parcial (cabecera Range, primeros 16 KB): tamaño en píxeles y transformación
   afín (etiqueta TIFF 34264). Guarda las huellas en data/fase-1b/fotogramas_huellas.geojson.
2. Busca el subconjunto más pequeño de fotogramas tal que, tomando cada punto del
   recinto (comun.RECINTO) del fotograma del subconjunto cuyo centro está más cerca,
   ese fotograma contenga el punto. Lo marca en el GeoJSON (seleccionado = true).
3. Con --descargar, baja a data/fase-1b/ortofoto/ los seleccionados que falten y
   comprueba el tamaño contra la lista. Se para si el total supera --max-gb.

Uso (desde la raíz del repo):
    uv run --group geo python scripts/fase_1b/fotogramas.py            # 1 y 2
    uv run --group geo python scripts/fase_1b/fotogramas.py --descargar
"""

import argparse
import csv
import hashlib
import json
import struct
import sys
import time
import urllib.request

import numpy as np
from comun import CRS, HUELLAS, LISTA_FOTOGRAMAS, ORTOFOTO, RECINTO, URL_BASE

PAUSA_S = 3  # entre peticiones: el servidor del CNIG es HTTP y a veces corta
PASO_MALLA_M = 20  # separación de los puntos con que se comprueba la cobertura


def leer_lista() -> dict[str, int]:
    with open(LISTA_FOTOGRAMAS, newline="") as f:
        return {fila["fichero"]: int(fila["bytes"]) for fila in csv.DictReader(f)}


def _pedir(url: str, rango: str | None = None, intentos: int = 4) -> bytes:
    for intento in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"Range": rango} if rango else {})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except OSError as e:
            if intento == intentos - 1:
                raise
            print(f"  fallo ({e}); reintento en {10 * (intento + 1)} s", file=sys.stderr)
            time.sleep(10 * (intento + 1))
    raise AssertionError("inalcanzable")


def leer_cabecera_tiff(datos: bytes) -> tuple[int, int, list[float]]:
    """Ancho, alto y transformación afín (a, b, c, d, e, f) de la primera IFD de un
    TIFF clásico: x = a·col + b·fila + c; y = d·col + e·fila + f."""
    orden = {b"II": "<", b"MM": ">"}[datos[:2]]
    if struct.unpack(orden + "H", datos[2:4])[0] != 42:
        raise ValueError("No es un TIFF clásico (¿BigTIFF?).")
    ifd = struct.unpack(orden + "I", datos[4:8])[0]
    n = struct.unpack(orden + "H", datos[ifd : ifd + 2])[0]
    etiquetas = {}
    for i in range(n):
        etiqueta, tipo, cuenta, valor = struct.unpack(
            orden + "HHII", datos[ifd + 2 + 12 * i : ifd + 14 + 12 * i]
        )
        etiquetas[etiqueta] = (tipo, cuenta, valor, ifd + 2 + 12 * i + 8)

    def entero(etiqueta):
        tipo, _, _, pos = etiquetas[etiqueta]
        return struct.unpack(
            orden + ("H" if tipo == 3 else "I"), datos[pos : pos + (2 if tipo == 3 else 4)]
        )[0]

    def dobles(etiqueta):
        tipo, cuenta, desplazamiento, _ = etiquetas[etiqueta]
        assert tipo == 12  # DOUBLE
        if desplazamiento + 8 * cuenta > len(datos):
            raise ValueError("La etiqueta queda fuera de los bytes leídos.")
        return struct.unpack(
            orden + "d" * cuenta, datos[desplazamiento : desplazamiento + 8 * cuenta]
        )

    ancho, alto = entero(256), entero(257)
    if 34264 in etiquetas:  # ModelTransformationTag, matriz 4x4 por filas
        m = dobles(34264)
        afin = [m[0], m[1], m[3], m[4], m[5], m[7]]
    else:  # ModelPixelScale + ModelTiepoint, sin giro
        sx, sy, _ = dobles(33550)
        _, _, _, x0, y0, _ = dobles(33922)
        afin = [sx, 0.0, x0, 0.0, -sy, y0]
    return ancho, alto, afin


def esquinas(ancho: int, alto: int, afin: list[float]) -> list[tuple[float, float]]:
    a, b, c, d, e, f = afin
    return [
        (a * x + b * y + c, d * x + e * y + f)
        for x, y in ((0, 0), (ancho, 0), (ancho, alto), (0, alto))
    ]


def obtener_huellas(lista: dict[str, int]) -> dict:
    """Lee (o reutiliza de HUELLAS) la huella de cada fotograma."""
    previas = {}
    if HUELLAS.exists():
        previas = {
            ft["properties"]["fichero"]: ft for ft in json.loads(HUELLAS.read_text())["features"]
        }
    rasgos = []
    for i, fichero in enumerate(lista):
        if fichero in previas:
            rasgos.append(previas[fichero])
            continue
        if i:
            time.sleep(PAUSA_S)
        datos = _pedir(URL_BASE + fichero, "bytes=0-16383")
        ancho, alto, afin = leer_cabecera_tiff(datos)
        cs = esquinas(ancho, alto, afin)
        centro = (
            afin[0] * ancho / 2 + afin[1] * alto / 2 + afin[2],
            afin[3] * ancho / 2 + afin[4] * alto / 2 + afin[5],
        )
        print(f"{fichero}: {ancho} x {alto}, centro {centro[0]:.0f} E {centro[1]:.0f} N")
        rasgos.append(
            {
                "type": "Feature",
                "properties": {
                    "fichero": fichero,
                    "bytes": lista[fichero],
                    "ancho_px": ancho,
                    "alto_px": alto,
                    "afin": afin,
                    "centro": centro,
                    "seleccionado": False,
                },
                "geometry": {"type": "Polygon", "coordinates": [[*map(list, cs), list(cs[0])]]},
            }
        )
    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": CRS}},
        "features": rasgos,
    }


def contiene(props: dict, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """¿Cae cada punto (x, y) dentro del fotograma? Invierte su transformación afín."""
    a, b, c, d, e, f = props["afin"]
    det = a * e - b * d
    col = (e * (x - c) - b * (y - f)) / det
    fila = (-d * (x - c) + a * (y - f)) / det
    return (col >= 0) & (col < props["ancho_px"]) & (fila >= 0) & (fila < props["alto_px"])


def malla_recinto() -> tuple[np.ndarray, np.ndarray]:
    x0, y0, x1, y1 = RECINTO
    xs = np.arange(x0, x1 + 1e-6, PASO_MALLA_M)
    ys = np.arange(y0, y1 + 1e-6, PASO_MALLA_M)
    x, y = np.meshgrid(xs, ys)
    return x.ravel(), y.ravel()


def seleccionar(rasgos: list[dict]) -> list[int]:
    """Índices del subconjunto mínimo, por búsqueda exacta en profundidad creciente.

    Un punto está «mal» si el fotograma de centro más cercano del subconjunto no lo
    contiene (o el subconjunto está vacío). Cualquier subconjunto válido que amplíe el
    actual tiene que incluir un fotograma que contenga ese punto y cuyo centro esté más
    cerca que el más cercano actual (si no, el más cercano seguiría siendo el mismo).
    Se ramifica solo sobre esos fotogramas, eligiendo el punto mal cubierto con menos
    opciones. Con profundidad máxima k creciente, la primera solución es mínima (sobre
    la malla de puntos cada PASO_MALLA_M metros)."""
    x, y = malla_recinto()
    props = [r["properties"] for r in rasgos]
    dentro = np.array([contiene(p, x, y) for p in props])
    if not dentro.any(axis=0).all():
        raise SystemExit("Ni con todos los fotogramas se cubre el recinto: revisa RECINTO.")
    centros = np.array([p["centro"] for p in props])
    d2 = (x[None, :] - centros[:, 0:1]) ** 2 + (y[None, :] - centros[:, 1:2]) ** 2
    opciones = dentro.sum(axis=0)
    print(
        f"{int(dentro.any(axis=1).sum())} fotogramas tocan el recinto; "
        f"malla de {len(x)} puntos cada {PASO_MALLA_M} m"
    )

    vistos: set[frozenset] = set()

    def buscar(elegidos: list[int], dist: np.ndarray, cerca: np.ndarray, k: int):
        clave = frozenset(elegidos)
        if clave in vistos:
            return None
        vistos.add(clave)
        mal = ~dentro[cerca, np.arange(len(x))] if elegidos else np.ones(len(x), bool)
        if not mal.any():
            return elegidos
        if len(elegidos) == k:
            return None
        p = np.flatnonzero(mal)[np.argmin(opciones[mal])]
        validos = [g for g in range(len(props)) if dentro[g, p] and d2[g, p] < dist[p]]
        for g in sorted(validos, key=lambda g: d2[g, p]):
            mejor = d2[g] < dist
            r = buscar([*elegidos, g], np.where(mejor, d2[g], dist), np.where(mejor, g, cerca), k)
            if r is not None:
                return r
        return None

    inicio = (np.full(len(x), np.inf), np.zeros(len(x), int))
    for k in range(1, len(props) + 1):
        vistos.clear()
        r = buscar([], *inicio, k)
        print(f"  k = {k}: {'solución' if r else 'sin solución'} ({len(vistos)} nodos)")
        if r is not None:
            return sorted(r)
    raise AssertionError("inalcanzable")


def descargar(fichero: str, esperado: int) -> dict:
    destino = ORTOFOTO / fichero
    parcial = destino.with_suffix(".part")
    url = URL_BASE + fichero
    for intento in range(5):
        hecho = parcial.stat().st_size if parcial.exists() else 0
        req = urllib.request.Request(url, headers={"Range": f"bytes={hecho}-"} if hecho else {})
        try:
            with (
                urllib.request.urlopen(req, timeout=120) as r,
                open(parcial, "ab" if hecho else "wb") as f,
            ):
                if hecho and r.status != 206:
                    raise OSError("el servidor no admite reanudar")
                cabeceras = {
                    "etag": r.headers.get("ETag"),
                    "last_modified": r.headers.get("Last-Modified"),
                }
                while bloque := r.read(1 << 20):
                    f.write(bloque)
            break
        except OSError as e:
            print(f"  corte ({e}); reanudo en {15 * (intento + 1)} s", file=sys.stderr)
            time.sleep(15 * (intento + 1))
    else:
        raise SystemExit(f"No se pudo bajar {fichero}.")
    tam = parcial.stat().st_size
    if tam != esperado:
        raise SystemExit(f"{fichero}: {tam} bytes, se esperaban {esperado}. Se deja en {parcial}.")
    parcial.rename(destino)
    return {"fichero": fichero, "bytes": tam, **cabeceras}


def sha256(ruta) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while bloque := f.read(1 << 22):
            h.update(bloque)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--descargar", action="store_true", help="baja los seleccionados que falten")
    p.add_argument("--max-gb", type=float, default=3.0, help="se para si hay que bajar más")
    args = p.parse_args()

    lista = leer_lista()
    huellas = obtener_huellas(lista)
    elegidos = seleccionar(huellas["features"])
    for i, rasgo in enumerate(huellas["features"]):
        rasgo["properties"]["seleccionado"] = i in elegidos
    HUELLAS.parent.mkdir(parents=True, exist_ok=True)
    HUELLAS.write_text(json.dumps(huellas, ensure_ascii=False, indent=1))

    nombres = [huellas["features"][i]["properties"]["fichero"] for i in elegidos]
    faltan = [n for n in nombres if not (ORTOFOTO / n).exists()]
    total = sum(lista[n] for n in faltan)
    print("Seleccionados:", *nombres, sep="\n  ")
    print(f"Faltan {len(faltan)}: {total / 1e9:.2f} GB")
    for n in nombres:
        if (ORTOFOTO / n).exists() and (ORTOFOTO / n).stat().st_size != lista[n]:
            raise SystemExit(f"{n} ya existe pero su tamaño no coincide con la lista.")
    if not args.descargar or not faltan:
        return
    if total > args.max_gb * 1e9:
        raise SystemExit(
            f"Hay que bajar {total / 1e9:.2f} GB, más que --max-gb={args.max_gb}. No se baja nada."
        )

    registro_ruta = ORTOFOTO / "descargas.json"
    registro = json.loads(registro_ruta.read_text()) if registro_ruta.exists() else []
    for i, n in enumerate(faltan):
        if i:
            time.sleep(PAUSA_S * 3)
        print(f"Bajando {n} ({lista[n] / 1e6:.1f} MB)")
        fila = descargar(n, lista[n])
        fila["sha256"] = sha256(ORTOFOTO / n)
        registro.append(fila)
        registro_ruta.write_text(json.dumps(registro, ensure_ascii=False, indent=1))
    print("Hecho.")


if __name__ == "__main__":
    main()
