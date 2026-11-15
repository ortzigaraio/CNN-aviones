# Sitios candidatos: fechas de vuelo PNOA

Verificación de la Fase 0 (`docs/specs/fase-0.md`, sección 6) para los aeropuertos civiles candidatos. Consultas hechas el **2026-11-15**. No se ha descargado ninguna ortofoto ni fotograma: solo metadatos de servicios web.

Términos:

* **Ortofoto**: foto aérea corregida para que tenga escala uniforme, como un mapa. Se fabrica uniendo (en mosaico) muchos **fotogramas**, que son las fotos originales que toma el avión.
* **Pasada**: cada pasada en línea recta del avión fotogramétrico; una pasada se vuela normalmente de una vez, pero pasadas vecinas pueden ser de días distintos.
* **GSD**: tamaño real que cubre cada píxel (por ejemplo, 0,25 m).
* **WMS** / **GetFeatureInfo**: servicio de mapas por internet y la petición que pregunta «qué hay en este punto» y devuelve sus atributos.

## De dónde salen las fechas

| Fuente | Qué da | Precisión de la fecha |
|---|---|---|
| WMS PNOA máxima actualidad, capa `OI.MosaicElement` ([capacidades](https://www.ign.es/wms-inspire/pnoa-ma?SERVICE=WMS&REQUEST=GetCapabilities)) | Fecha y resolución de la ortofoto más reciente en el punto. | Solo **año-mes** (campo `FECHA`, p. ej. `2023-07`). |
| WMS PNOA histórico, capas `PNOAaaaa` e `infoVuelos` ([capacidades](https://www.ign.es/wms/pnoa-historico?SERVICE=WMS&REQUEST=GetCapabilities)) | Qué ortofotos históricas existen en el punto y su resolución. | Solo **año**. |
| WMS de la Fototeca Digital, capas `vuelo_pnoa_aaaa` ([capacidades](https://wms-fototeca.idee.es/fototeca?SERVICE=WMS&REQUEST=GetCapabilities)) | Cada **fotograma** que cubre el punto: código, pasada, `fecha_fotograma`, nombre del vuelo y ruta del fichero. | **Día** (`dd/mm/aaaa`). **Sin hora**: ningún campo de hora en la respuesta. |

Método: para cada aeropuerto y cada año de 2016 a 2025 se preguntó a la Fototeca por el punto de referencia del aeródromo (ARP, de `config/aerodromos.yaml`) y, si había vuelo, por otros 8 puntos en una malla de ±0,018° de latitud y ±0,022° de longitud (unos ±2 km) alrededor. Se anotan todas las fechas y pasadas distintas que aparecen. Ejemplo de consulta (Barajas, 2023): [GetFeatureInfo](https://wms-fototeca.idee.es/fototeca?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS=vuelo_pnoa_2023&QUERY_LAYERS=vuelo_pnoa_2023&STYLES=&CRS=EPSG:4326&BBOX=40.462222,-3.570833,40.482222,-3.550833&WIDTH=101&HEIGHT=101&I=50&J=50&INFO_FORMAT=text/plain&FEATURE_COUNT=20).

Limitaciones del método (importantes para usar estas fechas):

1. **La fecha es del fotograma, no del píxel de la ortofoto.** Los servicios consultados no dicen qué fotograma se usó para cada zona del mosaico. Si todos los fotogramas que cubren el aeropuerto son del mismo día, la ortofoto de ese año tiene que ser de ese día (siempre que se haya hecho con ese vuelo, cosa que el nombre y la resolución apoyan pero no se ha comprobado). Si hay varios días, el aeropuerto puede estar partido y no se sabe dónde cae cada parte.
2. **La malla de ±2 km no cubre todo el recinto** de los aeropuertos grandes. En Barajas se añadieron tres puntos (plataforma de la T4, extremo norte y extremo sureste) para 2017, 2020 y 2023; no cambiaron las fechas. En los demás aeropuertos puede haber más fechas de las anotadas en zonas fuera de la malla.
3. **Hora**: el WMS de la Fototeca no la da. Podría venir en los metadatos internos de cada fichero de fotograma, pero comprobarlo exige leer parte del fichero (unos 79 MB cada uno) y en esta sesión no se ha hecho. Queda **sin comprobar**.
4. El Centro de Descargas del CNIG (`centrodedescargas.cnig.es`) no respondió desde este entorno («Empty reply from server»), así que no se han podido ver los metadatos de las hojas de ortofoto ni su tamaño de descarga.

## Resumen por aeropuerto

Columna «ADS-B»: si la fecha cae dentro del histórico de OpenSky (tabla `flights_data4` desde 2016, ver `docs/licencias.md`) y del histórico de adsb.lol (publicado en GitHub desde el **2023-02-16**; hay entrada en su lista de publicaciones para cada una de las fechas de 2023-2024 de esta tabla). Que exista el volcado del día no dice nada de la cobertura en tierra en ese aeropuerto: eso se mide en la Fase 1.

### LEMD, Madrid-Barajas

| Año | Fechas de los fotogramas (pasadas) | ¿Partido en días distintos? | GSD ortofoto (fotograma) | ADS-B | Estado |
|---|---|---|---|---|---|
| 2023 (más reciente) | 28/07/2023 (pasadas 002-007) | No (malla y puntos de la T4) | 0,25 m (0,22 m) | OpenSky sí · adsb.lol sí | verificado |
| 2020 | 16/07/2020 (032) y 24/07/2020 (030, 031) | **Sí** | 0,25 m | OpenSky sí · adsb.lol no | verificado |
| 2017 | 13/08/2017 (020, 021, 039) y 20/08/2017 (039) | **Sí** (la pasada 039 tiene fotogramas de los dos días) | 0,25 m | OpenSky sí · adsb.lol no | verificado |
| 2016 (PNOA10, 0,10 m) | Sin fotogramas en la capa `vuelo_pnoa_2016` en el punto | — | 0,10 m | — | sin verificar: la Fototeca no devuelve el vuelo PNOA10 de Madrid 2016; no hay fecha de día |

La ortofoto de máxima actualidad en el ARP es de `2023-07`, coherente con el vuelo del 28/07/2023.

### LEBL, Barcelona-El Prat

| Año | Fechas de los fotogramas (pasadas) | ¿Partido? | GSD ortofoto (fotograma) | ADS-B | Estado |
|---|---|---|---|---|---|
| 2024 (más reciente) | 17/07/2024 (200-202) y 18/07/2024 (203-205) | **Sí** (días consecutivos) | 0,25 m (0,22 m) | OpenSky sí · adsb.lol sí | verificado |
| 2021 | 09/06/2021 (081-083) y 05/07/2021 (080) | **Sí** | 0,25 m | OpenSky sí · adsb.lol no | verificado |
| 2018 | 03/07/2018 (168-171) | No en la malla | 0,25 m | OpenSky sí · adsb.lol no | verificado |

Máxima actualidad en el ARP: `2024-07`.

### LEPA, Palma de Mallorca

| Año | Fechas de los fotogramas (pasadas) | ¿Partido? | GSD ortofoto (fotograma) | ADS-B | Estado |
|---|---|---|---|---|---|
| 2024 (más reciente) | 30/05/2024 (007, 009, 010, 054, 055) | No en la malla | 0,25 m (0,22 m) | OpenSky sí · adsb.lol sí | verificado |
| 2021 | 09/06/2021 (009-011) | No en la malla | 0,25 m | OpenSky sí · adsb.lol no | verificado |
| 2018 | 23/04/2018 (016-020) | No en la malla | 0,15 m | OpenSky sí · adsb.lol no | verificado (el vuelo figura como años «2018,2019»; los fotogramas del aeropuerto son de 2018) |

Máxima actualidad en el ARP: `2024-05`.

### LETL, Teruel

| Año | Fechas de los fotogramas (pasadas) | ¿Partido? | GSD ortofoto (fotograma) | ADS-B | Estado |
|---|---|---|---|---|---|
| 2024 (más reciente) | 07/08/2024 (074, 075), 09/08/2024 (073), 10/08/2024 (024, 025) | **Sí** (tres días) | 0,25 m (0,35 m) | OpenSky sí · adsb.lol sí | verificado |
| 2021 | 16/08, 17/08, 28/08 y 27/09/2021 | **Sí** (cuatro días, hasta seis semanas de diferencia) | 0,25 m | OpenSky sí · adsb.lol no | verificado |
| 2018 | 28/07, 29/07 y 04/10/2018 | **Sí** | 0,25 m | OpenSky sí · adsb.lol no | verificado |

Máxima actualidad en el ARP: `2024-08`. En 2024 el fotograma tiene 0,35 m, más grueso que la ortofoto (0,25 m).

### LEVC, Valencia

| Año | Fechas de los fotogramas (pasadas) | ¿Partido? | GSD ortofoto (fotograma) | ADS-B | Estado |
|---|---|---|---|---|---|
| 2024 (más reciente) | 29/05/2024 (048-050, 104, 105) y 05/07/2024 (050) | **Sí** | 0,25 m (0,22 m) | OpenSky sí · adsb.lol sí | verificado |
| 2021 | 29/05/2021 (varias) y 07/06/2021 (1071) | **Sí** | 0,25 m | OpenSky sí · adsb.lol no | verificado |
| 2018 | 22/06, 03/07 y 04/07/2018 | **Sí** | 0,25 m | OpenSky sí · adsb.lol no | verificado |

Máxima actualidad en el ARP: `2024-05`.

### LEZG, Zaragoza

No se ha consultado: es `mixto` y la especificación lo deja fuera de la validación civil.

## Hora, tamaño de descarga y criterios no comprobados

* **Hora por fotograma o por pasada**: no la da ninguno de los tres servicios. Sin comprobar en los metadatos internos de los ficheros (ver limitación 3). Sigue valiendo la propuesta de la revisión del encargo (sombras y «reloj ADS-B»).
* **Tamaño aproximado**: un fotograma de Barajas 2023 ocupa 79.357.968 bytes (unos 79 MB, según la cabecera HTTP `content-length` de su ruta en `ftpcdd.cnig.es`, sin descargarlo). En la malla salen de 15 a 55 fotogramas por aeropuerto y año, es decir, del orden de 1-4 GB si se trabajase con fotogramas. El tamaño de las hojas de ortofoto **no se ha podido comprobar** (Centro de Descargas bloqueado).
* **Criterios 3 y 4 de la especificación** (más de 30 aviones comerciales en plataforma; aeropuerto no enmascarado ni degradado): exigen mirar la imagen. **No comprobados** en esta fase.

## Lectura para la elección de sitios (propuesta, decide Fable)

* Fecha de un solo día sobre el aeropuerto (en la malla): LEMD 2023, LEBL 2018, LEPA 2024, LEPA 2021, LEPA 2018.
* Si OpenSky da el acceso de investigador, todas las fechas desde 2017 sirven. Si solo queda adsb.lol, sirven únicamente LEMD 2023 y las de 2024 (LEBL, LEPA, LETL, LEVC).
* Teruel tiene siempre el aeropuerto repartido en varios días, hasta semanas: para «verdad fuerte» de larga estancia puede servir igual, pero hay que tratar cada zona con su fecha.
