"""Goat Simulator - شبیه‌ساز بز"""
from services.livestock.schemas import (
    AnimalProduction,
    EconomicAnalysis,
    EnvironmentalImpact,
    FeedRequirement,
    HealthRisk,
    LivestockSimulationRequest,
    LivestockSimulationResult,
)
from services.livestock.simulators.base import (
    BaseLivestockSimulator,
    calculate_forage_quality_factor,
)


class GoatSimulator(BaseLivestockSimulator):
    name = "Goat"

    BODY_WEIGHT_KG = 40.0
    DAILY_DMI_PCT = 0.035  # 3.5% BW
    MILK_YIELD_LITERS_DAY = 2.5
    MEAT_YIELD_KG = 15.0
    KIDDING_RATE = 1.5
    WATER_LITERS_DAY = 5.0

    def simulate(self, request: LivestockSimulationRequest) -> LivestockSimulationResult:
        herd = request.herd
        forage = request.forage
        quality_factor = calculate_forage_quality_factor(forage)

        daily_dmi = self.BODY_WEIGHT_KG * self.DAILY_DMI_PCT

        feed_req = FeedRequirement(
            dry_matter_kg_day=round(daily_dmi * herd.head_count, 2),
            metabolizable_energy_mj_day=round(daily_dmi * 11.5 * herd.head_count, 2),
            water_liters_day=self.WATER_LITERS_DAY * herd.head_count,
            supplement_kg_day=round(0.25 * herd.head_count, 2),
            grazing_hours=10.0,
        )

        production = AnimalProduction(
            milk_kg_day=round(self.MILK_YIELD_LITERS_DAY * herd.head_count * quality_factor * (herd.female_ratio_pct / 100), 2),
            meat_kg_year=round(self.MEAT_YIELD_KG * herd.head_count * 0.5 * quality_factor, 2),
            offspring_per_year=round(herd.head_count * (herd.female_ratio_pct / 100) * self.KIDDING_RATE, 2),
        )

        manure = self.calculate_manure(self.BODY_WEIGHT_KG, herd.head_count)
        methane = self.calculate_methane(daily_dmi, herd.head_count) * 0.25
        carrying_capacity = int(request.land_area_ha * forage.dry_matter_ton_ha * 1000 / (daily_dmi * 365))

        environmental = EnvironmentalImpact(
            methane_kg_co2e_year=round(methane, 1),
            water_footprint_m3_year=round(self.WATER_LITERS_DAY * herd.head_count * 365 / 1000, 1),
            grazing_pressure_index=round(herd.head_count / max(1, carrying_capacity), 2),
            carrying_capacity_head=carrying_capacity,
        )

        health = HealthRisk(
            disease_risk_score=0.2,
            mortality_rate_pct=4.0,
            parasitic_risk="medium",
        )

        prices = request.market_prices or {
            "milk_usd_kg": 1.2, "meat_usd_kg": 9.0, "feed_usd_kg": 0.3,
        }

        revenue = (
            production.milk_kg_day * 365 * prices["milk_usd_kg"]
            + production.meat_kg_year * prices["meat_usd_kg"]
            + production.offspring_per_year * 60
        )

        feed_cost = feed_req.dry_matter_kg_day * 365 * prices["feed_usd_kg"] * 0.2
        vet_cost = herd.head_count * 12
        total_costs = feed_cost + vet_cost + herd.head_count * 8

        economics = EconomicAnalysis(
            gross_revenue_usd_year=round(revenue, 2),
            feed_cost_usd_year=round(feed_cost, 2),
            veterinary_cost_usd_year=round(vet_cost, 2),
            labor_cost_usd_year=round(herd.head_count * 8, 2),
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
                "بزها می‌توانند از بوته‌ها و درختچه‌ها نیز تغذیه کنند",
                "مناسب برای زمین‌های شیب‌دار و سنگی",
                "شیر بز ارزش بازار بالاتری دارد",
            ],
        )
