"""AquaCrop Motor - FAO Crop Yield Model (Daily Water Balance)."""
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

# Crop parameters database (FAO AquaCrop)
# Reference: Raes et al. (2009), Steduto et al. (2009)
CROP_DATABASE = {
    "wheat": {
        "kc_max": 1.1,
        "p_lower": 0.20,
        "p_upper": 0.55,
        "wp": 15.0,          # g/m2 biomass per mm water
        "harvest_index": 0.45,
        "growing_days": 150,
        "water_requirement_mm": 450,  # typical seasonal requirement
    },
    "maize": {
        "kc_max": 1.2,
        "p_lower": 0.14,
        "p_upper": 0.69,
        "wp": 24.0,
        "harvest_index": 0.55,
        "growing_days": 140,
        "water_requirement_mm": 550,
    },
    "barley": {
        "kc_max": 1.05,
        "p_lower": 0.25,
        "p_upper": 0.55,
        "wp": 13.0,
        "harvest_index": 0.42,
        "growing_days": 130,
        "water_requirement_mm": 400,
    },
    "cotton": {
        "kc_max": 1.15,
        "p_lower": 0.35,
        "p_upper": 0.65,
        "wp": 9.5,
        "harvest_index": 0.45,
        "growing_days": 160,
        "water_requirement_mm": 700,
    },
    "tomato": {
        "kc_max": 1.15,
        "p_lower": 0.25,
        "p_upper": 0.60,
        "wp": 22.0,
        "harvest_index": 0.60,
        "growing_days": 120,
        "water_requirement_mm": 500,
    },
}


class AquaCropMotor(AbstractScientificMotor):
    """
    AquaCrop model (FAO-66) with Daily Water Balance.

    Simulates crop yield with realistic water limitation:
    - Daily transpiration based on Kc curve
    - Water stress when soil water depletes
    - Biomass accumulation over growing season
    - Harvest index conversion to yield
    """

    def __init__(self, crop_type: str = "wheat", **kwargs):
        super().__init__(**kwargs)
        self.crop_type = crop_type.lower()
        self.crop_params = CROP_DATABASE.get(self.crop_type)

        if self.crop_params is None:
            self.crop_type = "wheat"
            self.crop_params = CROP_DATABASE["wheat"]

    @property
    def motor_type(self) -> MotorType:
        return MotorType.AQUACROP

    @property
    def display_name(self) -> str:
        return f"AquaCrop ({self.crop_type})"

    def get_input_requirements(self) -> list[MotorInput]:
        return [
            MotorInput("soil_water_mm", "raster", True, "Initial soil water (from SWAT+)"),
            MotorInput("et_mm", "raster", True, "Reference ET (from SWAT+)"),
        ]

    def get_outputs(self) -> list[MotorOutput]:
        return [
            MotorOutput("yield_ton_ha", "raster", "t/ha", "Crop yield"),
            MotorOutput("biomass_ton_ha", "raster", "t/ha", "Above-ground biomass"),
            MotorOutput("water_productivity", "raster", "g/m2/mm", "WP achieved"),
            MotorOutput("stress_index", "raster", "0-1", "Average water stress"),
            MotorOutput("total_transpiration_mm", "raster", "mm", "Seasonal transpiration"),
        ]

    async def execute(
        self,
        inputs: dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute AquaCrop simulation."""
        start_time = time.time()
        run_id = f"AC_{self.crop_type}_{parameters.scenario_name}_{int(time.time())}"

        try:
            if not self.validate_inputs(inputs):
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="Missing required inputs",
                )

            soil_water = inputs.get("soil_water_mm")
            et_ref = inputs.get("et_mm")
            irrigation_mm = parameters.custom_params.get("irrigation_mm", 0.0)

            results = await self._simulate_crop(
                soil_water=soil_water,
                et_ref=et_ref,
                irrigation_mm=irrigation_mm,
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

    async def _simulate_crop(
        self,
        soil_water: xr.DataArray,
        et_ref: xr.DataArray,
        irrigation_mm: float,
        parameters: MotorParameters,
    ) -> dict[str, Any]:
        """Simulate crop growth with daily water balance."""
        p = self.crop_params
        kc_max = p["kc_max"]
        wp = p["wp"]
        hi = p["harvest_index"]
        growing_days = p["growing_days"]

        # Generate Kc curve for the season
        kc_curve = self._generate_kc_curve(growing_days, kc_max)

        # Initial available water
        available_water = soil_water + irrigation_mm  # mm

        # ET0 from SWAT+ (assume daily value)
        et0 = et_ref  # mm/day

        # Daily simulation
        total_transpiration = xr.zeros_like(soil_water, dtype=np.float32)
        total_stress = xr.zeros_like(soil_water, dtype=np.float32)
        water_remaining = available_water.copy()

        for day in range(growing_days):
            kc = kc_curve[day]

            # Potential transpiration for this day
            t_potential = kc * et0  # mm/day

            # Actual transpiration (limited by available water)
            # If enough water: full transpiration
            # If not enough: stress occurs
            t_actual = xr.where(
                water_remaining >= t_potential,
                t_potential,
                water_remaining.clip(0, None),
            )

            # Stress factor (0 = no stress, 1 = full stress)
            stress = xr.where(
                t_potential > 0,
                1.0 - (t_actual / (t_potential + 1e-6)),
                0.0,
            )
            stress = stress.clip(0, 1)

            # Update water balance
            water_remaining = water_remaining - t_actual
            water_remaining = water_remaining.clip(0, None)

            # Accumulate
            total_transpiration = total_transpiration + t_actual
            total_stress = total_stress + stress

        # Average stress over season
        avg_stress = total_stress / growing_days

        # Biomass = WP * Total Transpiration
        biomass_g_m2 = wp * total_transpiration
        biomass_ton_ha = biomass_g_m2 / 100  # g/m2 to t/ha

        # Yield = HI * Biomass
        yield_ton_ha = hi * biomass_ton_ha

        # Achieved Water Productivity
        achieved_wp = xr.where(
            total_transpiration > 0,
            biomass_g_m2 / (total_transpiration + 1e-6),
            0,
        )

        return {
            "yield_ton_ha": yield_ton_ha,
            "biomass_ton_ha": biomass_ton_ha,
            "water_productivity": achieved_wp,
            "stress_index": avg_stress,
            "total_transpiration_mm": total_transpiration,
        }

    def _generate_kc_curve(self, days: int, kc_max: float) -> np.ndarray:
        """Generate daily Kc curve (simplified 4-phase)."""
        kc = np.zeros(days)

        # Phase 1: Initial (0-30 days) - establishment
        kc[:30] = 0.3

        # Phase 2: Development (30-90 days)
        if days > 30:
            end_dev = min(90, days)
            kc[30:end_dev] = np.linspace(0.3, kc_max, end_dev - 30)

        # Phase 3: Mid-season (90-120 days)
        if days > 90:
            end_mid = min(120, days)
            kc[90:end_mid] = kc_max

        # Phase 4: Late season (120+ days) - senescence
        if days > 120:
            kc[120:] = np.linspace(kc_max, 0.4, days - 120)

        return kc

    def _compute_summary(self, results: dict[str, Any]) -> dict[str, Any]:
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
