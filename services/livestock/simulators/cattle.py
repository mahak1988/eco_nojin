"""Cattle Simulator - شبیه‌ساز گاو (شیری و گوشتی)"""
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


class CattleSimulator(BaseLivestockSimulator):
    name = "Cattle"

    # پارامترهای پایه
    BODY_WEIGHT_KG = 450.0
    DAILY_DMI_PCT = 0.025  # 2.5% BW
    MILK_YIELD_LITERS_DAY = 15.0  # شیری متوسط
    MEAT_YIELD_KG = 220.0  # گوشت در سال
    CALVING_RATE = 0.85
    WATER_LITERS_DAY = 50.0

    def simulate(self, request: LivestockSimulationRequest) -> LivestockSimulationResult:
        herd = request.herd
        forage = request.forage

        # کیفیت علوفه
        quality_factor = calculate_forage_quality_factor(forage)

        # نیاز غذایی (NRC)
        daily_dmi = self.BODY_WEIGHT_KG * self.DAILY_DAILY_PCT if hasattr(self, 'DAILY_DAILY_PCT') else self.BODY_WEIGHT_KG * self.DAILY_DMI_PCT
        feed_req = FeedRequirement(
            dry_matter_kg_day=round(daily_dmi * herd.head_count, 2),
            metabolizable_energy_mj_day=round(daily_dmi * 10.5 * herd.head_count, 2),
            water_liters_day=self.WATER_LITERS_DAY * herd.head_count,
            supplement_kg_day=round(max(0, 2.0 - forage.crude_protein_pct * 0.1) * herd.head_count, 2),
            grazing_hours=8.0 if quality_factor > 0.7 else 10.0,
        )

        # تولید
        production = AnimalProduction(
            milk_kg_day=round(self.MILK_YIELD_LITERS_DAY * herd.head_count * quality_factor * (herd.female_ratio_pct / 100), 2),
            meat_kg_year=round(self.MEAT_YIELD_KG * herd.head_count * 0.3 * quality_factor, 2),  # 30% کشتار سالانه
            offspring_per_year=round(herd.head_count * (herd.female_ratio_pct / 100) * self.CALVING_RATE, 2),
        )

        # کود
        manure = self.calculate_manure(self.BODY_WEIGHT_KG, herd.head_count)

        # اثرات زیست‌محیطی
        methane = self.calculate_methane(daily_dmi, herd.head_count)
        carrying_capacity = int(request.land_area_ha * forage.dry_matter_ton_ha * 1000 / (daily_dmi * 365))

        environmental = EnvironmentalImpact(
            methane_kg_co2e_year=round(methane, 1),
            water_footprint_m3_year=round(self.WATER_LITERS_DAY * herd.head_count * 365 / 1000, 1),
            grazing_pressure_index=round(herd.head_count / max(1, carrying_capacity), 2),
            carrying_capacity_head=carrying_capacity,
        )

        # سلامت
        heat_stress = "high" if request.parameters.get("temp_max_c", 25) > 35 else "low"
        disease_risk = 0.3 if quality_factor < 0.7 else 0.1

        health = HealthRisk(
            disease_risk_score=disease_risk,
            mortality_rate_pct=2.0 + (disease_risk * 3),
            heat_stress_risk=heat_stress,
            parasitic_risk="medium" if quality_factor < 0.8 else "low",
        )

        # اقتصاد
        prices = request.market_prices or {
            "milk_usd_kg": 0.5,
            "meat_usd_kg": 8.0,
            "feed_usd_kg": 0.3,
        }

        revenue = (
            production.milk_kg_day * 365 * prices["milk_usd_kg"]
            + production.meat_kg_year * prices["meat_usd_kg"]
            + production.offspring_per_year * 500  # ارزش گوساله
        )

        feed_cost = feed_req.dry_matter_kg_day * 365 * prices["feed_usd_kg"] * 0.3
        vet_cost = herd.head_count * 50
        labor_cost = herd.head_count * 30

        total_costs = feed_cost + vet_cost + labor_cost

        economics = EconomicAnalysis(
            gross_revenue_usd_year=round(revenue, 2),
            feed_cost_usd_year=round(feed_cost, 2),
            veterinary_cost_usd_year=round(vet_cost, 2),
            labor_cost_usd_year=round(labor_cost, 2),
            total_costs_usd_year=round(total_costs, 2),
            net_profit_usd_year=round(revenue - total_costs, 2),
            profit_margin_pct=round((revenue - total_costs) / max(1, revenue) * 100, 1),
        )

        # توصیه‌ها
        recommendations = []
        if quality_factor < 0.8:
            recommendations.append("بهبود کیفیت علوفه با کشت شبدر یا یونجه")
        if environmental.grazing_pressure_index > 1.0:
            recommendations.append("کاهش تعداد دام یا افزایش زمین چرا")
        if heat_stress == "high":
            recommendations.append("ایجاد سایبان و تأمین آب کافی")
        recommendations.append("استفاده از کود دامی برای تقویت خاک (RothC)")

        warnings = []
        if environmental.grazing_pressure_index > 1.5:
            warnings.append("فشار چرای بیش از حد - خطر فرسایش")

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
            recommendations=recommendations,
            warnings=warnings,
        )
