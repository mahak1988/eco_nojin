"""Smoke tests for the AquaCrop-OSPy runner (Phase 3, sprint 1).

Runs a real single-season wheat simulation with synthetic weather; asserts
the model completes and the provenance labels are honest.
"""

import pandas as pd
import pytest

from engine.hydroma.simulation.runners.aquacrop_runner import (
    AquaCropRunner,
    synthetic_weather,
)


class TestSyntheticWeather:
    def test_columns_and_length(self):
        weather = synthetic_weather("2020/03/01", "2020/07/15")
        # aquacrop reads values positionally: MinTemp, MaxTemp, Precip, ET0, Date
        assert list(weather.columns) == ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]
        assert len(weather) >= 130

    def test_temperature_ramp(self):
        weather = synthetic_weather("2020/03/01", "2020/07/15")
        assert weather["MaxTemp"].iloc[-1] > weather["MaxTemp"].iloc[0]


class TestAquaCropRunner:
    @pytest.mark.slow
    def test_wheat_season_completes(self):
        result = AquaCropRunner().run(
            crop="Wheat",
            soil_type="SiltLoam",
            planting_date="2020/03/01",
            harvest_date="2020/07/20",
        )
        assert result["data_source"] == "simulated"
        assert "AquaCrop-OSPy" in result["model"]
        assert result["yield_kg_ha"] is not None and result["yield_kg_ha"] > 0.0
        assert result["biomass_kg_ha"] is not None and result["biomass_kg_ha"] > 0.0
        assert result["residue_kg_ha"] >= 0.0
        assert "Dry yield (tonne/ha)" in result["raw_keys"]

    def test_missing_weather_column_rejected(self):
        bad = pd.DataFrame({"Date": pd.date_range("2020-01-01", periods=5, freq="D")})
        with pytest.raises(ValueError, match="missing columns"):
            AquaCropRunner().run(crop="Wheat", weather=bad)
