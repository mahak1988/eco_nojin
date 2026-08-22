"""
Earthwork & Infrastructure Calculator
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class PondDesign:
    volume_m3: float
    surface_area_m2: float
    depth_m: float
    embankment_volume_m3: float

def design_storage_pond(daily_demand_m3: float, autonomy_days: int, evaporation_mm_day: float, surface_area_m2: float) -> PondDesign:
    """طراحی استخر ذخیره آب"""
    storage = daily_demand_m3 * autonomy_days
    evaporation_loss = (evaporation_mm_day / 1000) * surface_area_m2 * autonomy_days
    total_volume = storage + evaporation_loss
    depth = total_volume / surface_area_m2 if surface_area_m2 > 0 else 0
    return PondDesign(
        volume_m3=total_volume,
        surface_area_m2=surface_area_m2,
        depth_m=depth,
        embankment_volume_m3=surface_area_m2 * depth * 0.3  # تخمین ساده
    )
