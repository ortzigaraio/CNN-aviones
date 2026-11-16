"""Servidor MCP 1 (tráfico aéreo) con el SDK oficial de MCP para Python.

Solo envuelve las funciones de `herramientas`, que leen el almacén local `data/adsb/`.
Arranque, por la entrada y salida estándar (transporte stdio):

    uv run python -m avion_osint.mcp_server.trafico.servidor
"""

from datetime import date

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from avion_osint.mcp_server.trafico import herramientas

servidor = MCPServer(
    "trafico",
    instructions=(
        "Consulta retrospectiva del almacén local de ADS-B del proyecto (aterrizajes y "
        "despegues). Solo fechas con al menos 30 días de antigüedad. En aeródromos no "
        "civiles solo hay conteos agregados. Cita siempre la fuente, el periodo y la "
        "cobertura que acompañan a cada respuesta."
    ),
)


def _sin_excepciones_ocultas(funcion, *argumentos):
    """Convierte los ValueError (incluida una fecha demasiado reciente) en ToolError, para
    que quien pregunta reciba el mensaje claro y no un error genérico del SDK."""
    try:
        return funcion(*argumentos)
    except ValueError as error:
        raise ToolError(str(error)) from error


@servidor.tool()
def vuelos_en_zona(
    lat: float, lon: float, radio_km: float, fecha_inicio: date, fecha_fin: date
) -> dict:
    """Aterrizajes y despegues de los aeródromos del proyecto cuyo punto de referencia
    está a radio_km o menos de (lat, lon), entre fecha_inicio y fecha_fin (AAAA-MM-DD,
    ambos incluidos, UTC). Si algún aeródromo del círculo no es civil, solo devuelve
    conteos por aeródromo, día y categoría de tamaño."""
    return _sin_excepciones_ocultas(
        herramientas.vuelos_en_zona, lat, lon, radio_km, fecha_inicio, fecha_fin
    )


@servidor.tool()
def info_avion(icao24: str) -> dict:
    """Matrícula, tipo OACI, fabricante, modelo y operador de un avión según la base de
    aeronaves de OpenSky, a partir de su código de transpondedor (icao24)."""
    return _sin_excepciones_ocultas(herramientas.info_avion, icao24)


@servidor.tool()
def resumen_actividad(aerodromo: str, periodo: str, por: str = "dia") -> dict:
    """Conteos de llegadas, salidas y aviones distintos de un aeródromo (código OACI) por
    día o por semana (por = "dia" | "semana") en el periodo 'AAAA-MM-DD/AAAA-MM-DD'
    (ambos días incluidos), con la cobertura de los datos."""
    return _sin_excepciones_ocultas(herramientas.resumen_actividad, aerodromo, periodo, por)


if __name__ == "__main__":
    servidor.run()
