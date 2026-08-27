"""Farms CRUD router."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import Farm, User
from services.api_gateway.auth import require_user

router = APIRouter(prefix="/api/v1/farms", tags=["farms"])


class FarmCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float | None = None
    area_hectares: float = Field(gt=0, le=100000)
    soil_type: str | None = None
    climate_zone: str | None = None


class FarmOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    elevation_m: float | None
    area_hectares: float
    soil_type: str | None
    climate_zone: str | None

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[FarmOut])
def list_farms(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """List all farms owned by current user."""
    return db.query(Farm).filter(Farm.owner_id == user.id).order_by(Farm.created_at.desc()).all()


@router.post("/", response_model=FarmOut)
def create_farm(req: FarmCreate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Create a new farm."""
    farm = Farm(
        name=req.name,
        owner_id=user.id,
        latitude=req.latitude,
        longitude=req.longitude,
        elevation_m=req.elevation_m,
        area_hectares=req.area_hectares,
        soil_type=req.soil_type,
        climate_zone=req.climate_zone,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get a specific farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.delete("/{farm_id}")
def delete_farm(farm_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Delete a farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    db.delete(farm)
    db.commit()
    return {"success": True}
