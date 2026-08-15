# Actividad 3: Linear Regression con Calibración de Hiperparámetros

Pipeline de Machine Learning implementado con **scikit-learn** y **CRISP-DM** como referencia metodológica.

## Descripción

Implementación completa de un modelo de regresión lineal con:
- Preprocesamiento de datos (limpieza, transformación)
- Calibración automática de hiperparámetros usando GridSearchCV
- Evaluación del modelo con métricas estandarizadas
- Análisis de overfitting y coeficientes interpretables

## Estructura

```
actividad_3/
├── notebooks/
│   └── actividad3.ipynb          # Notebook principal con análisis completo
├── src/
│   └── ml_pipeline/
│       └── __init__.py           # Paquete Python
├── requirements.txt              # Dependencias del proyecto
├── pyproject.toml               # Configuración de compilación
└── README.md                    # Este archivo
```

## Instalación

### Opción 1: Con pip (recomendado)
```bash
pip install -e .
```

### Opción 2: Instalar dependencias directamente
```bash
pip install -r requirements.txt
```

## Uso

### Abrir Notebook
```bash
jupyter notebook notebooks/actividad3.ipynb
```

### Ejecutar Análisis Completo
1. Abrir `notebooks/actividad3.ipynb` en Jupyter
2. Ejecutar todas las celdas (Kernel > Run All)
3. Los resultados se mostrarán en tiempo real

## Funciones Disponibles

### Funciones de Pipeline
- `crear_pipeline_modelo(preprocessor, modelo_clase, **params)` - Crear pipeline parametrizable
- `calibrar_modelo(pipeline, X_train, y_train, param_grid, cv)` - GridSearchCV automático
- `evaluar_modelo(modelo, X_train, y_train, X_test, y_test)` - Evaluar con múltiples métricas

### Funciones de Análisis
- `analizar_overfitting(metricas)` - Detectar overfitting automáticamente
- `mostrar_coeficientes(modelo)` - Mostrar coeficientes ordenados por magnitud
- `validacion_cruzada(modelo, X_train, y_train, cv)` - Validación cruzada k-fold

## Metodología CRISP-DM

Fases cubiertas:
- **Business Understanding** ✓ - Predicción de límite de crédito
- **Data Understanding** ✓ - Análisis de 660 registros, 7 variables
- **Data Preparation** ✓ - Limpieza, filtrado, transformación
- **Modeling** ✓ - Linear Regression con GridSearchCV
- **Evaluation** ✓ - Métricas R², MAE, RMSE, análisis de residuos
- **Deployment** - Empaquetado para compartir

## Resultados Principales

| Métrica | Valor |
|---------|-------|
| R² Test | 0.5664 |
| R² Train | 0.6271 |
| MAE Test | $17,968.33 |
| RMSE Test | $24,358.73 |
| Overfitting | Moderado (0.0607) |

## Cambiar Modelo

Para probar con otro algoritmo (Ridge, Lasso, etc):

```python
# En el notebook, cambiar esta línea:
lr_pipeline = crear_pipeline_modelo(preprocessor)

# Por:
from sklearn.linear_model import Ridge
lr_pipeline = crear_pipeline_modelo(preprocessor, Ridge)
```

## Requiere Python

- Python >= 3.8
- scikit-learn >= 1.0
- pandas >= 1.3.0
- numpy >= 1.20.0

## Autor

Machine Learning Engineering - Universidad Valle de Guatemala

## Licencia

MIT License
