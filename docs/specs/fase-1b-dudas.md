# Fase 1b: dudas y hallazgos para Fable

Anotado por Opus durante la parte de la Fase 1b que no necesita datos (código de `fusion/`, tabla de categorías, `LICENSE` y propuesta de descargas). En cada punto se dice qué se ha hecho (la opción más conservadora) y qué queda por decidir. Nada de esto es una decisión de diseño tomada: todo se puede cambiar.

## Requieren decisión

### 1. La zona norte de Barajas tiene también fotogramas del 26/07/2023

Consultando la Fototeca en una malla más amplia que la de la Fase 0 (hasta 40,525° N), en las dos filas norte aparecen 8 fotogramas del **26/07/2023** (pasada 027) además de los del 28/07. `docs/sitios.md` marcaba LEMD 2023 como «no partido» porque su malla no llegaba tan al norte.

* Con **fotogramas originales** no es problema: se usan solo los del 28/07, que cubren todo el recinto.
* Con la **ortofoto (mosaico)** no se sabe qué fotograma alimenta el extremo norte; podría ser del 26/07. Afecta a D10 y a la fila de LEMD en `docs/sitios.md` (no se ha tocado).

Hecho: la propuesta de descargas solo incluye fotogramas del 28/07. Decide Fable si hay que corregir `docs/sitios.md` y si el mosaico sigue valiendo como alternativa.

### 2. Fotograma original frente a ortofoto

La spec prefiere el fotograma original. Un fotograma no está ortorrectificado (tiene perspectiva y no está orientado al norte), lo que afecta a:

* medir el acimut de las sombras en QGIS (paso A.2): en un fotograma la dirección «norte» no es la de arriba y la perspectiva deforma los ángulos lejos del centro;
* casar posiciones con ADS-B a menos de 100 m (paso A.3) y emparejar detecciones a 15 m (paso C);
* medir `longitud_m`.

No se ha comprobado qué georreferencia trae cada COG. Hecho: nada; se propone bajar primero 2-3 fotogramas para comprobarlo. Decide Fable qué producto se usa para cada paso (p. ej. fotograma para contar, ortofoto para medir), o si se mantiene solo el fotograma.

### 3. `hora_por_sombra` espera el acimut respecto al norte geográfico

La función trabaja con el **norte geográfico** (verdadero). En QGIS sobre una ortofoto en UTM (coordenadas planas por husos), el norte de la cuadrícula no coincide con el geográfico: en Barajas (huso 30) la diferencia, llamada convergencia de meridianos, es de unos 0,36° (calculada como (λ − λ₀)·sen φ = (−3,56° + 3°)·sen 40,47°). Según la hora, eso son de unos segundos a 1-2 minutos. Hecho: la función no corrige nada y su documentación lo dice; la conversión la tendrá que hacer quien mida. Decide Fable si se corrige dentro de la función (habría que pasarle el sistema de coordenadas).

### 4. Adsb.lol da posiciones, no llegadas y salidas

`inferir_en_tierra` recibe llegadas y salidas. adsb.lol (la única fuente ADS-B disponible ahora) da trazas de posiciones. Habrá que deducir aterrizajes y despegues (la spec, sección 8, propone «último punto bajo y lento cerca del aeropuerto»). Es la decisión de diseño que la spec pide anotar aquí para que Fable la valide antes de implementarla. No se ha implementado nada.

### 5. Huecos de cobertura y verdad fuerte

En `inferir_en_tierra`, una salida que falta (el receptor no la captó) hace que el avión parezca seguir en tierra hasta el final de la ventana, y una llegada que falta hace lo mismo hacia atrás. Con eso un avión puede salir como **fuerte** sin haberlo sido, y la `cobertura_fuerte` subiría. Tal como lo describe la spec (nulo = fuera de la ventana), se ha implementado así. Decide Fable si una estancia sin uno de sus extremos debe quedar como débil, o si se exige ver tanto la llegada como la salida.

### 6. Categoría por longitud y grupo «comerciales»

La tabla `config/categorias_tipo.yaml` asigna categoría solo por longitud, como dice la spec. Consecuencias:

* Reactores de negocios de 20-30 m (Gulfstream IV/V, Falcon 7X/900/2000, Challenger) salen como `regional`, y por tanto entran en el grupo **comerciales** del paso E, aunque aparquen en aviación general.
* Embraer 190/195, CRJ900 y Dash 8 Q400 salen como `pasillo_unico`; el B757 como `fuselaje_ancho`.
* Los límites exactos (20, 30 y 45 m) no dicen a qué lado caen. Se ha usado: `ligero` < 20, `regional` de 20 a < 30, `pasillo_unico` de 30 a 45 incluido, `fuselaje_ancho` > 45. Ningún tipo de la tabla cae justo en un límite, pero varios están cerca (marcados en el fichero; p. ej. A321 con 44,51 m, E170 con 29,90 m).

Decide Fable si el grupo comercial se define por categoría (como ahora) o por tipo de operación.

## Elecciones hechas donde la spec no decía (conservadoras, revisables)

### 7. `hora_por_sombra`

* **Fórmula:** algoritmo de la calculadora solar de la NOAA (fórmulas de baja precisión de Meeus, «Astronomical Algorithms»). Error del orden de un minuto. Sin refracción atmosférica.
* **Acimut de la sombra:** dirección desde la base del objeto hacia la punta de la sombra = acimut del sol + 180°.
* **Qué «día» es `fecha`:** el día solar local (de 0 h a 24 h de hora solar media del lugar). En España coincide en la práctica con el día UTC.
* **Solo con el sol sobre el horizonte** (altura > 0°). Si hay **más de una** solución en el día (posible en los trópicos), `ValueError`, como cuando no hay ninguna: no se elige una al azar.
* **Devuelve** un `datetime` con zona horaria UTC (no «ingenuo», sin zona), redondeado al segundo.
* Pasa la fecha por `comprobar_fecha_retrospectiva`. La spec lo pide «antes de descargar nada»; aquí se ha puesto también en esta función porque las normas del proyecto (sección 4, «Límites») piden que todo pipeline pase sus fechas por esa salvaguarda.

### 8. `inferir_en_tierra`

* Columnas de salida: `icao24`, `llegada`, `salida`, `verdad` (fechas con zona UTC). Sin `tipo_oaci` ni `categoria`, como dice la firma.
* «Antes de `t_min − margen`» y «después de `t_max + margen`» son **estrictos**: llegar justo a `t_min − 30 min` da débil.
* Débil = la estancia solapa `[t_min, t_max]` sin cumplir lo anterior. Una estancia que acaba justo en `t_min` o empieza justo en `t_max` no cuenta.
* Un avión sale **una sola vez** (riesgo de contar dos veces, spec sección 8). Si tiene varias estancias que tocan el intervalo, se queda la primera y es débil.
* **Secuencias incoherentes** (dos llegadas seguidas sin salida, o dos salidas seguidas sin llegada): la estancia con un extremo desconocido se descarta. Esto baja `n_adsb`, nunca lo sube.
* Rechaza instantes sin zona horaria y `t_min > t_max`. Pasa `t_max` por `comprobar_fecha_retrospectiva`.

### 9. `comparar_conteos`

* Devuelve `{"por_categoria": {cat: {n_foto, n_adsb, explicados}}, "total": {n_foto, n_adsb, explicados, cobertura, cobertura_ic95, exceso_adsb}}`.
* Intervalo de Wilson al 95 % con z = 1,959963985 (cuantil 0,975 de la normal), escrito a mano.
* Si un denominador es 0, el cociente y su intervalo son `None`.
* Observación (no cambiada): Wilson supone ensayos independientes; `explicados = min(n_foto, n_adsb)` por categoría no lo es del todo. Se implementa como dice la spec.

### 10. Dependencia nueva: `pandas`

La firma de `inferir_en_tierra` usa `DataFrame`, así que se ha añadido `pandas` (3.1.1, que trae `numpy` 2.5.4) a las dependencias de ejecución con `uv add pandas`. No se ha añadido nada más (tampoco `pyarrow` para escribir Parquet; hará falta al generar `en_tierra.parquet`).

### 11. Fichero `LICENSE`

* `https://www.gnu.org/licenses/agpl-3.0.txt` cortaba la conexión desde este entorno; la misma dirección por **HTTP** sí respondió (661 líneas, el tamaño conocido del texto oficial).
* Como HTTP no va cifrado, se ha contrastado con el texto de la lista oficial de licencias SPDX (`spdx/license-list-data`, `AGPL-3.0-or-later.txt`, descargado por HTTPS): son **iguales palabra por palabra**; la única diferencia es `http://fsf.org/` frente a `https://fsf.org/` en la línea del copyright y el ajuste de líneas.
* SHA-256 del `LICENSE`: `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0`. Se ha añadido `license = "AGPL-3.0-or-later"` en `pyproject.toml`. D15 dice «AGPL-3.0»; se ha puesto la variante «or later» (la habitual de la FSF y la indicada en las instrucciones de esta tarea). Si el autor prefiere «only», es cambiar esa línea.

### 12. Longitudes de `config/categorias_tipo.yaml` sin contrastar

Salen del conocimiento de quien escribió el fichero, no de una fuente; está dicho en el propio fichero. Hay que verificarlas antes de dar resultados, sobre todo las cercanas a un umbral.

## No se ha podido hacer

* **Tamaño del ADS-B de adsb.lol:** GitHub responde `403` para `adsblol/globe_history_2023` desde esta sesión y la petición para añadir el repositorio fue denegada. La propuesta de descargas explica cómo verlo en el PC del autor.
* **Comprobar los pesos en GitHub** (`ultralytics/assets`), la fuente por defecto de la librería: mismo motivo. Se han tomado de Hugging Face (cuenta oficial `Ultralytics`).
* **Condiciones de uso de la base de aeronaves de OpenSky:** `opensky-network.org` sigue respondiendo `403`.
* **Centro de Descargas del CNIG:** sigue sin responder; no se conoce el tamaño de las hojas de ortofoto.
