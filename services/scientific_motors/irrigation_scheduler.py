"""
Hydroma Nojin - Global Irrigation Scheduler
Crop water requirement calculation and irrigation scheduling.

Science: FAO-56 Method
ETc = ET0 × Kc  (Crop evapotranspiration = Reference ET × Crop coefficient)
"""
from __future__ import annotations

# =========================================================================
# C++ Bridge Integration - Irrigation Scheduler with C++ FAO-56
# Added by fix_future_imports.py
# =========================================================================
try:
    from engine.hydroma.cpp_bridge import (
        simulate_crop_water as _cpp_crop_water,
        penman_monteith_et0 as _cpp_penman,
        is_cpp_available,
    )
    _CPP_AVAILABLE = is_cpp_available()
except ImportError:
    _CPP_AVAILABLE = False


import time
import numpy as np
import xarray as xr
from typing import Dict, Any, List
from enum import Enum

from .base import (
    AbstractScientificMotor, MotorInput, MotorOutput,
    MotorParameters, MotorResult, MotorStatus, MotorType,
)


class IrrigationSystem(Enum):
    """سیستم‌های آبیاری با راندمان جهانی"""
    SURFACE_FLOOD = ("Surface/Flood", 0.60, 500)      # راندمان 60%, هزینه $500/ha
    SPRINKLER = ("Sprinkler", 0.75, 2000)              # بارانی، $2000/ha
    CENTER_PIVOT = ("Center Pivot", 0.85, 4000)        # محور مرکزی، $4000/ha
    DRIP = ("Drip", 0.90, 3000)                        # قطره‌ای، $3000/ha
    SUBSURFACE_DRIP = ("Subsurface Drip", 0.95, 5000)  # قطره‌ای زیرسطحی، $5000/ha


# Crop coefficients (Kc) - FAO-56 standard
# Format: crop_id -> {stage: Kc}
CROP_COEFFICIENTS = {
    "wheat": {"initial": 0.40, "development": 0.90, "mid_season": 1.15, "late_season": 0.40},
    "maize": {"initial": 0.50, "development": 0.96, "mid_season": 1.20, "late_season": 0.60},
    "rice_paddy": {"initial": 1.05, "development": 1.10, "mid_season": 1.20, "late_season": 0.90},
    "soybean": {"initial": 0.40, "development": 0.90, "mid_season": 1.15, "late_season": 0.50},
    "potato": {"initial": 0.50, "development": 0.90, "mid_season": 1.15, "late_season": 0.75},
    "tomato": {"initial": 0.60, "development": 0.85, "mid_season": 1.15, "late_season": 0.80},
    "cotton": {"initial": 0.50, "development": 0.85, "mid_season": 1.15, "late_season": 0.70},
    "sorghum": {"initial": 0.40, "development": 0.90, "mid_season": 1.10, "late_season": 0.50},
    "barley": {"initial": 0.40, "development": 0.85, "mid_season": 1.10, "late_season": 0.30},
    "onion": {"initial": 0.50, "development": 0.80, "mid_season": 1.05, "late_season": 0.75},
    "alfalfa": {"initial": 0.40, "development": 0.95, "mid_season": 1.20, "late_season": 0.90},
    "sunflower": {"initial": 0.50, "development": 0.90, "mid_season": 1.10, "late_season": 0.50},
    "date_palm": {"initial": 0.65, "development": 0.85, "mid_season": 1.00, "late_season": 0.90},
    "olive": {"initial": 0.65, "development": 0.70, "mid_season": 0.70, "late_season": 0.65},
    "apple": {"initial": 0.50, "development": 0.80, "mid_season": 1.00, "late_season": 0.75},
    "default": {"initial": 0.50, "development": 0.90, "mid_season": 1.10, "late_season": 0.60},
}


class IrrigationSchedulerMotor(AbstractScientificMotor):
    """FAO-56 based irrigation scheduler."""

    @property
    def motor_type(self) -> MotorType:
        return MotorType.BIOFERTILIZER

    @property
    def display_name(self) -> str:
        return "Global Irrigation Scheduler (FAO-56)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("et0_mm_day", "raster", True, "Reference evapotranspiration ET0 (mm/day)"),
            MotorInput("soil_moisture", "raster", True, "Soil moisture (fraction)"),
            MotorInput("field_capacity", "scalar", True, "Field capacity (fraction)"),
            MotorInput("wilting_point", "scalar", True, "Wilting point (fraction)"),
            MotorInput("root_depth_m", "scalar", False, "Root zone depth (m)"),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("etc_mm_day", "raster", "mm/day", "Crop water requirement"),
            MotorOutput("irrigation_schedule", "json", "days", "Irrigation events"),
            MotorOutput("water_requirement_mm", "scalar", "mm", "Total seasonal water"),
            MotorOutput("irrigation_system_recommendation", "json", "system", "Optimal system"),
            MotorOutput("cost_estimate", "json", "USD", "Water and energy costs"),
        ]

    async def execute(self, inputs: Dict[str, Any], parameters: MotorParameters) -> MotorResult:
        start_time = time.time()
        run_id = f"IRRIG_{int(time.time())}"

        try:
            et0 = inputs.get("et0_mm_day")
            soil_moisture = inputs.get("soil_moisture")
            field_capacity = float(parameters.custom_params.get("field_capacity", 0.30))
            wilting_point = float(parameters.custom_params.get("wilting_point", 0.15))
            root_depth = float(parameters.custom_params.get("root_depth_m", 0.8))
            
            crop_id = parameters.custom_params.get("crop", "wheat")
            season_days = int(parameters.custom_params.get("season_days", 120))
            water_cost_m3 = float(parameters.custom_params.get("water_cost_per_m3", 0.05))

            if et0 is None:
                return MotorResult(run_id=run_id, motor_type=self.motor_type,
                                   status=MotorStatus.FAILED,
                                   error_message="ET0 is required")

            # Get crop coefficients
            kc_stages = CROP_COEFFICIENTS.get(crop_id, CROP_COEFFICIENTS["default"])

            # 1. Calculate ETc for full season (simplified daily simulation)
            etc_season, kc_series = self._simulate_season(
                et0, kc_stages, season_days
            )

            # 2. Soil water balance
            awc = field_capacity - wilting_point  # Available Water Capacity
            mad = awc * 0.5  # Management Allowed Depletion (50%)
            
            mean_moisture = float(np.mean(soil_moisture.values)) if soil_moisture is not None else field_capacity
            
            # 3. Generate irrigation schedule
            schedule = self._generate_schedule(
                kc_series, et0_mean=float(np.mean(et0.values)),
                soil_moisture=mean_moisture, field_capacity=field_capacity,
                wilting_point=wilting_point, root_depth=root_depth,
                season_days=season_days,
            )

            # 4. Total water requirement
            total_irrigation_mm = sum(e["amount_mm"] for e in schedule)
            gross_season_water = etc_season  # ETc total
            
            # 5. Recommend irrigation system based on water scarcity
            water_balance = gross_season_water - (season_days * float(np.mean(et0.values)) * 0.3)
            system = self._recommend_system(
                etc_season=etc_season, 
                available_water=water_balance,
                crop_id=crop_id,
            )

            # 6. Cost estimation
            water_volume_m3 = total_irrigation_mm * 10  # 1mm on 1ha = 10 m³
            efficiency = system["efficiency"]
            gross_water_m3 = water_volume_m3 / efficiency
            water_cost = gross_water_m3 * water_cost_m3
            energy_cost = gross_water_m3 * 0.15  # ~$0.15/m³ pumping
            system_cost = system["installation_cost_usd"] / 10  # 10-year amortization

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "etc_mm_day": etc_season,
                    "irrigation_schedule": schedule,
                    "water_requirement_mm": {
                        "net_crop_requirement_mm": float(etc_season),
                        "irrigation_events": len(schedule),
                        "gross_irrigation_mm": float(total_irrigation_mm / efficiency),
                        "efficiency": efficiency,
                    },
                    "irrigation_system_recommendation": system,
                    "cost_estimate": {
                        "water_volume_m3_ha": round(gross_water_m3, 1),
                        "water_cost_usd": round(water_cost, 2),
                        "energy_cost_usd": round(energy_cost, 2),
                        "system_cost_annual_usd": round(system_cost, 2),
                        "total_season_cost_usd": round(water_cost + energy_cost + system_cost, 2),
                    },
                    "kc_series_sample": kc_series[:10],
                },
                summary={
                    "crop": crop_id,
                    "season_days": season_days,
                    "total_etc_mm": float(etc_season),
                    "irrigation_events": len(schedule),
                    "recommended_system": system["name"],
                    "efficiency_percent": efficiency * 100,
                    "total_water_m3_ha": round(gross_water_m3, 0),
                    "total_cost_usd_ha": round(water_cost + energy_cost + system_cost, 2),
                },
                execution_time_seconds=time.time() - start_time,
            )

        except Exception as e:
            return MotorResult(run_id=run_id, motor_type=self.motor_type,
                               status=MotorStatus.FAILED, error_message=str(e))

    def _simulate_season(self, et0, kc_stages, season_days):
        """Simulate daily Kc and calculate ETc."""
        et0_mean = float(np.mean(et0.values))
        
        # Stage durations (FAO-56 typical proportions)
        stages = [
            ("initial", 0.15),
            ("development", 0.25),
            ("mid_season", 0.40),
            ("late_season", 0.20),
        ]
        
        kc_series = []
        etc_total = 0.0
        
        for stage_name, proportion in stages:
            days = int(season_days * proportion)
            kc = kc_stages.get(stage_name, 1.0)
            for _ in range(days):
                kc_series.append(kc)
                etc_total += et0_mean * kc
        
        # Fill remaining days
        while len(kc_series) < season_days:
            kc_series.append(kc_stages.get("late_season", 0.6))
            etc_total += et0_mean * kc_stages.get("late_season", 0.6)
        
        return etc_total, kc_series

    def _generate_schedule(self, kc_series, et0_mean, soil_moisture,
                          field_capacity, wilting_point, root_depth, season_days):
        """Generate irrigation events using simple water balance."""
        awc = field_capacity - wilting_point
        mad = awc * 0.5
        root_mm = root_depth * 1000  # Convert m to mm
        
        schedule = []
        current_moisture = soil_moisture
        cumulative_etc = 0
        
        for day, kc in enumerate(kc_series[:season_days], 1):
            etc_day = et0_mean * kc
            cumulative_etc += etc_day
            
            # Deplete soil moisture
            current_moisture -= etc_day / root_mm
            
            # Irrigate when below MAD threshold
            if current_moisture <= (field_capacity - mad):
                # Refill to field capacity
                deficit_mm = (field_capacity - current_moisture) * root_mm
                schedule.append({
                    "day": day,
                    "amount_mm": round(deficit_mm, 1),
                    "kc": kc,
                    "stage": self._get_stage(day, season_days),
                    "cumulative_mm": round(cumulative_etc, 1),
                })
                current_moisture = field_capacity
        
        return schedule

    def _get_stage(self, day, season_days):
        ratio = day / season_days
        if ratio < 0.15: return "initial"
        elif ratio < 0.40: return "development"
        elif ratio < 0.80: return "mid_season"
        else: return "late_season"

    def _recommend_system(self, etc_season, available_water, crop_id):
        """Recommend optimal irrigation system."""
        # Row crops prefer drip, field crops can use sprinkler
        row_crops = {"tomato", "potato", "onion", "cotton", "date_palm", "olive", "apple"}
        
        if etc_season > 800:  # High water need
            if crop_id in row_crops:
                sys_type = IrrigationSystem.DRIP
            else:
                sys_type = IrrigationSystem.CENTER_PIVOT
        elif etc_season > 500:
            if crop_id in row_crops:
                sys_type = IrrigationSystem.DRIP
            else:
                sys_type = IrrigationSystem.SPRINKLER
        else:
            sys_type = IrrigationSystem.SPRINKLER
        
        name, efficiency, cost = sys_type.value
        return {
            "id": sys_type.name,
            "name": name,
            "efficiency": efficiency,
            "installation_cost_usd": cost,
            "reason": self._system_reason(sys_type, etc_season, crop_id),
        }

    def _system_reason(self, system, etc_season, crop_id):
        reasons = {
            IrrigationSystem.DRIP: f"Row crop ({crop_id}) with high precision water needs",
            IrrigationSystem.CENTER_PIVOT: "Field crop with uniform water demand",
            IrrigationSystem.SPRINKLER: "Moderate water requirement, flexible",
            IrrigationSystem.SURFACE_FLOOD: "Low cost, low efficiency (not recommended)",
            IrrigationSystem.SUBSURFACE_DRIP: "Maximum efficiency for water-scarce regions",
        }
        return reasons.get(system, "General recommendation")
