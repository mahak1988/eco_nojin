from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class LandProfileCreateRequest(BaseModel):
    """Request model for creating a new land profile."""
    project_id: str
    latitude: float
    longitude: float
    boundary_geojson: Optional[Dict[str, Any]] = None
    area_hectares: Optional[float] = None


class LandProfileResponse(BaseModel):
    """Response model for a land profile."""
    id: str
    project_id: str
    location: Dict[str, float]  # {"lat": lat, "lng": lng}
    boundary: Optional[Dict[str, Any]]
    area_hectares: Optional[float]
    elevation_min: Optional[float]
    elevation_max: Optional[float]
    elevation_mean: Optional[float]
    slope_mean_degrees: Optional[float]
    aspect_dominant: Optional[str]
    terrain_type: Optional[str]
    drainage_pattern: Optional[str]
    erosion_risk_level: Optional[str]
    accessibility_score: Optional[float]
    land_capability_class: Optional[str]
    development_constraints: Optional[Dict[str, Any]]
    dem_source: Optional[str]
    dem_resolution: Optional[float]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)



def calculate_land_profile(request: LandProfileCreateRequest) -> LandProfileResponse:
    """
    Calculates the basic profile of a land based on input coordinates and area.
    This function acts as a placeholder for the actual calculation logic
    which would involve calling the engine modules.
    """
    # Placeholder calculation - this should eventually call engine.land modules
    print(f"Calculating profile for project {request.project_id} at ({request.latitude}, {request.longitude})")
    
    # Mock data for now
    profile_data = {
        "id": str(uuid.uuid4()),
        "project_id": request.project_id,
        "location": {"lat": request.latitude, "lng": request.longitude},
        "boundary": request.boundary_geojson,
        "area_hectares": request.area_hectares,
        "elevation_min": 100.0,
        "elevation_max": 250.0,
        "elevation_mean": 175.0,
        "slope_mean_degrees": 15.5,
        "aspect_dominant": "South",
        "terrain_type": "Rolling Hills",
        "drainage_pattern": "Dendritic",
        "erosion_risk_level": "Moderate",
        "accessibility_score": 0.75,
        "land_capability_class": "Class III",
        "development_constraints": {},
        "dem_source": "SRTM",
        "dem_resolution": 30.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    return LandProfileResponse(**profile_data)

# --- کلاس‌های اضافه شده برای سرویس LandService ---

class LandProfile(BaseModel):
    terrain_analysis: Optional['TerrainAnalysis'] = None
    drainage_analysis: Optional['DrainageAnalysis'] = None
    capability_assessment: Optional['CapabilityAssessment'] = None
    terrain_analysis: Optional['TerrainAnalysis'] = None
    drainage_analysis: Optional['DrainageAnalysis'] = None
    capability_assessment: Optional['CapabilityAssessment'] = None
    """مدل پروفایل زمین (ساده)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location_lat: float = 0.0
    location_lon: float = 0.0
    area_ha: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TerrainAnalysis(BaseModel):
    """تحلیل توپوگرافی"""
    profile_id: str
    terrain_type: Optional[str]= None
    elevation_min: Optional[float] = None
    elevation_max: Optional[float] = None
    elevation_mean: Optional[float] = None
    slope_mean: Optional[float] = None
    slope_max: Optional[float] = None
    aspect_dominant: Optional[float]= None
    mean_slope_degrees: float = 0.0
    dominant_aspect_degrees: float = 0.0
    analysis_data: dict = {}
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DrainageAnalysis(BaseModel):
    """تحلیل زهکشی"""
    profile_id: str
    drainage_pattern: Optional[str] = None
    drainage_density: Optional[float] = None
    density_class: Optional[str] = None
    stream_orders: Optional[List[int]]= None
    stream_order_max: Optional[int] = None
    bifurcation_ratio: Optional[float] = None
    flow_accumulation: Optional[Any] = None
    watershed_area_km2: Optional[float] = None
    time_of_concentration_hours: Optional[float] = None
    main_channel_length_km: Optional[float] = None
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
class CapabilityAssessment(BaseModel):
    """ارزیابی قابلیت اراضی"""
    profile_id: str
    capability_class: Optional[str] = None
    confidence_score: Optional[float] = None
    limitations: Optional[list] = None
    analysis_data: dict = {}
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
