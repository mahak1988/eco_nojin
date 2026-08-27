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
from typing import Any

from services.scientific_motors.base import MotorParameters, MotorResult, MotorStatus

C_TO_CO2E = 3.667  # t C -> t CO2e (IPCC)

# Gold Standard Soil Organic Carbon Framework (v1.0) reporting parameters
GS_MONITORING = {
    "soil_depth_cm": 30,
    "monitoring_interval_years": 5,
    "requirement": "measure SOC at 0-30 cm every 5 years (GS SOC Framework)",
}


class CarbonMrvMotor:
    """Carbon budget (SOC stock change) with honest data provenance."""

    motor_type = "carbon_mrv"

    def execute(
        self,
        parameters: dict[str, Any],
        _base: MotorParameters | None = None,
    ) -> MotorResult:
        run_id = f"carbon_mrv_{int(time.time() * 1000)}"
        start_time = time.time()
        try:
            soc_initial = float(parameters.get("soc_initial_t_ha", 0.0))
            soc_final = float(parameters.get("soc_final_t_ha", 0.0))
            area_ha = float(parameters.get("area_ha", 0.0))
            practice = parameters.get("practice", "none")
            measured_soc = parameters.get("measured_soc_t_ha")
            methodology = str(parameters.get("methodology", "vm0032")).lower()
            permanence = float(parameters.get("permanence_factor", 0.85))
            # multi-period measurements: [{year, soc_t_ha}] -> t0..tn trend
            measurements = parameters.get("measurements") or []
            periods: list[dict[str, Any]] = []
            if isinstance(measurements, list) and len(measurements) >= 2:
                prev = None
                for m in sorted(measurements, key=lambda x: float(x.get("year", 0))):
                    soc = float(m.get("soc_t_ha", 0.0))
                    if prev is not None:
                        d_c = soc - prev
                        periods.append(
                            {
                                "year": int(m.get("year", 0)),
                                "soc_t_ha": round(soc, 3),
                                "delta_tco2e_ha": round(d_c * C_TO_CO2E, 3),
                            }
                        )
                    prev = soc

            if soc_initial <= 0 or area_ha <= 0:
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="soc_initial_t_ha and area_ha must be positive",
                    execution_time_seconds=round(time.time() - start_time, 3),
                )

            # measured SOC (field data) replaces the modelled baseline when present.
            # Multi-period series: the LAST measured point acts as the field baseline
            # (consistent with single measured_soc_t_ha semantics).
            baseline_soc = soc_initial
            data_mode = "modelled_estimate"
            if measured_soc is not None and measured_soc > 0:
                baseline_soc = float(measured_soc)
                data_mode = "field_verified"
            elif periods:
                last_measured = float(periods[-1]["soc_t_ha"])
                if last_measured > 0:
                    baseline_soc = last_measured
                    data_mode = "field_verified"

            delta_c_t_ha = soc_final - baseline_soc
            delta_co2e_ha = delta_c_t_ha * C_TO_CO2E
            delta_co2e_total = delta_co2e_ha * area_ha

            # Verra VM0032-style permanence buffer (100-yr accounting, default 15%
            # uncertainty deduction — applied only to the certified figure, reported
            # separately so the raw number stays honest).
            certified_delta = delta_co2e_total * permanence if delta_co2e_total > 0 else delta_co2e_total

            if methodology == "gold_standard":
                methodology_label = "Gold Standard Soil Organic Carbon Framework (v1.0) — simplified"
                extra: dict[str, Any] = {"monitoring": GS_MONITORING}
            else:
                methodology = "vm0032"
                methodology_label = "Verra VM0032 (soil carbon) — simplified accounting"
                extra: dict[str, Any] = {"certification_note": "VM0032 registration requires full methodology docs"}


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
                    "periods": periods,
                    "certified_delta_co2e_total": round(certified_delta, 2),
                    "permanence_factor": permanence,
                    "area_ha": area_ha,
                    "practice": practice,
                    "conversion": "t C -> tCO2e × 3.667 (IPCC)",
                    "methodology": methodology_label,
                    "methodology_id": methodology,
                    "data_mode": data_mode,
                    "engine": "carbon_mrv 1.1",
                    **extra,
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
