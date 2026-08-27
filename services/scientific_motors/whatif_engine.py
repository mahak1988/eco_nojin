"""What-If Engine - Scenario Analysis and Monte Carlo Simulation."""
from __future__ import annotations

import time
from typing import Any

import numpy as np
import xarray as xr

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)


class WhatIfMotor(AbstractScientificMotor):
    """
    What-if analysis engine with Monte Carlo simulation.

    Features:
    - Multiple scenario comparison
    - Monte Carlo uncertainty analysis
    - Multi-criteria decision support
    """

    def __init__(self, n_iterations: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.n_iterations = n_iterations

    @property
    def motor_type(self) -> MotorType:
        return MotorType.WHAT_IF

    @property
    def display_name(self) -> str:
        return f"What-If Engine (n={self.n_iterations})"

    def get_input_requirements(self) -> list[MotorInput]:
        return [
            MotorInput("baseline_yield", "raster", True, "Baseline yield"),
            MotorInput("baseline_water", "raster", True, "Baseline water use"),
            MotorInput("baseline_carbon", "raster", True, "Baseline carbon"),
        ]

    def get_outputs(self) -> list[MotorOutput]:
        return [
            MotorOutput("scenario_comparison", "table", "dict", "Scenario results"),
            MotorOutput("uncertainty_range", "raster", "min-max", "Monte Carlo range"),
            MotorOutput("best_scenario", "scalar", "name", "Optimal scenario"),
        ]

    async def execute(
        self,
        inputs: dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute what-if analysis."""
        start_time = time.time()
        run_id = f"WHATIF_{parameters.scenario_name}_{int(time.time())}"

        try:
            baseline_yield = inputs.get("baseline_yield")
            baseline_water = inputs.get("baseline_water")
            baseline_carbon = inputs.get("baseline_carbon")

            # Define scenarios
            scenarios = self._define_scenarios()

            # Monte Carlo simulation
            mc_results = await self._monte_carlo(
                baseline_yield=baseline_yield,
                scenarios=scenarios,
                parameters=parameters,
            )

            # Multi-criteria decision
            best_scenario = self._select_best_scenario(mc_results)

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "scenarios": scenarios,
                    "monte_carlo": mc_results,
                    "best_scenario": best_scenario,
                },
                summary=self._compute_summary(mc_results),
                execution_time_seconds=time.time() - start_time,
            )

        except Exception as e:
            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def _define_scenarios(self) -> dict[str, dict[str, float]]:
        """Define analysis scenarios."""
        return {
            "baseline": {
                "irrigation_mm": 50,
                "fertilizer_factor": 1.0,
                "yield_modifier": 1.0,
                "description": "Current practices",
            },
            "improved_irrigation": {
                "irrigation_mm": 75,
                "fertilizer_factor": 1.0,
                "yield_modifier": 1.15,
                "description": "Drip irrigation, +50% water",
            },
            "organic_farming": {
                "irrigation_mm": 50,
                "fertilizer_factor": 0.8,
                "yield_modifier": 0.85,
                "description": "Organic inputs, -15% yield",
            },
            "climate_change": {
                "irrigation_mm": 50,
                "fertilizer_factor": 1.0,
                "yield_modifier": 0.75,
                "description": "CC scenario, -25% yield",
            },
        }

    async def _monte_carlo(
        self,
        baseline_yield: xr.DataArray,
        scenarios: dict[str, dict],
        parameters: MotorParameters,
    ) -> dict[str, Any]:
        """Run Monte Carlo simulation for each scenario."""
        results = {}

        for scenario_name, scenario_params in scenarios.items():
            # Sample parameters with uncertainty
            yield_samples = []
            water_samples = []
            carbon_samples = []

            for _ in range(self.n_iterations):
                # Add uncertainty (±10%)
                yield_mod = scenario_params["yield_modifier"] * np.random.uniform(0.9, 1.1)
                water_use = scenario_params["irrigation_mm"] * np.random.uniform(0.85, 1.15)
                carbon_factor = np.random.uniform(0.95, 1.05)

                # Apply to baseline
                scenario_yield = baseline_yield * yield_mod
                yield_samples.append(float(scenario_yield.mean()))
                water_samples.append(water_use)
                carbon_samples.append(carbon_factor)

            results[scenario_name] = {
                "yield_mean": float(np.mean(yield_samples)),
                "yield_std": float(np.std(yield_samples)),
                "yield_min": float(np.min(yield_samples)),
                "yield_max": float(np.max(yield_samples)),
                "water_mean": float(np.mean(water_samples)),
                "carbon_mean": float(np.mean(carbon_samples)),
            }

        return results

    def _select_best_scenario(self, mc_results: dict[str, Any]) -> str:
        """Select best scenario based on multi-criteria."""
        scores = {}
        for name, stats in mc_results.items():
            # Score = yield - water penalty + carbon bonus
            score = (
                stats["yield_mean"]
                - 0.1 * stats["water_mean"]
                + 0.2 * stats["carbon_mean"]
            )
            scores[name] = score

        return max(scores, key=scores.get)

    def _compute_summary(self, mc_results: dict[str, Any]) -> dict[str, Any]:
        """Compute summary statistics."""
        return {
            name: {
                "yield_mean": stats["yield_mean"],
                "yield_range": f"{stats['yield_min']:.2f}-{stats['yield_max']:.2f}",
                "water_mean": stats["water_mean"],
            }
            for name, stats in mc_results.items()
        }
