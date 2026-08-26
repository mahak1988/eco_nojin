"""Integration tests for Livestock Module"""
import pytest
from services.livestock.service import LivestockService
from services.livestock.schemas import (
    LivestockSimulationRequest, HerdProfile, ForageQuality,
    AnimalType, ProductionSystem,
)
from services.livestock.nutrition.forage_quality import ndvi_to_forage_quality

class TestLivestockModule:
    def test_list_animal_types(self):
        service = LivestockService()
        types = service.list_animal_types()
        assert len(types) >= 4
        names = [t["type"] for t in types]
        assert "cattle" in names
        assert "sheep" in names
        assert "goat" in names
        assert "poultry" in names
    
    def test_cattle_simulation(self):
        service = LivestockService()
        req = LivestockSimulationRequest(
            herd=HerdProfile(
                animal_type=AnimalType.CATTLE,
                head_count=20,
                breed="Holstein",
                production_system=ProductionSystem.MIXED,
            ),
            forage=ForageQuality(ndvi_value=0.7),
            land_area_ha=50.0,
        )
        result = service.simulate(req)
        assert result.status == "completed"
        assert result.production.milk_kg_day > 0
        assert result.production.meat_kg_year > 0
        assert result.manure.total_kg_year > 0
        assert result.economics.gross_revenue_usd_year > 0
        assert result.environmental.methane_kg_co2e_year > 0
    
    def test_sheep_simulation(self):
        service = LivestockService()
        req = LivestockSimulationRequest(
            herd=HerdProfile(
                animal_type=AnimalType.SHEEP,
                head_count=100,
            ),
            forage=ForageQuality(ndvi_value=0.6),
            land_area_ha=30.0,
        )
        result = service.simulate(req)
        assert result.status == "completed"
        assert result.production.wool_kg_year > 0
        assert result.production.offspring_per_year > 0
    
    def test_goat_simulation(self):
        service = LivestockService()
        req = LivestockSimulationRequest(
            herd=HerdProfile(
                animal_type=AnimalType.GOAT,
                head_count=50,
            ),
            forage=ForageQuality(ndvi_value=0.5),
            land_area_ha=20.0,
        )
        result = service.simulate(req)
        assert result.status == "completed"
        assert result.production.milk_kg_day > 0
    
    def test_poultry_simulation(self):
        service = LivestockService()
        req = LivestockSimulationRequest(
            herd=HerdProfile(
                animal_type=AnimalType.POULTRY,
                head_count=500,
            ),
            forage=ForageQuality(ndvi_value=0.6),
            land_area_ha=5.0,
        )
        result = service.simulate(req)
        assert result.status == "completed"
        assert result.production.eggs_day > 0
        assert result.environmental.methane_kg_co2e_year == 0  # طیور CH4 ندارد
    
    def test_ndvi_to_forage_quality(self):
        result = ndvi_to_forage_quality(0.7, "spring")
        assert result.crude_protein_pct > 10
        assert result.digestibility_pct > 60
        assert result.dry_matter_ton_ha > 3
    
    def test_low_ndvi_warnings(self):
        """کیفیت پایین علوفه باید warning ایجاد کند"""
        service = LivestockService()
        req = LivestockSimulationRequest(
            herd=HerdProfile(
                animal_type=AnimalType.SHEEP,
                head_count=100,
            ),
            forage=ForageQuality(ndvi_value=0.2),
            land_area_ha=10.0,
        )
        result = service.simulate(req)
        # با NDVI پایین، recommendations باید وجود داشته باشد
        assert len(result.recommendations) > 0
    
    def test_manure_contributes_to_soil(self):
        """کود دامی باید به کربن خاک کمک کند"""
        service = LivestockService()
        req = LivestockSimulationRequest(
            herd=HerdProfile(
                animal_type=AnimalType.CATTLE,
                head_count=20,
            ),
            forage=ForageQuality(ndvi_value=0.6),
            land_area_ha=20.0,
        )
        result = service.simulate(req)
        assert result.manure.organic_carbon_kg_year > 0
        assert result.manure.nitrogen_kg_year > 0
    
    def test_carrying_capacity(self):
        """تست ظرفیت برد"""
        service = LivestockService()
        req = LivestockSimulationRequest(
            herd=HerdProfile(
                animal_type=AnimalType.CATTLE,
                head_count=100,  # تعداد زیاد
            ),
            forage=ForageQuality(ndvi_value=0.5),
            land_area_ha=10.0,  # زمین کم
        )
        result = service.simulate(req)
        assert result.environmental.carrying_capacity_head > 0
        # pressure باید بالا باشد
        assert result.environmental.grazing_pressure_index > 0
    