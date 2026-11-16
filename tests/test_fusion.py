"""Tests de `avion_osint.fusion` con datos pequeños escritos a mano, sin red."""

import math
from datetime import UTC, date, datetime, timedelta

import pandas as pd
import pytest

from avion_osint.fusion import comparar_conteos, hora_por_sombra, inferir_en_tierra

UN_MINUTO = timedelta(minutes=1)


def _t(texto: str) -> datetime:
    """Instante UTC a partir de 'AAAA-MM-DD HH:MM'."""
    return datetime.fromisoformat(texto).replace(tzinfo=UTC)


# ---------------------------------------------------------------- hora_por_sombra


def test_sombra_al_norte_en_el_mediodia_solar_de_noviembre():
    # Sombra hacia el norte (0°) = sol al sur = mediodía solar. En el meridiano 0 el
    # mediodía solar es 12:00 UTC menos la ecuación del tiempo, que hacia el 3 de
    # noviembre tiene su máximo anual, unos +16,4 min: mediodía hacia las 11:43:35 UTC.
    hora = hora_por_sombra(40.0, 0.0, date(2023, 11, 3), 0.0)
    assert abs(hora - _t("2023-11-03 11:43:35")) < UN_MINUTO
    assert hora.tzinfo is not None and hora.utcoffset() == timedelta(0)


def test_sombra_al_norte_en_el_mediodia_solar_de_febrero_en_barajas():
    # Hacia el 11 de febrero la ecuación del tiempo tiene su mínimo, unos -14,2 min:
    # en el meridiano 0 el mediodía solar cae hacia las 12:14:13 UTC. En Barajas
    # (longitud -3,56°) el sol pasa por el sur 3,56 × 4 = 14,24 min más tarde.
    hora = hora_por_sombra(40.47, -3.56, date(2023, 2, 11), 0.0)
    esperado = _t("2023-02-11 12:14:13") + timedelta(minutes=3.56 * 4)
    assert abs(hora - esperado) < UN_MINUTO


def test_sombra_al_oeste_en_el_solsticio_de_verano():
    # Sombra al oeste (270°) = sol justo al este. Por trigonometría esférica, el sol
    # cruza el este cuando el ángulo horario H cumple cos H = tan(dec) / tan(lat).
    # El 21/06/2023 la declinación es unos 23,44° y la ecuación del tiempo unos
    # -1,8 min (mediodía solar en el meridiano 0 hacia las 12:01:48 UTC).
    lat, dec = 40.0, 23.44
    h_grados = math.degrees(math.acos(math.tan(math.radians(dec)) / math.tan(math.radians(lat))))
    esperado = _t("2023-06-21 12:01:48") - timedelta(hours=h_grados / 15)
    hora = hora_por_sombra(lat, 0.0, date(2023, 6, 21), 270.0)
    assert abs(hora - esperado) < 2 * UN_MINUTO


def test_sombras_simetricas_alrededor_del_mediodia():
    dia = date(2023, 7, 28)
    mediodia = hora_por_sombra(40.47, -3.56, dia, 0.0)
    manana = hora_por_sombra(40.47, -3.56, dia, 315.0)  # sombra al noroeste: sol al sureste
    tarde = hora_por_sombra(40.47, -3.56, dia, 45.0)  # sombra al noreste: sol al suroeste
    assert manana < mediodia < tarde
    assert abs((mediodia - manana) - (tarde - mediodia)) < UN_MINUTO


def test_acimut_360_equivale_a_0():
    dia = date(2023, 7, 28)
    a360 = hora_por_sombra(40.47, -3.56, dia, 360.0)
    a0 = hora_por_sombra(40.47, -3.56, dia, 0.0)
    assert abs(a360 - a0) < timedelta(seconds=1)


def test_sombra_al_sur_en_verano_en_latitud_media_no_tiene_solucion():
    # Con el sol siempre al sur del cénit, una sombra hacia el sur exigiría el sol al
    # norte por encima del horizonte, cosa que a 40° N en junio no pasa.
    with pytest.raises(ValueError):
        hora_por_sombra(40.0, 0.0, date(2023, 6, 21), 180.0)


def test_noche_polar_no_tiene_solucion():
    with pytest.raises(ValueError):
        hora_por_sombra(80.0, 0.0, date(2023, 12, 21), 0.0)


def test_sombra_rechaza_fecha_demasiado_reciente():
    with pytest.raises(ValueError):
        hora_por_sombra(40.0, 0.0, datetime.now(UTC).date(), 0.0)


# -------------------------------------------------------------- inferir_en_tierra

T_MIN = _t("2023-07-28 10:00")
T_MAX = _t("2023-07-28 11:00")


def _eventos(filas: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        {"icao24": [f[0] for f in filas], "instante": [_t(f[1]) for f in filas]},
        columns=["icao24", "instante"],
    )


def _por_icao(tabla: pd.DataFrame) -> dict:
    return {fila.icao24: fila for fila in tabla.itertuples(index=False)}


def test_en_tierra_casos_basicos():
    llegadas = _eventos(
        [
            ("aaa001", "2023-07-27 20:00"),  # pernocta: fuerte
            ("aaa002", "2023-07-28 09:45"),  # llega dentro del margen: débil
            ("aaa003", "2023-07-28 10:30"),  # llega dentro del intervalo: débil
            ("aaa004", "2023-07-28 06:00"),  # se va antes del intervalo: no aparece
            ("aaa005", "2023-07-28 12:00"),  # llega después: no aparece
            ("aaa007", "2023-07-26 08:00"),  # llega y no se va en la ventana: débil (D18)
        ]
    )
    salidas = _eventos(
        [
            ("aaa001", "2023-07-28 14:00"),
            ("aaa002", "2023-07-28 13:00"),
            ("aaa003", "2023-07-28 15:00"),
            ("aaa004", "2023-07-28 08:00"),
            ("aaa005", "2023-07-28 13:00"),
            ("aaa006", "2023-07-29 09:00"),  # sin llegada en la ventana: débil (D18), llegada nula
        ]
    )
    tabla = inferir_en_tierra(llegadas, salidas, T_MIN, T_MAX)
    assert list(tabla.columns) == ["icao24", "llegada", "salida", "verdad"]
    filas = _por_icao(tabla)
    assert set(filas) == {"aaa001", "aaa002", "aaa003", "aaa006", "aaa007"}
    assert filas["aaa001"].verdad == "fuerte"
    assert filas["aaa001"].llegada == _t("2023-07-27 20:00")
    assert filas["aaa001"].salida == _t("2023-07-28 14:00")
    assert filas["aaa002"].verdad == "debil"
    assert filas["aaa003"].verdad == "debil"
    assert filas["aaa006"].verdad == "debil"
    assert pd.isna(filas["aaa006"].llegada)
    assert filas["aaa007"].verdad == "debil"
    assert pd.isna(filas["aaa007"].salida)


def test_en_tierra_sin_un_extremo_observado_es_debil_aunque_cubra_todo():
    # D18: verdad fuerte exige ver la llegada y la salida. Una estancia que cubre de
    # sobra el intervalo pero a la que le falta un extremo (hueco de cobertura o fuera
    # de la ventana) queda como débil.
    llegadas = _eventos([("ggg001", "2023-07-21 08:00"), ("ggg003", "2023-07-27 20:00")])
    salidas = _eventos([("ggg002", "2023-08-04 20:00"), ("ggg003", "2023-07-29 09:00")])
    filas = _por_icao(inferir_en_tierra(llegadas, salidas, T_MIN, T_MAX))
    assert filas["ggg001"].verdad == "debil"  # sin salida observada
    assert filas["ggg002"].verdad == "debil"  # sin llegada observada
    assert filas["ggg003"].verdad == "fuerte"  # ambos extremos vistos


def test_en_tierra_el_margen_es_estricto():
    # Llega justo a t_min - 30 min y se va justo a t_max + 30 min: no es «antes» ni
    # «después» estrictos, así que queda como débil.
    llegadas = _eventos([("bbb001", "2023-07-28 09:30")])
    salidas = _eventos([("bbb001", "2023-07-28 11:30")])
    tabla = inferir_en_tierra(llegadas, salidas, T_MIN, T_MAX)
    assert tabla["verdad"].tolist() == ["debil"]
    tabla = inferir_en_tierra(llegadas, salidas, T_MIN, T_MAX, margen=timedelta(minutes=29))
    assert tabla["verdad"].tolist() == ["fuerte"]


def test_en_tierra_un_avion_solo_cuenta_una_vez():
    # Dos estancias que tocan el intervalo: una fila, débil, con la primera estancia.
    llegadas = _eventos([("ccc001", "2023-07-28 09:50"), ("ccc001", "2023-07-28 10:40")])
    salidas = _eventos([("ccc001", "2023-07-28 10:15"), ("ccc001", "2023-07-28 12:00")])
    tabla = inferir_en_tierra(llegadas, salidas, T_MIN, T_MAX)
    assert len(tabla) == 1
    fila = tabla.iloc[0]
    assert fila["verdad"] == "debil"
    assert fila["llegada"] == _t("2023-07-28 09:50")
    assert fila["salida"] == _t("2023-07-28 10:15")


def test_en_tierra_secuencias_incoherentes_se_descartan():
    # Dos llegadas seguidas (falta una salida) y dos salidas seguidas (falta una
    # llegada): la estancia con un extremo desconocido no se usa.
    llegadas = _eventos([("ddd001", "2023-07-27 20:00"), ("ddd001", "2023-07-28 12:00")])
    salidas = _eventos([("eee001", "2023-07-27 20:00"), ("eee001", "2023-07-28 12:00")])
    tabla = inferir_en_tierra(llegadas, salidas, T_MIN, T_MAX)
    assert tabla.empty
    assert list(tabla.columns) == ["icao24", "llegada", "salida", "verdad"]


def test_en_tierra_rechaza_instantes_sin_zona_horaria():
    llegadas = pd.DataFrame({"icao24": ["fff001"], "instante": [datetime(2023, 7, 27, 20)]})
    salidas = _eventos([])
    with pytest.raises(ValueError):
        inferir_en_tierra(llegadas, salidas, T_MIN, T_MAX)
    with pytest.raises(ValueError):
        inferir_en_tierra(_eventos([]), salidas, datetime(2023, 7, 28, 10), T_MAX)


def test_en_tierra_rechaza_intervalo_al_reves():
    with pytest.raises(ValueError):
        inferir_en_tierra(_eventos([]), _eventos([]), T_MAX, T_MIN)


def test_en_tierra_rechaza_fecha_demasiado_reciente():
    ahora = datetime.now(UTC)
    with pytest.raises(ValueError):
        inferir_en_tierra(_eventos([]), _eventos([]), ahora - timedelta(hours=1), ahora)


# --------------------------------------------------------------- comparar_conteos


def test_comparar_conteos_por_categoria_y_total():
    foto = {"pasillo_unico": 6, "fuselaje_ancho": 3, "regional": 1}
    adsb = {"pasillo_unico": 4, "fuselaje_ancho": 4}
    r = comparar_conteos(foto, adsb)
    assert r["por_categoria"]["pasillo_unico"] == {"n_foto": 6, "n_adsb": 4, "explicados": 4}
    assert r["por_categoria"]["fuselaje_ancho"] == {"n_foto": 3, "n_adsb": 4, "explicados": 3}
    assert r["por_categoria"]["regional"] == {"n_foto": 1, "n_adsb": 0, "explicados": 0}
    total = r["total"]
    assert (total["n_foto"], total["n_adsb"], total["explicados"]) == (10, 8, 7)
    assert total["cobertura"] == pytest.approx(0.7)
    assert total["exceso_adsb"] == pytest.approx(1 / 8)


def test_intervalo_de_wilson_8_de_10():
    # Valor de referencia de Wilson (1927) al 95 % para 8 éxitos de 10, calculado a
    # mano con z = 1,96: (0,4902; 0,9433).
    r = comparar_conteos({"pasillo_unico": 10}, {"pasillo_unico": 8})
    bajo, alto = r["total"]["cobertura_ic95"]
    assert bajo == pytest.approx(0.4902, abs=1e-4)
    assert alto == pytest.approx(0.9433, abs=1e-4)


def test_intervalo_de_wilson_en_los_extremos():
    # Con 0 de n el límite inferior es 0 y con n de n el superior es 1.
    bajo, alto = comparar_conteos({"regional": 5}, {})["total"]["cobertura_ic95"]
    assert bajo == pytest.approx(0.0, abs=1e-12) and 0 < alto < 1
    bajo, alto = comparar_conteos({"regional": 5}, {"regional": 9})["total"]["cobertura_ic95"]
    assert 0 < bajo < 1 and alto == pytest.approx(1.0)


def test_comparar_conteos_sin_aviones():
    r = comparar_conteos({}, {})
    assert r["total"]["cobertura"] is None
    assert r["total"]["cobertura_ic95"] is None
    assert r["total"]["exceso_adsb"] is None


def test_comparar_conteos_rechaza_negativos():
    with pytest.raises(ValueError):
        comparar_conteos({"ligero": -1}, {})
