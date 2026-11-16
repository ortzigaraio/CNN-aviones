"""Tests del MCP 1 (tráfico aéreo): las cinco reglas de `docs/specs/fase-1.md` (sección 4)
sobre un almacén de juguete en tmp_path, y el servidor del SDK. Sin red.

Las respuestas guardadas son el propio almacén de juguete (`almacen_juguete.py`): el MCP
solo lee el almacén local, nunca una API.
"""

import asyncio
import json
from datetime import date, timedelta

import pytest
from almacen_juguete import crear_almacen
from mcp.server.mcpserver.exceptions import ToolError

from avion_osint.aerodromos import cargar_aerodromos
from avion_osint.limites import FechaDemasiadoRecienteError
from avion_osint.mcp_server.trafico import herramientas
from avion_osint.mcp_server.trafico.servidor import servidor

AERODROMOS = cargar_aerodromos()
LEMD, LEZG = AERODROMOS["LEMD"], AERODROMOS["LEZG"]
DIA = date(2023, 3, 6)
OTRO_DIA = date(2022, 1, 1)  # sin datos en el almacén de juguete
ICAO24_FICTICIOS = ["aaa001", "aaa002", "aaa003", "aaa004", "aaa005"]


@pytest.fixture
def almacen(tmp_path):
    return crear_almacen(tmp_path / "adsb")


def _respuestas(almacen):
    """Una respuesta de cada herramienta, con datos."""
    return [
        herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, DIA, DIA, almacen),
        herramientas.info_avion("aaa001", almacen),
        herramientas.resumen_actividad("LEMD", "2023-03-06/2023-03-12", "semana", almacen),
    ]


# ---------------------------------------------------------------- regla 1: retraso mínimo


def test_regla1_fecha_reciente_da_error_y_no_datos(almacen):
    hoy = date.today()
    with pytest.raises(FechaDemasiadoRecienteError, match="demasiado reciente"):
        herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, DIA, hoy, almacen)
    with pytest.raises(FechaDemasiadoRecienteError, match="demasiado reciente"):
        herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, hoy, hoy, almacen)
    periodo = f"{(hoy - timedelta(days=5)).isoformat()}/{hoy.isoformat()}"
    with pytest.raises(FechaDemasiadoRecienteError, match="demasiado reciente"):
        herramientas.resumen_actividad("LEMD", periodo, "dia", almacen)


def test_regla1_el_servidor_devuelve_el_mensaje_claro():
    # Pasa por el SDK: el error llega con su texto, no como un error genérico.
    hoy = date.today().isoformat()
    argumentos = {"lat": 40.0, "lon": -3.0, "radio_km": 10, "fecha_inicio": hoy, "fecha_fin": hoy}
    with pytest.raises(ToolError, match="demasiado reciente"):
        asyncio.run(servidor.call_tool("vuelos_en_zona", argumentos))


# ---------------------------------------------------------------- regla 2: no civil, agregado


def test_regla2_aerodromo_no_civil_solo_conteos(almacen):
    assert LEZG.solo_agregado
    respuesta = herramientas.vuelos_en_zona(LEZG.lat, LEZG.lon, 10, DIA, DIA, almacen)
    assert respuesta["agregado"] is True
    assert respuesta["resultado"] == [
        {"aerodromo": "LEZG", "fecha": "2023-03-06", "categoria": "desconocido",
         "n_llegadas": 1, "n_salidas": 0},  # aaa005, tipo ZZZZ fuera de la tabla
        {"aerodromo": "LEZG", "fecha": "2023-03-06", "categoria": "ligero",
         "n_llegadas": 1, "n_salidas": 1},  # aaa004, C172
    ]  # fmt: skip
    texto = json.dumps(respuesta)
    for prohibido in [*ICAO24_FICTICIOS, "FIC0", "FICT-", "icao24", "indicativo", "matricula"]:
        assert prohibido not in texto


def test_regla2_info_avion_no_cambia(almacen):
    # aaa004 solo ha operado en LEZG (mixto); su ficha pública se da igual.
    respuesta = herramientas.info_avion("aaa004", almacen)
    assert respuesta["resultado"]["matricula"] == "FICT-4"
    assert respuesta["resultado"]["tipo_oaci"] == "C172"


def test_aerodromo_civil_da_el_detalle(almacen):
    respuesta = herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, DIA, DIA, almacen)
    assert respuesta["agregado"] is False
    assert [m["icao24"] for m in respuesta["resultado"]] == ["aaa001", "aaa002", "aaa001"]
    primero = respuesta["resultado"][0]
    assert primero["instante"] == "2023-03-06T08:00:00+00:00"
    assert (primero["matricula"], primero["tipo_oaci"]) == ("FICT-1", "A320")
    assert primero["indicativo"] == "FIC001"


# ---------------------------------------------------------------- regla 3: círculo mixto


def test_regla3_circulo_con_civil_y_no_civil_agrega_todo(almacen):
    # LEMD y LEZG están a unos 260 km; un círculo de 200 km en el punto medio los coge a los
    # dos (y a LETL, que no tiene datos en el almacén de juguete).
    lat, lon = (LEMD.lat + LEZG.lat) / 2, (LEMD.lon + LEZG.lon) / 2
    respuesta = herramientas.vuelos_en_zona(lat, lon, 200, DIA, DIA, almacen)
    assert set(respuesta["aerodromos"]) == {"LEMD", "LETL", "LEZG"}
    assert respuesta["agregado"] is True
    lemd = [fila for fila in respuesta["resultado"] if fila["aerodromo"] == "LEMD"]
    assert lemd == [
        {"aerodromo": "LEMD", "fecha": "2023-03-06", "categoria": "fuselaje_ancho",
         "n_llegadas": 1, "n_salidas": 0},  # aaa002, B77W
        {"aerodromo": "LEMD", "fecha": "2023-03-06", "categoria": "pasillo_unico",
         "n_llegadas": 1, "n_salidas": 1},  # aaa001, A320
    ]  # fmt: skip
    texto = json.dumps(respuesta)
    for prohibido in [*ICAO24_FICTICIOS, "FIC0", "FICT-"]:
        assert prohibido not in texto


# ---------------------------------------------------------------- regla 4: fuente, periodo…


def test_regla4_toda_respuesta_lleva_fuente_periodo_y_cobertura(almacen, tmp_path):
    vacio = tmp_path / "vacio"
    sin_datos = [
        herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, DIA, DIA, vacio),
        herramientas.vuelos_en_zona(0.0, 0.0, 10, DIA, DIA, almacen),
        herramientas.info_avion("aaa999", almacen),
        herramientas.resumen_actividad("LEMD", "2023-03-06/2023-03-12", "dia", vacio),
    ]
    for respuesta in _respuestas(almacen) + sin_datos:
        assert {"fuente", "periodo", "cobertura", "resultado"} <= set(respuesta)
        json.dumps(respuesta)  # serializable tal cual


def test_regla4_contenido_de_fuente_periodo_y_cobertura(almacen):
    vuelos, avion, resumen = _respuestas(almacen)
    assert vuelos["fuente"] == ["adsblol"]
    assert vuelos["periodo"] == {
        "pedido": {"inicio": "2023-03-06", "fin": "2023-03-06"},
        "cubierto": {"inicio": "2023-03-06", "fin": "2023-03-06"},
    }
    assert vuelos["cobertura"]["LEMD"]["dias_pedidos"] == 1
    assert vuelos["cobertura"]["LEMD"]["dias"] == [
        {
            "fecha": "2023-03-06",
            "desequilibrio": pytest.approx(1 / 3),
            "n_puntos_tierra": 120,
            "fuente": "adsblol",
        }
    ]
    assert avion["fuente"] == herramientas.FUENTE_AERONAVES
    assert avion["periodo"] == {"fecha_base": "2023-07-01"}
    assert resumen["periodo"]["cubierto"] == {"inicio": "2023-03-06", "fin": "2023-03-08"}
    assert resumen["cobertura"]["dias_pedidos"] == 7
    assert resumen["cobertura"]["dias_con_datos"] == 3
    assert resumen["resultado"][0]["n_aviones"] == 3


# ---------------------------------------------------------------- regla 5: sin datos


def test_regla5_sin_datos_lo_dice_y_no_da_lista_vacia(almacen, tmp_path):
    vacio = tmp_path / "vacio"
    respuestas = [
        herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, DIA, DIA, vacio),
        herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, OTRO_DIA, OTRO_DIA, almacen),
        herramientas.vuelos_en_zona(0.0, 0.0, 10, DIA, DIA, almacen),  # sin aeródromos
        herramientas.info_avion("aaa999", almacen),
        herramientas.info_avion("aaa001", vacio),
        herramientas.resumen_actividad("LEPA", "2023-03-06/2023-03-12", "dia", almacen),
    ]  # fmt: skip
    for respuesta in respuestas:
        assert isinstance(respuesta["resultado"], str)
        assert respuesta["resultado"].startswith(herramientas.NO_HAY_DATOS)


def test_regla5_dia_descargado_sin_vuelos_si_da_lista_vacia(almacen):
    # El 2023-03-08 de LEMD tiene fila de cobertura y ningún movimiento: eso sí es «cero vuelos».
    dia = date(2023, 3, 8)
    respuesta = herramientas.vuelos_en_zona(LEMD.lat, LEMD.lon, 10, dia, dia, almacen)
    assert respuesta["resultado"] == []
    assert respuesta["cobertura"]["LEMD"]["dias_con_datos"] == 1
    # La fuente sale de la fila de cobertura aunque no haya movimientos.
    assert respuesta["fuente"] == ["adsblol"]


# ---------------------------------------------------------------- otros


def test_resumen_actividad_rechaza_periodo_mal_escrito(almacen):
    with pytest.raises(ValueError, match="AAAA-MM-DD/AAAA-MM-DD"):
        herramientas.resumen_actividad("LEMD", "2023-03-06", "dia", almacen)


def test_el_servidor_publica_las_tres_herramientas():
    nombres = {herramienta.name for herramienta in asyncio.run(servidor.list_tools())}
    assert nombres == {"vuelos_en_zona", "info_avion", "resumen_actividad"}
