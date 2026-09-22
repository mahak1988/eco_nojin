"""Shared helpers for the HyDroMa engine API routers.

Converts numpy outputs to JSON-safe values and turns raw JSON parameter
dicts into validated model keyword arguments. Used by the indices and soil
routers so both share one behaviour contract.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any

import numpy as np


def jsonable(value: Any) -> Any:
    """Recursively convert numpy scalars/arrays into JSON-safe Python types."""
    if isinstance(value, np.ndarray):
        return [jsonable(v) for v in value.tolist()]
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return value


def coerce(value: Any, kind: str) -> Any:
    """Coerce a raw JSON value to the type expected by a model param."""
    if kind == "float":
        return float(value)
    if kind == "int":
        return int(value)
    if kind in ("str", "select"):
        return str(value)
    if kind == "list_float":
        if isinstance(value, str):
            parts = [p for p in value.replace(";", ",").split(",") if p.strip() != ""]
            return np.array([float(p) for p in parts], dtype=float)
        return np.array([float(v) for v in value], dtype=float)
    if kind == "list_str":
        if isinstance(value, str):
            return [p.strip() for p in value.split(",") if p.strip() != ""]
        return [str(v) for v in value]
    raise ValueError(f"unknown param kind: {kind}")


def build_kwargs(spec: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    """Turn a raw params dict into validated keyword arguments for a model.

    Params marked ``optional`` and left empty are omitted so the engine can
    apply its own default behaviour instead of failing.
    """
    kwargs: dict[str, Any] = {}
    for p in spec["params"]:
        name = p["name"]
        raw = params.get(name)
        if raw is None or raw == "":
            if p.get("optional"):
                continue
            raw = p.get("default")
        if raw is None:
            raise ValueError(f"missing required parameter: {name}")
        kwargs[name] = coerce(raw, p["kind"])
    return kwargs
