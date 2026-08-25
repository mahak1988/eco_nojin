"""
Land Intelligence API Router
============================

REST API endpoints for land analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.land.service import LandService
from engine.land.models import (
    LandProfile,
    TerrainAnalysis,
    DrainageAnalysis,
    CapabilityAssessment,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/land", tags=["land"])

# Service instance (in production, use dependency injection)
land_service = LandService()


# ============================================================================
# Request/Response Models
# ============================================================================



def _map_terrain_type(slope_mean_deg: float) -> str:
    """نگاشت شیب متوسط به نوع زمین"""
    if slope_mean_deg < 2:
        return "flat"
    elif slope_mean_deg < 5:
        return "nearly_flat"
    elif slope_mean_deg < 10:
        return "gentle"
    elif slope_mean_deg < 15:
        return "rolling"
    elif slope_mean_deg < 25:
        return "hilly"
    elif slope_mean_deg < 35:
        return "mountainous"
    elif slope_mean_deg < 45:
        return "steep"
    else:
        return "very_steep"

def _format_aspect(aspect_deg: float) -> str:
    """تبدیل جهت به رشته قطبنما"""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    idx = int((aspect_deg % 360) / 45) % 8
    return directions[idx]

class CreateProfileRequest(BaseModel):
    """درخواست ایجاد پروفایل"""
    name: str = Field(..., description="نام زمین")
    location_lat: float = Field(..., ge=-90, le=90, description="عرض جغرافیایی")
    location_lon: float = Field(..., ge=-180, le=180, description="طول جغرافیایی")
    description: Optional[str] = Field(None, description="توضیحات")
    area_hectares: Optional[float] = Field(None, ge=0, description="مساحت (هکتار)")
    dem_source: Optional[str] = Field(None, description="منبع DEM")
    dem_resolution_m: Optional[float] = Field(None, ge=0, description="وضوح DEM (متر)")


class AnalyzeTerrainRequest(BaseModel):
    """درخواست تحلیل توپوگرافی"""
    dem_array: List[List[float]] = Field(..., description="آرایه DEM")
    resolution: float = Field(..., gt=0, description="وضوح (متر)")


class AnalyzeDrainageRequest(BaseModel):
    """درخواست تحلیل زهکشی"""
    dem_array: List[List[float]] = Field(..., description="آرایه DEM")
    resolution: float = Field(..., gt=0, description="وضوح (متر)")
    area_km2: Optional[float] = Field(None, gt=0, description="مساحت (km²)")


class AssessCapabilityRequest(BaseModel):
    """درخواست ارزیابی قابلیت"""
    slope_degrees: float = Field(..., ge=0, le=90, description="شیب (درجه)")
    soil_depth_m: Optional[float] = Field(None, ge=0, description="عمق خاک (متر)")
    erosion_risk: str = Field("low", description="ریسک فرسایش")
    drainage_class: str = Field("well_drained", description="کلاس زهکشی")
    climate_zone: str = Field("temperate", description="منطقه اقلیمی")
    soil_texture: str = Field("loam", description="بافت خاک")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/profiles", operation_id="create_land_profile", response_model=LandProfile, status_code=status.HTTP_201_CREATED)
async def create_profile(request: CreateProfileRequest):
    """
    ایجاد پروفایل زمین جدید
    
    Creates a new land profile with basic information.
    """
    try:
        profile = land_service.create_profile(
            name=request.name,
            location_lat=request.location_lat,
            location_lon=request.location_lon,
            description=request.description,
            area_hectares=request.area_hectares,
            dem_source=request.dem_source,
            dem_resolution_m=request.dem_resolution_m
        )
        
        logger.info(f"Created profile via API: {profile.id}")
        return profile
        
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/profiles", operation_id="list_land_profiles", response_model=List[LandProfile])
async def list_profiles():
    """
    لیست تمام پروفایل‌های زمین
    
    Returns all land profiles.
    """
    try:
        profiles = land_service.list_profiles()
        return profiles
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/profiles/{profile_id}", operation_id="get_land_profile", response_model=LandProfile)
async def get_profile(profile_id: str):
    """
    دریافت پروفایل زمین
    
    Returns a specific land profile by ID.
    """
    profile = land_service.get_profile(profile_id)
    
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found: {profile_id}"
        )
    
    return profile


@router.delete("/profiles/{profile_id}", operation_id="delete_land_profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: str):
    """
    حذف پروفایل زمین
    
    Deletes a land profile by ID.
    """
    deleted = land_service.delete_profile(profile_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found: {profile_id}"
        )
    
    return None


@router.post("/profiles/{profile_id}/terrain-analysis", operation_id="analyze_land_terrain", response_model=TerrainAnalysis)
async def analyze_terrain(profile_id: str, request: AnalyzeTerrainRequest):
    """
    تحلیل توپوگرافی
    
    Performs comprehensive terrain analysis on DEM data.
    """
    import numpy as np
    
    profile = land_service.get_profile(profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found: {profile_id}"
        )
    
    try:
        dem_array = np.array(request.dem_array)
        
        analysis = land_service.analyze_terrain(
            profile_id=profile_id,
            dem_array=dem_array,
            resolution=request.resolution
        )
        
        logger.info(f"Terrain analysis via API: {profile_id}")
        return analysis
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in terrain analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/profiles/{profile_id}/drainage-analysis", operation_id="analyze_land_drainage", response_model=DrainageAnalysis)
async def analyze_drainage(profile_id: str, request: AnalyzeDrainageRequest):
    """
    تحلیل زهکشی
    
    Performs drainage pattern and flow accumulation analysis.
    """
    import numpy as np
    
    profile = land_service.get_profile(profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found: {profile_id}"
        )
    
    try:
        dem_array = np.array(request.dem_array)
        
        analysis = land_service.analyze_drainage(
            profile_id=profile_id,
            dem_array=dem_array,
            resolution=request.resolution,
            area_km2=request.area_km2
        )
        
        logger.info(f"Drainage analysis via API: {profile_id}")
        return analysis
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in drainage analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/profiles/{profile_id}/capability-assessment", operation_id="assess_land_capability", response_model=CapabilityAssessment)
async def assess_capability(profile_id: str, request: AssessCapabilityRequest):
    """
    ارزیابی قابلیت زمین
    
    Evaluates land capability for various uses based on physical characteristics.
    """
    profile = land_service.get_profile(profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found: {profile_id}"
        )
    
    try:
        assessment = land_service.assess_capability(
            profile_id=profile_id,
            slope_degrees=request.slope_degrees,
            soil_depth_m=request.soil_depth_m,
            erosion_risk=request.erosion_risk,
            drainage_class=request.drainage_class,
            climate_zone=request.climate_zone,
            soil_texture=request.soil_texture
        )
        
        logger.info(f"Capability assessment via API: {profile_id}")
        return assessment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in capability assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """
    بررسی سلامت سرویس
    
    Returns health status of the land service.
    """
    return {
        "status": "healthy",
        "service": "land",
        "profiles_count": len(land_service.list_profiles())
    }
