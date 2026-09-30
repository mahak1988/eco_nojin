"""Inter-model data contracts for the simulation chain (Phase 3).

Every model output carries an explicit provenance: ``data_source`` is
"simulated" for model runs (never mislabeled as measured data) and the
``model`` field records the engine (name + version) so dashboards can show
where a number came from.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from engine.hydroma.provenance import DataSource, Provenance, ProvenanceCarrier


class MonthClimate(BaseModel):
    """One monthly climate slice used by the RothC runner."""

    year: int = Field(..., ge=1900)
    month: int = Field(..., ge=1, le=12)
    tmean_c: float = Field(..., ge=-40, le=60, description="Mean monthly air temperature (C)")
    smd_mm: float = Field(..., ge=0, description="Soil moisture deficit (mm)")
    max_smd_mm: float = Field(..., gt=0, description="Max soil moisture deficit (mm)")


class ScenarioParams(BaseModel):
    """Intervention scenario parameter matrix (shared across the chain)."""

    name: Literal["Baseline", "Medium", "Intensive"]
    cn_change: float = Field(..., description="Curve-number change (negative = less runoff)")
    c_factor_factor: float = Field(
        ..., gt=0, le=1, description="Multiplier applied to the RUSLE C-factor"
    )
    p_factor: float = Field(..., gt=0, le=1, description="RUSLE support-practice factor")


class RusleOutput(BaseModel):
    """RUSLE soil-loss result for before/after intervention."""

    erosion_before_t_ha: float | None = None
    erosion_after_t_ha: float | None = None
    reduction_pct: float | None = None
    data_source: Literal["simulated"] = "simulated"
    model: str = "RUSLE (C++ core or analytic product)"


class AquacropOutput(BaseModel):
    """AquaCrop-OSPy crop-simulation result for one season."""

    crop: str | None = None
    yield_kg_ha: float | None = None
    biomass_kg_ha: float | None = None
    residue_kg_ha: float | None = None
    et_mm: float | None = None
    wue_kg_m3: float | None = None
    data_source: Literal["simulated"] = "simulated"
    model: str = "AquaCrop-OSPy 3.1.0"


class RothcOutput(BaseModel):
    """RothC soil-carbon result (one run window)."""

    soc_before_t_ha: float | None = None
    soc_after_t_ha: float | None = None
    soc_change_t_ha_yr: float | None = None
    co2_respired_t_ha: float | None = None
    co2e_t_ha: float | None = None
    data_source: Literal["simulated"] = "simulated"
    model: str = "RothC (in-house port, pending reference validation)"


class ChainInputs(BaseModel):
    """Everything the orchestrator needs to run one scenario for one site."""

    site_id: str = Field(..., min_length=1, max_length=200)
    area_ha: float = Field(..., gt=0)
    scenario: ScenarioParams

    # RUSLE
    r_factor: float = Field(..., gt=0, description="Rainfall erosivity (MJ mm ha-1 h-1 yr-1)")
    k_factor: float = Field(..., gt=0, description="Soil erodibility (t h MJ-1 mm-1)")
    ls_factor: float = Field(..., gt=0, description="Slope length/steepness factor")
    c_factor_base: float = Field(..., gt=0, le=1, description="Baseline cover-management factor")

    # AquaCrop
    crop: str = "Wheat"
    soil_type: str = "SiltLoam"
    planting_date: str = "2020/03/01"
    harvest_date: str = "2020/07/20"
    lat: float | None = Field(None, ge=-90, le=90, description="Site latitude (real weather)")
    lon: float | None = Field(None, ge=-180, le=180, description="Site longitude (real weather)")
    use_real_weather: bool = Field(
        False, description="Fetch Open-Meteo historical weather instead of synthetic"
    )

    # RothC
    initial_soc_t_ha: float = Field(..., gt=0)
    clay_pct: float = Field(..., ge=0, le=100)
    residue_c_t_ha_per_month: float = Field(0.0, ge=0)
    monthly_climate: list[MonthClimate] | None = None
    years: int = Field(1, ge=1, le=100)


class ChainResult(BaseModel):
    """Output of one full chain execution."""

    site_id: str
    scenario: str
    area_ha: float
    outputs: dict[str, Any]
    status: Literal["ok", "partial", "failed"]
    message: str = ""
    executed_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════
# PHASE 3: WATER INTELLIGENCE CONTRACTS
# ═══════════════════════════════════════════════════════════════════


class GroundwaterInput(BaseModel):
    """Input contract for groundwater analysis."""

    land_profile_id: str
    well_depth_m: float
    water_table_depth_m: float
    hydraulic_conductivity_m_s: float
    aquifer_thickness_m: float
    aquifer_type: str = "unconfined"
    recharge_rate_mm_yr: float = 0.0
    abstraction_rate_m3_yr: float = 0.0
    tds_mg_l: float = 0.0
    porosity: float = 0.3
    specific_yield: float = 0.15


class GroundwaterOutput(Provenance, BaseModel):
    """Output contract for groundwater analysis."""

    land_profile_id: str
    darcy_flux_m_s: float
    transmissivity_m2_s: float
    specific_capacity_m2_s: float
    sustainability_index: float
    safe_yield_m3_yr: float
    reserve_m3: float
    water_quality_class: str
    overexploitation_risk: str
    contamination_risk: str
    recommendations: list[str]
    status: str


class WatershedInput(BaseModel):
    """Input contract for watershed analysis."""

    land_profile_id: str
    stream_network: dict
    stream_lengths: dict[str, float]
    catchment_area_km2: float
    main_channel_length_m: float
    average_slope_m_m: float


class WatershedOutput(Provenance, BaseModel):
    """Output contract for watershed analysis."""

    land_profile_id: str
    strahler_max_order: int
    stream_count: int
    horton_Rb: float
    horton_Rl: float
    kirpich_tc_minutes: float
    order_counts: dict[int, int]
    flood_risk: str


class WaterQualityInput(BaseModel):
    """Input contract for water quality analysis."""

    land_profile_id: str
    sample_date: str
    tds_mg_l: float
    ph: float
    ec_dsm_cm: float
    chloride_mg_l: float = 0.0
    nitrate_mg_l: float = 0.0
    fluoride_mg_l: float = 0.0
    hardness_mg_l: float = 0.0


class WaterQualityOutput(Provenance, BaseModel):
    """Output contract for water quality analysis."""

    land_profile_id: str
    sample_date: str
    quality_class: str
    wqi_score: float  # Water Quality Index (0-100)
    suitable_for: list[str]
    health_risk: str
    treatment_needed: bool


class SWATInput:
    """Placeholder for compatibility with old tests."""

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class SWATOutput(ProvenanceCarrier):
    """Placeholder for compatibility with old tests."""

    _FIELDS = (
        "water_yield_m3",
        "runoff_m3",
        "sediment_yield_t",
        "evapotranspiration_mm",
        "start_date",
        "end_date",
    )

    def __init__(self, *args, data_source: DataSource, model: str, **kwargs):
        super().__init__(data_source=data_source, model=model)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def model_dump(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class AquaCropInput:
    """Placeholder for compatibility with old tests."""

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class AquaCropOutput(ProvenanceCarrier):
    """Placeholder for compatibility with old tests."""

    _FIELDS = ("yield_t_ha", "biomass_t_ha", "water_use_mm")

    def __init__(self, *args, data_source: DataSource, model: str, **kwargs):
        super().__init__(data_source=data_source, model=model)
        for k, v in kwargs.items():
            setattr(self, k, v)


class RothCInput:
    """Placeholder for compatibility with old tests."""

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class RothCOutput(ProvenanceCarrier):
    """Placeholder for compatibility with old tests."""

    _FIELDS = ("total_soc", "co2_emitted")

    def __init__(self, *args, data_source: DataSource, model: str, **kwargs):
        super().__init__(data_source=data_source, model=model)
        for k, v in kwargs.items():
            setattr(self, k, v)


class HECRASInput:
    """Placeholder for compatibility."""

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class HECRASOutput(ProvenanceCarrier):
    """Placeholder for compatibility."""

    _FIELDS = (
        "water_surface_profile",
        "shear_stress_pa",
        "velocity_m_s",
        "flood_extent",
        "structure_safety",
    )

    def __init__(self, *args, data_source: DataSource, model: str, **kwargs):
        super().__init__(data_source=data_source, model=model)
        for k, v in kwargs.items():
            setattr(self, k, v)


class RUSLEInput:
    """Placeholder for compatibility."""

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class RUSLEOutput(ProvenanceCarrier):
    """Placeholder for compatibility."""

    _FIELDS = ("soil_loss_t_ha", "gross_erosion_t")

    def __init__(self, *args, data_source: DataSource, model: str, **kwargs):
        super().__init__(data_source=data_source, model=model)
        for k, v in kwargs.items():
            setattr(self, k, v)


class WEAPInput:
    """Placeholder for compatibility."""

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class WEAPOutput(ProvenanceCarrier):
    """Placeholder for compatibility."""

    _FIELDS = ("water_allocation_m3", "unmet_demand_m3", "water_balance", "allocation_efficiency")

    def __init__(self, *args, data_source: DataSource, model: str, **kwargs):
        super().__init__(data_source=data_source, model=model)
        for k, v in kwargs.items():
            setattr(self, k, v)
