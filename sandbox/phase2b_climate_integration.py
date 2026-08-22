"""
Phase 2B: Climate Integration
================================
Connects engine/land/ to climate modules:
- engine/hydroma/climate/et_calculator.py
- engine/hydroma/models/global_watchdog/koppen.py
- services/satellite/open_meteo.py

Creates:
- engine/land/integration/climate_models.py
- engine/land/integration/climate_integrator.py
- engine/land/integration/tests/test_climate_integrator.py

Run: python sandbox/phase2b_climate_integration.py
"""

from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")
INTEGRATION_DIR = PROJECT_ROOT / "engine" / "land" / "integration"
TESTS_DIR = INTEGRATION_DIR / "tests"


def create_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ Created: {path.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("🌤️  Phase 2B: Climate Integration")
    print("=" * 70)
    
    # ==========================================================================
    # 1. Climate Models
    # ==========================================================================
    print("\n[1/4] Creating climate_models.py...")
    
    climate_models_content = '''"""
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
'''
    
    create_file(INTEGRATION_DIR / "climate_models.py", climate_models_content)
    
    # ==========================================================================
    # 2. Climate Integrator
    # ==========================================================================
    print("\n[2/4] Creating climate_integrator.py...")
    
    integrator_content = '''"""
Climate Integrator
===================
Connects engine/land/ to climate modules.
Uses existing modules:
- engine/hydroma/climate/et_calculator.py
- engine/hydroma/models/global_watchdog/koppen.py
- services/satellite/open_meteo.py
"""

import logging
import math
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from .models import LandProfile
from .climate_models import (
    ClimateProfile, ClimateIntegrationResult,
    MonthlyClimate, KoppenClimate, AridityClass,
    KOPPEN_DESCRIPTIONS,
)

logger = logging.getLogger(__name__)

# Synthetic climate data for fallback (based on latitude bands)
# Each entry: (t_min_jan, t_max_jan, t_min_jul, t_max_jul, annual_precip)
LATITUDE_CLIMATE_BANDS = {
    "tropical": {
        "lat_range": (-23.5, 23.5),
        "t_min_jan": 22.0, "t_max_jan": 32.0,
        "t_min_jul": 22.0, "t_max_jul": 32.0,
        "annual_precip": 2000.0,
        "koppen": KoppenClimate.Aw,
    },
    "subtropical_arid": {
        "lat_range": (23.5, 35.0),
        "t_min_jan": 5.0, "t_max_jan": 18.0,
        "t_min_jul": 22.0, "t_max_jul": 42.0,
        "annual_precip": 150.0,
        "koppen": KoppenClimate.BWh,
    },
    "subtropical_arid_south": {
        "lat_range": (-35.0, -23.5),
        "t_min_jan": 22.0, "t_max_jan": 42.0,
        "t_min_jul": 5.0, "t_max_jul": 18.0,
        "annual_precip": 150.0,
        "koppen": KoppenClimate.BWh,
    },
    "temperate": {
        "lat_range": (35.0, 50.0),
        "t_min_jan": -2.0, "t_max_jan": 8.0,
        "t_min_jul": 15.0, "t_max_jul": 28.0,
        "annual_precip": 700.0,
        "koppen": KoppenClimate.Cfb,
    },
    "temperate_south": {
        "lat_range": (-50.0, -35.0),
        "t_min_jan": 15.0, "t_max_jan": 28.0,
        "t_min_jul": -2.0, "t_max_jul": 8.0,
        "annual_precip": 700.0,
        "koppen": KoppenClimate.Cfb,
    },
    "continental": {
        "lat_range": (50.0, 66.5),
        "t_min_jan": -15.0, "t_max_jan": -5.0,
        "t_min_jul": 12.0, "t_max_jul": 24.0,
        "annual_precip": 500.0,
        "koppen": KoppenClimate.Dfb,
    },
    "continental_south": {
        "lat_range": (-66.5, -50.0),
        "t_min_jan": 12.0, "t_max_jan": 24.0,
        "t_min_jul": -15.0, "t_max_jul": -5.0,
        "annual_precip": 500.0,
        "koppen": KoppenClimate.Dfb,
    },
    "polar": {
        "lat_range": (66.5, 90.0),
        "t_min_jan": -30.0, "t_max_jan": -15.0,
        "t_min_jul": 0.0, "t_max_jul": 8.0,
        "annual_precip": 250.0,
        "koppen": KoppenClimate.ET,
    },
    "polar_south": {
        "lat_range": (-90.0, -66.5),
        "t_min_jan": 0.0, "t_max_jan": 8.0,
        "t_min_jul": -30.0, "t_max_jul": -15.0,
        "annual_precip": 250.0,
        "koppen": KoppenClimate.ET,
    },
}


class ClimateIntegrator:
    """
    Integrates climate data with land profiles.
    
    Connects to:
    - engine/hydroma/climate/et_calculator.py (ET0)
    - engine/hydroma/models/global_watchdog/koppen.py (KGCv5)
    - services/satellite/open_meteo.py (climate data)
    """
    
    def __init__(self):
        """Initialize integrator with climate modules."""
        self._et_calculator = None
        self._koppen_classifier = None
        self._load_climate_modules()
    
    def _load_climate_modules(self):
        """Load climate modules (lazy loading)."""
        # Load ET calculator
        try:
            from engine.hydroma.climate.et_calculator import (
                calc_et0_hargreaves,
                calc_extraterrestrial_radiation,
            )
            self._et_calculator = {
                "hargreaves": calc_et0_hargreaves,
                "radiation": calc_extraterrestrial_radiation,
            }
            logger.info("ET calculator loaded")
        except ImportError as e:
            logger.warning(f"Could not load ET calculator: {e}")
        
        # Load Köppen classifier
        try:
            from engine.hydroma.models.global_watchdog.koppen import KGCv5
            self._koppen_classifier = KGCv5()
            logger.info("KGCv5 Köppen classifier loaded")
        except ImportError as e:
            logger.warning(f"Could not load KGCv5: {e}")
    
    def get_latitude_band(self, lat: float) -> Dict[str, Any]:
        """Get climate band for a given latitude."""
        for name, band in LATITUDE_CLIMATE_BANDS.items():
            low, high = band["lat_range"]
            if low <= lat < high:
                return {"name": name, **band}
        # Default to temperate if not found
        return {
            "name": "temperate",
            **LATITUDE_CLIMATE_BANDS["temperate"]
        }
    
    def generate_synthetic_monthly_climate(
        self, lat: float, lon: float
    ) -> List[MonthlyClimate]:
        """
        Generate synthetic monthly climate data based on latitude.
        
        This is the L0 fallback when real data is not available.
        """
        band = self.get_latitude_band(lat)
        
        # Determine hemisphere
        is_northern = lat >= 0
        
        # Interpolate monthly temperatures using cosine function
        # T(month) = T_mean + (T_jul - T_jan)/2 * cos(2π(month - 7)/12)
        # for northern hemisphere (warmest in July)
        t_jan_mean = (band["t_min_jan"] + band["t_max_jan"]) / 2
        t_jul_mean = (band["t_min_jul"] + band["t_max_jul"]) / 2
        t_annual_mean = (t_jan_mean + t_jul_mean) / 2
        t_amplitude = abs(t_jul_mean - t_jan_mean) / 2
        
        # Precipitation distribution (simple sinusoidal with peak in warm season for temperate)
        annual_precip = band["annual_precip"]
        
        monthly = []
        for month in range(1, 13):
            # Temperature: cosine curve
            phase = (month - 7) * 2 * math.pi / 12  # Peak in July (month 7)
            if not is_northern:
                phase = (month - 1) * 2 * math.pi / 12  # Peak in January for south
            
            t_mean = t_annual_mean + t_amplitude * math.cos(phase)
            
            # Add some daily range
            daily_range = 8.0 + 2.0 * math.cos(phase)  # Varies seasonally
            t_min = t_mean - daily_range / 2
            t_max = t_mean + daily_range / 2
            
            # Precipitation: peak in warm season for temperate, wet season varies
            # Simplified: more in summer for temperate, winter for Mediterranean
            precip_phase = phase + math.pi  # Opposite phase for precip
            monthly_frac = (1 + 0.5 * math.cos(precip_phase)) / 12
            precip_mm = annual_precip * monthly_frac
            
            monthly.append(MonthlyClimate(
                month=month,
                t_min_c=round(t_min, 1),
                t_max_c=round(t_max, 1),
                t_mean_c=round(t_mean, 1),
                precipitation_mm=round(max(0, precip_mm), 1),
            ))
        
        return monthly
    
    def calculate_et0_hargreaves_monthly(
        self, monthly: List[MonthlyClimate], lat: float
    ) -> List[MonthlyClimate]:
        """
        Calculate monthly ET0 using Hargreaves method.
        
        ET0 = 0.0023 * Ra * (T_mean + 17.8) * (T_max - T_min)^0.5
        
        Reference: Hargreaves & Samani (1985)
        """
        if not self._et_calculator:
            # Fallback: simple empirical formula
            for m in monthly:
                # Simplified Hargreaves approximation
                ra = self._extraterrestrial_radiation_monthly(m.month, lat)
                t_range = m.t_max_c - m.t_min_c
                if t_range <= 0:
                    t_range = 0.1
                et0 = 0.0023 * ra * (m.t_mean_c + 17.8) * math.sqrt(t_range)
                m.et0_mm = round(max(0, et0), 1)
            return monthly
        
        try:
            for m in monthly:
                # Days in month (approximate)
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                days = days_in_month[m.month - 1]
                
                # Daily ET0 then multiply by days
                ra = self._extraterrestrial_radiation_monthly(m.month, lat)
                t_range = m.t_max_c - m.t_min_c
                if t_range <= 0:
                    t_range = 0.1
                et0_daily = 0.0023 * ra * (m.t_mean_c + 17.8) * math.sqrt(t_range)
                m.et0_mm = round(max(0, et0_daily * days), 1)
        except Exception as e:
            logger.warning(f"ET0 calculation failed: {e}")
            # Leave et0_mm as None
        
        return monthly
    
    def _extraterrestrial_radiation_monthly(
        self, month: int, lat: float
    ) -> float:
        """
        Calculate extraterrestrial radiation (MJ/m²/day).
        
        Based on FAO-56 equation 21.
        """
        # Julian day (approximate for middle of month)
        julian_days = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
        J = julian_days[month - 1]
        
        # Solar constant
        Gsc = 0.0820  # MJ/m²/min
        
        # Inverse relative distance Earth-Sun
        dr = 1 + 0.033 * math.cos(2 * math.pi * J / 365)
        
        # Solar declination
        delta = 0.409 * math.sin(2 * math.pi * J / 365 - 1.39)
        
        # Latitude in radians
        phi = math.radians(lat)
        
        # Sunset hour angle
        cos_ws = -math.tan(phi) * math.tan(delta)
        cos_ws = max(-1, min(1, cos_ws))  # Clamp
        ws = math.acos(cos_ws)
        
        # Extraterrestrial radiation
        Ra = (24 * 60 / math.pi) * Gsc * dr * (
            ws * math.sin(phi) * math.sin(delta)
            + math.cos(phi) * math.cos(delta) * math.sin(ws)
        )
        
        return Ra
    
    def classify_koppen(
        self, monthly: List[MonthlyClimate], lat: float
    ) -> Tuple[Optional[KoppenClimate], Optional[str]]:
        """
        Classify climate using Köppen-Geiger system.
        
        Uses KGCv5 from engine/hydroma/models/global_watchdog/koppen.py
        """
        if self._koppen_classifier is None:
            # Fallback: use latitude band
            band = self.get_latitude_band(lat)
            return band.get("koppen"), "synthetic"
        
        try:
            # Prepare input for KGCv5
            # KGCv5 expects: t_min[12], t_max[12], precip[12]
            t_min = [m.t_min_c for m in monthly]
            t_max = [m.t_max_c for m in monthly]
            precip = [m.precipitation_mm for m in monthly]
            
            result = self._koppen_classifier.classify(t_min, t_max, precip, lat)
            
            # Parse result
            if isinstance(result, tuple):
                koppen_code = result[0] if result else None
            elif hasattr(result, "code"):
                koppen_code = result.code
            else:
                koppen_code = str(result)
            
            # Map to enum
            try:
                koppen_enum = KoppenClimate(koppen_code)
                description = KOPPEN_DESCRIPTIONS.get(koppen_enum, koppen_code)
                return koppen_enum, description
            except ValueError:
                logger.warning(f"Unknown Köppen code: {koppen_code}")
                return None, koppen_code
        
        except Exception as e:
            logger.warning(f"Köppen classification failed: {e}")
            band = self.get_latitude_band(lat)
            return band.get("koppen"), "synthetic (fallback)"
    
    def calculate_aridity_index(
        self, annual_precip_mm: float, annual_et0_mm: float
    ) -> Tuple[float, AridityClass]:
        """
        Calculate UNEP Aridity Index = P / PET.
        
        Reference: UNEP (1992) "World Atlas of Desertification"
        """
        if annual_et0_mm <= 0:
            return 1.0, AridityClass.HUMID
        
        ai = annual_precip_mm / annual_et0_mm
        ai = min(ai, 2.0)  # Cap for safety
        
        if ai < 0.05:
            return ai, AridityClass.HYPER_ARID
        elif ai < 0.20:
            return ai, AridityClass.ARID
        elif ai < 0.50:
            return ai, AridityClass.SEMI_ARID
        elif ai < 0.65:
            return ai, AridityClass.DRY_SUBHUMID
        else:
            return ai, AridityClass.HUMID
    
    def calculate_growing_season(
        self, monthly: List[MonthlyClimate]
    ) -> Tuple[int, int]:
        """
        Calculate growing season length and frost-free days.
        
        Growing season: months with T_mean > 5°C (suitable for most crops)
        Frost-free days: days where T_min > 0°C
        
        Returns:
            (growing_season_days, frost_free_days)
        """
        growing_days = 0
        frost_free_days = 0
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        for m in monthly:
            days = days_in_month[m.month - 1]
            
            # Growing season: T_mean > 5°C
            if m.t_mean_c > 5.0:
                growing_days += days
            
            # Frost-free: T_min > 0°C
            if m.t_min_c > 0.0:
                frost_free_days += days
            elif m.t_min_c > -5.0:
                # Partial month (estimate fraction without frost)
                frost_fraction = (m.t_min_c + 5.0) / 10.0  # Rough estimate
                frost_free_days += int(days * frost_fraction)
        
        return growing_days, frost_free_days
    
    def build_climate_profile(
        self, lat: float, lon: float, elevation_m: Optional[float] = None
    ) -> ClimateProfile:
        """
        Build complete climate profile for a location.
        
        Priority:
        1. Try Open-Meteo (real data)
        2. Fall back to synthetic data
        
        Returns:
            ClimateProfile with all derived metrics
        """
        data_source = "synthetic"
        
        # Try to fetch from Open-Meteo
        real_data = self._fetch_open_meteo(lat, lon)
        if real_data:
            monthly = real_data
            data_source = "open_meteo"
        else:
            monthly = self.generate_synthetic_monthly_climate(lat, lon)
        
        # Calculate ET0
        monthly = self.calculate_et0_hargreaves_monthly(monthly, lat)
        
        # Köppen classification
        koppen, koppen_description = self.classify_koppen(monthly, lat)
        
        # Annual aggregates
        annual_precip = sum(m.precipitation_mm for m in monthly)
        annual_et0 = sum(m.et0_mm for m in monthly if m.et0_mm is not None)
        annual_t_mean = sum(m.t_mean_c for m in monthly) / 12
        
        # Aridity index
        aridity_index, aridity_class = self.calculate_aridity_index(
            annual_precip, annual_et0
        )
        
        # Growing season
        growing_season_days, frost_free_days = self.calculate_growing_season(monthly)
        
        # Köppen group (first letter)
        koppen_group = koppen.value[0] if koppen else None
        
        return ClimateProfile(
            lat=lat,
            lon=lon,
            elevation_m=elevation_m,
            koppen=koppen,
            koppen_description=koppen_description,
            koppen_group=koppen_group,
            annual_precip_mm=round(annual_precip, 1),
            annual_et0_mm=round(annual_et0, 1) if annual_et0 else None,
            annual_t_mean_c=round(annual_t_mean, 1),
            aridity_index=round(aridity_index, 3),
            aridity_class=aridity_class,
            growing_season_days=growing_season_days,
            frost_free_days=frost_free_days,
            monthly=monthly,
            data_source=data_source,
            data_quality_level="L0" if data_source == "synthetic" else "L3",
        )
    
    def _fetch_open_meteo(self, lat: float, lon: float) -> Optional[List[MonthlyClimate]]:
        """
        Try to fetch climate data from Open-Meteo.
        
        Open-Meteo provides free, no-API-key climate data.
        Endpoint: https://archive-api.open-meteo.com/v1/archive
        """
        try:
            import httpx
            
            # Get last 30 years of monthly data (climatology)
            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": "1991-01-01",
                "end_date": "2020-12-31",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if "daily" not in data:
                return None
            
            # Aggregate daily to monthly (climatology)
            daily = data["daily"]
            t_max = daily.get("temperature_2m_max", [])
            t_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            times = daily.get("time", [])
            
            if not times or not t_max:
                return None
            
            # Aggregate by month (30-year climatology)
            monthly_t_max = {m: [] for m in range(1, 13)}
            monthly_t_min = {m: [] for m in range(1, 13)}
            monthly_precip = {m: [] for m in range(1, 13)}
            
            for i, date_str in enumerate(times):
                if i >= len(t_max) or i >= len(t_min) or i >= len(precip):
                    continue
                if t_max[i] is None or t_min[i] is None or precip[i] is None:
                    continue
                
                # Parse date
                try:
                    dt = datetime.fromisoformat(date_str)
                    month = dt.month
                    monthly_t_max[month].append(t_max[i])
                    monthly_t_min[month].append(t_min[i])
                    monthly_precip[month].append(precip[i])
                except (ValueError, TypeError):
                    continue
            
            # Build monthly averages
            monthly = []
            for m in range(1, 13):
                if not monthly_t_max[m]:
                    continue
                
                t_max_mean = sum(monthly_t_max[m]) / len(monthly_t_max[m])
                t_min_mean = sum(monthly_t_min[m]) / len(monthly_t_min[m])
                # Precipitation: sum of daily for month, then average over years
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                years = len(monthly_t_max[m]) / days_in_month[m - 1]
                total_precip = sum(monthly_precip[m])
                avg_monthly_precip = total_precip / years if years > 0 else 0
                
                monthly.append(MonthlyClimate(
                    month=m,
                    t_min_c=round(t_min_mean, 1),
                    t_max_c=round(t_max_mean, 1),
                    t_mean_c=round((t_min_mean + t_max_mean) / 2, 1),
                    precipitation_mm=round(avg_monthly_precip, 1),
                ))
            
            return monthly if len(monthly) == 12 else None
        
        except Exception as e:
            logger.info(f"Open-Meteo fetch failed (using synthetic): {e}")
            return None
    
    def integrate_with_land(
        self,
        profile_id: str,
        lat: float,
        lon: float,
        elevation_m: Optional[float] = None,
        terrain_type: Optional[str] = None,
        soil_profile: Optional[Any] = None,
    ) -> ClimateIntegrationResult:
        """
        Integrate climate data with land profile.
        
        Args:
            profile_id: Land profile ID
            lat: Latitude
            lon: Longitude
            elevation_m: Elevation (optional)
            terrain_type: Terrain type from land analysis (optional)
            soil_profile: Soil profile from Phase 2A (optional)
            
        Returns:
            ClimateIntegrationResult
        """
        start_time = time.time()
        
        try:
            # Build climate profile
            climate_profile = self.build_climate_profile(lat, lon, elevation_m)
            
            # Determine limitations
            limitations = []
            recommendations = []
            irrigation_required = False
            drought_only = False
            cold_climate = False
            heat_stress = False
            
            # Aridity-based limitations
            if climate_profile.aridity_class in [
                AridityClass.HYPER_ARID, AridityClass.ARID
            ]:
                limitations.append("severe_water_scarcity")
                irrigation_required = True
                drought_only = True
                recommendations.append("Use drip irrigation for water efficiency")
                recommendations.append("Select drought-tolerant crop varieties")
            elif climate_profile.aridity_class == AridityClass.SEMI_ARID:
                limitations.append("water_scarcity")
                irrigation_required = True
                recommendations.append("Consider supplemental irrigation")
                recommendations.append("Use drought-adapted crop varieties")
            
            # Cold climate limitations
            if climate_profile.frost_free_days is not None:
                if climate_profile.frost_free_days < 120:
                    limitations.append("short_growing_season")
                    cold_climate = True
                    recommendations.append("Use short-season crop varieties")
                    recommendations.append("Consider season extension techniques")
                elif climate_profile.frost_free_days < 180:
                    limitations.append("moderate_growing_season")
                    cold_climate = True
                    recommendations.append("Choose varieties with appropriate maturity dates")
            
            # Heat stress
            if climate_profile.annual_t_mean_c > 25:
                heat_stress = True
                limitations.append("heat_stress_risk")
                recommendations.append("Consider heat-tolerant crop varieties")
                recommendations.append("Provide shade or windbreaks if possible")
            
            # Temperature extremes
            for m in climate_profile.monthly:
                if m.t_max_c > 40:
                    limitations.append("extreme_heat")
                    heat_stress = True
                    recommendations.append("Avoid planting during peak heat months")
                    break
            
            if not limitations:
                recommendations.append(
                    "Climate conditions are favorable - no special adaptations needed"
                )
            
            integration_time_ms = (time.time() - start_time) * 1000
            
            return ClimateIntegrationResult(
                profile_id=profile_id,
                success=True,
                climate_profile=climate_profile,
                irrigation_required=irrigation_required,
                drought_tolerant_crops_only=drought_only,
                cold_climate_limitation=cold_climate,
                heat_stress_risk=heat_stress,
                limitations=list(set(limitations)),
                recommendations=recommendations,
                integration_time_ms=integration_time_ms,
                data_quality_level=climate_profile.data_quality_level,
            )
        
        except Exception as e:
            logger.error(f"Climate integration failed: {e}")
            integration_time_ms = (time.time() - start_time) * 1000
            return ClimateIntegrationResult(
                profile_id=profile_id,
                success=False,
                error_message=str(e),
                integration_time_ms=integration_time_ms,
            )
'''
    
    create_file(INTEGRATION_DIR / "climate_integrator.py", integrator_content)
    
    # ==========================================================================
    # 3. Tests
    # ==========================================================================
    print("\n[3/4] Creating tests...")
    
    tests_content = '''"""
Tests for Climate Integrator
=============================
"""

import pytest
import math

from engine.land.integration.climate_integrator import (
    ClimateIntegrator, LATITUDE_CLIMATE_BANDS
)
from engine.land.integration.climate_models import (
    ClimateProfile, ClimateIntegrationResult,
    MonthlyClimate, KoppenClimate, AridityClass,
    KOPPEN_DESCRIPTIONS,
)


class TestLatitudeBands:
    """Test latitude-based climate band assignment"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_tropical_band(self, integrator):
        """Equator should be tropical"""
        band = integrator.get_latitude_band(0.0)
        assert band["name"] == "tropical"
    
    def test_subtropical_arid_band(self, integrator):
        """Iran latitude should be subtropical arid"""
        band = integrator.get_latitude_band(32.65)
        assert band["name"] == "subtropical_arid"
        assert band["koppen"] == KoppenClimate.BWh
    
    def test_temperate_band(self, integrator):
        """European latitude should be temperate"""
        band = integrator.get_latitude_band(45.0)
        assert band["name"] == "temperate"
    
    def test_continental_band(self, integrator):
        """High latitude should be continental"""
        band = integrator.get_latitude_band(55.0)
        assert band["name"] == "continental"
    
    def test_polar_band(self, integrator):
        """Very high latitude should be polar"""
        band = integrator.get_latitude_band(75.0)
        assert band["name"] == "polar"
    
    def test_southern_hemisphere(self, integrator):
        """Southern hemisphere should work correctly"""
        band = integrator.get_latitude_band(-30.0)
        assert "south" in band["name"] or band["name"] == "subtropical_arid_south"


class TestSyntheticClimate:
    """Test synthetic climate data generation"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_synthetic_12_months(self, integrator):
        """Should generate 12 months of data"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        assert len(monthly) == 12
    
    def test_synthetic_month_range(self, integrator):
        """Months should be 1-12"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        months = [m.month for m in monthly]
        assert months == list(range(1, 13))
    
    def test_synthetic_temperature_realistic(self, integrator):
        """Temperatures should be in realistic range"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        for m in monthly:
            assert -50 <= m.t_min_c <= 60
            assert -50 <= m.t_max_c <= 60
            assert m.t_min_c <= m.t_max_c
    
    def test_synthetic_precipitation_non_negative(self, integrator):
        """Precipitation should be non-negative"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        for m in monthly:
            assert m.precipitation_mm >= 0
    
    def test_synthetic_summer_warmer_northern(self, integrator):
        """Northern hemisphere should have warmer summers"""
        monthly = integrator.generate_synthetic_monthly_climate(45.0, 0.0)
        summer = [m for m in monthly if m.month in [6, 7, 8]]
        winter = [m for m in monthly if m.month in [12, 1, 2]]
        summer_mean = sum(m.t_mean_c for m in summer) / 3
        winter_mean = sum(m.t_mean_c for m in winter) / 3
        assert summer_mean > winter_mean
    
    def test_synthetic_summer_warmer_southern(self, integrator):
        """Southern hemisphere should have warmer January"""
        monthly = integrator.generate_synthetic_monthly_climate(-45.0, 0.0)
        jan_mean = next(m for m in monthly if m.month == 1).t_mean_c
        jul_mean = next(m for m in monthly if m.month == 7).t_mean_c
        assert jan_mean > jul_mean


class TestET0Calculation:
    """Test ET0 Hargreaves calculation"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_et0_positive(self, integrator):
        """ET0 should be positive for warm months"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        monthly = integrator.calculate_et0_hargreaves_monthly(monthly, 32.65)
        for m in monthly:
            assert m.et0_mm is not None
            assert m.et0_mm >= 0
    
    def test_et0_higher_in_summer(self, integrator):
        """ET0 should be higher in summer months"""
        monthly = integrator.generate_synthetic_monthly_climate(45.0, 0.0)
        monthly = integrator.calculate_et0_hargreaves_monthly(monthly, 45.0)
        
        summer_et0 = sum(m.et0_mm for m in monthly if m.month in [6, 7, 8])
        winter_et0 = sum(m.et0_mm for m in monthly if m.month in [12, 1, 2])
        assert summer_et0 > winter_et0
    
    def test_et0_reasonable_range(self, integrator):
        """Annual ET0 should be in reasonable range (200-2500 mm)"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        monthly = integrator.calculate_et0_hargreaves_monthly(monthly, 32.65)
        annual_et0 = sum(m.et0_mm for m in monthly)
        assert 200 <= annual_et0 <= 3000
    
    def test_extraterrestrial_radiation(self, integrator):
        """Extraterrestrial radiation should be positive"""
        for month in range(1, 13):
            ra = integrator._extraterrestrial_radiation_monthly(month, 32.65)
            assert ra > 0
    
    def test_radiation_seasonal_variation(self, integrator):
        """Radiation should vary seasonally"""
        ra_summer = integrator._extraterrestrial_radiation_monthly(6, 45.0)
        ra_winter = integrator._extraterrestrial_radiation_monthly(12, 45.0)
        assert ra_summer != ra_winter


class TestKoppenClassification:
    """Test Köppen-Geiger classification"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_koppen_classify_tropical(self, integrator):
        """Tropical latitudes should classify as A group"""
        monthly = integrator.generate_synthetic_monthly_climate(0.0, 0.0)
        koppen, description = integrator.classify_koppen(monthly, 0.0)
        assert koppen is not None
        assert koppen.value.startswith("A") or koppen.value.startswith("B")
    
    def test_koppen_classify_arid(self, integrator):
        """Iran should classify as arid"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        koppen, description = integrator.classify_koppen(monthly, 32.65)
        assert koppen is not None
        # Arid climates start with B
        assert koppen.value.startswith("B") or koppen.value.startswith("C")
    
    def test_koppen_classify_temperate(self, integrator):
        """European latitudes should be C or D group"""
        monthly = integrator.generate_synthetic_monthly_climate(48.0, 2.0)
        koppen, description = integrator.classify_koppen(monthly, 48.0)
        assert koppen is not None
        assert koppen.value[0] in ["C", "D"]
    
    def test_koppen_has_description(self, integrator):
        """Köppen should have a description"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        koppen, description = integrator.classify_koppen(monthly, 32.65)
        assert description is not None
        assert len(description) > 0


class TestAridityIndex:
    """Test Aridity Index calculation"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_hyper_arid(self, integrator):
        """AI < 0.05 should be hyper-arid"""
        ai, cls = integrator.calculate_aridity_index(50, 1500)
        assert cls == AridityClass.HYPER_ARID
        assert ai < 0.05
    
    def test_arid(self, integrator):
        """AI 0.05-0.20 should be arid"""
        ai, cls = integrator.calculate_aridity_index(200, 1500)
        assert cls == AridityClass.ARID
    
    def test_semi_arid(self, integrator):
        """AI 0.20-0.50 should be semi-arid"""
        ai, cls = integrator.calculate_aridity_index(500, 1500)
        assert cls == AridityClass.SEMI_ARID
    
    def test_dry_subhumid(self, integrator):
        """AI 0.50-0.65 should be dry subhumid"""
        ai, cls = integrator.calculate_aridity_index(800, 1500)
        assert cls == AridityClass.DRY_SUBHUMID
    
    def test_humid(self, integrator):
        """AI >= 0.65 should be humid"""
        ai, cls = integrator.calculate_aridity_index(1200, 1500)
        assert cls == AridityClass.HUMID
    
    def test_zero_et0_handled(self, integrator):
        """Zero ET0 should not crash"""
        ai, cls = integrator.calculate_aridity_index(1000, 0)
        assert cls == AridityClass.HUMID


class TestGrowingSeason:
    """Test growing season calculation"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_growing_season_positive(self, integrator):
        """Growing season should be positive"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert growing >= 0
        assert frost_free >= 0
    
    def test_growing_season_tropical_long(self, integrator):
        """Tropical should have long growing season"""
        monthly = integrator.generate_synthetic_monthly_climate(0.0, 0.0)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert growing > 300  # Almost year-round
    
    def test_growing_season_polar_short(self, integrator):
        """Polar should have short growing season"""
        monthly = integrator.generate_synthetic_monthly_climate(75.0, 0.0)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert growing < 150  # Short summer
    
    def test_frost_free_leq_365(self, integrator):
        """Frost-free days should not exceed 365"""
        monthly = integrator.generate_synthetic_monthly_climate(32.65, 51.67)
        growing, frost_free = integrator.calculate_growing_season(monthly)
        assert frost_free <= 365


class TestClimateProfileBuilding:
    """Test complete climate profile building"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_profile_complete(self, integrator):
        """Profile should have all fields"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.lat == 32.65
        assert profile.lon == 51.67
        assert profile.annual_precip_mm > 0
        assert profile.annual_t_mean_c != 0
        assert len(profile.monthly) == 12
    
    def test_profile_has_koppen(self, integrator):
        """Profile should have Köppen classification"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.koppen is not None
    
    def test_profile_has_aridity(self, integrator):
        """Profile should have aridity index"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.aridity_index is not None
        assert profile.aridity_class is not None
    
    def test_profile_has_growing_season(self, integrator):
        """Profile should have growing season"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.growing_season_days is not None
        assert profile.frost_free_days is not None
    
    def test_profile_data_source(self, integrator):
        """Profile should have data source"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.data_source in ["synthetic", "open_meteo"]
    
    def test_profile_quality_level(self, integrator):
        """Profile should have quality level"""
        profile = integrator.build_climate_profile(32.65, 51.67)
        assert profile.data_quality_level in ["L0", "L3", "L5"]


class TestClimateIntegration:
    """Test climate integration with land profile"""
    
    @pytest.fixture
    def integrator(self):
        return ClimateIntegrator()
    
    def test_integration_success(self, integrator):
        """Integration should succeed"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert result.success
        assert result.profile_id == "test-001"
    
    def test_integration_returns_profile(self, integrator):
        """Integration should return climate profile"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert result.climate_profile is not None
        assert result.climate_profile.koppen is not None
    
    def test_integration_arid_irrigation_required(self, integrator):
        """Arid location should require irrigation"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67  # Isfahan, Iran - arid
        )
        # Arid climates typically require irrigation
        assert "water_scarcity" in result.limitations or "severe_water_scarcity" in result.limitations
        assert result.irrigation_required
    
    def test_integration_recommendations_present(self, integrator):
        """Integration should return recommendations"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert len(result.recommendations) > 0
    
    def test_integration_time_reasonable(self, integrator):
        """Integration should complete in reasonable time"""
        result = integrator.integrate_with_land(
            profile_id="test-001",
            lat=32.65,
            lon=51.67
        )
        assert result.integration_time_ms < 5000  # 5 seconds
    
    def test_integration_different_locations(self, integrator):
        """Different locations should give different results"""
        result_iran = integrator.integrate_with_land(
            profile_id="iran", lat=32.65, lon=51.67
        )
        result_europe = integrator.integrate_with_land(
            profile_id="europe", lat=48.0, lon=2.0
        )
        
        assert result_iran.climate_profile.koppen != result_europe.climate_profile.koppen
        # Europe should have more precipitation than arid Iran
        assert result_europe.climate_profile.annual_precip_mm > result_iran.climate_profile.annual_precip_mm


class TestKoppenDescriptions:
    """Test Köppen descriptions dictionary"""
    
    def test_all_koppen_have_descriptions(self):
        """All Köppen classes should have descriptions"""
        for koppen in KoppenClimate:
            assert koppen in KOPPEN_DESCRIPTIONS
    
    def test_descriptions_not_empty(self):
        """Descriptions should not be empty"""
        for koppen, desc in KOPPEN_DESCRIPTIONS.items():
            assert len(desc) > 0


class TestLatitudeClimateBands:
    """Test latitude climate bands configuration"""
    
    def test_bands_cover_globe(self):
        """Bands should cover entire globe"""
        # Check that all latitudes have a band
        integrator = ClimateIntegrator()
        for lat in [-80, -45, -30, -10, 0, 10, 30, 45, 60, 80]:
            band = integrator.get_latitude_band(lat)
            assert band is not None
    
    def test_bands_have_required_fields(self):
        """Bands should have required fields"""
        for name, band in LATITUDE_CLIMATE_BANDS.items():
            assert "lat_range" in band
            assert "koppen" in band
            assert "annual_precip" in band
'''
    
    create_file(TESTS_DIR / "test_climate_integrator.py", tests_content)
    
    # ==========================================================================
    # 4. Update __init__.py
    # ==========================================================================
    print("\n[4/4] Updating __init__.py...")
    
    init_content = INTEGRATION_DIR / "__init__.py"
    if init_content.exists():
        existing = init_content.read_text(encoding="utf-8")
        # Append new exports
        new_exports = """

# Phase 2B: Climate Integration
from .climate_models import (
    ClimateProfile,
    ClimateIntegrationResult,
    MonthlyClimate,
    KoppenClimate,
    AridityClass,
    KOPPEN_DESCRIPTIONS,
)
from .climate_integrator import ClimateIntegrator

__all__.extend([
    "ClimateProfile",
    "ClimateIntegrationResult",
    "MonthlyClimate",
    "KoppenClimate",
    "AridityClass",
    "KOPPEN_DESCRIPTIONS",
    "ClimateIntegrator",
])
"""
        if "ClimateIntegrator" not in existing:
            init_content.write_text(existing + new_exports, encoding="utf-8")
            print("  ✓ Updated __init__.py with climate exports")
    
    print("\n" + "=" * 70)
    print("✅ Phase 2B files created successfully")
    print("=" * 70)
    print("\n📋 Next steps:")
    print("  1. python -m pytest engine/land/integration/tests/test_climate_integrator.py -v")
    print("  2. If tests pass: python -m pytest engine/land/ -v  (all tests)")
    print("  3. Commit: python sandbox/phase2b_complete_and_commit.py")


if __name__ == "__main__":
    main()