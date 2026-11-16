# Fase 1 — Dudas y elecciones de Opus

Parte sin datos (tareas 1-5 de la sección 8 de `docs/specs/fase-1.md`). La tarea 6 (adaptadores) **no se ha hecho**: no hay ninguna fuente accesible desde el entorno de trabajo. `descargar_movimientos` queda sin implementar.

Todo lo de abajo son elecciones provisionales, conservadoras, que decide Fable.

## Para decidir (cambian el diseño o un umbral)

### 1. Duración mínima de un «silencio» en la regla D17

D17 dice «antes de un tramo en tierra **o de un silencio**», pero no fija cuánto dura un silencio. Puesto: `SILENCIO_MINIMO = 10 min` (`src/avion_osint/adsb/trazas.py`). Motivo: a velocidad de aproximación, 10 km se recorren en unos 4 minutos; 10 minutos sin puntos estando por debajo de 1.000 m y a menos de 10 km no se explican con un hueco de cobertura en vuelo. Un valor menor daría llegadas falsas en aproximaciones con huecos cortos; uno mayor perdería aterrizajes con el transpondedor apagado al poco de tocar tierra (si no hay puntos en tierra). Hay que validarlo con la muestra de 20 aviones (criterio 7).

### 2. La altura de D17 es «sobre el aeródromo», pero `aerodromos.yaml` no tiene la elevación

`deducir_movimientos` interpreta `altitud_m` como altura **sobre el aeródromo**, tal como dice D17, y lo deja escrito. Las fuentes ADS-B dan altitud sobre el nivel del mar (o barométrica). Quien escriba el adaptador tendrá que restar la elevación, que hoy no está en `config/aerodromos.yaml` (Barajas está a unos 600 m: sin restarla, el umbral de 1.000 m equivaldría a unos 400 m sobre la pista). Propuesta: añadir `elevacion_m` a cada aeródromo, tomada del AIP (mismo apartado AD 2.2 que el punto de referencia). No se ha añadido porque cambia el esquema de la configuración.

### 3. El principio y el final de una traza no cuentan como silencio

Si la traza acaba con el avión bajo y cerca, **no** se da llegada (y si empieza así, no se da salida). Motivo: si el adaptador corta las trazas por días, un avión en final a las 23:59 daría una llegada ese día y una salida falsa al día siguiente. Coste: si el avión aterriza y apaga el transpondedor y la traza no sigue, esa llegada se pierde (estancia débil por D18, no fuerte falsa). Requisito para el adaptador: pasar la traza completa de cada avión, uniendo días seguidos.

### 4. La salida también tiene que estar «cerca»

D17 define la salida como «primer punto en vuelo después». Se ha aplicado la misma condición de cercanía que a la llegada (< 1.000 m y < 10 km): si el primer punto tras el tramo en tierra o el silencio ya está alto o lejos, no se da salida (falta el extremo → débil por D18). Lectura simétrica y conservadora.

### 5. `resumen_actividad(aerodromo, periodo)`: formato de `periodo`

La spec no lo define. Puesto: `periodo` = intervalo ISO 8601 `'AAAA-MM-DD/AAAA-MM-DD'` (ambos días incluidos) y un parámetro más, `por` (`"dia"` | `"semana"`, por defecto `"dia"`), que es el de `consultas.resumen`. Alternativa: `fecha_inicio`, `fecha_fin` y `por`, como `vuelos_en_zona`.

### 6. La tabla `cobertura` no tiene columna `fuente` — **resuelta**

Aceptada en la revisión de Fable: `cobertura` lleva ahora la columna `fuente` (añadida a la sección 3 de la spec, al almacén de juguete, a `consultas.resumen` y a la cobertura por día del MCP). La `fuente` de las respuestas del MCP une las de los movimientos y las de la cobertura, así que un periodo descargado sin vuelos ya no da `"fuente": []`. Texto original de la duda:

La regla 4 pide la fuente en toda respuesta. Hoy se saca de los movimientos del periodo (valores distintos de `fuente`). Si un periodo tiene días descargados pero ningún movimiento, la respuesta lleva `"fuente": []`. Propuesta: añadir `fuente` a la tabla `cobertura`. No se ha hecho porque cambia el esquema de la sección 3.

### 7. Columnas del CSV de aeronaves deducidas, no declaradas

Se leyeron los primeros 64 KB de `aircraft-database-complete-2023-07.csv` con una petición parcial (cabecera `Range`; el servidor respondió `206`, 61.498.207 bytes en total). **La primera fila es una cabecera con las 15 columnas vacías (`""`)**: el fichero no dice qué es cada columna. Las posiciones se han deducido del contenido:

| Posición | Contenido de ejemplo | Columna de `aeronaves.parquet` | Seguridad |
|---|---|---|---|
| 0 | código hexadecimal de 6 cifras | `icao24` | alta |
| 1 | matrícula con prefijo de país | `matricula` | alta |
| 2 | nombre del fabricante en mayúsculas | (no se guarda: fabricante en mayúsculas, parece el código OACI) | — |
| 3 | nombre del fabricante | `fabricante` | alta |
| 4 | nombre del modelo y su variante | `modelo` | alta |
| 5 | código OACI de 4 caracteres | `tipo_oaci` | alta |
| 6, 7 | números | (no se guardan: número de serie y de línea) | — |
| 8 | código de 3 caracteres (p. ej. «L2J») | (no se guarda: clase de aeronave OACI) | — |
| 9 | nombre de aerolínea o de fuerza aérea | `operador` | **media** |
| 10-12 | palabra en mayúsculas, código de 3 letras, código de 2 | (no se guardan: indicativo, OACI e IATA del operador) | — |
| 13 | nombre de empresa o «Private» | (no se guarda: parece el propietario) | — |
| 14 | texto como «Large (75000 to 300000 lbs)» | (no se guarda: categoría de emisor ADS-B) | — |

El orden coincide con el de las columnas con nombre del otro formato de OpenSky (`aircraftDatabase.csv`: icao24, registration, manufacturericao, manufacturername, model, typecode, serialnumber, linenumber, icaoaircrafttype, operator, operatorcallsign, operatoricao, operatoriata, owner, …, categoryDescription), pero eso es una deducción, no algo que diga el fichero. La más dudosa es `operador`: la columna 9 a menudo está vacía y la 13 rellena. Si se prefiere el propietario, es cambiar una posición en `aeronaves.POSICIONES`.

Otras cosas vistas en la muestra:

* `NULL` aparece **sin comillas** como valor nulo, además de `""`. Los dos se guardan como nulos.
* El fichero **no es UTF-8 limpio**: hay al menos un byte de Windows-1252 (`0x96`, un guion, en una de las primeras filas). Se lee como UTF-8 sustituyendo los bytes no válidos por «�». Si el fichero entero fuera Windows-1252, los acentos se perderían (quedarían como «�»), pero no se inventaría texto. Sin el fichero completo no se puede saber.
* Hay filas con icao24 que no son 6 cifras hexadecimales o con matrícula `-UNKNOWN-`. No se filtran.
* No se ha comprobado si hay icao24 repetidos (haría falta el fichero entero). Si los hay, `consultas.aeronave` devuelve la primera fila.

La muestra de los tests, `tests/datos/aeronaves-opensky-formato-muestra.csv`, es **ficticia con formato real** (revisión de Fable): 7 filas inventadas (icao24 `aaa001`…, matrículas `FICT-1`…, operadores «Aerolínea Ficticia»…) con la estructura vista en el fichero real: cabecera con las 15 columnas vacías, mismas posiciones de columna, mismo entrecomillado, `NULL` sin comillas y un byte `0x96`. No contiene ninguna fila real. **Licencia de la base de aeronaves: sigue sin verificar** (`docs/licencias.md`; `opensky-network.org` responde 403). Hay que confirmarla antes de usar la base completa.

## Elecciones menores (revisables)

* **Ruta del almacén:** `RUTA_ALMACEN = data/adsb/` en `avion_osint.adsb`; todas las funciones aceptan otra con el parámetro `almacen`. El servidor MCP usa siempre la ruta por defecto.
* **`consultas.movimientos`:** intervalo semiabierto `inicio <= instante < fin`. Rechaza aeródromos que no estén en `config/aerodromos.yaml` (la spec deja fuera cualquier otro).
* **`consultas.en_tierra`:** mira las llegadas y salidas de `t_min − 7 días` a `t_max + 7 días`, la ventana de la Fase 1b (`docs/specs/fase-1b.md`, sección 5). Al comprobar el retraso mínimo se comprueba también `t_max + 7 días`, así que un intervalo de hace menos de 37 días se rechaza (más estricto, no menos).
* **`consultas.resumen`:** los conteos salen de la tabla de movimientos; `dias_con_datos` y `n_puntos_tierra`, de la de cobertura. Las columnas `n_llegadas`, `n_salidas`, `n_aviones` y `desequilibrio` de la tabla `cobertura` no se leen (se recalculan). Semana = lunes a domingo (ISO). `n_puntos_tierra` semanal = suma de los días que lo tienen; nulo si ninguno.
* **«Hay datos»:** un aeródromo-día tiene datos si tiene fila en `cobertura` o algún movimiento. Así se distingue «no se descargó» (regla 5: «no hay datos en el almacén») de «se descargó y no hubo vuelos» (lista vacía, con la cobertura que lo respalda).
* **Agregado de la regla 2:** conteos por **aeródromo**, día (UTC) y categoría de tamaño, separando llegadas y salidas. La categoría sale de `config/categorias_tipo.yaml`; un tipo que no esté allí es `desconocido`. La respuesta agregada también da por día `desequilibrio` y `n_puntos_tierra`, que son cifras del aeródromo, no de aviones. Aviso: con conteos tan pequeños (p. ej. un solo `fuselaje_ancho` un día en una base mixta) un avión concreto puede ser reconocible; la spec no pide un umbral mínimo y no se ha puesto.
* **Errores en el MCP:** con el SDK de MCP 2.x, una excepción cualquiera llega al cliente como un error genérico, sin su texto. Por eso el servidor convierte los `ValueError` (incluida `FechaDemasiadoRecienteError`) en `ToolError`, que sí llega con su mensaje (regla 1).
* **SDK de MCP:** se ha instalado `mcp` 2.3.0, donde `FastMCP` se llama `MCPServer`.
* **Órdenes de terminal** (`python -m avion_osint.adsb ...`, sección 4 de la spec): no se han hecho. Solo tendrían sentido con `descargar_movimientos`; `cargar_aeronaves` se puede llamar desde Python mientras tanto.
* **Aviso en los tests:** DuckDB 2.0, al pasar resultados a pandas 3.1, da un `Pandas4Warning` (uso interno de `inplace` en DuckDB). No viene del código del proyecto y no afecta a los resultados.
