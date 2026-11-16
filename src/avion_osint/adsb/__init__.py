"""Almacén local de ADS-B (Fase 1): movimientos, cobertura y base de aeronaves.

El almacén son ficheros Parquet en `data/adsb/` (esquema en `docs/specs/fase-1.md`,
sección 3). Todas las funciones que lo leen o escriben aceptan otra ruta con el
parámetro `almacen`; por defecto usan `RUTA_ALMACEN`.
"""

from pathlib import Path

RUTA_ALMACEN = Path(__file__).resolve().parents[3] / "data" / "adsb"
