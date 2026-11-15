"""Comparación de conteos por categoría entre la foto y ADS-B."""

import math
from collections.abc import Mapping

# Cuantil 0,975 de la normal estándar: intervalo bilateral al 95 %.
Z_95 = 1.959963984540054


def intervalo_wilson(exitos: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Intervalo de Wilson (1927) para una proporción exitos/n:
    (p + z²/2n ± z·sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n)."""
    p = exitos / n
    z2 = z * z
    denominador = 1 + z2 / n
    centro = (p + z2 / (2 * n)) / denominador
    semiancho = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominador
    return max(0.0, centro - semiancho), min(1.0, centro + semiancho)


def comparar_conteos(foto: Mapping[str, int], adsb: Mapping[str, int]) -> dict:
    """Por categoría: n_foto, n_adsb, explicados = min(n_foto, n_adsb).
    Total: cobertura = suma(explicados) / suma(n_foto), con intervalo de Wilson al 95 %;
    exceso_adsb = suma(max(n_adsb - n_foto, 0)) / suma(n_adsb).

    Devuelve {"por_categoria": {categoria: {...}}, "total": {n_foto, n_adsb,
    explicados, cobertura, cobertura_ic95, exceso_adsb}}. Cuando un denominador es 0,
    el cociente (y su intervalo) es None.
    """
    for nombre, conteos in (("foto", foto), ("adsb", adsb)):
        if any(n < 0 for n in conteos.values()):
            raise ValueError(f"Hay conteos negativos en {nombre}.")

    por_categoria = {}
    for categoria in sorted(set(foto) | set(adsb)):
        n_foto, n_adsb = foto.get(categoria, 0), adsb.get(categoria, 0)
        por_categoria[categoria] = {
            "n_foto": n_foto,
            "n_adsb": n_adsb,
            "explicados": min(n_foto, n_adsb),
        }

    n_foto = sum(c["n_foto"] for c in por_categoria.values())
    n_adsb = sum(c["n_adsb"] for c in por_categoria.values())
    explicados = sum(c["explicados"] for c in por_categoria.values())
    exceso = sum(max(c["n_adsb"] - c["n_foto"], 0) for c in por_categoria.values())
    return {
        "por_categoria": por_categoria,
        "total": {
            "n_foto": n_foto,
            "n_adsb": n_adsb,
            "explicados": explicados,
            "cobertura": explicados / n_foto if n_foto else None,
            "cobertura_ic95": intervalo_wilson(explicados, n_foto) if n_foto else None,
            "exceso_adsb": exceso / n_adsb if n_adsb else None,
        },
    }
