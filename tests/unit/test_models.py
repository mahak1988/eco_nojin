"""Test database models and connection."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from engine.hydroma.core.models import Plant, SoilProfile


def test_soil_profile_creation():
    """Verify that the ORM can create and retrieve a soil profile in memory."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    new_soil = SoilProfile(
        name="Test Sandy Loam", texture="Sandy Loam", ph=7.2, ec=1.5, organic_matter=1.2
    )
    session.add(new_soil)
    session.commit()
    session.refresh(new_soil)

    assert new_soil.id == 1
    assert new_soil.name == "Test Sandy Loam"
    session.close()


def test_plant_creation():
    """Verify that the ORM can create and retrieve a plant entity in memory."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    new_plant = Plant(
        scientific_name="Opuntia ficus-indica",
        local_name="Prickly Pear",
        category="cactus",
        water_need="low",
        drought_tolerance="high",
    )
    session.add(new_plant)
    session.commit()
    session.refresh(new_plant)

    assert new_plant.id == 1
    assert new_plant.scientific_name == "Opuntia ficus-indica"
    session.close()
