"""Pytest config for ECO_NOJIN"""
import pytest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def sample_climate():
    return {"tmax":[25,28,30],"tmin":[15,18,20],"rain":[0,5,15]}

@pytest.fixture
def soil_profile():
    return {"soc":[15000,8000,4000],"clay":[0.3,0.35,0.4]}

@pytest.fixture
def rothc_params():
    return {"BIO_FRAC":0.46,"HUM_FRAC":0.55,"RATE_PM":0.08}
