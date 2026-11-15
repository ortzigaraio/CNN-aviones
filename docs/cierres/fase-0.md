# Cierre de la Fase 0 — Preparación

Fecha: 2026-11-15. Especificación: `docs/specs/fase-0.md`. Dudas abiertas: `docs/specs/fase-0-dudas.md`.

## Resumen

* Entorno con `uv` (gestor de entornos de Python): proyecto `avion-osint`, Python 3.12, disposición `src/`, dependencia de ejecución `pyyaml` y grupo `dev` con `pytest`, `ruff` y `dvc`. `uv.lock` generado.
* Salvaguardas en código:
  * `src/avion_osint/limites.py`: rechaza fechas con menos de 30 días de antigüedad; `AVION_OSINT_RETRASO_DIAS` solo puede subir el retraso (decisión D3).
  * `src/avion_osint/aerodromos.py` + `config/aerodromos.yaml`: seis aeródromos con su tipo; `solo_agregado` es cierto para todo lo que no es `civil`. Coordenadas del AIP de ENAIRE (apartado AD 2.2).
* 14 tests (8 de límites, 6 de aeródromos), todos pasan.
* DVC (control de versiones para datos) inicializado sin remoto (D6). CI de GitHub Actions con `uv sync --locked`, `ruff check`, `ruff format --check` y `pytest`.
* `docs/licencias.md`: 15 fuentes; 10 verificadas (3 de ellas con ambigüedad anotada), 4 sin verificar y 1 mixta (OpenSky Trino: acceso verificado, licencia de datos sin verificar).
* `docs/sitios.md`: fechas de vuelo **de día** para los cinco aeropuertos civiles (2017-2024), obtenidas de la Fototeca Digital por fotograma. No hay hora en ningún servicio consultado.

### Hallazgos que afectan al diseño

1. **Fecha PNOA:** la ortofoto solo publica año-mes; el día sale de los fotogramas. Barajas 2023 (28/07/2023), Barcelona 2018, Palma 2018, 2021 y 2024 tienen un solo día sobre el aeropuerto; el resto mezcla días (Teruel 2021, hasta seis semanas).
2. **Histórico ADS-B:** OpenSky `flights_data4` desde 2016 (con acceso de investigador); adsb.lol publica volcados diarios en GitHub desde el 2023-02-16 con licencia ODbL. Con solo adsb.lol, sirven LEMD 2023 y las fechas de 2024.
3. **ACLED:** su EULA prohíbe usar sus datos como base de conocimiento de modelos sin permiso escrito; choca con el diseño de la Fase 5b y del MCP 2 (duda 1).
4. **ADS-B Exchange:** sus condiciones impiden publicar datos y derivados; no sirve para un trabajo publicado.

## Comandos de comprobación

Ejecutados en una copia limpia (sin `.venv`) y en el repositorio, con el mismo resultado:

```text
$ uv sync
Resolved 103 packages ...  (instalación completa, sin error)
$ uv run ruff check .
All checks passed!
$ uv run ruff format --check .
5 files already formatted
$ uv run pytest
tests/test_aerodromos.py ......                                          [ 42%]
tests/test_limites.py ........                                           [100%]
============================== 14 passed in 0.04s ==============================
```

## Criterios de aceptación (sección 5 de la especificación)

1. Cuatro comandos sin error en copia limpia: **sí** (arriba).
2. Tests de `limites`: **sí** (30 días pasa, 29 falla, futura falla, variable a 60 rechaza 45 días, variable a 5 sigue en 30, variable no numérica da `ValueError`; además, sin variable = 30 y el mensaje incluye la fecha más reciente permitida).
3. Tests de `aerodromos`: **sí** (YAML real, `solo_agregado` para los tres tipos, tipo inválido, código repetido).
4. CI en verde en GitHub: **no comprobado**. El flujo existe, pero en esta sesión no se ha hecho commit ni push.
5. Sin claves ni tokens en git y `.env` fuera de git: **sí** (`git grep` de patrones de clave sin resultados; `.env` ignorado y no presente).
6. Cada fila de licencias y sitios marcada como verificado o sin verificar: **sí**.
7. Este cierre: **sí**.

## Checklist (`CLAUDE.md`, sección 5)

- [x] **Fugas de datos:** no aplica; no hay datos ni modelos en esta fase.
- [x] **Métricas engañosas:** no aplica.
- [x] **Incertidumbre:** no aplica.
- [x] **Cambio de dominio:** no aplica.
- [x] **Explicaciones:** no aplica. Las fechas y licencias anotadas llevan su fuente enlazada.
- [ ] **Reproducibilidad:** entorno fijado con `uv.lock` y DVC inicializado. Sin remoto de DVC ni MLflow todavía (D6, pendiente del autor). No hay semillas porque no hay experimentos.
- [x] **Tests:** los dos módulos de `src/` tienen tests. No hay MCP todavía.
- [x] **Licencias:** revisadas en `docs/licencias.md`. No se ha descargado ningún dato.
- [x] **Límites:** retraso mínimo de 30 días en código y probado; la regla de agregación tiene su fuente de verdad (`tipo` en `config/aerodromos.yaml`). Ningún pipeline la usa aún.
- [x] **Honestidad:** lo no comprobado está dicho: CI en GitHub, hora por fotograma, tamaño de las hojas de ortofoto, criterios 3 y 4 de elección de sitios (exigen mirar la imagen), licencias de NAIP, FAIR1M y OpenSky (hosts bloqueados o sin texto de licencia).

## Pendiente para el autor

* Pedir acceso a OpenSky (Trino) y a ACLED con correo de la universidad (pasos en `docs/licencias.md`).
* Decidir sobre las dudas 1-5 de `docs/specs/fase-0-dudas.md` (con Fable cuando sean de diseño).
* Hacer commit y push, y comprobar que el CI termina en verde (y cuánto tarda; si pasa de 3 minutos, anotarlo).
