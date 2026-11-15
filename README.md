# CNN-aviones (`avion-osint`)

Proyecto académico de detección y clasificación de aviones en ortofotos (fotos aéreas corregidas para que tengan escala uniforme, como un mapa) con redes neuronales convolucionales (CNN), contrastada con datos de tráfico aéreo ADS-B (la señal con posición e identificador que emiten los aviones) y con noticias públicas. Es un análisis **retrospectivo** hecho solo con fuentes abiertas (OSINT).

## Límites

El proyecto tiene límites fijos: solo datos públicos o de acceso académico, solo fechas con al menos 30 días de antigüedad, nada de seguimiento en vivo ni de alerta de operaciones, y resultados solo agregados en aeródromos militares o mixtos. Están descritos en [`CLAUDE.md`](CLAUDE.md) (sección 4) y en [`docs/encargo.md`](docs/encargo.md) (sección 1). En código, la salvaguarda del retraso mínimo está en `src/avion_osint/limites.py` y la lista de aeródromos con su tipo en `config/aerodromos.yaml`.

## Instalación y tests

Hace falta [uv](https://docs.astral.sh/uv/) (gestor de entornos y dependencias de Python). El proyecto usa Python 3.12; uv lo instala si no está.

```bash
uv sync                      # instalar el entorno
uv run pytest                # tests
uv run ruff check .          # lint (revisión de estilo y errores típicos)
uv run ruff format --check . # formato
```

Las variables de entorno que existen están en `.env.example`. Para cambiarlas, copiar a `.env` (que no va a git).

Los datos se versionarán con DVC (herramienta de control de versiones para datos); de momento está inicializado sin almacenamiento remoto.

## Mapa de `docs/`

| Ruta | Contenido |
|---|---|
| `docs/encargo.md` | Planteamiento completo del proyecto, plan por fases y normas. |
| `docs/decisiones.md` | Registro de decisiones de diseño. |
| `docs/licencias.md` | Condiciones de uso de cada fuente de datos y software. |
| `docs/sitios.md` | Fechas de vuelo de las ortofotos PNOA de los aeropuertos candidatos. |
| `docs/specs/` | Especificación de cada fase (`fase-N.md`) y dudas abiertas (`fase-N-dudas.md`). |
| `docs/revisiones/` | Revisión de cada fase o documento. |
| `docs/cierres/` | Cierre de cada fase: checklist y resumen de resultados. |

## Atribuciones

Las atribuciones que exige cada fuente están en [`docs/licencias.md`](docs/licencias.md), sección «Consecuencias para el proyecto». Se completarán aquí a medida que cada fuente se use de verdad.
