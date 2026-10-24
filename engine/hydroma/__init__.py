"""HyDroMa engine — scientific computation core for Eco Nojin.

Public API
----------
- ``models.results``: Pydantic result models for engine analyses
- ``config.settings``: engine configuration

Note: the result models are imported lazily.  Importing them eagerly here
created a re-entrant import (``engine.hydroma.models`` while
``engine.hydroma`` was still initialising), which made
``import engine.hydroma.<anything>`` fail depending on import order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from engine.hydroma.models.results import (
        ClimateAnalysisResult,
        GroundwaterAnalysisResult,
        SoilAnalysisResult,
        WatershedAnalysisResult,
    )

__all__ = [
    "ClimateAnalysisResult",
    "GroundwaterAnalysisResult",
    "SoilAnalysisResult",
    "WatershedAnalysisResult",
]


def __getattr__(name: str) -> Any:
    """Resolve the public result models lazily on first attribute access."""
    if name in __all__:
        from engine.hydroma.models import results

        return getattr(results, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
