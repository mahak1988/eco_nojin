"""Multi-Layer Cropping (Agroforestry) Adapter"""
from datetime import UTC, datetime

from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext,
    SimulationResult,
    SimulationStatus,
    SimulationType,
)


@SimulatorRegistry.register
class MultiLayerAdapter(BaseSimulator):
    """کشت چندلایه - Agroforestry & Multi-story cropping"""
    simulator_type = SimulationType.MULTI_LAYER
    name = "AgroforestryEngine"
    version = "1.0.0"

    # الگوهای کشت چندلایه
    SYSTEMS = {
        "silvopasture": {"trees": True, "crops": False, "livestock": True},
        "alley_cropping": {"trees": True, "crops": True, "livestock": False},
        "forest_garden": {"trees": True, "crops": True, "livestock": False},
        "home_garden": {"trees": True, "crops": True, "livestock": True},
    }

    async def validate_context(self, ctx: SimulationContext) -> list[str]:
        if not ctx.multi_layer:
            return ["Multi-layer configuration required"]
        return []

    async def run(self, ctx: SimulationContext) -> SimulationResult:
        ml = ctx.multi_layer
        layers = []

        # لایه بالایی (canopy - درختان)
        if ml.canopy_layer:
            canopy_yield = self._estimate_yield(ml.canopy_layer, shade_provider=True)
            layers.append({
                "layer": "canopy",
                "crop": ml.canopy_layer.crop_type,
                "yield_estimate": canopy_yield,
                "shade_provided_pct": 40,
                "height_m": 8.0,
            })

        # لایه میانی
        if ml.sub_canopy_layer:
            sub_yield = self._estimate_yield(
                ml.sub_canopy_layer,
                shade_tolerance=ml.shade_tolerance,
            )
            layers.append({
                "layer": "sub_canopy",
                "crop": ml.sub_canopy_layer.crop_type,
                "yield_estimate": sub_yield,
                "shade_tolerance": ml.shade_tolerance,
                "height_m": 2.5,
            })

        # لایه زمینی
        if ml.ground_layer:
            ground_yield = self._estimate_yield(
                ml.ground_layer,
                shade_tolerance=ml.shade_tolerance * 0.8,
            )
            layers.append({
                "layer": "ground",
                "crop": ml.ground_layer.crop_type,
                "yield_estimate": ground_yield,
                "height_m": 0.5,
            })

        # مجموع عملکرد و مقایسه با monoculture
        total_yield = sum(l["yield_estimate"] for l in layers)
        mono_equivalent = total_yield * 1.25  # Land Equivalent Ratio

        # مزایای اکولوژیک
        biodiversity_score = len(layers) * 25
        water_use_efficiency = 1.3  # ۳۰٪ بهتر از monoculture
        pest_reduction = 40  # کاهش آفت بدون سم

        return SimulationResult(
            simulation_id=ctx.simulation_id,
            simulation_type=self.simulator_type,
            status=SimulationStatus.COMPLETED,
            started_at=datetime.now(UTC),
            summary={
                "layers": layers,
                "total_layers": len(layers),
                "total_yield_ton_ha": round(total_yield, 2),
                "land_equivalent_ratio": round(mono_equivalent / max(1, total_yield / len(layers)), 2),
                "biodiversity_score": biodiversity_score,
                "water_use_efficiency_gain_pct": 30,
                "pest_reduction_pct": pest_reduction,
                "carbon_sequestration_ton_ha_year": round(len(layers) * 2.5, 2),
                "soil_health_improvement_pct": 45,
                "microclimate_benefit": "improved",
            },
        )

    def _estimate_yield(self, crop, shade_provider=False, shade_tolerance=1.0) -> float:
        base_yields = {
            "wheat": 4.5, "barley": 4.0, "maize": 8.0, "rice": 6.0,
            "tomato": 30.0, "potato": 25.0, "olive": 8.0, "pistachio": 2.5,
            "walnut": 3.0, "almond": 2.0, "pomegranate": 12.0, "grape": 15.0,
            "alfalfa": 12.0, "clover": 8.0, "mint": 3.0, "saffron": 0.01,
        }
        base = base_yields.get(crop.crop_type.lower(), 5.0)
        if shade_provider:
            return base
        return base * shade_tolerance
