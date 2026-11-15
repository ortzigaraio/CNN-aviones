"""Aviones en tierra durante el intervalo de la foto, a partir de llegadas y salidas."""

from datetime import datetime, timedelta

import pandas as pd

from avion_osint.limites import comprobar_fecha_retrospectiva

COLUMNAS = ["icao24", "llegada", "salida", "verdad"]


def _instantes_utc(eventos: pd.DataFrame, nombre: str) -> pd.DataFrame:
    """Copia con columnas icao24 e instante; instante debe llevar zona horaria."""
    if eventos.empty:
        return pd.DataFrame(
            {"icao24": pd.Series(dtype=str), "instante": pd.Series(dtype="datetime64[ns, UTC]")}
        )
    instante = pd.to_datetime(eventos["instante"])
    if instante.dt.tz is None:
        raise ValueError(f"La columna instante de {nombre} no tiene zona horaria; debe ser UTC.")
    return pd.DataFrame({"icao24": eventos["icao24"], "instante": instante.dt.tz_convert("UTC")})


def _estancias(eventos: list[tuple[pd.Timestamp, str]]):
    """Pares (llegada, salida) de un avión, con None en el extremo que queda fuera de la
    ventana. Las estancias con un extremo perdido (dos llegadas o dos salidas seguidas)
    se descartan: no se sabe cuándo empezaron o acabaron."""
    llegada = None
    abierta = False  # hay una llegada sin su salida
    for i, (instante, clase) in enumerate(eventos):
        if clase == "llegada":
            # Una llegada abierta seguida de otra llegada: falta la salida; se descarta.
            llegada, abierta = instante, True
        else:
            if abierta:
                yield llegada, instante
            elif i == 0:
                yield None, instante  # en tierra desde antes de la ventana
            # Salida tras salida: falta la llegada; se descarta.
            abierta = False
    if abierta:
        yield llegada, None  # sigue en tierra al final de la ventana


def inferir_en_tierra(
    llegadas: pd.DataFrame,
    salidas: pd.DataFrame,
    t_min: datetime,
    t_max: datetime,
    margen: timedelta = timedelta(minutes=30),
) -> pd.DataFrame:
    """Devuelve la tabla en_tierra (sin tipo ni categoría).
    llegadas y salidas: columnas icao24, instante (UTC).

    * fuerte: llegó antes de t_min - margen (o antes de la ventana) y no se fue hasta
      después de t_max + margen (o después de la ventana).
    * debil: su estancia solapa [t_min, t_max] sin cumplir lo anterior.
    Un avión aparece como mucho una vez; si tiene varias estancias que solapan el
    intervalo, se queda la primera y es débil. Los aviones sin ningún evento en la
    ventana no aparecen. t_min y t_max deben llevar zona horaria.
    """
    if t_min.tzinfo is None or t_max.tzinfo is None:
        raise ValueError("t_min y t_max deben llevar zona horaria (UTC).")
    if t_min > t_max:
        raise ValueError("t_min es posterior a t_max.")
    comprobar_fecha_retrospectiva(t_max.date())
    ini, fin = pd.Timestamp(t_min), pd.Timestamp(t_max)

    eventos = pd.concat(
        [
            _instantes_utc(llegadas, "llegadas").assign(clase="llegada"),
            _instantes_utc(salidas, "salidas").assign(clase="salida"),
        ],
        ignore_index=True,
    ).sort_values(["icao24", "instante"], kind="stable")

    filas = []
    for icao24, grupo in eventos.groupby("icao24", sort=True):
        solapan = [
            (llegada, salida)
            for llegada, salida in _estancias(
                list(zip(grupo["instante"], grupo["clase"], strict=True))
            )
            if (llegada is None or llegada < fin) and (salida is None or salida > ini)
        ]
        if not solapan:
            continue
        llegada, salida = solapan[0]
        fuerte = (
            len(solapan) == 1
            and (llegada is None or llegada < ini - margen)
            and (salida is None or salida > fin + margen)
        )
        filas.append((icao24, llegada, salida, "fuerte" if fuerte else "debil"))

    tabla = pd.DataFrame(filas, columns=COLUMNAS)
    for columna in ("llegada", "salida"):
        tabla[columna] = pd.to_datetime(tabla[columna], utc=True)
    return tabla
