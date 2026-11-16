# Fase 3 — Tamaño y tipo de avión

Especificación de Fable para Opus. Leer antes `CLAUDE.md`, `docs/encargo.md` (sección 4, «Visión», puntos 3 a 5), `docs/revisiones/encargo.md` (punto 1), `docs/licencias.md` y las decisiones D14, D15, D19 y D29.

**Estado: borrador.** Depende de la calidad de las cajas que mida la Fase 2 (sección 9).

## 1. Objetivo

Decir, para cada avión detectado, **de qué tamaño es** y, cuando se pueda, **de qué tipo**, sabiendo cuánto fiarse de la respuesta.

Se hace en dos niveles (decisión D29):

| Nivel | Qué dice | Con qué | Dónde se valida |
|---|---|---|---|
| **1. Tamaño** (obligatorio) | `ligero`, `regional`, `pasillo_unico`, `fuselaje_ancho` | Medidas de la caja en metros | PNOA, contra el conteo manual y contra ADS-B |
| **2. Tipo** (método) | Uno de 20 tipos, o «desconocido» | Recorte de imagen + medidas | MAR20, el propio conjunto de datos |

Por qué así: el resultado central del proyecto es «% bien clasificado frente a ADS-B en aeropuertos civiles». ADS-B da el tipo de cada avión, y de ahí su tamaño sin ambigüedad. Pero no hay un conjunto de datos de tipos **civiles** que se pueda usar: FAIR1M no tiene licencia localizable. MAR20 son 20 tipos militares; sirve para construir y medir el método, no para validar en aeropuertos civiles.

## 2. Restricciones

* **GPU:** RTX 3070 de 8 GB (D14). Modelo ligero (ConvNeXt-Tiny o EfficientNet-B0), recortes de 224 px, lote de 32 a 64.
* **Licencias:** MAR20 es CC BY-NC 4.0 y solo para investigación. No se redistribuyen imágenes ni recortes; los pesos quedan como no comerciales. **FAIR1M no se usa** mientras su licencia no esté clara.
* **Límites del proyecto:** el clasificador de tipos militares se evalúa **solo dentro de MAR20**. No se aplica a imágenes de aeródromos militares o mixtos para dar tipos de aviones concretos; ahí solo valen conteos agregados (sección 4 de `CLAUDE.md`).

## 3. Nivel 1: tamaño por medidas

### Entradas y salidas

Entrada: una caja orientada del detector, en metros. Salida:

```python
@dataclass
class Medida:
    longitud_m: float        # lado largo de la caja
    envergadura_m: float     # lado corto de la caja
    categoria: str           # ligero | regional | pasillo_unico | fuselaje_ancho
    margen_m: float          # incertidumbre de la longitud
    dudosa: bool             # la longitud ± margen cruza un límite entre categorías

def medir(caja: ndarray, gsd_m: float) -> Medida
```

*GSD* = metros de suelo que cubre cada píxel.

### Decisiones

* **Qué lado es la longitud.** En un avión comercial la longitud y la envergadura (de punta a punta de las alas) se parecen, y la caja no dice cuál es cuál. Regla: se calculan las dos; la categoría se decide con la **mayor** de las dos dimensiones y con límites propios para esa medida, que se obtienen de `config/categorias_tipo.yaml` añadiendo la envergadura de cada tipo. Así no hace falta saber dónde está el morro.
* **Límites.** Los de D19 para la longitud. Los de «dimensión mayor» se derivan de la tabla de tipos, **no** se ajustan con las fotos de prueba.
* **Margen.** `margen_m` = error típico de la caja medido en la Fase 2 (sección 6 de su spec), más un píxel por extremo.
* **Las longitudes de `config/categorias_tipo.yaml` están sin verificar.** Antes de usarlas hay que contrastarlas con una fuente pública citada (fichas del fabricante o la base de tipos de la OACI) y añadir la envergadura. Opus lo propone; se anota la fuente por tipo.

### Línea base

Asignar a todo avión la categoría más frecuente del aeropuerto. Si medir no la supera con claridad, se dice.

## 4. Nivel 2: tipo con MAR20

### Datos y partición

* MAR20: unos 3.800 recortes de imagen con 20 tipos militares, de Google Earth, con cajas orientadas.
* **Riesgo de fuga:** imágenes del mismo aeródromo, o la misma imagen en fechas cercanas, a los dos lados de la partición. Qué se hace:
  1. Si MAR20 dice de qué aeródromo es cada imagen, se parte **por aeródromo**.
  2. Si no lo dice, se agrupan las imágenes casi duplicadas (huella perceptual) y se parte **por grupo**. Se reporta cuántos grupos hay.
  3. La partición oficial se evalúa también, solo para poder compararse con otros trabajos, marcada como «optimista».
* Tres partes: entrenamiento, validación (para elegir épocas y calibrar) y prueba (se mira una vez).
* Los recortes se sacan con la caja de la **etiqueta** para entrenar, y además con la caja del **detector** para evaluar: en uso real la caja no será perfecta.

### Modelo

* Entrada: recorte de 224 px girado para que el lado largo quede horizontal, más dos números (longitud y envergadura en metros).
* Salida: los tres tipos más probables con su confianza.
* **Confianza calibrada:** después de entrenar se ajusta un único número (temperatura) en validación para que «80 % de confianza» signifique acertar 8 de cada 10. Se mide con el error de calibración (ECE).
* **«Desconocido»:** si la confianza más alta no llega a un umbral, la respuesta es «desconocido». El umbral se elige en validación. Se evalúa dejando 4 tipos fuera del entrenamiento y midiendo cuántas veces el modelo los marca como desconocidos.

### Líneas base obligatorias

1. Solo medidas: un clasificador sencillo (árbol o vecinos más cercanos) con longitud y envergadura.
2. Solo imagen: el mismo modelo sin los dos números.

Si el modelo completo no supera claramente a la línea base de solo medidas, **ese es el resultado** y se reporta.

## 5. Métricas

Nivel 1 (en PNOA-desarrollo y PNOA-prueba, por separado):

* Exactitud y F1 por categoría, matriz de confusión, con intervalo de confianza.
* Porcentaje de aviones `dudosa`, y exactitud con y sin ellos.
* Error de longitud en metros frente a la longitud real del tipo que da ADS-B (solo verdad fuerte).

Nivel 2 (en MAR20-prueba):

* Exactitud del primero y de los tres primeros; F1 por tipo; matriz de confusión; los 5 pares de tipos más confundidos.
* ECE antes y después de calibrar.
* Con «desconocido»: porcentaje de tipos no vistos rechazados y porcentaje de tipos vistos rechazados por error.
* Todo, para el modelo completo y las dos líneas base, con caja de etiqueta y con caja de detector.

## 6. Criterios de aceptación

1. Tabla con las métricas de la sección 5.
2. Test automático de que ningún grupo (aeródromo o duplicados) está en dos partes.
3. Las longitudes y envergaduras de la tabla de tipos, con fuente citada.
4. Comparación explícita con las líneas base.
5. Comando para repetir cada experimento; registro en MLflow; semilla fija.
6. Checklist de cierre rellenada.

## 7. Riesgos y qué hacer

| Riesgo | Qué hacer |
|---|---|
| Las cajas del detector en PNOA son imprecisas (error de varios metros). | El nivel 1 da muchos `dudosa`. Se reporta; no se cambian los límites para arreglarlo. |
| Exactitud muy alta en MAR20 (> 0,97). | Sospechar fuga: revisar la partición por grupos antes de darla por buena. Anotar en dudas. |
| MAR20 no se puede descargar. | Se hace solo el nivel 1 y se dice. |
| Sombras que alargan la caja. | Medir el efecto en PNOA-desarrollo comparando con la longitud medida a mano en la Fase 1b. |
| Reactores de negocios en la categoría `regional`. | Previsto en D19; se cuenta aparte. |

## 8. Tareas para Opus, en orden

1. Verificar longitudes y añadir envergaduras en `config/categorias_tipo.yaml`, con fuente por tipo. Proponer en dudas los límites de «dimensión mayor».
2. `medir` con tests (cajas sintéticas, casos en los límites, `dudosa`).
3. Evaluación del nivel 1 sobre el conteo manual de la Fase 1b, cuando exista.
4. Preparación de MAR20: recortes, agrupación de duplicados, partición, test de fuga.
5. Líneas base. Configuración y comando de entrenamiento; prueba de arranque en CPU.
6. *(Autor)* Entrenar en su PC.
7. Calibración, «desconocido», evaluación final y cierre.

Fuera de alcance: tipos civiles finos, FAIR1M, aplicar el clasificador de tipos a aeródromos militares o mixtos reales.

## 9. Pendiente de otras fases

* El error de caja de la Fase 2 fija `margen_m`.
* Si la Fase 1b sale «replantear», el nivel 1 sigue valiendo (no necesita ADS-B para medirse contra el conteo manual), pero pierde la validación contra tipos reales.

## 10. Lo que puede hacer el autor

Escribir a los autores de FAIR1M preguntando por la licencia. Si la aclaran y permite uso académico, se añade un nivel de familias civiles y se revisa esta spec.
