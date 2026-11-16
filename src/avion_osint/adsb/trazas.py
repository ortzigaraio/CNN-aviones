"""Aterrizajes y despegues deducidos de una traza de posiciones (decisión D17).

* **llegada** = último punto en vuelo cerca del aeródromo antes de un tramo en tierra o
  de un silencio;
* **salida** = primer punto en vuelo cerca del aeródromo después de un tramo en tierra o
  de un silencio.

«Cerca» = por debajo de 1.000 m sobre el aeródromo y a menos de 10 km de su punto de
referencia. Los umbrales los fija `docs/specs/fase-1.md` (sección 5); si se cambian,
lo decide Fable. La duración mínima de un silencio no la fija D17: el valor de aquí es
provisional y está anotado en `docs/specs/fase-1-dudas.md`.
"""

import math
from datetime import timedelta

import pandas as pd

from avion_osint.aerodromos import Aerodromo
from avion_osint.limites import comprobar_fecha_retrospectiva

ALTURA_MAXIMA_M = 1000  # D17
DISTANCIA_MAXIMA_KM = 10  # D17
SILENCIO_MINIMO = timedelta(minutes=10)  # provisional: ver docs/specs/fase-1-dudas.md
RADIO_TIERRA_KM = 6371.0088  # radio medio de la Tierra (IUGG)

COLUMNAS = ["tipo_movimiento", "instante"]


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia por la superficie de una esfera (fórmula del semiverseno), en km."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(a))


def deducir_movimientos(traza: pd.DataFrame, aerodromo: Aerodromo) -> pd.DataFrame:
    """Regla D17. traza: instante (UTC, con zona horaria), lat, lon, altitud_m, en_tierra
    (booleano). altitud_m es la altura **sobre el aeródromo**, como dice D17: si la
    fuente da altitud sobre el nivel del mar, quien llama debe restar la elevación.
    Devuelve tipo_movimiento ("llegada" | "salida") e instante, ordenados por instante.

    * Silencio: dos puntos seguidos separados por SILENCIO_MINIMO o más.
    * El principio y el final de la traza **no** cuentan como silencio: no se sabe qué
      pasó antes o después (si la traza se corta a medianoche con el avión en final, daría
      una llegada y luego una salida falsas). Quien llama debe pasar la traza completa
      del avión, sin cortarla por días.
    * Un punto en vuelo sin altitud (nula) no cuenta como cerca.
    * Una aproximación frustrada o un sobrevuelo bajo, sin tramo en tierra ni silencio,
      no dan ningún movimiento.
    """
    if traza.empty:
        return pd.DataFrame(
            {
                "tipo_movimiento": pd.Series(dtype=str),
                "instante": pd.Series(dtype="datetime64[us, UTC]"),
            }
        )
    instante = pd.to_datetime(traza["instante"])
    if instante.dt.tz is None:
        raise ValueError("La columna instante de la traza no tiene zona horaria; debe ser UTC.")
    comprobar_fecha_retrospectiva(instante.max().date())

    puntos = traza.assign(instante=instante.dt.tz_convert("UTC")).sort_values(
        "instante", kind="stable"
    )
    instantes = list(puntos["instante"])
    en_tierra = [bool(valor) for valor in puntos["en_tierra"]]
    cerca = [
        pd.notna(altitud)
        and altitud < ALTURA_MAXIMA_M
        and distancia_km(lat, lon, aerodromo.lat, aerodromo.lon) < DISTANCIA_MAXIMA_KM
        for lat, lon, altitud in zip(puntos["lat"], puntos["lon"], puntos["altitud_m"], strict=True)
    ]

    filas = []
    for i in range(len(instantes) - 1):
        j = i + 1
        silencio = instantes[j] - instantes[i] >= SILENCIO_MINIMO
        # Llegada: punto en vuelo cerca seguido de un punto en tierra o de un silencio.
        if not en_tierra[i] and cerca[i] and (en_tierra[j] or silencio):
            filas.append(("llegada", instantes[i]))
        # Salida: punto en vuelo cerca precedido de un punto en tierra o de un silencio.
        if not en_tierra[j] and cerca[j] and (en_tierra[i] or silencio):
            filas.append(("salida", instantes[j]))

    tabla = pd.DataFrame(filas, columns=COLUMNAS)
    tabla["instante"] = pd.to_datetime(tabla["instante"], utc=True)
    return tabla
