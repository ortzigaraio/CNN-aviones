# CLAUDE.md

Proyecto: detección y clasificación de aviones en ortofotos, contrastada con tráfico aéreo (ADS-B) y noticias públicas. Análisis **retrospectivo** con fuentes abiertas.

**Antes de empezar cualquier tarea, lee entero `docs/encargo.md`.** Este fichero resume sus secciones 0, 0.1, 1 y 7; si hay contradicción, manda este fichero y se avisa al autor.

## 1. Normas comunes

* Responde en castellano, claro y sin rodeos. Explica cada término técnico con palabras sencillas la primera vez que salga.
* Antes de algo grande o difícil de deshacer (borrar datos, migraciones, descargas masivas, publicar, gastar dinero en APIs o GPU), explica qué vas a hacer y espera el visto bueno.
* Nunca pidas, repitas ni guardes contraseñas, tokens o claves. Van en `.env` (fuera de git); en git solo `.env.example` con los nombres.
* Si algo falla o no se ha podido probar, dilo tal cual. No inventes resultados, métricas, licencias ni rutas.

## 2. Git

* Autor y committer: `OG <144943468+ortzigaraio@users.noreply.github.com>`.
* Nunca añadir Co-Authored-By, Claude-Session, «Generated with Claude Code» ni ninguna línea que nombre a Claude o a Anthropic en commits, PRs ni merges.
* Una sola rama: `main`. No crear ramas ni abrir PRs si no se pide. Si se crea otra rama, se borra al terminar.
* Cada PR o merge lleva título y descripción en castellano: qué cambia, por qué, qué tiene que hacer el autor, cómo se ha probado.

## 3. Reparto de trabajo

Fable 5.2 diseña y revisa; Opus 5.5 construye. El puente entre sesiones son los ficheros de `docs/`, no la memoria de la conversación.

| Quién | Hace | No hace |
|---|---|---|
| Fable | Plan, riesgos, alcance. `docs/specs/fase-N.md`. Decisiones de diseño (particiones, métricas, umbrales, fuentes). Revisión en `docs/revisiones/fase-N.md`. | Código. |
| Opus | Código, tests, scripts, configuración, MCP. Cierre en `docs/cierres/fase-N.md` (checklist de la sección 5 + resumen de resultados). | Tomar decisiones de diseño: las propone. |

Opus **para y anota en `docs/specs/fase-N-dudas.md`** (y avisa) si hay que: cambiar la partición de datos, cambiar una métrica o un umbral, añadir una fuente de datos, si un resultado es sorprendentemente bueno (sospecha de fuga), o ante cualquier duda sobre los límites.

Las decisiones importantes se registran en `docs/decisiones.md` (fecha, decisión, alternativas descartadas, motivo).

## 4. Límites del proyecto (fijos)

* Solo datos públicos o de acceso académico, respetando sus condiciones de uso (`docs/licencias.md`).
* Solo análisis retrospectivo. Todo pipeline y todo MCP pasa las fechas por `avion_osint.limites`, que rechaza fechas con menos de 30 días de antigüedad. El retraso se puede subir, nunca bajar de 30.
* No es un sistema de seguimiento en vivo, ni de alerta de operaciones, ni de predicción de ataques, ni de selección de objetivos.
* En aeródromos militares o mixtos (`tipo` distinto de `civil` en `config/aerodromos.yaml`): solo resultados agregados por aeródromo y día/semana. Nada de trayectorias ni identificadores de aviones concretos.
* Una anomalía es «actividad inusual» con su explicación pública más probable y sus fuentes citadas. Nunca «misión confirmada» ni «ataque inminente». Sin evidencia: «sin explicación pública».
* Si una tarea se acerca a estos límites: detente y dilo.

## 5. Checklist de cierre de fase

Opus la rellena en `docs/cierres/fase-N.md`; Fable la usa para revisar.

- [ ] **Fugas de datos:** ¿mismo aeródromo, escena o fecha en train y test? ¿Periodos mezclados al evaluar anomalías? ¿Noticias posteriores al corte de *k* días?
- [ ] **Métricas engañosas:** F1 por clase y matriz de confusión siempre. ¿Hay línea base sencilla para comparar?
- [ ] **Incertidumbre:** con pocos casos, intervalos de confianza.
- [ ] **Cambio de dominio:** evaluado en datos de origen y en PNOA/NAIP por separado.
- [ ] **Explicaciones:** cada causa con evidencia citada.
- [ ] **Reproducibilidad:** semillas fijas, datos en DVC, experimentos en MLflow, comando para repetir.
- [ ] **Tests:** cada módulo de `src/` con tests; los MCP con respuestas guardadas.
- [ ] **Licencias:** ¿los datos permiten lo que se ha hecho con ellos?
- [ ] **Límites:** retraso mínimo y agregación militar respetados.
- [ ] **Honestidad:** lo no probado está dicho como tal.

## 6. Comandos

```bash
uv sync                      # instalar el entorno
uv run pytest                # tests
uv run ruff check .          # lint (revisión de estilo y errores típicos)
uv run ruff format --check . # formato
```

## 7. Guías de comportamiento

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

* State your assumptions explicitly. If uncertain, ask.
* If multiple interpretations exist, present them - don't pick silently.
* If a simpler approach exists, say so. Push back when warranted.
* If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

* No features beyond what was asked.
* No abstractions for single-use code.
* No "flexibility" or "configurability" that wasn't requested.
* No error handling for impossible scenarios.
* If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:

* Don't "improve" adjacent code, comments, or formatting.
* Don't refactor things that aren't broken.
* Match existing style, even if you'd do it differently.
* If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

* Remove imports/variables/functions that YOUR changes made unused.
* Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

* "Add validation" → "Write tests for invalid inputs, then make them pass"
* "Fix the bug" → "Write a test that reproduces it, then make it pass"
* "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

These guidelines are working if: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
