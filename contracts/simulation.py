from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class SWATInput(BaseModel):
    """قرارداد ورودی برای مدل SWAT+"""
    land_profile_id: str
    climate_data: List[dict]
    soil_data: List[dict]
    land_use: List[str]
    management_practices: List[str]
    start_date: date
    end_date: date
    time_step: str = "daily"

class SWATOutput(BaseModel):
    """قرارداد خروجی از مدل SWAT+"""
    runoff_m3: List[float]
    soil_water_content: List[float]
    recharge_mm: List[float]
    groundwater_recharge_mm: List[float]
    sediment_yield_t: List[float]
    et_mm: List[float]
    water_yield_m3: List[float]

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
    hotspots: List[dict]
    intervention_priority: List[dict]

class RothCInput(BaseModel):
    """قرارداد ورودی برای مدل RothC"""
    land_profile_id: str
    soil_organic_carbon_t_ha: float
    crop_residues_t_ha: float
    temperature_data: List[float]
    rainfall_data: List[float]
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
    climate_data: List[dict]
    soil_data: List[dict]
    irrigation_data: List[dict]
    planting_date: date
    harvest_date: date

class AquaCropOutput(BaseModel):
    """قرارداد خروجی از مدل AquaCrop"""
    yield_t_ha: float
    biomass_t_ha: float
    wue_kg_m3: float
    water_demand_mm: List[float]
    crop_residue_t_ha: float
    growth_stage_data: List[dict]

class WEAPInput(BaseModel):
    """قرارداد ورودی برای مدل WEAP"""
    land_profile_id: str
    water_demand_data: List[float]
    water_supply_data: List[float]
    allocation_rules: List[dict]
    start_date: date
    end_date: date

class WEAPOutput(BaseModel):
    """قرارداد خروجی از مدل WEAP"""
    water_allocation_m3: List[float]
    unmet_demand_m3: List[float]
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
    water_surface_profile: List[float]
    shear_stress_pa: List[float]
    velocity_m_s: List[float]
    flood_extent: dict
    structure_safety: dict
