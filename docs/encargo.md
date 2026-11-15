# Proyecto: Detección y clasificación de aviones + contexto de tráfico aéreo y noticias (OSINT retrospectivo)

> Documento de encargo del proyecto. Contiene el planteamiento, la evaluación, el plan por fases, el reparto de trabajo entre modelos y las normas. **Quien lo lea (Fable u Opus) debe leerlo entero antes de empezar.**
>
> *OSINT* = inteligencia de fuentes abiertas: análisis hecho solo con información pública.

---

## 0. Instrucciones comunes (para cualquier modelo)

- **Idioma:** responde siempre en castellano, claro y sin rodeos. Explica cada término técnico con palabras sencillas la primera vez que salga (ver glosario, sección 9).
- **Antes de algo grande o difícil de deshacer** (borrar datos, migraciones, descargas masivas, publicar, gastar dinero en APIs o GPU), explica qué vas a hacer y espera mi visto bueno.
- **Nunca** pidas, repitas ni guardes contraseñas, tokens o claves de API. Usa variables de entorno (`.env`, fuera de git; en git solo `.env.example` con los nombres).
- **Si algo falla o no lo has podido probar, dilo tal cual.** No inventes resultados, métricas ni rutas de ficheros.
- **Git:** autor y committer `OG <144943468+ortzigaraio@users.noreply.github.com>`. Nunca añadas `Co-Authored-By`, `Claude-Session`, «Generated with Claude Code» ni ninguna línea que nombre a Claude o a Anthropic en commits, PRs o merges. No crees ramas ni abras PRs si no te lo pido. Cada PR o merge lleva título y descripción en castellano (qué cambia, por qué, qué tengo que hacer yo, cómo se ha probado).
- **Límites del proyecto (sección 1):** si una tarea se acerca a seguimiento en vivo, alerta de operaciones o predicción de ataques, detente y dilo.

---

## 0.1 Reparto de trabajo: Fable 5.2 diseña, Opus 5.5 construye

Fable 5.2 es más caro: se reserva para **planificar, diseñar y revisar**. Opus 5.5 hace **todo lo demás**. Se trabaja en sesiones separadas; el puente entre ambos son ficheros en el repo, no la memoria de la conversación.

| Tarea | Fable 5.2 | Opus 5.5 |
|---|---|---|
| Plan general, riesgos, cambios de alcance | ✅ | — |
| Especificación de cada fase (`docs/specs/fase-N.md`) | ✅ | — |
| Decisiones de diseño (splits de datos, métricas, arquitectura, fuentes nuevas) | ✅ | Propone, no decide |
| Código, tests, notebooks, scripts de descarga, MCP | — | ✅ |
| Configuración (DVC, MLflow, CI, entorno) | Diseña | ✅ Implementa |
| Revisión crítica al cerrar cada fase | ✅ | Autorrevisión previa con la checklist de la sección 7 |
| Redacción de la memoria/README final | ✅ (estructura y conclusiones) | ✅ (tablas, figuras, reproducibilidad) |

### Protocolo de traspaso

1. **Fable escribe la especificación** de la fase en `docs/specs/fase-N.md` con esta plantilla:
   - Objetivo y pregunta que responde.
   - Entradas y salidas (formatos, esquemas de tablas, rutas).
   - Interfaces (firmas de funciones o herramientas MCP).
   - Partición de datos (qué va a train/val/test y por qué no hay fuga).
   - Métricas y **criterios de aceptación** comprobables ("hecho" significa…).
   - Riesgos conocidos y qué hacer si se materializan.
   - Lista de tareas para Opus, ordenadas y pequeñas.
2. **Opus implementa** siguiendo la especificación. Si algo no encaja o hay que tomar una decisión de diseño no prevista, **no la toma solo**: la anota en `docs/specs/fase-N-dudas.md` y me avisa.
3. **Opus cierra** con la checklist de la sección 7 rellenada y un resumen de resultados (métricas, enlaces a runs de MLflow, versiones de datos DVC).
4. **Fable revisa** el resumen y el diff, busca fugas, métricas engañosas y conclusiones no justificadas, y deja el veredicto en `docs/revisiones/fase-N.md`.
5. Las decisiones importantes se registran en `docs/decisiones.md` (fecha, decisión, alternativas descartadas, motivo).

**Cuándo Opus debe escalar a Fable (o a mí):** cambiar la partición de datos, cambiar una métrica o un umbral, añadir una fuente de datos, resultados sorprendentemente buenos (sospecha de fuga), o cualquier duda sobre los límites del proyecto.

### Primer paso que se pide a Fable

Revisar este documento, señalar riesgos o huecos, proponer el `CLAUDE.md` del repositorio (que resuma las secciones 0, 0.1, 1 y 7) y escribir `docs/specs/fase-0.md` y `docs/specs/fase-1b.md` (prueba de concepto, ver sección 5). No escribir código.

---

## 1. Planteamiento

**Pregunta del proyecto:**
¿Se pueden detectar y clasificar aviones en imágenes aéreas o de satélite, contrastarlo con datos de tráfico aéreo (ADS-B) y con noticias públicas, y detectar y explicar actividad fuera de lo normal en aeródromos?

**Resultado central (lo que tiene que salir sí o sí):** cuánto acierta la cadena *imagen → detección → tipo de avión* comparada con ADS-B en aeropuertos civiles. Todo lo demás se construye sobre eso.

**Piezas:**
1. **Visión (CNN):** detector de aviones con cajas orientadas + clasificador de tipo, apoyado en medidas en metros.
2. **Tráfico aéreo:** pipeline de ADS-B (y NOTAM si es viable), con un MCP propio para consultarlo desde Claude.
3. **Contexto:** ingesta de noticias y eventos (GDELT, ACLED, comunicados oficiales) con un segundo MCP.
4. **Análisis:** línea base de actividad, detección de anomalías y **explicación pública más probable** de cada anomalía, validado con casos pasados conocidos.
5. **MLOps:** datos versionados, experimentos registrados, reentrenamiento reproducible y monitorización de deriva.

### Límites del proyecto (fijos, no negociables)

- Solo **datos públicos o de acceso académico**, respetando sus condiciones de uso, y análisis **retrospectivo**.
- **No** es un sistema de seguimiento en vivo de despliegues militares, ni de alerta de operaciones, ni de predicción de ataques a partir de la actividad de bases concretas, ni nada orientado a selección de objetivos.
- **Salvaguarda técnica del carácter retrospectivo:** los MCP y los pipelines rechazan fechas más recientes que un retraso mínimo configurable (por defecto, 30 días).
- **Agregación:** en bases militares, los resultados se presentan agregados (por aeródromo y día/semana), no como trayectorias o identificadores de aviones militares concretos.
- Una anomalía se presenta como **"actividad inusual"** con su explicación pública más probable, **nunca** como "misión confirmada" o "ataque inminente".
- La parte predictiva, si se hace, es de **riesgo de escalada agregado por país o región y mes** (estilo académico ViEWS, Universidad de Uppsala), no de operaciones concretas.
- Toda explicación generada debe **citar sus fuentes**.

---

## 2. Evaluación de viabilidad

| Componente | Viabilidad | Motivo |
|---|---|---|
| Detector de aviones | Alta | Datasets públicos grandes (DOTA, FAIR1M, xView, DIOR) y modelos maduros (YOLO con cajas orientadas). |
| Clasificador de tipo | Media | MAR20 (20 tipos militares) y FAIR1M (modelos civiles) lo permiten, pero los tipos parecidos se confunden y el cambio de sensor baja el rendimiento. |
| Pipeline ADS-B + MCP | Alta, **si se consigue acceso histórico** | La API pública de OpenSky tiene historia limitada; el histórico completo requiere acceso de investigador (suele pedir afiliación institucional). |
| "Verdad terreno" ADS-B en tierra | **Media-baja, a comprobar pronto** | Ver punto débil 2. |
| Anomalías con ADS-B | Media-alta en civil, baja en militar | Muchos militares no emiten o lo hacen de forma intermitente. |
| Capa de noticias + causa probable | Media | GDELT y ACLED son abiertos; el reto es etiquetar casos, evitar relaciones inventadas y la fuga temporal (punto débil 3). |
| Cruce imagen ↔ ADS-B diario | Baja con datos gratis | Ortofotos gratuitas (PNOA, NAIP) cada 2-3 años. Sin imágenes comerciales no hay serie temporal. |

### Punto débil 1: no hay imágenes frecuentes

Sin imágenes frecuentes de alta resolución no se puede seguir el movimiento diario con la CNN.
**Solución:** validar la cadena en **aeropuertos civiles**, donde casi todos los aviones emiten ADS-B y la fecha de vuelo de la ortofoto es conocida. Después se aplica a bases sabiendo ya cuánto falla el sistema.

### Punto débil 2: la "verdad" de ADS-B en tierra es más débil de lo que parece

- **Aviones aparcados con el transpondedor apagado:** muchos aviones en plataforma no emiten. Su presencia hay que **inferirla**: aterrizó antes del momento de la foto y no despegó hasta después.
- **Fecha sin hora:** la ortofoto PNOA normalmente indica el día de vuelo, no la hora, y un mosaico puede mezclar pasadas de días distintos. En un aeropuerto con rotaciones de 1-2 horas, "estaba en tierra ese día" no equivale a "estaba en la foto".
- **Cobertura en tierra:** los receptores ADS-B captan peor los aviones en el suelo.

**Mitigación:**
- Comprobar si el CNIG/IGN ofrece la hora por fotograma o por pasada; si existe, usarla.
- Usar como verdad fuerte solo los aviones que estuvieron en tierra **todo el intervalo plausible** (pernoctas, estancias largas, aviones de mantenimiento) y tratar el resto como verdad débil.
- Comparar **conteos por tipo y zona de plataforma**, no identidades avión a avión.
- **Hacer una prueba de concepto en la semana 2-3 (Fase 1b)** antes de invertir en entrenar modelos. Si la verdad terreno no se sostiene, se replantea el resultado central a tiempo.

### Punto débil 3: fuga temporal en la capa de noticias

En análisis retrospectivo es fácil "explicar" una anomalía con noticias publicadas **después**. Eso infla los resultados.
**Mitigación:** cada explicación solo puede usar fuentes publicadas hasta el día de la anomalía + *k* días, con *k* fijado de antemano y declarado. Se reporta el resultado con *k* = 0 y con el *k* elegido.

### Por qué no se predicen "ataques"

- Muy pocos casos positivos frente a muchísimos picos de actividad (desbalance extremo).
- Las operaciones reales suelen hacerse sin transpondedor y sin noticias previas: faltan justo los datos clave.
- Ejercicios, mantenimiento, exhibiciones, clima y rotaciones generan los mismos picos.

La pregunta útil es: **"¿qué explicación pública encaja mejor con esta actividad?"**

### Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Cambio de dominio (otro sensor, resolución, estación) | Medirlo explícitamente y reportarlo como resultado. |
| Pocas etiquetas propias | Cruces con ADS-B como etiquetas débiles; etiquetado manual pequeño pero cuidado. |
| Acceso a datos denegado o lento (OpenSky, ACLED) | Pedirlo en la semana 1 con aval del tutor. Plan B: adsb.lol y la API REST limitada, reduciendo el alcance. |
| Condiciones de uso y licencias (OpenSky, ACLED, DOTA, xView, FAIR1M, MAR20) | Revisarlas antes de descargar; anotar en `docs/licencias.md` qué permite cada una (muchas son solo uso no comercial; algunas limitan redistribuir datos). |
| Relaciones espurias en noticias | Casos etiquetados, evidencia citada, control de fuga temporal. |
| Falta de GPU | Decidir en Fase 0 dónde se entrena (Colab, Kaggle, GPU de la universidad) y con qué presupuesto. |
| Alcance excesivo para el tiempo disponible | Núcleo obligatorio + ampliaciones opcionales (sección 5), con criterios de recorte. |
| Coste de modelos | Fable solo para diseño y revisión (sección 0.1). |

---

## 3. Datos y fuentes

### Imágenes
- **Sentinel-2 (10 m):** no sirve para aviones sueltos (un caza de ~15 m son 1-2 píxeles).
- **PNOA (IGN, España, 25-50 cm)** y **NAIP (EE. UU., 0,6-1 m):** gratis, actualización cada 2-3 años. Fecha de vuelo conocida (hora: a comprobar).
- **Comerciales (Planet, Maxar, Capella, ICEYE):** series densas. Comprobar acceso académico de la universidad y programas de datos abiertos.
- Comprobar si algún aeródromo militar de interés aparece **enmascarado** en las ortofotos.

### Datasets de entrenamiento
- Detección: **DOTA, FAIR1M, xView, DIOR**.
- Tipo de avión: **MAR20** (militares), **FAIR1M** (civiles). Verificar clases, origen de las imágenes y licencia antes de elegir.
- **Ojo con las particiones oficiales:** comprobar si un mismo aeródromo o escena aparece en train y test; si es así, rehacer la partición por aeródromo.

### Tráfico aéreo
- **OpenSky Network:** API REST (historia limitada) y base histórica para investigadores (requiere solicitud).
- **adsb.lol** (comunitaria, datos abiertos) y **ADS-B Exchange** (API de pago).
- **Flightradar24:** API de pago.
- **Base de datos de aeronaves de OpenSky / registros públicos:** código hexadecimal del transpondedor (icao24) → matrícula y tipo.
- **NOTAM** (avisos a navegantes aéreos sobre cierres, restricciones o actividad especial): histórico difícil de conseguir; tratarlo como opcional.

### Noticias y eventos
- **GDELT:** noticias codificadas en eventos (quién, qué, dónde, cuándo). API y BigQuery. Mucho ruido y duplicados.
- **ACLED:** eventos de conflicto verificados. Acceso para investigación (revisar condiciones de uso y redistribución).
- **Comunicados oficiales:** OTAN, Ministerio de Defensa y equivalentes (calendarios de ejercicios y despliegues).

No existe conector oficial de ADS-B ni de noticias geopolíticas en el directorio de Claude: se construyen **dos MCP propios**.

---

## 4. Diseño técnico

### Visión
1. **Detector:** YOLO con cajas orientadas (OBB) entrenado en DOTA/FAIR1M, solo clase avión. Métrica: **mAP** (precisión media; resume aciertos y fallos a distintos umbrales de confianza).
2. **Recorte** de cada detección.
3. **Medidas:** longitud y envergadura en metros a partir de la caja y el **GSD** (tamaño real que cubre cada píxel). Estimar también su error.
4. **Clasificador de grano fino** (ConvNeXt / EfficientNet / ViT) con imagen + medidas como entradas extra. Clase **"desconocido"** y salida **top-3 con confianza calibrada**. Métricas: accuracy top-1/top-3, F1 por clase, matriz de confusión.
5. **Línea base sencilla obligatoria:** clasificar solo por medidas (longitud, envergadura). Si la CNN no la supera claramente, es un resultado a reportar.

### Cruce imagen ↔ ADS-B
- Para cada ortofoto: aviones que ADS-B sitúa (o permite inferir) en tierra en esa fecha y aeródromo, separados en verdad fuerte y débil (sección 2, punto débil 2).
- Métricas: % detectados, % bien clasificados, conteos por tipo, huecos (en imagen y no en ADS-B, y al revés). Un avión visto sin ADS-B es informativo, no concluyente.

### Anomalías
- Línea base de actividad por aeródromo con estacionalidad (día de la semana, mes, festivos).
- Métodos: puntuación z frente al mismo periodo de otros años; isolation forest (algoritmo que aísla puntos raros).
- **Evaluación con partición temporal:** la línea base se ajusta con años anteriores al periodo evaluado.
- Validación con ejercicios pasados conocidos, **elegidos donde haya buena cobertura ADS-B** (p. ej. Trident Juncture 2018, Steadfast Defender 2024). Zapad 2021 probablemente tiene muy poca cobertura útil: si se usa, como caso de "lo que el sistema no ve".
- Añadir también anomalías civiles conocidas (cierres de espacio aéreo, grandes eventos, temporales) como casos de control.
- Métrica: precisión y exhaustividad (recall) frente a la lista de eventos conocidos, con una ventana de tolerancia en días fijada de antemano.

### Explicación de causa probable
Clases:
1. Ejercicio anunciado
2. Despliegue o apoyo aliado público
3. Puente aéreo humanitario o de evacuación
4. Evento o exhibición
5. Contexto de crisis activa (según noticias)
6. Sin explicación pública

Con 50-100 casos etiquetados repartidos en 6 clases no hay datos para entrenar un clasificador fiable. Enfoque propuesto:
- **Recuperación + reglas + modelo de lenguaje:** buscar eventos y comunicados cercanos en espacio y tiempo (respetando el corte de *k* días), y que el modelo elija la causa **solo** entre la evidencia recuperada, citándola.
- Los casos etiquetados se usan **para evaluar**, no para entrenar. Reportar F1 por clase con intervalos de confianza (con tan pocos casos, la incertidumbre es grande y hay que decirlo).
- "Sin explicación pública" es una salida válida y se favorece cuando la evidencia es débil.

### MCP 1 — Tráfico aéreo
- `vuelos_en_zona(lat, lon, radio_km, fecha_inicio, fecha_fin)`
- `info_avion(icao24)`
- `resumen_actividad(aerodromo, periodo)`

### MCP 2 — Contexto
- `eventos_en_zona(region, fecha_inicio, fecha_fin)` (GDELT + ACLED)
- `ejercicios_anunciados(pais, fecha_inicio, fecha_fin)`
- `noticias_relacionadas(aerodromo, fecha, dias_despues=k)`

**Diseño común de los MCP:**
- Implementados con el SDK oficial de MCP para Python.
- **Consultan el almacén local** (Parquet/DuckDB) que llenan los pipelines de descarga; no llaman a la API externa en cada consulta. Así se respetan los límites de peticiones y el carácter retrospectivo.
- Retraso mínimo obligatorio (sección 1) y resultados agregados para aeródromos militares.
- Claves por variables de entorno. Tests con respuestas guardadas, sin llamar a la API real.

### MLOps
- **DVC** (control de versiones para datos) para datos y recortes; definir el almacenamiento remoto en Fase 0.
- **MLflow** para registrar experimentos y modelos.
- Etapas en `dvc.yaml`: descargar → preparar → entrenar → evaluar.
- **GitHub Actions:** tests, lint y comprobaciones de datos en cada push. Los ejecutores gratuitos no tienen GPU, así que el **reentrenamiento** es un comando reproducible (`dvc repro`) que se lanza en la máquina con GPU; programarlo solo si hay GPU disponible.
- **Deriva** (cambio en los datos de entrada respecto a los de entrenamiento): vigilar distribución de colores/brillo, tamaños de detección y mAP/IoU sobre un conjunto de validación fijo; alerta si cae por debajo de un umbral.

---

## 5. Plan por fases (~17 semanas)

**Núcleo obligatorio:** Fases 0, 1, 1b, 2, 3 y 4. **Ampliaciones:** 5, 5b y la opcional. Si el núcleo va con más de 2 semanas de retraso al final de la Fase 3, la Fase 5b se reduce a un estudio de casos cualitativo.

| Fase | Semanas | Contenido | Entregable / criterio de "hecho" | Fable | Opus |
|---|---|---|---|---|---|
| **0. Preparación** | 1 | Repo, entorno (`uv`), DVC, MLflow, `CLAUDE.md`. **Pedir acceso a OpenSky y ACLED** (con aval del tutor). Revisar licencias. Decidir GPU. Elegir 3-4 aeropuertos civiles con PNOA reciente y 2-3 bases con ejercicios pasados bien cubiertos por ADS-B. | Repo con tests en CI pasando, `docs/licencias.md`, `docs/decisiones.md` iniciado. | Spec, CLAUDE.md, elección de sitios | Montaje |
| **1. ADS-B + MCP 1** | 2-4 | Descarga histórica por zona y fechas a Parquet. Enriquecimiento con tipo vía icao24. MCP 1. | Preguntar a Claude "¿qué aviones aterrizaron en Barajas el día X?" y obtener datos reales, con tests sobre respuestas guardadas. | Spec + revisión | Todo el código |
| **1b. Prueba de concepto de verdad terreno** | 2-3 (en paralelo) | 1 aeropuerto, 1 ortofoto, detector preentrenado sin ajustar, ADS-B de ese día. Contar a mano y comparar. | Informe corto: ¿cuántos aviones de la foto se pueden explicar con ADS-B? **Decisión de seguir o replantear.** | Spec + decisión | Ejecución |
| **2. Detector** | 5-7 | YOLO-OBB en DOTA/FAIR1M. Partición por aeródromo. Evaluación en test y en PNOA etiquetado a mano (~200-300 aviones). | mAP en origen y en PNOA (cuantifica el cambio de dominio). | Spec + revisión | Entrenamiento, etiquetado asistido |
| **3. Clasificador de tipo** | 8-10 | Recortes + medidas por GSD. MAR20 + FAIR1M, clase "desconocido", top-3, línea base solo-medidas. | Matriz de confusión, análisis de tipos confundidos, comparación con la línea base. | Spec + revisión | Implementación |
| **4. Cruce y validación civil** | 11-12 | Detecciones vs ADS-B en la fecha de cada ortofoto, con verdad fuerte y débil. | **Resultado central:** % detectado, % bien clasificado, huecos, separado por aeropuerto y tipo de verdad. | Spec + revisión a fondo | Implementación |
| **5. Anomalías** | 13 | Línea base y anomalías con ADS-B, partición temporal, casos históricos y de control. | Gráficos de actividad con eventos marcados; precisión/recall frente a eventos conocidos. | Spec + revisión | Implementación |
| **5b. Noticias + causa probable** | 14-16 | Ingesta GDELT/ACLED, MCP 2, etiquetado de 50-100 anomalías, explicación con recuperación y citas. | F1 por clase con intervalos, matriz de confusión, ejemplos con fuentes citadas, resultado con *k* = 0. | Spec, protocolo de etiquetado, revisión | Implementación, ingesta |
| **6. MLOps y cierre** | 17 | `dvc repro` de punta a punta, alertas de deriva, panel de resultados, memoria/README con limitaciones. | Proyecto reproducible desde cero en una máquina limpia. | Estructura y conclusiones | Documentación técnica, panel |
| **Opcional** | — | Con imágenes comerciales frecuentes: serie temporal de conteos por base fusionada con ADS-B (agregada). | — | — | — |

---

## 6. Estructura del repositorio

```
avion-osint/
├── CLAUDE.md              # normas para Claude: estilo, reparto de roles, tests, límites éticos
├── README.md
├── .env.example           # nombres de variables, nunca valores reales
├── docs/
│   ├── specs/             # fase-N.md (Fable) y fase-N-dudas.md (Opus)
│   ├── revisiones/        # fase-N.md: veredicto de Fable
│   ├── decisiones.md      # registro de decisiones
│   └── licencias.md       # condiciones de uso de cada fuente
├── data/                  # versionado con DVC (no en git)
├── src/
│   ├── adsb/              # descarga y limpieza de ADS-B
│   ├── news/              # ingesta de GDELT, ACLED y comunicados
│   ├── mcp_server/
│   │   ├── opensky/       # MCP 1
│   │   └── contexto/      # MCP 2
│   ├── vision/            # detector y clasificador
│   ├── fusion/            # cruce imagen ↔ ADS-B
│   ├── anomalies/         # línea base y anomalías
│   └── causes/            # explicación de causa probable
├── pipelines/             # dvc.yaml
├── notebooks/             # exploración (nunca lógica que no esté también en src/)
└── tests/
```

---

## 7. Checklist de calidad y revisión

Opus la rellena al cerrar cada fase; Fable la usa para revisar.

- [ ] **Fugas de datos:** ¿mismo aeródromo, escena o fecha en train y test? ¿Periodos mezclados al evaluar anomalías? ¿Noticias posteriores al corte de *k* días?
- [ ] **Métricas engañosas:** ¿accuracy alta por desbalance? Reportar siempre F1 por clase y matriz de confusión. ¿Hay línea base sencilla para comparar?
- [ ] **Incertidumbre:** con pocos casos, ¿se dan intervalos de confianza?
- [ ] **Cambio de dominio:** ¿evaluado en datos de origen **y** en PNOA/NAIP por separado?
- [ ] **Explicaciones:** ¿cada causa propuesta tiene evidencia citada? Si no, "sin explicación pública".
- [ ] **Reproducibilidad:** semillas fijas, versiones de datos en DVC, experimentos en MLflow, comando para repetir el resultado.
- [ ] **Tests:** cada módulo de `src/` con tests básicos; los MCP con respuestas guardadas.
- [ ] **Licencias:** ¿los datos usados permiten lo que se ha hecho con ellos?
- [ ] **Límites del proyecto:** ¿algo se acerca a seguimiento en vivo, alerta de operaciones o predicción de ataques? ¿Se respeta el retraso mínimo y la agregación en bases militares?
- [ ] **Honestidad:** ¿lo que no se ha podido probar está dicho como tal?

---

## 8. Contexto del autor

- Estudiante de grado en España (Inteligencia Artificial). Intereses: ML, CNN, MLOps, radar, geopolítica y análisis aplicado.
- Objetivo: proyecto de portfolio o TFG riguroso, con resultados honestos aunque sean negativos.

---

## 9. Glosario rápido

- **ADS-B:** señal que emiten los aviones con su posición, altitud e identificador; la captan receptores en tierra.
- **icao24 / Mode S:** código hexadecimal único del transpondedor de cada avión.
- **NOTAM:** aviso oficial a pilotos sobre cierres, restricciones o actividad especial en el espacio aéreo.
- **Ortofoto:** foto aérea corregida para que tenga escala uniforme, como un mapa.
- **GSD:** tamaño real (en metros) que representa un píxel de la imagen.
- **OBB (caja orientada):** rectángulo que puede girar para ajustarse a un objeto en diagonal.
- **mAP:** métrica estándar de detección; resume precisión y exhaustividad a varios umbrales.
- **IoU:** cuánto se solapa la caja predicha con la real (0 = nada, 1 = perfecta).
- **F1:** media entre precisión (cuántos de los que marco son correctos) y exhaustividad (cuántos de los correctos encuentro).
- **Matriz de confusión:** tabla que muestra qué clase real se confunde con cuál.
- **Cambio de dominio:** el modelo empeora al pasar a imágenes distintas de las de entrenamiento.
- **Fuga de datos:** información del test que se cuela en el entrenamiento y da métricas falsamente buenas.
- **Deriva:** los datos nuevos dejan de parecerse a los de entrenamiento con el tiempo.
- **MCP:** protocolo para que Claude use herramientas externas (aquí, consultar nuestros datos).
- **DVC / MLflow:** herramientas para versionar datos y registrar experimentos, respectivamente.
- **Etiquetas débiles:** etiquetas obtenidas automáticamente (p. ej. de ADS-B), útiles pero con errores.
