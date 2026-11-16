"""Geometría de cajas orientadas: área, intersección e IoU de cuadriláteros convexos.

Una caja es un array (4, 2) con sus cuatro esquinas en orden (horario o antihorario),
en metros o en píxeles. IoU (intersection over union) = área común / área de la unión:
0 si no se tocan, 1 si coinciden.
"""

import numpy as np


def area(p: np.ndarray) -> float:
    """Área de un polígono simple (fórmula del cordón)."""
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def _cruz(u, v) -> float:
    """Componente z del producto vectorial de dos vectores del plano."""
    return float(u[0] * v[1] - u[1] * v[0])


def interseccion(p: np.ndarray, q: np.ndarray) -> float:
    """Área común de dos cuadriláteros convexos (recorte de Sutherland-Hodgman)."""
    sentido = 1.0 if _cruz(q[1] - q[0], q[2] - q[1]) > 0 else -1.0
    poligono = [tuple(v) for v in p]
    for i in range(len(q)):
        a, b = q[i], q[(i + 1) % len(q)]
        entrada, poligono = poligono, []
        if not entrada:
            break

        def dentro(v, a=a, b=b):
            return sentido * _cruz(b - a, np.asarray(v) - a) >= 0

        for j, v in enumerate(entrada):
            w = entrada[(j + 1) % len(entrada)]
            dv, dw = dentro(v), dentro(w)
            if dv:
                poligono.append(v)
            if dv != dw:
                v_, w_ = np.asarray(v), np.asarray(w)
                d1 = _cruz(b - a, v_ - a)
                d2 = _cruz(b - a, w_ - a)
                poligono.append(tuple(v_ + (w_ - v_) * d1 / (d1 - d2)))
    return area(np.array(poligono)) if len(poligono) >= 3 else 0.0


def iou(p: np.ndarray, q: np.ndarray) -> float:
    """IoU de dos cajas orientadas. 0 si la unión no tiene área."""
    ap, aq = area(p), area(q)
    # Con bordes casi paralelos y coincidentes el recorte puede salir inestable; la
    # intersección nunca supera el área de la menor.
    inter = min(interseccion(p, q), ap, aq)
    union = ap + aq - inter
    return inter / union if union > 0 else 0.0


def matriz_iou(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """IoU de cada caja de a (n, 4, 2) con cada caja de b (m, 4, 2): array (n, m).
    Solo se recortan los pares cuyos rectángulos envolventes se tocan."""
    a = np.asarray(a, dtype=float).reshape(-1, 4, 2)
    b = np.asarray(b, dtype=float).reshape(-1, 4, 2)
    resultado = np.zeros((len(a), len(b)))
    if len(a) == 0 or len(b) == 0:
        return resultado
    amin, amax = a.min(axis=1), a.max(axis=1)
    bmin, bmax = b.min(axis=1), b.max(axis=1)
    tocan = np.all(
        (amin[:, None, :] <= bmax[None, :, :]) & (bmin[None, :, :] <= amax[:, None, :]), axis=2
    )
    for i, j in zip(*np.nonzero(tocan), strict=True):
        resultado[i, j] = iou(a[i], b[j])
    return resultado


def longitud_anchura(p: np.ndarray) -> tuple[float, float]:
    """(lado mayor, lado menor) de una caja rectangular, en sus unidades."""
    lados = [float(np.linalg.norm(p[1] - p[0])), float(np.linalg.norm(p[2] - p[1]))]
    return max(lados), min(lados)
