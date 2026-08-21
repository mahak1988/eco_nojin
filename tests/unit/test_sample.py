"""Sample unit tests."""
import pytest
import os


class TestEnvironment:
    def test_env_example_exists(self):
        assert os.path.exists(".env.example")

    def test_default_values(self):
        assert os.getenv("DEFAULT_LATITUDE", "35.6892") == "35.6892"


class TestSample:
    def test_addition(self):
        assert 1 + 1 == 2

    def test_string(self):
        assert "Eco Nojin".lower() == "eco nojin"


@pytest.fixture
def coords():
    return {"latitude": 35.6892, "longitude": 51.3890, "area_ha": 50.0}


def test_fixture(coords):
    assert coords["area_ha"] > 0
