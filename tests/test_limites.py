"""Tests de la salvaguarda retrospectiva (`avion_osint.limites`)."""

from datetime import date, timedelta

import pytest

from avion_osint.limites import (
    RETRASO_MINIMO_DIAS,
    FechaDemasiadoRecienteError,
    comprobar_fecha_retrospectiva,
    retraso_dias,
)

HOY = date(2026, 11, 15)


@pytest.fixture(autouse=True)
def sin_variable(monkeypatch):
    """Cada test empieza sin la variable de entorno definida."""
    monkeypatch.delenv("AVION_OSINT_RETRASO_DIAS", raising=False)


def test_sin_variable_el_retraso_es_30():
    assert retraso_dias() == RETRASO_MINIMO_DIAS == 30


def test_fecha_a_30_dias_se_acepta():
    comprobar_fecha_retrospectiva(HOY - timedelta(days=30), hoy=HOY)


def test_fecha_a_29_dias_se_rechaza():
    with pytest.raises(FechaDemasiadoRecienteError):
        comprobar_fecha_retrospectiva(HOY - timedelta(days=29), hoy=HOY)


def test_fecha_futura_se_rechaza():
    with pytest.raises(FechaDemasiadoRecienteError):
        comprobar_fecha_retrospectiva(HOY + timedelta(days=1), hoy=HOY)


def test_variable_a_60_rechaza_fecha_a_45_dias(monkeypatch):
    monkeypatch.setenv("AVION_OSINT_RETRASO_DIAS", "60")
    assert retraso_dias() == 60
    with pytest.raises(FechaDemasiadoRecienteError):
        comprobar_fecha_retrospectiva(HOY - timedelta(days=45), hoy=HOY)


def test_variable_a_5_sigue_siendo_30(monkeypatch):
    monkeypatch.setenv("AVION_OSINT_RETRASO_DIAS", "5")
    assert retraso_dias() == 30
    with pytest.raises(FechaDemasiadoRecienteError):
        comprobar_fecha_retrospectiva(HOY - timedelta(days=10), hoy=HOY)


def test_variable_no_numerica_da_value_error(monkeypatch):
    monkeypatch.setenv("AVION_OSINT_RETRASO_DIAS", "treinta")
    with pytest.raises(ValueError):
        retraso_dias()


def test_mensaje_indica_fecha_mas_reciente_permitida():
    with pytest.raises(FechaDemasiadoRecienteError, match="2026-10-16"):
        comprobar_fecha_retrospectiva(HOY, hoy=HOY)
