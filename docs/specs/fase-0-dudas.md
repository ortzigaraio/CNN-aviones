# Fase 0: dudas y hallazgos para Fable

Anotado durante la implementación de la Fase 0. En cada punto se dice qué se ha hecho (siempre la opción más conservadora) y qué hay que decidir.

## Requieren decisión

### 1. ACLED prohíbe usar sus datos como base de conocimiento de un modelo (afecta a las Fases 5b y MCP 2)

La EULA de ACLED (versión del 2026-11-01, sección 7.1) prohíbe usar su contenido «as training data, embeddings, or knowledge-base input for any model or system […] without ACLED's express prior written consent», y que terceros accedan al contenido a través de esos sistemas. El encargo prevé recuperar eventos (GDELT + ACLED) para que un modelo de lenguaje elija la causa citándolos, y un MCP que sirva esos eventos. Tal como está escrita, la EULA parece impedirlo sin permiso escrito. Textos literales en `docs/licencias.md`.

Hecho: nada; solo documentado. Opciones a valorar (no decididas): pedir permiso escrito a ACLED, usar ACLED solo como verdad de evaluación agregada y no como entrada del modelo, o prescindir de ACLED y quedarse con GDELT y comunicados oficiales. Es un cambio de fuentes: lo decide Fable o el autor.

### 2. La fecha PNOA de día solo existe por fotograma

* El WMS de ortofotos da solo **año-mes** (máxima actualidad) o **año** (histórico).
* La fecha de **día** sale de la Fototeca Digital, por **fotograma**, no por zona de la ortofoto. Los servicios consultados no dicen qué fotograma alimenta cada parte del mosaico.
* En muchos casos el aeropuerto está cubierto por fotogramas de varios días (Teruel siempre; Valencia en los tres años; Barcelona 2024 y 2021; Barajas 2020 y 2017).

El criterio 1 de la sección 6 («fecha de vuelo conocida») admite dos lecturas: (a) todos los fotogramas del aeropuerto son de un solo día; (b) hay fecha de día aunque sean varios. En `docs/sitios.md` se han separado los dos casos sin descartar ninguno. Decide Fable.

### 3. La hora por fotograma no se ha podido comprobar

El WMS de la Fototeca no tiene campo de hora. Podría estar en los metadatos internos de los ficheros de fotograma (TIFF de unos 79 MB). Se intentó leer solo la cabecera (los primeros 64 KB) con una petición parcial y el sistema de permisos de la sesión lo denegó. Si se quiere comprobar, el autor tendría que autorizarlo (o preguntar a la Fototeca del CNIG por correo).

### 4. Ruff formatea también Markdown

La versión de ruff que instala `uv` (0.17.5) aplica `ruff format` a los bloques de código Python dentro de los `.md`. `uv run ruff format --check .` fallaba por las firmas de ejemplo de `docs/specs/fase-0.md` y `docs/specs/fase-1b.md`. Para no tocar las especificaciones se ha añadido en `pyproject.toml`:

```toml
[tool.ruff.format]
exclude = ["*.md"]
```

Alternativa: dejar que ruff reformatee los bloques de las specs. Decide Fable.

### 5. DVC envía estadísticas de uso anónimas por defecto

`dvc init` avisa: «DVC has enabled anonymous aggregate usage analytics». No se ha cambiado (no estaba en la especificación). Se puede desactivar con `uv run dvc config core.analytics false`, que lo guarda en `.dvc/config`. Decide el autor.

## Hosts bloqueados o inestables desde el entorno

No se han buscado rodeos; se anota el host:

| Host | Qué pasó | Afecta a |
|---|---|---|
| `opensky-network.org` | 403 (nginx) en cualquier página | Términos de uso de OpenSky, base de aeronaves, formulario de acceso. Se usó la documentación en `openskynetwork.github.io`, que sí carga. |
| `adsb.lol` | 403 con el texto «This network is blocked from adsb.lol because it was used for automated scraping» | Condiciones del sitio. Se usaron sus repositorios en GitHub. |
| `centrodedescargas.cnig.es` | Conexión cerrada sin respuesta | Metadatos y tamaño de las hojas de ortofoto. |
| `fototeca.cnig.es`, `wms-fototeca.idee.es` | Cortes de conexión intermitentes | Se repitieron las consultas hasta tener respuesta completa. |
| `www.fpacbc.usda.gov`, `data.usgs.gov` | 503 y 403 | Licencia de NAIP. |
| `ourairports.com` | Certificado TLS caducado / 503 | Se tomaron las coordenadas del AIP de ENAIRE. |
| `aip.enaire.es` | 403 de su cortafuegos tras varias peticiones seguidas | Se completó con peticiones espaciadas. |

## Menores (sin decisión pendiente, para que conste)

* `requires-python = ">=3.12,<3.13"`: la especificación dice «Python 3.12»; se ha fijado a esa versión menor. El entorno tenía 3.13 por defecto y 3.12 en `/usr/bin/python3.12`; uv usó 3.12.3.
* Se usa `hatchling` como sistema de construcción del paquete (necesario para la disposición `src/` con `uv sync`). No es una dependencia de ejecución.
* El CI usa `actions/checkout@v4` y `astral-sh/setup-uv@v6` con `uv sync --locked` (falla si `uv.lock` no está al día). No se ha podido comprobar que termine en verde: hace falta el push.
* La malla de puntos de `docs/sitios.md` (±2 km) no cubre todo el recinto de los aeropuertos grandes. En Barajas se comprobaron además tres puntos (T4, extremos) y la fecha de 2023 sigue siendo única (28/07/2023). En los otros aeropuertos no se ha ampliado.
