"""Integration tests for Simulation Framework"""
from datetime import date

import pytest

from services.simulation.schemas import (
    BBox,
    CropParameters,
    MultiLayerConfig,
    SimulationContext,
    SimulationStatus,
    SimulationType,
    SoilProfile,
    WeatherData,
    WindbreakConfig,
)
from services.simulation.service import SimulationService


@pytest.fixture
def base_context():
    return SimulationContext(
        simulation_id="test-001",
        simulation_type=SimulationType.COMPREHENSIVE,
        bbox=BBox(north=35.5, south=35.4, east=51.5, west=51.4),
        soil=SoilProfile(
            texture="loam",
            organic_carbon_pct=1.5,
            infiltration_rate_mm_hr=20.0,
        ),
        weather=WeatherData(
            precipitation_mm=50.0,
            wind_speed_ms=12.0,  # باد قوی برای فرسایش
            temp_min_c=15.0,
            temp_max_c=32.0,
            solar_radiation_mj_m2=18.0,
        ),
        crop=CropParameters(
            crop_type="wheat",
            planting_date=date(2026, 10, 15),
        ),
    )

@pytest.mark.asyncio
class TestSimulationFramework:
    async def test_list_simulators(self):
        service = SimulationService()
        sims = service.list_simulators()
        assert len(sims) >= 6
        types = [s["type"] for s in sims]
        assert "crop_growth" in types
        assert "soil_carbon" in types
        assert "wind_erosion" in types

    async def test_crop_simulation(self, base_context):
        service = SimulationService()
        result = await service.run_simulation(
            SimulationType.CROP_GROWTH, base_context,
        )
        assert result.status == SimulationStatus.COMPLETED, f"Error: {result.error}"
        assert "yield_ton_ha" in result.summary
        assert result.summary["yield_ton_ha"] > 0

    async def test_carbon_simulation(self, base_context):
        service = SimulationService()
        result = await service.run_simulation(
            SimulationType.SOIL_CARBON, base_context,
        )
        assert result.status == SimulationStatus.COMPLETED
        assert result.summary["co2e_sequestered_t_ha"] > 0
        assert len(result.time_series) == 20

    async def test_wind_erosion(self, base_context):
        service = SimulationService()
        result = await service.run_simulation(
            SimulationType.WIND_EROSION, base_context,
        )
        assert result.status == SimulationStatus.COMPLETED
        assert "erosion_ton_ha_year" in result.summary
        assert "risk_level" in result.summary

    async def test_windbreak_design(self, base_context):
        base_context.windbreak = WindbreakConfig(
            tree_species="cypress",
            height_m=8.0,
            length_m=200.0,
            porosity_pct=40.0,
        )
        service = SimulationService()
        result = await service.run_simulation(
            SimulationType.WINDBREAK, base_context,
        )
        assert result.status == SimulationStatus.COMPLETED
        assert result.summary["wind_reduction_pct"] > 0
        assert result.summary["total_trees"] > 0

    async def test_windbreak_reduces_erosion(self, base_context):
        """تست مهم: بادشکن باید فرسایش را کاهش دهد"""
        service = SimulationService()

        # بدون بادشکن
        r1 = await service.run_simulation(
            SimulationType.WIND_EROSION, base_context,
        )

        # با بادشکن
        ctx_with_wb = base_context.model_copy()
        ctx_with_wb.windbreak = WindbreakConfig(
            tree_species="cypress",
            height_m=8.0,
            length_m=200.0,
            porosity_pct=40.0,
        )
        r2 = await service.run_simulation(
            SimulationType.WIND_EROSION, ctx_with_wb,
        )

        e1 = r1.summary["erosion_ton_ha_year"]
        e2 = r2.summary["erosion_ton_ha_year"]
        assert e1 > 0, f"Erosion without windbreak should be > 0, got {e1}"
        assert e2 < e1, f"Windbreak should reduce erosion: {e2} >= {e1}"

    async def test_infiltration(self, base_context):
        service = SimulationService()
        result = await service.run_simulation(
            SimulationType.INFILTRATION, base_context,
        )
        assert result.status == SimulationStatus.COMPLETED
        assert len(result.time_series) == 24
        assert result.summary["infiltration_efficiency_pct"] >= 0

    async def test_multi_layer_cropping(self, base_context):
        base_context.multi_layer = MultiLayerConfig(
            canopy_layer=CropParameters(
                crop_type="walnut", planting_date=date(2026, 3, 1),
            ),
            sub_canopy_layer=CropParameters(
                crop_type="alfalfa", planting_date=date(2026, 4, 1),
            ),
            ground_layer=CropParameters(
                crop_type="clover", planting_date=date(2026, 4, 15),
            ),
            shade_tolerance=0.7,
        )
        service = SimulationService()
        result = await service.run_simulation(
            SimulationType.MULTI_LAYER, base_context,
        )
        assert result.status == SimulationStatus.COMPLETED
        assert result.summary["total_layers"] == 3
        assert result.summary["biodiversity_score"] >= 75

    async def test_comprehensive_simulation(self, base_context):
        service = SimulationService()
        results = await service.run_comprehensive(base_context)
        assert len(results) >= 5
        assert "crop_growth" in results
        assert "soil_carbon" in results

    async def test_watershed_with_bbox(self, base_context):
        service = SimulationService()
        result = await service.run_simulation(
            SimulationType.WATERSHED, base_context,
        )
        assert result.status == SimulationStatus.COMPLETED
        assert "aquifer_recharge_mm" in result.summary
        assert result.summary["aquifer_recharge_mm"] >= 0
