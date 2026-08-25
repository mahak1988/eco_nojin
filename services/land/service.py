"""
خدمات مدیریت زمین (Land Service)
نسخه استاندارد با استفاده از موتور واقعی
"""

from datetime import datetime, timezone
from typing import Any, Optional, List
from adapters.engine_adapter import EngineAdapter
from services.land.land_profile import (
    LandProfile,
    TerrainAnalysis,
    DrainageAnalysis,
    CapabilityAssessment,
)

class LandService:
    """سرویس مدیریت زمین با استفاده از آداپتور موتور"""

    def __init__(self, engine: Optional[EngineAdapter] = None, db=None, session=None):
        self.engine = engine or EngineAdapter()
        self.db = db
        self.session = session
        self._profiles = {}  # id -> LandProfile

    def create_profile(
        self,
        name: str,
        location_lat: float = 0,
        location_lon: float = 0,
        area_ha: Optional[float] = None,
        **kwargs
    ) -> LandProfile:
        """ایجاد پروفایل جدید"""
        profile = LandProfile(
            name=name,
            location_lat=location_lat,
            location_lon=location_lon,
            area_ha=area_ha,
            **kwargs
        )
        self._profiles[profile.id] = profile
        return profile

    def get_profile(self, profile_id: str) -> Optional[LandProfile]:
        """دریافت پروفایل با شناسه"""
        return self._profiles.get(profile_id)

    def list_profiles(self) -> List[LandProfile]:
        """فهرست پروفایل‌ها"""
        return list(self._profiles.values())

    def delete_profile(self, profile_id: str) -> bool:
        """حذف پروفایل"""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            return True
        return False

    def _profile_exists(self, profile_id: str) -> bool:
        """بررسی وجود پروفایل"""
        return profile_id in self._profiles

    def analyze_terrain(
        self,
        profile_id: str,
        dem_array: Any,
        resolution: float
    ) -> TerrainAnalysis:
        """تحلیل توپوگرافی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        print(f"Delegating terrain analysis for profile {profile_id} to engine via interface.")
        engine_results = self.engine.analyze_terrain(dem_array, profile_id)

        analysis = TerrainAnalysis(
            profile_id=profile_id,
            terrain_type=engine_results.get('terrain_type', 'unknown'),
            elevation_min=engine_results.get('elevation_min', 0.0),
            elevation_max=engine_results.get('elevation_max', 0.0),
            elevation_mean=engine_results.get('elevation_mean', 0.0),
            slope_mean=engine_results.get('slope_mean', 0.0),
            slope_max=engine_results.get('slope_max', 0.0),
            aspect_dominant=engine_results.get('aspect_dominant', 0.0),
            mean_slope_degrees=engine_results.get('slope_mean', 0.0),
            dominant_aspect_degrees=engine_results.get('aspect_dominant', 0.0),
            analysis_data=engine_results,
            analyzed_at=datetime.now(timezone.utc)
        )
        self._profiles[profile_id].terrain_analysis = analysis
        return analysis

    def analyze_drainage(
        self,
        profile_id: str,
        dem_array: Any,
        resolution: float,
        area_km2: Optional[float] = None
    ) -> DrainageAnalysis:
        """تحلیل زهکشی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        print(f"Delegating drainage analysis for profile {profile_id} to engine via interface.")
        engine_results = self.engine.analyze_drainage(
            dem_array, profile_id, resolution, area_km2 or 1.0
        )

        analysis = DrainageAnalysis(
            profile_id=profile_id,
            drainage_pattern=engine_results.get('drainage_pattern', 'dendritic'),
            drainage_density=engine_results.get('drainage_density', 0.0),
            density_class=engine_results.get('density_class', 'low'),
            stream_orders=engine_results.get('stream_orders', []),
            stream_order_max=engine_results.get('stream_order_max', 0),
            bifurcation_ratio=engine_results.get('bifurcation_ratio', 0.0),
            flow_accumulation=engine_results.get('flow_accumulation', []),
            watershed_area_km2=area_km2 or 1.0,
            time_of_concentration_hours=engine_results.get('time_of_concentration_hours', 0.0),
            main_channel_length_km=engine_results.get('main_channel_length_km', 0.0),
            analyzed_at=datetime.now(timezone.utc)
        )
        self._profiles[profile_id].drainage_analysis = analysis
        return analysis

    def assess_capability(
        self,
        profile_id: str,
        slope_degrees: float,
        soil_depth_m: Optional[float] = None,
        erosion_risk: str = "low",
        drainage_class: str = "well_drained",
        climate_zone: str = "temperate",
        soil_texture: str = "loam"
    ) -> CapabilityAssessment:
        """ارزیابی قابلیت اراضی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        print(f"Delegating capability assessment for profile {profile_id} to engine via interface.")
        engine_results = self.engine.assess_capability(
            profile_id=profile_id,
            slope_degrees=slope_degrees,
            soil_depth_m=soil_depth_m,
            erosion_risk=erosion_risk,
            drainage_class=drainage_class,
            climate_zone=climate_zone,
            soil_texture=soil_texture
        )

        assessment = CapabilityAssessment(
            profile_id=profile_id,
            capability_class=engine_results.get('class', 'I'),
            confidence_score=engine_results.get('confidence_score', 0.8),
            limitations=engine_results.get('limitations', []),
            analysis_data=engine_results,
            assessed_at=datetime.now(timezone.utc)
        )
        self._profiles[profile_id].capability_assessment = assessment
        return assessment
