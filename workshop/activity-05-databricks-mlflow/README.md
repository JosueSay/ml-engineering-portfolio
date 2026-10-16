# Actividad 5: Adaptación de Pipeline de scikit-learn con MLflow en Databricks

**Grupo 7:** Carlos Valladares, Gustavo Cruz, José Gramajo, Josué Say y Mathew Cordero  
**Entregable individual de código Python:** Josué Say  
**Repositorio GitHub:** <https://github.com/JosueSay/ml-engineering-portfolio/tree/main/workshop/activity-05-databricks-mlflow>

---

## 1. Descripción de la actividad

Esta actividad consiste en la adaptación de un **Pipeline de scikit-learn** para incorporar las funcionalidades de ciclo de vida de Machine Learning que provee **MLflow**, diseñado para interactuar con la plataforma de **Databricks** (o ejecutarse en modo local con fallback transparente).

### Requerimientos cubiertos por este código:
1. **Archivo de Python independiente (`src/pipeline.py`):** Ejecutable desde terminal o como tarea remota, sin requerir una interfaz gráfica de notebook para operar.
2. **Uso de funcionalidades de MLflow:**
   - **Experiments y Runs:** Trazabilidad, nombrado y registro de metadatos/tags de auditoría.
   - **Tracking de Parámetros y Métricas:** Hiperparámetros del estimador y métricas en conjuntos de entrenamiento y prueba ($RMSE$, $MAE$, $R^2$).
   - **Model Registry & Signature:** Inferencia de contratos de datos (`infer_signature`), empaquetado del pipeline completo y versionado en el registro de modelos.
   - **Artefactos:** Generación y registro automático de gráficos de dispersión y análisis de residuos.
3. **Integración con Databricks:**
   - Autenticación remota mediante `DATABRICKS_HOST` y `DATABRICKS_TOKEN`.
   - Registro de experimentos en el workspace de Databricks de Grupo 7 (`https://dbc-5ade37d5-76a7.cloud.databricks.com`).

---

## 2. Alineación con las etapas de CRISP-DM

| Etapa CRISP-DM | Implementación en este Pipeline | Funcionalidad de MLflow / Databricks |
| :--- | :--- | :--- |
| **Preparación de Datos** | Partición temporal cronológica (`split_temporal_data`) y derivación de variables de fecha y mercado (`DemandFeatures`). | Metadatos de features y tamaño de muestra registrados como parámetros. |
| **Modelado** | Pipeline compuesto con `ColumnTransformer` (`StandardScaler` numérico, `OneHotEncoder` categórico y `passthrough` binario) conectado al estimador `Ridge`. | Registro de hiperparámetros (`alpha`, `model_type`, `pipeline_steps`). |
| **Evaluación** | Cálculo de $RMSE$, $MAE$ y $R^2$ tanto en entrenamiento como en prueba para diagnosticar sobreajuste o subajuste. | `mlflow.log_metrics` y gráfico de residuos guardado con `mlflow.log_figure`. |
| **Despliegue** | Serialización del pipeline completo (incluyendo transformadores y preprocesamiento) con firma estricta. | `mlflow.sklearn.log_model` y registro en el **Databricks Model Registry** (`registered_model_name`). |

---

## 3. Estructura del proyecto

```text
activity-05-databricks-mlflow/
├── pipeline_mlflow.ipynb     # Notebook por etapas: datos, entrenamiento, evaluación y MLflow
├── src/
│   ├── __init__.py           # Exporta funciones publicas
│   ├── data.py               # Generador sintetico de demanda y factores economicos
│   └── pipeline.py           # Pipeline scikit-learn con integracion a MLflow y Databricks
├── .env.example              # Plantilla para variables de conexion a Databricks
├── pyproject.toml            # Especificacion de dependencias y empaquetado
└── README.md                 # Documentacion tecnica e instrucciones de ejecucion
```

---

## 4. Instalación

Se requiere Python 3.11+.

### Opción A: Con `uv` (Recomendado)

```bash
cd workshop/activity-05-databricks-mlflow
uv sync
```

### Opción B: Con `pip` y entorno virtual

```bash
cd workshop/activity-05-databricks-mlflow
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -e .
```

---

## 5. Ejecución

### Jupyter Notebook por etapas

Abre [`pipeline_mlflow.ipynb`](pipeline_mlflow.ipynb), ubicado en esta misma carpeta:

```bash
uv sync --extra notebook
uv run --extra notebook jupyter lab pipeline_mlflow.ipynb
```

También puedes abrirlo en VS Code y seleccionar el intérprete `.venv/bin/python`
de esta actividad como kernel. Ejecuta las celdas en orden.

El notebook incluye las salidas guardadas de una ejecución local: tablas, diagrama
del pipeline, métricas, gráficos y predicciones. Se pueden ver al abrirlo sin
ejecutarlo de nuevo; los identificadores de MLflow corresponden al almacén local
de esa ejecución.

El notebook separa configuración, generación de datos, partición temporal,
entrenamiento, evaluación, registro en MLflow, consulta de runs y carga del modelo
para inferencia. Reutiliza las funciones de `src/` y muestra explícitamente el
registro de parámetros, métricas, artefactos y el pipeline completo con firma.
Incluye una comprobación de que las predicciones coinciden tras recuperar el modelo.

El modo predeterminado utiliza SQLite local y el experimento
`activity-05-demand-notebook`. Para Databricks, configura las credenciales fuera
del notebook, define `MLFLOW_EXPERIMENT_NAME` con la ruta del experimento y cambia
`USE_DATABRICKS = True` en la sección 2. El Model Registry es opcional y se activa
en la última celda; para Unity Catalog configura un nombre `catalog.schema.model`.

### Modo A: Ejecución Local (Prueba rápida offline)

Si no se configuran credenciales de Databricks, el script utiliza automáticamente un almacén local SQLite (`mlflow.db`) en la carpeta del proyecto:

```bash
uv run python src/pipeline.py --alpha 1.0 --rows 3000
```

Para visualizar la interfaz local de MLflow:

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```
Abrir en el navegador: <http://127.0.0.1:5000>.

---

### Modo B: Conexión Remota con Databricks

Para enviar los experimentos, métricas y modelos directamente al workspace de Databricks:

1. **Obtener Token de Databricks:**
   - En el workspace de Databricks (`https://dbc-5ade37d5-76a7.cloud.databricks.com`), ir a **User Settings** $\rightarrow$ **Developer** $\rightarrow$ **Access tokens** $\rightarrow$ **Generate new token**.

2. **Configurar las variables de entorno:**
   ```bash
   export DATABRICKS_HOST="https://dbc-5ade37d5-76a7.cloud.databricks.com"
   export DATABRICKS_TOKEN="dapi_tu_token_aqui"
   export DATABRICKS_USER="josuesay770@gmail.com"
   ```

3. **Ejecutar el pipeline registrando en Databricks:**
   ```bash
   uv run python src/pipeline.py --databricks --alpha 1.0 --register
   ```

4. **Verificación en Databricks:**
   - Ir a la pestaña **Experiments** en el workspace de Databricks: se observará la corrida con sus tags de `Grupo 7`, métricas de train/test, artefactos visuales y el modelo registrado en el catálogo.

---

## 6. Enlaces de entrega

- **Enlace al código del pipeline en GitHub (para el PDF):**  
  [`src/pipeline.py`](https://github.com/JosueSay/ml-engineering-portfolio/blob/main/workshop/activity-05-databricks-mlflow/src/pipeline.py)
- **Directorio de la Actividad 5 en GitHub:**  
  [workshop/activity-05-databricks-mlflow](https://github.com/JosueSay/ml-engineering-portfolio/tree/main/workshop/activity-05-databricks-mlflow)
- **Experimento en vivo en el Workspace de Databricks:**  
  [Experimento MLflow en Databricks (ID: 2671168015268648)](https://dbc-5ade37d5-76a7.cloud.databricks.com/ml/experiments/2671168015268648)
- **Ejecución de referencia en Databricks:**  
  [Run `ridge_alpha_1.0_databricks` (ID: 6b30b3596c3b4f21b359fc06c45d4221)](https://dbc-5ade37d5-76a7.cloud.databricks.com/ml/experiments/2671168015268648/runs/6b30b3596c3b4f21b359fc06c45d4221)

