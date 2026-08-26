"""Sheep Simulator - شبیه‌ساز گوسفند"""
from services.livestock.simulators.base import (
    BaseLivestockSimulator, calculate_forage_quality_factor,
)
from services.livestock.schemas import (
    LivestockSimulationRequest, LivestockSimulationResult,
    AnimalProduction, FeedRequirement, HealthRisk,
    EnvironmentalImpact, EconomicAnalysis,
)

class SheepSimulator(BaseLivestockSimulator):
    name = "Sheep"
    
    BODY_WEIGHT_KG = 50.0
    DAILY_DMI_PCT = 0.03  # 3% BW
    MILK_YIELD_LITERS_DAY = 1.0
    MEAT_YIELD_KG = 20.0
    WOOL_YIELD_KG = 3.5
    LAMBING_RATE = 1.3
    WATER_LITERS_DAY = 6.0
    
    def simulate(self, request: LivestockSimulationRequest) -> LivestockSimulationResult:
        herd = request.herd
        forage = request.forage
        quality_factor = calculate_forage_quality_factor(forage)
        
        daily_dmi = self.BODY_WEIGHT_KG * self.DAILY_DMI_PCT
        
        feed_req = FeedRequirement(
            dry_matter_kg_day=round(daily_dmi * herd.head_count, 2),
            metabolizable_energy_mj_day=round(daily_dmi * 11.0 * herd.head_count, 2),
            water_liters_day=self.WATER_LITERS_DAY * herd.head_count,
            supplement_kg_day=round(0.3 * herd.head_count * (1 - quality_factor), 2),
            grazing_hours=9.0,
        )
        
        production = AnimalProduction(
            milk_kg_day=round(self.MILK_YIELD_LITERS_DAY * herd.head_count * quality_factor * (herd.female_ratio_pct / 100), 2),
            meat_kg_year=round(self.MEAT_YIELD_KG * herd.head_count * 0.4 * quality_factor, 2),
            wool_kg_year=round(self.WOOL_YIELD_KG * herd.head_count * quality_factor, 2),
            offspring_per_year=round(herd.head_count * (herd.female_ratio_pct / 100) * self.LAMBING_RATE, 2),
        )
        
        manure = self.calculate_manure(self.BODY_WEIGHT_KG, herd.head_count)
        methane = self.calculate_methane(daily_dmi, herd.head_count) * 0.3
        carrying_capacity = int(request.land_area_ha * forage.dry_matter_ton_ha * 1000 / (daily_dmi * 365))
        
        environmental = EnvironmentalImpact(
            methane_kg_co2e_year=round(methane, 1),
            water_footprint_m3_year=round(self.WATER_LITERS_DAY * herd.head_count * 365 / 1000, 1),
            grazing_pressure_index=round(herd.head_count / max(1, carrying_capacity), 2),
            carrying_capacity_head=carrying_capacity,
        )
        
        health = HealthRisk(
            disease_risk_score=0.25 if quality_factor < 0.7 else 0.1,
            mortality_rate_pct=3.0,
            parasitic_risk="high" if quality_factor < 0.6 else "medium",
        )
        
        prices = request.market_prices or {
            "milk_usd_kg": 0.8, "meat_usd_kg": 10.0,
            "wool_usd_kg": 3.0, "feed_usd_kg": 0.3,
        }
        
        revenue = (
            production.milk_kg_day * 365 * prices["milk_usd_kg"]
            + production.meat_kg_year * prices["meat_usd_kg"]
            + production.wool_kg_year * prices["wool_usd_kg"]
            + production.offspring_per_year * 80
        )
        
        feed_cost = feed_req.dry_matter_kg_day * 365 * prices["feed_usd_kg"] * 0.2
        vet_cost = herd.head_count * 15
        total_costs = feed_cost + vet_cost + herd.head_count * 10
        
        economics = EconomicAnalysis(
            gross_revenue_usd_year=round(revenue, 2),
            feed_cost_usd_year=round(feed_cost, 2),
            veterinary_cost_usd_year=round(vet_cost, 2),
            labor_cost_usd_year=round(herd.head_count * 10, 2),
            total_costs_usd_year=round(total_costs, 2),
            net_profit_usd_year=round(revenue - total_costs, 2),
            profit_margin_pct=round((revenue - total_costs) / max(1, revenue) * 100, 1),
        )
        
        return LivestockSimulationResult(
            simulation_id=request.simulation_id,
            animal_type=herd.animal_type,
            herd_size=herd.head_count,
            production=production,
            feed_requirements=feed_req,
            health=health,
            manure=manure,
            environmental=environmental,
            economics=economics,
            recommendations=[
                "چرخش چرا برای جلوگیری از تخریب زمین",
                "پشم‌چینی سالانه در بهار",
                "استفاده از کود برای تقویت مراتع",
            ],
            warnings=["حساسیت بالا به انگل در کیفیت پایین علوفه"] if quality_factor < 0.6 else [],
        )
    