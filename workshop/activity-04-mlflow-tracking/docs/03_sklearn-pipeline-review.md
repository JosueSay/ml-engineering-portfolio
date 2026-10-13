# Análisis del código que conecta MLflow con un Pipeline

Documentación oficial completa: [MLflow Scikit-learn Integration](https://mlflow.org/docs/latest/ml/traditional-ml/sklearn/).

Responde al tercer punto del taller: buscar en la documentación la sección que explica cómo
usar MLflow y scikit-learn en conjunto, y analizar el código que muestra cómo conectar
MLflow con un `Pipeline`.

Las cifras salen de ejecutar el ejemplo oficial sin cambios, con MLflow 3.17.1 y
scikit-learn 1.9.1.

## Dónde lo explica la documentación

| Página | Sección | Qué explica |
| :--- | :--- | :--- |
| [MLflow Scikit-learn Integration](https://mlflow.org/docs/latest/ml/traditional-ml/sklearn/) | "Autologging" y "What Gets Logged" | Con `mlflow.sklearn.autolog()` se registran los parámetros de `get_params(deep=True)`, las métricas, el modelo con su firma y los artefactos |
| La misma | "Hyperparameter Tuning", "Grid Search" | Con `GridSearchCV` se crea una ejecución hija por combinación y el mejor estimador se guarda aparte |
| [Automatic Logging with MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/autolog/) | "Scikit-learn" | Un `Pipeline` es un meta-estimador: produce una sola ejecución, no una por paso. Enlaza el código de ejemplo |

La idea central de esas secciones: la conexión no se escribe paso por paso. Se activa una
vez y MLflow intercepta la llamada a `fit`.

## El código analizado

El enunciado no entrega código, así que se analiza el ejemplo al que remite la
documentación:
[`examples/sklearn_autolog/pipeline.py`](https://github.com/mlflow/mlflow/blob/master/examples/sklearn_autolog/pipeline.py),
del repositorio de MLflow. Lo esencial:

```python
mlflow.sklearn.autolog()

X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
y = np.dot(X, np.array([1, 2])) + 3

pipe = Pipeline([("scaler", StandardScaler()), ("lr", LinearRegression())])
pipe.fit(X, y)
run_id = mlflow.last_active_run().info.run_id
```

Cuatro filas, un escalador y una regresión lineal. No hay ninguna llamada a `log_param` ni
a `log_metric`.

## El criterio

Conectar un pipeline con MLflow sirve si otra persona, más adelante y sin el código que lo
entrenó, puede hacer dos cosas: entender cómo se hizo el modelo y volver a usarlo.

La pregunta de fondo es: **¿lo que quedó registrado alcanza para entender y reutilizar el
pipeline sin tener el código original?**

## Las preguntas

| # | Pregunta | Cómo se comprueba | Resultado en el ejemplo |
| :--- | :--- | :--- | :--- |
| 1 | ¿Dónde está la conexión? | Leyendo qué líneas mencionan a MLflow | Una sola línea |
| 2 | ¿Se sabe cómo se hizo? | Listando los parámetros registrados | Sí |
| 3 | ¿Se sabe qué tan bueno es? | Listando las métricas y viendo sobre qué datos se calcularon | No |
| 4 | ¿Se puede volver a usar? | Cargando el modelo y prediciendo con datos crudos | Sí |
| 5 | ¿Se puede encontrar después? | Mirando en qué experimento y con qué nombre quedó | Con dificultad |
| 6 | ¿Qué pasa con un pipeline real? | Probando pasos propios y una búsqueda | El ejemplo no lo cubre |

### 1. ¿Dónde está la conexión?

- **Hallazgo.** Toda la conexión es `mlflow.sklearn.autolog()` antes de `fit`. El pipeline
  no se modifica y no sabe que MLflow existe.
- **Consecuencia.** El orden importa: activado después de `fit`, no registra nada.

### 2. ¿Se sabe cómo se hizo?

- **Hallazgo.** Quedan 14 parámetros, los de todos los pasos y no solo los del modelo. Cada
  uno lleva el nombre de su paso como prefijo: `scaler__with_mean`, `lr__fit_intercept`.
  También queda `steps`, con el orden de los pasos.
- **Por qué importa.** Dos pipelines con el mismo modelo y distinto preprocesamiento dan
  resultados distintos. Registrar solo el modelo los haría parecer iguales.

### 3. ¿Se sabe qué tan bueno es?

- **Hallazgo.** Quedan 5 métricas y todas empiezan con `training_`. Se calcularon sobre las
  mismas 4 filas con que se entrenó, y $R^2$ vale 1.0 porque los datos son exactamente
  lineales.
- **Límite.** No hay conjunto de prueba. La métrica registrada no dice nada sobre datos
  nuevos, y el autologging no puede inventarla: no sabe cuál es el conjunto de prueba.

### 4. ¿Se puede volver a usar?

- **Hallazgo.** El modelo guardado es el pipeline completo, escalador incluido. Cargado
  desde MLflow y con datos sin escalar, predice `[6, 16]` para las filas `[1, 1]` y
  `[3, 5]`, que es el valor exacto de $y = x_1 + 2 x_2 + 3$.
- **Por qué importa.** Quien usa el modelo no tiene que repetir el preprocesamiento. Es la
  razón principal para registrar el pipeline y no el estimador suelto.

### 5. ¿Se puede encontrar después?

- **Hallazgo.** La ejecución cae en el experimento `Default` con un nombre al azar, en esta
  corrida `nosy-crow-504`, y sin etiquetas propias.
- **Límite.** Con diez ejecuciones así no se distingue cuál es cuál. El autologging decide
  qué registrar, no cómo organizarlo.

### 6. ¿Qué pasa con un pipeline real?

El ejemplo usa solo piezas de scikit-learn y un único entrenamiento. Al llevarlo al
pipeline del taller aparecieron tres cosas que el ejemplo no muestra:

- **Pasos propios.** Un transformador escrito por el equipo hay que declararlo en
  `skops_trusted_types` al guardar el modelo, y sus atributos aprendidos deben ser tipos
  simples.
- **Búsqueda de hiperparámetros.** Las ejecuciones hijas heredan los parámetros del
  pipeline base, así que pueden mostrar valores que no les aplican.
- **Guardado por defecto.** El autologging guarda el modelo con `pickle`, y MLflow avisa en
  cada ejecución que el formato recomendado es `skops`.

## Cuánto vale cada hallazgo

Ninguno es un error del ejemplo: hace lo que promete, que es mostrar el autologging sobre
un `Pipeline` en el menor número de líneas. Son los límites de usarlo tal cual.

| Tipo | Preguntas | Qué lo respalda |
| :--- | :--- | :--- |
| Demostrable | 2, 3 y 4 | La lista de parámetros y métricas registradas, y una predicción comprobada a mano |
| Observable | 1 y 5 | Lo que se ve en el código y en la interfaz |
| De criterio | 6 | Depende de qué tan lejos esté el pipeline propio del ejemplo |

## Qué hace el notebook del taller con cada límite

| Límite del ejemplo | Cómo se resuelve en [`02_mlflow-sklearn-pipeline.ipynb`](../notebooks/02_mlflow-sklearn-pipeline.ipynb) |
| :--- | :--- |
| Solo métricas de entrenamiento | Partición temporal y métricas de prueba registradas a mano con `log_metrics` (sección 4) |
| Experimento `Default` y nombre al azar | Experimento propio creado al inicio, `run_name` en cada ejecución y etiquetas en las secciones 4 y 5 |
| Un solo entrenamiento | `GridSearchCV` con una ejecución padre y ocho hijas (sección 4) |
| Solo piezas de scikit-learn | Transformador propio `DemandFeatures` y registro con `skops_trusted_types` (sección 5) |
| Modelo sin versión | Model Registry con el alias `champion` (sección 5) |

La conclusión del análisis: el autologging basta para saber cómo se hizo un pipeline y para
volver a usarlo. Para saber qué tan bueno es y para encontrarlo después, hay que
completarlo con registro explícito.
