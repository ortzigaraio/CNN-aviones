"""Hora de la foto a partir de la dirección de las sombras.

Posición del sol: algoritmo de la calculadora solar de la NOAA (National Oceanic and
Atmospheric Administration de EE. UU.), que resume las fórmulas de baja precisión de
J. Meeus, «Astronomical Algorithms» (1991), capítulos 24-25 y 28: longitud media y
anomalía media del sol, ecuación del centro, longitud aparente, oblicuidad de la
eclíptica, declinación y ecuación del tiempo. Error del orden de 1 minuto de tiempo
entre 1800 y 2100, de sobra frente a la precisión de medir una sombra.

No se corrige la refracción atmosférica, que solo importa con el sol muy bajo.

Convención de ángulos: acimut en grados desde el norte geográfico (verdadero), en el
sentido de las agujas del reloj (90° = este). El acimut de la sombra es la dirección
desde la base del objeto hacia la punta de su sombra; es el del sol más 180°.
"""

import math
from datetime import UTC, date, datetime, timedelta

from avion_osint.limites import comprobar_fecha_retrospectiva

_J2000 = datetime(2000, 1, 1, 12, tzinfo=UTC)  # día juliano 2451545,0
_PASO = timedelta(minutes=2)
_TOLERANCIA = timedelta(seconds=1)


def posicion_sol(instante: datetime, lat: float, lon: float) -> tuple[float, float]:
    """(acimut, altura) del sol en grados para un instante UTC con zona horaria.
    Longitud positiva al este."""
    t = (instante - _J2000).total_seconds() / 86400 / 36525  # siglos julianos desde J2000
    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
    m = math.radians(357.52911 + t * (35999.05029 - 0.0001537 * t))
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    centro = (
        math.sin(m) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + math.sin(2 * m) * (0.019993 - 0.000101 * t)
        + math.sin(3 * m) * 0.000289
    )
    omega = math.radians(125.04 - 1934.136 * t)
    longitud_aparente = math.radians(l0 + centro - 0.00569 - 0.00478 * math.sin(omega))
    oblicuidad = math.radians(
        23
        + (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60) / 60
        + 0.00256 * math.cos(omega)
    )
    declinacion = math.asin(math.sin(oblicuidad) * math.sin(longitud_aparente))

    y = math.tan(oblicuidad / 2) ** 2
    l0r = math.radians(l0)
    ecuacion_tiempo_min = 4 * math.degrees(
        y * math.sin(2 * l0r)
        - 2 * e * math.sin(m)
        + 4 * e * y * math.sin(m) * math.cos(2 * l0r)
        - 0.5 * y * y * math.sin(4 * l0r)
        - 1.25 * e * e * math.sin(2 * m)
    )

    utc = instante.astimezone(UTC)
    minutos_utc = utc.hour * 60 + utc.minute + utc.second / 60 + utc.microsecond / 6e7
    tiempo_solar_verdadero = minutos_utc + ecuacion_tiempo_min + 4 * lon
    angulo_horario = math.radians(tiempo_solar_verdadero / 4 - 180)

    phi = math.radians(lat)
    sen_altura = math.sin(phi) * math.sin(declinacion) + math.cos(phi) * math.cos(
        declinacion
    ) * math.cos(angulo_horario)
    altura = math.degrees(math.asin(max(-1.0, min(1.0, sen_altura))))
    # atan2 da el acimut contado desde el sur hacia el oeste; +180 lo cuenta desde el norte.
    acimut = (
        math.degrees(
            math.atan2(
                math.sin(angulo_horario),
                math.cos(angulo_horario) * math.sin(phi) - math.tan(declinacion) * math.cos(phi),
            )
        )
        + 180
    ) % 360
    return acimut, altura


def hora_por_sombra(lat: float, lon: float, fecha: date, acimut_sombra_grados: float) -> datetime:
    """Hora UTC en la que el sol proyecta una sombra con ese acimut (dirección, en
    grados desde el norte) en ese lugar y día. ValueError si no hay solución.

    `fecha` se toma como día solar local: se busca entre las 0:00 y las 24:00 de hora
    solar media del lugar (en España coincide en la práctica con el día UTC). Solo se
    aceptan instantes con el sol sobre el horizonte. Si hay más de una solución ese
    día (posible en los trópicos), también ValueError, porque no se sabe cuál es.
    Devuelve un datetime con zona horaria UTC, redondeado al segundo.
    """
    comprobar_fecha_retrospectiva(fecha)
    objetivo = (acimut_sombra_grados + 180) % 360  # acimut del sol

    def diferencia(instante: datetime) -> float:
        acimut, _ = posicion_sol(instante, lat, lon)
        return (acimut - objetivo + 180) % 360 - 180  # en (-180, 180]

    def de_dia(instante: datetime) -> bool:
        return posicion_sol(instante, lat, lon)[1] > 0

    inicio = datetime(fecha.year, fecha.month, fecha.day, tzinfo=UTC) - timedelta(hours=lon / 15)
    soluciones: list[datetime] = []
    a = inicio
    while a < inicio + timedelta(days=1):
        b = a + _PASO
        if de_dia(a) and de_dia(b):
            da, db = diferencia(a), diferencia(b)
            # Cambio de signo en [a, b) sin salto de ±180° (que sería el lado opuesto del
            # cielo). Se busca la raíz por bisección hasta el segundo.
            if (da <= 0 < db or db < 0 <= da) and abs(da - db) < 90:
                izq, der = a, b
                while der - izq > _TOLERANCIA:
                    medio = izq + (der - izq) / 2
                    if (diferencia(medio) <= 0) == (da <= 0):
                        izq = medio
                    else:
                        der = medio
                soluciones.append(izq)
        a = b

    if not soluciones:
        raise ValueError(
            f"Ningún instante del {fecha.isoformat()} con el sol sobre el horizonte da una "
            f"sombra de acimut {acimut_sombra_grados}° en ({lat}, {lon})."
        )
    if len(soluciones) > 1:
        raise ValueError(
            f"Hay {len(soluciones)} instantes posibles el {fecha.isoformat()} para una sombra "
            f"de acimut {acimut_sombra_grados}° en ({lat}, {lon}); no se puede elegir."
        )
    solucion = soluciones[0]
    return (solucion + timedelta(microseconds=500_000)).replace(microsecond=0)
