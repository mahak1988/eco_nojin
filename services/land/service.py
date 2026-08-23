"""
Land Intelligence Service
=========================

Main service for land analysis operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
import uuid

# --- تغییرات اعمال شده در واردات ---
# حذف واردات مستقیم از engine/land و engine/hydroma
# from engine.land import (...)
# from engine.hydroma.soil.salinity import ...
# from engine.hydroma.climate.et_calculator import ...
from interfaces.land_engine_interface import ILandEngine
from interfaces.hydroma_engine_interface import IHydromaEngine
from adapters.engine_adapter import EngineAdapter # Import default adapter for initialization
from adapters.hydroma_adapter import HydromaAdapter # Import default adapter for initialization

# برای مدل‌های پایه، موقتاً از Pydantic استفاده می‌کنیم یا یک مدل ساده تعریف می‌کنیم
from pydantic import BaseModel

class LandProfile(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    location_lat: float
    location_lon: float
    area_hectares: Optional[float] = None
    dem_source: Optional[str] = None
    dem_resolution_m: Optional[float] = None
    created_by: Optional[str] = None
    terrain_analysis: Optional[dict] = None
    drainage_analysis: Optional[dict] = None
    capability_assessment: Optional[dict] = None
    soil_analysis: Optional[dict] = None # افزودن فیلد تحلیل خاک
    climate_analysis: Optional[dict] = None # افزودن فیلد تحلیل اقلیم
    surface_water_analysis: Optional[dict] = None # افزودن فیلد تحلیل آب سطحی
    watershed_analysis: Optional[dict] = None # افزودن فیلد تحلیل آبخیز
    groundwater_analysis: Optional[dict] = None # افزودن فیلد تحلیل آب زیرزمینی
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

class TerrainAnalysis(BaseModel):
    profile_id: str
    mean_slope_degrees: float
    dominant_aspect_degrees: float
    analysis_data: dict

class DrainageAnalysis(BaseModel):
    profile_id: str
    flow_directions: Any # نوع واقعی بستگی به پیاده‌سازی دارد
    stream_order: int

class CapabilityAssessment(BaseModel):
    profile_id: str
    class_: str # استفاده از class_ چون class کلمه کلیدی است
    subclass: Optional[str] = None
    limitations: List[str] = []



logger = logging.getLogger(__name__)


class LandService:
    """سرویس اصلی تحلیل زمین"""
    
    def __init__(self, engine: Optional[ILandEngine] = None, hydroma_engine: Optional[IHydromaEngine] = None):
        """مقداردهی اولیه"""
        # Use provided engines or default to Adapters
        self.engine = engine if engine else EngineAdapter()
        self.hydroma_engine = hydroma_engine if hydroma_engine else HydromaAdapter()
        self.profiles: Dict[str, LandProfile] = {}
        
    def create_profile(
        self,
        name: str,
        location_lat: float,
        location_lon: float,
        description: Optional[str] = None,
        area_hectares: Optional[float] = None,
        dem_source: Optional[str] = None,
        dem_resolution_m: Optional[float] = None,
        created_by: Optional[str] = None
    ) -> LandProfile:
        """
        ایجاد پروفایل زمین جدید
        
        Args:
            name: نام زمین
            location_lat: عرض جغرافیایی
            location_lon: طول جغرافیایی
            description: توضیحات
            area_hectares: مساحت (هکتار)
            dem_source: منبع DEM
            dem_resolution_m: وضوح DEM
            created_by: ایجادکننده
            
        Returns:
            LandProfile ایجاد شده
        """
        profile_id = str(uuid.uuid4())
        
        profile = LandProfile(
            id=profile_id,
            name=name,
            description=description,
            location_lat=location_lat,
            location_lon=location_lon,
            area_hectares=area_hectares,
            dem_source=dem_source,
            dem_resolution_m=dem_resolution_m,
            created_by=created_by
        )
        
        self.profiles[profile_id] = profile
        logger.info(f"Created land profile: {profile_id} ({name})")
        
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[LandProfile]:
        """
        دریافت پروفایل زمین
        
        Args:
            profile_id: شناسه پروفایل
            
        Returns:
            LandProfile یا None
        """
        return self.profiles.get(profile_id)
    
    def list_profiles(self) -> List[LandProfile]:
        """
        لیست تمام پروفایل‌ها
        
        Returns:
            لیست LandProfile
        """
        return list(self.profiles.values())
    
    def analyze_terrain(self, profile_id: str, dem_array: Any, resolution: float) -> TerrainAnalysis:
        """
        تحلیل توپوگرافی (تابع ساختگی برای این مرحله)
        این تابع باید با استفاده از DEMProcessor و SlopeAspectAnalyzer کار کند.
        """
        # اکنون از موتور وابسته به رابط استفاده می‌کند
        print(f"Delegating terrain analysis for profile {profile_id} to engine via interface.")
        engine_results = self.engine.analyze_terrain(dem_array, profile_id)
        
        # Parse results from engine (which now returns a dict)
        mean_slope = engine_results.get('slope_mean', 10.0) # Example key from engine output
        dominant_aspect = engine_results.get('aspect_dominant', 180.0) # Example key from engine output

        analysis = TerrainAnalysis(
            profile_id=profile_id,
            mean_slope_degrees=mean_slope, # مقدار نمونه
            dominant_aspect_degrees=dominant_aspect, # مقدار نمونه
            analysis_data=engine_results # Pass the full dict from engine
        )
        profile = self.get_profile(profile_id)
        if profile:
            profile.terrain_analysis = analysis.model_dump()
            profile.updated_at = datetime.now(timezone.utc)
        return analysis
    
    def analyze_drainage(
        self,
        profile_id: str,
        dem_array: Any,
        resolution: float,
        area_km2: Optional[float] = None
    ) -> DrainageAnalysis:
        """
        تحلیل زهکشی (تابع ساختگی برای این مرحله)
        """
        print(f"Delegating drainage analysis for profile {profile_id} to engine via interface.")
        engine_results = self.engine.analyze_drainage(dem_array, profile_id)
        # Parse results similarly...
        analysis = DrainageAnalysis(
            profile_id=profile_id,
            flow_directions=engine_results.get('flow_directions', []), # مقدار نمونه
            stream_order=engine_results.get('stream_order', 1) # مقدار نمونه
        )
        profile = self.get_profile(profile_id)
        if profile:
            profile.drainage_analysis = analysis.model_dump()
            profile.updated_at = datetime.now(timezone.utc)
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
        """
        ارزیابی قابلیت زمین (تابع ساختگی برای این مرحله)
        """
        print(f"Delegating capability assessment for profile {profile_id} to engine via interface.")
        engine_results = self.engine.assess_capability(
            slope_degrees, soil_depth_m, erosion_risk, drainage_class, climate_zone, soil_texture
        )
        # Parse results from engine
        cap_class = engine_results.get('class_', 'Class I')

        assessment = CapabilityAssessment(
            profile_id=profile_id,
            class_=cap_class,
            limitations=engine_results.get('limitations', ["slope" if slope_degrees > 15 else "none"])
        )
        profile = self.get_profile(profile_id)
        if profile:
            profile.capability_assessment = assessment.model_dump()
            profile.updated_at = datetime.now(timezone.utc)
        return assessment

    # --- توابع جدید برای فاز ۳: آب، آبخیزداری و آب زیرزمینی ---
    def analyze_surface_water(self, profile_id: str, dem_file_path: str) -> Optional[dict]:
        """
        تحلیل اولیه منابع آب سطحی با استفاده از DEM.
        """
        profile = self.get_profile(profile_id)
        if not profile:
            logger.error(f"Profile {profile_id} not found for surface water analysis.")
            return None

        print(f"Delegating surface water analysis for profile {profile_id} to engine via interface.")
        try:
            # Call the engine's surface water analysis method via the interface
            engine_results = self.engine.analyze_surface_water(dem_file_path)

            surface_water_analysis = {
                "profile_id": profile_id,
                "results": engine_results,
                "method": "DEM_based_flow_proxy_via_adapter"
            }
            profile.surface_water_analysis = surface_water_analysis
            profile.updated_at = datetime.now(timezone.utc)
            logger.info(f"Surface water analysis completed for profile {profile_id}.")
            return surface_water_analysis
        except Exception as e:
            logger.error(f"Error in surface water analysis for profile {profile_id}: {e}")
            return None

    def analyze_watershed(self, profile_id: str, slope_pct: float, area_m2: float, rainfall_mm: float = 100) -> Optional[dict]:
        """
        تحلیل اولیه آبخیز و طراحی سازه‌های آبخیزداری.
        """
        # Now delegates to the hydroma_engine via its interface
        print(f"Delegating watershed analysis for profile {profile_id} to hydroma engine via interface.")
        try:
            engine_results = self.hydroma_engine.analyze_watershed(slope_pct, area_m2, rainfall_mm)

            watershed_analysis = {
                "profile_id": profile_id,
                "design_proposal": engine_results.get("design_proposal"),
                "input_data": engine_results.get("input_data")
            }
            profile = self.get_profile(profile_id)
            if profile:
                profile.watershed_analysis = watershed_analysis
                profile.updated_at = datetime.now(timezone.utc)
            logger.info(f"Watershed analysis completed for profile {profile_id}.")
            return watershed_analysis
        except Exception as e:
            logger.error(f"Error in watershed analysis for profile {profile_id}: {e}")
            return None

    def analyze_groundwater(self, profile_id: str, gw_data: Dict[str, Any]) -> Optional[dict]:
        """
        تحلیل اولیه آب زیرزمینی (Placeholder).
        """
        # Now delegates to the hydroma_engine via its interface
        print(f"Delegating groundwater analysis for profile {profile_id} to hydroma engine via interface.")
        try:
            engine_results = self.hydroma_engine.analyze_groundwater(gw_data)

            groundwater_analysis = {
                "profile_id": profile_id,
                "estimated_depth_m": engine_results.get("estimated_depth_m"),
                "quality_class": engine_results.get("quality_class"),
                "input_data": engine_results.get("input_data")
            }
            profile = self.get_profile(profile_id)
            if profile:
                profile.groundwater_analysis = groundwater_analysis
                profile.updated_at = datetime.now(timezone.utc)
            logger.info(f"Groundwater analysis (via adapter) completed for profile {profile_id}.")
            return groundwater_analysis
        except Exception as e:
            logger.error(f"Error in groundwater analysis for profile {profile_id}: {e}")
            return None
    
    # --- توابع جدید برای اتصال به خاک و اقلیم ---
    def analyze_soil(self, profile_id: str, soil_data: Dict[str, Any]) -> Optional[dict]:
        """
        تحلیل اولیه خاک با استفاده از ماژول‌های Hydroma.
        """
        # Now delegates to the hydroma_engine via its interface
        print(f"Delegating soil analysis for profile {profile_id} to hydroma engine via interface.")
        try:
            engine_results = self.hydroma_engine.analyze_soil(soil_data)

            soil_analysis = {
                "profile_id": profile_id,
                "salinity_classification": engine_results.get("salinity_classification"),
                "texture_class": engine_results.get("texture_class"),
                "calculated_properties": engine_results.get("calculated_properties")
            }
            profile = self.get_profile(profile_id)
            if profile:
                profile.soil_analysis = soil_analysis
                profile.updated_at = datetime.now(timezone.utc)
            logger.info(f"Soil analysis (via adapter) completed for profile {profile_id}.")
            return soil_analysis
        except Exception as e:
            logger.error(f"Error in soil analysis for profile {profile_id}: {e}")
            return None

    def analyze_climate(self, profile_id: str, climate_data: Dict[str, Any]) -> Optional[dict]:
        """
        تحلیل اولیه اقلیم با استفاده از ماژول‌های Hydroma.
        """
        # Now delegates to the hydroma_engine via its interface
        print(f"Delegating climate analysis for profile {profile_id} to hydroma engine via interface.")
        try:
            engine_results = self.hydroma_engine.analyze_climate(climate_data)

            climate_analysis = {
                "profile_id": profile_id,
                "estimated_et0": engine_results.get("estimated_et0"),
                "input_data": engine_results.get("input_data"),
                "method": engine_results.get("method")
            }
            profile = self.get_profile(profile_id)
            if profile:
                profile.climate_analysis = climate_analysis
                profile.updated_at = datetime.now(timezone.utc)
            logger.info(f"Climate analysis (via adapter) completed for profile {profile_id}.")
            return climate_analysis
        except Exception as e:
            logger.error(f"Error in climate analysis for profile {profile_id}: {e}")
            return None
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        حذف پروفایل زمین
        
        Args:
            profile_id: شناسه پروفایل
            
        Returns:
            True اگر حذف شد
        """
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            logger.info(f"Deleted land profile: {profile_id}")
            return True
        return False