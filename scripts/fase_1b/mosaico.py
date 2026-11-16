"""Mosaico propio del recinto de Barajas (decisión D16, anexo de docs/specs/fase-1b.md).

Cada punto del recinto (comun.RECINTO) se toma del fotograma seleccionado (ver
fotogramas.py) cuyo centro está más cerca. Salidas:

* data/fase-1b/mosaico.tif: COG (GeoTIFF en teselas, con vistas reducidas internas),
  EPSG:25830, 0,25 m, RGB, compresión JPEG calidad 90.
* data/fase-1b/mosaico_fotogramas.geojson: zona que aporta cada fotograma.
* data/fase-1b/mosaico_vista.png: vista reducida (unos 2.000 px de lado) para revisar a ojo.

Se trabaja por bloques para no cargar el mosaico entero en memoria. Uso:
    uv run --group geo python scripts/fase_1b/mosaico.py
"""

import json
import time
import warnings

import numpy as np
import rasterio
import rasterio.shutil
from comun import CRS, DATOS, GSD_MOSAICO, HUELLAS, MOSAICO, MOSAICO_ZONAS, ORTOFOTO, RECINTO
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.windows import Window

BLOQUE = 2048  # píxeles de lado de cada bloque de trabajo
MARGEN_PX = 8  # margen al leer el fotograma, para que el remuestreo tenga vecinos
VISTA = DATOS / "mosaico_vista.png"
LADO_VISTA = 2000


def recortar(poligono: list[tuple[float, float]], a: float, b: float, c: float):
    """Parte del polígono convexo con a·x + b·y <= c (Sutherland-Hodgman)."""
    salida = []
    for i, p in enumerate(poligono):
        q = poligono[(i + 1) % len(poligono)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            salida.append(p)
        if fp * fq < 0:
            t = fp / (fp - fq)
            salida.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return salida


def zonas(centros: np.ndarray) -> list[list[tuple[float, float]]]:
    """Celda de centro más cercano de cada fotograma, recortada al recinto."""
    x0, y0, x1, y1 = RECINTO
    celdas = []
    for i, ci in enumerate(centros):
        pol = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for j, cj in enumerate(centros):
            if i != j:  # más cerca de ci que de cj: 2(cj - ci)·p <= |cj|² - |ci|²
                d = cj - ci
                pol = recortar(pol, 2 * d[0], 2 * d[1], cj @ cj - ci @ ci)
        celdas.append(pol)
    return celdas


def dentro_huella(props: dict, x, y):
    a, b, c, d, e, f = props["afin"]
    det = a * e - b * d
    col = (e * (x - c) - b * (y - f)) / det
    fila = (-d * (x - c) + a * (y - f)) / det
    return (col >= 0) & (col < props["ancho_px"]) & (fila >= 0) & (fila < props["alto_px"])


def main() -> None:
    inicio = time.time()
    rasgos = [
        r["properties"]
        for r in json.loads(HUELLAS.read_text())["features"]
        if r["properties"]["seleccionado"]
    ]
    if not rasgos:
        raise SystemExit("No hay fotogramas seleccionados: ejecuta antes fotogramas.py.")
    centros = np.array([r["centro"] for r in rasgos])
    for r in rasgos:
        if not (ORTOFOTO / r["fichero"]).exists():
            raise SystemExit(f"Falta {r['fichero']}: ejecuta fotogramas.py --descargar.")

    # Zonas que aporta cada fotograma; se comprueba que caen dentro de su huella.
    celdas = zonas(centros)
    salida_zonas = []
    for r, pol in zip(rasgos, celdas, strict=True):
        xs, ys = np.array(pol).T
        if not dentro_huella(r, xs, ys).all():
            raise SystemExit(f"La zona de {r['fichero']} se sale de su huella.")
        area = 0.5 * abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1)))
        salida_zonas.append(
            {
                "type": "Feature",
                "properties": {"fichero": r["fichero"], "area_km2": round(area / 1e6, 3)},
                "geometry": {"type": "Polygon", "coordinates": [[*map(list, pol), list(pol[0])]]},
            }
        )
    MOSAICO_ZONAS.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": CRS}},
                "features": salida_zonas,
            },
            ensure_ascii=False,
            indent=1,
        )
    )

    x0, y0, x1, y1 = RECINTO
    ancho, alto = round((x1 - x0) / GSD_MOSAICO), round((y1 - y0) / GSD_MOSAICO)
    destino_t = from_origin(x0, y1, GSD_MOSAICO, GSD_MOSAICO)
    print(f"Mosaico: {ancho} x {alto} px, {len(rasgos)} fotogramas")

    temporal = MOSAICO.with_name("mosaico_temporal.tif")
    perfil = {
        "driver": "GTiff",
        "width": ancho,
        "height": alto,
        "count": 3,
        "dtype": "uint8",
        "crs": CRS,
        "transform": destino_t,
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "lzw",
        "bigtiff": "yes",
        "photometric": "rgb",
    }
    fuentes = [rasterio.open(ORTOFOTO / r["fichero"]) for r in rasgos]
    huecos = 0
    with rasterio.open(temporal, "w", **perfil) as dst:
        for fila in range(0, alto, BLOQUE):
            for col in range(0, ancho, BLOQUE):
                ventana = Window(col, fila, min(BLOQUE, ancho - col), min(BLOQUE, alto - fila))
                vt = dst.window_transform(ventana)
                h, w = int(ventana.height), int(ventana.width)
                # Centros de los píxeles del bloque.
                cx = vt.c + (np.arange(w) + 0.5) * vt.a
                cy = vt.f + (np.arange(h) + 0.5) * vt.e
                gx, gy = np.meshgrid(cx, cy)
                d2 = (gx[None] - centros[:, 0, None, None]) ** 2 + (
                    gy[None] - centros[:, 1, None, None]
                ) ** 2
                etiqueta = np.argmin(d2, axis=0)
                del d2
                bloque = np.zeros((3, h, w), np.uint8)
                cubierto = np.zeros((h, w), bool)
                for g in np.unique(etiqueta):
                    src = fuentes[g]
                    # Ventana del fotograma que cubre el bloque: la transformación del
                    # fotograma lleva un giro pequeño, así que se invierte en las
                    # cuatro esquinas del bloque.
                    inv = ~src.transform
                    cs, fs = zip(
                        *(inv * (vt * (c, f)) for c, f in ((0, 0), (w, 0), (w, h), (0, h))),
                        strict=True,
                    )
                    c0 = max(int(np.floor(min(cs))) - MARGEN_PX, 0)
                    f0 = max(int(np.floor(min(fs))) - MARGEN_PX, 0)
                    c1 = min(int(np.ceil(max(cs))) + MARGEN_PX, src.width)
                    f1 = min(int(np.ceil(max(fs))) + MARGEN_PX, src.height)
                    if c1 <= c0 or f1 <= f0:
                        continue
                    vs = Window(c0, f0, c1 - c0, f1 - f0)
                    datos = src.read(window=vs)
                    rellenado = np.zeros((3, h, w), np.uint8)
                    valido = np.zeros((h, w), np.uint8)
                    reproject(
                        datos,
                        rellenado,
                        src_transform=src.window_transform(vs),
                        src_crs=src.crs,
                        dst_transform=vt,
                        dst_crs=CRS,
                        resampling=Resampling.bilinear,
                    )
                    reproject(
                        np.ones(datos.shape[1:], np.uint8),
                        valido,
                        src_transform=src.window_transform(vs),
                        src_crs=src.crs,
                        dst_transform=vt,
                        dst_crs=CRS,
                        resampling=Resampling.nearest,
                    )
                    m = (etiqueta == g) & (valido == 1)
                    bloque[:, m] = rellenado[:, m]
                    cubierto |= m
                huecos += int((~cubierto).sum())
                dst.write(bloque, window=ventana)
            print(
                f"  filas {fila}-{min(fila + BLOQUE, alto)} de {alto}"
                f" ({time.time() - inicio:.0f} s)"
            )
    for f in fuentes:
        f.close()
    print(f"Píxeles sin dato (huecos): {huecos}")

    # COG final con compresión JPEG y vistas reducidas internas.
    with rasterio.open(temporal) as src:
        rasterio.shutil.copy(
            src,
            MOSAICO,
            driver="COG",
            compress="JPEG",
            quality=90,
            blocksize=512,
            overview_resampling="average",
            bigtiff="IF_SAFER",
        )
    temporal.unlink()

    with rasterio.open(MOSAICO) as src:
        escala = LADO_VISTA / max(src.width, src.height)
        vh, vw = round(src.height * escala), round(src.width * escala)
        vista = src.read(out_shape=(3, vh, vw), resampling=Resampling.average)
        print(f"COG: {src.width} x {src.height} px, {MOSAICO.stat().st_size / 1e6:.0f} MB")
    warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)
    with rasterio.open(VISTA, "w", driver="PNG", width=vw, height=vh, count=3, dtype="uint8") as o:
        o.write(vista)
    print(f"Hecho en {time.time() - inicio:.0f} s")


if __name__ == "__main__":
    main()
