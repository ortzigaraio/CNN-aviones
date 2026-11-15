# Fase 1b — Prueba de concepto de la verdad terreno

Especificación de Fable para Opus. Leer antes `CLAUDE.md`, `docs/encargo.md` (sección 2, punto débil 2) y `docs/revisiones/encargo.md` (puntos 2, 8 y 11).

*Verdad terreno* = lo que se toma como «lo que había de verdad» para medir cuánto acierta el sistema. Aquí, los aviones que ADS-B dice que estaban en tierra.

## 1. Objetivo

Con **una** ortofoto de **un** aeropuerto, responder antes de entrenar nada:

> De los aviones que se ven en la foto, ¿cuántos se pueden explicar con ADS-B?

El resultado decide si el resultado central del proyecto se mantiene, se ajusta o se replantea (sección 7). Es una fase de medir, no de construir: el código es el mínimo para obtener el número y poder repetirlo.

## 2. Requisitos previos

* Fase 0 cerrada, con `docs/sitios.md` verificado para el aeropuerto elegido.
* Sitio: Madrid-Barajas (LEMD). Si su ortofoto no tiene fecha fiable o no hay ADS-B de esa fecha, pasar a LEBL y luego a LEPA (decisión D7). Anotar el cambio en `docs/decisiones.md`.
* **Visto bueno del autor** antes de descargar la ortofoto y antes de descargar ADS-B (norma de descargas). Opus dice antes qué va a bajar, de dónde y cuánto ocupa.
* El autor ha decidido si el repo es público (condiciona usar pesos de Ultralytics, licencia AGPL-3.0).

## 3. Entradas y salidas

### Entradas

| Dato | Origen | Ruta |
|---|---|---|
| Ortofoto PNOA del aeropuerto, a resolución nativa, con su fecha de vuelo. Preferir la hoja o el fotograma original antes que el mosaico servido por WMS, que oculta las costuras entre pasadas. | CNIG | `data/fase-1b/ortofoto/` |
| ADS-B del aeropuerto desde 7 días antes hasta 7 días después de la fecha de la foto. | Por orden de preferencia: (1) base histórica de OpenSky si ya hay acceso; (2) API REST de OpenSky, llegadas y salidas por aeropuerto, si admite esa fecha; (3) histórico de adsb.lol. Anotar cuál se usó y por qué. | `data/fase-1b/adsb/` |
| Tabla icao24 → tipo OACI. | Base de aeronaves de OpenSky. | `data/fase-1b/aeronaves.parquet` |
| Pesos de un detector de cajas orientadas preentrenado en DOTA, **sin ajustar**. | Ultralytics (modelo OBB pequeño o mediano). | No se versionan; se anota nombre y versión exactos. |

Todo `data/` va con DVC, no a git. Comprobar en `docs/licencias.md` que cada dato permite este uso.

### Salidas

| Ruta | Contenido |
|---|---|
| `data/fase-1b/conteo_manual.geojson` | Un punto por avión visible, hecho **por el autor** (sección 5, paso B). |
| `data/fase-1b/detecciones.geojson` | Salida del detector. |
| `data/fase-1b/en_tierra.parquet` | Aviones en tierra inferidos de ADS-B (esquema abajo). |
| `docs/informes/fase-1b.md` | Informe corto con los números de la sección 7 y la recomendación. |
| `docs/cierres/fase-1b.md` | Checklist de cierre. |

Esquema de `en_tierra.parquet`:

| Columna | Tipo | Significado |
|---|---|---|
| `icao24` | texto | Código del transpondedor. |
| `tipo_oaci` | texto o nulo | P. ej. `A320`. Nulo si no está en la base. |
| `categoria` | texto | `ligero`, `regional`, `pasillo_unico`, `fuselaje_ancho`, `desconocido`. |
| `llegada` | fecha-hora UTC o nulo | Último aterrizaje antes del intervalo. Nulo si es anterior a la ventana. |
| `salida` | fecha-hora UTC o nulo | Primer despegue después. Nulo si es posterior a la ventana. |
| `verdad` | texto | `fuerte` o `debil` (definición en el paso D). |

Esquema de `conteo_manual.geojson` (propiedades de cada punto): `categoria` (las mismas cinco), `zona` (`terminal`, `remoto`, `mantenimiento`, `aviacion_general`), `en_movimiento` (sí/no: en pista o calle de rodaje), `longitud_m` (medida en QGIS, opcional).

Categorías por longitud del avión: `ligero` < 20 m · `regional` 20-30 m · `pasillo_unico` 30-45 m · `fuselaje_ancho` > 45 m. Para ADS-B, la categoría sale de una tabla tipo OACI → categoría escrita a mano en `config/categorias_tipo.yaml` solo para los tipos que aparezcan.

## 4. Interfaces

En `src/avion_osint/fusion/`, con tests. Se reutilizarán en la Fase 4, por eso van en `src/` y no en un notebook.

```python
def hora_por_sombra(lat: float, lon: float, fecha: date, acimut_sombra_grados: float
                    ) -> datetime:
    """Hora UTC en la que el sol proyecta una sombra con ese acimut (dirección, en
    grados desde el norte) en ese lugar y día. ValueError si no hay solución."""

def inferir_en_tierra(llegadas: DataFrame, salidas: DataFrame,
                      t_min: datetime, t_max: datetime,
                      margen: timedelta = timedelta(minutes=30)) -> DataFrame:
    """Devuelve la tabla en_tierra (sin tipo ni categoría).
    llegadas y salidas: columnas icao24, instante (UTC)."""

def comparar_conteos(foto: Mapping[str, int], adsb: Mapping[str, int]) -> dict:
    """Por categoría: n_foto, n_adsb, explicados = min(n_foto, n_adsb).
    Total: cobertura = suma(explicados) / suma(n_foto), con intervalo de Wilson al 95 %;
    exceso_adsb = suma(max(n_adsb - n_foto, 0)) / suma(n_adsb)."""
```

Toda fecha pasa por `avion_osint.limites.comprobar_fecha_retrospectiva` antes de descargar nada.

La descarga puntual de ADS-B y la ejecución del detector son guiones sencillos en `scripts/fase_1b/`; no se generalizan (el pipeline de verdad es la Fase 1).

## 5. Procedimiento

### A. Acotar el momento de la foto → intervalo `[t_min, t_max]`

Tres métodos, del más al menos directo. Aplicar todos los que se pueda y anotar si coinciden:

1. **Metadatos:** hora del fotograma o de la pasada, si el CNIG la da.
2. **Sombras:** medir en QGIS el acimut de la sombra de 3 o más objetos verticales (torre de control, farolas de plataforma) y aplicar `hora_por_sombra`. El intervalo es la media ± la dispersión entre objetos, y nunca menos de ± 15 min.
3. **Reloj ADS-B:** para cada avión marcado `en_movimiento` en el conteo manual, buscar en ADS-B un avión cuya posición coincida (a menos de 100 m) en algún instante del día. Cada coincidencia fija la hora al minuto.

Si los métodos se contradicen, o los aviones en movimiento de zonas distintas dan horas distintas, la foto mezcla pasadas: partir el aeropuerto en zonas, cada una con su intervalo, y decirlo en el informe.

Si no funciona ningún método: `[t_min, t_max]` = horas de luz útil de ese día (sol a más de 30° de altura), y decirlo.

### B. Conteo manual (lo hace el autor)

En QGIS, sobre la ortofoto, un punto por avión visible dentro del recinto del aeropuerto, con las propiedades del esquema. Se hace **antes** de ver la salida del detector y los datos ADS-B, para no contaminarse. Opus prepara el proyecto QGIS o las instrucciones paso a paso; no hace el conteo.

### C. Detector preentrenado

Pasar el detector por la ortofoto en teselas de 1024 px con solape del 20 %, a resolución nativa y remuestreada a 0,5 m/píxel. Quedarse solo con la clase avión. Umbral de confianza 0,25, fijado aquí.

Emparejar cada detección con el punto manual más cercano si cae dentro de 15 m. Dar exhaustividad (de los aviones reales, cuántos detecta) y precisión (de lo que detecta, cuánto es avión), por categoría.

Esto es informativo: un adelanto del cambio de dominio. **No entra en la decisión.**

### D. Inferir quién estaba en tierra

Con llegadas y salidas de la ventana de ± 7 días:

* **Fuerte:** aterrizó antes de `t_min − 30 min` y no despegó hasta después de `t_max + 30 min`. Estuvo en tierra todo el intervalo.
* **Débil:** estuvo en tierra solo durante parte de `[t_min, t_max]`.
* Los que aterrizaron antes de la ventana y siguen allí no aparecen: quedan como aviones de la foto sin explicar. Contarlos y decirlo.

### E. Comparar

`comparar_conteos` entre el conteo manual y: (1) solo fuerte, (2) fuerte + débil. Siempre en dos grupos separados: **comerciales** (`regional`, `pasillo_unico`, `fuselaje_ancho`) y **ligeros**. Si ADS-B da posiciones en tierra, repetir por `zona`.

## 6. Partición de datos

No se entrena nada, así que no hay train/val/test. Pero:

* La ortofoto de esta fase queda marcada como **dato de desarrollo** (decisión D9): en la Fase 4 se reporta aparte.
* El conteo manual se hace a ciegas respecto al detector y a ADS-B (paso B).
* Los umbrales de la sección 7 están fijados aquí, antes de ver datos (decisión D8).

## 7. Métricas y criterio de decisión

Métricas, todas sobre aviones **comerciales**:

| Métrica | Definición |
|---|---|
| `ancho_intervalo` | `t_max − t_min`, en minutos. |
| `cobertura_fuerte` | Aviones de la foto explicados por verdad fuerte / aviones de la foto. Con intervalo de Wilson al 95 %. |
| `cobertura_total` | Lo mismo con fuerte + débil. Es un techo, no una medida. |
| `exceso_fuerte` | Aviones de verdad fuerte que no caben en la foto / aviones de verdad fuerte. Debería ser casi cero; si no, la inferencia falla o hay aviones en hangar. |

Decisión (usando el valor central de `cobertura_fuerte`; si el intervalo cruza un umbral, decirlo y recomendar repetir con una segunda foto):

| Resultado | Decisión |
|---|---|
| `cobertura_fuerte` ≥ 50 % y `exceso_fuerte` ≤ 15 % | **Seguir** con el plan. |
| `ancho_intervalo` ≤ 30 min, `cobertura_total` ≥ 80 % y `exceso_fuerte` ≤ 15 % | **Seguir**: con la hora bien acotada, casi toda la verdad débil es utilizable. |
| `cobertura_fuerte` entre 25 % y 50 % | **Ajustar:** el resultado central se da por conteos por categoría y zona; se añaden aeropuertos de larga estancia (Teruel) y fechas históricas. |
| `cobertura_fuerte` < 25 %, o `exceso_fuerte` > 30 % | **Replantear:** el detector y el clasificador se evalúan contra etiquetas manuales; ADS-B queda como comprobación agregada de plausibilidad. |

Los umbrales son criterio de diseño, no vienen de la literatura. La decisión final la toman Fable y el autor con el informe delante; Opus recomienda, no decide.

«Hecho» significa:

1. `docs/informes/fase-1b.md` da las cuatro métricas con sus intervalos, separadas en comerciales y ligeros, y dice qué fila de la tabla de decisión aplica.
2. El informe dice qué método acotó la hora y si los tres coinciden.
3. El informe lista lo que no se ha podido hacer o comprobar.
4. Las tres funciones de `fusion/` tienen tests que pasan, con datos de ejemplo pequeños escritos a mano (sin red).
5. Con los datos en DVC, un comando documentado regenera las tablas del informe.
6. Checklist de cierre rellenada.

## 8. Riesgos y qué hacer

| Riesgo | Qué hacer |
|---|---|
| No hay ADS-B accesible para la fecha de la foto. | Probar la siguiente ortofoto más antigua o más reciente del mismo aeropuerto; luego el aeropuerto de reserva. No cambiar de método. |
| El histórico solo da posiciones, no llegadas y salidas. | Derivar aterrizajes y despegues de las trazas (último punto bajo y lento cerca del aeropuerto). Anotarlo en dudas: es una decisión de diseño que Fable debe validar. |
| La foto mezcla pasadas de días distintos. | Tratar cada zona por separado (paso A). Si es inviable, cambiar de aeropuerto. |
| El detector preentrenado no ve casi nada. | Es un resultado; se reporta. No ajustar el modelo ni el umbral. |
| `cobertura` sale por encima del 95 %. | Sospechar: revisar que el conteo se hizo a ciegas y que la ventana de ADS-B no cuenta aviones dos veces. Anotar en dudas antes de dar el número por bueno. |
| Más del 20 % de los icao24 sin tipo en la base. | Reportar el porcentaje; van a `desconocido`; dar la cobertura también sin distinguir categorías. |

## 9. Tareas para Opus, en orden

1. Confirmar sitio y fecha con `docs/sitios.md`. Proponer al autor las descargas (qué, de dónde, tamaño) y esperar su visto bueno.
2. Descargar la ortofoto; añadirla a DVC.
3. Preparar el proyecto QGIS o las instrucciones para el conteo manual y pasárselas al autor. **Esperar el conteo.**
4. Mientras tanto: `fusion/` con sus tres funciones y tests.
5. Descargar ADS-B y la base de aeronaves; añadir a DVC.
6. Paso A (hora), con lo que el autor haya medido de sombras y aviones en movimiento.
7. Pasos D y E.
8. Paso C (detector), solo después de tener el conteo manual.
9. Informe y cierre.

Fuera de alcance: entrenar o ajustar modelos, generalizar la descarga de ADS-B, MCP, clasificar por tipo fino, cualquier aeródromo no civil.
