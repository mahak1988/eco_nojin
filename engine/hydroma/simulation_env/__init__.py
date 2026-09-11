"""Eco Nojin simulation environment (Phase 4).

A deterministic, seed-reproducible simulation environment built on top of the
existing HyDroMa scientific stack (satellite indices, RUSLE/SWAT runoff,
soil water-retention, crop-yield and SSP climate machinery).

Modules
-------
- ``contracts``: shared provenance-tagged dataclasses/pydantic models.
- ``weather``: pure synthetic weather generator (no external API).
- ``climate``: drought, monsoon/flood, temperature-extremes and climate-change
  projection simulators.
- ``disasters``: wildfire (dNBR), flood/inundation, storm/hurricane and
  landslide/erosion simulators.
- ``stress``: combinatorial runner, data-quality injection, volume stress,
  fallback validation and performance profiling.
- ``controller``: unified dispatch API for the simulators above.

Every output carries ``data_source="simulated"``; synthetic results must never
be presented as measured observations.
"""

from engine.hydroma.simulation_env.contracts import (
    ENGINE_VERSION,
    SYNTHETIC,
    AnnualImpact,
    ClimateProfile,
    DisasterImpact,
    Provenance,
    Severity,
    SimulationMetadata,
    StressTestResult,
)
from engine.hydroma.simulation_env.controller import (
    SimulationController,
    SimulationRequest,
    SimulationResponse,
    build_default_controller,
)

__all__ = [
    "ENGINE_VERSION",
    "SYNTHETIC",
    "AnnualImpact",
    "ClimateProfile",
    "DisasterImpact",
    "Provenance",
    "Severity",
    "SimulationController",
    "SimulationMetadata",
    "SimulationRequest",
    "SimulationResponse",
    "StressTestResult",
    "build_default_controller",
]
