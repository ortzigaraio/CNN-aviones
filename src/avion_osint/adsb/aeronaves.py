"""Base de aeronaves de OpenSky (icao24 → matrícula, tipo…) convertida a `aeronaves.parquet`.

Formato comprobado con los primeros 64 KB de `aircraft-database-complete-2023-07.csv`
(muestra con filas ficticias y el mismo formato en `tests/datos/`):

* 15 columnas, todas entre comillas salvo el valor `NULL`, que va sin comillas.
* La primera fila es una cabecera con los 15 nombres **vacíos** (`""`): el fichero no
  dice qué es cada columna. Las posiciones de `POSICIONES` se han deducido del
  contenido (una columna con matrículas, otra con códigos OACI de 4 caracteres…); el operador es la
  más dudosa. Ver `docs/specs/fase-1-dudas.md`.
* No es UTF-8 limpio: hay al menos un byte de Windows-1252 (0x96, un guion). Se lee
  como UTF-8 y los bytes no válidos se sustituyen por «�».
"""

from datetime import date
from pathlib import Path

import pandas as pd

from avion_osint.adsb import RUTA_ALMACEN
from avion_osint.limites import comprobar_fecha_retrospectiva

N_COLUMNAS = 15
# Posición (desde 0) en el CSV → columna de aeronaves.parquet.
POSICIONES = {
    0: "icao24",
    1: "matricula",
    5: "tipo_oaci",
    3: "fabricante",
    4: "modelo",
    9: "operador",
}
VALORES_NULOS = {"", "NULL"}


def cargar_aeronaves(ruta_csv: Path, fecha_base: date, almacen: Path = RUTA_ALMACEN) -> int:
    """Convierte la base de aeronaves de OpenSky a `<almacen>/aeronaves.parquet`
    (columnas icao24, matricula, tipo_oaci, fabricante, modelo, operador, fecha_base).
    Devuelve las filas escritas. Sobrescribe el fichero: repetir la carga no duplica.

    icao24 se pasa a minúsculas; los textos vacíos y `NULL` quedan como nulos. Las filas
    no se filtran ni se quitan duplicados. ValueError si el CSV no tiene 15 columnas
    (otro formato, como `aircraftDatabase-AAAA-MM.csv`, no se acepta).
    """
    comprobar_fecha_retrospectiva(fecha_base)
    tabla = pd.read_csv(
        ruta_csv,
        header=0,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        encoding_errors="replace",
    )
    if tabla.shape[1] != N_COLUMNAS:
        raise ValueError(
            f"{ruta_csv} tiene {tabla.shape[1]} columnas; se esperaban {N_COLUMNAS} "
            "(formato aircraft-database-complete de OpenSky)."
        )

    aeronaves = pd.DataFrame(
        {nombre: tabla.iloc[:, posicion].str.strip() for posicion, nombre in POSICIONES.items()}
    )
    aeronaves = aeronaves.mask(aeronaves.isin(VALORES_NULOS))
    aeronaves["icao24"] = aeronaves["icao24"].str.lower()
    aeronaves["fecha_base"] = fecha_base

    almacen.mkdir(parents=True, exist_ok=True)
    aeronaves.to_parquet(almacen / "aeronaves.parquet", index=False)
    return len(aeronaves)
