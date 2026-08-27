"""
Soil Integration Models
========================
Deep soil profile models for 6 layers (0-200cm).
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SoilTexture(str, Enum):
    """USDA Soil Texture Classes (12 classes)"""
    SAND = "sand"
    LOAMY_SAND = "loamy_sand"
    SANDY_LOAM = "sandy_loam"
    LOAM = "loam"
    SILT_LOAM = "silt_loam"
    SILT = "silt"
    SANDY_CLAY_LOAM = "sandy_clay_loam"
    CLAY_LOAM = "clay_loam"
    SILTY_CLAY_LOAM = "silty_clay_loam"
    SANDY_CLAY = "sandy_clay"
    SILTY_CLAY = "silty_clay"
    CLAY = "clay"


class SalinityClass(str, Enum):
    """Soil Salinity Classes based on ECe (dS/m)"""
    NON_SALINE = "non_saline"          # < 2 dS/m
    SLIGHTLY_SALINE = "slightly_saline"  # 2-4 dS/m
    MODERATELY_SALINE = "moderately_saline"  # 4-8 dS/m
    STRONGLY_SALINE = "strongly_saline"  # 8-16 dS/m
    VERY_STRONGLY_SALINE = "very_strongly_saline"  # > 16 dS/m


class DrainageClass(str, Enum):
    """Soil Drainage Classes"""
    EXCESSIVE = "excessive"
    SOMEWHAT_EXCESSIVE = "somewhat_excessive"
    WELL = "well"
    MODERATE = "moderate"
    SOMEWHAT_POOR = "somewhat_poor"
    POOR = "poor"
    VERY_POOR = "very_poor"


class SoilLayer(BaseModel):
    """Single soil layer (e.g., 0-5cm, 5-15cm, etc.)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "depth_min_cm": 0,
                "depth_max_cm": 5,
                "sand_pct": 40.0,
                "silt_pct": 30.0,
                "clay_pct": 30.0,
                "texture": "loam",
                "ph": 7.2,
                "ec_dsm": 1.5,
                "organic_carbon_g_kg": 12.0,
                "cec_mmolc_kg": 18.0,
                "bulk_density_g_cm3": 1.35,
                "theta_r": 0.08,
                "theta_s": 0.45,
                "alpha": 0.02,
                "n": 1.5
            }
        }
    )

    depth_min_cm: int = Field(..., ge=0, description="Upper depth (cm)")
    depth_max_cm: int = Field(..., gt=0, description="Lower depth (cm)")

    # Texture (must sum to 100)
    sand_pct: float = Field(..., ge=0, le=100)
    silt_pct: float = Field(..., ge=0, le=100)
    clay_pct: float = Field(..., ge=0, le=100)
    texture: SoilTexture

    # Chemistry
    ph: float | None = Field(None, ge=0, le=14)
    ec_dsm: float | None = Field(None, ge=0, description="Electrical conductivity (dS/m)")
    cec_mmolc_kg: float | None = Field(None, ge=0, description="Cation Exchange Capacity")
    esp_pct: float | None = Field(None, ge=0, le=100, description="Exchangeable Sodium Percentage")
    organic_carbon_g_kg: float | None = Field(None, ge=0, description="Soil Organic Carbon")

    # Physical properties
    bulk_density_g_cm3: float | None = Field(None, gt=0, le=2.0)

    # van Genuchten parameters (for water retention)
    theta_r: float | None = Field(None, ge=0, le=1, description="Residual water content")
    theta_s: float | None = Field(None, ge=0, le=1, description="Saturated water content")
    alpha: float | None = Field(None, gt=0, description="VG alpha parameter")
    n: float | None = Field(None, gt=1, description="VG n parameter")

    # Data quality
    data_source: str | None = None  # "soilgrids", "user", "estimated"
    uncertainty: float | None = Field(None, ge=0, le=1)

    def depth_thickness_cm(self) -> int:
        """Return layer thickness in cm."""
        return self.depth_max_cm - self.depth_min_cm

    def validate_texture_sum(self) -> bool:
        """Check that sand+silt+clay sums to ~100."""
        total = self.sand_pct + self.silt_pct + self.clay_pct
        return 99.5 <= total <= 100.5


class DeepSoilProfile(BaseModel):
    """Complete soil profile with 6 layers (0-200cm)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "layers": [
                    {"depth_min_cm": 0, "depth_max_cm": 5},
                    {"depth_min_cm": 5, "depth_max_cm": 15},
                    {"depth_min_cm": 15, "depth_max_cm": 30},
                    {"depth_min_cm": 30, "depth_max_cm": 60},
                    {"depth_min_cm": 60, "depth_max_cm": 100},
                    {"depth_min_cm": 100, "depth_max_cm": 200}
                ],
                "total_depth_cm": 200,
                "dominant_texture": "loam",
                "rooting_depth_cm": 120
            }
        }
    )

    layers: list[SoilLayer] = Field(..., min_length=1, max_length=10)
    total_depth_cm: int = Field(..., gt=0)
    dominant_texture: SoilTexture | None = None
    rooting_depth_cm: int | None = Field(None, gt=0, description="Effective rooting depth")

    # Derived properties
    awc_mm: float | None = Field(None, ge=0, description="Available Water Capacity")
    salinity_class: SalinityClass | None = None
    drainage_class: DrainageClass | None = None

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data_source: str | None = None


class SoilIntegrationResult(BaseModel):
    """Result of soil integration with land profile"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "success": True,
                "soil_profile": {"total_depth_cm": 200},
                "soil_health_score": 65.5,
                "capabilities": {"suitable_for": ["wheat", "barley"]}
            }
        }
    )

    profile_id: str
    success: bool = True
    error_message: str | None = None

    soil_profile: DeepSoilProfile | None = None
    soil_health_score: float | None = Field(None, ge=0, le=100)

    # Capabilities derived from soil
    suitable_crops: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    # Integration metadata
    integrated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    integration_time_ms: float | None = None
    data_quality_level: str | None = None  # L0-L5
