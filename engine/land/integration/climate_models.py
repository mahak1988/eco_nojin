"""
Climate Integration Models
===========================
Models for climate data integration with land profiles.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class KoppenClimate(str, Enum):
    """Köppen-Geiger climate classification (simplified main groups)"""
    Af = "Af"    # Tropical rainforest
    Am = "Am"    # Tropical monsoon
    Aw = "Aw"    # Tropical savanna
    BWh = "BWh"  # Hot desert
    BWk = "BWk"  # Cold desert
    BSh = "BSh"  # Hot semi-arid
    BSk = "BSk"  # Cold semi-arid
    Csa = "Csa"  # Hot-summer Mediterranean
    Csb = "Csb"  # Warm-summer Mediterranean
    Csc = "Csc"  # Cold-summer Mediterranean
    Cwa = "Cwa"  # Humid subtropical (dry winter)
    Cwb = "Cwb"  # Subtropical highland (dry winter)
    Cwc = "Cwc"  # Cold subtropical highland (dry winter)
    Cfa = "Cfa"  # Humid subtropical
    Cfb = "Cfb"  # Oceanic
    Cfc = "Cfc"  # Subpolar oceanic
    Dsa = "Dsa"  # Hot-summer Mediterranean continental
    Dsb = "Dsb"  # Warm-summer Mediterranean continental
    Dsc = "Dsc"  # Dry-summer subarctic
    Dsd = "Dsd"  # Dry-summer extremely continental subarctic
    Dwa = "Dwa"  # Hot-summer humid continental (dry winter)
    Dwb = "Dwb"  # Warm-summer humid continental (dry winter)
    Dwc = "Dwc"  # Subarctic (dry winter)
    Dwd = "Dwd"  # Extremely continental subarctic (dry winter)
    Dfa = "Dfa"  # Hot-summer humid continental
    Dfb = "Dfb"  # Warm-summer humid continental
    Dfc = "Dfc"  # Subarctic
    Dfd = "Dfd"  # Extremely continental subarctic
    ET = "ET"    # Tundra
    EF = "EF"    # Ice cap


class AridityClass(str, Enum):
    """UNEP Aridity Index classification"""
    HYPER_ARID = "hyper_arid"      # AI < 0.05
    ARID = "arid"                   # 0.05 <= AI < 0.20
    SEMI_ARID = "semi_arid"        # 0.20 <= AI < 0.50
    DRY_SUBHUMID = "dry_subhumid"  # 0.50 <= AI < 0.65
    HUMID = "humid"                # AI >= 0.65


class MonthlyClimate(BaseModel):
    """Monthly climate data"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month": 1,
                "t_min_c": 2.5,
                "t_max_c": 12.0,
                "t_mean_c": 7.2,
                "precipitation_mm": 85.0,
                "et0_mm": 45.0,
            }
        }
    )
    
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    t_min_c: float = Field(..., description="Minimum temperature (°C)")
    t_max_c: float = Field(..., description="Maximum temperature (°C)")
    t_mean_c: float = Field(..., description="Mean temperature (°C)")
    precipitation_mm: float = Field(..., ge=0, description="Monthly precipitation (mm)")
    et0_mm: Optional[float] = Field(None, ge=0, description="Reference ET (mm)")
    
    def t_range(self) -> float:
        """Daily temperature range."""
        return self.t_max_c - self.t_min_c


class ClimateProfile(BaseModel):
    """Complete climate profile for a location"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lat": 32.65,
                "lon": 51.67,
                "koppen": "BWh",
                "koppen_description": "Hot desert",
                "annual_precip_mm": 125.0,
                "annual_et0_mm": 1850.0,
                "aridity_index": 0.068,
                "aridity_class": "arid",
                "growing_season_days": 280,
                "frost_free_days": 240,
            }
        }
    )
    
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    elevation_m: Optional[float] = None
    
    # Köppen-Geiger
    koppen: Optional[KoppenClimate] = None
    koppen_description: Optional[str] = None
    koppen_group: Optional[str] = None  # A, B, C, D, E
    
    # Annual aggregates
    annual_precip_mm: float = Field(..., ge=0, description="Annual precipitation (mm)")
    annual_et0_mm: Optional[float] = Field(None, ge=0, description="Annual ET0 (mm)")
    annual_t_mean_c: float = Field(..., description="Annual mean temperature (°C)")
    
    # Aridity
    aridity_index: Optional[float] = Field(
        None, ge=0, description="Aridity Index = P/PET"
    )
    aridity_class: Optional[AridityClass] = None
    
    # Growing season
    growing_season_days: Optional[int] = Field(
        None, ge=0, description="Growing season length (days)"
    )
    frost_free_days: Optional[int] = Field(
        None, ge=0, description="Frost-free days per year"
    )
    
    # Monthly data
    monthly: List[MonthlyClimate] = Field(default_factory=list)
    
    # Metadata
    data_source: Optional[str] = None  # "open_meteo", "era5", "synthetic"
    data_quality_level: Optional[str] = None  # L0-L5
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClimateIntegrationResult(BaseModel):
    """Result of climate integration with land profile"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "success": True,
                "climate_profile": {"koppen": "BWh"},
                "capabilities": {
                    "irrigation_required": True,
                    "drought_tolerant_crops_only": True
                }
            }
        }
    )
    
    profile_id: str
    success: bool = True
    error_message: Optional[str] = None
    
    climate_profile: Optional[ClimateProfile] = None
    
    # Capabilities derived from climate
    irrigation_required: bool = False
    drought_tolerant_crops_only: bool = False
    cold_climate_limitation: bool = False
    heat_stress_risk: bool = False
    
    # Limitations
    limitations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Integration metadata
    integrated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    integration_time_ms: Optional[float] = None
    data_quality_level: Optional[str] = None


# Reference Köppen descriptions
KOPPEN_DESCRIPTIONS = {
    KoppenClimate.Af: "Tropical rainforest",
    KoppenClimate.Am: "Tropical monsoon",
    KoppenClimate.Aw: "Tropical savanna",
    KoppenClimate.BWh: "Hot desert",
    KoppenClimate.BWk: "Cold desert",
    KoppenClimate.BSh: "Hot semi-arid (steppe)",
    KoppenClimate.BSk: "Cold semi-arid (steppe)",
    KoppenClimate.Csa: "Hot-summer Mediterranean",
    KoppenClimate.Csb: "Warm-summer Mediterranean",
    KoppenClimate.Csc: "Cold-summer Mediterranean",
    KoppenClimate.Cwa: "Humid subtropical (dry winter)",
    KoppenClimate.Cwb: "Subtropical highland (dry winter)",
    KoppenClimate.Cwc: "Cold subtropical highland",
    KoppenClimate.Cfa: "Humid subtropical",
    KoppenClimate.Cfb: "Oceanic",
    KoppenClimate.Cfc: "Subpolar oceanic",
    KoppenClimate.Dsa: "Hot-summer Mediterranean continental",
    KoppenClimate.Dsb: "Warm-summer Mediterranean continental",
    KoppenClimate.Dsc: "Dry-summer subarctic",
    KoppenClimate.Dsd: "Extremely continental subarctic (dry summer)",
    KoppenClimate.Dwa: "Hot-summer humid continental (dry winter)",
    KoppenClimate.Dwb: "Warm-summer humid continental (dry winter)",
    KoppenClimate.Dwc: "Subarctic (dry winter)",
    KoppenClimate.Dwd: "Extremely continental subarctic (dry winter)",
    KoppenClimate.Dfa: "Hot-summer humid continental",
    KoppenClimate.Dfb: "Warm-summer humid continental",
    KoppenClimate.Dfc: "Subarctic",
    KoppenClimate.Dfd: "Extremely continental subarctic",
    KoppenClimate.ET: "Tundra",
    KoppenClimate.EF: "Ice cap",
}
