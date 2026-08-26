"""Windbreak Adapter - طراحی و ارزیابی بادشکن"""
from typing import List
from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext, SimulationResult, SimulationStatus, SimulationType,
)
from datetime import datetime, timezone
import math

@SimulatorRegistry.register
class WindbreakAdapter(BaseSimulator):
    """بادشکن - Windbreak design and impact analysis"""
    simulator_type = SimulationType.WINDBREAK
    name = "WindbreakEngine"
    version = "1.0.0"
    
    # دیتابیس گونه‌های درختی
    TREE_SPECIES = {
        "cypress": {"height_m": 10, "density": 0.7, "root_depth_m": 2.5, "lifespan_years": 50},
        "eucalyptus": {"height_m": 15, "density": 0.6, "root_depth_m": 3.0, "lifespan_years": 40},
        "poplar": {"height_m": 20, "density": 0.5, "root_depth_m": 2.0, "lifespan_years": 30},
        "olive": {"height_m": 8, "density": 0.65, "root_depth_m": 3.5, "lifespan_years": 100},
        "pistachio": {"height_m": 6, "density": 0.7, "root_depth_m": 4.0, "lifespan_years": 80},
        "acacia": {"height_m": 7, "density": 0.55, "root_depth_m": 5.0, "lifespan_years": 35},
        "juniper": {"height_m": 5, "density": 0.75, "root_depth_m": 2.0, "lifespan_years": 60},
    }
    
    async def validate_context(self, ctx: SimulationContext) -> List[str]:
        if not ctx.windbreak:
            return ["Windbreak configuration required"]
        return []
    
    async def run(self, ctx: SimulationContext) -> SimulationResult:
        wb = ctx.windbreak
        species_data = self.TREE_SPECIES.get(wb.tree_species, self.TREE_SPECIES["cypress"])
        
        # محاسبه protected zone
        # بادشکن تا ۱۰-۲۰ برابر ارتفاع محافظت می‌کند
        protection_distance_m = wb.height_m * 15
        
        # محاسبه کاهش سرعت باد
        porosity = wb.porosity_pct / 100
        optimal_porosity = 0.4  # بهینه برای بادشکن
        efficiency = 1 - abs(porosity - optimal_porosity)
        wind_reduction_pct = efficiency * 65  # حداکثر ۶۵٪ کاهش
        
        # تعداد درختان
        trees_per_row = int(wb.length_m / 2)  # فاصله ۲ متری
        total_trees = trees_per_row * max(1, int(wb.length_m / wb.row_spacing_m))
        
        # اثر بر تبخیر و رطوبت
        evaporation_reduction = wind_reduction_pct * 0.6  # ۶۰٪ از کاهش باد به کاهش تبخیر
        soil_moisture_gain = evaporation_reduction * 0.3  # ۳۰٪ تبدیل به رطوبت خاک
        
        # هزینه و بازگشت سرمایه
        cost_per_tree = 50  # USD
        total_cost = total_trees * cost_per_tree
        annual_water_savings_m3 = (soil_moisture_gain / 100) * 500 * (wb.length_m * protection_distance_m / 10000)
        
        return SimulationResult(
            simulation_id=ctx.simulation_id,
            simulation_type=self.simulator_type,
            status=SimulationStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            summary={
                "species": wb.tree_species,
                "species_data": species_data,
                "height_m": wb.height_m,
                "length_m": wb.length_m,
                "total_trees": total_trees,
                "protection_distance_m": protection_distance_m,
                "protected_area_ha": round(
                    (wb.length_m * protection_distance_m) / 10000, 3
                ),
                "wind_reduction_pct": round(wind_reduction_pct, 1),
                "evaporation_reduction_pct": round(evaporation_reduction, 1),
                "soil_moisture_gain_pct": round(soil_moisture_gain, 1),
                "erosion_reduction_pct": round(wind_reduction_pct * 0.8, 1),
                "estimated_cost_usd": total_cost,
                "payback_years": round(total_cost / max(1, annual_water_savings_m3 * 2), 1),
                "carbon_sequestration_ton_year": round(total_trees * 0.02, 3),
            },
        )
    