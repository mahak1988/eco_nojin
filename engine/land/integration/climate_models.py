"""
Climate Integration Models
===========================
Models for climate data integration with land profiles.
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from engine.hydroma.provenance import ResultProvenance

#: Maps this package's fine-grained provenance vocabulary onto the canonical
#: ``DataSource`` literal that ``ResultProvenance`` enforces.
#:
#: ``open_meteo`` is a real retrieval -- 30 years of daily records from the
#: Open-Meteo archive -- so it is ``measured``. ``synthetic`` is a series this
#: package generated from latitude bands, so it is ``simulated``. The mapping
#: loses no information: the exact value is preserved in
#: ``data_source_detail``.
_DATA_SOURCE_TO_CANONICAL = {
    "open_meteo": "measured",
    "synthetic": "simulated",
}


class KoppenClimate(StrEnum):
    """Köppen-Geiger climate classification (simplified main groups)"""

    Af = "Af"  # Tropical rainforest
    Am = "Am"  # Tropical monsoon
    Aw = "Aw"  # Tropical savanna
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
    ET = "ET"  # Tundra
    EF = "EF"  # Ice cap


class AridityClass(StrEnum):
    """UNEP Aridity Index classification"""

    # The index could not be computed, typically because reference
    # evapotranspiration was unavailable. This is not a climate class and must
    # not be mapped onto one: absence of ET0 is not evidence of a wet climate.
    UNKNOWN = "unknown"
    HYPER_ARID = "hyper_arid"  # AI < 0.05
    ARID = "arid"  # 0.05 <= AI < 0.20
    SEMI_ARID = "semi_arid"  # 0.20 <= AI < 0.50
    DRY_SUBHUMID = "dry_subhumid"  # 0.50 <= AI < 0.65
    HUMID = "humid"  # AI >= 0.65


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
    et0_mm: float | None = Field(None, ge=0, description="Reference ET (mm)")

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
    elevation_m: float | None = None

    # Köppen-Geiger
    koppen: KoppenClimate | None = None
    koppen_description: str | None = None
    koppen_group: str | None = None  # A, B, C, D, E

    # Annual aggregates
    annual_precip_mm: float = Field(..., ge=0, description="Annual precipitation (mm)")
    annual_et0_mm: float | None = Field(None, ge=0, description="Annual ET0 (mm)")
    annual_t_mean_c: float = Field(..., description="Annual mean temperature (°C)")

    # Aridity
    aridity_index: float | None = Field(None, ge=0, description="Aridity Index = P/PET")
    aridity_class: AridityClass | None = None

    # Growing season
    growing_season_days: int | None = Field(None, ge=0, description="Growing season length (days)")
    frost_free_days: int | None = Field(None, ge=0, description="Frost-free days per year")

    # Monthly data
    monthly: list[MonthlyClimate] = Field(default_factory=list)

    # Metadata
    data_source: str | None = None  # "open_meteo", "era5", "synthetic"
    data_quality_level: str | None = None  # L0-L5
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ClimateIntegrationResult(ResultProvenance, BaseModel):
    """Result of climate integration with land profile"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "success": True,
                "climate_profile": {"koppen": "BWh"},
                "capabilities": {"irrigation_required": True, "drought_tolerant_crops_only": True},
            }
        }
    )

    profile_id: str
    success: bool = True
    error_message: str | None = None

    climate_profile: ClimateProfile | None = None

    # Capabilities derived from climate
    irrigation_required: bool = False
    drought_tolerant_crops_only: bool = False
    cold_climate_limitation: bool = False
    heat_stress_risk: bool = False

    # Limitations
    limitations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    # Integration metadata
    integrated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    integration_time_ms: float | None = None
    data_quality_level: str | None = None

    #: The provenance value this package actually had, before it was folded onto
    #: the canonical ``DataSource`` literal -- ``"open_meteo"`` or
    #: ``"synthetic"``. Kept so the normaliser below is lossless.
    data_source_detail: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _fold_data_source_onto_canonical_literal(cls, data):
        """Accept this package's own vocabulary for ``data_source``.

        ``build_climate_profile`` sets ``data_source`` to ``"open_meteo"`` or
        ``"synthetic"`` and ``integrate_with_land`` propagates it verbatim. Those
        are honest values, but they are not in ``DataSource``, so pydantic
        rejected them -- and because ``integrate_with_land`` wraps its body in
        ``except Exception``, the rejection was swallowed and turned into a
        ``success=False`` result carrying a validation error. Every integration
        therefore failed, including the ones that had real data.

        Unmapped values are passed through unchanged rather than coerced, so a
        genuine typo still raises instead of being silently reinterpreted.
        """
        if not isinstance(data, dict):
            return data
        raw = data.get("data_source")
        if not isinstance(raw, str) or raw not in _DATA_SOURCE_TO_CANONICAL:
            return data
        folded = dict(data)
        folded["data_source_detail"] = raw
        folded["data_source"] = _DATA_SOURCE_TO_CANONICAL[raw]
        return folded


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
