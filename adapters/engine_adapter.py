"""
آداپتور موتور زمین
"""
from typing import Any, Dict, Optional
from engine.land.terrain_analysis import calculate_terrain_metrics
from engine.land.drainage import calculate_drainage_metrics
from engine.land.capability import assess_land_capability

class EngineAdapter:
    """آداپتور برای اتصال سرویس‌ها به موتور زمین"""

    def analyze_terrain(self, dem_array: Any, profile_id: str) -> Dict[str, Any]:
        """تحلیل توپوگرافی"""
        result = calculate_terrain_metrics(dem_array)
        result['profile_id'] = profile_id
        return result

    def analyze_drainage(
        self,
        dem_array: Any,
        profile_id: str,
        resolution: float,
        area_km2: float
    ) -> Dict[str, Any]:
        """تحلیل زهکشی"""
        result = calculate_drainage_metrics(
            dem_array,
            resolution=resolution,
            area_km2=area_km2
        )
        result['profile_id'] = profile_id
        return result

    def assess_capability(
        self,
        profile_id: str,
        slope_degrees: float,
        soil_depth_m: Optional[float] = None,
        erosion_risk: str = "low",
        drainage_class: str = "well_drained",
        climate_zone: str = "temperate",
        soil_texture: str = "loam"
    ) -> Dict[str, Any]:
        """ارزیابی قابلیت"""
        result = assess_land_capability(
            slope_degrees=slope_degrees,
            soil_depth_m=soil_depth_m,
            erosion_risk=erosion_risk,
            drainage_class=drainage_class,
            climate_zone=climate_zone,
            soil_texture=soil_texture
        )
        result['profile_id'] = profile_id
        return result
