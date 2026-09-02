"""Logging con dos salidas: consola legible y archivo JSONL trazable"""

import json
import logging
from datetime import datetime

from core.config import LOG_LEVEL, PATH_STORAGE_LOG


class JsonlFormatter(logging.Formatter):
    """Una linea JSON por evento. Los kwargs extra viajan en 'extra'."""

    RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
        "message",
        "asctime",
    }

    def format(self, record):
        payload = {
            "ts": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = {k: v for k, v in record.__dict__.items() if k not in self.RESERVED}
        if extra:
            payload["extra"] = extra
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_logger(name, run_tag=None):
    """Devuelve un logger. run_tag nombra el archivo de la corrida."""
    PATH_STORAGE_LOG.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)-7s %(name)s | %(message)s"))
    logger.addHandler(console)

    tag = run_tag or name
    stamp = datetime.now().strftime("%Y%m%d")
    archivo = logging.FileHandler(
        PATH_STORAGE_LOG / f"{stamp}_{tag}.jsonl", encoding="utf-8"
    )
    archivo.setFormatter(JsonlFormatter())
    logger.addHandler(archivo)

    return logger