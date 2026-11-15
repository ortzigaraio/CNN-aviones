# Fase 2 — Detector de aviones

Especificación de Fable para Opus. Leer antes `CLAUDE.md`, `docs/encargo.md` (sección 4, «Visión»), `docs/licencias.md` y las decisiones D9 a D16.

**Estado: borrador.** Se cierra cuando se conozca el resultado del detector preentrenado en la Fase 1b (sección 9). Lo que no depende de eso ya se puede preparar.

## 1. Objetivo

Un detector de aviones con cajas orientadas (rectángulos que giran para ajustarse al avión) y, sobre todo, una medida honesta de cuánto empeora al pasar de las imágenes con las que se entrenó a las ortofotos PNOA.

Pregunta que responde: **¿cuántos aviones de una ortofoto PNOA encuentra el detector, cuántas falsas alarmas da, y cuánto de eso se debe al cambio de dominio?**

*Cambio de dominio* = el modelo empeora con imágenes distintas de las de entrenamiento (otro sensor, otra resolución, otra luz).

## 2. Restricciones

* **GPU:** RTX 3070 de 8 GB, en el PC del autor (D14). Kaggle como reserva. Todo se dimensiona para 8 GB: modelo pequeño (`s`), teselas de 1.024 px, lote de 4 a 8.
* **Licencias:** DOTA y DIOR, uso académico o no comercial. **FAIR1M y xView no se usan** mientras su licencia no esté clara (`docs/licencias.md`). Los modelos resultantes son de uso no comercial (D15).
* **Quién ejecuta:** el entrenamiento lo lanza el autor en su PC con un comando. Opus deja el comando y lo prueba antes en CPU con una fracción mínima de datos, solo para ver que arranca y termina.

## 3. Datos

| Conjunto | Origen | Uso |
|---|---|---|
| DOTA v1.0, solo clase `plane` | Descarga oficial | Entrenar y validar en origen. |
| DIOR-R, solo clase `airplane` | Descarga oficial | Ampliar el entrenamiento (experimento opcional). |
| PNOA-ajuste | Aeropuertos civiles **que no están** en la Fase 4 | Ajuste fino (experimento C). |
| PNOA-desarrollo | LEMD 2023 (la foto de la Fase 1b) | Elegir el umbral de confianza y comparar experimentos. |
| PNOA-prueba | LEPA 2024 y LEBL 2018 | Resultado final. Se mira **una sola vez**, al final. |

### Etiquetado de PNOA

* **PNOA-desarrollo:** el conteo manual de la Fase 1b da puntos. Se convierten en cajas orientadas con etiquetado asistido (el detector propone la caja y una persona la corrige) **después** de cerrar la Fase 1b.
* **PNOA-prueba:** etiquetado por el autor, a mano o asistido, sin ver las métricas de ningún experimento.
* **PNOA-ajuste:** etiquetado asistido. Aeropuertos candidatos: Valencia (LEVC), Málaga (LEMG), Alicante (LEAL), Sevilla (LEZL). Aquí no importa que la foto mezcle días. Objetivo: 200-300 aviones.
* Formato de etiquetas: el de cajas orientadas de Ultralytics (cuatro esquinas normalizadas por línea), una sola clase.
* Reglas de etiquetado en `docs/guias/etiquetado-aviones.md`: se etiqueta todo avión de ala fija visible en más de la mitad; no helicópteros; un avión parcialmente bajo una pasarela o un hangar abierto se etiqueta si se ve más de la mitad.

## 4. Partición y por qué no hay fuga

*Fuga de datos* = información de la prueba que se cuela en el entrenamiento y da métricas falsamente buenas.

1. **Por aeropuerto en PNOA.** Ningún aeropuerto aparece en dos conjuntos. Los de ajuste son distintos de los de desarrollo y de prueba. Se comprueba con un test que lee los nombres de las carpetas.
2. **En DOTA:** se usa la partición oficial de entrenamiento y validación (las etiquetas de la prueba oficial no son públicas). DOTA no dice de qué aeropuerto es cada imagen, así que puede haber un mismo aeropuerto a los dos lados. Qué se hace:
   * Comprobación: buscar imágenes casi duplicadas entre entrenamiento y validación (huella perceptual, una firma que se parece cuando las imágenes se parecen) y revisar a mano los 50 pares más parecidos. Reportar cuántos hay.
   * Si hay pares del mismo aeropuerto, se mueven a entrenamiento y se dice.
   * En cualquier caso, la métrica en DOTA se presenta como **techo optimista**. La que cuenta es la de PNOA-prueba, que no comparte nada con el entrenamiento.
3. **Teselas:** cada imagen grande se parte en teselas de 1.024 px **después** de asignarla a un conjunto, nunca antes.
4. **El umbral de confianza** se elige en PNOA-desarrollo y se aplica tal cual a PNOA-prueba.
5. **La foto de LEMD 2023 es de desarrollo** (D9): se puede mirar cuanto haga falta, pero sus métricas no son el resultado.

## 5. Experimentos

| | Modelo | Entrenamiento | Para qué |
|---|---|---|---|
| **A** | Pesos oficiales preentrenados en DOTA (15 clases), sin tocar | Ninguno | Línea base. Es lo que se ejecuta en la Fase 1b. |
| **B** | Mismo modelo, entrenado por nosotros con DOTA, solo aviones | Desde los pesos preentrenados genéricos | Reproducibilidad: un modelo cuyo entrenamiento controlamos entero. |
| **C** | B (o A, si B no lo mejora) con ajuste fino en PNOA-ajuste | Pocas épocas, tasa de aprendizaje baja | Medir cuánto del cambio de dominio se recupera con 200-300 etiquetas. |

Cada experimento se evalúa a resolución nativa (0,25 m) y remuestreado a 0,5 m. Todo se registra en MLflow (herramienta que guarda parámetros, métricas y modelos de cada experimento); semilla fija; un único fichero de configuración por experimento en `config/detector/`.

Sin búsqueda de hiperparámetros: los valores por defecto de la librería, salvo tamaño de imagen y lote. Si alguien quiere cambiar algo más, se anota en dudas.

## 6. Métricas

En cada conjunto de evaluación, por separado (DOTA validación, PNOA-desarrollo, PNOA-prueba):

* **AP50** y **AP50-95** (precisión media con solape de cajas del 50 %, y promediada del 50 % al 95 %).
* Con el umbral fijado: **precisión, exhaustividad y F1**, con intervalo de confianza por remuestreo de imágenes (*bootstrap*).
* Lo mismo **por categoría de tamaño** (`ligero`, `regional`, `pasillo_unico`, `fuselaje_ancho`): los aviones pequeños fallarán más y hay que verlo.
* **Error de conteo** por aeropuerto: detectados menos reales, con signo.
* **Falsas alarmas típicas:** las 30 de mayor confianza, clasificadas a mano (pasarelas, vehículos, marcas del suelo, sombras…).
* **Calidad de la caja:** en los aciertos, error de longitud y de anchura en metros frente a la etiqueta. La Fase 3 depende de esto para medir aviones.

**Cambio de dominio** = diferencia de AP50 y de F1 entre DOTA validación y PNOA-prueba, para A y B. **Recuperación** = cuánto de esa diferencia cierra C.

## 7. Criterios de aceptación

«Hecho» significa:

1. Tabla con todas las métricas de la sección 6 para A, B y C, a las dos resoluciones.
2. Test automático que comprueba que ningún aeropuerto está en dos conjuntos.
3. Informe de la comprobación de duplicados en DOTA.
4. `dvc repro` regenera la evaluación a partir de los pesos; el comando de entrenamiento está documentado y probado.
5. PNOA-prueba se evaluó una sola vez, con el umbral ya fijado, y así consta en el cierre.
6. Checklist de cierre rellenada.

Objetivo orientativo (no es condición para cerrar): en PNOA-prueba, aviones de 20 m o más, exhaustividad ≥ 0,90 con precisión ≥ 0,90. Si no se llega, la Fase 4 sigue adelante, pero el resultado central se presenta separando «el detector no lo vio» de «ADS-B no lo explica».

## 8. Riesgos y qué hacer

| Riesgo | Qué hacer |
|---|---|
| El modelo `s` no cabe en 8 GB a 1.024 px. | Bajar el lote; si no basta, modelo `n`. No bajar el tamaño de imagen sin anotarlo en dudas. |
| B no mejora a A. | Es un resultado. C parte de A. |
| C mejora mucho en desarrollo y no en prueba. | Sobreajuste a los aeropuertos de ajuste; se reporta tal cual. |
| Resultado sorprendentemente bueno en PNOA (F1 > 0,97). | Sospechar fuga: revisar que los aeropuertos de prueba no están en el ajuste y que el umbral no se eligió en prueba. Anotar en dudas antes de darlo por bueno. |
| DOTA tiene aviones a resoluciones muy distintas de 0,25 m. | Por eso se evalúa también a 0,5 m. No se filtra DOTA por resolución sin anotarlo. |
| La caja no distingue morro de cola. | No importa para detectar. Para medir, la Fase 3 decide qué lado es el fuselaje. |
| Etiquetar PNOA lleva más tiempo del previsto. | Prioridad: prueba, luego desarrollo, luego ajuste. Sin ajuste, C no se hace y se dice. |

## 9. Pendiente de la Fase 1b

* Si el detector preentrenado (A) ya encuentra casi todo en LEMD 2023, B y C pesan menos y se puede recortar tiempo.
* Si no encuentra casi nada a resolución nativa pero sí a 0,5 m, el remuestreo pasa a ser el modo normal.
* El resultado de la Fase 1b decide además si la Fase 4 se hace como estaba prevista.

## 10. Tareas para Opus, en orden

1. Guion de preparación de DOTA: filtrar la clase avión, partir en teselas, formato de Ultralytics. Con test sobre tres imágenes de ejemplo.
2. Comprobación de duplicados entre entrenamiento y validación de DOTA.
3. Guion de evaluación con todas las métricas de la sección 6, probado con el experimento A sobre DOTA validación.
4. Herramienta de etiquetado asistido para PNOA y la guía de etiquetado.
5. Configuración y comando de entrenamiento de B; prueba de arranque en CPU.
6. *(Autor)* Entrenar B en su PC. *(Autor)* Etiquetar PNOA.
7. Experimento C.
8. Evaluación final en PNOA-prueba, una sola vez. Cierre.

Fuera de alcance: clasificar el tipo de avión, otras clases de objetos, FAIR1M y xView, búsqueda de hiperparámetros.
