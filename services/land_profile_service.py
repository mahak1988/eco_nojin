from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from database.models import LandProfile as LandProfileModel, User
from typing import Optional


class LandProfileCreate(BaseModel):
    name: str
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    area_ha: Optional[float] = None
    user_id: str

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip(): # بررسی خالی یا فقط فضای خالی
            raise ValueError('Name cannot be empty or just whitespace.')
        return v.strip() # بازگرداندن نام بدون فضای اضافی

    @validator('area_ha')
    def area_ha_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Area must be positive.')
        return v

    @validator('location_lat')
    def validate_latitude(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees.')
        return v

    @validator('location_lon')
    def validate_longitude(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees.')
        return v


def create_land_profile(db: Session, land_profile_data: LandProfileCreate):
    """
    Creates a new LandProfile instance in the database after validating input data.
    """
    # Pydantic model_validate ensures the data conforms to our rules
    validated_data = land_profile_data.dict()

    db_land_profile = LandProfileModel(**validated_data)
    db.add(db_land_profile)
    db.commit()
    db.refresh(db_land_profile)
    return db_land_profile