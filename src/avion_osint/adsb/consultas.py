"""Consultas sobre el almacén local de ADS-B, con DuckDB. Las usan el MCP 1 y la Fase 4.

Esquema del almacén (`docs/specs/fase-1.md`, sección 3):

* `movimientos/aerodromo=<OACI>/fecha=<AAAA-MM-DD>/parte.parquet`: icao24,
  tipo_movimiento, instante (UTC), indicativo, fuente, metodo.
* `cobertura/aerodromo=<OACI>/fecha=<AAAA-MM-DD>/parte.parquet`: una fila por día con
  n_llegadas, n_salidas, n_aviones, desequilibrio, n_puntos_tierra, fuente. Que exista la fila
  de un día significa que ese día se descargó, aunque no tenga movimientos.
* `aeronaves.parquet`: ver `avion_osint.adsb.aeronaves`.

Estas funciones no aplican la agregación de los aeródromos no civiles: eso lo hace
quien presenta los resultados (el MCP o los informes).
"""

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import duckdb
import pandas as pd

from avion_osint.adsb import RUTA_ALMACEN
from avion_osint.aerodromos import cargar_aerodromos
from avion_osint.fusion import inferir_en_tierra
from avion_osint.limites import comprobar_fecha_retrospectiva

# Llegadas y salidas que se miran alrededor del intervalo, como en la Fase 1b
# (docs/specs/fase-1b.md, sección 5: «ventana de ± 7 días»).
VENTANA_EN_TIERRA = timedelta(days=7)

TIPOS_MOVIMIENTOS = {
    "icao24": "str",
    "tipo_movimiento": "str",
    "instante": "datetime64[us, UTC]",
    "indicativo": "str",
    "fuente": "str",
    "metodo": "str",
}
TIPOS_COBERTURA = {"fecha": "datetime64[us]", "n_puntos_tierra": "Int64", "fuente": "str"}
COLUMNAS_RESUMEN = [
    "periodo",
    "dias_con_datos",
    "n_llegadas",
    "n_salidas",
    "n_aviones",
    "desequilibrio",
    "n_puntos_tierra",
    "fuente",
]


def _comprobar_aerodromo(aerodromo: str) -> None:
    """ValueError si el aeródromo no está en config/aerodromos.yaml."""
    if aerodromo not in cargar_aerodromos():
        raise ValueError(f"El aeródromo {aerodromo!r} no está en config/aerodromos.yaml.")


def _leer(
    almacen: Path, tabla: str, aerodromo: str, tipos: dict[str, str], filtro: str, valores: list
) -> pd.DataFrame:
    """Columnas `tipos` de una tabla particionada, para un aeródromo, con el filtro SQL
    dado. Si no hay ningún fichero, una tabla vacía con esas columnas y tipos."""
    carpeta = almacen / tabla / f"aerodromo={aerodromo}"
    if not any(carpeta.glob("fecha=*/*.parquet")):
        return pd.DataFrame({columna: pd.Series(dtype=tipo) for columna, tipo in tipos.items()})
    with duckdb.connect() as conexion:
        conexion.execute("SET TimeZone = 'UTC'")
        return conexion.execute(
            f"SELECT {', '.join(tipos)} "
            "FROM read_parquet(?, hive_partitioning = true) "
            f"WHERE {filtro}",
            [str(carpeta / "fecha=*" / "*.parquet"), *valores],
        ).df()


def movimientos(
    aerodromo: str, inicio: datetime, fin: datetime, almacen: Path = RUTA_ALMACEN
) -> pd.DataFrame:
    """Movimientos del aeródromo con inicio <= instante < fin, ordenados por instante.
    Columnas: icao24, tipo_movimiento, instante, indicativo, fuente, metodo. inicio y fin
    deben llevar zona horaria. Tabla vacía si el almacén no tiene ese aeródromo."""
    if inicio.tzinfo is None or fin.tzinfo is None:
        raise ValueError("inicio y fin deben llevar zona horaria (UTC).")
    # fin no se incluye: se comprueba el último instante que sí entra.
    comprobar_fecha_retrospectiva((fin - timedelta(microseconds=1)).astimezone(UTC).date())
    _comprobar_aerodromo(aerodromo)
    tabla = _leer(
        almacen,
        "movimientos",
        aerodromo,
        TIPOS_MOVIMIENTOS,
        "instante >= ? AND instante < ? ORDER BY instante, icao24",
        [inicio, fin],
    )
    return tabla.reset_index(drop=True)


def en_tierra(
    aerodromo: str, t_min: datetime, t_max: datetime, almacen: Path = RUTA_ALMACEN
) -> pd.DataFrame:
    """Tabla de `fusion.inferir_en_tierra` con las llegadas y salidas del aeródromo
    entre t_min - VENTANA_EN_TIERRA y t_max + VENTANA_EN_TIERRA."""
    tabla = movimientos(aerodromo, t_min - VENTANA_EN_TIERRA, t_max + VENTANA_EN_TIERRA, almacen)
    llegadas = tabla[tabla["tipo_movimiento"] == "llegada"]
    salidas = tabla[tabla["tipo_movimiento"] == "salida"]
    return inferir_en_tierra(llegadas, salidas, t_min, t_max)


def _periodo(dias: pd.Series, por: str) -> pd.Series:
    """Día (sin hora) o lunes de la semana ISO de cada fecha."""
    if por == "semana":
        dias = dias - pd.to_timedelta(dias.dt.day_of_week, unit="D")
    return dias.dt.date


def resumen(
    aerodromo: str, inicio: date, fin: date, por: str = "dia", almacen: Path = RUTA_ALMACEN
) -> pd.DataFrame:
    """Una fila por día o por semana (que empieza en lunes) de [inicio, fin], solo para
    los periodos con datos (fila de cobertura o algún movimiento), ordenadas.

    Columnas: periodo (fecha del día o del lunes), dias_con_datos (días con fila de
    cobertura), n_llegadas, n_salidas, n_aviones (icao24 distintos), desequilibrio
    (|llegadas − salidas| / (llegadas + salidas); nulo si no hay movimientos) y
    n_puntos_tierra (suma de los días; nulo si ningún día lo tiene) y fuente (fuentes
    de las filas de cobertura del periodo, separadas por comas; nula si no hay ninguna).
    Los conteos salen de la tabla de movimientos; dias_con_datos, n_puntos_tierra y
    fuente, de la de cobertura.
    Las semanas de los extremos solo cuentan los días que caen en [inicio, fin].
    """
    if por not in ("dia", "semana"):
        raise ValueError(f"por debe ser 'dia' o 'semana'; vale {por!r}.")
    if inicio > fin:
        raise ValueError("inicio es posterior a fin.")
    comprobar_fecha_retrospectiva(fin)

    tabla_movimientos = movimientos(
        aerodromo,
        datetime.combine(inicio, time(), UTC),
        datetime.combine(fin + timedelta(days=1), time(), UTC),
        almacen,
    )
    tabla_cobertura = _leer(
        almacen, "cobertura", aerodromo, TIPOS_COBERTURA, "fecha BETWEEN ? AND ?", [inicio, fin]
    )

    dias_movimiento = tabla_movimientos["instante"].dt.tz_localize(None).dt.normalize()
    conteos = (
        tabla_movimientos.assign(
            periodo=_periodo(dias_movimiento, por),
            llegada=tabla_movimientos["tipo_movimiento"] == "llegada",
            salida=tabla_movimientos["tipo_movimiento"] == "salida",
        )
        .groupby("periodo")
        .agg(
            n_llegadas=("llegada", "sum"),
            n_salidas=("salida", "sum"),
            n_aviones=("icao24", "nunique"),
        )
    )
    cobertura = (
        tabla_cobertura.assign(periodo=_periodo(tabla_cobertura["fecha"], por))
        .groupby("periodo")
        .agg(
            dias_con_datos=("fecha", "size"),
            n_puntos_tierra=("n_puntos_tierra", lambda serie: serie.sum(min_count=1)),
            fuente=("fuente", lambda serie: ", ".join(sorted(set(serie.dropna()))) or None),
        )
    )

    tabla = cobertura.join(conteos, how="outer").sort_index().reset_index()
    for columna in ("dias_con_datos", "n_llegadas", "n_salidas", "n_aviones"):
        tabla[columna] = tabla[columna].fillna(0).astype(int)
    tabla["n_puntos_tierra"] = tabla["n_puntos_tierra"].astype("Int64")
    total = tabla["n_llegadas"] + tabla["n_salidas"]
    tabla["desequilibrio"] = ((tabla["n_llegadas"] - tabla["n_salidas"]).abs() / total).where(
        total > 0
    )
    return tabla[COLUMNAS_RESUMEN]


def aeronave(icao24: str, almacen: Path = RUTA_ALMACEN) -> dict | None:
    """Fila de aeronaves.parquet para ese icao24 (sin distinguir mayúsculas), como
    diccionario. None si no está o si el almacén no tiene la base de aeronaves. Si el
    icao24 estuviera repetido en la base, devuelve la primera fila."""
    ruta = almacen / "aeronaves.parquet"
    if not ruta.exists():
        return None
    with duckdb.connect() as conexion:
        cursor = conexion.execute(
            "SELECT * FROM read_parquet(?) WHERE icao24 = ? LIMIT 1",
            [str(ruta), icao24.strip().lower()],
        )
        fila = cursor.fetchone()
        if fila is None:
            return None
        return dict(zip([columna[0] for columna in cursor.description], fila, strict=True))
