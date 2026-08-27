"""
Land Intelligence Models (Pydantic V2)
=======================================
Complete data structures for land analysis.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TerrainType(str, Enum):
    """Terrain type (USDA/FAO standard)"""
    FLAT = "flat"
    NEARLY_FLAT = "nearly_flat"
    GENTLE = "gentle"
    ROLLING = "rolling"
    HILLY = "hilly"
    MOUNTAINOUS = "mountainous"
    STEEP = "steep"
    VERY_STEEP = "very_steep"


class SlopeClass(str, Enum):
    """USDA Slope Classes"""
    CLASS_0 = "0"  # 0-1%
    CLASS_1 = "1"  # 1-3%
    CLASS_2 = "2"  # 3-8%
    CLASS_3 = "3"  # 8-15%
    CLASS_4 = "4"  # 15-25%
    CLASS_5 = "5"  # 25-45%
    CLASS_6 = "6"  # >45%


class DrainagePattern(str, Enum):
    """Drainage patterns"""
    DENDRITIC = "dendritic"
    TRELLIS = "trellis"
    RADIAL = "radial"
    PARALLEL = "parallel"
    RECTANGULAR = "rectangular"
    DERANGED = "deranged"
    ANNULAR = "annular"
    CENTRIPETAL = "centripetal"


class DrainageDensityClass(str, Enum):
    """Drainage density classes"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ErosionRisk(str, Enum):
    """Erosion risk levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class LandCapabilityClass(str, Enum):
    """USDA Land Capability Classes"""
    CLASS_I = "I"
    CLASS_II = "II"
    CLASS_III = "III"
    CLASS_IV = "IV"
    CLASS_V = "V"
    CLASS_VI = "VI"
    CLASS_VII = "VII"
    CLASS_VIII = "VIII"


class LandformType(str, Enum):
    """TPI-based landform types"""
    VALLEY = "valley"
    LOWER_SLOPE = "lower_slope"
    FLAT = "flat"
    MID_SLOPE = "mid_slope"
    UPPER_SLOPE = "upper_slope"
    RIDGE = "ridge"


class SlopeAspectResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slope_degrees": 15.5,
                "slope_percent": 27.7,
                "slope_class": "3",
                "aspect_degrees": 180.0,
                "aspect_cardinal": "S"
            }
        }
    )
    slope_degrees: float = Field(..., ge=0, le=90)
    slope_percent: float = Field(..., ge=0)
    slope_class: SlopeClass | None = None
    aspect_degrees: float = Field(..., ge=0, le=360)
    aspect_cardinal: str


class CurvatureResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_curvature": -0.02,
                "plan_curvature": 0.01,
                "total_curvature": -0.01
            }
        }
    )
    profile_curvature: float
    plan_curvature: float
    total_curvature: float
    convergence_index: float | None = None


class TerrainIndices(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "twi": 8.5,
                "tpi": 12.3,
                "roughness_index": 0.15,
                "landform": "mid_slope"
            }
        }
    )
    twi: float | None = None
    tpi: float | None = None
    roughness_index: float | None = Field(None, ge=0)
    landform: LandformType | None = None
    wetness_class: Literal["dry", "moderate", "wet", "very_wet"] | None = None


class TerrainAnalysis(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "terrain_type": "rolling",
                "elevation_min": 1200.0,
                "elevation_max": 1350.0,
                "slope_mean": 12.5
            }
        }
    )
    profile_id: str
    terrain_type: str | None = None
    elevation_min: float
    elevation_max: float
    elevation_mean: float
    elevation_range: float | None = None
    slope_mean: float = Field(..., ge=0, le=90)
    slope_max: float = Field(..., ge=0, le=90)
    slope_class_dominant: SlopeClass | None = None
    slope_distribution: dict[str, float] | None = None
    aspect_dominant: float | None = None
    aspect_distribution: dict[str, float] | None = None
    curvature: CurvatureResult | None = None
    indices: TerrainIndices | None = None
    roughness_index: float = Field(0, ge=0)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StreamOrder(BaseModel):
    """Strahler stream order"""
    order: int = Field(..., ge=1)
    count: int = Field(..., ge=0)
    length_km: float = Field(0, ge=0)


class DrainageAnalysis(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "drainage_pattern": "dendritic",
                "drainage_density": 2.5,
                "stream_order_max": 3
            }
        }
    )
    profile_id: str
    drainage_pattern: DrainagePattern | None = None
    drainage_density: float | None = Field(None, ge=0)
    density_class: DrainageDensityClass | None = None
    stream_orders: list[int] | None = None
    stream_order_max: int | None = Field(None, ge=1)
    bifurcation_ratio: float | None = None
    flow_accumulation: Any | None = None
    watershed_area_km2: float | None = Field(None, ge=0)
    time_of_concentration_hours: float | None = Field(None, ge=0)
    main_channel_length_km: float | None = Field(None, ge=0)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class CapabilityAssessment(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "capability_class": "III",
                "subclass": "e",
                "limiting_factors": ["slope", "erosion_risk"]
            }
        }
    )
    profile_id: str
    capability_class: LandCapabilityClass
    subclass: str | None = None
    limiting_factors: list[str] = Field(default_factory=list)
    suitable_uses: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0, le=1)
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    assessed_by: str | None = None


class LandProfile(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "مزرعه نمونه",
                "country": "Iran",
                "region": "Isfahan",
                "location_lat": 32.65,
                "location_lon": 51.67
            }
        }
    )
    id: str
    name: str
    description: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    location_lat: float = Field(..., ge=-90, le=90)
    location_lon: float = Field(..., ge=-180, le=180)
    area_hectares: float | None = Field(None, ge=0)
    boundary_geojson: dict[str, Any] | None = None
    dem_source: str | None = None
    dem_resolution_m: float | None = Field(None, ge=0)
    terrain_analysis: TerrainAnalysis | None = None
    drainage_analysis: DrainageAnalysis | None = None
    capability_assessment: CapabilityAssessment | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None
