"""
Hydroma Scientific Models Library
=================================

Proprietary scientific models for precision agriculture and landscape management.

Models:
- EWSI: Multi-source Water Stress Index
- HYRUE: Radiation Use Efficiency Model
- ECSI: Carbon Sequestration Index
- HDVI: Drought Vulnerability Index
- EPIA: Precision Irrigation Advisor
- HPheno: Phenology Detection
- ESRI: Salinity Risk Index
- HLHS: Landscape Health Score

Author: EcoNojin Scientific Council
License: Proprietary

Note: submodules are resolved lazily via ``__getattr__`` to avoid re-entrant
import chains that made deep imports fail depending on import order.
"""

from __future__ import annotations

import importlib
from typing import Any

#: Public name -> submodule that defines it.
_EXPORTS: dict[str, str] = {
    "ScientificModel": "base",
    "ValidationResult": "base",
    "ECSI": "ecsi",
    "EPIA": "epia",
    "ESRI": "esri",
    "EWSI": "ewsi",
    "HDVI": "hdvi",
    "HLHS": "hlhs",
    "HPheno": "hpheno",
    "HYRUE": "hyrue",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Resolve a public name by importing its defining submodule on demand."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))
