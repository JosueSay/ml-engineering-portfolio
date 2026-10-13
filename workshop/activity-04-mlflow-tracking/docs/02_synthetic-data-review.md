# Análisis del generador de datos sintéticos

Documentación oficial completa: [Logging plots in MLflow](https://mlflow.org/docs/latest/ml/traditional-ml/tutorials/hyperparameter-tuning/notebooks/logging-plots-in-mlflow/),
la página del tutorial que publica la función analizada.

Responde al inciso (a) del segundo punto del taller: analizar la sección que genera los
datos sintéticos y ver si se le pueden hacer mejoras al algoritmo propuesto.

- Función del tutorial, copiada sin cambios: [`tutorial_data.py`](../src/mlflow_workshop/tutorial_data.py)
- Versión mejorada: [`synthetic_data.py`](../src/mlflow_workshop/synthetic_data.py)

La función no usa MLflow: es `numpy` y `pandas`. Fabrica los datos con los que después se
entrena y se registra. Las cifras se midieron con pandas 3.0.6, generando 5,000 filas.

## El criterio

Unos datos sintéticos son un examen con clave de respuestas. El autor escribe la fórmula
que genera la demanda, así que conoce la respuesta correcta:

$$
\text{demanda} = (\text{base} - 50 \cdot \text{precio} + 50 \cdot \text{cosecha} + 200 \cdot \text{promo} + 300 \cdot \text{fin de semana} + \varepsilon) \cdot \text{inflación}
$$

Sirven para comprobar si un modelo aprende lo que debería. Si la clave está mal, la nota
del modelo no significa nada.

Por eso el análisis no pregunta si los datos se parecen a la realidad. Pregunta esto:
**¿los datos hacen lo que su autor dice que hacen?** Cada mejora sale de encontrar una
promesa incumplida.

## Las preguntas

El criterio se baja a cinco preguntas que se le hacen al código, más una sexta de menor
peso. Cada una tiene una forma de comprobarse que no depende de opiniones.

| # | Pregunta | Cómo se comprueba | Hallazgos |
| :--- | :--- | :--- | :--- |
| 1 | ¿Se ejecuta? | Corriéndolo | 1 y 2 |
| 2 | ¿Da lo mismo cada vez? | Corriéndolo dos veces y comparando | 3 y 4 |
| 3 | ¿Cada línea hace lo que promete su comentario? | Leyendo el comentario y midiendo el resultado | 5 |
| 4 | ¿Cada variable aporta algo a la demanda? | Midiendo su distribución y su correlación con la demanda | 6 y 7 |
| 5 | ¿Lo que el modelo ve al entrenar es lo que verá al usarse? | Comparando la columna con el dato real que representa | 8 |
| 6 | ¿Es verosímil? | Mirando la forma de la serie | 9 |

### 1. ¿Se ejecuta?

- **Hallazgo 1.** `fillna(method="bfill", inplace=True)` falla con `TypeError`: pandas 3
  eliminó el argumento `method`. La función no devuelve nada.
- **Hallazgo 2.** Corregido eso, `df["marketing_intensity"].fillna(..., inplace=True)` no
  da error pero tampoco hace nada: en pandas 3 actúa sobre una copia. Quedan nulos en el
  marketing y, como se suma a la demanda, también en el objetivo.
- **Mejora.** Sin `fillna`. Se generan 7 días previos que se descartan, así ningún rezago
  nace vacío.

Estos dos son los únicos hallazgos que dependen de la versión de pandas.

### 2. ¿Da lo mismo cada vez?

- **Hallazgo 3.** Las fechas salen de `datetime.now()`. La semilla fija los números al
  azar, pero no el calendario: mañana los mismos números caen en otros días, y con ellos
  cambian el fin de semana, el mes, las promociones y la inflación.
- **Hallazgo 4.** `np.random.seed(9999)` fija la semilla global de numpy, así que altera
  cualquier otro código que use números al azar en el mismo proceso.
- **Mejora.** Fecha final fija como parámetro (`end_date`) y generador propio con
  `np.random.default_rng(seed)`.

### 3. ¿Cada línea hace lo que promete su comentario?

- **Hallazgo 5.** El comentario dice "seasonality due to apple harvests" y la intención son
  dos cosechas al año. El código suma dos senos desfasados seis meses, que es medio ciclo,
  y dos senos a medio ciclo se cancelan: $\sin(x) + \sin(x - \pi) = 0$. Al calcular la
  columna para los doce meses, su valor máximo es $2.2 \times 10^{-16}$, puro error de
  redondeo. La estacionalidad no existe, ni en el precio ni en la demanda.
- **Mejora.** Un coseno de periodo 6 meses, con máximos en marzo y septiembre.

Es el hallazgo más importante porque es silencioso. El resultado es idéntico en cada
ejecución, pero reproducible no significa correcto: da siempre el mismo valor equivocado.

¿Y si el autor quiso dejarla en cero? El propio código lo descarta, sin saber nada del
negocio de las manzanas. Tres líneas posteriores dan por hecho que la cosecha varía:

- `peak_months = [4, 10]  # months following the peak availability` habla de un pico de
  disponibilidad, que no existe si la columna es constante.
- `price_per_kg - harvest_effect * 0.5` ajusta el precio según la cosecha.
- `seasonality_effect = harvest_effect * 50` suma la estacionalidad a la demanda.

Nadie escribe dos senos y tres líneas que dependen de ellos para obtener cero. Que las
manzanas tengan o no estacionalidad en la realidad es una pregunta de negocio; que el
código no entrega la que su autor describió es un hecho.

### 4. ¿Cada variable aporta algo a la demanda?

- **Hallazgo 6.** La intensidad de marketing vale entre 0.7 y 1 en el 99.8 % de los días,
  casi una constante, y se suma a la demanda sin coeficiente: aporta menos de 1 unidad a
  una demanda de unas 1,200. Su correlación con la demanda es $-0.02$.
- **Hallazgo 7.** Temperatura, lluvia y festivos se entregan como variables pero no entran
  en la fórmula. Tener variables de ruido es útil; el problema es que no se declara.
- **Mejora.** El marketing sale de la fracción de días con inventario alto en la última
  semana y entra con un coeficiente explícito. Lluvia y festivos reciben efecto; la
  temperatura queda como variable de control, y la función lo documenta.

### 5. ¿Lo que el modelo ve al entrenar es lo que verá al usarse?

- **Hallazgo 8.** `previous_days_demand` se calcula antes de sumar los efectos de la
  competencia y del marketing. Difiere de la demanda real del día anterior en hasta 50
  unidades. En uso real, el modelo recibiría la demanda de ayer, no ese valor intermedio.
- **Mejora.** El rezago se calcula al final, sobre la demanda terminada.

### 6. ¿Es verosímil?

- **Hallazgo 9.** La inflación sube en un escalón cada 1 de enero y multiplica también el
  ruido, que así crece con los años.
- **Mejora.** Crecimiento continuo por días transcurridos, aplicado a la señal y no al
  ruido.

## Cuánto vale cada hallazgo

| Tipo | Hallazgos | Qué lo respalda |
| :--- | :--- | :--- |
| Demostrable | 1, 2, 3 y 5 | Un mensaje de error, dos ejecuciones que difieren o una identidad matemática |
| Medible | 6 y 8 | Una cifra. Que sea un defecto depende de aceptar que la variable debe aportar señal |
| De criterio | 4, 7 y 9 | Buenas prácticas o decisiones de diseño que un tutorial puede dejar por simplicidad |

Si hubiera que quedarse con tres mejoras, salen de las demostrables: la estacionalidad (5),
la reproducibilidad (3) y la ejecución en pandas 3 (1 y 2).

## Resultado

| Comprobación | Tutorial | Mejorado |
| :--- | :--- | :--- |
| Se ejecuta con pandas 3 | No | Sí |
| Dos ejecuciones dan el mismo resultado | Solo el mismo día | Sí |
| Valores nulos en la demanda | Sí | No |
| Amplitud del efecto de cosecha | 0 | 1 |
| Correlación de marketing con la demanda | $-0.02$ | $0.15$ |
| El rezago coincide con la demanda del día previo | No | Sí |

Las cifras del tutorial se midieron corrigiendo solo las dos líneas de `fillna`, sin lo
cual la función no devuelve nada que medir.

## Fuera del generador: la partición

La misma pregunta 5 aplica a cómo se separan los datos. El tutorial usa `train_test_split`
aleatorio, que mezcla días futuros en el entrenamiento. El primer notebook registra el
mismo modelo con las dos particiones:

| Partición | RMSE | $R^2$ | Sesgo medio |
| :--- | :--- | :--- | :--- |
| Aleatoria, como en el tutorial | 129.4 | 0.768 | 3.2 |
| Temporal, último 20 % de los días | 198.1 | 0.424 | 175.7 |

La partición aleatoria hace parecer bueno a un modelo que se queda corto en el 98 % de los
días futuros.
