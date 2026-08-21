"""RothC Motor - Soil Organic Carbon Model (5-pool, Numerically Stable)."""
from __future__ import annotations

import time
from typing import Any, Dict, List

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


# RothC pool decomposition rates (yr^-1)
# Reduced rates for numerical stability
ROTHC_RATES = {
    "dpm": 1.0,    # Decomposable plant material (was 10, reduced for stability)
    "rpm": 0.3,    # Resistant plant material
    "bio": 0.66,   # Microbial biomass
    "hum": 0.02,   # Humified organic matter
    "iom": 0.0,    # Inert organic matter (stable)
}

# Carbon partitioning: DPM/RPM ratio depends on land use
DPM_RPM_RATIOS = {
    "cropland": 1.44,
    "grassland": 0.67,
    "forest": 0.25,
    "shrubland": 0.50,
    "bare": 0.0,
}


class RothCMotor(AbstractScientificMotor):
    """
    RothC soil organic carbon model (numerically stable version).

    Key improvements over v1:
    - Bounded decomposition (cannot exceed pool size)
    - Non-negative pool constraints
    - Steady-state initialization
    - Realistic rate modifiers
    """

    def __init__(self, years: int = 20, **kwargs):
        super().__init__(**kwargs)
        self.years = years

    @property
    def motor_type(self) -> MotorType:
        return MotorType.ROTH_C

    @property
    def display_name(self) -> str:
        return f"RothC (Soil Carbon, {self.years}yr)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("soil_water_mm", "raster", True, "Soil moisture (from SWAT+)"),
            MotorInput("biomass_ton_ha", "raster", True, "Plant biomass (from AquaCrop)"),
            MotorInput("initial_soc_pct", "scalar", False, "Initial SOC (default 1.5%)"),
            MotorInput("clay_percent", "scalar", False, "Clay content (default 25%)"),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("final_soc_t_ha", "raster", "t C/ha", "Final soil carbon"),
            MotorOutput("soc_change_t_ha_yr", "raster", "t C/ha/yr", "Annual SOC change"),
            MotorOutput("co2_emission_t_ha_yr", "raster", "t CO2/ha/yr", "Microbial CO2"),
            MotorOutput("sequestration_potential", "raster", "t C/ha", "C sequestration"),
        ]

    async def execute(
        self,
        inputs: Dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute RothC simulation."""
        start_time = time.time()
        run_id = f"ROTHC_{parameters.scenario_name}_{int(time.time())}"

        try:
            if not self.validate_inputs(inputs):
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="Missing required inputs",
                )

            soil_water = inputs.get("soil_water_mm")
            biomass = inputs.get("biomass_ton_ha")
            initial_soc_pct = parameters.custom_params.get("initial_soc_pct", 1.5)
            clay_percent = parameters.custom_params.get("clay_percent", 25.0)
            land_use = parameters.custom_params.get("land_use", "cropland")

            results = await self._simulate_soc(
                soil_water=soil_water,
                biomass=biomass,
                initial_soc_pct=initial_soc_pct,
                clay_percent=clay_percent,
                land_use=land_use,
                parameters=parameters,
            )

            summary = self._compute_summary(results)

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs=results,
                summary=summary,
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

    async def _simulate_soc(
        self,
        soil_water: xr.DataArray,
        biomass: xr.DataArray,
        initial_soc_pct: float,
        clay_percent: float,
        land_use: str,
        parameters: MotorParameters,
    ) -> Dict[str, Any]:
        """Simulate SOC dynamics over years (stable version)."""
        # Convert initial SOC% to t/ha
        # SOC_t_ha = SOC% * BD * depth * 10000 / 100
        # For 1.5% SOC, BD=1.3, depth=0.3m: ~58.5 t C/ha
        initial_soc_t_ha = initial_soc_pct * 1.3 * 0.3 * 10000 / 100
        initial_soc_t_ha = float(initial_soc_t_ha)

        # Annual carbon input from plant residues
        # ~40% of biomass returns as residue, ~45% is carbon
        c_input = biomass * 0.4 * 0.45  # t C/ha/yr

        # DPM/RPM ratio based on land use
        dpm_rpm = DPM_RPM_RATIOS.get(land_use, 1.44)

        # Initial pool distribution (steady-state approximation)
        dpm_ratio = dpm_rpm / (1 + dpm_rpm)
        rpm_ratio = 1 / (1 + dpm_rpm)

        # Initialize pools at approximate steady state
        dpm = initial_soc_t_ha * dpm_ratio * 0.15
        rpm = initial_soc_t_ha * rpm_ratio * 0.15
        bio = initial_soc_t_ha * 0.03
        hum = initial_soc_t_ha * 0.57
        iom = initial_soc_t_ha * 0.10

        # Moisture rate modifier (0.2 - 1.0)
        # Optimal at ~60% of field capacity
        rate_modifier = (soil_water / 100.0).clip(0.2, 1.0)

        # Clay protection factor
        clay_factor = 1.0 - (clay_percent / 100.0) * 0.5

        # Annual simulation with stability constraints
        total_co2 = xr.zeros_like(soil_water, dtype=np.float32)
        yearly_soc = []

        for year in range(self.years):
            # Decomposition: bounded by pool size
            dpm_loss = np.minimum(dpm * ROTHC_RATES["dpm"] * rate_modifier, dpm)
            rpm_loss = np.minimum(rpm * ROTHC_RATES["rpm"] * rate_modifier, rpm)
            bio_loss = np.minimum(bio * ROTHC_RATES["bio"] * rate_modifier, bio)
            hum_loss = np.minimum(hum * ROTHC_RATES["hum"] * rate_modifier, hum)

            # CO2 emissions (fraction lost to respiration)
            co2_year = (dpm_loss + rpm_loss + bio_loss + hum_loss) * 0.4 * clay_factor
            total_co2 = total_co2 + co2_year

            # Carbon transfer between pools
            # 46% to BIO, 54% to HUM
            dpm_to_bio = dpm_loss * 0.46
            dpm_to_hum = dpm_loss * 0.54
            rpm_to_bio = rpm_loss * 0.46
            rpm_to_hum = rpm_loss * 0.54
            bio_to_hum = bio_loss * 0.46
            bio_to_co2 = bio_loss * 0.54
            hum_to_bio = hum_loss * 0.46  # recirculation

            # Update pools with non-negative constraint
            dpm = np.maximum(dpm - dpm_loss + c_input * dpm_ratio, 0.0)
            rpm = np.maximum(rpm - rpm_loss + c_input * rpm_ratio, 0.0)
            bio = np.maximum(bio - bio_loss + dpm_to_bio + rpm_to_bio + hum_to_bio, 0.0)
            hum = np.maximum(hum - hum_loss + dpm_to_hum + rpm_to_hum + bio_to_hum, 0.0)
            # iom is stable

            yearly_soc.append(dpm + rpm + bio + hum + iom)

        # Final SOC
        final_soc = dpm + rpm + bio + hum + iom

        # SOC change rate (t C/ha/yr)
        soc_change = (final_soc - initial_soc_t_ha) / self.years

        # Sequestration potential (positive only)
        sequestration = (final_soc - initial_soc_t_ha).clip(0, None)

        # Average annual CO2
        avg_co2 = total_co2 / self.years

        return {
            "final_soc_t_ha": final_soc,
            "soc_change_t_ha_yr": soc_change,
            "co2_emission_t_ha_yr": avg_co2,
            "sequestration_potential": sequestration,
        }

    def _compute_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary statistics."""
        summary = {}
        for key, data in results.items():
            if isinstance(data, xr.DataArray):
                values = data.values[~np.isnan(data.values)]
                if len(values) > 0:
                    summary[key] = {
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                    }
        return summary