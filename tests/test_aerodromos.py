"""Tests de la carga de aeródromos (`avion_osint.aerodromos`)."""

import pytest

from avion_osint.aerodromos import Aerodromo, cargar_aerodromos


def escribir_yaml(tmp_path, texto: str):
    ruta = tmp_path / "aerodromos.yaml"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def test_carga_el_yaml_real_del_repo():
    aerodromos = cargar_aerodromos()
    assert set(aerodromos) == {"LEMD", "LEBL", "LEPA", "LETL", "LEVC", "LEZG"}
    lemd = aerodromos["LEMD"]
    assert lemd.icao == "LEMD"
    assert lemd.tipo == "civil"
    assert lemd.radio_km == 5
    assert 40 < lemd.lat < 41 and -4 < lemd.lon < -3
    assert aerodromos["LEZG"].tipo == "mixto"


@pytest.mark.parametrize(
    ("tipo", "esperado"),
    [("civil", False), ("militar", True), ("mixto", True)],
)
def test_solo_agregado_segun_tipo(tipo, esperado):
    aerodromo = Aerodromo(icao="XXXX", nombre="Prueba", lat=0.0, lon=0.0, radio_km=5.0, tipo=tipo)
    assert aerodromo.solo_agregado is esperado


def test_tipo_invalido_da_value_error(tmp_path):
    ruta = escribir_yaml(
        tmp_path,
        """
aerodromos:
  - {icao: LEMD, nombre: Barajas, lat: 40.47, lon: -3.56, radio_km: 5, tipo: comercial}
""",
    )
    with pytest.raises(ValueError, match="comercial"):
        cargar_aerodromos(ruta)


def test_codigo_repetido_da_value_error(tmp_path):
    ruta = escribir_yaml(
        tmp_path,
        """
aerodromos:
  - {icao: LEMD, nombre: Barajas, lat: 40.47, lon: -3.56, radio_km: 5, tipo: civil}
  - {icao: LEMD, nombre: Otra vez, lat: 40.47, lon: -3.56, radio_km: 5, tipo: civil}
""",
    )
    with pytest.raises(ValueError, match="LEMD"):
        cargar_aerodromos(ruta)
