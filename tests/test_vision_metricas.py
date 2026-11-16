"""Tests de `avion_osint.vision.metricas` con cajas sintéticas calculables a mano.

Las cajas están en metros. Las de imágenes distintas o del mismo caso se ponen lejos
unas de otras para que no se solapen salvo cuando se busca.
"""

import numpy as np
import pytest
from test_vision_geometria import caja, rect

from avion_osint.vision.metricas import (
    Imagen,
    categoria_tamano,
    emparejar,
    error_caja,
    error_conteo,
    exhaustividad_por_categoria,
    metricas_con_umbral,
    precision_media,
)

VACIA = np.zeros((0, 4, 2))


def imagen(detecciones, confianzas, etiquetas) -> Imagen:
    return Imagen(
        np.array(detecciones, dtype=float).reshape(-1, 4, 2),
        np.array(confianzas, dtype=float),
        np.array(etiquetas, dtype=float).reshape(-1, 4, 2),
    )


# ---------------------------------------------------------------- emparejar


def test_emparejar_va_de_mayor_a_menor_confianza():
    etiqueta = caja(0, 0, 3, 1)
    exacta, desplazada = caja(0, 0, 3, 1), caja(1, 0, 4, 1)  # IoU 1 y 0,5
    # La desplazada tiene más confianza: se queda la etiqueta aunque la otra solape más.
    pareja = emparejar(np.stack([exacta, desplazada]), [0.6, 0.9], np.stack([etiqueta]), 0.5)
    assert pareja.tolist() == [-1, 0]


def test_emparejar_elige_la_etiqueta_libre_de_mayor_iou():
    etiquetas = np.stack([caja(1, 0, 4, 1), caja(0, 0, 3, 1)])
    pareja = emparejar(np.stack([caja(0, 0, 3, 1)]), [0.9], etiquetas, 0.5)
    assert pareja.tolist() == [1]


def test_emparejar_dos_detecciones_sobre_la_misma_etiqueta():
    etiqueta = rect(0, 0, 40, 35, 20)
    pareja = emparejar(np.stack([etiqueta, etiqueta]), [0.8, 0.9], np.stack([etiqueta]), 0.5)
    assert pareja.tolist() == [-1, 0]  # la segunda (0,9) acierta; la primera sobra


def test_emparejar_iou_exactamente_en_el_umbral():
    det, etq = np.stack([caja(1, 0, 4, 1)]), np.stack([caja(0, 0, 3, 1)])  # IoU = 0,5
    assert emparejar(det, [0.9], etq, 0.5).tolist() == [0]
    assert emparejar(det, [0.9], etq, 0.55).tolist() == [-1]


def test_emparejar_cajas_giradas():
    etq = np.stack([rect(0, 0, 40, 6, 30)])
    assert emparejar(np.stack([rect(0, 0, 40, 6, 30)]), [0.9], etq, 0.5).tolist() == [0]
    # La misma caja girada 90°: IoU = 36 / (240 + 240 − 36) ≈ 0,08.
    assert emparejar(np.stack([rect(0, 0, 40, 6, 120)]), [0.9], etq, 0.5).tolist() == [-1]


def test_emparejar_sin_detecciones_o_sin_etiquetas():
    assert emparejar(VACIA, [], np.stack([caja(0, 0, 1, 1)]), 0.5).tolist() == []
    assert emparejar(np.stack([caja(0, 0, 1, 1)]), [0.9], VACIA, 0.5).tolist() == [-1]


# ---------------------------------------------------------------- precision_media


def test_ap_deteccion_perfecta():
    etiquetas = [rect(0, 0, 40, 35, 10), rect(200, 0, 15, 12, 80)]
    imagenes = [
        imagen(etiquetas, [0.9, 0.7], etiquetas),
        imagen(etiquetas[:1], [0.5], etiquetas[:1]),
    ]
    assert precision_media(imagenes) == {"ap50": 1.0, "ap50_95": 1.0}


def test_ap_sin_detecciones_es_cero():
    imagenes = [imagen(VACIA, [], [caja(0, 0, 40, 35)])]
    assert precision_media(imagenes) == {"ap50": 0.0, "ap50_95": 0.0}


def test_ap_sin_etiquetas_no_esta_definida():
    imagenes = [imagen([caja(0, 0, 40, 35)], [0.9], VACIA)]
    assert precision_media(imagenes) == {"ap50": None, "ap50_95": None}


def test_ap_con_la_mitad_encontrada():
    # 2 etiquetas, 1 acierto con precisión 1: la exhaustividad llega a 0,5. Con 101 puntos,
    # r = 0; 0,01; …; 0,50 (51 puntos) valen 1 y los demás 0.
    imagenes = [imagen([caja(0, 0, 40, 35)], [0.9], [caja(0, 0, 40, 35), caja(100, 0, 140, 35)])]
    assert precision_media(imagenes)["ap50"] == pytest.approx(51 / 101)


def test_ap_con_falsa_alarma_de_mas_confianza():
    # Primero una falsa alarma (0,9) y luego el acierto (0,8): la única exhaustividad
    # alcanzada (1) se consigue con precisión 1/2, así que la envolvente vale 0,5 en todo.
    imagenes = [
        imagen([caja(100, 0, 140, 35), caja(0, 0, 40, 35)], [0.9, 0.8], [caja(0, 0, 40, 35)])
    ]
    assert precision_media(imagenes)["ap50"] == pytest.approx(0.5)


def test_ap_dos_detecciones_sobre_la_misma_etiqueta():
    # La segunda es falsa alarma, pero llega después de alcanzar exhaustividad 1 con
    # precisión 1: no baja el AP.
    e = caja(0, 0, 40, 35)
    assert precision_media([imagen([e, e], [0.9, 0.8], [e])])["ap50"] == 1.0


def test_ap_varias_imagenes_se_ordenan_juntas():
    # Imagen 1: acierto con 0,9. Imagen 2: falsa alarma con 0,8 y acierto con 0,7.
    # Orden global: A(0,9) F(0,8) A(0,7). Exhaustividad 0,5 con precisión 1; exhaustividad 1
    # con precisión 2/3. AP = (51 · 1 + 50 · 2/3) / 101.
    e = caja(0, 0, 40, 35)
    imagenes = [imagen([e], [0.9], [e]), imagen([caja(100, 0, 140, 35), e], [0.8, 0.7], [e])]
    assert precision_media(imagenes)["ap50"] == pytest.approx((51 + 50 * 2 / 3) / 101)


def test_ap50_95_con_iou_en_el_umbral_de_050():
    # IoU = 0,5 justo: acierta solo con el umbral 0,50 (1 de 10).
    imagenes = [imagen([caja(1, 0, 4, 1)], [0.9], [caja(0, 0, 3, 1)])]
    assert precision_media(imagenes) == {"ap50": 1.0, "ap50_95": pytest.approx(0.1)}


def test_ap50_95_con_iou_intermedio():
    # Largo 10, desplazada 1: IoU = 9 / 11 ≈ 0,818. Acierta con 0,50 … 0,80 (7 de 10).
    imagenes = [imagen([caja(1, 0, 11, 1)], [0.9], [caja(0, 0, 10, 1)])]
    assert precision_media(imagenes)["ap50_95"] == pytest.approx(0.7)


# ---------------------------------------------------------------- metricas_con_umbral


def test_metricas_deteccion_perfecta():
    e = [rect(0, 0, 40, 35, 10), rect(200, 0, 30, 28, 60)]
    m = metricas_con_umbral([imagen(e, [0.9, 0.6], e), imagen(e, [0.8, 0.7], e)], 0.5)
    assert (m["aciertos"], m["falsas_alarmas"], m["fallos"]) == (4, 0, 0)
    assert m["precision"] == m["exhaustividad"] == m["f1"] == 1.0
    assert m["precision_ic95"] == m["exhaustividad_ic95"] == m["f1_ic95"] == (1.0, 1.0)


def test_metricas_sin_detecciones():
    m = metricas_con_umbral([imagen(VACIA, [], [caja(0, 0, 40, 35)])], 0.5)
    assert (m["aciertos"], m["falsas_alarmas"], m["fallos"]) == (0, 0, 1)
    assert m["precision"] is None and m["precision_ic95"] is None
    assert m["exhaustividad"] == 0.0 and m["f1"] == 0.0


def test_metricas_sin_etiquetas():
    m = metricas_con_umbral([imagen([caja(0, 0, 40, 35)], [0.9], VACIA)], 0.5)
    assert (m["aciertos"], m["falsas_alarmas"], m["fallos"]) == (0, 1, 0)
    assert m["precision"] == 0.0 and m["f1"] == 0.0
    assert m["exhaustividad"] is None and m["exhaustividad_ic95"] is None


def test_metricas_con_falsas_alarmas_y_umbral_de_confianza():
    e = caja(0, 0, 40, 35)
    im = imagen([caja(100, 0, 140, 35), e, caja(300, 0, 340, 35)], [0.9, 0.8, 0.3], [e])
    m = metricas_con_umbral([im], 0.5)  # la de 0,3 no cuenta
    assert (m["aciertos"], m["falsas_alarmas"], m["fallos"]) == (1, 1, 0)
    assert m["precision"] == 0.5 and m["exhaustividad"] == 1.0
    assert m["f1"] == pytest.approx(2 / 3)
    m = metricas_con_umbral([im], 0.85)  # solo queda la falsa alarma
    assert (m["aciertos"], m["falsas_alarmas"], m["fallos"]) == (0, 1, 1)
    assert m["precision"] == m["exhaustividad"] == m["f1"] == 0.0


def test_metricas_umbral_de_confianza_incluye_el_valor_exacto():
    e = caja(0, 0, 40, 35)
    assert metricas_con_umbral([imagen([e], [0.5], [e])], 0.5)["aciertos"] == 1


def test_bootstrap_remuestrea_imagenes_no_cajas():
    # Imagen A: 3 etiquetas encontradas. Imagen B: 1 etiqueta sin encontrar.
    # Por imágenes, un remuestreo {B, B} (probabilidad 1/4) da exhaustividad 0, así que el
    # percentil 2,5 es 0. Remuestreando las 4 cajas, 0 solo saldría con probabilidad
    # (1/4)⁴ ≈ 0,4 % y el percentil 2,5 sería 0,25.
    a = [caja(100 * i, 0, 100 * i + 40, 35) for i in range(3)]
    imagenes = [imagen(a, [0.9] * 3, a), imagen(VACIA, [], [caja(0, 0, 40, 35)])]
    m = metricas_con_umbral(imagenes, 0.5)
    assert m["exhaustividad"] == 0.75
    assert m["exhaustividad_ic95"] == (0.0, 1.0)


def test_bootstrap_reproducible_con_la_semilla():
    e = caja(0, 0, 40, 35)
    imagenes = [imagen([e], [0.9], [e]), imagen(VACIA, [], [e]), imagen([e], [0.9], VACIA)] * 3
    assert metricas_con_umbral(imagenes, 0.5) == metricas_con_umbral(imagenes, 0.5)
    a = metricas_con_umbral(imagenes, 0.5, n_remuestreos=50, semilla=1)
    b = metricas_con_umbral(imagenes, 0.5, n_remuestreos=50, semilla=2)
    assert a["f1"] == b["f1"]
    lo, hi = a["f1_ic95"]
    assert lo <= a["f1"] <= hi


# ---------------------------------------------------------------- por categoría


@pytest.mark.parametrize(
    ("longitud", "categoria"),
    [
        (19.99, "ligero"),
        (20.0, "regional"),
        (29.99, "regional"),
        (30.0, "pasillo_unico"),
        (45.0, "pasillo_unico"),
        (45.01, "fuselaje_ancho"),
    ],
)
def test_categoria_tamano_limites_d19(longitud, categoria):
    assert categoria_tamano(longitud) == categoria


def test_exhaustividad_por_categoria():
    # Etiquetas de 15 (ligero), 22 (regional), 30 y 45 (pasillo_unico) m, giradas; solo se
    # encuentra la de 30 m. Ninguna de fuselaje ancho.
    etiquetas = [
        rect(0, 0, 15, 14, 30),
        rect(100, 0, 22, 20, 30),
        rect(200, 0, 30, 28, 30),
        rect(300, 0, 45, 40, 30),
    ]
    falsa = rect(500, 0, 60, 60)  # una falsa alarma no cambia nada por categoría
    r = exhaustividad_por_categoria([imagen([etiquetas[2], falsa], [0.9, 0.9], etiquetas)], 0.5)
    assert r["ligero"] == {
        "n_etiquetas": 1,
        "aciertos": 0,
        "exhaustividad": 0.0,
        "exhaustividad_ic95": (0.0, 0.0),
    }
    assert r["regional"]["exhaustividad"] == 0.0
    assert r["pasillo_unico"]["n_etiquetas"] == 2
    assert r["pasillo_unico"]["exhaustividad"] == 0.5
    assert r["fuselaje_ancho"] == {
        "n_etiquetas": 0,
        "aciertos": 0,
        "exhaustividad": None,
        "exhaustividad_ic95": None,
    }


# ---------------------------------------------------------------- conteo y caja


def test_error_conteo_con_signo():
    e = caja(0, 0, 40, 35)
    sobra = imagen([e, caja(100, 0, 140, 35)], [0.9, 0.6], [e])
    falta = imagen(VACIA, [], [e, caja(100, 0, 140, 35)])
    assert error_conteo([sobra], 0.5) == 1
    assert error_conteo([sobra], 0.7) == 0
    assert error_conteo([falta], 0.5) == -2
    assert error_conteo([sobra, falta], 0.5) == -1  # aeropuerto con las dos imágenes


def test_error_caja_en_los_aciertos():
    # Etiqueta 40 × 3 m; detección 42 × 2,9 m, mismo centro y giro (IoU ≈ 0,89).
    # La falsa alarma no cuenta.
    for angulo in (0, 30, 135):
        etq = rect(10, 20, 40, 3, angulo)
        det = rect(10, 20, 42, 2.9, angulo)
        im = imagen([det, rect(500, 0, 40, 3)], [0.9, 0.9], [etq])
        r = error_caja([im], 0.5)
        np.testing.assert_allclose(r["error_longitud_m"], [2.0])
        np.testing.assert_allclose(r["error_anchura_m"], [-0.1], atol=1e-9)


def test_error_caja_sin_aciertos_esta_vacio():
    r = error_caja([imagen(VACIA, [], [caja(0, 0, 40, 35)])], 0.5)
    assert len(r["error_longitud_m"]) == 0 and len(r["error_anchura_m"]) == 0
