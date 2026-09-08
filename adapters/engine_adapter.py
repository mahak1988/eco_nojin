"""
آداپتور موتور زمین - استاندارد شده با مدل‌های Pydantic
"""
from typing import Any
from engine.land.terrain_analysis import TerrainAnalyzer
from engine.land.drainage import DrainageAnalyzer
from engine.land.capability import assess_land_capability
from engine.land.models import (
    CapabilityAssessment,
    DrainageAnalysis,
    TerrainAnalysis,
)


class EngineAdapter:
    """آداپتور برای اتصال سرویس‌ها به موتور زمین"""

    def analyze_terrain(self, dem_array: Any, profile_id: str, resolution: float = 30.0) -> TerrainAnalysis:
        """تحلیل توپوگرافی - بازگرداندن مدل TerrainAnalysis"""
        analyzer = TerrainAnalyzer(resolution=resolution)
        return analyzer.analyze(dem_array, profile_id=profile_id)

    def analyze_drainage(
        self,
        dem_array: Any,
        profile_id: str,
        resolution: float = 30.0,
        area_km2: float = 1.0,
    ) -> DrainageAnalysis:
        """تحلیل زهکشی - بازگرداندن مدل DrainageAnalysis"""
        analyzer = DrainageAnalyzer(resolution=resolution)
        return analyzer.analyze(dem_array, profile_id=profile_id, area_km2=area_km2)

    def assess_capability(
        self,
        profile_id: str,
        slope_degrees: float,
        soil_depth_m: float | None = None,
        erosion_risk: str = "low",
        drainage_class: str = "well_drained",
        climate_zone: str = "temperate",
        soil_texture: str = "loam"
    ) -> CapabilityAssessment:
        """ارزیابی قابلیت - بازگرداندن مدل CapabilityAssessment"""
        return assess_land_capability(
            profile_id=profile_id,
            slope_degrees=slope_degrees,
            soil_depth_m=soil_depth_m,
            erosion_risk=erosion_risk,
            drainage_class=drainage_class,
            climate_zone=climate_zone,
            soil_texture=soil_texture
        )
