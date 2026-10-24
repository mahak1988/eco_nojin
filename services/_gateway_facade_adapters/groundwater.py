"""Groundwater and surface-water engine bindings for the gateway facade.

Owns the facade's engine imports from ``engine.hydroma.models.runoff_model``
(the runoff calculators the analyses router constructs) and
``engine.hydroma.water.quality`` (the field / mobile water-quality
classification).

Every module name imported here was previously imported directly by
``services/_gateway_facade.py``; nothing here re-implements computation.
"""

from __future__ import annotations

from engine.hydroma.models.runoff_model import (
    RunoffCalculator,
    RunoffInput,
)
from engine.hydroma.water.quality import assess_water_quality

__all__ = [
    "RunoffCalculator",
    "RunoffInput",
    "assess_water_quality",
]
