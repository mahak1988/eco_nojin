from datetime import date

from pydantic import BaseModel


class SWATInput(BaseModel):
    """قرارداد ورودی برای مدل SWAT+"""

    land_profile_id: str
    climate_data: list[dict]
    soil_data: list[dict]
    land_use: list[str]
    management_practices: list[str]
    start_date: date
    end_date: date
    time_step: str = "daily"


class SWATOutput(BaseModel):
    """قرارداد خروجی از مدل SWAT+"""

    runoff_m3: list[float]
    soil_water_content: list[float]
    recharge_mm: list[float]
    groundwater_recharge_mm: list[float]
    sediment_yield_t: list[float]
    et_mm: list[float]
    water_yield_m3: list[float]


class RUSLEInput(BaseModel):
    """قرارداد ورودی برای مدل RUSLE"""

    land_profile_id: str
    rainfall_erosivity: float
    soil_erodibility: float
    slope_length_factor: float
    slope_steepness_factor: float
    cover_factor: float
    management_factor: float


class RUSLEOutput(BaseModel):
    """قرارداد خروجی از مدل RUSLE"""

    erosion_rate_t_ha_yr: float
    erosion_risk_class: str
    hotspots: list[dict]
    intervention_priority: list[dict]


class RothCInput(BaseModel):
    """قرارداد ورودی برای مدل RothC"""

    land_profile_id: str
    soil_organic_carbon_t_ha: float
    crop_residues_t_ha: float
    temperature_data: list[float]
    rainfall_data: list[float]
    clay_content_percent: float
    start_date: date
    end_date: date


class RothCOutput(BaseModel):
    """قرارداد خروجی از مدل RothC"""

    soc_change_t_ha_yr: float
    soc_final_t_ha: float
    carbon_sequestration_t_co2e_yr: float
    carbon_balance: float
    mrV_data: dict


class AquaCropInput(BaseModel):
    """قرارداد ورودی برای مدل AquaCrop"""

    land_profile_id: str
    crop_type: str
    climate_data: list[dict]
    soil_data: list[dict]
    irrigation_data: list[dict]
    planting_date: date
    harvest_date: date


class AquaCropOutput(BaseModel):
    """قرارداد خروجی از مدل AquaCrop"""

    yield_t_ha: float
    biomass_t_ha: float
    wue_kg_m3: float
    water_demand_mm: list[float]
    crop_residue_t_ha: float
    growth_stage_data: list[dict]


class WEAPInput(BaseModel):
    """قرارداد ورودی برای مدل WEAP"""

    land_profile_id: str
    water_demand_data: list[float]
    water_supply_data: list[float]
    allocation_rules: list[dict]
    start_date: date
    end_date: date


class WEAPOutput(BaseModel):
    """قرارداد خروجی از مدل WEAP"""

    water_allocation_m3: list[float]
    unmet_demand_m3: list[float]
    water_balance: dict
    allocation_efficiency: float


class HECRASInput(BaseModel):
    """قرارداد ورودی برای مدل HEC-RAS"""

    land_profile_id: str
    channel_geometry: dict
    boundary_conditions: dict
    initial_conditions: dict
    start_date: date
    end_date: date
    time_step: str = "hourly"


class HECRASOutput(BaseModel):
    """قرارداد خروجی از مدل HEC-RAS"""

    water_surface_profile: list[float]
    shear_stress_pa: list[float]
    velocity_m_s: list[float]
    flood_extent: dict
    structure_safety: dict
