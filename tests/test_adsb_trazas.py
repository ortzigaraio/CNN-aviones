"""Tests de `deducir_movimientos` (regla D17) con trazas escritas a mano, sin red.

El aeródromo es ficticio, en (40° N, 0°). Cada punto se da por su minuto desde las
10:00 UTC, su distancia al norte del aeródromo en km, su altura sobre el aeródromo en m
y si está en tierra.
"""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from avion_osint.adsb.trazas import deducir_movimientos, distancia_km
from avion_osint.aerodromos import Aerodromo
from avion_osint.limites import FechaDemasiadoRecienteError

AERODROMO = Aerodromo(icao="XXXX", nombre="Ficticio", lat=40.0, lon=0.0, radio_km=5, tipo="civil")
KM_POR_GRADO = 111.195  # km por grado de latitud con RADIO_TIERRA_KM
INICIO = datetime(2023, 3, 6, 10, 0, tzinfo=UTC)


def traza(*puntos: tuple[float, float, float | None, bool]) -> pd.DataFrame:
    """puntos: (minuto, km al norte, altura en m, en_tierra)."""
    return pd.DataFrame(
        {
            "instante": [INICIO + timedelta(minutes=p[0]) for p in puntos],
            "lat": [AERODROMO.lat + p[1] / KM_POR_GRADO for p in puntos],
            "lon": [AERODROMO.lon] * len(puntos),
            "altitud_m": [p[2] for p in puntos],
            "en_tierra": [p[3] for p in puntos],
        }
    )


def movimientos(tabla: pd.DataFrame) -> list[tuple[str, float]]:
    """(tipo, minuto desde las 10:00) de cada movimiento."""
    return [
        (fila.tipo_movimiento, (fila.instante - INICIO).total_seconds() / 60)
        for fila in tabla.itertuples()
    ]


def test_distancia_km_un_grado_de_latitud():
    assert distancia_km(40.0, 0.0, 41.0, 0.0) == pytest.approx(KM_POR_GRADO, rel=1e-4)


def test_aterrizaje_normal():
    tabla = deducir_movimientos(
        traza(
            (0, 30, 3000, False),
            (2, 15, 1500, False),
            (4, 6, 600, False),
            (6, 2, 200, False),
            (7, 0, 0, True),
            (8, 0, 0, True),
            (20, 0, 0, True),
        ),
        AERODROMO,
    )
    assert movimientos(tabla) == [("llegada", 6)]
    assert tabla["instante"].dt.tz is not None


def test_despegue_normal():
    tabla = deducir_movimientos(
        traza(
            (0, 0, 0, True),
            (5, 0, 0, True),
            (6, 1, 150, False),
            (7, 5, 700, False),
            (8, 12, 1500, False),
            (10, 25, 3000, False),
        ),
        AERODROMO,
    )
    assert movimientos(tabla) == [("salida", 6)]


def test_traza_con_hueco_cerca_del_aerodromo():
    # Aproximación, sin ningún punto en tierra (receptor sin cobertura en el suelo), dos
    # horas de silencio y despegue: llegada al último punto antes del hueco y salida al
    # primero después.
    tabla = deducir_movimientos(
        traza(
            (0, 15, 1500, False),
            (3, 5, 500, False),
            (5, 2, 150, False),
            (125, 1, 150, False),
            (126, 6, 700, False),
            (128, 15, 1800, False),
        ),
        AERODROMO,
    )
    assert movimientos(tabla) == [("llegada", 5), ("salida", 125)]


def test_traza_con_hueco_en_ruta_no_da_movimientos():
    # Silencio de 40 min lejos y alto (fuera de cobertura en ruta): no es un aterrizaje.
    tabla = deducir_movimientos(
        traza((0, 80, 9000, False), (40, 150, 9000, False), (41, 160, 9000, False)),
        AERODROMO,
    )
    assert tabla.empty


def test_sobrevuelo_bajo_que_no_aterriza():
    # Pasa a 600 m de altura sobre el aeródromo, sin tocar tierra ni silencios.
    tabla = deducir_movimientos(
        traza(
            (0, -20, 800, False),
            (2, -8, 600, False),
            (4, 0, 600, False),
            (6, 8, 600, False),
            (8, 20, 800, False),
        ),
        AERODROMO,
    )
    assert tabla.empty


def test_aproximacion_frustrada():
    # Baja hasta 50 m, frustra (motor y al aire), da la vuelta sin salir de 10 km y
    # aterriza en el segundo intento: una sola llegada, la del segundo intento.
    tabla = deducir_movimientos(
        traza(
            (0, 12, 1200, False),
            (2, 5, 500, False),
            (4, 1, 50, False),
            (5, -2, 300, False),
            (7, -6, 900, False),
            (10, 4, 900, False),
            (12, 6, 600, False),
            (14, 2, 200, False),
            (15, 0, 0, True),
            (16, 0, 0, True),
        ),
        AERODROMO,
    )
    assert movimientos(tabla) == [("llegada", 14)]


def test_hueco_corto_en_la_aproximacion_no_es_silencio():
    # 5 minutos sin puntos (menos que SILENCIO_MINIMO) sin tocar tierra: nada.
    tabla = deducir_movimientos(
        traza((0, 8, 800, False), (5, 3, 300, False), (6, 9, 800, False)),
        AERODROMO,
    )
    assert tabla.empty


def test_final_de_la_traza_no_cuenta_como_silencio():
    # La traza acaba con el avión bajo y cerca: no se sabe si aterrizó.
    tabla = deducir_movimientos(traza((0, 8, 800, False), (2, 2, 150, False)), AERODROMO)
    assert tabla.empty


def test_punto_sin_altitud_no_cuenta_como_cerca():
    tabla = deducir_movimientos(
        traza((0, 5, 500, False), (2, 2, None, False), (3, 0, 0, True)), AERODROMO
    )
    assert tabla.empty


def test_traza_vacia_y_orden_de_entrada():
    assert deducir_movimientos(traza(), AERODROMO).empty
    desordenada = traza((7, 0, 0, True), (6, 2, 200, False), (4, 6, 600, False))
    assert movimientos(deducir_movimientos(desordenada, AERODROMO)) == [("llegada", 6)]


def test_exige_zona_horaria():
    tabla = traza((0, 2, 200, False), (1, 0, 0, True))
    tabla["instante"] = tabla["instante"].dt.tz_localize(None)
    with pytest.raises(ValueError, match="zona horaria"):
        deducir_movimientos(tabla, AERODROMO)


def test_rechaza_traza_reciente():
    tabla = traza((0, 2, 200, False), (1, 0, 0, True))
    tabla["instante"] = pd.Timestamp.now(tz="UTC") + pd.to_timedelta([0, 1], unit="min")
    with pytest.raises(FechaDemasiadoRecienteError):
        deducir_movimientos(tabla, AERODROMO)
