"""Taller de MLflow: datos sinteticos y pipeline de scikit-learn.

Uso:
    from mlflow_workshop import (
        generate_apple_sales_data, split_by_time,
        build_pipeline, regression_metrics,
    )
"""

from .pipeline import (
    DemandFeatures,
    build_pipeline,
    build_preprocessor,
    regression_metrics,
    split_by_time,
)
from .synthetic_data import (
    COMPONENT_COLUMNS,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    generate_apple_sales_data,
)

__version__ = "0.1.0"

__all__ = [
    "COMPONENT_COLUMNS",
    "FEATURE_COLUMNS",
    "TARGET_COLUMN",
    "DemandFeatures",
    "build_pipeline",
    "build_preprocessor",
    "generate_apple_sales_data",
    "regression_metrics",
    "split_by_time",
]
