"""
Recursively converts numpy/pandas objects (numpy.float64, numpy.int64,
numpy.ndarray, pandas.Timestamp, NaN/Inf, etc.) into plain, JSON-serializable
Python types. Plotly figures and pandas DataFrame summaries both leak these
types by default, and FastAPI's default encoder can't serialize them —
this is the single choke point that fixes that for every chart/table
returned by the API.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def to_jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, bool)):
        return obj

    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj

    if isinstance(obj, int):
        return obj

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        value = float(obj)
        return None if (math.isnan(value) or math.isinf(value)) else value

    if isinstance(obj, np.ndarray):
        return [to_jsonable(x) for x in obj.tolist()]

    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(x) for x in obj]

    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}

    # pandas Timestamp / Period / numpy datetime64, without importing pandas
    # unconditionally at module import time.
    type_name = type(obj).__name__
    if type_name in ("Timestamp", "Period", "datetime64"):
        try:
            return obj.isoformat()
        except Exception:  # noqa: BLE001
            return str(obj)

    # Anything else with a numpy/pandas .item() (e.g. 0-d arrays, scalars)
    if hasattr(obj, "item") and callable(getattr(obj, "item")):
        try:
            return to_jsonable(obj.item())
        except Exception:  # noqa: BLE001
            pass

    # Last resort: keep JSON-safe basic types as-is, stringify anything unknown
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    return str(obj)
