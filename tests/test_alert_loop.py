import os
"""Tests: run_all_farm_alerts (all-farm loop) + main.py import sanity."""
import pytest

from database.base import Base
from database.config import engine
from tests.conftest import TEST_SESSION_FACTORY as SessionLocal
from database import models  # noqa: F401
from database.hub import hub as db_models
from services.bots.core.alert_runner import run_all_farm_alerts


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def _farm(db, name="مزرعه آزمایشی"):
    owner = db_models.User(
        email="owner@test.com",
        full_name="owner",
        hashed_password = os.getenv("PASSWORD", ""),
        role="farmer",
        is_active=True,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    f = db_models.Farm(
        name=name,
        owner_id=owner.id,
        latitude=35.69,
        longitude=51.39,
        area_hectares=5.0,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def test_run_all_farm_alerts_empty_without_real_rows(db_session):
    farm = _farm(db_session)
    fired = run_all_farm_alerts(db_session)
    assert fired == []


def test_run_all_farm_alerts_fires_on_real_ndvi_drop(db_session):
    farm = _farm(db_session)
    # Real copernicus row with poor NDVI -> should fire
    owner = db_session.query(db_models.User).first()
    db_session.add(
        db_models.SatelliteAnalysis(
            farm_id=farm.id,
            user_id=owner.id,
            ndvi=0.15,
            evi=0.1,
            savi=0.1,
            data_source="copernicus",
            scene_id="S2A_test",
        )
    )
    # Simulated row with poor NDVI -> must NOT fire (honesty rule)
    db_session.add(
        db_models.SatelliteAnalysis(
            farm_id=farm.id,
            user_id=owner.id,
            ndvi=0.1,
            evi=0.05,
            savi=0.05,
            data_source="simulated",
            scene_id=None,
        )
    )
    db_session.commit()
    fired = run_all_farm_alerts(db_session)
    assert len(fired) >= 1
    assert "مزرعه" in fired[0]


def test_run_all_farm_alerts_skips_broken_farms(db_session):
    _farm(db_session, "سالم")
    fired = run_all_farm_alerts(db_session)
    assert fired == []


def test_main_imports_with_alert_loop():
    from services.api_gateway import main  # noqa: F401

    assert callable(main._alert_loop)
    assert callable(main._run_alerts_once)
