"""Lógica de las herramientas del MCP 1 (tráfico aéreo), sin depender del SDK de MCP.

Solo lee el almacén local (vía `avion_osint.adsb.consultas`); nunca llama a una API
externa. Reglas obligatorias (`docs/specs/fase-1.md`, sección 4):

1. Toda fecha pasa por `comprobar_fecha_retrospectiva`: una fecha reciente lanza
   `FechaDemasiadoRecienteError` (el servidor la convierte en un error del MCP).
2. Si un aeródromo no es civil, `vuelos_en_zona` solo da conteos por aeródromo, día y
   categoría de tamaño, sin icao24, indicativos ni matrículas. `info_avion` no cambia.
3. Si el círculo incluye algún aeródromo no civil, la regla 2 se aplica a todo.
4. Toda respuesta lleva `fuente`, `periodo` y `cobertura`.
5. Sin datos, `resultado` es el texto «no hay datos en el almacén…», no una lista vacía.
   Una lista vacía solo sale si hay días descargados y en ellos no hubo movimientos.
"""

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pandas as pd
import yaml

from avion_osint.adsb import RUTA_ALMACEN, consultas
from avion_osint.adsb.trazas import distancia_km
from avion_osint.aerodromos import cargar_aerodromos
from avion_osint.limites import comprobar_fecha_retrospectiva

RUTA_CATEGORIAS = Path(__file__).resolve().parents[4] / "config" / "categorias_tipo.yaml"
NO_HAY_DATOS = "no hay datos en el almacén"
FUENTE_AERONAVES = "Base de aeronaves de OpenSky"


def _comprobar_fechas(inicio: date, fin: date) -> None:
    for fecha in (inicio, fin):
        comprobar_fecha_retrospectiva(fecha)
    if inicio > fin:
        raise ValueError("fecha_inicio es posterior a fecha_fin.")


def _o_nulo(valor, tipo):
    """None si el valor es nulo; si no, convertido con `tipo` (int, float, str…) para
    que la respuesta tenga solo tipos de Python serializables a JSON."""
    return None if pd.isna(valor) else tipo(valor)


def _cobertura(aerodromo: str, inicio: date, fin: date, almacen: Path) -> dict:
    """Días pedidos, días descargados y, por día con datos, desequilibrio, puntos en tierra
    y fuente."""
    dias = consultas.resumen(aerodromo, inicio, fin, "dia", almacen)
    return {
        "dias_pedidos": (fin - inicio).days + 1,
        "dias_con_datos": int(dias["dias_con_datos"].sum()),
        "dias": [
            {
                "fecha": fila.periodo.isoformat(),
                "desequilibrio": _o_nulo(fila.desequilibrio, float),
                "n_puntos_tierra": _o_nulo(fila.n_puntos_tierra, int),
                "fuente": _o_nulo(fila.fuente, str),
            }
            for fila in dias.itertuples()
        ],
    }


def _fuentes(fuentes_movimientos: pd.Series, coberturas: list[dict]) -> list[str]:
    """Fuentes de los movimientos y de las filas de cobertura, sin repetir. Con la
    cobertura, un periodo descargado y sin vuelos también dice de dónde salen los datos."""
    fuentes = set(fuentes_movimientos.dropna())
    for cobertura in coberturas:
        for dia in cobertura["dias"]:
            if dia["fuente"]:
                fuentes.update(dia["fuente"].split(", "))
    return sorted(fuentes)


def _periodo(inicio: date, fin: date, coberturas: list[dict]) -> dict:
    """Periodo pedido y periodo cubierto (primer y último día con datos, o None)."""
    dias = sorted(dia["fecha"] for cobertura in coberturas for dia in cobertura["dias"])
    return {
        "pedido": {"inicio": inicio.isoformat(), "fin": fin.isoformat()},
        "cubierto": {"inicio": dias[0], "fin": dias[-1]} if dias else None,
    }


def _tipos(icao24s: list[str], almacen: Path) -> pd.DataFrame:
    """icao24, matricula y tipo_oaci de esos aviones (vacía si no hay base de aeronaves)."""
    ruta = almacen / "aeronaves.parquet"
    columnas = ["icao24", "matricula", "tipo_oaci"]
    if not ruta.exists() or not icao24s:
        return pd.DataFrame({columna: pd.Series(dtype=str) for columna in columnas})
    tabla = pd.read_parquet(ruta, columns=columnas, filters=[("icao24", "in", icao24s)])
    return tabla.drop_duplicates("icao24")


def _categorias() -> dict[str, str]:
    """Tipo OACI → categoría de tamaño (config/categorias_tipo.yaml)."""
    with open(RUTA_CATEGORIAS, encoding="utf-8") as fichero:
        tipos = yaml.safe_load(fichero)["tipos"]
    return {tipo: datos["categoria"] for tipo, datos in tipos.items()}


def _detalle(tabla: pd.DataFrame) -> list[dict]:
    """Movimientos uno a uno (solo aeródromos civiles)."""
    return [
        {
            "aerodromo": fila.aerodromo,
            "instante": fila.instante.isoformat(),
            "tipo_movimiento": fila.tipo_movimiento,
            "icao24": fila.icao24,
            "indicativo": _o_nulo(fila.indicativo, str),
            "matricula": _o_nulo(fila.matricula, str),
            "tipo_oaci": _o_nulo(fila.tipo_oaci, str),
            "fuente": fila.fuente,
            "metodo": fila.metodo,
        }
        for fila in tabla.itertuples()
    ]


def _agregado(tabla: pd.DataFrame) -> list[dict]:
    """Conteos por aeródromo, día y categoría de tamaño, sin identificadores (regla 2).
    Un tipo que no esté en config/categorias_tipo.yaml (o sin tipo) es «desconocido»."""
    categorias = _categorias()
    conteos = (
        tabla.assign(
            fecha=tabla["instante"].dt.date,
            categoria=tabla["tipo_oaci"].map(categorias).fillna("desconocido"),
            llegada=tabla["tipo_movimiento"] == "llegada",
            salida=tabla["tipo_movimiento"] == "salida",
        )
        .groupby(["aerodromo", "fecha", "categoria"], sort=True)
        .agg(n_llegadas=("llegada", "sum"), n_salidas=("salida", "sum"))
        .reset_index()
    )
    return [
        {
            "aerodromo": fila.aerodromo,
            "fecha": fila.fecha.isoformat(),
            "categoria": fila.categoria,
            "n_llegadas": int(fila.n_llegadas),
            "n_salidas": int(fila.n_salidas),
        }
        for fila in conteos.itertuples()
    ]


def vuelos_en_zona(
    lat: float,
    lon: float,
    radio_km: float,
    fecha_inicio: date,
    fecha_fin: date,
    almacen: Path = RUTA_ALMACEN,
) -> dict:
    """Movimientos (días fecha_inicio a fecha_fin, ambos incluidos, en UTC) de los
    aeródromos de config/aerodromos.yaml cuyo punto de referencia está a radio_km o menos
    de (lat, lon). Si alguno no es civil, solo conteos agregados para todos (reglas 2 y 3)."""
    _comprobar_fechas(fecha_inicio, fecha_fin)
    zona = [
        aerodromo
        for aerodromo in cargar_aerodromos().values()
        if distancia_km(lat, lon, aerodromo.lat, aerodromo.lon) <= radio_km
    ]
    agregado = any(aerodromo.solo_agregado for aerodromo in zona)
    inicio = datetime.combine(fecha_inicio, time(), UTC)
    fin = datetime.combine(fecha_fin + timedelta(days=1), time(), UTC)

    coberturas = {a.icao: _cobertura(a.icao, fecha_inicio, fecha_fin, almacen) for a in zona}
    tablas = [
        consultas.movimientos(a.icao, inicio, fin, almacen).assign(aerodromo=a.icao) for a in zona
    ]
    tabla = pd.concat(tablas, ignore_index=True) if tablas else pd.DataFrame()

    respuesta = {
        "fuente": _fuentes(
            tabla["fuente"] if not tabla.empty else pd.Series(dtype=str),
            list(coberturas.values()),
        ),
        "periodo": _periodo(fecha_inicio, fecha_fin, list(coberturas.values())),
        "cobertura": coberturas,
        "aerodromos": [a.icao for a in zona],
        "agregado": agregado,
    }
    if not zona:
        respuesta["resultado"] = (
            f"{NO_HAY_DATOS}: ningún aeródromo del proyecto está a {radio_km} km o menos "
            f"de ({lat}, {lon})."
        )
    elif tabla.empty and not any(c["dias"] for c in coberturas.values()):
        respuesta["resultado"] = (
            f"{NO_HAY_DATOS} para {', '.join(coberturas)} entre {fecha_inicio.isoformat()} "
            f"y {fecha_fin.isoformat()}."
        )
    else:
        tabla = tabla.merge(_tipos(sorted(set(tabla["icao24"])), almacen), on="icao24", how="left")
        respuesta["resultado"] = _agregado(tabla) if agregado else _detalle(tabla)
    return respuesta


def info_avion(icao24: str, almacen: Path = RUTA_ALMACEN) -> dict:
    """Fila de la base de aeronaves para ese icao24. Es un dato público del avión, no de
    su actividad, así que no se agrega (regla 2)."""
    fila = consultas.aeronave(icao24, almacen)
    if fila is not None:
        fila["fecha_base"] = _o_nulo(fila["fecha_base"], date.isoformat)
    return {
        "fuente": FUENTE_AERONAVES,
        "periodo": {"fecha_base": fila["fecha_base"] if fila else None},
        "cobertura": (
            "Copia mensual de la base de aeronaves (mes de fecha_base): no recoge cambios "
            "posteriores de matrícula, tipo u operador, y puede tener huecos o errores."
        ),
        "resultado": fila if fila else f"{NO_HAY_DATOS} para el icao24 {icao24!r}.",
    }


def leer_periodo(periodo: str) -> tuple[date, date]:
    """'AAAA-MM-DD/AAAA-MM-DD' (intervalo ISO 8601, ambos días incluidos) → (inicio, fin)."""
    partes = periodo.split("/")
    if len(partes) != 2:
        raise ValueError(f"periodo debe ser 'AAAA-MM-DD/AAAA-MM-DD'; vale {periodo!r}.")
    return date.fromisoformat(partes[0]), date.fromisoformat(partes[1])


def resumen_actividad(
    aerodromo: str, periodo: str, por: str = "dia", almacen: Path = RUTA_ALMACEN
) -> dict:
    """Conteos por día o semana del aeródromo en el periodo ('AAAA-MM-DD/AAAA-MM-DD'),
    con la cobertura. Solo cifras agregadas, sea el aeródromo civil o no."""
    inicio, fin = leer_periodo(periodo)
    _comprobar_fechas(inicio, fin)
    tabla = consultas.resumen(aerodromo, inicio, fin, por, almacen)
    cobertura = _cobertura(aerodromo, inicio, fin, almacen)
    fuentes = consultas.movimientos(
        aerodromo,
        datetime.combine(inicio, time(), UTC),
        datetime.combine(fin + timedelta(days=1), time(), UTC),
        almacen,
    )["fuente"]
    respuesta = {
        "fuente": _fuentes(fuentes, [cobertura]),
        "periodo": _periodo(inicio, fin, [cobertura]),
        "cobertura": cobertura,
        "por": por,
    }
    if tabla.empty:
        respuesta["resultado"] = (
            f"{NO_HAY_DATOS} para {aerodromo} entre {inicio.isoformat()} y {fin.isoformat()}."
        )
    else:
        respuesta["resultado"] = [
            {
                "periodo": fila.periodo.isoformat(),
                "dias_con_datos": int(fila.dias_con_datos),
                "n_llegadas": int(fila.n_llegadas),
                "n_salidas": int(fila.n_salidas),
                "n_aviones": int(fila.n_aviones),
                "desequilibrio": _o_nulo(fila.desequilibrio, float),
                "n_puntos_tierra": _o_nulo(fila.n_puntos_tierra, int),
            }
            for fila in tabla.itertuples()
        ]
    return respuesta
