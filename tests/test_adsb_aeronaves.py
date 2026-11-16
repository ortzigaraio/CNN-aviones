"""Tests de `avion_osint.adsb.aeronaves` con una muestra del CSV de OpenSky.

`tests/datos/aeronaves-opensky-formato-muestra.csv`: 7 filas **ficticias** (icao24 aaa00N,
matrículas FICT-N) con la estructura real de
https://s3.opensky-network.org/data-samples/metadata/aircraft-database-complete-2023-07.csv,
vista en sus primeros 64 KB el 2026-11-16: cabecera con 15 columnas vacías, mismas
posiciones y entrecomillado, `NULL` sin comillas y un byte 0x96 (Windows-1252). No lleva
filas reales porque la licencia de la base está sin verificar y el repo es público.
"""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from avion_osint.adsb.aeronaves import cargar_aeronaves
from avion_osint.limites import FechaDemasiadoRecienteError

MUESTRA = Path(__file__).parent / "datos" / "aeronaves-opensky-formato-muestra.csv"
COLUMNAS = ["icao24", "matricula", "tipo_oaci", "fabricante", "modelo", "operador", "fecha_base"]


def _cargar(tmp_path) -> pd.DataFrame:
    filas = cargar_aeronaves(MUESTRA, date(2023, 7, 1), tmp_path)
    tabla = pd.read_parquet(tmp_path / "aeronaves.parquet")
    assert filas == len(tabla)
    return tabla


def test_convierte_la_muestra(tmp_path):
    tabla = _cargar(tmp_path)
    assert list(tabla.columns) == COLUMNAS
    assert len(tabla) == 7
    filas = tabla.set_index("icao24")
    fila = filas.loc["aaa001"]
    assert fila.matricula == "FICT-1"
    assert fila.tipo_oaci == "A320"
    assert fila.fabricante == "Fabricante A"
    assert fila.modelo == "Modelo A-1"
    assert fila.operador == "Aerolínea Ficticia"  # UTF-8 válido: se conserva
    assert fila.fecha_base == date(2023, 7, 1)
    assert pd.isna(filas.loc["aaa003"].operador)
    assert "aaa007" in filas.index  # AAA007 en el CSV: icao24 en minúsculas


def test_null_y_vacios_quedan_nulos(tmp_path):
    fila = _cargar(tmp_path).set_index("icao24").loc["aaa004"]
    assert fila.matricula == "FICT-4"
    assert fila.tipo_oaci == "BE35"
    assert pd.isna(fila.fabricante)  # NULL sin comillas en el CSV
    assert pd.isna(fila.operador)  # "" en el CSV


def test_byte_no_utf8_no_rompe_la_carga(tmp_path):
    # La fila aaa002 lleva un byte 0x96 (Windows-1252) en una columna que no se guarda.
    tabla = _cargar(tmp_path)
    assert "aaa002" in set(tabla["icao24"])


def test_repetir_la_carga_no_duplica(tmp_path):
    _cargar(tmp_path)
    assert len(_cargar(tmp_path)) == 7


def test_rechaza_csv_con_otro_numero_de_columnas(tmp_path):
    ruta = tmp_path / "otro.csv"
    ruta.write_text("icao24,registration\naaa001,FICT-1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="15"):
        cargar_aeronaves(ruta, date(2023, 7, 1), tmp_path)


def test_rechaza_fecha_base_reciente(tmp_path):
    with pytest.raises(FechaDemasiadoRecienteError):
        cargar_aeronaves(MUESTRA, date.today(), tmp_path)
