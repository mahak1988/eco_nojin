"""
Land Intelligence Models (Pydantic V2)
=======================================
Complete data structures for land analysis.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from engine.hydroma.provenance import ResultProvenance


class TerrainType(StrEnum):
    """Terrain type (USDA/FAO standard)"""

    FLAT = "flat"
    NEARLY_FLAT = "nearly_flat"
    GENTLE = "gentle"
    ROLLING = "rolling"
    HILLY = "hilly"
    MOUNTAINOUS = "mountainous"
    STEEP = "steep"
    VERY_STEEP = "very_steep"


class SlopeClass(StrEnum):
    """USDA Slope Classes"""

    CLASS_0 = "0"  # 0-1%
    CLASS_1 = "1"  # 1-3%
    CLASS_2 = "2"  # 3-8%
    CLASS_3 = "3"  # 8-15%
    CLASS_4 = "4"  # 15-25%
    CLASS_5 = "5"  # 25-45%
    CLASS_6 = "6"  # >45%


class DrainagePattern(StrEnum):
    """Drainage patterns"""

    DENDRITIC = "dendritic"
    TRELLIS = "trellis"
    RADIAL = "radial"
    PARALLEL = "parallel"
    RECTANGULAR = "rectangular"
    DERANGED = "deranged"
    ANNULAR = "annular"
    CENTRIPETAL = "centripetal"


class DrainageDensityClass(StrEnum):
    """Drainage density classes"""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ErosionRisk(StrEnum):
    """Erosion risk levels"""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class LandCapabilityClass(StrEnum):
    """USDA Land Capability Classes"""

    CLASS_I = "I"
    CLASS_II = "II"
    CLASS_III = "III"
    CLASS_IV = "IV"
    CLASS_V = "V"
    CLASS_VI = "VI"
    CLASS_VII = "VII"
    CLASS_VIII = "VIII"


class LandformType(StrEnum):
    """TPI-based landform types"""

    VALLEY = "valley"
    LOWER_SLOPE = "lower_slope"
    FLAT = "flat"
    MID_SLOPE = "mid_slope"
    UPPER_SLOPE = "upper_slope"
    RIDGE = "ridge"


class SlopeAspectResult(ResultProvenance, BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slope_degrees": 15.5,
                "slope_percent": 27.7,
                "slope_class": "3",
                "aspect_degrees": 180.0,
                "aspect_cardinal": "S",
            }
        }
    )
    slope_degrees: float = Field(..., ge=0, le=90)
    slope_percent: float = Field(..., ge=0)
    slope_class: SlopeClass | None = None
    aspect_degrees: float = Field(..., ge=0, le=360)
    aspect_cardinal: str


class CurvatureResult(ResultProvenance, BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_curvature": -0.02,
                "plan_curvature": 0.01,
                "total_curvature": -0.01,
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
            "example": {"twi": 8.5, "tpi": 12.3, "roughness_index": 0.15, "landform": "mid_slope"}
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
                "slope_mean": 12.5,
            }
        }
    )
    data_source: str = "modelled"
    model: str = "terrain_analysis (Horn 1981)"
    profile_id: str | None = None
    terrain_type: TerrainType | None = None
    elevation_min: float | None = None
    elevation_max: float | None = None
    elevation_mean: float | None = None
    elevation_range: float | None = None
    slope_mean: float = Field(..., ge=0, le=90)
    slope_max: float = Field(..., ge=0, le=90)
    slope_class_dominant: SlopeClass | None = None
    slope_distribution: dict[str, float] | None = None
    aspect_dominant: str | float | None = None
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
                "stream_order_max": 3,
            }
        }
    )
    data_source: str = "modelled"
    model: str = "drainage_analysis (Strahler)"
    profile_id: str | None = None
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
                "limiting_factors": ["slope", "erosion_risk"],
            }
        }
    )
    data_source: str = "simulated"
    model: str = "USDA land capability (rules, unvalidated)"
    profile_id: str | None = None
    capability_class: LandCapabilityClass | None = None
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
                "location_lon": 51.67,
            }
        }
    )
    data_source: str = "simulated"
    model: str = "default land profile (built-in constants)"
    id: str | None = None
    name: str | None = None
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


# ═══════════════════════════════════════════════════════════════════════
# Land registry / cadastre data contracts (P2-16)
#
# Pure data contracts: no database or service imports. The registry
# tables live in ``database/models.py`` and the behaviour in
# ``services/land/registry.py``; these classes are the shared shape of
# parcels, ownership shares and tenure rights between the two layers.
# ═══════════════════════════════════════════════════════════════════════


class LandUseType(StrEnum):
    """Cadastral land-use classification of a parcel."""

    AGRICULTURAL = "agricultural"
    RANGELAND = "rangeland"
    FOREST = "forest"
    RESIDENTIAL = "residential"
    WATER = "water"
    PROTECTED = "protected"
    OTHER = "other"


class OwnershipType(StrEnum):
    """Legal form under which ownership of a parcel is held."""

    INDIVIDUAL = "individual"
    COOPERATIVE = "cooperative"
    TRIBAL_COMMUNAL = "tribal-communal"
    STATE = "state"


class HolderType(StrEnum):
    """Kind of entity that may hold a tenure right."""

    USER = "user"
    COMMUNITY = "community"


class TenureRightType(StrEnum):
    """Use rights over a parcel that fall short of ownership."""

    GRAZING = "grazing"
    SEASONAL_CORRIDOR = "seasonal_corridor"


class TenureRightStatus(StrEnum):
    """Lifecycle states of a tenure right."""

    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class LandParcelInput(BaseModel):
    """Caller-supplied data for registering a cadastral parcel."""

    parcel_id: str | None = Field(
        None, description="Optional stable identifier; generated when omitted"
    )
    deed_no: str = Field(..., description="Deed (title) number, unique per registry")
    village_id: str
    name: str
    area_ha: Decimal = Field(..., ge=0)
    boundary: dict[str, Any] | None = Field(None, description="GeoJSON boundary polygon")
    land_use: LandUseType = LandUseType.AGRICULTURAL
    capability_class: LandCapabilityClass | None = None


class LandParcel(BaseModel):
    """A registered cadastral parcel."""

    parcel_id: str
    deed_no: str
    village_id: str
    name: str
    area_ha: Decimal
    boundary: dict[str, Any] | None = None
    land_use: LandUseType
    capability_class: LandCapabilityClass | None = None
    created_at: datetime
    updated_at: datetime | None = None


class LandOwnershipInput(BaseModel):
    """Caller-supplied data for recording an ownership share."""

    parcel_id: str
    owner_user_id: str
    ownership_type: OwnershipType
    share_pct: Decimal = Field(..., gt=0, le=100)
    effective_from: date | None = None
    effective_to: date | None = None
    evidence_ref: str | None = Field(None, description="Deed / registry document reference")


class LandOwnershipRecord(BaseModel):
    """A stored ownership record; title history is kept via effective dates."""

    ownership_id: str
    parcel_id: str
    owner_user_id: str
    ownership_type: OwnershipType
    share_pct: Decimal
    effective_from: date | None = None
    effective_to: date | None = None
    evidence_ref: str | None = None
    is_verified: bool = False
    verified_by: str | None = None
    verified_at: datetime | None = None
    created_at: datetime


class LandTenureRight(BaseModel):
    """A use right (grazing or seasonal corridor) held over one parcel.

    A user holder carries ``holder_user_id``; a community holder (e.g. a
    nomadic community) carries ``community_id``. ``season_start`` and
    ``season_end`` are month numbers (1-12) and may wrap across the year
    end, so a winter window is expressed as 11 to 3.
    """

    right_id: str
    right_type: TenureRightType
    parcel_id: str
    holder_type: HolderType
    holder_user_id: str | None = None
    community_id: str | None = None
    season_start: int = Field(..., ge=1, le=12)
    season_end: int = Field(..., ge=1, le=12)
    granted_by: str
    status: TenureRightStatus = TenureRightStatus.PENDING
    created_at: datetime
    activated_at: datetime | None = None
    closed_at: datetime | None = None

    @model_validator(mode="after")
    def _holder_matches_holder_type(self) -> Self:
        if self.holder_type is HolderType.USER and self.holder_user_id is None:
            raise ValueError("holder_user_id is required when holder_type is 'user'")
        if self.holder_type is HolderType.COMMUNITY and self.community_id is None:
            raise ValueError("community_id is required when holder_type is 'community'")
        return self


class CadastralSummary(BaseModel):
    """Aggregate registry read model for a village scope or the whole registry."""

    data_source: str = "database"
    village_id: str | None = None
    parcel_count: int = 0
    total_area_ha: Decimal = Decimal("0")
    area_by_land_use: dict[str, Decimal] = Field(default_factory=dict)
    ownership_record_count: int = 0
    verified_ownership_count: int = 0
    tenure_right_count: int = 0
    active_tenure_count: int = 0
    tenure_counts_by_type: dict[str, int] = Field(default_factory=dict)
