# Ciclo de vida del caso

Las tres primeras fases del ciclo de vida de un proyecto de datos, aplicadas a
este caso: qué se quería resolver, qué se encontró en los datos y qué hubo que
hacerles antes de que sirvieran. Parte de la documentación; el índice está en
[README.md](README.md).

Se documenta después de hacerlo y no antes, y se nota: casi todo lo que sigue
contradice lo que se suponía al empezar. Eso es el contenido, no un defecto del
documento.

## 1. Comprensión del problema

### La pregunta

Cuándo conviene llenar el tanque. No cuánto cuesta hoy —eso se ve en el rótulo—
sino si esperar una semana sale mejor o peor.

### Qué haría útil una respuesta

Una recomendación sirve si quien la recibe puede actuar sobre ella. De ahí tres
condiciones que se fijaron antes de escribir código:

- **Horizonte corto.** A un mes nadie planifica una carga de combustible. Se
  predice a 1, 2 y 4 semanas.
- **Con su motivo.** Un `SÍ` sin explicación no es accionable. La recomendación
  devuelve el porqué junto al qué.
- **Sobre un dato rastreable.** Ante una recomendación mala hay que poder saber
  si falló el modelo o si falló la lectura de la fotografía. Son dos problemas
  distintos y desde fuera se ven igual.

Esa tercera condición es la que más forma le dio al proyecto. No es una
propiedad del modelo: es la forma de los datos, y por eso ocupa siete tablas
encadenadas en vez de un campo que alguien rellena.

### Restricciones que vinieron dadas

- Servidor modesto, sin tarjeta gráfica.
- No usar un modelo de lenguaje como predictor.
- El histórico de fotografías llega tarde, cuando el pipeline ya tiene que
  existir.

La tercera obligó a una decisión temprana: **el sistema tiene que funcionar sin
datos reales**. De ahí la serie sintética, la decisión explícita de fuente en la
integración continua, y que los datos nunca vivan en el repositorio.

### Qué es fracasar

Se escribió antes de medir nada, para no moverlo después:

- Que el error del modelo supere el umbral configurado.
- Que no mejore a una referencia simple. Un modelo que no gana a "mañana igual
  que hoy" no aporta.
- Que la señal de tendencia sea peor que aleatoria.

Las tres son una compuerta que **falla la corrida**, no un informe que alguien
lee. Un pipeline en verde con un modelo inservible es peor que uno en rojo.

## 2. Comprensión de los datos

### Lo que se creía tener

Fotografías de tótems con cuatro precios legibles: diésel, regular, súper y
V-Power. La suposición era que extraerlos sería mecánico y el trabajo estaría en
el modelo.

### Lo que había

Al mirar los recortes guardados, **10 de 16 no contenían display**. La
localización, no la lectura, era el problema mayor.

Y sobre los que sí lo contenían, el clasificador de siete segmentos leía `4??8`
donde el rótulo decía `43.19`. La causa tardó en aparecer porque parecía
perspectiva: se probó rectificar y no cambió nada. **Los dígitos son cursivos
por diseño tipográfico**, no por el ángulo de la cámara. Corregir la
inclinación llevó la lectura de 0 a 4 de 5 dígitos, y reposicionar el punto
decimal por su lugar —un precio en quetzales siempre lleva dos decimales— dio la
primera lectura correcta.

### Lo que eso cambió

Que la extracción **no va a ser completa**, y que eso no es un fallo a corregir
sino una condición del problema. De ahí que el eje del caso se desplazara: lo
interesante no es leer el 100% de las fotografías, sino qué se hace con lo que
falta.

También cambió qué se mide. La métrica que importa no es el acierto por dígito
sino **la proporción de lecturas válidas sobre el conjunto completo**, y se fijó
un umbral con consecuencia: por debajo del 70%, entrenar un detector de visor en
vez de seguir afinando reglas.

### Lo que se descartó, y por qué

Un modelo de visión y lenguaje como caja negra. Se probó y no quedó:

- 1.5 GB de pesos contra la restricción de servidor modesto.
- Requiere ejecutar código del repositorio remoto para cargarse.
- Su repositorio no publica versiones, solo una rama, y una confirmación cambió
  los pesos a un modelo distinto sobre esa misma rama. "El modelo" no era una
  cosa fija: descargarlo dos veces en fechas distintas daba dos modelos
  diferentes con el mismo nombre.

Ese último punto sobrevivió al descarte y es hoy política del proyecto: **fijar
la revisión exacta, nunca la rama**, y fallar ruidosamente si no está declarada.

## 3. Preparación de los datos

### Tres capas, y por qué tres

| Capa | Qué contiene | Qué se puede rehacer sin ella |
|---|---|---|
| Bronze | Lo leído de cada fotografía, tal cual, con su confianza | Nada: es el único punto donde existe el vínculo con la imagen |
| Silver | Precios limpios, validados y con los huecos tratados | Se rehace desde Bronze |
| Gold | El conjunto de modelado, con sus features | Se rehace desde Silver |

La separación no es organización: es qué se pierde si algo se borra. Bronze es
irreemplazable porque reconstruirlo exige volver a las fotografías.

### El tratamiento de los huecos, que es el centro

Una lectura fallida no se descarta ni se rellena en silencio. Cada precio que
llega al conjunto de modelado **declara de dónde salió**:

| Método | Qué significa |
|---|---|
| `ocr` | Leído de una fotografía |
| `arithmetic` | Recuperado del total de la factura, con conversión de litros a galones y una cota de plausibilidad |
| `interpolated` | Interpolado entre dos lecturas reales del mismo combustible |
| `median_imputed` / `mean_imputed` | Imputado, y con cuál estadístico |
| `synthetic` | Generado, sin fotografía detrás |

Esa columna viaja hasta el modelo. Se descubrió que no lo hacía —`build_features`
la dejaba fuera— y se corrigió: un dato imputado y uno leído no valen lo mismo, y
el modelo no puede distinguirlos si nadie se lo dice.

Reglas que salieron de errores concretos:

- **No se mezclan combustibles al rellenar.** El precio del diésel no informa
  sobre el del súper.
- **Solo se marcan las filas efectivamente rellenadas**, no el bloque entero.
- **Las filas sintéticas se marcan como tales.** Al principio decían `ocr` y
  nadie las leía como lo que eran.

### Reproducibilidad

Dos cosas rompían que dos ejecuciones dieran lo mismo, y las dos se arreglaron:

- La serie sintética llegaba hasta "hoy". El conjunto cambiaba cada día sin que
  cambiara nada más. Ahora la fecha de corte se resuelve con precedencia
  explícita y avisa solo cuando la elección no es reproducible.
- El reprocesado era ciego. Ahora la caché se indexa por el trío **datos,
  versión del paquete y huella de la configuración**: cambiar cualquiera de los
  tres reprocesa, y no cambiar ninguno no cuesta nada.

### Qué no se hizo

- **No se aumentó el conjunto de imágenes.** Con 16 fotografías, generar
  variantes no crea información nueva y da una falsa sensación de volumen.
- **No se descartaron las filas incompletas.** Descartar es la salida fácil y
  destruye justo lo que este caso quería estudiar.
- **No se mezcló la exploración con el pipeline.** Los cuadernos viven aparte;
  lo que entra al pipeline es código con pruebas.

## Lo que quedó pendiente de este ciclo

Con el histórico completo hay que rehacer las mediciones de la fase 2, porque
las de arriba salen de 16 fotografías y no aguantan una conclusión. En concreto:
volver a medir la proporción de lecturas válidas, decidir si se cruza el umbral
del 70%, revisar la calibración de paneles contra el conjunto real y elegir la
estrategia de relleno según lo que muestren los datos, no según lo que parezca
razonable ahora.

El flujo completo, de la fotografía a la recomendación, está en
[12_flow.md](12_flow.md).
