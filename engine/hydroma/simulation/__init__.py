"""Simulation module: integrated model chain for Eco Nojin.

Contains inter-model data contracts, scenario matrices, model runners
(AquaCrop-OSPy, RothC, RUSLE) and the orchestrator that executes the
chain with explicit provenance labels (data_source="simulated" + model
name/version) — never presenting model output as measured field data.

Note: submodules are resolved lazily via ``__getattr__``.  Eagerly importing
them here created a re-entrant import chain that made
``import engine.hydroma.simulation.<module>`` fail depending on import order.
"""

from __future__ import annotations

import importlib
from typing import Any

#: Public name -> submodule that defines it.
_EXPORTS: dict[str, str] = {
    "AquacropOutput": "contracts",
    "ChainInputs": "contracts",
    "ChainResult": "contracts",
    "MonthClimate": "contracts",
    "RothcOutput": "contracts",
    "RusleOutput": "contracts",
    "ScenarioParams": "contracts",
    "run_chain": "orchestrator",
    "SCENARIOS": "scenarios",
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
