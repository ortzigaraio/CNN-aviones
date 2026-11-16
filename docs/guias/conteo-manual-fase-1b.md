# Fase 1b: guía del conteo manual y de la medida de sombras

Para el autor. No hace falta haber usado QGIS antes. Es el paso B de `docs/specs/fase-1b.md` (conteo) y el punto 3 de su anexo (sombras).

**Antes de empezar:** el conteo se hace **a ciegas**. No abras `data/fase-1b/detecciones_nativa.geojson` ni `data/fase-1b/detecciones_05m.geojson` (salida del detector), ni datos ADS-B, hasta haber guardado el conteo. Si en QGIS aparecen esas capas, quítalas sin mirarlas.

## Términos

* **QGIS**: programa gratuito para ver y editar mapas e imágenes con coordenadas (un SIG, *sistema de información geográfica*).
* **Mosaico**: una sola imagen del aeropuerto hecha pegando varios fotogramas (fotos originales del vuelo PNOA del 28/07/2023). Cada punto sale del fotograma cuyo centro está más cerca. Fichero `data/fase-1b/mosaico.tif`.
* **GeoTIFF / COG**: imagen con coordenadas dentro. COG es un GeoTIFF preparado para abrirse rápido a cualquier zoom.
* **Capa**: cada cosa que se pinta en QGIS (la imagen, tus puntos…). Una capa de **puntos** guarda un punto por objeto, con sus **atributos** (campos con valores, como una fila de una tabla).
* **SRC** (*sistema de referencia de coordenadas*): cómo se traducen coordenadas a sitios del mundo. Aquí siempre **EPSG:25830** (ETRS89 / UTM huso 30 N), en metros, el oficial en la España peninsular.
* **GeoJSON**: formato de texto para guardar puntos, líneas o polígonos con sus atributos.
* **Acimut**: dirección medida en grados desde el norte, girando como las agujas del reloj (0° norte, 90° este, 180° sur, 270° oeste).

## 1. Conseguir el mosaico

El mosaico no va a git (pesa varios cientos de MB). Cómo hacértelo llegar está pendiente de decidir (ver `docs/specs/fase-1b-dudas.md`, punto 18). La opción que no depende de nadie es generarlo en tu PC, desde la raíz del repositorio:

```bash
uv sync --group geo
uv run --group geo python scripts/fase_1b/fotogramas.py --descargar
uv run --group geo python scripts/fase_1b/mosaico.py
```

El primero instala `rasterio` (librería para leer y escribir imágenes con coordenadas). El segundo lee la cabecera de los 49 fotogramas del 28/07/2023 (unos KB de cada uno), elige los 12 que hacen falta, los baja del CNIG (951.656.867 bytes, unos 0,95 GB; menos si ya tienes alguno en `data/fase-1b/ortofoto/`) y comprueba su tamaño. El tercero (unos 12 minutos y 3 GB de disco temporal) genera `data/fase-1b/mosaico.tif` (unos 422 MB), `data/fase-1b/mosaico_fotogramas.geojson` y una vista reducida `data/fase-1b/mosaico_vista.png`.

## 2. Instalar QGIS y abrir el mosaico

1. Baja QGIS de <https://qgis.org> (la versión **LTR**, la de soporte largo) e instálalo. Los menús de esta guía son los de QGIS 3 en castellano; en otra versión pueden cambiar un poco de nombre.
2. Abre QGIS ▸ **Proyecto ▸ Nuevo**.
3. **Proyecto ▸ Propiedades ▸ SRC**: busca `25830`, elige *ETRS89 / UTM zone 30N* y acepta. Así las medidas salen en metros.
4. En **Proyecto ▸ Propiedades ▸ General ▸ Medidas**, pon *Elipsoide* en **Ninguno / Planimétrico** y las unidades de distancia en **metros**. (Medir sobre el plano UTM es lo que se usa en el resto del proyecto; la diferencia con el elipsoide es despreciable aquí).
5. Arrastra `data/fase-1b/mosaico.tif` a la ventana de QGIS. Aparece la capa del mosaico.
6. Arrastra también `data/fase-1b/mosaico_fotogramas.geojson` (las zonas que aporta cada fotograma). En sus propiedades (doble clic ▸ **Simbología**) pon *Relleno* **sin relleno** y un borde de color vivo: así ves dónde están las **costuras**, las líneas donde se pasa de un fotograma a otro.
7. **Proyecto ▸ Guardar como…** y guarda el proyecto (p. ej. `data/fase-1b/conteo.qgz`).

Para moverte: rueda del ratón para el zoom, arrastrar con la rueda pulsada (o la barra espaciadora) para desplazarte.

## 3. Crear la capa de puntos

Se crea en GeoPackage (un formato de fichero que QGIS guarda en disco a cada paso; menos riesgo de perder trabajo) y al final se exporta a GeoJSON.

1. **Capa ▸ Crear capa ▸ Nueva capa GeoPackage…**
2. *Base de datos*: `data/fase-1b/conteo_manual.gpkg`. *Nombre de la tabla*: `conteo_manual`. *Tipo de geometría*: **Punto**. SRC: **EPSG:25830**.
3. En *Nuevo campo* añade estos cuatro, **con estos nombres exactos** (minúsculas, sin tildes):

| Nombre | Tipo en QGIS | Valores |
|---|---|---|
| `categoria` | Texto (cadena) | `ligero`, `regional`, `pasillo_unico`, `fuselaje_ancho`, `desconocido` |
| `zona` | Texto (cadena) | `terminal`, `remoto`, `mantenimiento`, `aviacion_general` |
| `en_movimiento` | Booleano | verdadero (sí) / falso (no) |
| `longitud_m` | Número decimal (real) | longitud medida en metros; se puede dejar vacío |

4. Acepta.
5. Para no escribir mal los valores: doble clic en la capa ▸ **Formulario de atributos**. Para `categoria`, cambia el *tipo de control* a **Mapa de valores** y añade los cinco valores (en las dos columnas, *Valor* y *Descripción*, el mismo texto). Lo mismo para `zona` con sus cuatro valores. Acepta.

## 4. Qué cuenta como avión

Un punto por **avión de ala fija en tierra, visible en la imagen, dentro del recinto del aeropuerto** (pistas, calles de rodaje, plataformas y zonas de mantenimiento; el mosaico abarca algo más que el aeropuerto).

Sí se cuentan:

* Aviones aparcados, en rodaje, en la pista, remolcados o con escaleras y vehículos alrededor.
* Aviones dentro de un hangar **abierto** si se ve al menos la mitad del avión y no hay duda de que es un avión. Zona `mantenimiento`. Si no se ve lo bastante, no se cuenta.
* Aviones cortados por una costura del mosaico: **uno** solo (ver «Costuras» abajo).

No se cuentan:

* **Helicópteros** (no son de ala fija).
* Aviones **en el aire** (despegando o aterrizando ya separados del suelo). Se reconocen porque su sombra está separada del avión, a cierta distancia.
* **Restos**: fuselajes sin alas, piezas, aviones desguazados.
* **Maquetas** y simulacros: p. ej. el avión de prácticas de bomberos (suele estar quemado o sin pintura, junto a una explanada de entrenamiento), siluetas pintadas en el suelo.
* Lo que no se ve: aviones dentro de hangares cerrados o tapados.
* Fuera del recinto del aeropuerto.

Si dudas con un objeto, **no lo cuentes** y apunta sus coordenadas y el motivo en un fichero de texto aparte (`data/fase-1b/conteo_dudas.txt`). No añadas campos nuevos a la capa.

**Costuras.** En las líneas de `mosaico_fotogramas.geojson` se pasa de un fotograma a otro, tomados con segundos o minutos de diferencia. Un avión que se movía puede salir partido, duplicado o faltar. Además, los fotogramas no están corregidos del relieve: el suelo empalma bien (1-2 m), pero lo que tiene altura (edificios, colas de avión) puede salir con un escalón en la costura. Cerca de una costura, mira el avión en los dos fotogramas originales (sección 6) y cuéntalo una sola vez.

## 5. Marcar cada avión

1. Selecciona la capa `conteo_manual` y pulsa **Conmutar edición** (el lápiz).
2. Pulsa **Añadir punto** y haz clic en el **centro del avión** (donde se cruzan fuselaje y alas).
3. Se abre el formulario. Rellena:
   * `categoria`, por la **longitud** del avión (de punta del morro a punta de la cola, sin contar las alas):

     | categoria | longitud |
     |---|---|
     | `ligero` | menos de 20 m |
     | `regional` | de 20 m (incluido) a menos de 30 m |
     | `pasillo_unico` | de 30 m (incluido) a 45 m (incluido) |
     | `fuselaje_ancho` | más de 45 m |
     | `desconocido` | no se puede medir ni estimar |

     (Límites de la decisión D19).
   * `zona`:
     * `terminal`: en un puesto pegado al edificio de la terminal, con pasarela (*finger*, el túnel que une avión y terminal) o junto a él.
     * `remoto`: en una plataforma separada de los edificios (los pasajeros van en autobús).
     * `mantenimiento`: frente a o dentro de hangares de mantenimiento.
     * `aviacion_general`: plataforma de aviación general y ejecutiva (avionetas, reactores privados).
     * Si el avión está en una pista o calle de rodaje, pon la zona más cercana y marca `en_movimiento`.
   * `en_movimiento`: **sí** si está en una pista o en una calle de rodaje (camino entre pistas y plataformas), o si se ha movido entre dos fotogramas (sección 6). **No** si está parado en un puesto de estacionamiento.
   * `longitud_m`: si lo mides (abajo). Si no, déjalo vacío.
4. **Guarda a menudo**: botón **Guardar cambios de la capa** (disco junto al lápiz).

Consejo: recorre el aeropuerto con orden (p. ej. de norte a sur, plataforma a plataforma) para no saltarte ni repetir zonas.

### Cómo medir una longitud

1. **Ver ▸ Herramientas de medida ▸ Medir línea** (o `Ctrl+Mayús+M`).
2. Clic en la punta del morro, clic en la punta de la cola, **clic derecho** para terminar. La ventana muestra la longitud total en metros (comprueba que dice *metros* y, si se ofrece, *cartesiano*).
3. Escribe el valor, con dos decimales como mucho, en `longitud_m`.

Medir sobre el avión y no sobre su sombra. El mosaico tiene 0,25 m por píxel: el error esperable es de 1-2 píxeles por extremo (±0,5 m), algo más si el borde está borroso.

## 6. Ver los fotogramas originales

Para dudas en costuras y para decidir `en_movimiento`: los fotogramas originales están en `data/fase-1b/ortofoto/` (también tienen coordenadas en EPSG:25830). Arrástralos a QGIS, pon el mosaico encima y activa y desactiva las capas con su casilla. Dos fotogramas que se solapan se tomaron con segundos de diferencia: un avión que **cambia de sitio** entre uno y otro se estaba moviendo; uno que no se mueve, estaba parado (anexo de la spec, punto 2).

## 7. Guardar como GeoJSON

1. Termina la edición (lápiz) y guarda.
2. Clic derecho en la capa `conteo_manual` ▸ **Exportar ▸ Guardar objetos como…**
3. *Formato*: **GeoJSON**. *Nombre de archivo*: `data/fase-1b/conteo_manual.geojson`. *SRC*: **EPSG:25830**. Deja marcados los cuatro campos.
4. Acepta. Comprueba que el fichero existe y, abriéndolo con un editor de texto, que cada punto lleva `categoria`, `zona`, `en_movimiento` y `longitud_m`.

## 8. Aparte: acimut de la sombra de 5 torres de iluminación

Sirve para estimar a qué hora se tomó la foto (`hora_por_sombra`, paso A de la spec). Se hace en el mismo proyecto.

**Qué objetos.** Al menos **5** objetos verticales altos y delgados, repartidos por el aeropuerto: las **torres de iluminación** de plataforma (mástiles altos con focos) y la torre de control. Elige los que proyectan la sombra sobre suelo llano y despejado (no sobre edificios, aviones ni taludes).

**Cuidado con la perspectiva.** En la foto, un objeto alto aparece inclinado hacia fuera del centro del fotograma: su punta no está encima de su base. Eso **no** es la sombra. La sombra es la mancha oscura **en el suelo**. Para distinguirlas, mira el objeto en dos fotogramas que se solapen (sección 6): la sombra queda en el mismo sitio; la imagen del objeto cambia de inclinación.

**Pasos:**

1. **Capa ▸ Crear capa ▸ Nueva capa GeoPackage…**: base de datos `data/fase-1b/sombras.gpkg`, tabla `sombras`, geometría **Línea**, SRC **EPSG:25830**. Campos: `objeto` (texto: p. ej. «torre iluminación plataforma T4 n.º 3»), `fotograma` (texto: el fichero en que mediste).
2. Conmutar edición ▸ **Añadir línea**. Primer clic en la **base** del objeto (donde toca el suelo); segundo clic en la **punta de la sombra en el suelo**; clic derecho para terminar. Rellena los campos.
3. Repite para los 5 objetos o más. Guarda.
4. Abre la **calculadora de campos** (ábaco en la barra de la tabla de atributos): crea un campo nuevo `acimut_cuadricula` (decimal) con la expresión

   ```
   degrees(azimuth(start_point($geometry), end_point($geometry)))
   ```

   Da el acimut de la sombra respecto al norte **de la cuadrícula UTM** (el «arriba» del mapa).
5. Crea otro campo `acimut_verdadero` (decimal) con `"acimut_cuadricula" - 0.36`. Es la corrección al norte geográfico de la decisión D20 (en Barajas, el norte de la cuadrícula UTM está girado 0,36° respecto al geográfico).
6. Exporta como en la sección 7, en formato GeoJSON, a `data/fase-1b/sombras.geojson`.

Si los acimutes de los distintos objetos difieren mucho entre sí (más de unos 5°), revisa que mediste la sombra y no la inclinación del objeto, y si persiste, apúntalo: puede indicar que zonas distintas se fotografiaron a horas distintas.
