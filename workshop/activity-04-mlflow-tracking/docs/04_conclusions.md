# Conclusiones del taller

Documentación oficial completa: [MLflow para Machine Learning](https://mlflow.org/docs/latest/ml/).

## Qué deja el ejercicio

- **MLflow no entrena mejor: deja constancia de lo que se entrenó.** No cambió ningún
  modelo del taller. Lo que cambió es que cada resultado quedó atado a su configuración, a
  sus datos y a su artefacto, y se puede volver a él sin depender de la memoria de nadie.
- **El autologging cubre lo repetitivo, pero no lo que importa decidir.** Con una línea
  quedaron registrados los 37 parámetros del pipeline y las métricas de entrenamiento. Las
  métricas de prueba, el gráfico y la firma del modelo hubo que registrarlos a mano, porque
  dependen de decisiones que la herramienta no puede adivinar. Los dos modos se usan juntos.
- **Registrar el pipeline, no el modelo.** Guardar solo el estimador obliga a repetir el
  preprocesamiento al usarlo, y ahí es donde entrenamiento y uso terminan haciendo cosas
  distintas. El pipeline registrado recibe datos crudos, con la fecha sin procesar, y
  devuelve la predicción.
- **Comparar ejecuciones sirve para cuestionar el método, no solo para elegir
  hiperparámetros.** El hallazgo más útil del taller salió de dos ejecuciones que solo
  diferían en la partición: con la aleatoria del tutorial el bosque aleatorio daba
  $R^2 = 0.77$, con la temporal $R^2 = 0.42$ y un sesgo de 176 unidades. Sin las dos
  ejecuciones lado a lado, el primer número habría pasado por bueno.
- **Un tutorial también se revisa.** El generador de datos del tutorial no se ejecuta con
  pandas 3 y su estacionalidad vale cero por un error de fórmula. Seguir los pasos sin
  comprobar qué producen habría dado un modelo entrenado sobre datos que no eran lo que la
  documentación decía.
- **La integración tiene fricción real.** MLflow 3 serializa los modelos de scikit-learn con
  `skops`, que rechaza los tipos que no conoce. Un bosque aleatorio y un transformador
  propio exigen declararse en `skops_trusted_types`, y un atributo aprendido de tipo
  `pandas.Timestamp` hubo que guardarlo como texto. Es un costo razonable a cambio de no
  ejecutar código arbitrario al cargar un modelo, pero conviene saberlo antes de diseñar los
  transformadores.

## Posibles usos en proyectos propios y profesionales

### Caso de estudio 01: precios de combustible

El caso [`cs1`](../../../case-studies/cs1/) ya resuelve a mano lo que MLflow ofrece. Su
módulo de entrenamiento calcula una huella del conjunto de datos, escribe un manifiesto con
los hiperparámetros elegidos y guarda cada modelo como `xgboost_{combustible}_h{horizonte}.joblib`.

| Lo que hoy hace el código propio | Con MLflow |
| :--- | :--- |
| Manifiesto de entrenamientos | Experiment Tracking: una ejecución por combustible y horizonte |
| Huella del conjunto de datos | `mlflow.data.from_pandas` y `mlflow.log_input` |
| Búsqueda con `RandomizedSearchCV` y `TimeSeriesSplit` | Autologging: ejecución padre con una hija por combinación |
| Nombre de archivo como identidad del modelo | Model Registry: un modelo registrado por combustible y horizonte, con versiones |
| Qué modelo sirve la API | Alias `champion`, que se mueve sin tocar el código de la API |

El beneficio concreto es comparar horizontes y combustibles en una sola tabla, y poder
volver a una versión anterior del modelo cambiando un alias en lugar de un archivo.

### Caso de estudio 02: sistema de recompensas

La propuesta de ML del caso [`reward-system`](../../../case-studies/reward-system/) fija dos
reglas: cada modelo compite contra la alternativa sin modelo, y el umbral de aceptación se
decide antes de entrenar. Las dos se pueden hacer cumplir con MLflow en vez de dejarlas
como intención: la referencia sin modelo se registra como una ejecución más del mismo
experimento, y Model Evaluation permite declarar umbrales de validación (`MetricThreshold`
con `mlflow.validate_evaluation_results`) que el modelo debe superar antes de registrarse.

### Talleres del curso

En la actividad 03 los resultados de `GridSearchCV` están escritos en el `README`, y nada
los ata a la ejecución que los produjo. Con autologging esa tabla sale de `cv_results.csv`,
que queda guardado junto a la ejecución, y el documento se puede generar a partir de lo
registrado.

### Uso profesional y en una startup

- **Equipo pequeño sin infraestructura**: el almacén local en SQLite no necesita servidor.
  Se empieza en un portátil y, cuando hace falta compartir, se cambia la URI de seguimiento
  sin tocar el código de entrenamiento.
- **Trazabilidad ante un cliente o una auditoría**: poder responder con qué datos, qué
  código y qué parámetros se entrenó el modelo que está en producción.
- **Relevo entre personas**: el historial de experimentos sustituye a las hojas de cálculo y
  a los cuadernos sueltos. Quien llega ve qué se probó y qué se descartó.
- **Despliegue controlado**: el alias separa entrenar de publicar. Un modelo nuevo se
  registra, se evalúa y solo entonces recibe el alias que consume el servicio.

## Límites

- MLflow registra lo que se le da. Una métrica mal calculada o una partición que filtra el
  objetivo quedan registradas con la misma prolijidad que una correcta.
- El almacén local no resuelve el trabajo en equipo: la base y los artefactos viven en una
  máquina. Compartirlos exige un servidor de seguimiento y un almacén de artefactos.
- No sustituye a CRISP-DM ni al versionado de código y de datos. Es transversal a las fases
  de modelado, evaluación y despliegue.
