# Licencias y condiciones de uso

Condiciones de cada fuente de datos (y del software que afecta a la licencia del repositorio), consultadas en la web para la Fase 0. Todas las consultas son del **2026-11-15**.

Cómo leer la columna «Estado»:

* **verificado**: leído en una página o documento del propio titular de los datos, enlazado en la fila.
* **verificado, ambiguo**: leído en fuente primaria, pero el texto deja dudas; se copia literal abajo y no se interpreta a favor.
* **sin verificar**: no se ha podido leer la fuente primaria (se dice por qué). Lo que aparezca en esa fila es orientativo y no vale para decidir.

Términos que salen en la tabla:

* **CC BY 4.0**: licencia Creative Commons que permite cualquier uso, también comercial, siempre que se cite el origen.
* **CC BY-NC 4.0**: igual, pero **NC** = no comercial. **SA** (*ShareAlike*, «compartir igual») obliga a publicar lo derivado con la misma licencia.
* **ODbL**: *Open Database License*, licencia abierta para bases de datos: permite copiar, redistribuir y crear obras a partir de ellas, citando el origen; si se publica una base de datos *adaptada*, debe llevar la misma licencia.
* **AGPL-3.0**: licencia de software libre que obliga a publicar bajo la misma licencia todo el código de un proyecto que la use, también si se ofrece como servicio por red.
* **Derivado**: lo que se obtiene a partir de los datos (un modelo entrenado, una tabla de conteos, una figura).

## Tabla

| Fuente | Licencia o condiciones | Uso permitido | ¿Redistribuir datos? | ¿Publicar modelos / resultados derivados? | Atribución exigida | Enlace | Consulta | Estado |
|---|---|---|---|---|---|---|---|---|
| **PNOA** (ortofotos IGN/CNIG) | CC BY 4.0 (Orden FOM/2807/2015). | Académico y comercial. | Sí, con atribución. | Sí, con la fórmula de obra derivada. | «Obra derivada de PNOA <fecha> CC-BY 4.0 scne.es», visible junto a la imagen o figura. | [Licencia IGN (PDF)](https://www.ign.es/web/resources/licencia/Condiciones_licenciaUso_IGN.pdf); `AccessConstraints` del [WMS PNOA](https://www.ign.es/wms-inspire/pnoa-ma?SERVICE=WMS&REQUEST=GetCapabilities): «CC BY 4.0 scne.es» | 2026-11-15 | verificado |
| **NAIP** (ortofotos EE. UU.) | Fuentes secundarias la dan como dominio público; también citan que el USDA estudió pasar a un modelo de licencia para imágenes posteriores a 2019. | — | — | — | — | [USDA FPAC GEO](https://www.fpacbc.usda.gov/geo/imagery-programs/naip-imagery/index.html) | 2026-11-15 | sin verificar: `www.fpacbc.usda.gov` respondió 503 y `data.usgs.gov` 403. No se usa en el núcleo del proyecto. |
| **DOTA** | Solo uso académico; imágenes de Google Earth sujetas a sus condiciones. | Académico. Comercial **prohibido**. | No lo dice. | No lo dice. | Citar Xia et al. (CVPR 2018) y Ding et al. (TPAMI 2021). | [DOTA, dataset](https://captain-whu.github.io/DOTA/dataset.html) | 2026-11-15 | verificado, ambiguo (redistribución y modelos: no lo dice) |
| **FAIR1M** | No encontrada en fuente primaria. | — | — | — | Citar Sun et al. (arXiv:2103.05569). | [Gaofen Challenge](https://www.gaofen-challenge.com/benchmark); [artículo](https://arxiv.org/abs/2103.05569) | 2026-11-15 | sin verificar: la página oficial solo carga un título (aplicación JavaScript) y el artículo no da licencia del dataset. Las copias en Hugging Face o Roboflow no son del titular. |
| **xView** | CC BY-NC-SA 4.0, pero el uso concedido es «para preparar y competir en el Challenge». | No comercial; posible límite al propio concurso. | Con la misma licencia (SA), no comercial. | No lo dice; por SA, lo derivado iría con la misma licencia. | La licencia exige citar; no da fórmula concreta. | [xView, términos](https://xviewdataset.org/terms.html) | 2026-11-15 | verificado, ambiguo |
| **DIOR** (y DIOR-R) | CC BY-NC 4.0. | Académico; comercial no. | Sí, no comercial y citando. | Sí, no comercial. | Citar Li et al. (ISPRS 2020) y Cheng et al. (TGRS 2022). | [Página de G. Cheng (NWPU)](https://gcheng-nwpu.github.io/) | 2026-11-15 | verificado |
| **MAR20** | CC BY-NC 4.0 y «used for research purposes only». | Solo investigación; comercial no. | Sí, no comercial y citando. | Sí, no comercial. | Citar Yu et al., «MAR20…», 2022. | [Página de G. Cheng (NWPU)](https://gcheng-nwpu.github.io/) | 2026-11-15 | verificado |
| **OpenSky, API REST** | La documentación dice «research and non-commercial purposes»; las condiciones completas están en `opensky-network.org/about/terms-of-use`. | Investigación, no comercial. | No comprobado. | No comprobado. | Citar Schäfer et al., «Bringing Up OpenSky…», IPSN 2014. | [Documentación API](https://openskynetwork.github.io/opensky-api/); [términos](https://opensky-network.org/about/terms-of-use) | 2026-11-15 | sin verificar: `opensky-network.org` responde 403 desde este entorno. Solo se ha leído la documentación (sí verificada). |
| **OpenSky, base histórica (Trino)** | Acceso para investigadores con afiliación universitaria, organismos públicos y autoridades aeronáuticas, previa solicitud. Empresas, con licencia. | Investigación aeronáutica. | No lo dice la página de acceso. | No lo dice la página de acceso. | Ver fila anterior. | [Trino, datos históricos](https://openskynetwork.github.io/opensky-api/trino.html) | 2026-11-15 | verificado (condiciones de acceso); sin verificar (licencia de los datos: términos en el host bloqueado) |
| **OpenSky, base de aeronaves** | — | — | — | — | — | `opensky-network.org` | 2026-11-15 | sin verificar: `opensky-network.org` responde 403. |
| **adsb.lol** (histórico) | ODbL 1.0. El repositorio incluye además un fichero CC0 sin decir a qué se aplica. | Cualquier uso, citando. | Sí, con la misma licencia. | Sí; citar la fuente y la licencia; una base adaptada que se publique va con ODbL. | Citar adsb.lol y la licencia ODbL. | [globe_history_2025](https://github.com/adsblol/globe_history_2025); [lista de repos](https://github.com/orgs/adsblol/repositories?q=globe_history); [resumen ODbL](https://opendatacommons.org/licenses/odbl/summary/) | 2026-11-15 | verificado, ambiguo (ODbL y CC0 a la vez). El sitio `adsb.lol` responde 403 («network is blocked») desde este entorno. |
| **ADS-B Exchange** | Condiciones de JETNET: uso solo interno; prohibido publicar o redistribuir datos; derivados solo dentro de la organización; prohibido entrenar modelos de lenguaje. API «Community» para uso personal no comercial. Muestra gratis: el día 1 de cada mes, sin licencia propia indicada. | Interno / personal. | **No.** | **No** fuera de la organización. | — | [Términos JETNET](https://www.jetnet.com/legal/terms-of-use); [Uso aceptable](https://www.adsbexchange.com/acceptable-use-policy/); [Muestras](https://www.adsbexchange.com/data-products/sample-data/) | 2026-11-15 | verificado |
| **GDELT** | Uso «unlimited and unrestricted», incluido comercial. | Académico y comercial. | Sí. | Sí. | Citar el GDELT Project con enlace a su web. | [GDELT, about](https://www.gdeltproject.org/about.html) | 2026-11-15 | verificado |
| **ACLED** | EULA del 2026-11-01: licencia no comercial; lo que se publique debe ser «transformativo» y no permitir reconstruir los datos; **prohibido usar los datos como entrenamiento, *embeddings* o base de conocimiento de cualquier modelo o sistema sin permiso escrito**; acceso automático solo por su API. | No comercial. Gobiernos y empresas, con licencia aparte. | **No** (solo derivados transformativos). | Solo transformativos y no reversibles; ver sección 7 de la EULA. | Cita visible con fecha de acceso, filtros usados y cambios hechos a los datos. | [EULA](https://acleddata.com/eula); [Atribución](https://acleddata.com/attributionpolicy); [FAQ de acceso](https://acleddata.com/myacled-faqs) | 2026-11-15 | verificado |
| **Ultralytics YOLO** (código y pesos) | AGPL-3.0 por defecto, también para los modelos entrenados con su código; licencia Enterprise de pago para no publicar el proyecto. | Académico y comercial, publicando todo bajo AGPL. | El código y pesos, bajo AGPL. | Sí, publicando el proyecto entero (incluidos, «where applicable», los pesos) bajo AGPL. | Mantener la licencia AGPL. | [Licencia Ultralytics](https://www.ultralytics.com/license) | 2026-11-15 | verificado |

## Textos literales relevantes

**PNOA** (licencia IGN): «el uso de los productos y servicios de información geográfica del IGN […] conlleva la aceptación por el usuario de una licencia CC-BY 4.0». Para obras derivadas: «se añadirá «Obra derivada de» delante de la expresión general […] Como en: Obra derivada de PNOA 2010-2013 CC-BY scne.es». La mención «se mostrará visible junto con los datos, de forma legible y a pie de mapa, imagen, presentación o ventana de visualización».

**DOTA** (dataset.html): «can be used for academic purposes only, but any commercial use is prohibited» y «Use of the Google Earth images must respect the "Google Earth" terms of use».

**xView** (terms.html, 5.1): el dataset se publica «under an Attribution-Noncommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license», y a la vez: «You may use the data and content made available on the Challenge Website to prepare for and compete in the Challenge». No está claro si el uso fuera del concurso está cubierto.

**MAR20 / DIOR** (gcheng-nwpu.github.io): MAR20 «used for research purposes only» y «freely available under the CC BY-NC 4.0 license agreement»; DIOR y DIOR-R: «Both of the two datasets are freely available under the CC BY-NC 4.0 license agreement».

**OpenSky** (documentación): «The API lets you retrieve live airspace information for research and non-commerical purposes». Trino: acceso «available to university-affiliated researchers, governmental organisations, and aviation authorities» para investigación aeronáutica e investigación de incidentes; «Private or commercial entities must contact us for a licence».

**adsb.lol** (GitHub): «This database is made available under the Open Database License»; los repositorios listan además CC0-1.0.

**ADS-B Exchange / JETNET** (términos, 2.a y 2.b): acceso «solely for Customer's internal business purposes»; prohibido «publish, resell, transmit, broadcast, distribute the Services or data acquired from the Services or any Company Data»; derivados permitidos siempre que no se distribuyan «outside Customer's organization».

**GDELT**: «all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee» y «You may redistribute, rehost, republish, and mirror any of the GDELT datasets in any form», con «a citation to the GDELT Project and a link to this website».

**ACLED** (EULA, 3.1): licencia «for non-commercial purposes […] provided that any materials that the Licensee intends to disclose, publish, or distribute externally must be transformative, such that they cannot be reverse engineered to recreate the Licensed Content». (7.1) Prohibido usar el contenido «to train, test, develop, or improve any machine learning model, LLM, AI system […] in any manner that: […] Allows third parties to access, extract, or retrieve Content through such systems […] or Uses Content as training data, embeddings, or knowledge-base input for any model or system, regardless of whether the output is competitive with ACLED's products or services, without ACLED's express prior written consent». (7.2) Ningún agente automático o de IA puede acceder al contenido «except through ACLED's designated API».

**Ultralytics**: «All Ultralytics YOLO trained models fall under the AGPL-3.0 License by default» y «An Enterprise License is required if you want to use Ultralytics YOLO without open-sourcing your entire project».

## Cómo pedir acceso

### OpenSky (base histórica, Trino)

Según la [documentación de Trino](https://openskynetwork.github.io/opensky-api/trino.html):

1. Crear una cuenta en OpenSky y verificar el correo.
2. En «My OpenSky», abrir «Request Data Access» y rellenar el formulario.
3. Se revisa cada solicitud; pueden rechazar las que no estén bien justificadas y retirar el acceso si hay mal uso.

Requisitos que dice la página: estar afiliado a una universidad (o ser organismo público o autoridad aeronáutica) y que el uso sea investigación aeronáutica. Límites de uso: dos consultas a la vez y dos en cola por usuario, 30 minutos como máximo por consulta. Cobertura: `state_vectors_data4` desde 2013 y `flights_data4` desde 2016. **No se ha encontrado** el plazo de respuesta ni si piden aval del tutor; el formulario está en `opensky-network.org`, que no se ha podido abrir desde este entorno.

API REST (sin solicitud, solo cuenta): según la [documentación REST](https://openskynetwork.github.io/opensky-api/rest.html), autenticación OAuth2 (*client credentials*, un sistema de credenciales de aplicación); vectores de estado solo de la última hora; llegadas y salidas por aeropuerto en tramos de hasta dos días y solo del día anterior o antes; trayectorias de no más de 30 días atrás; cupo diario de 4.000 créditos para usuarios registrados. La documentación no dice hasta cuándo hacia atrás llegan las llegadas y salidas.

### ACLED

Según la [FAQ de myACLED](https://acleddata.com/myacled-faqs):

1. Registrarse una vez en `https://acleddata.com/user/register` **con el correo institucional de la universidad**, no con uno personal. Al registrarse se aceptan las condiciones.
2. El nivel de acceso lo da el dominio del correo. Con correo genérico (gmail, etc.) se recibe el nivel abierto («Open»). Si la organización no era usuaria, se empieza en el nivel abierto hasta que su equipo de acceso la evalúe.
3. Niveles: «Open» (solo datos agregados, sin API), «Research» (agregados + datos por evento con retraso, con API), «Partner» y «Enterprise» (de pago o con licencia).
4. Para dudas de nivel o licencias, la página remite a una dirección de correo del equipo de acceso (oculta en la página; no se copia aquí).

No se ha encontrado plazo de respuesta para el nivel «Research» ni requisito de aval. El plazo de «un día laborable» de la FAQ es para licencias Partner o Enterprise.

## Consecuencias para el proyecto

**No se sube al repositorio** (ni a git ni a un remoto público de DVC):

* Imágenes o anotaciones de DOTA, FAIR1M, xView, DIOR y MAR20 (no comerciales; DOTA y MAR20 limitadas a uso académico o de investigación; FAIR1M sin licencia verificada).
* Datos de ACLED en bruto ni tablas que permitan reconstruirlos.
* Nada de ADS-B Exchange (sus condiciones prohíben publicar datos y derivados fuera de la organización). Se recomienda **no usarlo**.
* Datos de OpenSky hasta haber leído sus condiciones completas.
* Las ortofotos PNOA se podrían redistribuir (CC BY 4.0), pero por tamaño van en DVC, no en git.

**Atribuciones que habrá que poner en el README** cuando se usen:

* PNOA: «Obra derivada de PNOA <año> CC-BY 4.0 scne.es», también al pie de cada figura hecha con ortofotos.
* OpenSky: cita del artículo de Schäfer et al. (IPSN 2014).
* adsb.lol: origen y licencia ODbL.
* GDELT: cita y enlace a gdeltproject.org.
* ACLED: cita con fecha de acceso, filtros y cambios hechos.
* DOTA, FAIR1M, xView, DIOR, MAR20: los artículos que pide cada uno.

**Qué condiciona la licencia del repositorio:**

* Si se usa código o pesos de Ultralytics y el repositorio se publica, todo el proyecto tiene que ir bajo AGPL-3.0 (o pagar la licencia Enterprise).
* Los pesos entrenados con DOTA, xView, DIOR o MAR20 heredan su límite no comercial (y en xView, *ShareAlike*). Choca con la parte de AGPL que permite uso comercial: si se publican pesos, hay que avisar de que su uso está limitado por las licencias de los datos.

**Conflictos con lo previsto en el encargo (a decidir por Fable o el autor):**

* **ACLED y la capa de explicación (Fases 5b y MCP 2):** la EULA prohíbe usar los datos de ACLED como «knowledge-base input» de cualquier modelo o sistema sin permiso escrito, y que terceros accedan al contenido a través de esos sistemas. El enfoque previsto (recuperar eventos y que un modelo de lenguaje elija la causa citándolos, y un MCP que sirva eventos de ACLED) parece caer dentro de esa prohibición. Anotado en `docs/specs/fase-0-dudas.md`.
* **ADS-B Exchange** no sirve para un trabajo que se publica.
* **xView**: su texto limita el uso al concurso; mejor no depender de él para resultados publicados mientras no se aclare.
