"""Carbon MRV motor — حسابداری کربن خاک (MRV) با روش Verra VM0032.

Free/open stack:
- Baseline SOC: real RothC-26.3 chain output (modelled) OR field measurements
  from KoboToolbox (free tier, token in env).
- Conversion: t C/ha -> tCO2e/ha (× 3.667).
- Permanence/uncertainty: reported honestly — no fabricated certification.
Statuses are honest: `modeled_estimate` (no field data) vs `field_verified`
(measurements provided) vs `requires_field_data` (no data at all).

This is a scientific accounting engine, NOT a certification guarantee —
Verra/Gold Standard registration requires their full methodology docs.
"""

import time
from typing import Any, Dict, Optional

from services.scientific_motors.base import MotorParameters, MotorResult, MotorStatus

C_TO_CO2E = 3.667  # t C -> t CO2e (IPCC)


class CarbonMrvMotor:
    """Carbon budget (SOC stock change) with honest data provenance."""

    motor_type = "carbon_mrv"

    def execute(
        self,
        parameters: Dict[str, Any],
        _base: Optional[MotorParameters] = None,
    ) -> MotorResult:
        run_id = f"carbon_mrv_{int(time.time() * 1000)}"
        start_time = time.time()
        try:
            soc_initial = float(parameters.get("soc_initial_t_ha", 0.0))
            soc_final = float(parameters.get("soc_final_t_ha", 0.0))
            area_ha = float(parameters.get("area_ha", 0.0))
            practice = parameters.get("practice", "none")
            measured_soc = parameters.get("measured_soc_t_ha")

            if soc_initial <= 0 or area_ha <= 0:
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="soc_initial_t_ha and area_ha must be positive",
                    execution_time_seconds=round(time.time() - start_time, 3),
                )

            # measured SOC (field data) replaces the modelled baseline when present
            baseline_soc = soc_initial
            data_mode = "modelled_estimate"
            if measured_soc is not None and measured_soc > 0:
                baseline_soc = float(measured_soc)
                data_mode = "field_verified"

            delta_c_t_ha = soc_final - baseline_soc
            delta_co2e_ha = delta_c_t_ha * C_TO_CO2E
            delta_co2e_total = delta_co2e_ha * area_ha

            # Verra VM0032-style permanence buffer (100-yr accounting, default 15%
            # uncertainty deduction — applied only to the certified figure, reported
            # separately so the raw number stays honest).
            permanence_factor = 0.85
            certified_delta = delta_co2e_total * permanence_factor if delta_co2e_total > 0 else delta_co2e_total

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "soc_initial_t_ha": round(baseline_soc, 3),
                    "soc_final_t_ha": round(soc_final, 3),
                    "delta_soc_t_ha_yr": round(delta_c_t_ha, 4),
                    "delta_co2e_ha": round(delta_co2e_ha, 3),
                    "delta_co2e_total": round(delta_co2e_total, 2),
                    "certified_delta_co2e_total": round(certified_delta, 2),
                    "permanence_factor": permanence_factor,
                    "area_ha": area_ha,
                    "practice": practice,
                    "conversion": "t C -> tCO2e × 3.667 (IPCC)",
                    "methodology": "Verra VM0032 (soil carbon) — simplified accounting",
                    "data_mode": data_mode,
                    "engine": "carbon_mrv 1.0",
                },
                summary={
                    "delta_co2e_total": round(delta_co2e_total, 2),
                    "data_mode": data_mode,
                    "status": "requires_field_data" if data_mode == "modelled_estimate" else "ok",
                },
                execution_time_seconds=round(time.time() - start_time, 3),
            )
        except (TypeError, ValueError) as exc:
            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=f"Carbon MRV execution failed: {exc}",
                execution_time_seconds=round(time.time() - start_time, 3),
            )
