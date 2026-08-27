"""Poultry Simulator - شبیه‌ساز طیور"""
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


class PoultrySimulator(BaseLivestockSimulator):
    name = "Poultry"

    BODY_WEIGHT_KG = 2.0
    DAILY_DMI_KG = 0.12
    EGGS_PER_DAY = 0.7  # 70% تولید
    MEAT_YIELD_KG = 1.8
    WATER_LITERS_DAY = 0.25

    def simulate(self, request: LivestockSimulationRequest) -> LivestockSimulationResult:
        herd = request.herd
        forage = request.forage
        quality_factor = calculate_forage_quality_factor(forage)

        feed_req = FeedRequirement(
            dry_matter_kg_day=round(self.DAILY_DMI_KG * herd.head_count, 2),
            metabolizable_energy_mj_day=round(self.DAILY_DMI_KG * 12.5 * herd.head_count, 2),
            water_liters_day=self.WATER_LITERS_DAY * herd.head_count,
            supplement_kg_day=round(self.DAILY_DMI_KG * 0.8 * herd.head_count, 2),
            grazing_hours=6.0 if request.herd.production_system == "grazing" else 0.0,
        )

        production = AnimalProduction(
            eggs_day=round(self.EGGS_PER_DAY * herd.head_count * quality_factor, 2),
            meat_kg_year=round(self.MEAT_YIELD_KG * herd.head_count * 2.0, 2),  # ۲ دوره در سال
        )

        manure = self.calculate_manure(self.BODY_WEIGHT_KG, herd.head_count)
        methane = 0.0  # طیور CH4 ناچیز
        carrying_capacity = int(request.land_area_ha * 500)

        environmental = EnvironmentalImpact(
            methane_kg_co2e_year=round(methane, 1),
            water_footprint_m3_year=round(self.WATER_LITERS_DAY * herd.head_count * 365, 1),
            grazing_pressure_index=round(herd.head_count / max(1, carrying_capacity), 2),
            carrying_capacity_head=carrying_capacity,
        )

        health = HealthRisk(
            disease_risk_score=0.4 if quality_factor < 0.6 else 0.15,
            mortality_rate_pct=5.0,
            heat_stress_risk="high" if request.parameters.get("temp_max_c", 25) > 32 else "low",
        )

        prices = request.market_prices or {
            "eggs_usd_piece": 0.15, "meat_usd_kg": 5.0, "feed_usd_kg": 0.4,
        }

        revenue = (
            production.eggs_day * 365 * prices["eggs_usd_piece"]
            + production.meat_kg_year * prices["meat_usd_kg"]
        )

        feed_cost = feed_req.dry_matter_kg_day * 365 * prices["feed_usd_kg"]
        vet_cost = herd.head_count * 1
        total_costs = feed_cost + vet_cost + herd.head_count * 2

        economics = EconomicAnalysis(
            gross_revenue_usd_year=round(revenue, 2),
            feed_cost_usd_year=round(feed_cost, 2),
            veterinary_cost_usd_year=round(vet_cost, 2),
            labor_cost_usd_year=round(herd.head_count * 2, 2),
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
                "کود مرغی بسیار غنی از نیتروژن - استفاده کم مقدار",
                "سیستم free-range کیفیت تخم‌مرغ را بهبود می‌دهد",
                "تهویه مناسب برای جلوگیری از بیماری‌های تنفسی",
            ],
        )
