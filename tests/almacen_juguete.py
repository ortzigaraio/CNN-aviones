"""Almacén ADS-B de juguete para los tests, con datos claramente ficticios (icao24 aaa0NN,
indicativos FIC0NN, matrículas FICT-N). Se crea en una carpeta temporal en cada test."""

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from avion_osint.adsb.aeronaves import cargar_aeronaves

# Partición (aerodromo, fecha) → movimientos (icao24, tipo, hora UTC, indicativo).
MOVIMIENTOS = {
    ("LEMD", "2023-03-06"): [  # lunes
        ("aaa001", "llegada", "08:00", "FIC001"),
        ("aaa002", "llegada", "09:00", "FIC002"),
        ("aaa001", "salida", "18:00", "FIC003"),
    ],
    ("LEMD", "2023-03-07"): [
        ("aaa003", "salida", "07:00", None),
    ],
    ("LEMD", "2023-03-13"): [  # lunes de la semana siguiente
        ("aaa002", "salida", "10:00", "FIC004"),
    ],
    ("LEZG", "2023-03-06"): [  # aeródromo mixto
        ("aaa004", "llegada", "10:00", "FIC005"),
        ("aaa005", "llegada", "11:00", "FIC006"),
        ("aaa004", "salida", "15:00", "FIC007"),
    ],
}

# Partición → n_puntos_tierra. El 2023-03-08 de LEMD se descargó y no tuvo movimientos.
COBERTURA = {
    ("LEMD", "2023-03-06"): 120,
    ("LEMD", "2023-03-07"): None,
    ("LEMD", "2023-03-08"): 15,
    ("LEMD", "2023-03-13"): 40,
    ("LEZG", "2023-03-06"): 30,
}


# Base de aeronaves de juguete con el formato real de OpenSky (15 columnas, cabecera vacía).
def _fila_csv(icao24: str, matricula: str, fabricante: str, modelo: str, tipo: str, operador: str):
    """Fila de 15 columnas con los valores en las posiciones de `aeronaves.POSICIONES`."""
    valores = [icao24, matricula, "", fabricante, modelo, tipo, "", "", "", operador] + [""] * 5
    return ",".join(f'"{valor}"' for valor in valores)


AERONAVES_CSV = "\n".join(
    [
        ",".join(['""'] * 15),
        _fila_csv("AAA001", "FICT-1", "Fabricante1", "Modelo1", "A320", "Op1"),
        _fila_csv("aaa002", "FICT-2", "Fabricante2", "Modelo2", "B77W", "Op2"),
        _fila_csv("aaa004", "FICT-4", "Fabricante3", "Modelo3", "C172", ""),
        _fila_csv("aaa005", "FICT-5", "", "", "ZZZZ", ""),
        "",
    ]
)


def _escribir(almacen: Path, tabla: str, aerodromo: str, fecha: str, filas: pd.DataFrame) -> None:
    carpeta = almacen / tabla / f"aerodromo={aerodromo}" / f"fecha={fecha}"
    carpeta.mkdir(parents=True)
    filas.to_parquet(carpeta / "parte.parquet", index=False)


def crear_almacen(almacen: Path) -> Path:
    """Escribe movimientos, cobertura y aeronaves.parquet en `almacen` y lo devuelve."""
    for (aerodromo, fecha), filas in MOVIMIENTOS.items():
        tabla = pd.DataFrame(
            {
                "icao24": [f[0] for f in filas],
                "tipo_movimiento": [f[1] for f in filas],
                "instante": pd.to_datetime([f"{fecha} {f[2]}" for f in filas], utc=True),
                "indicativo": [f[3] for f in filas],
                "fuente": "adsblol",
                "metodo": "deducido",
            }
        )
        _escribir(almacen, "movimientos", aerodromo, fecha, tabla)

    for (aerodromo, fecha), puntos in COBERTURA.items():
        filas = MOVIMIENTOS.get((aerodromo, fecha), [])
        llegadas = sum(f[1] == "llegada" for f in filas)
        salidas = len(filas) - llegadas
        tabla = pd.DataFrame(
            {
                "n_llegadas": [llegadas],
                "n_salidas": [salidas],
                "n_aviones": [len({f[0] for f in filas})],
                "desequilibrio": [abs(llegadas - salidas) / len(filas) if filas else None],
                "n_puntos_tierra": pd.array([puntos], dtype="Int64"),
                "fuente": ["adsblol"],
            }
        )
        _escribir(almacen, "cobertura", aerodromo, fecha, tabla)

    ruta_csv = almacen.parent / "aeronaves_juguete.csv"
    ruta_csv.write_text(AERONAVES_CSV, encoding="utf-8")
    cargar_aeronaves(ruta_csv, date(2023, 7, 1), almacen)
    return almacen


def t(texto: str) -> datetime:
    """Instante UTC a partir de 'AAAA-MM-DD HH:MM'."""
    return datetime.fromisoformat(texto).replace(tzinfo=UTC)
