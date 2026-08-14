"""API endpoints for satellite data analysis."""
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from engine.hydroma.satellite import get_analyzer

router = APIRouter(prefix="/api/v1/satellite", tags=["Satellite Analysis"])


class PointAnalysisRequest(BaseModel):
    """Request for point-based satellite analysis."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    analysis_date: str | None = Field(
        None,
        description="Date in YYYY-MM-DD format (defaults to 7 days ago)"
    )


class VegetationClass(BaseModel):
    """Vegetation classification."""
    class_name: str = Field(alias="class")
    description: str


class FieldAnalysisResponse(BaseModel):
    """Response containing complete field analysis."""
    lat: float
    lon: float
    analysis_date: str
    ndvi: float
    evi: float
    savi: float
    ndwi: float
    nbr: float
    vegetation_status: VegetationClass
    cloud_cover: float
    data_quality: str
    recommendation: str


@router.post("/analyze", response_model=FieldAnalysisResponse)
def analyze_field(payload: PointAnalysisRequest):
    """Analyze a geographic point using satellite data.
    
    Returns vegetation indices (NDVI, EVI, SAVI, NDWI, NBR) and
    actionable recommendations for farmers and land managers.
    """
    analyzer = get_analyzer()
    
    # Parse date if provided
    analysis_date = None
    if payload.analysis_date:
        try:
            analysis_date = date.fromisoformat(payload.analysis_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD."
            )
    
    result = analyzer.analyze_point(
        lat=payload.lat,
        lon=payload.lon,
        analysis_date=analysis_date,
    )
    
    return FieldAnalysisResponse(
        lat=result.lat,
        lon=result.lon,
        analysis_date=result.analysis_date.isoformat(),
        ndvi=result.ndvi,
        evi=result.evi,
        savi=result.savi,
        ndwi=result.ndwi,
        nbr=result.nbr,
        vegetation_status=VegetationClass(
            **result.ndvi_class
        ),
        cloud_cover=result.cloud_cover,
        data_quality=result.data_quality,
        recommendation=result.recommendation,
    )


@router.get("/health")
def satellite_health():
    """Check satellite service availability."""
    analyzer = get_analyzer()
    return {
        "status": "operational",
        "providers": ["earth_search", "nasa_power"],
        "supported_indices": ["NDVI", "EVI", "SAVI", "NDWI", "NBR"],
    }
