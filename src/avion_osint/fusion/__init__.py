"""Cruce imagen ↔ ADS-B (Fase 1b; se reutiliza en la Fase 4)."""

from avion_osint.fusion.conteos import comparar_conteos
from avion_osint.fusion.en_tierra import inferir_en_tierra
from avion_osint.fusion.sombra import hora_por_sombra

__all__ = ["comparar_conteos", "hora_por_sombra", "inferir_en_tierra"]
