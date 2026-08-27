"""
Reference Data Models
=====================

Base models for geographic reference data:
- Country (کشور)
- Region/Province (استان)
- City (شهر)
- Terrain Classification (طبقه‌بندی توپوگرافی)
- Drainage Standard (استاندارد زهکشی)
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Continent(str, Enum):
    """Continents"""
    AFRICA = "africa"
    ASIA = "asia"
    EUROPE = "europe"
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    OCEANIA = "oceania"
    ANTARCTICA = "antarctica"


class Country(BaseModel):
    """Country reference data"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "IR",
                "name": "Iran",
                "name_fa": "ایران",
                "continent": "asia",
                "capital_lat": 35.69,
                "capital_lon": 51.39,
            }
        }
    )

    code: str = Field(..., min_length=2, max_length=3, description="ISO 3166-1 alpha-2/3")
    name: str = Field(..., description="Country name (English)")
    name_fa: str | None = Field(None, description="Country name (Persian)")
    continent: Continent
    capital_lat: float | None = Field(None, ge=-90, le=90)
    capital_lon: float | None = Field(None, ge=-180, le=180)
    area_km2: float | None = Field(None, ge=0)
    population: int | None = Field(None, ge=0)
    dominant_climate: str | None = Field(None, description="Köppen class")
    currency: str | None = Field(None, max_length=3)


class Region(BaseModel):
    """Province/State/Region reference data"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "IR-04",
                "name": "Isfahan",
                "name_fa": "اصفهان",
                "country_code": "IR",
                "center_lat": 32.65,
                "center_lon": 51.67,
            }
        }
    )

    code: str = Field(..., description="ISO 3166-2 code or internal code")
    name: str = Field(..., description="Region name (English)")
    name_fa: str | None = Field(None, description="Region name (Persian)")
    country_code: str = Field(..., min_length=2, max_length=3)
    center_lat: float | None = Field(None, ge=-90, le=90)
    center_lon: float | None = Field(None, ge=-180, le=180)
    area_km2: float | None = Field(None, ge=0)
    population: int | None = Field(None, ge=0)
    elevation_mean_m: float | None = None


class City(BaseModel):
    """City reference data"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Isfahan",
                "name_fa": "اصفهان",
                "country_code": "IR",
                "region_code": "IR-04",
                "lat": 32.65,
                "lon": 51.67,
            }
        }
    )

    name: str = Field(..., description="City name (English)")
    name_fa: str | None = Field(None, description="City name (Persian)")
    country_code: str = Field(..., min_length=2, max_length=3)
    region_code: str | None = None
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    population: int | None = Field(None, ge=0)
    elevation_m: float | None = None


class TerrainClassification(BaseModel):
    """Standard terrain classification reference"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "rolling",
                "slope_min_deg": 8,
                "slope_max_deg": 15,
                "description": "Rolling terrain with gentle undulations"
            }
        }
    )

    code: str
    name: str
    slope_min_deg: float = Field(..., ge=0, le=90)
    slope_max_deg: float = Field(..., ge=0, le=90)
    description: str
    source: str | None = Field(None, description="Reference standard")


class DrainageStandard(BaseModel):
    """Standard drainage density classification"""
    code: str
    name: str
    density_min_km_km2: float = Field(..., ge=0)
    density_max_km_km2: float = Field(..., ge=0)
    description: str
    typical_geology: str | None = None
