"""Salvaguarda del carácter retrospectivo del proyecto.

Todo pipeline y todo servidor MCP debe pasar sus fechas por
`comprobar_fecha_retrospectiva`, que rechaza las que tengan menos antigüedad que el
retraso mínimo. El retraso se puede subir con la variable de entorno
`AVION_OSINT_RETRASO_DIAS`, pero nunca bajar de `RETRASO_MINIMO_DIAS` (decisión D3).
"""

import os
from datetime import UTC, date, datetime, timedelta

RETRASO_MINIMO_DIAS = 30


class FechaDemasiadoRecienteError(ValueError):
    """La fecha es más reciente de lo que permite el retraso mínimo."""


def retraso_dias() -> int:
    """Lee AVION_OSINT_RETRASO_DIAS. Devuelve max(valor, 30). Sin variable: 30.
    Valor no entero: ValueError."""
    valor = os.environ.get("AVION_OSINT_RETRASO_DIAS")
    if valor is None:
        return RETRASO_MINIMO_DIAS
    try:
        dias = int(valor)
    except ValueError:
        raise ValueError(
            f"AVION_OSINT_RETRASO_DIAS debe ser un número entero de días; vale {valor!r}."
        ) from None
    return max(dias, RETRASO_MINIMO_DIAS)


def comprobar_fecha_retrospectiva(fecha: date, hoy: date | None = None) -> None:
    """Lanza FechaDemasiadoRecienteError si fecha > hoy - retraso_dias().
    `hoy` por defecto es la fecha actual en UTC; el parámetro existe para los tests."""
    if hoy is None:
        hoy = datetime.now(UTC).date()
    limite = hoy - timedelta(days=retraso_dias())
    if fecha > limite:
        raise FechaDemasiadoRecienteError(
            f"La fecha {fecha.isoformat()} es demasiado reciente para un análisis "
            f"retrospectivo. La fecha más reciente permitida es {limite.isoformat()}."
        )
