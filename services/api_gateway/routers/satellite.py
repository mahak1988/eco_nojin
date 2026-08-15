"""Satellite analysis router - uses C++ indices + database."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import SatelliteAnalysis

router = APIRouter(prefix="/api/v1/satellite", tags=["satellite"])


class SatelliteRequest(BaseModel):
    lat: float
    lon: float
    red: float = Field(0.2, ge=0, le=1, description="Red band reflectance")
    nir: float = Field(0.5, ge=0, le=1, description="NIR band reflectance")
    blue: float = Field(0.1, ge=0, le=1)
    green: float = Field(0.3, ge=0, le=1)
    swir: float = Field(0.2, ge=0, le=1)
    farm_id: int | None = None
    user_id: int | None = None


@router.post("/analyze")
def analyze_satellite(req: SatelliteRequest, db: Session = Depends(get_db)):
    """Compute vegetation indices from reflectance bands."""
    from engine.hydroma.wrapper import compute_all_indices

    indices = compute_all_indices(
        red=req.red, nir=req.nir, blue=req.blue, green=req.green, swir=req.swir
    )

    # Interpretation
    ndvi = indices["ndvi"]
    if ndvi < 0:
        health = "no vegetation / water"
    elif ndvi < 0.2:
        health = "bare soil / sparse"
    elif ndvi < 0.4:
        health = "moderate vegetation"
    elif ndvi < 0.6:
        health = "dense vegetation"
    else:
        health = "very dense / healthy"

    result = {
        "latitude": req.lat,
        "longitude": req.lon,
        "indices": indices,
        "vegetation_health": health,
        "recommendations": [],
    }

    if ndvi < 0.3:
        result["recommendations"].append("Consider irrigation or fertilization")
    if ndvi > 0.7:
        result["recommendations"].append("Excellent vegetation - maintain current practices")
    if indices["ndwi"] > 0.3:
        result["recommendations"].append("High water content detected - possible flooding")

    # Save to database
    if req.farm_id and req.user_id:
        try:
            record = SatelliteAnalysis(
                farm_id=req.farm_id,
                user_id=req.user_id,
                latitude=req.lat,
                longitude=req.lon,
                ndvi=indices["ndvi"],
                evi=indices["evi"],
                savi=indices["savi"],
                ndwi=indices["ndwi"],
                nbr=indices["nbr"],
                satellite="Sentinel-2",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            result["saved_id"] = record.id
        except Exception as e:
            db.rollback()
            result["save_warning"] = str(e)

    return result
