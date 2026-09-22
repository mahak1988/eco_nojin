"""Unified simulation controller for the Eco Nojin simulation environment.

Provides a single entry point to run any simulator by name with a typed
config, returning provenance-labeled results.  The controller is the
integration seam recommended by the simulation design document and is what
the API layer should call (rather than importing simulators directly).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from engine.hydroma.simulation_env.contracts import (
    SimulationMetadata,
)


@dataclass
class SimulationRequest:
    """A serializable simulation request."""

    name: str
    parameters: dict[str, Any]
    seed: int = 42


@dataclass
class SimulationResponse:
    """A provenance-labeled simulation response."""

    name: str
    seed: int
    result: dict[str, Any]
    metadata: SimulationMetadata


class SimulationController:
    """Registry + dispatcher for synthetic simulators."""

    def __init__(self) -> None:
        self._registry: dict[str, tuple[Callable[..., object], type]] = {}

    def register(self, name: str, simulator: Callable[..., object], config_cls: type) -> None:
        self._registry[name] = (simulator, config_cls)

    def available(self) -> list[str]:
        return sorted(self._registry)

    def run(self, request: SimulationRequest) -> SimulationResponse:
        if request.name not in self._registry:
            raise ValueError(f"Unknown simulator: {request.name}. Available: {self.available()}")
        simulator, config_cls = self._registry[request.name]
        config = config_cls(**request.parameters)
        result = simulator(config)
        dump = _to_dict(result)
        return SimulationResponse(
            name=request.name,
            seed=request.seed,
            result=dump,
            metadata=_meta(request.name, request.seed, request.parameters),
        )


def _meta(name: str, seed: int, params: dict[str, Any]) -> SimulationMetadata:
    return SimulationMetadata(
        scenario=name,
        site_id=params.get("site_id", "synth"),
        seed=seed,
        start_year=params.get("start_year", 2024),
        end_year=params.get("end_year", 2024),
        parameters=params,
    )


def _to_dict(obj: object) -> dict[str, Any]:
    """Best-effort dict conversion of a simulator result (pydantic/dataclass)."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict

        try:
            return asdict(obj)  # type: ignore[arg-type]
        except Exception:
            return {k: getattr(obj, k) for k in obj.__dataclass_fields__}  # type: ignore[attr-defined]
    if isinstance(obj, dict):
        return obj
    return {"value": str(obj)}


def build_default_controller() -> SimulationController:
    """Build a controller pre-registered with all simulation_env simulators."""
    from engine.hydroma.simulation_env.climate import (
        DroughtScenario,
        HeatWaveScenario,
        MonsoonScenario,
        simulate_climate_change,
        simulate_drought,
        simulate_monsoon,
        simulate_temperature_extremes,
    )
    from engine.hydroma.simulation_env.disasters import (
        FireScenario,
        FloodScenario,
        LandslideScenario,
        StormScenario,
        simulate_flood,
        simulate_landslide,
        simulate_storm,
        simulate_wildfire,
    )

    ctrl = SimulationController()

    # Climate
    ctrl.register("drought", simulate_drought, DroughtScenario)
    ctrl.register("monsoon", simulate_monsoon, MonsoonScenario)
    ctrl.register("temperature_extremes", simulate_temperature_extremes, HeatWaveScenario)
    ctrl.register("climate_change_projection", simulate_climate_change, type("CCParams", (), {}))
    # Disasters
    ctrl.register("wildfire", simulate_wildfire, FireScenario)
    ctrl.register("flood", simulate_flood, FloodScenario)
    ctrl.register("storm", simulate_storm, StormScenario)
    ctrl.register("landslide", simulate_landslide, LandslideScenario)
    # Stress (function-style, wrapped to accept a config dataclass)
    _register_stress_wrappers(ctrl)
    return ctrl


def _register_stress_wrappers(ctrl: SimulationController) -> None:
    """Register stress-test entry points that accept seed-driven parameters."""

    @dataclass
    class _CorruptionParams:
        grid_size: int = 64
        seed: int = 42
        cloud_cover_pct: float = 30.0
        sensor_noise_std: float = 0.02
        dead_pixels_pct: float = 2.0

    def _run_index_robustness(cfg: _CorruptionParams) -> dict[str, Any]:
        from engine.hydroma.simulation_env.stress import CorruptionConfig, validate_index_robustness

        corruptions = [
            CorruptionConfig(
                cloud_cover_pct=cfg.cloud_cover_pct,
                sensor_noise_std=cfg.sensor_noise_std,
                dead_pixels_pct=cfg.dead_pixels_pct,
                seed=cfg.seed,
            )
        ]
        res = validate_index_robustness(
            grid_size=cfg.grid_size, seed=cfg.seed, corruptions=corruptions
        )
        return {"results": [r.model_dump() for r in res]}

    def _run_volume(cfg: _CorruptionParams) -> dict[str, Any]:
        from engine.hydroma.simulation_env.stress import run_volume_stress

        res = run_volume_stress(sizes=[64, 256, 512], seed=cfg.seed)
        return {"results": [r.__dict__ for r in res]}

    def _run_fallbacks(_: _CorruptionParams) -> dict[str, Any]:
        from engine.hydroma.simulation_env.stress import validate_fallbacks

        res = validate_fallbacks()
        return {"results": [r.model_dump() for r in res]}

    ctrl.register("stress_index_robustness", _run_index_robustness, _CorruptionParams)
    ctrl.register("stress_volume", _run_volume, _CorruptionParams)
    ctrl.register("stress_fallbacks", _run_fallbacks, _CorruptionParams)


__all__ = [
    "SimulationController",
    "SimulationRequest",
    "SimulationResponse",
    "build_default_controller",
]
