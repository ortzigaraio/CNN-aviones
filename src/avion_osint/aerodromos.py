"""Carga de los aeródromos declarados en `config/aerodromos.yaml`.

Es la única fuente de verdad sobre qué aeródromos son civiles y cuáles militares o mixtos
(decisión D4); de eso depende la regla de agregación.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

RUTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "config" / "aerodromos.yaml"
TIPOS_VALIDOS = {"civil", "militar", "mixto"}


@dataclass(frozen=True)
class Aerodromo:
    icao: str  # código OACI de 4 letras, p. ej. "LEMD"
    nombre: str
    lat: float
    lon: float
    radio_km: float
    tipo: str  # "civil" | "militar" | "mixto"

    @property
    def solo_agregado(self) -> bool:
        """True si tipo != "civil"."""
        return self.tipo != "civil"


def cargar_aerodromos(ruta: Path = RUTA_POR_DEFECTO) -> dict[str, Aerodromo]:
    """Clave: código OACI. ValueError si un tipo no es válido o un código está repetido."""
    with open(ruta, encoding="utf-8") as fichero:
        contenido = yaml.safe_load(fichero)

    aerodromos: dict[str, Aerodromo] = {}
    for entrada in contenido["aerodromos"]:
        aerodromo = Aerodromo(**entrada)
        if aerodromo.tipo not in TIPOS_VALIDOS:
            raise ValueError(
                f"Tipo no válido para {aerodromo.icao}: {aerodromo.tipo!r}. "
                f"Debe ser uno de {sorted(TIPOS_VALIDOS)}."
            )
        if aerodromo.icao in aerodromos:
            raise ValueError(f"Código OACI repetido en {ruta}: {aerodromo.icao}.")
        aerodromos[aerodromo.icao] = aerodromo
    return aerodromos
