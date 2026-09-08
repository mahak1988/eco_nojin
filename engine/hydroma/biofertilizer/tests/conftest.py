"""Fixtures for biofertilizer tests."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from database.hub import hub
from database.base import Base
from engine.hydroma.biofertilizer.models import (
    NojinMaterial,
    NojinSoilType,
)
from engine.hydroma.biofertilizer.data.materials_data import MATERIALS, SOIL_TYPES


@pytest.fixture(scope="session", autouse=True)
def seed_biofertilizer_data():
    """Seed biofertilizer tables once per test session."""
    engine = hub.get_sqlalchemy_engine()
    Base.metadata.create_all(bind=engine)

    with hub.get_session() as session:
        if session.query(NojinMaterial).count() > 0:
            return

        for mat_data in MATERIALS:
            material = NojinMaterial(
                material_code=mat_data["material_code"],
                common_name=mat_data["common_name"],
                scientific_name=mat_data["scientific_name"],
                category=mat_data["category"],
                nitrogen_pct=mat_data.get("nitrogen_pct", 0),
                phosphorus_pct=mat_data.get("phosphorus_pct", 0),
                potassium_pct=mat_data.get("potassium_pct", 0),
                carbon_pct=mat_data.get("carbon_pct", 0),
                organic_matter_pct=mat_data.get("organic_matter_pct", 0),
                cn_ratio=mat_data.get("cn_ratio"),
                ph=mat_data.get("ph"),
                release_rate=mat_data.get("release_rate"),
                persistence_years=mat_data.get("persistence_years"),
                cost_per_ton_usd=mat_data.get("cost_per_ton_usd"),
                availability=mat_data.get("availability"),
                source_regions=mat_data.get("source_regions"),
                benefits=mat_data.get("benefits"),
                overuse_risks=mat_data.get("overuse_risks"),
                is_locally_available=mat_data.get("is_locally_available", True),
                is_suitable_for_arid=mat_data.get("is_suitable_for_arid", False),
                arid_priority_score=mat_data.get("arid_priority_score"),
                historical_use=mat_data.get("historical_use"),
                modern_research=mat_data.get("modern_research"),
            )
            session.add(material)

        for soil_data in SOIL_TYPES:
            soil = NojinSoilType(
                soil_code=soil_data["soil_code"],
                soil_name=soil_data["soil_name"],
                soil_category=soil_data["soil_category"],
                texture=soil_data.get("texture"),
                typical_ph_min=soil_data.get("typical_ph_min"),
                typical_ph_max=soil_data.get("typical_ph_max"),
                typical_om_pct=soil_data.get("typical_om_pct"),
                typical_cec_cmol_kg=soil_data.get("typical_cec_cmol_kg"),
                water_holding_capacity=soil_data.get("water_holding_capacity"),
                drainage=soil_data.get("drainage"),
                common_problems=soil_data.get("common_problems"),
                nutrient_deficiencies=soil_data.get("nutrient_deficiencies"),
                common_regions=soil_data.get("common_regions"),
            )
            session.add(soil)

        session.commit()
