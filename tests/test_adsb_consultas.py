"""Tests de `avion_osint.adsb.consultas` con un almacén de juguete en tmp_path, sin red."""

from datetime import date, timedelta

import pandas as pd
import pytest
from almacen_juguete import crear_almacen, t

from avion_osint.adsb import consultas
from avion_osint.limites import FechaDemasiadoRecienteError


@pytest.fixture
def almacen(tmp_path):
    return crear_almacen(tmp_path / "adsb")


# ---------------------------------------------------------------- movimientos


def test_movimientos_de_un_dia_ordenados(almacen):
    tabla = consultas.movimientos("LEMD", t("2023-03-06 00:00"), t("2023-03-07 00:00"), almacen)
    assert list(tabla.columns) == list(consultas.TIPOS_MOVIMIENTOS)
    assert list(tabla["icao24"]) == ["aaa001", "aaa002", "aaa001"]
    assert list(tabla["tipo_movimiento"]) == ["llegada", "llegada", "salida"]
    assert tabla["instante"].iloc[0] == pd.Timestamp("2023-03-06 08:00", tz="UTC")
    assert set(tabla["fuente"]) == {"adsblol"}


def test_movimientos_intervalo_semiabierto(almacen):
    # inicio entra, fin no.
    tabla = consultas.movimientos("LEMD", t("2023-03-06 08:00"), t("2023-03-06 18:00"), almacen)
    assert list(tabla["instante"].dt.hour) == [8, 9]


def test_movimientos_no_mezcla_aerodromos(almacen):
    tabla = consultas.movimientos("LEZG", t("2023-03-01 00:00"), t("2023-03-31 00:00"), almacen)
    assert set(tabla["icao24"]) == {"aaa004", "aaa005"}


def test_movimientos_sin_ficheros_da_tabla_vacia_con_columnas(tmp_path):
    tabla = consultas.movimientos("LEPA", t("2023-03-06 00:00"), t("2023-03-07 00:00"), tmp_path)
    assert tabla.empty
    assert list(tabla.columns) == list(consultas.TIPOS_MOVIMIENTOS)


def test_movimientos_rechaza_aerodromo_fuera_de_la_configuracion(almacen):
    with pytest.raises(ValueError, match="XXXX"):
        consultas.movimientos("XXXX", t("2023-03-06 00:00"), t("2023-03-07 00:00"), almacen)


def test_movimientos_rechaza_fecha_reciente(almacen):
    fin = pd.Timestamp.now(tz="UTC").to_pydatetime()
    with pytest.raises(FechaDemasiadoRecienteError):
        consultas.movimientos("LEMD", fin - timedelta(days=1), fin, almacen)


def test_movimientos_exige_zona_horaria(almacen):
    with pytest.raises(ValueError, match="zona horaria"):
        consultas.movimientos(
            "LEMD", t("2023-03-06 00:00").replace(tzinfo=None), t("2023-03-07 00:00"), almacen
        )


# ---------------------------------------------------------------- en_tierra


def test_en_tierra_usa_las_llegadas_y_salidas_del_almacen(almacen):
    tabla = consultas.en_tierra("LEMD", t("2023-03-06 12:00"), t("2023-03-06 13:00"), almacen)
    filas = {fila.icao24: fila for fila in tabla.itertuples()}
    # aaa001: llegada 08:00 y salida 18:00 vistas → fuerte.
    assert filas["aaa001"].verdad == "fuerte"
    # aaa002: llegada el 6 y salida el 13, a 7 días; con la ventana de ± 7 días se ve.
    assert filas["aaa002"].verdad == "fuerte"
    # aaa003: solo su salida del día 7 → estancia sin llegada → débil (D18).
    assert filas["aaa003"].verdad == "debil"


# ---------------------------------------------------------------- resumen


def test_resumen_por_dia(almacen):
    tabla = consultas.resumen("LEMD", date(2023, 3, 6), date(2023, 3, 13), "dia", almacen)
    assert list(tabla.columns) == consultas.COLUMNAS_RESUMEN
    assert list(tabla["periodo"]) == [
        date(2023, 3, 6),
        date(2023, 3, 7),
        date(2023, 3, 8),
        date(2023, 3, 13),
    ]
    lunes = tabla.iloc[0]
    assert (lunes.n_llegadas, lunes.n_salidas, lunes.n_aviones) == (2, 1, 2)
    assert lunes.desequilibrio == pytest.approx(1 / 3)
    assert lunes.n_puntos_tierra == 120
    assert lunes.fuente == "adsblol"
    # Día descargado sin movimientos: cuenta como día con datos, con ceros.
    sin_vuelos = tabla.iloc[2]
    assert (sin_vuelos.dias_con_datos, sin_vuelos.n_llegadas, sin_vuelos.n_salidas) == (1, 0, 0)
    assert pd.isna(sin_vuelos.desequilibrio)
    assert sin_vuelos.fuente == "adsblol"
    assert pd.isna(tabla.iloc[1].n_puntos_tierra)


def test_resumen_por_semana(almacen):
    tabla = consultas.resumen("LEMD", date(2023, 3, 6), date(2023, 3, 19), "semana", almacen)
    assert list(tabla["periodo"]) == [date(2023, 3, 6), date(2023, 3, 13)]
    semana = tabla.iloc[0]
    assert semana.dias_con_datos == 3
    assert (semana.n_llegadas, semana.n_salidas) == (2, 2)
    assert semana.n_aviones == 3  # aaa001, aaa002, aaa003: distintos en la semana
    assert semana.desequilibrio == 0
    assert semana.n_puntos_tierra == 135  # 120 + 15; el día sin dato no suma


def test_resumen_sin_datos_da_tabla_vacia(almacen):
    tabla = consultas.resumen("LEPA", date(2023, 3, 6), date(2023, 3, 13), "dia", almacen)
    assert tabla.empty
    assert list(tabla.columns) == consultas.COLUMNAS_RESUMEN


def test_resumen_rechaza_por_desconocido_y_fecha_reciente(almacen):
    with pytest.raises(ValueError, match="mes"):
        consultas.resumen("LEMD", date(2023, 3, 6), date(2023, 3, 13), "mes", almacen)
    hoy = date.today()
    with pytest.raises(FechaDemasiadoRecienteError):
        consultas.resumen("LEMD", hoy - timedelta(days=3), hoy, "dia", almacen)


# ---------------------------------------------------------------- aeronave


def test_aeronave_encontrada_sin_distinguir_mayusculas(almacen):
    fila = consultas.aeronave("AAA001", almacen)
    assert fila == {
        "icao24": "aaa001",
        "matricula": "FICT-1",
        "tipo_oaci": "A320",
        "fabricante": "Fabricante1",
        "modelo": "Modelo1",
        "operador": "Op1",
        "fecha_base": date(2023, 7, 1),
    }


def test_aeronave_no_encontrada_o_sin_base(almacen, tmp_path):
    assert consultas.aeronave("aaa999", almacen) is None
    assert consultas.aeronave("aaa001", tmp_path / "vacio") is None
