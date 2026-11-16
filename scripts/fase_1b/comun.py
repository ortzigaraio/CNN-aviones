"""Constantes compartidas por los guiones de la Fase 1b (docs/specs/fase-1b.md, anexo)."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "data" / "fase-1b"
ORTOFOTO = DATOS / "ortofoto"
HUELLAS = DATOS / "fotogramas_huellas.geojson"
MOSAICO = DATOS / "mosaico.tif"
MOSAICO_ZONAS = DATOS / "mosaico_fotogramas.geojson"
LISTA_FOTOGRAMAS = Path(__file__).with_name("fotogramas_28jul2023.csv")

URL_BASE = (
    "http://ftpcdd.cnig.es/Vuelos_2023/Vuelos_2023/madrid_2023/01.VF/"
    "01.08_PNOA_2023_MAD_22cm_VF_img8c_rgb_hu30/"
)
CRS = "EPSG:25830"  # ETRS89 / UTM 30N, el de los fotogramas

# Recinto del aeropuerto de Madrid-Barajas, rectángulo en EPSG:25830 (metros):
# (este mínimo, norte mínimo, este máximo, norte máximo).
# Se ha elegido generoso, a partir del punto de referencia (ARP, config/aerodromos.yaml:
# 40,472222 N, -3,560833 E -> 452.459 E, 4.480.322 N) y de lo que se ve en los
# fotogramas 006-1459 y 006-1460. La justificación de cada lado está en
# docs/specs/fase-1b-dudas.md («Recinto del aeropuerto»).
RECINTO = (448_700.0, 4_477_300.0, 456_000.0, 4_488_000.0)

GSD_MOSAICO = 0.25  # metros por píxel del mosaico (anexo, punto 1)
