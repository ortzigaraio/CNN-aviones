"""Métricas del detector de aviones (docs/specs/fase-2.md, sección 6), de una sola clase.

Cada imagen evaluada es un `Imagen(detecciones, confianzas, etiquetas)`: cajas orientadas
(n, 4, 2) y (m, 4, 2) con sus cuatro esquinas, y la confianza de cada detección. Las
métricas por tamaño y la calidad de la caja necesitan las esquinas **en metros** (si están
en píxeles, multiplicarlas antes por el GSD, el tamaño en metros de un píxel).

Convenciones (anotadas en docs/specs/fase-2-dudas.md):
* Una detección acierta si su IoU con una etiqueta libre es **mayor o igual** que el umbral.
* Con un umbral de confianza, cuentan las detecciones con confianza **mayor o igual**.
* Las métricas con umbral de confianza emparejan con IoU ≥ 0,5 salvo que se diga otro.
* Un cociente con denominador 0 (p. ej. precisión sin detecciones) es None.
"""

from typing import NamedTuple

import numpy as np

from avion_osint.vision.geometria import longitud_anchura, matriz_iou

UMBRALES_AP50_95 = tuple(round(0.50 + 0.05 * i, 2) for i in range(10))  # 0,50 … 0,95
CATEGORIAS = ("ligero", "regional", "pasillo_unico", "fuselaje_ancho")


class Imagen(NamedTuple):
    detecciones: np.ndarray  # (n, 4, 2)
    confianzas: np.ndarray  # (n,)
    etiquetas: np.ndarray  # (m, 4, 2)


def _cajas(c) -> np.ndarray:
    return np.asarray(c, dtype=float).reshape(-1, 4, 2)


def categoria_tamano(longitud_m: float) -> str:
    """Categoría por longitud (D19): < 20 ligero, [20, 30) regional, [30, 45] pasillo_unico,
    > 45 fuselaje_ancho."""
    if longitud_m < 20:
        return "ligero"
    if longitud_m < 30:
        return "regional"
    if longitud_m <= 45:
        return "pasillo_unico"
    return "fuselaje_ancho"


def _emparejar_iou(iou: np.ndarray, confianzas: np.ndarray, umbral_iou: float) -> np.ndarray:
    """Como `emparejar`, a partir de la matriz de IoU (detecciones × etiquetas)."""
    pareja = np.full(iou.shape[0], -1)
    libre = np.ones(iou.shape[1], dtype=bool)
    # Orden estable: con confianzas iguales, manda el orden de entrada.
    for i in np.argsort(-np.asarray(confianzas, dtype=float), kind="stable"):
        if not libre.any():
            break
        candidatas = np.where(libre, iou[i], -1.0)
        j = int(np.argmax(candidatas))
        if candidatas[j] >= umbral_iou:
            pareja[i] = j
            libre[j] = False
    return pareja


def emparejar(detecciones, confianzas, etiquetas, umbral_iou: float) -> np.ndarray:
    """Para cada detección, índice de la etiqueta con la que acierta, o -1 si es falsa alarma.

    De mayor a menor confianza, cada detección se queda con la etiqueta todavía libre de
    mayor IoU, si ese IoU es ≥ umbral_iou. Una etiqueta acierta como mucho con una detección
    (las demás que caigan sobre ella son falsas alarmas). Mismo criterio que COCO.
    """
    iou = matriz_iou(_cajas(detecciones), _cajas(etiquetas))
    return _emparejar_iou(iou, confianzas, umbral_iou)


def _emparejar_con_umbral(im: Imagen, umbral_conf: float, umbral_iou: float):
    """(detecciones con confianza ≥ umbral_conf, etiquetas, `emparejar` entre ambas)."""
    confianzas = np.asarray(im.confianzas, dtype=float)
    elegidas = confianzas >= umbral_conf
    detecciones, etiquetas = _cajas(im.detecciones)[elegidas], _cajas(im.etiquetas)
    return (
        detecciones,
        etiquetas,
        emparejar(detecciones, confianzas[elegidas], etiquetas, umbral_iou),
    )


def _precision_media(aciertos: np.ndarray, confianzas: np.ndarray, n_etiquetas: int) -> float:
    """AP con la interpolación de 101 puntos de COCO (ver `precision_media`)."""
    orden = np.argsort(-confianzas, kind="stable")
    tp = np.cumsum(aciertos[orden])
    exhaustividad = tp / n_etiquetas
    precision = tp / np.arange(1, len(tp) + 1)
    # Envolvente: precisión máxima a exhaustividad igual o mayor.
    envolvente = np.maximum.accumulate(precision[::-1])[::-1]
    puntos = np.linspace(0, 1, 101)
    k = np.searchsorted(exhaustividad, puntos, side="left")
    return float(np.mean([envolvente[i] if i < len(envolvente) else 0.0 for i in k]))


def precision_media(imagenes: list[Imagen]) -> dict:
    """AP50 y AP50-95 (precisión media), de una sola clase, sobre todas las imágenes juntas.

    Para cada umbral de IoU se emparejan las detecciones de cada imagen (`emparejar`), se
    ordenan todas por confianza y se recorre la curva precisión-exhaustividad. La curva se
    resume con la **interpolación de 101 puntos de COCO**: en cada exhaustividad r = 0;
    0,01; …; 1 se toma la precisión máxima alcanzada con exhaustividad ≥ r (0 si no se
    llega a r), y AP es la media de esos 101 valores. Puede diferir un poco del AP que da
    Ultralytics, que integra la misma curva por trapecios.

    AP50 usa IoU ≥ 0,50; AP50-95 es la media de los AP con IoU 0,50, 0,55, …, 0,95.
    Devuelve {"ap50", "ap50_95"}; None si no hay ninguna etiqueta.
    """
    n_etiquetas = sum(len(_cajas(im.etiquetas)) for im in imagenes)
    if n_etiquetas == 0:
        return {"ap50": None, "ap50_95": None}
    ious = [matriz_iou(_cajas(im.detecciones), _cajas(im.etiquetas)) for im in imagenes]
    confianzas = np.concatenate([np.asarray(im.confianzas, dtype=float) for im in imagenes])
    aps = []
    for umbral in UMBRALES_AP50_95:
        aciertos = np.concatenate(
            [
                _emparejar_iou(iou, im.confianzas, umbral) >= 0
                for iou, im in zip(ious, imagenes, strict=True)
            ]
        ).astype(float)
        aps.append(_precision_media(aciertos, confianzas, n_etiquetas))
    return {"ap50": aps[0], "ap50_95": float(np.mean(aps))}


def _cociente(a, b):
    return a / b if b else None


def _intervalo(valores: np.ndarray) -> tuple[float, float] | None:
    """Intervalo del 95 % por percentiles; los remuestreos sin valor (NaN) no cuentan."""
    valores = valores[~np.isnan(valores)]
    if len(valores) == 0:
        return None
    return float(np.percentile(valores, 2.5)), float(np.percentile(valores, 97.5))


def _remuestreos(n_imagenes: int, n_remuestreos: int, semilla: int) -> np.ndarray:
    """Índices de imágenes sacadas con reemplazo: (n_remuestreos, n_imagenes)."""
    return np.random.default_rng(semilla).integers(0, n_imagenes, (n_remuestreos, n_imagenes))


def metricas_con_umbral(
    imagenes: list[Imagen],
    umbral_conf: float,
    umbral_iou: float = 0.5,
    n_remuestreos: int = 1000,
    semilla: int = 0,
) -> dict:
    """Precisión, exhaustividad y F1 con las detecciones de confianza ≥ umbral_conf.

    F1 = 2·aciertos / (2·aciertos + falsas alarmas + fallos), que es la media armónica de
    precisión y exhaustividad y vale 0 (no None) si hay etiquetas pero ninguna detección.

    Intervalos del 95 % por remuestreo de imágenes (bootstrap por percentiles): se sacan
    n_remuestreos conjuntos de imágenes con reemplazo, del mismo tamaño que el original, se
    suman sus aciertos, falsas alarmas y fallos, y se toman los percentiles 2,5 y 97,5.

    Devuelve {"aciertos", "falsas_alarmas", "fallos", "precision", "exhaustividad", "f1",
    "precision_ic95", "exhaustividad_ic95", "f1_ic95"}.
    """
    conteos = []  # por imagen: aciertos, falsas alarmas, fallos
    for im in imagenes:
        _, etiquetas, pareja = _emparejar_con_umbral(im, umbral_conf, umbral_iou)
        tp = int((pareja >= 0).sum())
        conteos.append((tp, len(pareja) - tp, len(etiquetas) - tp))
    conteos = np.array(conteos, dtype=float).reshape(-1, 3)
    tp, fp, fn = conteos.sum(axis=0)
    p, r, f1 = _cociente(tp, tp + fp), _cociente(tp, tp + fn), _cociente(2 * tp, 2 * tp + fp + fn)

    sumas = conteos[_remuestreos(len(conteos), n_remuestreos, semilla)].sum(axis=1)
    btp, bfp, bfn = sumas[:, 0], sumas[:, 1], sumas[:, 2]
    with np.errstate(invalid="ignore", divide="ignore"):
        bp = btp / (btp + bfp)
        br = btp / (btp + bfn)
        bf1 = 2 * btp / (2 * btp + bfp + bfn)
    return {
        "aciertos": int(tp),
        "falsas_alarmas": int(fp),
        "fallos": int(fn),
        "precision": p,
        "exhaustividad": r,
        "f1": f1,
        "precision_ic95": _intervalo(bp),
        "exhaustividad_ic95": _intervalo(br),
        "f1_ic95": _intervalo(bf1),
    }


def exhaustividad_por_categoria(
    imagenes: list[Imagen],
    umbral_conf: float,
    umbral_iou: float = 0.5,
    n_remuestreos: int = 1000,
    semilla: int = 0,
) -> dict:
    """Exhaustividad por categoría de tamaño de la etiqueta (`categoria_tamano` de su lado
    mayor, en metros), con intervalo del 95 % por remuestreo de imágenes como en
    `metricas_con_umbral`. El emparejamiento se hace con todas las detecciones a la vez.

    No hay precisión por categoría: una falsa alarma no tiene etiqueta y, por tanto, no
    tiene categoría.

    Devuelve {categoria: {"n_etiquetas", "aciertos", "exhaustividad", "exhaustividad_ic95"}}
    para las cuatro categorías.
    """
    conteos = np.zeros((len(imagenes), len(CATEGORIAS), 2))  # aciertos, etiquetas
    for k, im in enumerate(imagenes):
        _, etiquetas, pareja = _emparejar_con_umbral(im, umbral_conf, umbral_iou)
        acertadas = set(pareja[pareja >= 0].tolist())
        for j, caja in enumerate(etiquetas):
            c = CATEGORIAS.index(categoria_tamano(longitud_anchura(caja)[0]))
            conteos[k, c, 0] += j in acertadas
            conteos[k, c, 1] += 1

    sumas = conteos[_remuestreos(len(conteos), n_remuestreos, semilla)].sum(axis=1)
    resultado = {}
    for c, nombre in enumerate(CATEGORIAS):
        tp, n = conteos[:, c, :].sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            br = sumas[:, c, 0] / sumas[:, c, 1]
        resultado[nombre] = {
            "n_etiquetas": int(n),
            "aciertos": int(tp),
            "exhaustividad": _cociente(tp, n),
            "exhaustividad_ic95": _intervalo(br) if n else None,
        }
    return resultado


def error_conteo(imagenes: list[Imagen], umbral_conf: float) -> int:
    """Detecciones con confianza ≥ umbral_conf menos etiquetas, sumadas sobre las imágenes
    dadas (una imagen, o todas las de un aeropuerto). Positivo = sobran detecciones."""
    detectadas = sum(int((np.asarray(im.confianzas) >= umbral_conf).sum()) for im in imagenes)
    return detectadas - sum(len(_cajas(im.etiquetas)) for im in imagenes)


def error_caja(imagenes: list[Imagen], umbral_conf: float, umbral_iou: float = 0.5) -> dict:
    """En cada acierto (confianza ≥ umbral_conf, IoU ≥ umbral_iou): longitud y anchura de la
    detección menos las de la etiqueta, en metros (lado mayor y lado menor de cada caja).

    Devuelve {"error_longitud_m": array, "error_anchura_m": array}, un valor con signo por
    acierto.
    """
    longitud, anchura = [], []
    for im in imagenes:
        detecciones, etiquetas, pareja = _emparejar_con_umbral(im, umbral_conf, umbral_iou)
        for i, j in enumerate(pareja):
            if j >= 0:
                ld, ad = longitud_anchura(detecciones[i])
                le, ae = longitud_anchura(etiquetas[j])
                longitud.append(ld - le)
                anchura.append(ad - ae)
    return {"error_longitud_m": np.array(longitud), "error_anchura_m": np.array(anchura)}
