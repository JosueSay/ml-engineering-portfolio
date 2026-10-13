# Top de funcionalidades de MLflow

Documentación oficial completa: [MLflow para Machine Learning](https://mlflow.org/docs/latest/ml/).

Este documento responde al primer punto del taller: recorrer la documentación de MLflow,
elegir las páginas que más llamaron la atención y explicar por qué.

## Las tres páginas elegidas

| # | Página | Enlace |
| :--- | :--- | :--- |
| 1 | ML Experiment Tracking | <https://mlflow.org/docs/latest/ml/tracking/> |
| 2 | Automatic Logging with MLflow Tracking | <https://mlflow.org/docs/latest/ml/tracking/autolog/> |
| 3 | MLflow Scikit-learn Integration | <https://mlflow.org/docs/latest/ml/traditional-ml/sklearn/> |

### Por qué estas tres

- **Son las que se usan en el trabajo real.** Registrar experimentos, automatizar ese
  registro e integrarlo con la librería con la que ya se entrena es lo que un equipo hace a
  diario con MLflow. Conocerlas suma tanto para un puesto como para un proyecto propio o una
  startup, donde no hay nadie más que lleve la cuenta de qué se probó.
- **Cubren las fases de CRISP-DM que interesan en este taller.** Las tres se concentran en
  Modeling y Evaluation, que es donde se decide qué modelo se queda y con qué evidencia.
- **Se encadenan.** No son tres temas sueltos: el seguimiento define qué es una ejecución,
  el autologging la llena sin escribir código y la integración con scikit-learn lleva las
  dos cosas a un `Pipeline` y a una búsqueda de hiperparámetros. Los notebooks del taller
  las usan en ese orden.

### Qué aporta cada una

**1. Experiment Tracking.** Define los conceptos sobre los que se apoya todo lo demás:
el experimento como grupo de ejecuciones comparables, y la ejecución como el registro de un
entrenamiento, con sus parámetros, métricas, etiquetas, artefactos y conjunto de datos.
Llamó la atención que el almacén es intercambiable: el mismo código escribe en una base
SQLite local o en un servidor compartido cambiando solo la URI de seguimiento.

**2. Autologging.** Con `mlflow.autolog()` o `mlflow.sklearn.autolog()` antes de entrenar,
MLflow registra por su cuenta los parámetros del estimador, las métricas de entrenamiento y
el modelo. Llamó la atención lo que hace con los meta-estimadores: para un `Pipeline`
registra los parámetros de todos sus pasos, y para `GridSearchCV` crea una ejecución padre
y una hija por combinación.

**3. Scikit-learn Integration.** Es la página que pide el tercer punto del taller: explica
cómo usar las dos herramientas en conjunto. Reúne el autologging, el registro explícito con
`mlflow.sklearn.log_model`, la firma del modelo, la búsqueda de hiperparámetros y la
evaluación. Llamó la atención que el pipeline completo se guarda como un solo artefacto:
quien lo carga le pasa datos crudos y no tiene que repetir el preprocesamiento.

## El top 5 completo

Las tres páginas elegidas salen de una selección más amplia de cinco funcionalidades.

| Funcionalidad | Resumen | Utilidad práctica |
| :--- | :--- | :--- |
| 1. Experiment Tracking | Registra parámetros, métricas y modelos de cada entrenamiento; permite consultar resultados desde una interfaz gráfica. | Comparar experimentos y determinar qué configuración funciona mejor. |
| 2. Autologging | Automatiza el registro de métricas, hiperparámetros y modelos mediante `mlflow.autolog()`. | Reducir código repetitivo y mantener un historial de entrenamientos. |
| 3. Model Registry | Centraliza modelos, administra versiones, metadatos y alias, y permite rastrear su origen. | Controlar qué versión de un modelo se utiliza en producción y recuperar versiones anteriores. |
| 4. Scikit-learn Integration | Integra MLflow con modelos y pipelines de scikit-learn, incluyendo optimización mediante `GridSearchCV` y `RandomizedSearchCV`. | Registrar pipelines completos y comparar configuraciones de entrenamiento. |
| 5. Model Evaluation | Evalúa modelos de clasificación y regresión mediante métricas, gráficos y criterios de validación. | Detectar problemas de rendimiento y verificar si un modelo cumple los requisitos antes de utilizarlo. |

Las dos que quedaron fuera de la selección principal son
[Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) y
[Model Evaluation](https://mlflow.org/docs/latest/ml/evaluation/). No se descartan: el
segundo notebook las usa de forma breve para cerrar el ciclo, registrando el pipeline
ganador con un alias y evaluándolo con `mlflow.models.evaluate`.

Estas cinco funcionalidades permiten gestionar el desarrollo de modelos de Machine Learning
desde la experimentación hasta su evaluación y versionado, mejorando la reproducibilidad,
la trazabilidad y el mantenimiento en proyectos reales.

## Relación con CRISP-DM

Las cinco funcionalidades se utilizan principalmente en las etapas de Modeling, Evaluation
y Deployment del ciclo CRISP-DM.

| Funcionalidad | Etapa principal | Otras etapas | Aplicación |
| :--- | :--- | :--- | :--- |
| 1. Experiment Tracking | Modeling | Evaluation | Registra parámetros, métricas y resultados para comparar entrenamientos. |
| 2. Autologging | Modeling | Evaluation | Captura automáticamente parámetros, modelos y métricas durante el entrenamiento y la evaluación. |
| 3. Model Registry | Deployment | Evaluation | Gestiona versiones y permite seleccionar qué modelo utilizar en producción. |
| 4. Scikit-learn Integration | Modeling | Data Preparation, Evaluation | Integra el preprocesamiento y el entrenamiento mediante pipelines, registrando sus resultados en MLflow. |
| 5. Model Evaluation | Evaluation | Deployment | Calcula métricas, genera visualizaciones y valida si el modelo cumple criterios de rendimiento. |

MLflow no sustituye las etapas de CRISP-DM: funciona como una herramienta transversal que
permite registrar, evaluar, versionar y gestionar los modelos desarrollados durante el
proceso.

## Lo que hay detrás de cada funcionalidad

Las tres páginas elegidas describen qué hace MLflow. Estas notas cubren lo que hay que
saber para decidir cómo usarlo: dónde queda el registro, cuánto cuesta y qué no resuelve.

### Dónde vive el registro

MLflow separa lo que anota de lo que guarda. Sirve pensarlo como un cuaderno de laboratorio
y una bodega: en el cuaderno se anota qué se probó y qué salió, en la bodega se guarda lo
pesado, y el cuaderno solo apunta en qué estante está.

| Pieza | Qué guarda | Dónde puede vivir |
| :--- | :--- | :--- |
| Almacén de seguimiento (el cuaderno) | Parámetros, métricas, etiquetas, datos de cada ejecución y versiones del Model Registry | SQLite, PostgreSQL, MySQL o SQL Server |
| Almacén de artefactos (la bodega) | Modelos serializados, gráficos y cualquier archivo | Carpeta local o un bucket: S3, Azure Blob Storage, Google Cloud Storage |

- **No es cualquier base de datos**: son los cuatro motores SQL de la tabla.
- **SQLite es un archivo y sirve para una persona.** Con varios procesos o máquinas
  escribiendo a la vez se bloquea. Para concurrencia alta la documentación recomienda
  PostgreSQL.
- **En la nube** se levanta un servidor de MLflow (`mlflow server`) con PostgreSQL y un
  bucket. El código de entrenamiento no cambia: solo cambia la URI de seguimiento.
- **La URI decide dónde se escribe lo nuevo.** No traslada lo que ya estaba registrado en
  otro almacén.

Documentación: [Tracking Server](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/).

### Un registro, no una fuente de configuración

MLflow anota lo que se usó en cada entrenamiento. No es el lugar donde se define con qué se
va a entrenar: esa configuración vive en el código o en un archivo versionado con git.

Lo que sí se puede hacer con el registro, porque se consulta como cualquier tabla:

- **Leer un punto de partida.** Una ejecución etiquetada como `baseline` se busca con
  `mlflow.search_runs` y sus parámetros sirven para arrancar la siguiente búsqueda.
- **Tener un histórico por organización.** Una sola base con un experimento por problema o
  por modelo. Las ejecuciones solo son comparables dentro del mismo experimento, porque
  cada negocio tiene sus datos y sus métricas.
- **Usarlo como compuerta.** Un modelo nuevo se compara contra el que tiene el alias
  `champion` y solo recibe el alias si lo supera.

Lo que MLflow no hace:

- **No optimiza.** La búsqueda de hiperparámetros la hace `GridSearchCV`, Optuna u otra
  librería. MLflow registra cada intento.
- **No automatiza.** Programar reentrenamientos es trabajo de un orquestador o de un flujo
  de integración continua. MLflow es donde ese flujo deja constancia y consulta el estado.

### Cuánto cuesta registrar

El registro corre dentro del mismo proceso que entrena y usa CPU. No usa GPU ni lanza
procesos aparte; a lo sumo abre hilos dentro de ese proceso. Las métricas de sistema (uso
de CPU, GPU y memoria) son opcionales y solo leen contadores cada cierto intervalo.

Las métricas `training_*` del autologging no salen gratis: al terminar `fit`, MLflow llama a
`predict` sobre los datos de entrenamiento y calcula las métricas con ese resultado.

Medición con el pipeline `Ridge` de este taller (4,000 filas, almacén SQLite local):

| Caso | Tiempo por entrenamiento |
| :--- | :--- |
| Sin MLflow | 0.12 s |
| Autologging sin guardar el modelo (`log_models=False`) | 0.15 s |
| Autologging guardando el modelo | 1.1 s, y 17.6 s la primera vez |
| 200 llamadas a `log_metric`, una por una | 2.2 s en total |

- **Anotar parámetros y métricas es barato.** Lo caro es guardar el modelo: serializarlo,
  inferir su firma y, la primera vez, capturar las dependencias del entorno.
- **En proporción solo pesa con modelos pequeños.** En un entrenamiento de horas, un
  segundo no se nota.
- **Contra un servidor remoto, cada llamada es un viaje de red.** Conviene agrupar con
  `log_metrics`, registrar cada varios pasos o activar el registro asíncrono con
  `mlflow.config.enable_async_logging()`.

Al entrenar en la nube el costo tiene tres partes, y las dos últimas son las que conviene
presupuestar:

1. Segundos extra de cómputo en la máquina que entrena.
2. Almacenamiento de cada modelo guardado, que crece con cada ejecución.
3. El servidor de MLflow y su base de datos, encendidos aunque no se entrene.

Documentación: [System Metrics](https://mlflow.org/docs/latest/ml/tracking/system-metrics/).

### Guardar el modelo: lo caro y lo que habilita

El modelo guardado es la parte más cara del registro y también la que sostiene el
versionado y el despliegue: sin el artefacto no hay nada que registrar en el Model Registry
ni que servir.

La regla práctica es separar explorar de publicar:

- **Durante la búsqueda**, `mlflow.sklearn.autolog(log_models=False)`. Quedan parámetros y
  métricas de todas las combinaciones, sin un modelo por cada una.
- **Al terminar**, se guarda solo el ganador con `mlflow.sklearn.log_model` y se registra.
- `max_tuning_runs` limita además cuántas ejecuciones hijas crea `GridSearchCV`.

Borrar una ejecución desde la interfaz solo la marca como eliminada. El espacio se libera
al ejecutar `mlflow gc`.

### La huella de los datos

`mlflow.data.from_pandas` no guarda los datos. Guarda una ficha del conjunto: nombre,
esquema, número de filas, origen y una huella (`digest`), que es un hash corto como
`4168f798`. Se calcula con las primeras 10,000 filas, el total de filas y los nombres de
las columnas.

Para qué sirve si no versiona:

- **Saber si dos ejecuciones usaron los mismos datos.** Misma huella, comparación justa.
  Huella distinta, la diferencia de métricas puede venir de los datos y no del modelo.
- **Detectar que los datos cambiaron** entre un entrenamiento y el siguiente.
- **Filtrar ejecuciones por conjunto de datos** en la interfaz.

Para qué no sirve:

- **No permite recuperar los datos.** Solo se pueden volver a cargar si al crear el
  conjunto se indicó un origen accesible, como una URL o una ruta (`source=`). En este
  taller los datos se generan en memoria, así que el origen registrado es el código.
- **No distingue cambios más allá de la fila 10,000** si el total de filas no varía.

El versionado de datos se resuelve con otra herramienta (DVC, lakeFS, tablas con versiones)
y las dos se complementan: la huella dice qué datos se usaron y la otra herramienta permite
volver a ellos.

Documentación: [MLflow Dataset Tracking](https://mlflow.org/docs/latest/ml/dataset/).

### Acceso al servidor

Un servidor de MLflow no pide usuario ni contraseña por defecto. Quien alcance su dirección
puede leer y borrar experimentos, así que no se expone a internet sin configurarlo.

La autenticación se configura en el servicio, no en el código de entrenamiento:

- **En el servidor**: se arranca con `mlflow server --app-name basic-auth` y la variable
  `MLFLOW_AUTH_ADMIN_PASSWORD`, que define la contraseña del administrador en el primer
  arranque. Los usuarios y sus permisos quedan en una base de datos del propio servidor.
- **En el cliente**: las credenciales se pasan por las variables de entorno
  `MLFLOW_TRACKING_USERNAME` y `MLFLOW_TRACKING_PASSWORD`. El código no cambia.
- **Permisos**: se asignan por experimento y por modelo registrado. Quien crea uno queda
  como su administrador.

Documentación: [Basic HTTP Auth](https://mlflow.org/docs/latest/self-hosting/security/basic-http-auth/).

Aparte del registro propio, MLflow 3 envía telemetría de uso a sus desarrolladores y viene
activada por defecto. Se desactiva con la variable de entorno `MLFLOW_DISABLE_TELEMETRY=true`
o con `DO_NOT_TRACK=true`, que conviene fijar en entornos de cliente o con datos sensibles.

### Trasladar o respaldar el almacén

Respaldar y mover la base es trabajo de la política de datos del equipo, con las
herramientas del motor. Hay dos puntos que sí son propios de MLflow:

- **El esquema lo migra MLflow.** Al actualizar de versión se ejecuta `mlflow db upgrade`
  sobre la base.
- **La base guarda la ruta de los artefactos.** Cada experimento registra dónde está su
  bodega; en este taller es una ruta absoluta del equipo donde se ejecutó. Mover los
  artefactos sin actualizar esas rutas deja las ejecuciones apuntando a un lugar vacío.

Pasar de un motor a otro, por ejemplo de SQLite a PostgreSQL, no es un respaldo y
restauración: hay que exportar e importar las ejecuciones. Si el historial importa,
conviene elegir el motor antes de acumularlo.

## Dónde se usa cada una en este taller

| Funcionalidad | Notebook | Qué se hace |
| :--- | :--- | :--- |
| Experiment Tracking | [`01_mlflow-tracking-tutorial.ipynb`](../notebooks/01_mlflow-tracking-tutorial.ipynb) | Registro manual de parámetros, métricas, conjunto de datos, gráfico y modelo; ejecuciones padre e hijas; consulta con `search_runs`. |
| Autologging | [`02_mlflow-sklearn-pipeline.ipynb`](../notebooks/02_mlflow-sklearn-pipeline.ipynb) | `mlflow.sklearn.autolog()` sobre un `Pipeline` y sobre `GridSearchCV`. |
| Scikit-learn Integration | [`02_mlflow-sklearn-pipeline.ipynb`](../notebooks/02_mlflow-sklearn-pipeline.ipynb) | Registro del pipeline completo con firma y carga para predecir con datos crudos. |
| Model Evaluation | [`02_mlflow-sklearn-pipeline.ipynb`](../notebooks/02_mlflow-sklearn-pipeline.ipynb) | `mlflow.models.evaluate` con `model_type="regressor"` sobre el conjunto de prueba. |
| Model Registry | [`02_mlflow-sklearn-pipeline.ipynb`](../notebooks/02_mlflow-sklearn-pipeline.ipynb) | Versión registrada del pipeline y alias `champion`. |
