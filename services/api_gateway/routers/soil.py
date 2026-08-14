"""API endpoints for soil profile management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from engine.hydroma.core.models import SoilProfile as SoilProfileModel
from engine.hydroma.core.schemas import SoilProfileCreate, SoilProfileRead
from ..dependencies import get_db

router = APIRouter(prefix="/api/v1/soil", tags=["Soil Management"])

@router.post("/", response_model=SoilProfileRead, status_code=status.HTTP_201_CREATED)
def create_soil_profile(payload: SoilProfileCreate, db: Session = Depends(get_db)):
    """Register a new soil analysis in the database."""
    db_soil = SoilProfileModel(**payload.model_dump())
    db.add(db_soil)
    db.commit()
    db.refresh(db_soil)
    return db_soil

@router.get("/", response_model=List[SoilProfileRead])
def list_soil_profiles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of all registered soil profiles."""
    return db.query(SoilProfileModel).offset(skip).limit(limit).all()
