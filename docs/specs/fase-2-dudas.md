# Fase 2: dudas y elecciones de Opus

Anotado por Opus durante la parte de la Fase 2 que no necesita datos ni GPU: el cálculo de las métricas de la sección 6 en `src/avion_osint/vision/` (`geometria.py`, `metricas.py`). En cada punto se dice qué se ha puesto (la opción más conservadora o la más habitual) y qué queda por decidir. Nada de esto es una decisión de diseño tomada.

## Requieren decisión

### 1. No hay precisión por categoría de tamaño

La sección 6 pide «lo mismo por categoría de tamaño», es decir, también precisión y F1. Pero la categoría sale de la longitud de la **etiqueta**, y una falsa alarma no tiene etiqueta: no se sabe a qué categoría restarla. Puesto: solo **exhaustividad por categoría** (`exhaustividad_por_categoria`), con su intervalo por remuestreo. Alternativa, si Fable la quiere: dar a cada falsa alarma la categoría de la longitud de **su propia caja** detectada y calcular así una precisión por categoría (con el aviso de que mezcla dos criterios: aciertos por longitud real, falsas alarmas por longitud estimada). El objetivo orientativo de la sección 7 («aviones de 20 m o más, exhaustividad ≥ 0,90 con precisión ≥ 0,90») necesita una precisión por tamaño, así que esto hay que decidirlo antes de evaluar.

### 2. Umbral de IoU para precisión, exhaustividad, F1, conteo de aciertos y calidad de la caja

La spec dice «con el umbral fijado» (de confianza) pero no con qué solape cuenta un acierto. Puesto: **IoU ≥ 0,5** por defecto (parámetro `umbral_iou`), el mismo que AP50.

### 3. Interpolación de la curva para AP

Puesto: **interpolación de 101 puntos de COCO** (en cada exhaustividad 0; 0,01; …; 1, la precisión máxima alcanzada con exhaustividad igual o mayor; AP es la media). Es una definición estándar y calculable a mano. Ultralytics integra la misma curva envolvente por trapecios sobre esos 101 puntos, así que su `val` puede dar un AP algo distinto. Para la tabla de la Fase 2 se propone usar siempre esta función (no el número de Ultralytics), para que A, B y C se comparen con la misma regla.

### 4. Intervalos por remuestreo (bootstrap)

Puesto: método de **percentiles** (2,5 y 97,5), **1.000 remuestreos**, **semilla 0**, por imagen (cada remuestreo saca tantas imágenes como hay, con reemplazo, y suma sus aciertos, falsas alarmas y fallos). Los remuestreos en los que la métrica no está definida (p. ej. precisión sin ninguna detección, o una categoría sin etiquetas en ese remuestreo) **se descartan**; con muy pocas imágenes esto sesga el intervalo hacia las imágenes que sí tienen casos. Con PNOA-prueba de solo dos aeropuertos y pocas fotos, el remuestreo por imagen tiene muy pocas unidades: si se parten las ortofotos en teselas, ¿la unidad de remuestreo es la tesela o la ortofoto? Puesto en el código: lo que se le pase como «imagen»; la elección es de Fable. (Lo conservador sería la ortofoto entera, con intervalos más anchos.)

### 5. La «longitud» de la caja puede ser la envergadura

`longitud` = lado mayor de la caja y `anchura` = lado menor, como en `scripts/fase_1b/detector.py`. La caja de un avión abarca fuselaje × envergadura, y en algunos aviones la envergadura es mayor que el fuselaje (avionetas, algunos reactores de negocios y turbohélices). Consecuencias: (a) la categoría de tamaño de una etiqueta se asigna por max(fuselaje, envergadura), no por la longitud del fuselaje de D19 y `config/categorias_tipo.yaml`; (b) «error de longitud» y «error de anchura» comparan lado mayor con lado mayor, aunque en la detección y en la etiqueta el lado mayor sea distinto (fuselaje en una, ala en la otra) cuando son casi iguales. Es el mismo riesgo que «La caja no distingue morro de cola» (sección 8), que la spec deja a la Fase 3. Si se quiere la longitud del fuselaje para las categorías, el etiquetado tendría que marcar qué lado es el fuselaje.

### 6. Categorías en DOTA validación

La categoría necesita las esquinas en metros. DOTA da las cajas en píxeles y su GSD por imagen (tamaño en metros de un píxel) debería venir en la cabecera de cada fichero de etiquetas (de memoria, no verificado), pero hay que comprobar que esté en todas: si falta en alguna, esas imágenes no se pueden repartir por categoría. Sin comprobar (no hay datos en el entorno).

## Elecciones menores (avisar si no valen)

* **Acierto en el umbral exacto:** una detección acierta si IoU **≥** umbral (como COCO y Ultralytics). Con un umbral de confianza cuentan las detecciones con confianza **≥** umbral.
* **Emparejamiento:** de mayor a menor confianza, cada detección toma la etiqueta **todavía libre** de mayor IoU (criterio COCO). Si dos detecciones tienen la misma confianza, va primero la que aparece antes en la lista.
* **AP sobre el conjunto:** todas las detecciones de todas las imágenes se ordenan juntas (no se promedia el AP por imagen). Sin ninguna etiqueta, AP es None; con etiquetas y sin detecciones, 0.
* **F1** = 2·aciertos / (2·aciertos + falsas alarmas + fallos): vale 0 si hay etiquetas y ninguna detección (la precisión, en cambio, es None).
* **Exhaustividad por categoría:** el emparejamiento se hace con todas las detecciones a la vez y luego se reparten las etiquetas acertadas por categoría.
* **Error de conteo:** detecciones con confianza ≥ umbral menos etiquetas, sumado sobre las imágenes que se pasen (una imagen, o todas las de un aeropuerto).
* **Calidad de la caja:** `error_caja` devuelve el error con signo (detección − etiqueta) de cada acierto, en metros. Qué resumen se reporta en la tabla (media, mediana, error absoluto medio, percentiles) no está decidido; no se ha calculado ninguno.
* La intersección de cajas se ha movido tal cual de `scripts/fase_1b/detector.py` a `avion_osint.vision.geometria` (solo se ha añadido un docstring a `area`); el guion la importa de ahí. `iou` añade el mismo tope que usaba el guion (la intersección nunca supera el área de la menor) y da 0 si la unión no tiene área. El guion no se ha vuelto a ejecutar.
* `numpy` se ha declarado como dependencia directa (`numpy>=2.5.4`, la versión que ya estaba en `uv.lock` a través de pandas).
