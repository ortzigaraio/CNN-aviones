# Fase 0 — Preparación

Especificación de Fable para Opus. Leer antes `CLAUDE.md` y `docs/encargo.md`.

## 1. Objetivo

Dejar el repositorio listo para trabajar: entorno reproducible, tests y lint (revisión automática de estilo) corriendo en cada push, las dos salvaguardas de los límites del proyecto ya en código, y la información que hace falta para elegir aeropuertos y saber qué datos se pueden usar.

Pregunta que responde: **¿con qué datos y en qué sitios se puede hacer el proyecto, y bajo qué condiciones de uso?**

## 2. Entradas y salidas

Entradas: ninguna más que el repo y acceso web para consultar licencias y fechas de ortofotos.

Salidas (rutas exactas):

| Ruta | Contenido |
|---|---|
| `pyproject.toml`, `uv.lock` | Proyecto `avion-osint`, Python 3.12, disposición `src/`. Dependencia de ejecución: `pyyaml`. Grupo `dev`: `pytest`, `ruff`, `dvc`. Nada más. |
| `.gitignore` | `.env`, `.venv/`, `mlruns/`, `__pycache__/`, cachés de pytest y ruff, `/data/*` salvo ficheros `.dvc` y `.gitignore`. |
| `.env.example` | Solo las variables que existen hoy: `AVION_OSINT_RETRASO_DIAS=30`, `MLFLOW_TRACKING_URI=mlruns`. Sin valores secretos. |
| `src/avion_osint/__init__.py` | Vacío. |
| `src/avion_osint/limites.py` | Salvaguarda retrospectiva (sección 3). |
| `src/avion_osint/aerodromos.py` | Carga de aeródromos (sección 3). |
| `config/aerodromos.yaml` | Aeródromos candidatos (sección 6). |
| `tests/test_limites.py`, `tests/test_aerodromos.py` | Tests (sección 5). |
| `.github/workflows/ci.yml` | En cada push y PR: `uv sync`, `ruff check`, `ruff format --check`, `pytest`. |
| `.dvc/` | Resultado de `dvc init`. Sin remoto (decisión D6). |
| `README.md` | Qué es el proyecto (3-4 líneas), límites (enlace a `CLAUDE.md`), cómo instalar y lanzar tests, mapa de `docs/`. |
| `docs/licencias.md` | Tabla de condiciones de uso (sección 7). |
| `docs/sitios.md` | Fechas de ortofoto verificadas por aeropuerto candidato (sección 6). |
| `docs/cierres/fase-0.md` | Checklist de `CLAUDE.md` sección 5 rellenada + resumen. |

No crear carpetas vacías para fases futuras (decisión D5). No añadir MLflow como dependencia todavía: en esta fase solo se reserva la variable y se ignora `mlruns/`.

## 3. Interfaces

### `avion_osint/limites.py`

```python
RETRASO_MINIMO_DIAS = 30

class FechaDemasiadoRecienteError(ValueError): ...

def retraso_dias() -> int:
    """Lee AVION_OSINT_RETRASO_DIAS. Devuelve max(valor, 30). Sin variable: 30.
    Valor no entero: ValueError."""

def comprobar_fecha_retrospectiva(fecha: date, hoy: date | None = None) -> None:
    """Lanza FechaDemasiadoRecienteError si fecha > hoy - retraso_dias().
    `hoy` por defecto es la fecha actual en UTC; el parámetro existe para los tests."""
```

Reglas:

* El retraso solo se puede subir. `AVION_OSINT_RETRASO_DIAS=5` da 30, no 5 (decisión D3).
* Una fecha exactamente a 30 días se acepta; a 29, se rechaza. Fechas futuras, se rechazan.
* El mensaje de error dice cuál es la fecha más reciente permitida.

### `avion_osint/aerodromos.py`

```python
@dataclass(frozen=True)
class Aerodromo:
    icao: str        # código OACI de 4 letras, p. ej. "LEMD"
    nombre: str
    lat: float
    lon: float
    radio_km: float
    tipo: str        # "civil" | "militar" | "mixto"

    @property
    def solo_agregado(self) -> bool:
        """True si tipo != "civil"."""

def cargar_aerodromos(ruta: Path = <config/aerodromos.yaml>) -> dict[str, Aerodromo]:
    """Clave: código OACI. ValueError si un tipo no es válido o un código está repetido."""
```

Nada más. Sin pydantic, sin caché, sin CLI.

## 4. Partición de datos

No aplica: en esta fase no hay datos ni modelos.

## 5. Métricas y criterios de aceptación

«Hecho» significa que todo esto es cierto y comprobado:

1. En una copia limpia del repo, estos cuatro comandos terminan sin error:
   ```bash
   uv sync
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest
   ```
2. `tests/test_limites.py` cubre como mínimo: fecha a 30 días (pasa), a 29 (falla), futura (falla), variable a 60 (rechaza una fecha a 45 días), variable a 5 (sigue siendo 30), variable no numérica (`ValueError`).
3. `tests/test_aerodromos.py` cubre: carga del YAML real del repo, `solo_agregado` para los tres tipos, tipo inválido (`ValueError`), código repetido (`ValueError`).
4. El flujo de CI existe y, tras el push, termina en verde en GitHub. Si no se puede comprobar desde la sesión, decirlo en el cierre.
5. `git grep` no encuentra claves ni tokens; `.env` no está en git.
6. `docs/licencias.md` y `docs/sitios.md` tienen cada fila marcada como **verificado** (con enlace y fecha de consulta) o **sin verificar** (con el motivo). Ninguna fila rellenada de memoria sin marcar.
7. `docs/cierres/fase-0.md` existe con la checklist rellenada.

## 6. Elección de sitios

### Criterios (fijados por Fable)

Un aeropuerto civil vale si cumple todo:

1. Hay ortofoto PNOA con **fecha de vuelo conocida** sobre el aeropuerto.
2. Esa fecha cae dentro del histórico ADS-B accesible (OpenSky: aproximadamente 2016 en adelante con acceso de investigador; adsb.lol: histórico más corto, a verificar).
3. Tráfico suficiente: más de 30 aviones comerciales visibles en plataforma.
4. No está enmascarado ni degradado en la ortofoto.

### Candidatos

| OACI | Aeropuerto | Tipo | Por qué |
|---|---|---|---|
| LEMD | Madrid-Barajas | civil | Mejor cobertura ADS-B, más aviones. Sitio de la Fase 1b. |
| LEBL | Barcelona-El Prat | civil | Reserva de la 1b. Tráfico alto. |
| LEPA | Palma de Mallorca | civil | Mucha estacionalidad; otra región PNOA (otra fecha de vuelo). |
| LETL | Teruel | civil | Estacionamiento de larga estancia: verdad fuerte casi segura, pero exige meses de histórico. |
| LEVC | Valencia | civil | Reserva. |
| LEZG | Zaragoza | mixto | Solo para comprobar que la regla de agregación funciona. No se usa en la validación civil. |

`config/aerodromos.yaml` lleva estos seis, con coordenadas del punto de referencia del aeródromo y `radio_km: 5`. Las coordenadas se toman de una fuente pública (AIP de ENAIRE u OurAirports) y se cita cuál.

Las bases para la parte de anomalías **no** se eligen ahora: dependen de la cobertura ADS-B que se mida en la Fase 1.

### Tarea de verificación → `docs/sitios.md`

Para cada candidato civil, averiguar y anotar:

* Año y **fecha de vuelo** de la ortofoto PNOA más reciente y de las anteriores disponibles (PNOA histórico) desde 2016.
* De dónde sale la fecha (Centro de Descargas del CNIG, capa de fechas de vuelo, consulta `GetFeatureInfo` al servicio WMS, metadatos del fichero). Enlace.
* Si existe **hora** por fotograma o por pasada (Fototeca Digital, metadatos de los fotogramas). Sí / no / no se ha podido comprobar.
* Si el aeropuerto queda partido entre hojas o pasadas con fechas distintas.
* Resolución (GSD: tamaño real de cada píxel).
* Tamaño aproximado de la descarga.

**No descargar ortofotos en esta fase.** Solo consultar metadatos y páginas. Si la red del entorno bloquea el sitio del CNIG, marcar «sin verificar» y decir qué host hace falta.

## 7. `docs/licencias.md`

Una fila por fuente. Columnas: fuente · licencia o condiciones · uso permitido (académico / comercial) · se pueden redistribuir los datos · se pueden publicar modelos entrenados o resultados derivados · atribución exigida · enlace a las condiciones · fecha de consulta · estado (verificado / sin verificar).

Fuentes:

* Imágenes: PNOA (IGN/CNIG), NAIP.
* Datasets: DOTA, FAIR1M, xView, DIOR, MAR20.
* Tráfico: OpenSky (API REST y base histórica), base de aeronaves de OpenSky, adsb.lol, ADS-B Exchange.
* Noticias: GDELT, ACLED.
* Software con efecto sobre la licencia del repo: Ultralytics YOLO (código y pesos preentrenados).

Añadir al final una sección corta «Consecuencias para el proyecto»: qué no se puede subir al repo, qué atribuciones hay que poner en el README y qué condiciona la licencia del propio repositorio.

Para OpenSky y ACLED, anotar además **cómo se pide el acceso** y qué exigen (afiliación, aval, plazos), para que el autor pueda hacer la solicitud.

## 8. Riesgos y qué hacer

| Riesgo | Qué hacer |
|---|---|
| La red del entorno bloquea CNIG, OpenSky u otros sitios. | No insistir ni buscar rodeos. Marcar «sin verificar», anotar el host en `docs/specs/fase-0-dudas.md`. |
| Una licencia es ambigua. | Copiar el texto literal relevante con su enlace y marcarla como «ambigua»; no interpretarla a favor. |
| El CNIG no publica fecha de vuelo fiable para un aeropuerto. | Anotarlo; ese aeropuerto queda descartado. No estimar la fecha. |
| `dvc` trae muchas dependencias y alarga el CI. | Aceptable. Si el CI pasa de 3 minutos, anotarlo en dudas; no cambiar de herramienta. |

## 9. Tareas para Opus, en orden

1. `pyproject.toml` + `uv sync` + `uv.lock`. Configuración de `ruff` y `pytest` dentro de `pyproject.toml`.
2. `.gitignore` y `.env.example`.
3. `limites.py` con sus tests (escribir primero los tests).
4. `config/aerodromos.yaml`, `aerodromos.py` y sus tests.
5. `dvc init`.
6. `.github/workflows/ci.yml`.
7. `README.md`.
8. `docs/licencias.md` (consultando las fuentes en la web).
9. `docs/sitios.md` (consultando el CNIG).
10. Pasar los cuatro comandos de la sección 5 y rellenar `docs/cierres/fase-0.md`.

Fuera de alcance: código de descarga, MCP, modelos, notebooks, MLflow como dependencia, remoto de DVC, cualquier descarga de datos.

## 10. Lo que tiene que hacer el autor (no Opus)

* Pedir el acceso de investigador a OpenSky y el acceso a ACLED, con aval del tutor (los pasos quedarán en `docs/licencias.md`).
* Decidir dónde se entrena y si el repo será público.
* Confirmar o rechazar la decisión D3 (retraso mínimo no rebajable).
