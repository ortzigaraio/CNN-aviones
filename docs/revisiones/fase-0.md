# Revisión de la Fase 0 (Fable, 2026-11-15)

**Veredicto: aprobada, con puntos abiertos que no bloquean la Fase 1b.**

## Qué se ha revisado

* El código de `src/avion_osint/` y sus tests, leído entero.
* Los cuatro comandos de la spec, ejecutados de nuevo por el revisor: lint y formato sin errores, 14 tests pasan.
* `docs/specs/fase-0-dudas.md` y el informe de cierre.
* `docs/licencias.md` y `docs/sitios.md` **no** se han contrastado fila a fila contra las fuentes: se aceptan con el estado (verificado / sin verificar) que les puso Opus.

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| 1. Los cuatro comandos pasan | Cumplido. |
| 2. Tests de `limites` | Cumplido (8 tests; cubren los seis casos pedidos). |
| 3. Tests de `aerodromos` | Cumplido (6 tests). |
| 4. CI en verde en GitHub | Cumplido (ver el final). |
| 5. Sin claves en git | Cumplido. |
| 6. Filas marcadas como verificadas o sin verificar | Cumplido. Quedan sin verificar NAIP, FAIR1M y los términos de OpenSky, por bloqueo de red o porque la fuente no publica licencia. |
| 7. Cierre con checklist | Cumplido. |

## Código

Se ajusta a la spec y no añade nada de más. La salvaguarda retrospectiva hace lo que debe: el retraso no se puede bajar de 30 días por configuración. Sin observaciones.

## Resolución de las dudas

| Duda | Resolución |
|---|---|
| 1. ACLED prohíbe usar sus datos como entrada de un modelo | ACLED queda fuera del modelo y del MCP 2 (decisión D12). Pendiente de que el autor lo confirme. |
| 2. Aeropuertos con fotogramas de varios días | Solo valen los de un único día, salvo Teruel (D10). Selección definitiva en D11. |
| 3. Hora por fotograma sin comprobar | No bloquea: la Fase 1b acota la hora con sombras y con ADS-B. El autor puede preguntar a la Fototeca del CNIG si la hora existe. |
| 4. Ruff y los Markdown | Aceptada la exclusión (D13). |
| 5. Telemetría de DVC | Desactivada por el revisor (D13). |

## Hallazgos que cambian el plan

1. **El día de vuelo solo existe por fotograma, no por zona del mosaico.** Reduce los sitios útiles: Barajas 2023, Palma (tres fechas) y Barcelona 2018. Valencia cae.
2. **Sin acceso histórico a OpenSky solo quedan dos fotos** (Barajas 2023 y Palma 2024), porque adsb.lol empieza en febrero de 2023. Una de ellas es la de la prueba de concepto. El acceso a OpenSky pasa a ser el punto crítico del proyecto.
3. **La cobertura en tierra de adsb.lol está sin medir.** Es lo primero que dirá la Fase 1b.
4. **Ultralytics (AGPL-3.0)** obliga a publicar el repo bajo esa licencia si se distribuye, y los modelos entrenados con DOTA, DIOR, MAR20 o xView quedan limitados a uso no comercial. Asumible para un TFG; el autor debe decidirlo antes de la Fase 1b.
5. **FAIR1M no tiene licencia localizable.** Hasta que se aclare, no se puede contar con él; afecta a las Fases 2 y 3.

## Pendiente para el autor

* Solicitar el acceso de investigador a OpenSky (con correo y afiliación de la universidad) cuanto antes.
* Confirmar D3 (retraso no rebajable) y D12 (ACLED fuera).
* Decidir si el repo es público y dónde se entrena.

## CI

El flujo de CI terminó en verde en GitHub para el commit de la Fase 0 (`5cf2b49`), en unos 10 segundos. Criterio 4 cumplido.
