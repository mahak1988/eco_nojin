"""
Land Intelligence Service
=========================

Main service for land analysis operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
import uuid

from engine.land import (
    LandProfile,
    TerrainAnalysis,
    DrainageAnalysis,
    CapabilityAssessment,
    DEMProcessor,
    TerrainAnalyzer,
    DrainageAnalyzer,
    CapabilityAssessor,
)

logger = logging.getLogger(__name__)


class LandService:
    """سرویس اصلی تحلیل زمین"""
    
    def __init__(self):
        """مقداردهی اولیه"""
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
        تحلیل توپوگرافی
        
        Args:
            profile_id: شناسه پروفایل
            dem_array: آرایه DEM
            resolution: وضوح (متر)
            
        Returns:
            TerrainAnalysis
        """
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile not found: {profile_id}")
        
        analyzer = TerrainAnalyzer(resolution=resolution)
        analysis = analyzer.analyze(dem_array)
        
        # Set profile ID
        analysis_dict = analysis.model_dump()
        analysis_dict["profile_id"] = profile_id
        analysis = TerrainAnalysis(**analysis_dict)
        
        # Update profile
        profile.terrain_analysis = analysis
        profile.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Terrain analysis complete for profile: {profile_id}")
        return analysis
    
    def analyze_drainage(
        self,
        profile_id: str,
        dem_array: Any,
        resolution: float,
        area_km2: Optional[float] = None
    ) -> DrainageAnalysis:
        """
        تحلیل زهکشی
        
        Args:
            profile_id: شناسه پروفایل
            dem_array: آرایه DEM
            resolution: وضوح (متر)
            area_km2: مساحت (km²)
            
        Returns:
            DrainageAnalysis
        """
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile not found: {profile_id}")
        
        analyzer = DrainageAnalyzer(resolution=resolution)
        analysis = analyzer.analyze(dem_array, area_km2=area_km2)
        
        # Set profile ID
        analysis_dict = analysis.model_dump()
        analysis_dict["profile_id"] = profile_id
        analysis = DrainageAnalysis(**analysis_dict)
        
        # Update profile
        profile.drainage_analysis = analysis
        profile.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Drainage analysis complete for profile: {profile_id}")
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
        ارزیابی قابلیت زمین
        
        Args:
            profile_id: شناسه پروفایل
            slope_degrees: شیب (درجه)
            soil_depth_m: عمق خاک (متر)
            erosion_risk: ریسک فرسایش
            drainage_class: کلاس زهکشی
            climate_zone: منطقه اقلیمی
            soil_texture: بافت خاک
            
        Returns:
            CapabilityAssessment
        """
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile not found: {profile_id}")
        
        assessor = CapabilityAssessor()
        assessment = assessor.assess(
            slope_degrees=slope_degrees,
            soil_depth_m=soil_depth_m,
            erosion_risk=erosion_risk,
            drainage_class=drainage_class,
            climate_zone=climate_zone,
            soil_texture=soil_texture
        )
        
        # Set profile ID
        assessment_dict = assessment.model_dump()
        assessment_dict["profile_id"] = profile_id
        assessment = CapabilityAssessment(**assessment_dict)
        
        # Update profile
        profile.capability_assessment = assessment
        profile.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Capability assessment complete for profile: {profile_id}")
        return assessment
    
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