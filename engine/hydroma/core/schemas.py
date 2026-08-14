"""Pydantic schemas for data validation and API contracts."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class SoilProfileBase(BaseModel):
    name: str = Field(..., max_length=100)
    texture: str | None = Field(None, max_length=50)
    ph: float | None = Field(None, ge=0, le=14)
    ec: float | None = Field(None, ge=0, description="Electrical Conductivity (dS/m)")
    organic_matter: float | None = Field(None, ge=0, le=100)

class SoilProfileCreate(SoilProfileBase):
    pass

class SoilProfileRead(SoilProfileBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PlantBase(BaseModel):
    scientific_name: str = Field(..., max_length=150)
    local_name: str | None = Field(None, max_length=100)
    category: str = Field(..., max_length=50)
    water_need: str | None = None
    drought_tolerance: str | None = None
    salinity_tolerance: str | None = None

class PlantCreate(PlantBase):
    pass

class PlantRead(PlantBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MaterialBase(BaseModel):
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    c_n_ratio: float | None = Field(None, ge=0)
    ph: float | None = Field(None, ge=0, le=14)

class MaterialCreate(MaterialBase):
    pass

class MaterialRead(MaterialBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
