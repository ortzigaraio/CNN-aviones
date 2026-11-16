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

## Segunda tanda (2026-11-15): imágenes, mosaico y detector

Anotado por Opus al ejecutar las tareas del anexo de `fase-1b.md`. Como antes: se ha elegido lo más conservador y todo es revisable.

### 13. Recinto del aeropuerto

Rectángulo en EPSG:25830 (`scripts/fase_1b/comun.py`, `RECINTO`): este 448.700 a 456.000 m, norte 4.477.300 a 4.488.000 m. En grados: de 40,4448° a 40,5416° N y de −3,6049° a −3,5196° E. Son 7,3 × 10,7 km.

* **Punto de partida:** el ARP de `config/aerodromos.yaml` (40,472222 N, −3,560833 E) cae en 452.459 E, 4.480.322 N. La malla de la Fase 0 (40,445° a 40,525° N, −3,605° a −3,525° E) pretendía cubrir el recinto con margen.
* **Oeste (448.700, ≈ −3,605°)** y **sur (4.477.300, ≈ 40,445°):** los de esa malla. En la vista del mosaico la T4 y su plataforma quedan a más de 1 km del borde oeste, y las plataformas del sur (T1-T3, carga) acaban unos 900 m antes del borde sur (autovía y polígonos industriales).
* **Este (456.000, ≈ −3,520°):** algo más que la malla, para incluir con margen el extremo sureste de las pistas 14/32 y los hangares del sureste. En la vista, lo último del aeropuerto queda a 1-1,5 km del borde.
* **Norte (4.488.000, ≈ 40,542°):** primero se puso 4.487.200 (≈ 40,534°), pero al ver los fotogramas de la pasada 002 la pista este llegaba al borde de esos fotogramas, así que se subió a 4.488.000. En la vista del mosaico los extremos norte de las dos pistas norte-sur quedan unos 500 m dentro del borde.

No se ha usado ninguna fuente nueva (ni OpenStreetMap ni el AIP de pistas): solo el ARP y las propias imágenes. Si Fable quiere un recinto ceñido al vallado, habría que trazarlo a mano sobre el mosaico.

### 14. Subconjunto mínimo de fotogramas: 12

* Las cabeceras de los 49 se leyeron con peticiones parciales (`Range: bytes=0-16383`; la etiqueta 34264 está en los primeros 1.000 bytes). Todos miden 14.790 × 23.010 px y llevan la misma transformación con un giro de unos 0,26°. Huellas en `data/fase-1b/fotogramas_huellas.geojson`.
* Criterio, tal como lo pidió el autor: el subconjunto más pequeño tal que cada punto del recinto, asignado al fotograma **del subconjunto** con centro más cercano, cae dentro de ese fotograma. Búsqueda exacta (en profundidad creciente; ver `seleccionar` en `scripts/fase_1b/fotogramas.py`) sobre una malla de puntos cada 20 m: con 11 no hay solución; con 12, sí. Con el recinto primero puesto (norte en 4.487.200) salían 9.
* Seleccionados: `001-1680`, `001-1682`, `001-1684`, `002-1626`, `002-1628`, `002-1630`, `004-1518`, `004-1520`, `004-1522`, `006-1458`, `006-1460`, `006-1462` (951.656.867 bytes en total).
* **Consecuencia:** con 12 en vez de 49, muchos puntos se toman lejos del centro de su fotograma (hasta el borde), donde la perspectiva es mayor (ver punto 17). D16 dice «el fotograma de centro más cercano» sin decir entre cuáles; aquí se ha interpretado entre los del subconjunto. La alternativa (centro más cercano entre los 49) exigiría bajarlos casi todos (~4 GB).
* Descargados en esta sesión: 11 ficheros, 872.081.778 bytes (0,87 GB): los 12 menos `006-1460`, que ya estaba. Tamaños comprobados contra la tabla; `etag`, `last-modified` y SHA-256 de cada uno en `data/fase-1b/ortofoto/descargas.json`. `006-1459` (bajado antes) no entra en el mosaico; se conserva porque sirve para comparar solapes (anexo, puntos 2 y 3).

### 15. Resolución del mosaico y del detector

* Los fotogramas tienen 0,237 m/px; el mosaico, 0,25 m (anexo, punto 1). Se remuestrea con interpolación bilineal (media ponderada de los 4 píxeles vecinos).
* «Resolución nativa» del detector (paso C) se ha interpretado como la del mosaico, 0,25 m, porque el anexo manda pasarlo «sobre el mosaico». La versión a 0,5 m se obtiene promediando bloques de 2 × 2 píxeles del mosaico.

### 16. Compresión del mosaico: JPEG calidad 90 (con pérdida)

Con compresión sin pérdida (DEFLATE o LZW) el mosaico ocuparía unos 3 GB (el intermedio LZW ocupó 2,96 GB); con JPEG calidad 90 ocupa 422 MB. Los fotogramas originales ya vienen en JPEG calidad 80, así que la pérdida añadida es pequeña, pero existe. Si Fable prefiere sin pérdida, es cambiar `compress="JPEG"` en `scripts/fase_1b/mosaico.py`.

### 17. Las costuras se notan en lo que tiene altura

Revisado a resolución completa en una costura sobre la T4S: el suelo empalma con un salto de unos 1 m (como vio Fable), pero el tejado de la terminal tiene un escalón de varios metros, porque los fotogramas no están corregidos del relieve. Las colas de los aviones (10-20 m de alto) pueden salir algo desplazadas o partidas en una costura. Se avisa en la guía del conteo. No afecta a contar en el suelo, pero sí a dónde cae el centro de un avión cortado.

### 18. Cómo hacer llegar el mosaico al PC del autor (sin decidir)

`data/fase-1b/mosaico.tif` ocupa **421.749.947 bytes (422 MB)**, 29.200 × 42.800 px. No va a git. Dos opciones:

* **A. Generarlo en su PC** (no depende de nada más; descarga 0,95 GB del CNIG por HTTP y tarda unos 12 minutos en generar el mosaico, con 3 GB de disco temporal):

  ```bash
  uv sync --group geo
  uv run --group geo python scripts/fase_1b/fotogramas.py --descargar
  uv run --group geo python scripts/fase_1b/mosaico.py
  ```

  Debería salir idéntico salvo diferencias mínimas si su versión de GDAL (la librería que usa `rasterio`) es distinta; los `.dvc` de este repositorio dirían si los ficheros coinciden byte a byte.
* **B. Remoto de DVC** (sigue pendiente en `docs/decisiones.md`): se configura un remoto (p. ej. una carpeta compartida, Google Drive o un disco) y `dvc push` desde aquí, `dvc pull` en su PC. Subiría unos 1,5 GB (fotogramas + mosaico). Exige que el autor elija el remoto y, según cuál, credenciales que aquí no se usan.

### 19. Unión de duplicados del detector

Ultralytics ya quita duplicados dentro de cada tesela; entre teselas que se solapan no. Regla elegida (en `scripts/fase_1b/detector.py`): de mayor a menor confianza, se descarta una caja si su IoU con una ya aceptada es mayor que 0,3, o si más del 70 % de la más pequeña cae dentro de la otra (caso típico: un avión cortado por el borde de una tesela, cuya caja parcial queda dentro de la completa). Es una elección de Opus, sin ajustar a la vista de resultados.

Además, antes de unir se descartan las cajas de menos de 1 m² de área: en la primera ejecución el modelo devolvió alguna caja degenerada (casi sin área), con la que los cocientes anteriores no están definidos (avisos de división por cero). En esa ejecución ninguna caja degenerada llegó a la salida, así que no pudo eliminar a otra; el filtro no cambia el resultado, solo evita el caso. Un avión no puede ocupar menos de 1 m² a esta escala, pero el umbral es elección de Opus. En la segunda ejecución, ya con el filtro, aún salió un aviso de división por cero: con bordes casi paralelos y coincidentes, el recorte de polígonos puede dar una intersección disparatada. Se ha acotado la intersección al área de la caja menor (lo que la geometría garantiza) y se ha comprobado la función contra un cálculo por Monte Carlo en 3.000 pares de rectángulos (aleatorios, idénticos y casi idénticos): coincide dentro del ruido del muestreo. Las salidas guardadas son de una tercera ejecución con el código final, con los avisos numéricos convertidos en errores (si hubiera habido alguno, la ejecución habría fallado).

Tiempo de ejecución en este entorno (4 núcleos de CPU, sin GPU): entre 11,5 y 12,5 min a 0,25 m (1.908 teselas) y 3,2-3,3 min a 0,5 m (468 teselas), en tres ejecuciones; la última, 11,8 + 3,2 min.

### 20. Criterios de la guía del conteo que no venían en la spec

En `docs/guias/conteo-manual-fase-1b.md`:

* Avión en hangar abierto: se cuenta si se ve al menos la mitad y no hay duda; zona `mantenimiento`.
* Aviones en el aire (sombra separada del avión): no se cuentan (no están en tierra).
* Avión en pista o calle de rodaje: `zona` = la más cercana de las cuatro, y `en_movimiento` = sí. La spec no prevé una zona para pistas y rodaje.
* `en_movimiento` como campo booleano (verdadero/falso).
* El GeoJSON se guarda en EPSG:25830, como las detecciones, no en WGS84 (lo que pide la norma de GeoJSON); QGIS lo admite y escribe el SRC en el fichero.
* Dudas del conteo, en un fichero de texto aparte (`data/fase-1b/conteo_dudas.txt`), sin añadir campos.
* Sombras: capa de líneas base → punta de la sombra, con acimut de cuadrícula y acimut corregido (−0,36°, D20), en `data/fase-1b/sombras.geojson`.

### 21. Pesos del detector fuera de DVC

La spec dice que los pesos no se versionan. Están en `data/pesos/yolo26s-obb.pt` (ignorado por git y sin `.dvc`); el guion los baja de Hugging Face (revisión `070ac3c5…`) si faltan y comprueba el SHA-256 publicado (coincide: `38dbd72e…`). Versiones: `ultralytics` 8.4.214, `torch` 2.15.0+cpu. El guion pone `YOLO_OFFLINE=1` para que Ultralytics no envíe telemetría.

`pyproject.toml` fija `torch` y `torchvision` al índice de PyTorch **solo CPU** (grupo `vision`). Basta para esta fase, pero en el PC del autor (RTX 3070, D14) la Fase 2 necesitará las ruedas con CUDA: habrá que cambiar ese índice entonces. Instalado aquí, el grupo `vision` ocupó unos 1,2 GB.

### 22. Sin tests para los guiones

Los guiones de `scripts/fase_1b/` no tienen tests (la spec los pide para `src/`, y estos usan `rasterio` y `ultralytics`, que el CI no instala). Se han probado solo ejecutándolos de verdad una vez. Lo más delicado sin test: el lector de cabeceras TIFF, la búsqueda del subconjunto y la intersección de cajas orientadas.

### 23. DVC sin remoto y cambio en `.gitignore`

`dvc add` (sin remoto, decisión D6) de `data/fase-1b/ortofoto/` (los 13 fotogramas más `descargas.json`), `mosaico.tif`, `mosaico_fotogramas.geojson`, `mosaico_vista.png`, `fotogramas_huellas.geojson`, `detecciones_nativa.geojson` y `detecciones_05m.geojson`. La caché local de DVC ocupa 1,4 GB. Para que git y DVC vieran los `.dvc` dentro de `data/fase-1b/`, se han cambiado las reglas de `data/` en `.gitignore` por `/data/**`, `!/data/**/`, `!/data/**/*.dvc` y `!/data/**/.gitignore`: con las anteriores git sí veía los `.dvc`, pero DVC (que interpreta `.gitignore` con otra librería) daba la carpeta por ignorada y no los encontraba. Comprobado: `dvc status` dice «Data and pipelines are up to date» y `git status` solo muestra los `.dvc` dentro de `data/`.
