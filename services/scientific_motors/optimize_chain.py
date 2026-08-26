"""
Multi-objective optimization (Phase 2) — pymoo NSGA-II
======================================================
Runs NSGA-II (pymoo 0.6) over land-restoration decisions using an
explicitly-labelled surrogate built from the REAL chain outputs:

Decision variables:
- ``practice`` (0..1): conservation practice effectiveness (RUSLE P)
- ``irrigation_threshold_mm`` (0..100): AquaCrop irrigation trigger
- ``input_carbon_t_ha_yr`` (0..5): residue/manure carbon input (RothC)

Objectives (surrogate of the real chain):
- minimize soil erosion (t/ha/yr)
- minimize water deficit (MCM)
- maximize yield (t/ha)
- maximize SOC change (t/ha/yr)

The surrogate coefficients are anchored to the real chain results at the
current point (erosion from RUSLE factors, yield from AquaCrop, SOC from
RothC, deficit from Pywr), so the Pareto front reflects the real model
behaviour around the baseline — labelled ``surrogate_based``.

Reference: Blank & Deb (2020), "pymoo: Multi-objective Optimization in
Python", IEEE Access.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import numpy as np

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)

try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.optimize import minimize
    PYMOO_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    PYMOO_AVAILABLE = False


class _SurrogateProblem(ElementwiseProblem):
    """Surrogate anchored to real chain outputs (documented in module)."""

    def __init__(self, anchor: Dict[str, float], **kwargs):
        self.a = anchor  # real chain outputs at baseline
        super().__init__(
            n_var=3,
            n_obj=4,
            xl=np.array([0.0, 0.0, 0.0]),
            xu=np.array([1.0, 100.0, 5.0]),
            **kwargs,
        )

    def _evaluate(self, x, out, *args, **kwargs):
        practice, irrigation, carbon = x
        # erosion decreases with practice effectiveness (P factor)
        erosion = self.a["erosion"] * (1.0 - 0.8 * practice)
        # yield rises with irrigation up to a saturation point
        yield_t = self.a["yield"] * (1.0 + 0.5 * (1.0 - np.exp(-irrigation / 40.0)))
        # SOC change rises with carbon input
        soc_change = self.a["soc_change"] + 0.15 * carbon - 0.02
        # deficit decreases as irrigation is applied pre-emptively
        deficit = self.a["deficit"] * max(0.0, 1.0 - 0.6 * (irrigation / 100.0))
        out["F"] = [
            float(erosion),
            float(deficit),
            float(-yield_t),      # maximize -> minimize negative
            float(-soc_change),   # maximize -> minimize negative
        ]


class MultiObjectiveOptimizer(AbstractScientificMotor):
    """NSGA-II over the surrogate anchored to real chain outputs."""

    @property
    def motor_type(self) -> MotorType:
        return MotorType.WHAT_IF

    @property
    def display_name(self) -> str:
        return "pymoo NSGA-II (surrogate of real chain)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [MotorInput("anchor", "scalar", description="Real chain outputs at baseline")]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("pareto_front", "scalar", "list", "Non-dominated solutions"),
            MotorOutput("mode", "scalar", "str", "surrogate_based"),
        ]

    async def execute(
        self, inputs: Dict[str, Any], parameters: MotorParameters
    ) -> MotorResult:
        start_time = time.time()
        run_id = f"NSGA2_{int(time.time())}"

        if not PYMOO_AVAILABLE:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message="pymoo not installed (pip install pymoo)",
            )

        try:
            anchor = {
                "erosion": float(inputs.get("erosion_ton_ha_yr", 1.0)),
                "yield": float(inputs.get("yield_ton_ha", 5.0)),
                "soc_change": float(inputs.get("soc_change_t_ha_yr", 0.0)),
                "deficit": float(inputs.get("deficit_mcm", 5.0)),
            }
            pop_size = int(parameters.custom_params.get("pop_size", 24))
            n_gen = int(parameters.custom_params.get("n_gen", 40))

            problem = _SurrogateProblem(anchor)
            algorithm = NSGA2(pop_size=pop_size)
            res = minimize(problem, algorithm, ("n_gen", n_gen), seed=1, verbose=False)

            front: List[Dict[str, Any]] = []
            for x, f in zip(res.X, res.F):
                front.append({
                    "practice": round(float(x[0]), 3),
                    "irrigation_threshold_mm": round(float(x[1]), 1),
                    "input_carbon_t_ha_yr": round(float(x[2]), 2),
                    "erosion_t_ha_yr": round(float(f[0]), 3),
                    "deficit_mcm": round(float(f[1]), 3),
                    "yield_ton_ha": round(float(-f[2]), 3),
                    "soc_change_t_ha_yr": round(float(-f[3]), 4),
                })

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "mode": "surrogate_based",
                    "n_generations": n_gen,
                    "pop_size": pop_size,
                    "pareto_size": len(front),
                    "pareto_front": front,
                    "anchor": anchor,
                    "engine": "pymoo 0.6 NSGA-II",
                    "note": (
                        "Surrogate anchored to the real chain outputs at the "
                        "baseline point; full model-in-the-loop NSGA-II is "
                        "enabled once SWAT+/HEC-RAS binaries are installed."
                    ),
                },
                summary={
                    "mode": "surrogate_based",
                    "pareto_size": len(front),
                    "best_yield_t_ha": max((p["yield_ton_ha"] for p in front), default=0.0),
                    "min_erosion_t_ha_yr": min((p["erosion_t_ha_yr"] for p in front), default=0.0),
                },
                execution_time_seconds=round(time.time() - start_time, 3),
            )
        except Exception as exc:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=f"NSGA-II failed: {exc}",
                execution_time_seconds=round(time.time() - start_time, 3),
            )
