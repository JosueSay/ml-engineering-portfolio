"""Escritura de JSON tolerante a tipos de numpy y pandas.

pandas devuelve int64/float64/bool_, que json no sabe serializar. Este helper
los convierte en su equivalente de Python.
"""

import json

import numpy as np


def _json_safe(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def dump_json(payload, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=_json_safe)
    return ruta