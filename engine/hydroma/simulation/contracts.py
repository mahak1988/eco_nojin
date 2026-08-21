"""Inter-model data contracts for the simulation chain (Phase 3).

Every model output carries an explicit provenance: ``data_source`` is
"simulated" for model runs (never mislabeled as measured data) and the
``model`` field records the engine (name + version) so dashboards can show
where a number came from.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


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
    c_factor_factor: float = Field(..., gt=0, le=1, description="Multiplier applied to the RUSLE C-factor")
    p_factor: float = Field(..., gt=0, le=1, description="RUSLE support-practice factor")


class RusleOutput(BaseModel):
    """RUSLE soil-loss result for before/after intervention."""

    erosion_before_t_ha: float
    erosion_after_t_ha: float
    reduction_pct: float
    data_source: Literal["simulated"] = "simulated"
    model: str = "RUSLE (C++ core or analytic product)"


class AquacropOutput(BaseModel):
    """AquaCrop-OSPy crop-simulation result for one season."""

    crop: str
    yield_kg_ha: float | None = None
    biomass_kg_ha: float | None = None
    residue_kg_ha: float | None = None
    et_mm: float | None = None
    wue_kg_m3: float | None = None
    data_source: Literal["simulated"] = "simulated"
    model: str = "AquaCrop-OSPy 3.1.0"


class RothcOutput(BaseModel):
    """RothC soil-carbon result (one run window)."""

    soc_before_t_ha: float
    soc_after_t_ha: float
    soc_change_t_ha_yr: float
    co2_respired_t_ha: float
    co2e_t_ha: float
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
