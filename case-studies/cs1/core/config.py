"""Carga de configuracion. Rutas ancladas a la raiz del repo, no al cwd."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


def _abs(path_str):
    return (ROOT / path_str).resolve()


# Modelos
PATH_STORAGE_MODEL = _abs(config["models"]["path_storage_model"])

# Data
PATH_STORAGE_DATA = _abs(config["data"]["path_storage_data"])
PATH_STORAGE_DATA_RAW = _abs(config["data"]["path_storage_data_raw"])

# Loggin
PATH_STORAGE_LOGS = _abs(config["logging"]["path_storage_logs"])

# Output
PATH_STORAGE_OUTPUT = _abs(config["output"]["path_storage_output"])