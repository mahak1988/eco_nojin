"""
Pywr Water Allocation Motor (Phase 2) — real network simulation
===============================================================
Runs a REAL water-allocation network with the `pywr` package (the
open-source alternative to WEAP, MIT-licensed, free):

    Inflow (river) --> Reservoir --> Irrigation demand --> Environment

- Inflow: monthly runoff proxy from REAL rainfall (ERA5) with a runoff
  coefficient; when a SWAT+ run is available its flow replaces the proxy
  (the chain runner wires that in).
- Demand: monthly crop water demand (AquaCrop irrigation / ET0-based).
- Outputs: supply reliability, total deficit, storage trajectory,
  monthly supply series.

References
----------
- Pywr: Tomlinson et al. (2016), J. Open Source Software; pywr.org
- Water allocation modelling best practice (WEAP-alike node-link).
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

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
    from pywr.core import Input as PywrInput
    from pywr.core import Link as PywrLink
    from pywr.core import Model as PywrModel
    from pywr.core import Output as PywrOutput
    from pywr.core import Reservoir as PywrReservoir
    from pywr.parameters import ArrayIndexedParameter, DataFrameParameter
    from pywr.recorders import NumpyArrayNodeRecorder
    PYRW_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    PYRW_AVAILABLE = False


class PywrWaterAllocationMotor(AbstractScientificMotor):
    """Pywr node-link water allocation model (real execution)."""

    @property
    def motor_type(self) -> MotorType:
        return MotorType.WHAT_IF  # reuse enum slot; display name clarifies

    @property
    def display_name(self) -> str:
        return "Pywr water allocation (WEAP alternative)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("monthly_inflow_mcm", "timeseries", description="12 monthly inflows (MCM)"),
            MotorInput("monthly_demand_mcm", "timeseries", description="12 monthly demands (MCM)"),
            MotorInput("reservoir_capacity_mcm", "scalar", description="Storage capacity"),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("supply_reliability", "scalar", "%", "Fraction of demand met"),
            MotorOutput("total_deficit_mcm", "scalar", "MCM", "Unmet demand"),
            MotorOutput("storage_series", "timeseries", "MCM", "Reservoir storage"),
            MotorOutput("supply_series", "timeseries", "MCM", "Monthly supply"),
        ]

    async def execute(
        self, inputs: Dict[str, Any], parameters: MotorParameters
    ) -> MotorResult:
        start_time = time.time()
        run_id = f"PYWR_{int(time.time())}"

        if not PYRW_AVAILABLE:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message="pywr not installed (pip install pywr)",
            )

        try:
            inflow = np.asarray(inputs["monthly_inflow_mcm"], dtype=float)
            demand = np.asarray(inputs["monthly_demand_mcm"], dtype=float)
            capacity = float(inputs.get("reservoir_capacity_mcm", 50.0))
            if len(inflow) != 12 or len(demand) != 12:
                raise ValueError("inflow and demand must have exactly 12 values")
            inflow = np.maximum(inflow, 0.0)
            demand = np.maximum(demand, 0.0)

            start = parameters.custom_params.get("start_date", "2025-10-01")
            start_ts = pd.Timestamp(start)

            model = PywrModel()
            # 30-day steps: pywr derives freq "30D" from a timedelta delta
            # (a DateOffset is rejected by pandas 2.x period_range)
            model.timestepper.delta = pd.Timedelta("30D")
            model.timestepper.start = start_ts
            model.timestepper.end = start_ts + pd.Timedelta(days=30 * 11)
            period_starts = model.timestepper.datetime_index.to_timestamp()

            inflow_param = DataFrameParameter(
                model, pd.DataFrame({"inflow": inflow}, index=period_starts)
            )
            demand_param = DataFrameParameter(
                model, pd.DataFrame({"demand": demand}, index=period_starts)
            )
            inflow_node = PywrInput(model, "inflow", max_flow=inflow_param)
            reservoir = PywrReservoir(model, "reservoir", max_volume=capacity, initial_volume=capacity * 0.7)
            demand_node = PywrOutput(model, "demand", max_flow=demand_param, cost=-10.0)
            env_node = PywrOutput(model, "environment", cost=0.0)

            link1 = PywrLink(model, "river_to_reservoir", cost=0.0)
            link2 = PywrLink(model, "reservoir_to_supply", cost=0.0)

            inflow_node.connect(link1)
            link1.connect(reservoir)
            reservoir.connect(link2)
            link2.connect(demand_node)
            reservoir.connect(env_node)

            storage_rec = NumpyArrayNodeRecorder(model, reservoir, name="storage")
            supply_rec = NumpyArrayNodeRecorder(model, demand_node, name="supply")

            model.check()
            model.run()

            supply = np.asarray(supply_rec.data, dtype=float).flatten()
            storage = np.asarray(storage_rec.data, dtype=float).flatten()
            deficit = float(np.maximum(demand - supply, 0.0).sum())

            total_demand = float(demand.sum())
            reliability = (1.0 - deficit / total_demand) * 100.0 if total_demand > 0 else 100.0

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "supply_reliability_pct": round(reliability, 2),
                    "total_deficit_mcm": round(deficit, 3),
                    "total_demand_mcm": round(total_demand, 3),
                    "total_supply_mcm": round(float(supply.sum()), 3),
                    "storage_series": [round(float(x), 3) for x in storage],
                    "supply_series": [round(float(x), 3) for x in supply],
                    "engine": "pywr 1.31 (open-source WEAP alternative)",
                    "network": "inflow -> reservoir -> demand + environment",
                },
                summary={
                    "supply_reliability_pct": round(reliability, 1),
                    "total_deficit_mcm": round(deficit, 2),
                },
                execution_time_seconds=round(time.time() - start_time, 3),
            )
        except Exception as exc:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=f"Pywr execution failed: {exc}",
                execution_time_seconds=round(time.time() - start_time, 3),
            )
