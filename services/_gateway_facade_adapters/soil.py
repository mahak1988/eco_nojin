"""Soil and land-surface engine bindings for the gateway facade.

Owns the facade's engine imports under ``engine.hydroma.models`` (the
scientific index models and the validation corpus runner) plus the
land-surface analysis modules ``engine.hydroma.analyses.
topography_analysis`` and ``engine.hydroma.land.erosion_risk``.

Every module name imported here was previously imported directly by
``services/_gateway_facade.py``; nothing here re-implements computation. The
two wrappers whose engine import was function-local there stay function-local
here, so the facade still imports cleanly when the optional corpus dependency
is absent.
"""

from __future__ import annotations

from typing import Any

from engine.hydroma.analyses.topography_analysis import (
    AnalysisType,
    TopographyAnalyzer,
    TopographyInput,
    TopographyOutput,
)
from engine.hydroma.models import (
    ECSI,
    EPIA,
    ESRI,
    EWSI,
    HDVI,
    HLHS,
    HYRUE,
    HPheno,
)
from engine.hydroma.models.hlhs import LandscapeMetrics

__all__ = [
    "AnalysisType",
    "ECSI",
    "EPIA",
    "ESRI",
    "EWSI",
    "HDVI",
    "HLHS",
    "HYRUE",
    "HPheno",
    "LandscapeMetric",
    "LandscapeMetrics",
    "TopographyAnalyzer",
    "TopographyInput",
    "TopographyOutput",
    "estimate_rainfall_erosivity",
    "run_validation_summary",
]


#: ``hydroma_indices.py`` reads ``LandscapeMetrics`` in its body; the singular
#: spelling resolves to the same dataclass so either name works at a call site.
LandscapeMetric = LandscapeMetrics


def estimate_rainfall_erosivity(
    precipitation_mm: float,
    region: str = "temperate",
) -> float:
    """Estimate rainfall erosivity (R-factor) from annual precipitation.

    Uses the Renard & Freimund (1994) relation: R = a * P^b,
    with coefficients by climate region.
    """
    from engine.hydroma.land.erosion_risk import estimate_r_factor as _estimate_r_factor

    r_factor: float = _estimate_r_factor(precipitation_mm, region)
    return r_factor


def run_validation_summary() -> dict[str, Any]:
    """Machine evidence: the validation-corpus verdicts (read-only reporting).

    AR-08 (Fail Closed) and honesty contract 4 ("nothing green without a run")
    require that anything reported as ``passed`` has actually executed. The
    corpus runner is the engine's machine-evidence source; it is exposed here,
    through the sanctioned bridge, so that no service has to import engine
    internals directly (AR-13).

    The import is inside the function so this module keeps importing when the
    optional corpus dependencies are absent; the caller sees the ImportError.
    """
    from engine.hydroma.models.validation.runner import machine_summary

    return machine_summary()
