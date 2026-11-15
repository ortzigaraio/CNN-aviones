# Fase 1b: propuesta de descargas (pendiente del visto bueno del autor)

Propuesta de Opus según `docs/specs/fase-1b.md` (secciones 2 y 9, tarea 1). **No se ha descargado nada.** Los tamaños salen de peticiones `HEAD` (solo piden la cabecera del fichero, no su contenido) o del listado de ficheros del servidor. Consultas hechas el **2026-11-15** desde el entorno de trabajo de Opus.

Términos que salen aquí:

* **Fotograma**: cada foto original que toma el avión del vuelo PNOA. La **ortofoto** es el mosaico de muchos fotogramas, corregido para que tenga escala de mapa (ver `docs/sitios.md`).
* **COG** (*Cloud Optimized GeoTIFF*): un GeoTIFF (imagen con coordenadas) organizado para poder leer trozos sin bajar el fichero entero.
* **Volcado** (*dump*): copia completa de los datos de un día, en uno o varios ficheros.
* **Bloqueado**: el host no responde o rechaza la conexión desde este entorno; no quiere decir que esté caído para el autor.

Fechas: la foto es del 28/07/2023 y la ventana de ADS-B va del 21/07/2023 al 04/08/2023. Todas tienen más de 30 días de antigüedad, así que pasan `avion_osint.limites.comprobar_fecha_retrospectiva`.

## Resumen

| # | Qué | Origen | Tamaño | Licencia | ¿Bloqueado aquí? |
|---|---|---|---|---|---|
| 1 | 49 fotogramas PNOA del 28/07/2023 sobre Barajas | `ftpcdd.cnig.es` (CNIG) | 4.031.089.353 bytes (4,03 GB) | PNOA, CC BY 4.0 ([fila](../licencias.md#tabla)) | No (HTTP). El Centro de Descargas sí lo está. |
| 2 | ADS-B de adsb.lol, 15 volcados diarios (21/07 a 04/08/2023) | GitHub, `adsblol/globe_history_2023` | **Sin obtener** | adsb.lol, ODbL 1.0 ([fila](../licencias.md#tabla)) | **Sí** (GitHub para ese repositorio y `adsb.lol`) |
| 3 | Base de aeronaves de OpenSky, foto de julio de 2023 | `s3.opensky-network.org` | 61.498.207 bytes (61,5 MB) | **Sin verificar** ([fila](../licencias.md#tabla)) | No |
| 4 | Pesos del detector OBB preentrenado en DOTAv1 (YOLO26 *small*) | Hugging Face, `Ultralytics/YOLO26` | 21.701.632 bytes (21,7 MB) | AGPL-3.0; además, entrenado con DOTA (solo uso académico) ([filas](../licencias.md#tabla)) | No (GitHub, la fuente por defecto, no comprobado) |

**Total conocido: 4.114.289.192 bytes (unos 4,1 GB)**, más el ADS-B, cuyo tamaño no se ha podido obtener y probablemente es el bloque más grande (cada volcado es mundial, no se puede pedir solo Barajas). Con los pesos *medium* en vez de *small*: 4.140.951.213 bytes.

## 1. Ortofoto: fotogramas originales PNOA 2023

Se propone el **fotograma original** y no el mosaico WMS, como pide la spec. Las hojas de ortofoto del Centro de Descargas del CNIG (`centrodedescargas.cnig.es`) siguen **bloqueadas** desde este entorno (conexión cortada), así que no se ha podido ver su tamaño ni proponerlas como alternativa.

**Cómo se ha hecho la lista.** Se preguntó al WMS de la Fototeca (capa `vuelo_pnoa_2023`, petición GetFeatureInfo, ver `docs/sitios.md`) en una malla de 9 × 9 puntos, cada 0,01°, entre 40,445° y 40,525° de latitud y entre −3,605° y −3,525° de longitud. La malla cubre todo el recinto de Barajas y algo de alrededor, así que la lista es un **máximo**: hay fotogramas que solapan mucho y otros que apenas tocan el aeropuerto.

**Hallazgo: aparece otro día.** En las dos filas norte de la malla (40,515° y 40,525°) también hay 8 fotogramas del **26/07/2023** (pasada 027, hojas 0534 y 0535; 609.813.266 bytes). En esos mismos puntos hay fotogramas del 28/07 (pasadas 001 y 002), así que con fotogramas se puede usar **solo el 28/07** y no se proponen los del 26/07. Pero `docs/sitios.md` decía «no partido» para LEMD 2023 porque su malla (±2 km alrededor del ARP) no llegaba tan al norte; el mosaico de la ortofoto **podría** usar fotogramas del 26/07 en el extremo norte. Anotado en `docs/specs/fase-1b-dudas.md`.

**Qué se descargaría:** los 49 fotogramas del 28/07/2023 (pasadas 001 a 008, vuelo `PNOA_2023_MAD`, GSD 0,22 m, RGB). Todos en la misma carpeta:

`http://ftpcdd.cnig.es/Vuelos_2023/Vuelos_2023/madrid_2023/01.VF/01.08_PNOA_2023_MAD_22cm_VF_img8c_rgb_hu30/<fichero>`

El servidor respondió `200 OK`, `content-type: image/tiff`, `last-modified: Thu, 14 Sep 2023`. Solo sirve por **HTTP** (sin cifrar): conviene guardar la cabecera `etag` de cada fichero y comprobar que el tamaño coincide con esta tabla.

| Código de fotograma | Pasada | Fichero | Bytes |
|---|---|---|---|
| P-0234_0534_001_1679 | 001 | h50_0534_fot_001-1679_cog.tif | 71471617 |
| P-0234_0534_001_1680 | 001 | h50_0534_fot_001-1680_cog.tif | 74169747 |
| P-0234_0534_001_1681 | 001 | h50_0534_fot_001-1681_cog.tif | 76714067 |
| P-0234_0534_001_1682 | 001 | h50_0534_fot_001-1682_cog.tif | 75090456 |
| P-0234_0534_001_1683 | 001 | h50_0534_fot_001-1683_cog.tif | 74532883 |
| P-0234_0534_001_1684 | 001 | h50_0534_fot_001-1684_cog.tif | 82948919 |
| P-0234_0534_001_1685 | 001 | h50_0534_fot_001-1685_cog.tif | 93878236 |
| P-0234_0535_001_1678 | 001 | h50_0535_fot_001-1678_cog.tif | 69540794 |
| P-0234_0534_002_1624 | 002 | h50_0534_fot_002-1624_cog.tif | 94110963 |
| P-0234_0534_002_1625 | 002 | h50_0534_fot_002-1625_cog.tif | 86650931 |
| P-0234_0534_002_1626 | 002 | h50_0534_fot_002-1626_cog.tif | 77060062 |
| P-0234_0534_002_1627 | 002 | h50_0534_fot_002-1627_cog.tif | 70189133 |
| P-0234_0534_002_1628 | 002 | h50_0534_fot_002-1628_cog.tif | 73575039 |
| P-0234_0534_002_1629 | 002 | h50_0534_fot_002-1629_cog.tif | 81259215 |
| P-0234_0534_002_1630 | 002 | h50_0534_fot_002-1630_cog.tif | 82511898 |
| P-0234_0535_002_1631 | 002 | h50_0535_fot_002-1631_cog.tif | 74341299 |
| P-0234_0559_003_1315 | 003 | h50_0559_fot_003-1315_cog.tif | 85950559 |
| P-0234_0560_004_1517 | 004 | h50_0560_fot_004-1517_cog.tif | 79343939 |
| P-0234_0559_004_1518 | 004 | h50_0559_fot_004-1518_cog.tif | 80174872 |
| P-0234_0559_004_1519 | 004 | h50_0559_fot_004-1519_cog.tif | 73400778 |
| P-0234_0559_004_1520 | 004 | h50_0559_fot_004-1520_cog.tif | 72791323 |
| P-0234_0559_004_1521 | 004 | h50_0559_fot_004-1521_cog.tif | 78197846 |
| P-0234_0559_004_1522 | 004 | h50_0559_fot_004-1522_cog.tif | 85736161 |
| P-0234_0559_004_1523 | 004 | h50_0559_fot_004-1523_cog.tif | 88946528 |
| P-0234_0559_005_1292 | 005 | h50_0559_fot_005-1292_cog.tif | 80169836 |
| P-0234_0559_005_1293 | 005 | h50_0559_fot_005-1293_cog.tif | 88062891 |
| P-0234_0559_005_1294 | 005 | h50_0559_fot_005-1294_cog.tif | 89210071 |
| P-0234_0559_006_1456 | 006 | h50_0559_fot_006-1456_cog.tif | 97435002 |
| P-0234_0559_006_1457 | 006 | h50_0559_fot_006-1457_cog.tif | 92308055 |
| P-0234_0559_006_1458 | 006 | h50_0559_fot_006-1458_cog.tif | 89617589 |
| P-0234_0559_006_1459 | 006 | h50_0559_fot_006-1459_cog.tif | 84322406 |
| P-0234_0559_006_1460 | 006 | h50_0559_fot_006-1460_cog.tif | 79575089 |
| P-0234_0559_006_1461 | 006 | h50_0559_fot_006-1461_cog.tif | 79357968 |
| P-0234_0559_006_1462 | 006 | h50_0559_fot_006-1462_cog.tif | 78405712 |
| P-0234_0560_006_1463 | 006 | h50_0560_fot_006-1463_cog.tif | 76370894 |
| P-0234_0559_007_1284 | 007 | h50_0559_fot_007-1284_cog.tif | 93773631 |
| P-0234_0559_007_1285 | 007 | h50_0559_fot_007-1285_cog.tif | 87466331 |
| P-0234_0559_007_1286 | 007 | h50_0559_fot_007-1286_cog.tif | 83185975 |
| P-0234_0559_007_1287 | 007 | h50_0559_fot_007-1287_cog.tif | 84161258 |
| P-0234_0559_007_1288 | 007 | h50_0559_fot_007-1288_cog.tif | 84687712 |
| P-0234_0559_007_1289 | 007 | h50_0559_fot_007-1289_cog.tif | 81812221 |
| P-0234_0560_007_1290 | 007 | h50_0560_fot_007-1290_cog.tif | 78007763 |
| P-0234_0560_008_1345 | 008 | h50_0560_fot_008-1345_cog.tif | 77936108 |
| P-0234_0559_008_1346 | 008 | h50_0559_fot_008-1346_cog.tif | 83445878 |
| P-0234_0559_008_1347 | 008 | h50_0559_fot_008-1347_cog.tif | 87791157 |
| P-0234_0559_008_1348 | 008 | h50_0559_fot_008-1348_cog.tif | 87085082 |
| P-0234_0559_008_1349 | 008 | h50_0559_fot_008-1349_cog.tif | 84329781 |
| P-0234_0559_008_1350 | 008 | h50_0559_fot_008-1350_cog.tif | 87159885 |
| P-0234_0559_008_1351 | 008 | h50_0559_fot_008-1351_cog.tif | 92823793 |
| **Total (49)** | | | **4031089353** |

**Cosas a tener en cuenta antes de decidir** (detalle en las dudas):

* Un fotograma original **no está ortorrectificado**: tiene perspectiva y no está orientado al norte. Para contar aviones vale; para medir longitudes, acimuts de sombra o casar posiciones con ADS-B a menos de 100 m hay que georreferenciarlo bien. No se ha comprobado qué georreferencia trae el COG.
* Con los fotogramas solapando (cada punto sale en 5-10 fotogramas), seguramente basta con la mitad o menos. Elegir el subconjunto exige ver la huella de cada fotograma; se puede hacer con el mismo WMS sin descargar imágenes, si el autor quiere reducir.
* Opción más barata para empezar: bajar 2-3 fotogramas centrales (p. ej. `006-1459`, `006-1460`, unos 165 MB) y comprobar la georreferencia y la hora en los metadatos internos antes de bajar el resto.

## 2. ADS-B: adsb.lol, volcados `globe_history`

* **Qué:** los volcados diarios del 21/07/2023 al 04/08/2023 (15 días) del repositorio `adsblol/globe_history_2023`, publicados como *releases* de GitHub (ver `docs/licencias.md` y `docs/sitios.md`, donde en la Fase 0 se vio que hay publicación para la fecha de la foto).
* **URL:** `https://github.com/adsblol/globe_history_2023/releases`. Los nombres exactos de las publicaciones y de sus ficheros **no se han podido ver**.
* **Tamaño: sin obtener.** Desde este entorno GitHub responde `403` para ese repositorio («GitHub access to this repository is not enabled for this session») en la API y en la web, y la petición para añadir el repositorio a la sesión fue denegada. `adsb.lol` también responde `403`. No se da ninguna cifra para no inventarla.
* **Licencia:** ODbL 1.0 (con la ambigüedad CC0 anotada en `docs/licencias.md`).
* **Por qué adsb.lol y no OpenSky:** la spec prefiere (1) la base histórica de OpenSky, pero aún no hay acceso; (2) la API REST de OpenSky necesita credenciales, que no se piden ni se usan aquí, y su documentación no dice hasta qué fecha hacia atrás da llegadas y salidas. Queda (3) adsb.lol.
* **Cobertura en LEMD: sin medir.** Medirla exige descargar al menos un volcado; no se ha hecho.
* **Ojo:** los volcados son mundiales (no se pueden pedir solo de Barajas) y traen **posiciones**, no llegadas y salidas: habrá que deducir aterrizajes y despegues de las trazas, que es la decisión de diseño que la spec (sección 8) manda anotar en dudas.

**Qué tendría que hacer el autor en su PC** (con `gh`, la herramienta de línea de órdenes de GitHub, sin credenciales especiales porque el repositorio es público):

```bash
# 1. Ver los nombres de las publicaciones de esas fechas
gh release list -R adsblol/globe_history_2023 --limit 400 | grep -E "2023\.(07\.(2[1-9]|3[01])|08\.0[1-4])"
# 2. Para cada una, ver ficheros y tamaños (sin descargar)
gh release view <etiqueta> -R adsblol/globe_history_2023 --json assets --jq '.assets[] | [.name, .size] | @tsv'
```

Con esa salida se completa esta fila y el total, y el autor decide si baja los 15 días o empieza por el día de la foto.

## 3. Base de aeronaves de OpenSky

* **Qué:** `aircraft-database-complete-2023-07.csv`, la foto mensual de la base de aeronaves (icao24 → matrícula, tipo OACI…) más cercana a la fecha de la ortofoto.
* **URL:** `https://s3.opensky-network.org/data-samples/metadata/aircraft-database-complete-2023-07.csv` (la antigua `opensky-network.org/datasets/metadata/aircraftDatabase.csv` redirige a este mismo servidor).
* **Tamaño:** 61.498.207 bytes, según el listado del servidor (`data-samples`, prefijo `metadata/`). Alternativas en el mismo listado: la de 2023-08 (61.499.898 bytes) y `aircraftDatabase-2023-07.csv` (94.506.864 bytes, otro formato).
* **Licencia: sin verificar.** Las condiciones de OpenSky están en `opensky-network.org`, que responde `403` desde aquí. En la misma carpeta hay un `README.TXT` de 554 bytes que podría decir algo; no se ha abierto para no bajar nada.
* **Bloqueado:** no (`s3.opensky-network.org` responde).
* Hasta leer las condiciones, la tabla no se sube a ningún sitio público (ya lo dice `docs/licencias.md`).

## 4. Pesos del detector OBB preentrenado

* **Qué:** `yolo26s-obb.pt` (modelo *small*). Alternativa *medium*: `yolo26m-obb.pt`. Son los OBB de la versión más reciente de Ultralytics publicada en su cuenta de Hugging Face; según su ficha, «trained on DOTAv1, including 15 classes» (una de ellas, *plane*).
* **URL:** `https://huggingface.co/Ultralytics/YOLO26/resolve/main/yolo26s-obb.pt` (repositorio en la revisión `070ac3c51435984d992ba92eb3f234daf4e4500d`).
* **Tamaño:** 21.701.632 bytes (*small*) o 48.363.653 bytes (*medium*), según la API de Hugging Face y la cabecera `x-linked-size`. Huellas SHA-256 publicadas: *small* `38dbd72ef6804f9bbbea7ad20f486e6ca6e093c8cd9bc857207a846565bd6e0b`, *medium* `23e0630f66857cf4b87535f6e705b065f1e8a33603640b8e61ace85b75312903`.
* **Licencia:** AGPL-3.0 (ficha del modelo). Como están entrenados con DOTA, heredan su límite de uso solo académico (`docs/licencias.md`). Encaja con D15 (repo público AGPL, modelos de uso no comercial).
* **Bloqueado:** Hugging Face no. La descarga por defecto de la librería `ultralytics` va a `github.com/ultralytics/assets/releases`, que **no se ha comprobado** (GitHub está restringido en esta sesión).
* Para ejecutar el detector hará falta añadir la dependencia `ultralytics` (AGPL-3.0); no se ha añadido todavía porque no se usa en esta parte.

## Qué se pide al autor

1. Visto bueno (o recorte) de cada bloque: fotogramas (los 49, un subconjunto o primero 2-3 de prueba), ADS-B (tras ver su tamaño con los comandos de arriba), base de aeronaves y pesos (*small* o *medium*).
2. Dónde vive el remoto de DVC (pendiente en `docs/decisiones.md`), porque son más de 4 GB.
3. Ejecutar en su PC los comandos de `gh` de la sección 2 y pasar la salida.
