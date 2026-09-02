# Actividad 3: Linear Regression con Calibración de Hiperparámetros

Pipeline de Machine Learning implementado con **scikit-learn** y **CRISP-DM** como referencia metodológica.

## Descripción

Implementación completa de un modelo de regresión lineal con:

- Preprocesamiento de datos (limpieza, transformación)
- Calibración automática de hiperparámetros usando GridSearchCV
- Evaluación del modelo con métricas estandarizadas
- Análisis de overfitting y coeficientes interpretables

El pipeline vive en el paquete `ml_pipeline`, instalable y compartible con el equipo. El notebook lo importa en vez de definir las funciones inline.

## Estructura

```
activity-03-hyperparameter-tuning/
├── notebooks/
│   └── hyperparameter-tuning.ipynb          # Notebook principal con el análisis
├── src/
│   └── ml_pipeline/
│       ├── __init__.py           # Exporta los símbolos públicos
│       ├── transformers.py       # FeatureExtractor, RowFilter
│       ├── pipeline.py           # Construcción y calibración del pipeline
│       └── analysis.py           # Métricas, overfitting, coeficientes, CV
├── requirements.txt              # Dependencias del proyecto
├── pyproject.toml                # Configuración del paquete
└── README.md                     # Este archivo
```

## Instalación

El notebook **requiere** que el paquete esté instalado; sin este paso el import
`from ml_pipeline import ...` falla con `ModuleNotFoundError`.

### Linux / macOS

```bash
git clone https://github.com/JosueSay/ml-engineering-portfolio.git
cd ml-engineering-portfolio/workshop/activity-03-hyperparameter-tuning

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
```

### Windows (PowerShell)

```powershell
git clone https://github.com/JosueSay/ml-engineering-portfolio.git
cd "ml-engineering-portfolio\workshop\activity-03-hyperparameter-tuning"

python -m venv .venv
.venv\Scripts\activate

pip install -e .
```

La instalación termina con:

```
Successfully installed activity03-linear-regression-0.1.0
```

### Verificar la instalación

```bash
pip show activity03-linear-regression
python -c "import ml_pipeline; print(ml_pipeline.__version__)"
```

## Uso

### Ejecutar el notebook

```bash
jupyter notebook notebooks/hyperparameter-tuning.ipynb
```

Dentro de Jupyter: **Kernel > Restart & Run All**.

Si ya tenías el notebook abierto cuando instalaste el paquete, hay que reiniciar
el kernel para que tome el módulo recién instalado.

### Usar el paquete desde tu propio código

```python
from sklearn.model_selection import train_test_split
from ml_pipeline import (
    FeatureExtractor, RowFilter,
    crear_preprocesador, crear_pipeline_modelo, calibrar_modelo, evaluar_modelo,
    analizar_overfitting, mostrar_coeficientes, validacion_cruzada,
)

preprocessor = crear_preprocesador()
pipeline = crear_pipeline_modelo(preprocessor)

param_grid = {
    'modelo__fit_intercept': [True, False],
    'modelo__positive': [True, False],
}
grid_search = calibrar_modelo(pipeline, X_train, y_train, param_grid, cv=5)

best_model = grid_search.best_estimator_
metricas = evaluar_modelo(best_model, X_train, y_train, X_test, y_test)

analizar_overfitting(metricas)
mostrar_coeficientes(best_model)
validacion_cruzada(best_model, X_train, y_train)
```

## API del paquete

### `ml_pipeline.transformers`

| Objeto | Descripción |
| ------ | ----------- |
| `FeatureExtractor(columns_to_drop)` | Descarta columnas del dataframe crudo |
| `RowFilter(max_null_ratio, numeric_bounds)` | Elimina duplicados, filas con exceso de nulos y valores fuera de rango |

### `ml_pipeline.pipeline`

| Función | Descripción |
| ------- | ----------- |
| `crear_preprocesador()` | ColumnTransformer con ramas numérica y categórica |
| `crear_pipeline_modelo(preprocessor, modelo_clase, **params)` | Pipeline parametrizable: preprocesamiento + modelo |
| `calibrar_modelo(pipeline, X_train, y_train, param_grid, cv)` | GridSearchCV sobre el pipeline |
| `evaluar_modelo(modelo, X_train, y_train, X_test, y_test)` | Retorna dict `{train, test}` con `r2`, `mae`, `rmse` |

### `ml_pipeline.analysis`

| Función | Descripción |
| ------- | ----------- |
| `analizar_overfitting(metricas)` | Compara R_2 train vs test y reporta diagnóstico |
| `mostrar_coeficientes(modelo)` | Coeficientes ordenados por magnitud |
| `validacion_cruzada(modelo, X_train, y_train, cv)` | Validación cruzada k-fold |

## Cambiar de modelo

`crear_pipeline_modelo` acepta cualquier estimador de sklearn:

```python
from sklearn.linear_model import Ridge, Lasso

pipeline = crear_pipeline_modelo(preprocessor, Ridge, alpha=1.0)
pipeline = crear_pipeline_modelo(preprocessor, Lasso, alpha=0.1)
```

## Metodología CRISP-DM

| Fase | Estado | Detalle |
| ---- | ------ | ------- |
| Business Understanding | [OK] | Predicción de límite de crédito por cliente |
| Data Understanding | [OK] | 660 registros, 7 variables |
| Data Preparation | [OK] | Extracción, filtrado, preprocesamiento |
| Modeling | [OK] | Linear Regression calibrado con GridSearchCV |
| Evaluation | [OK] | R_2, MAE, RMSE, overfitting, validación cruzada |
| Deployment | [OK] | Paquete instalable con `pip install -e .` |

## Resultados

Mejores hiperparámetros: `fit_intercept=True`, `positive=False`

| Métrica | Train | Test |
| ------- | ----- | ---- |
| R_2 | 0.6271 | 0.5664 |
| MAE | — | $17,968.33 |
| RMSE | — | $24,358.73 |

Validación cruzada (5 folds): R_2 medio 0.6056, desviación estándar 0.0540.

Diferencia R_2 train-test de 0.0607: overfitting moderado, dentro de lo aceptable.

### Coeficientes

| Variable | Coeficiente |
| -------- | ----------- |
| Intercepto (beta_0) | 35,275.53 |
| Total_visits_online | +18,309.26 |
| Total_Credit_Cards | +14,782.76 |
| Total_calls_made | -11,062.22 |
| Total_visits_bank | -4,108.98 |

## Requisitos

- Python >= 3.8
- scikit-learn >= 1.0
- pandas >= 1.3.0
- numpy >= 1.20.0
- jupyter >= 1.0.0

## Autor

Machine Learning Engineering - Universidad del Valle de Guatemala
