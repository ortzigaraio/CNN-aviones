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

## Pendientes de decidir

| Tema | Quién decide | Cuándo |
|---|---|---|
| Dónde se entrena (GPU) y remoto de DVC | Autor | Antes de la Fase 2 |
| Repositorio público o privado y licencia del repo | Autor | Antes de usar pesos de Ultralytics (Fase 1b) |
| Aeropuertos civiles definitivos (3-4) | Fable, con las fechas PNOA verificadas en la Fase 0 | Cierre de la Fase 0 |
| Bases y ejercicios para anomalías | Fable, con la cobertura ADS-B medida en la Fase 1 | Spec de la Fase 5 |
| Taxonomía de tipos (ver revisión del encargo, punto 1) | Fable | Spec de la Fase 3 |
