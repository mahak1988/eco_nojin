"""کلاس پایه برای تمام شبیه‌سازهای دام"""
from abc import ABC, abstractmethod
from services.livestock.schemas import (
    LivestockSimulationRequest, LivestockSimulationResult,
    AnimalProduction, FeedRequirement, HealthRisk,
    ManureContribution, EnvironmentalImpact, EconomicAnalysis,
)

class BaseLivestockSimulator(ABC):
    name = "Base"
    
    @abstractmethod
    def simulate(self, request: LivestockSimulationRequest) -> LivestockSimulationResult:
        pass
    
    def calculate_manure(self, body_weight_kg: float, head_count: int) -> ManureContribution:
        """محاسبه کود دامی - NRC Standards"""
        # کود روزانه: ۸٪ وزن بدن
        daily_kg = body_weight_kg * 0.08 * head_count
        yearly_kg = daily_kg * 365
        
        return ManureContribution(
            total_kg_year=round(yearly_kg, 1),
            nitrogen_kg_year=round(yearly_kg * 0.006, 2),  # 0.6% N
            phosphorus_kg_year=round(yearly_kg * 0.0015, 2),  # 0.15% P
            potassium_kg_year=round(yearly_kg * 0.005, 2),  # 0.5% K
            organic_carbon_kg_year=round(yearly_kg * 0.12, 2),  # 12% C
            soil_carbon_boost_ton_ha_year=round(yearly_kg * 0.12 / 1000, 3),
        )
    
    def calculate_methane(self, daily_dmi_kg: float, head_count: int) -> float:
        """محاسبه CH4 - IPCC Tier 2"""
        # ۶.۵٪ انرژی دریافتی به CH4
        return daily_dmi_kg * head_count * 365 * 0.018 * 28  # CO2e

def calculate_forage_quality_factor(forage) -> float:
    """تبدیل NDVI به کیفیت علوفه"""
    ndvi = forage.ndvi_value
    if ndvi < 0.2:
        return 0.5
    elif ndvi < 0.4:
        return 0.75
    elif ndvi < 0.6:
        return 1.0
    else:
        return 1.15
    