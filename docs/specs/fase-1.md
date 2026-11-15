# Fase 1 — ADS-B y MCP 1

Especificación de Fable para Opus. Leer antes `CLAUDE.md`, `docs/encargo.md` (secciones 3 y 4), `docs/licencias.md` y las decisiones D10 a D18.

*ADS-B* = señal que emiten los aviones con su posición e identificador. *MCP* = protocolo para que un asistente use herramientas externas; aquí, consultar nuestros datos.

## 1. Objetivo

Tener en un almacén local los movimientos (aterrizajes y despegues) de los aeródromos del proyecto en las fechas que interesan, con el tipo de cada avión, y poder consultarlos desde un asistente mediante un servidor MCP.

Pregunta que responde: **¿qué aviones aterrizaron y despegaron en el aeródromo X entre las fechas A y B, y cuáles estaban en tierra en un instante dado?**

## 2. Estado de las fuentes (a 2026-11-15)

| Fuente | Qué da | Estado |
|---|---|---|
| OpenSky, base histórica (Trino) | Vuelos y posiciones desde 2016 | Sin acceso. El autor tiene que pedirlo. |
| OpenSky, API REST | Llegadas y salidas por aeropuerto | Responde desde el entorno de trabajo. Sin cuenta contesta «You cannot access historical flights». Con cuenta gratuita, sin comprobar. |
| adsb.lol, volcados diarios | Trazas de posiciones, mundiales, desde febrero de 2023 | Inaccesible desde el entorno de trabajo (GitHub lo deniega para esta sesión). Accesible desde el PC del autor. |

Consecuencia de diseño: **el almacén no depende de la fuente.** Cada fuente tiene un adaptador que escribe las mismas tablas. Se implementa primero el adaptador de la fuente que esté disponible; los demás, solo cuando haya acceso.

## 3. Entradas y salidas

### Almacén local

Ficheros Parquet (formato de tablas por columnas) en `data/adsb/`, versionados con DVC. Se consultan con DuckDB (motor de consultas SQL sobre ficheros, sin servidor).

`data/adsb/movimientos/aerodromo=<OACI>/fecha=<AAAA-MM-DD>/parte.parquet`

| Columna | Tipo | Significado |
|---|---|---|
| `icao24` | texto | Código del transpondedor, en minúsculas. |
| `tipo_movimiento` | texto | `llegada` o `salida`. |
| `instante` | fecha-hora UTC | Momento del aterrizaje o despegue. |
| `indicativo` | texto o nulo | Indicativo de vuelo (p. ej. `IBE3170`). |
| `fuente` | texto | `opensky_rest`, `opensky_trino` o `adsblol`. |
| `metodo` | texto | `declarado` (la fuente lo da) o `deducido` (regla D17). |

`data/adsb/cobertura/aerodromo=<OACI>/fecha=<AAAA-MM-DD>/parte.parquet` — una fila por día:

| Columna | Tipo | Significado |
|---|---|---|
| `n_llegadas`, `n_salidas` | entero | Movimientos del día. |
| `n_aviones` | entero | Aviones distintos. |
| `desequilibrio` | decimal | `abs(n_llegadas − n_salidas) / (n_llegadas + n_salidas)`. Si es alto, faltan movimientos. |
| `n_puntos_tierra` | entero o nulo | Posiciones recibidas en tierra (solo fuentes con trazas). |

`data/adsb/aeronaves.parquet`: `icao24`, `matricula`, `tipo_oaci`, `fabricante`, `modelo`, `operador`, `fecha_base` (mes de la copia de la base de aeronaves).

### Registro de descargas

`data/adsb/descargas.jsonl`: una línea por descarga (fuente, aeródromo, fechas, fecha de ejecución, filas, huella del fichero). Permite repetir y auditar.

## 4. Interfaces

### Adaptadores — `src/avion_osint/adsb/`

```python
def descargar_movimientos(fuente: str, aerodromo: str, inicio: date, fin: date) -> int:
    """Descarga y escribe movimientos y cobertura. Devuelve filas escritas.
    Comprueba `fin` con limites.comprobar_fecha_retrospectiva antes de pedir nada.
    Repetir la misma llamada no duplica filas."""

def deducir_movimientos(traza: DataFrame, aerodromo: Aerodromo) -> DataFrame:
    """Regla D17. traza: instante, lat, lon, altitud_m, en_tierra. Devuelve
    tipo_movimiento e instante."""

def cargar_aeronaves(ruta_csv: Path, fecha_base: date) -> int:
    """Convierte la base de aeronaves de OpenSky a aeronaves.parquet."""
```

Órdenes de terminal (una por función), con `python -m avion_osint.adsb ...`. Las credenciales, si hacen falta, se leen de variables de entorno cuyos nombres se añaden a `.env.example`.

### Consultas — `src/avion_osint/adsb/consultas.py`

Funciones puras sobre el almacén, que usan tanto el MCP como la Fase 4:

```python
def movimientos(aerodromo: str, inicio: datetime, fin: datetime) -> DataFrame
def en_tierra(aerodromo: str, t_min: datetime, t_max: datetime) -> DataFrame   # usa fusion.inferir_en_tierra
def resumen(aerodromo: str, inicio: date, fin: date, por: str = "dia") -> DataFrame  # "dia" | "semana"
def aeronave(icao24: str) -> dict | None
```

### MCP 1 — `src/avion_osint/mcp_server/trafico/`

Con el SDK oficial de MCP para Python. Solo lee el almacén local; **nunca** llama a una API externa.

| Herramienta | Devuelve |
|---|---|
| `vuelos_en_zona(lat, lon, radio_km, fecha_inicio, fecha_fin)` | Movimientos de los aeródromos del almacén cuyo punto de referencia cae en el círculo. |
| `info_avion(icao24)` | Fila de `aeronaves`. |
| `resumen_actividad(aerodromo, periodo)` | Conteos por día o semana, y la cobertura. |

Reglas obligatorias, con test cada una:

1. Toda fecha pasa por `comprobar_fecha_retrospectiva`. Una fecha reciente devuelve un error claro, no datos.
2. Si el aeródromo no es `civil` (`solo_agregado`): `vuelos_en_zona` devuelve solo conteos por día y categoría de tamaño, sin `icao24`, indicativos ni matrículas. `info_avion` no cambia (es un dato público del avión, no de su actividad).
3. Si un círculo incluye un aeródromo civil y otro que no lo es, se aplica la regla 2 a todo el resultado.
4. Toda respuesta lleva la fuente de los datos, el periodo cubierto y la cobertura (para que quien lea sepa cuánto fiarse).
5. Si no hay datos para lo pedido, se dice «no hay datos en el almacén», no se devuelve una lista vacía como si no hubiera habido vuelos.

El nombre de la carpeta es `trafico` y no `opensky` (como ponía el encargo) porque la fuente puede no ser OpenSky.

## 5. Partición de datos

No se entrena nada. Aun así:

* Los umbrales de la regla D17 (1.000 m, 10 km) se fijan aquí y se validan con una muestra; si se cambian, se anota en dudas y lo decide Fable.
* La validación de la regla D17 se hace con un día y un aeropuerto **distintos** de los de la Fase 1b, para no ajustar la regla al caso que luego se evalúa.

## 6. Métricas y criterios de aceptación

Sin datos reales (se puede cerrar ya):

1. Tests de los adaptadores con respuestas guardadas en `tests/datos/` (ficheros pequeños, anonimizados si hace falta), sin red.
2. Tests de `deducir_movimientos` con trazas escritas a mano: aterrizaje normal, despegue normal, traza con hueco, sobrevuelo bajo que no aterriza (no debe dar movimiento), aproximación frustrada.
3. Tests de las cinco reglas del MCP.
4. Idempotencia: descargar dos veces el mismo periodo deja las mismas filas.
5. Los cuatro comandos del proyecto pasan, y el CI también.

Con datos reales (cuando haya fuente):

6. Para LEMD, un día completo: `desequilibrio` < 10 %. Si es mayor, se reporta y no se usa ese día como verdad fuerte.
7. Validación de la regla D17: 20 aviones al azar de un día, comparando los movimientos deducidos con otra fuente pública consultada a mano. Se da el porcentaje de aciertos y el error típico en minutos.
8. Porcentaje de `icao24` sin tipo en `aeronaves`: reportado.
9. Desde un asistente con el MCP conectado, la pregunta «¿qué aviones aterrizaron en Barajas el día X?» devuelve datos reales.

## 7. Riesgos y qué hacer

| Riesgo | Qué hacer |
|---|---|
| Ninguna fuente accesible a tiempo. | Cerrar la parte sin datos (criterios 1-5). El resto queda abierto y se dice. No inventar datos de ejemplo que parezcan reales. |
| Los volcados de adsb.lol son mundiales y grandes. | Procesar un día cada vez: descargar, quedarse con las trazas que pasan a menos de 10 km de algún aeródromo del proyecto, borrar el volcado. Solo se guarda lo filtrado. |
| La cobertura en tierra es mala (pocos puntos en tierra). | La regla D17 no depende de ver el avión en tierra, solo de verlo bajar y subir. Reportar `n_puntos_tierra`. |
| El formato real de una fuente no coincide con lo supuesto. | El primer paso de cada adaptador es guardar una respuesta real pequeña y escribir el test contra ella. No escribir el adaptador a ciegas. |
| Límites de peticiones de una API. | Respetarlos con esperas; nunca paralelizar para saltárselos. Registrar los créditos gastados. |
| Aeronaves privadas identificables. | En informes y figuras, aviación privada solo agregada (revisión del encargo, punto de datos personales). |

## 8. Tareas para Opus, en orden

1. Dependencias: `duckdb`, `pyarrow`, SDK de MCP. Nada más.
2. `consultas.py` con el esquema de la sección 3 y sus tests (con un almacén de juguete creado en el propio test).
3. `deducir_movimientos` con sus tests.
4. `cargar_aeronaves` (la base de julio de 2023 se puede descargar: 61 MB, ver `docs/specs/fase-1b-descargas.md`).
5. Servidor MCP con sus cinco reglas y tests.
6. Adaptador de la primera fuente disponible. **Si no hay ninguna, parar aquí** y cerrar la parte sin datos.
7. Con datos: criterios 6 a 9 y cierre en `docs/cierres/fase-1.md`.

Fuera de alcance: NOTAM, posiciones en ruta, cualquier consulta en vivo, cualquier aeródromo que no esté en `config/aerodromos.yaml`.

## 9. Lo que tiene que hacer el autor

Una de estas tres cosas, por orden de preferencia:

1. Conseguir el acceso de investigador de OpenSky (da todo el histórico).
2. Crear una cuenta gratuita de OpenSky y probar si la API da llegadas históricas por aeropuerto.
3. Descargar en su PC los volcados de adsb.lol de las fechas necesarias con el guion que dejará Opus.
