# Registro de decisiones

Formato: fecha, decisión, alternativas descartadas, motivo. Las decisiones de diseño las toma Fable o el autor; Opus propone en `docs/specs/fase-N-dudas.md`.

| Nº | Fecha | Decisión | Alternativas descartadas | Motivo |
|---|---|---|---|---|
| D1 | 2026-11-15 | Una sola rama, `main`. Se trabaja directamente en ella. | Rama por fase con PR. | Petición del autor. |
| D2 | 2026-11-15 | Paquete Python `avion_osint` en `src/avion_osint/` (subpaquetes `adsb`, `fusion`, …). | `src/adsb`, `src/news`… como en el encargo. | Evita paquetes de nombre genérico que chocan con otras librerías. |
| D3 | 2026-11-15 | El retraso mínimo retrospectivo es de 30 días y solo se puede **subir** por configuración (`AVION_OSINT_RETRASO_DIAS`), nunca bajar. | Totalmente configurable, como dice el encargo. | Una salvaguarda que se apaga con una variable no protege nada. **Pendiente de confirmación del autor.** |
| D4 | 2026-11-15 | Los aeródromos se declaran en `config/aerodromos.yaml` con `tipo`: `civil`, `militar` o `mixto`. Todo lo que no sea `civil` se trata como militar a efectos de agregación. | Decidirlo caso a caso en cada módulo. | La regla de agregación necesita una única fuente de verdad. |
| D5 | 2026-11-15 | Solo se crean carpetas y dependencias cuando una fase las usa. | Crear en la Fase 0 todo el árbol de la sección 6 del encargo. | Simplicidad; carpetas vacías no aportan. |
| D6 | 2026-11-15 | DVC inicializado sin almacenamiento remoto y MLflow con registro local en `mlruns/`, hasta que el autor decida dónde se entrena. | Configurar ya un remoto (Drive, S3). | Depende de la GPU y de la cuenta que se use; decisión del autor. |
| D7 | 2026-11-15 | La Fase 1b se hace en Madrid-Barajas (LEMD); reservas: Barcelona (LEBL), Palma (LEPA). Condicionado a que la fecha de la ortofoto tenga ADS-B disponible. | Teruel (LETL) como primer sitio. | Barajas tiene la mejor cobertura ADS-B y más de cien aviones por foto. Teruel (estancias de meses) es mejor para verdad fuerte pero exige mucho histórico; se reserva para la Fase 4. |
| D8 | 2026-11-15 | Los umbrales de decisión de la Fase 1b quedan fijados en `docs/specs/fase-1b.md` antes de ver ningún dato. | Decidir a la vista del resultado. | Evita ajustar el criterio al resultado. |
| D9 | 2026-11-15 | La ortofoto usada en la Fase 1b se considera dato de desarrollo: en la Fase 4 se reporta aparte y no cuenta para el resultado central. | Reutilizarla como una más. | Se habrá mirado y usado para ajustar el método. |
| D10 | 2026-11-15 | «Fecha de vuelo conocida» significa que todos los fotogramas que cubren el aeropuerto son de **un solo día**. Excepción: Teruel (LETL), donde se admiten varios días porque los aviones pasan allí meses. | Admitir cualquier aeropuerto con fecha de día aunque mezcle varios. | Con días mezclados no se sabe qué día corresponde a cada zona de la foto. Resuelve la duda 2 de la Fase 0. |
| D11 | 2026-11-15 | Aeropuertos civiles del núcleo: **LEMD** (2023; es la foto de la Fase 1b, dato de desarrollo), **LEPA** (2024, 2021, 2018) y **LEBL** (2018). **LETL** como caso de larga estancia. LEVC descartado. Las fechas anteriores a 2023 dependen de conseguir el acceso histórico de OpenSky. | Mantener LEVC; usar las fechas de varios días de LEBL y LEMD. | Aplicación de D10 a las fechas verificadas en `docs/sitios.md`. Con solo adsb.lol quedan LEMD 2023 y LEPA 2024. |
| D12 | 2026-11-15 | ACLED **no** se usa como entrada del modelo de lenguaje ni se sirve por el MCP 2. La capa de contexto se hace con GDELT y comunicados oficiales. **Pendiente de confirmación del autor.** | Pedir permiso escrito a ACLED; usarlo igualmente. | Su EULA (sección 7.1) prohíbe usar los datos como base de conocimiento de un modelo sin permiso escrito. Resuelve la duda 1 de la Fase 0. Si el autor consigue el permiso, se revisa. |
| D13 | 2026-11-15 | `ruff format` no toca los `.md`; telemetría de DVC desactivada. | Dejar que ruff reformatee los ejemplos de las specs; dejar la telemetría por defecto. | Los bloques de las specs son firmas ilustrativas. La telemetría no aporta nada al proyecto. Resuelve las dudas 4 y 5. |
| D14 | 2026-11-15 | Se entrena en local con la GPU del autor (RTX 3070, 8 GB) y, si no basta, en Kaggle. Los modelos y tamaños de lote se eligen para caber en 8 GB. | Colab; GPU de la universidad. | Decisión del autor. 8 GB bastan para un detector YOLO pequeño o mediano y un clasificador ligero. |
| D15 | 2026-11-15 | El repositorio es público. Por usar Ultralytics (AGPL-3.0), el repo se publica bajo AGPL-3.0; el fichero `LICENSE` se añade al empezar la Fase 1b. Los datos no se suben (van por DVC) y los modelos entrenados con DOTA, DIOR, MAR20 o xView quedan como de uso no comercial. | Repo privado; otro detector con licencia más permisiva. | Decisión del autor. AGPL obliga a publicar el código bajo la misma licencia, lo que encaja con un TFG público. |

## Pendientes de decidir

| Tema | Quién decide | Cuándo |
|---|---|---|
| Remoto de DVC (propuesta: una carpeta o disco en el PC del autor) | Autor | Al descargar los primeros datos (Fase 1b) |
| Bases y ejercicios para anomalías | Fable, con la cobertura ADS-B medida en la Fase 1 | Spec de la Fase 5 |
| Taxonomía de tipos (ver revisión del encargo, punto 1) | Fable | Spec de la Fase 3 |
