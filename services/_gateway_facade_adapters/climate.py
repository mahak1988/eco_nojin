"""Climate, crop-water and simulation engine bindings for the gateway facade.

Owns the facade's engine imports from ``engine.hydroma.calculations.
crop_water_req_calc`` (the crop water requirement calculator) and the
``engine.hydroma.simulation`` chain (calibration kernels, the run contracts and
the orchestrator the simulation router drives directly).

Every module name imported here was previously imported directly by
``services/_gateway_facade.py``; nothing here re-implements computation.
"""

from __future__ import annotations

from engine.hydroma.calculations.crop_water_req_calc import (
    CropWaterReqInput,
    CropWaterRequirementCalculator,
)
from engine.hydroma.simulation.calibration import (
    ishigami,
    sensitivity_of_metric,
)
from engine.hydroma.simulation.contracts import ChainInputs, ChainResult
from engine.hydroma.simulation.orchestrator import run_chain

__all__ = [
    "ChainInputs",
    "ChainResult",
    "CropWaterReqInput",
    "CropWaterRequirementCalculator",
    "ishigami",
    "run_chain",
    "sensitivity_of_metric",
]
