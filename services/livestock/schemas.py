"""Pydantic schemas for Livestock"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnimalType(str, Enum):
    CATTLE = "cattle"
    SHEEP = "sheep"
    GOAT = "goat"
    POULTRY = "poultry"
    HORSE = "horse"
    DONKEY = "donkey"

class ProductionSystem(str, Enum):
    GRAZING = "grazing"
    MIXED = "mixed"
    INTENSIVE = "intensive"
    PASTORAL = "pastoral"

class ForageQuality(BaseModel):
    """کیفیت علوفه (از داده‌های ماهواره‌ای NDVI)"""
    ndvi_value: float = 0.5
    crude_protein_pct: float = 12.0
    digestibility_pct: float = 60.0
    dry_matter_ton_ha: float = 3.0
    season: str = "spring"

class HerdProfile(BaseModel):
    animal_type: AnimalType
    head_count: int = 10
    breed: str | None = None
    production_system: ProductionSystem = ProductionSystem.MIXED
    average_age_months: int = 36
    female_ratio_pct: float = 70.0

class LivestockSimulationRequest(BaseModel):
    simulation_id: str = Field(default_factory=lambda: "livestock-" + str(int(datetime.now().timestamp())))
    herd: HerdProfile
    forage: ForageQuality = Field(default_factory=ForageQuality)
    land_area_ha: float = 10.0
    water_availability_m3_day: float = 100.0
    simulation_days: int = 365
    market_prices: dict[str, float] | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)

class AnimalProduction(BaseModel):
    milk_kg_day: float = 0.0
    meat_kg_year: float = 0.0
    wool_kg_year: float = 0.0
    eggs_day: float = 0.0
    manure_kg_day: float = 0.0
    offspring_per_year: float = 0.0

class FeedRequirement(BaseModel):
    dry_matter_kg_day: float = 0.0
    metabolizable_energy_mj_day: float = 0.0
    water_liters_day: float = 0.0
    supplement_kg_day: float = 0.0
    grazing_hours: float = 0.0

class HealthRisk(BaseModel):
    disease_risk_score: float = 0.0
    mortality_rate_pct: float = 2.0
    heat_stress_risk: str = "low"
    parasitic_risk: str = "low"

class ManureContribution(BaseModel):
    """اثر کود دامی بر خاک"""
    total_kg_year: float = 0.0
    nitrogen_kg_year: float = 0.0
    phosphorus_kg_year: float = 0.0
    potassium_kg_year: float = 0.0
    organic_carbon_kg_year: float = 0.0
    soil_carbon_boost_ton_ha_year: float = 0.0

class EnvironmentalImpact(BaseModel):
    methane_kg_co2e_year: float = 0.0
    water_footprint_m3_year: float = 0.0
    grazing_pressure_index: float = 0.0
    carrying_capacity_head: int = 0

class EconomicAnalysis(BaseModel):
    """تحلیل اقتصادی گله"""
    gross_revenue_usd_year: float = 0.0
    feed_cost_usd_year: float = 0.0
    veterinary_cost_usd_year: float = 0.0
    labor_cost_usd_year: float = 0.0
    other_costs_usd_year: float = 0.0
    total_costs_usd_year: float = 0.0
    net_profit_usd_year: float = 0.0
    profit_margin_pct: float = 0.0
    roi_pct: float = 0.0
    break_even_head_count: int = 0

class LivestockSimulationResult(BaseModel):
    simulation_id: str
    animal_type: AnimalType
    herd_size: int
    status: str = "completed"
    started_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    production: AnimalProduction = Field(default_factory=AnimalProduction)
    feed_requirements: FeedRequirement = Field(default_factory=FeedRequirement)
    health: HealthRisk = Field(default_factory=HealthRisk)
    manure: ManureContribution = Field(default_factory=ManureContribution)
    environmental: EnvironmentalImpact = Field(default_factory=EnvironmentalImpact)
    economics: EconomicAnalysis = Field(default_factory=EconomicAnalysis)
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
