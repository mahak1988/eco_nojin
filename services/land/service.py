"""
خدمات مدیریت زمین (Land Service)
نسخه استاندارد با استفاده از موتور واقعی
"""

import structlog

logger = structlog.get_logger()
from datetime import UTC, datetime
from typing import Any

from adapters.engine_adapter import EngineAdapter
from engine.land.models import (
    CapabilityAssessment,
    DrainageAnalysis,
    TerrainAnalysis,
)


class LandProfile:
    """مدل پروفایل زمین"""
    def __init__(self, name: str, location_lat: float = 0.0, location_lon: float = 0.0, area_ha: float | None = None, **kwargs):
        self.id = str(__import__('uuid').uuid4())
        self.name = name
        self.location_lat = location_lat
        self.location_lon = location_lon
        self.area_ha = area_ha
        self.terrain_analysis: TerrainAnalysis | None = None
        self.drainage_analysis: DrainageAnalysis | None = None
        self.capability_assessment: CapabilityAssessment | None = None
        self.created_at = datetime.now(UTC)
        for key, value in kwargs.items():
            setattr(self, key, value)


class LandService:
    """سرویس مدیریت زمین با استفاده از آداپتور موتور"""

    def __init__(self, engine: EngineAdapter | None = None, db=None, session=None):
        self.engine = engine or EngineAdapter()
        self.db = db
        self.session = session
        self._profiles: dict[str, LandProfile] = {}

    def create_profile(
        self,
        name: str,
        location_lat: float = 0,
        location_lon: float = 0,
        area_ha: float | None = None,
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

    def get_profile(self, profile_id: str) -> LandProfile | None:
        """دریافت پروفایل با شناسه"""
        return self._profiles.get(profile_id)

    def list_profiles(self) -> list[LandProfile]:
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
        resolution: float = 30.0,
    ) -> TerrainAnalysis:
        """تحلیل توپوگرافی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        logger.info(f"Delegating terrain analysis for profile {profile_id} to engine via interface.")
        analysis = self.engine.analyze_terrain(dem_array, profile_id, resolution)

        self._profiles[profile_id].terrain_analysis = analysis
        return analysis

    def analyze_drainage(
        self,
        profile_id: str,
        dem_array: Any,
        resolution: float = 30.0,
        area_km2: float | None = None
    ) -> DrainageAnalysis:
        """تحلیل زهکشی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        logger.info(f"Delegating drainage analysis for profile {profile_id} to engine via interface.")
        analysis = self.engine.analyze_drainage(
            dem_array, profile_id, resolution, area_km2 or 1.0
        )

        self._profiles[profile_id].drainage_analysis = analysis
        return analysis

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
        """ارزیابی قابلیت اراضی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        logger.info(f"Delegating capability assessment for profile {profile_id} to engine via interface.")
        assessment = self.engine.assess_capability(
            profile_id=profile_id,
            slope_degrees=slope_degrees,
            soil_depth_m=soil_depth_m,
            erosion_risk=erosion_risk,
            drainage_class=drainage_class,
            climate_zone=climate_zone,
            soil_texture=soil_texture
        )

        self._profiles[profile_id].capability_assessment = assessment
        return assessment
