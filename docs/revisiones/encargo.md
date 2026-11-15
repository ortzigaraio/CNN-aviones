# Revisión del encargo (Fable, 2026-11-15)

Revisión de `docs/encargo.md` antes de empezar. El planteamiento es sólido: límites claros, resultado central bien elegido y una prueba de concepto temprana donde más duele. Lo que sigue son los huecos y riesgos que el documento no cubre o cubre a medias, ordenados por gravedad.

Nada de lo que se afirma aquí sobre fuentes externas (qué ofrece el CNIG, qué permite OpenSky hoy) está comprobado en esta revisión: son puntos a verificar y así aparecen en las especificaciones.

## Graves (pueden cambiar el resultado central)

### 1. Las clases del clasificador no coinciden con lo que hay en los aeropuertos españoles

El resultado central es «% bien clasificado frente a ADS-B en aeropuertos civiles». Pero:

* FAIR1M (el dataset civil) tiene clases como Boeing 737/747/777/787, A220, A321, A330, A350, ARJ21, C919 y «otro avión». **No tiene A320 ni A319** como clase propia, ni ATR, CRJ o Embraer, que son buena parte del tráfico en Barajas, Barcelona o Palma.
* MAR20 son 20 tipos militares: no aportan nada a la validación civil.
* ADS-B da el tipo con el código OACI (`A320`, `B738`, `AT76`…), otra taxonomía distinta.

Tal cual está, muchos aviones de la foto caerían en «otro» y el porcentaje no significaría gran cosa.

**Propuesta (se decide en la spec de la Fase 3):** evaluar en dos niveles. Nivel grueso obligatorio: categoría por tamaño (ligero, regional, pasillo único, fuselaje ancho), que se puede obtener de ADS-B sin ambigüedad. Nivel fino: solo para las familias que existan a la vez en el dataset y en ADS-B, con una tabla de equivalencias escrita antes de mirar resultados. Y valorar entrenar con recortes propios de PNOA etiquetados por ADS-B (etiquetas débiles) en aeropuertos distintos de los de evaluación.

### 2. La hora de la foto se puede acotar mucho mejor de lo que el encargo supone

El encargo depende de que el CNIG dé la hora. Hay dos métodos que no dependen de eso:

* **Sombras:** con la fecha y la dirección de la sombra de un objeto vertical (torre de control, farolas) se calcula la hora solar. Error esperable: decenas de minutos.
* **«Reloj ADS-B»:** un avión que sale en la foto rodando o en la pista está emitiendo. Si su posición ADS-B coincide con la de la foto, fija la hora al minuto. Con dos o tres coincidencias, además, se detecta si el mosaico mezcla pasadas.

Entran como tareas en la Fase 1b. Si funcionan, casi toda la verdad «débil» pasa a ser «fuerte» y el punto débil 2 se reduce mucho.

### 3. Muy pocas fotos: el resultado central tendrá intervalos anchos

3-4 aeropuertos con una ortofoto cada uno son unos pocos cientos de aviones, repartidos en muchas clases. Los intervalos de confianza por clase serán enormes.

**Propuesta:** usar también las ortofotos PNOA de años anteriores del mismo aeropuerto, siempre que haya ADS-B de esa fecha (aproximadamente desde 2016-2017 en OpenSky). Triplica las fechas sin añadir fuentes. Y fijar desde ya que el resultado central se da con intervalos, por aeropuerto y agregado.

### 4. La fecha de la foto y el histórico de ADS-B tienen que solaparse

La elección de aeropuertos no es libre: solo valen las ortofotos cuya fecha de vuelo cae dentro del histórico de ADS-B al que se tenga acceso. Si OpenSky deniega el acceso de investigador y solo queda adsb.lol (histórico más corto), algunas ortofotos dejan de servir. Por eso la Fase 0 verifica las fechas antes de elegir sitios, y la elección final es condicional.

### 5. El modelo de lenguaje ya «sabe» lo que pasó

El corte de *k* días filtra las noticias recuperadas, pero el modelo de lenguaje fue entrenado con texto posterior: conoce Trident Juncture o Steadfast Defender de memoria. Puede acertar la causa sin usar la evidencia, y eso es fuga temporal igualmente.

**Propuesta (spec de la Fase 5b):** medir esa fuga con una prueba «a libro cerrado» (el mismo modelo sin evidencia recuperada). Si acierta mucho, el resultado con evidencia no demuestra nada sobre el sistema. Exigir además que cada causa cite un documento recuperado concreto, y contar como fallo cualquier causa sin cita válida.

## Importantes

### 6. La cobertura de ADS-B cambia con los años

Cada año hay más receptores. Un aeródromo puede mostrar «más actividad» en 2024 que en 2018 solo porque se ve mejor. La línea base de anomalías «frente al mismo periodo de otros años» lo confundiría con actividad real. Hay que normalizar por una medida de cobertura (por ejemplo, actividad civil regular del mismo aeródromo o de vecinos) o limitar la comparación a años con cobertura comparable. Se decide en la spec de la Fase 5.

### 7. Sesgo de selección en los casos de anomalía

Elegir ejercicios «donde haya buena cobertura ADS-B» es razonable, pero la precisión y exhaustividad resultantes solo valen para ese tipo de caso. Hay que decirlo así en la memoria, no presentarlo como rendimiento general.

### 8. La Fase 1b no puede esperar al pipeline de la Fase 1

Van en paralelo (semanas 2-3), pero la 1b necesita ADS-B de un día concreto. La spec de la 1b pide una descarga mínima y manual de ese día, independiente del pipeline.

### 9. Falta definir qué es un aeródromo «militar»

La regla de agregación necesita una lista. Se crea `config/aerodromos.yaml` con un campo `tipo` (`civil`, `militar`, `mixto`). Los mixtos (Zaragoza, por ejemplo) se tratan como militares. Entra en la Fase 0.

### 10. Licencia del detector preentrenado

Los modelos YOLO de Ultralytics se publican bajo AGPL-3.0 (licencia que obliga a publicar bajo la misma licencia el código que los use si se distribuye o se ofrece como servicio). Para un TFG con repositorio público es asumible, pero condiciona la licencia del propio repositorio. Además, los pesos entrenados con DOTA heredan sus condiciones (uso académico). Se anota en `docs/licencias.md` y se decide la licencia del repo antes de hacerlo público.

### 11. Aviones en hangar y aviación ligera

* Un avión dentro de un hangar está en la verdad ADS-B («aterrizó y no ha salido») pero no en la foto. Infla los «fallos» del detector si no se separa.
* Muchas avionetas no emiten ADS-B. Si se cuentan junto a los comerciales, hunden la cobertura sin que sea un fallo del método.

La Fase 1b reporta por separado comerciales y aviación ligera, y anota los hangares como causa posible del exceso de ADS-B.

## Menores

* **Retraso mínimo:** el encargo dice «configurable (por defecto 30 días)». Propongo que solo se pueda subir, nunca bajar de 30: una salvaguarda que se desactiva con una variable no es una salvaguarda. Registrado en `docs/decisiones.md`.
* **Datos personales:** las matrículas de aviones privados pueden identificar a personas. En informes y figuras, aviación privada siempre agregada.
* **Nombre del proyecto:** el encargo llama al repo `avion-osint`; el repo real es `CNN-aviones`. El paquete Python se llama `avion_osint`.
* **Estructura de `src/`:** el encargo pone `src/adsb`, `src/news`… directamente, lo que crea paquetes Python con nombres muy genéricos. Se usa `src/avion_osint/adsb`, etc.
* **Calendario:** 17 semanas es justo. La Fase 1 depende de permisos de terceros; el plan B (adsb.lol + API pública) se prepara desde el día 1, no cuando llegue la negativa.
* **ACLED:** sus condiciones de acceso se han endurecido en los últimos años. Verificar pronto si un estudiante de grado puede acceder y qué puede redistribuir.

## Lo que necesito del autor

1. **Tutor y afiliación:** ¿hay tutor que avale la solicitud a OpenSky y ACLED? Sin eso, se va directo al plan B.
2. **GPU:** ¿la universidad ofrece alguna? Si no, propongo Kaggle (GPU gratuita con cupo semanal) como opción por defecto.
3. **Repositorio público o privado**, por la licencia (punto 10).
4. **Conteo manual de la Fase 1b:** lo tiene que hacer una persona (1-2 horas con QGIS). No puede hacerlo el mismo modelo que luego se evalúa.
