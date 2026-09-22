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
    LandProfile as LandProfileModel,
    TerrainAnalysis,
)


class LandService:
    """سرویس مدیریت زمین با استفاده از آداپتور موتور"""

    def __init__(
        self,
        engine: EngineAdapter | None = None,
        db=None,
        session=None,
        persist: bool = True,
    ):
        if (
            engine is not None
            and not isinstance(engine, EngineAdapter)
            and hasattr(engine, "execute")
            and hasattr(engine, "commit")
        ):
            if db is None:
                db = engine
            engine = None
        self.engine = engine or EngineAdapter()
        self.db = db
        self.session = session
        self.persist = persist
        self._profiles: dict[str, LandProfileModel] = {}

    def create_profile(
        self,
        name: str,
        location_lat: float = 0,
        location_lon: float = 0,
        area_ha: float | None = None,
        **kwargs,
    ) -> LandProfileModel:
        """D1 fix: router passes area_hectares which used to collide in **kwargs."""
        router_area = kwargs.pop("area_hectares", None)
        if area_ha is None:
            area_ha = router_area
        profile = LandProfileModel(
            id=str(__import__("uuid").uuid4()),
            name=name,
            location_lat=location_lat,
            location_lon=location_lon,
            area_hectares=area_ha,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            **{k: v for k, v in kwargs.items() if k in LandProfileModel.model_fields},
        )
        self._profiles[profile.id] = profile
        self._persist_profile(profile)
        return profile

    # ---- D5 fix: durable storage (DB with graceful in-memory fallback) ----

    def _db_session(self):
        if not self.persist:
            return None
        try:
            from database.hub import hub

            return hub.get_session()
        except Exception as e:
            logger.warning(f"LandService: DB unavailable ({e}); using in-memory store")
            return None

    def _persist_profile(self, profile) -> None:
        cm = self._db_session()
        if cm is None:
            return
        try:
            from database.models import LandProfile as LandProfileDB

            with cm as s:
                row = s.get(LandProfileDB, profile.id)
                if row is None:
                    row = LandProfileDB(id=profile.id)
                    s.add(row)
                row.name = profile.name
                row.location_lat = profile.location_lat
                row.location_lon = profile.location_lon
                row.description = getattr(profile, "description", None)
                row.area_ha = profile.area_hectares
                row.dem_source = getattr(profile, "dem_source", None)
                row.dem_resolution_m = getattr(profile, "dem_resolution_m", None)
                s.commit()
        except Exception as e:
            logger.warning(f"LandService: profile persistence failed: {e}")

    def _row_to_profile(self, row):
        try:
            return LandProfileModel(
                id=row.id,
                name=row.name,
                description=row.description,
                location_lat=row.location_lat or 0,
                location_lon=row.location_lon or 0,
                area_hectares=row.area_ha,
                dem_source=row.dem_source,
                dem_resolution_m=row.dem_resolution_m,
            )
        except Exception as e:
            logger.warning(f"LandService: bad land_profiles row {getattr(row, 'id', '?')}: {e}")
            return None

    def get_profile(self, profile_id: str) -> LandProfileModel | None:
        profile = self._profiles.get(profile_id)
        if profile is not None:
            return profile
        cm = self._db_session()
        if cm is not None:
            try:
                from database.models import LandProfile as LandProfileDB

                with cm as s:
                    row = s.get(LandProfileDB, profile_id)
                    if row is not None:
                        profile = self._row_to_profile(row)
                        if profile is not None:
                            self._profiles[profile_id] = profile
                        return profile
            except Exception as e:
                logger.warning(f"LandService: DB get failed: {e}")
        return None

    def list_profiles(self) -> list[LandProfileModel]:
        profiles: dict[str, LandProfileModel] = {}
        cm = self._db_session()
        if cm is not None:
            try:
                from database.models import LandProfile as LandProfileDB

                with cm as s:
                    for row in (
                        s.query(LandProfileDB).order_by(LandProfileDB.created_at.desc()).all()
                    ):
                        pr = self._row_to_profile(row)
                        if pr is not None:
                            profiles[pr.id] = pr
            except Exception as e:
                logger.warning(f"LandService: DB list failed: {e}")
        for pid, pr in self._profiles.items():
            profiles[pid] = pr
        self._profiles = profiles
        return list(profiles.values())

    def delete_profile(self, profile_id: str) -> bool:
        existed = False
        cm = self._db_session()
        if cm is not None:
            try:
                from database.models import LandProfile as LandProfileDB

                with cm as s:
                    row = s.get(LandProfileDB, profile_id)
                    if row is not None:
                        s.delete(row)
                        s.commit()
                        existed = True
            except Exception as e:
                logger.warning(f"LandService: DB delete failed: {e}")
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            existed = True
        return existed

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

        logger.info(
            f"Delegating terrain analysis for profile {profile_id} to engine via interface."
        )
        analysis = self.engine.analyze_terrain(dem_array, profile_id, resolution)

        self._profiles[profile_id].terrain_analysis = analysis
        return analysis

    def analyze_drainage(
        self,
        profile_id: str,
        dem_array: Any,
        resolution: float = 30.0,
        area_km2: float | None = None,
    ) -> DrainageAnalysis:
        """تحلیل زهکشی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        logger.info(
            f"Delegating drainage analysis for profile {profile_id} to engine via interface."
        )
        analysis = self.engine.analyze_drainage(dem_array, profile_id, resolution, area_km2 or 1.0)

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
        soil_texture: str = "loam",
    ) -> CapabilityAssessment:
        """ارزیابی قابلیت اراضی با استفاده از موتور"""
        if not self._profile_exists(profile_id):
            raise ValueError("Profile not found")

        logger.info(
            f"Delegating capability assessment for profile {profile_id} to engine via interface."
        )
        assessment = self.engine.assess_capability(
            profile_id=profile_id,
            slope_degrees=slope_degrees,
            soil_depth_m=soil_depth_m,
            erosion_risk=erosion_risk,
            drainage_class=drainage_class,
            climate_zone=climate_zone,
            soil_texture=soil_texture,
        )

        self._profiles[profile_id].capability_assessment = assessment
        return assessment
