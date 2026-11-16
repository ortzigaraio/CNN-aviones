"""Tests de `avion_osint.vision.geometria` con cuadriláteros de área conocida."""

import math

import numpy as np
import pytest

from avion_osint.vision.geometria import area, interseccion, iou, longitud_anchura, matriz_iou


def rect(cx: float, cy: float, largo: float, ancho: float, angulo: float = 0.0) -> np.ndarray:
    """Rectángulo centrado en (cx, cy), con el lado largo girado `angulo` grados."""
    a = math.radians(angulo)
    u = np.array([math.cos(a), math.sin(a)]) * largo / 2
    v = np.array([-math.sin(a), math.cos(a)]) * ancho / 2
    c = np.array([cx, cy])
    return np.array([c - u - v, c + u - v, c + u + v, c - u + v])


def caja(x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    """Rectángulo alineado con los ejes, esquinas en sentido antihorario."""
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=float)


def test_area_de_rectangulos_girados():
    assert area(caja(0, 0, 1, 1)) == 1.0
    assert area(rect(5, -3, 4, 2, 30)) == pytest.approx(8.0)
    assert area(rect(5, -3, 4, 2, 30)[::-1]) == pytest.approx(8.0)  # sentido horario


def test_interseccion_de_cuadrados_solapados_un_cuarto():
    # [0,2]² ∩ [1,3]² = [1,2]², área 1.
    assert interseccion(caja(0, 0, 2, 2), caja(1, 1, 3, 3)) == pytest.approx(1.0)


def test_interseccion_no_depende_del_sentido_de_las_esquinas():
    p, q = caja(0, 0, 2, 2), caja(1, 1, 3, 3)
    for a in (p, p[::-1]):
        for b in (q, q[::-1]):
            assert interseccion(a, b) == pytest.approx(1.0)


def test_interseccion_de_cajas_separadas_es_cero():
    assert interseccion(caja(0, 0, 1, 1), caja(5, 5, 6, 6)) == 0.0


def test_interseccion_de_caja_contenida_es_su_area():
    assert interseccion(caja(0, 0, 10, 10), caja(2, 3, 4, 7)) == pytest.approx(8.0)
    assert interseccion(caja(2, 3, 4, 7), caja(0, 0, 10, 10)) == pytest.approx(8.0)


def test_interseccion_de_un_cuadrado_con_su_giro_de_45_grados():
    # Dos cuadrados de lado a con el mismo centro, uno girado 45°: el área común es un
    # octógono regular de área 2·a²·(√2 − 1).
    a = 2.0
    esperado = 2 * a * a * (math.sqrt(2) - 1)
    assert interseccion(rect(1, 1, a, a), rect(1, 1, a, a, 45)) == pytest.approx(esperado)


def test_interseccion_de_dos_rectangulos_en_cruz():
    # 10 × 2 y el mismo girado 90°: el área común es el cuadrado central de 2 × 2.
    assert interseccion(rect(0, 0, 10, 2), rect(0, 0, 10, 2, 90)) == pytest.approx(4.0)
    # Y la cruz girada 30° entera da lo mismo.
    assert interseccion(rect(0, 0, 10, 2, 30), rect(0, 0, 10, 2, 120)) == pytest.approx(4.0)


def test_iou_de_cajas_iguales_es_uno():
    p = rect(3, 4, 40, 35, 17)
    assert iou(p, p) == pytest.approx(1.0)


def test_iou_de_la_cruz():
    # Intersección 4, unión 20 + 20 − 4 = 36.
    assert iou(rect(0, 0, 10, 2, 30), rect(0, 0, 10, 2, 120)) == pytest.approx(1 / 9)


def test_iou_exactamente_un_medio():
    # [0,3]×[0,1] y [1,4]×[0,1]: intersección 2, unión 4.
    assert iou(caja(0, 0, 3, 1), caja(1, 0, 4, 1)) == 0.5


def test_iou_de_caja_degenerada_es_cero():
    plana = np.array([[0, 0], [1, 0], [1, 0], [0, 0]], dtype=float)
    assert iou(plana, plana) == 0.0


def test_matriz_iou():
    a = np.stack([caja(0, 0, 3, 1), caja(10, 10, 11, 11)])
    b = np.stack([caja(1, 0, 4, 1), caja(0, 0, 3, 1), caja(50, 50, 51, 51)])
    m = matriz_iou(a, b)
    assert m.shape == (2, 3)
    np.testing.assert_allclose(m, [[0.5, 1.0, 0.0], [0.0, 0.0, 0.0]])
    assert matriz_iou(np.zeros((0, 4, 2)), b).shape == (0, 3)
    assert matriz_iou(a, []).shape == (2, 0)


def test_longitud_anchura():
    assert longitud_anchura(rect(0, 0, 38, 4, 63)) == pytest.approx((38, 4))
    assert longitud_anchura(rect(0, 0, 4, 38, 63)) == pytest.approx((38, 4))
