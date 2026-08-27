"""Simulation module (Phase 3): integrated model chain for Eco Nojin.

Contains inter-model data contracts, scenario matrices, model runners
(AquaCrop-OSPy, RothC, RUSLE) and the orchestrator that executes the
chain with explicit provenance labels (data_source="simulated" + model
name/version) — never presenting model output as measured field data.
"""

from engine.hydroma.simulation.contracts import (
    AquacropOutput,
    ChainInputs,
    ChainResult,
    MonthClimate,
    RothcOutput,
    RusleOutput,
    ScenarioParams,
)
from engine.hydroma.simulation.orchestrator import run_chain
from engine.hydroma.simulation.scenarios import SCENARIOS

__all__ = [
    "SCENARIOS",
    "AquacropOutput",
    "ChainInputs",
    "ChainResult",
    "MonthClimate",
    "RothcOutput",
    "RusleOutput",
    "ScenarioParams",
    "run_chain",
]
