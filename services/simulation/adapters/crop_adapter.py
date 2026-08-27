"""
AquaCrop Adapter - شبیه‌ساز رشد گیاه
نسخه علمی مبتنی بر FAO-33 و FAO-56 (بدون وابستگی به aquacrop library)
"""
import math
from datetime import UTC, datetime, timedelta

from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext,
    SimulationResult,
    SimulationStatus,
    SimulationType,
)


@SimulatorRegistry.register
class AquaCropAdapter(BaseSimulator):
    simulator_type = SimulationType.CROP_GROWTH
    name = "FAO-CropSim"
    version = "1.0.0"

    CROP_DB = {
        "wheat": {"yield": 4.5, "duration": 150, "kc": 0.85, "hi": 0.45},
        "barley": {"yield": 4.0, "duration": 130, "kc": 0.80, "hi": 0.45},
        "maize": {"yield": 8.0, "duration": 120, "kc": 0.95, "hi": 0.50},
        "rice": {"yield": 6.5, "duration": 140, "kc": 1.10, "hi": 0.45},
        "soybean": {"yield": 3.0, "duration": 110, "kc": 0.85, "hi": 0.40},
        "cotton": {"yield": 2.5, "duration": 180, "kc": 0.90, "hi": 0.35},
        "potato": {"yield": 25.0, "duration": 100, "kc": 0.90, "hi": 0.70},
        "tomato": {"yield": 40.0, "duration": 90, "kc": 0.95, "hi": 0.60},
        "alfalfa": {"yield": 12.0, "duration": 240, "kc": 0.95, "hi": 0.90},
        "olive": {"yield": 8.0, "duration": 365, "kc": 0.70, "hi": 0.30},
        "pistachio": {"yield": 2.5, "duration": 365, "kc": 0.70, "hi": 0.25},
        "walnut": {"yield": 3.0, "duration": 365, "kc": 0.75, "hi": 0.30},
        "pomegranate": {"yield": 15.0, "duration": 365, "kc": 0.70, "hi": 0.40},
    }

    async def validate_context(self, ctx: SimulationContext) -> list[str]:
        errors = []
        if not ctx.crop:
            errors.append("Crop parameters required")
        if not ctx.soil:
            errors.append("Soil profile required")
        return errors

    async def run(self, ctx: SimulationContext) -> SimulationResult:
        crop_type = ctx.crop.crop_type.lower()
        crop_data = self.CROP_DB.get(crop_type, {"yield": 5.0, "duration": 120, "kc": 0.85, "hi": 0.45})

        base_yield = crop_data["yield"]
        duration = crop_data["duration"]
        kc = crop_data["kc"]
        hi = crop_data["hi"]

        # فاکتورهای تعدیل
        soil_factor = self._soil_factor(ctx.soil)
        water_factor = self._water_factor(ctx.weather.precipitation_mm)
        climate_factor = self._climate_factor(ctx.weather)

        final_yield = base_yield * soil_factor * water_factor * climate_factor
        biomass = final_yield / hi

        # نیاز آبی
        et0_daily = self._et0_hargreaves(ctx.weather)
        total_water = et0_daily * kc * duration
        wue = (final_yield * 1000) / total_water if total_water > 0 else 0

        # تاریخ برداشت
        harvest_date = None
        if ctx.crop.planting_date:
            harvest_date = (ctx.crop.planting_date + timedelta(days=duration)).isoformat()

        # Time series (منحنی رشد logistic)
        time_series = []
        months = max(1, duration // 30)
        for m in range(1, months + 1):
            stage = m / months
            growth = 1 / (1 + math.exp(-10 * (stage - 0.5)))
            time_series.append({
                "month": m,
                "stage": round(stage, 2),
                "growth": round(growth, 3),
                "cumulative_yield": round(final_yield * growth, 2),
            })

        return SimulationResult(
            simulation_id=ctx.simulation_id,
            simulation_type=self.simulator_type,
            status=SimulationStatus.COMPLETED,
            started_at=datetime.now(UTC),
            summary={
                "crop_type": crop_type,
                "yield_ton_ha": round(final_yield, 2),
                "biomass_ton_ha": round(biomass, 2),
                "harvest_index": hi,
                "crop_duration_days": duration,
                "total_irrigation_mm": round(total_water, 1),
                "water_use_efficiency_kg_m3": round(wue, 2),
                "harvest_date": harvest_date,
                "soil_factor": round(soil_factor, 3),
                "water_factor": round(water_factor, 3),
                "climate_factor": round(climate_factor, 3),
            },
            time_series=time_series,
        )

    def _soil_factor(self, soil) -> float:
        oc_bonus = min(1.2, 0.7 + soil.organic_carbon_pct * 0.15)
        texture = {
            "loam": 1.0, "silt_loam": 1.05, "clay_loam": 0.95,
            "sandy_loam": 0.85, "clay": 0.80, "sand": 0.70,
        }.get(soil.texture.lower(), 0.90)
        return oc_bonus * texture

    def _water_factor(self, precipitation: float) -> float:
        if precipitation >= 500: return 1.0
        if precipitation >= 300: return 0.85
        if precipitation >= 150: return 0.70
        return 0.55

    def _climate_factor(self, weather) -> float:
        avg = (weather.temp_min_c + weather.temp_max_c) / 2
        if 18 <= avg <= 28: return 1.0
        if 12 <= avg < 18 or 28 < avg <= 32: return 0.85
        return 0.65

    def _et0_hargreaves(self, weather) -> float:
        tr = weather.temp_max_c - weather.temp_min_c
        ta = (weather.temp_max_c + weather.temp_min_c) / 2
        ra = weather.solar_radiation_mj_m2 if weather.solar_radiation_mj_m2 > 0 else 15.0
        et0 = 0.0023 * ra * math.sqrt(max(0, tr)) * (ta + 17.8)
        return max(0.5, et0)
