"""Carga de configuracion. Rutas ancladas a la raiz del repo, no al cwd.

Las anotaciones no son decorativas: yaml.safe_load devuelve Any, asi que sin
ellas todo lo que sale de config.yml es un agujero para el type checker y un
str puede pasar por donde se espera una coleccion sin que nadie se queje.
"""

from pathlib import Path

import yaml

ROOT: Path = Path(__file__).resolve().parent.parent
CONFIG_PATH: Path = ROOT / "config.yml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


def _abs(path_str: str) -> Path:
    return (ROOT / path_str).resolve()


# Modelos
PATH_STORAGE_MODEL: Path = _abs(config["models"]["path_storage_models"])
MODEL_HFA: str = config["models"]["model_hfa"]
LINK_HFA: str = config["models"]["link_hfa"]
# str | None a proposito: si falta en el yml, quien lo use debe decidir que
# hacer. Ver la validacion en download_models.py.
REVISION_HFA: str | None = config["models"].get("revision_hfa")

# model_id -> revision fijada, para que el adaptador no tenga que recibirla
REVISIONS: dict[str, str | None] = {MODEL_HFA: REVISION_HFA}

# Data
PATH_STORAGE_DATA: Path = _abs(config["data"]["path_storage_data"])
PATH_STORAGE_DATA_RAW: Path = _abs(config["data"]["path_raw_data"])

# Logging. Los nombres son los que consume core/logging_setup.py.
PATH_STORAGE_LOG: Path = _abs(config["logging"]["path_storage_log"])
LOG_LEVEL: str = config["logging"]["level"]

# Output
PATH_STORAGE_OUTPUT: Path = _abs(config["output"]["path_storage_output"])
