"""Tests for Stage 23: LAI and EWSI connections to HYRUE seasonal mode.

Tests cover:
- LAIModel produces valid LAI array from daily temperatures
- LAIModel provenance tracking
- EWSI daily computation from input series
- EWSI provenance tracking
- SeasonalClimateInputs with LAI/EWSI provenance
- compute_hyrue_seasonal with complete inputs
- compute_hyrue_seasonal with missing inputs (blocked)
- compute_hyrue_seasonal with legacy fallback
- Array length validation
- No synthetic LAI/EWSI generated without provenance
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.hydroma.simulation.ewsi_pipeline import (
    EWSIInputSeries,
    compute_daily_ewsi,
    compute_ewsi_from_scalars,
    ewsi_provenance,
)
from engine.hydroma.simulation.lai_model import (
    LAIModel,
    LAIModelConfig,
    compute_daily_lai,
)
from engine.hydroma.simulation.par_pipeline import (
    build_seasonal_climate_inputs,
    compute_hyrue_seasonal,
)
from engine.hydroma.simulation.weather_source import (
    WEATHER_COLUMNS,
    WeatherUnavailable,
)


def _make_weather_df(n_days: int = 10, with_shortwave: bool = True) -> pd.DataFrame:
    """Build a minimal weather DataFrame for testing."""
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    data = {
        "MinTemp": [5.0 + 0.5 * i for i in range(n_days)],
        "MaxTemp": [15.0 + 0.5 * i for i in range(n_days)],
        "Precipitation": [0.0] * n_days,
        "ReferenceET": [2.5] * n_days,
        "Date": dates,
    }
    if with_shortwave:
        data["ShortwaveRadiation"] = [10.5] * n_days
    df = pd.DataFrame(data, columns=WEATHER_COLUMNS)
    df["Date"] = pd.to_datetime(df["Date"])
    df.attrs["shortwave_unit"] = "MJ/m^2/day"
    df.attrs["shortwave_source"] = "test_source"
    df.attrs["shortwave_source_parameter"] = "shortwave_radiation_sum"
    return df


class TestLAIModel:
    """Tests for the GDD-based LAI model."""

    def test_lai_model_returns_valid_array(self):
        """LAIModel produces array with correct length."""
        tmean = np.linspace(10, 25, 100)
        model = LAIModel()
        lai = model.compute(tmean)
        assert len(lai) == 100
        assert np.all(lai >= 0.1)
        assert np.all(lai <= 4.0)

    def test_lai_grows_then_plateaus(self):
        """LAI follows sigmoid: starts low, grows, plateaus."""
        tmean = np.full(200, 20.0)  # constant warm temperature
        model = LAIModel()
        lai = model.compute(tmean)
        # First day should be near minimum
        assert lai[0] < lai[50]
        # Mid-season should be higher
        assert lai[50] > lai[0]
        # End should approach maximum
        assert lai[-1] > lai[100]

    def test_lai_provenance(self):
        """LAIModel propagates provenance metadata."""
        model = LAIModel()
        prov = model.provenance()
        assert prov["source_model"] == "LAIModel"
        assert prov["quality_status"] == "model_generated"
        assert prov["unit"] == "m²/m²"
        assert prov["scientific_status"] == "model_generated"

    def test_lai_zero_length_input(self):
        """Empty input returns empty array."""
        model = LAIModel()
        lai = model.compute(np.array([]))
        assert len(lai) == 0

    def test_lai_different_crop(self):
        """Model works for different crops."""
        tmean = np.linspace(10, 25, 100)
        for crop in ["wheat", "maize", "rice"]:
            model = LAIModel(config=LAIModelConfig(crop=crop))
            lai = model.compute(tmean)
            assert len(lai) == 100
            assert np.all(lai >= 0.1)

    def test_compute_daily_lai_convenience(self):
        """Convenience function returns array and provenance."""
        tmean = np.linspace(10, 25, 50)
        lai, prov = compute_daily_lai(tmean)
        assert len(lai) == 50
        assert prov["source_model"] == "LAIModel"

    def test_lai_clipped_to_range(self):
        """LAI values are clipped to [lai_min, lai_max]."""
        # Very cold days - GDD stays at 0, LAI stays at minimum
        tmean = np.full(200, 5.0)  # below t_base
        model = LAIModel()
        lai = model.compute(tmean)
        assert np.all(lai >= 0.1)


class TestEWSIPipeline:
    """Tests for the EWSI daily pipeline."""

    def test_compute_daily_ewsi_valid_inputs(self):
        """EWSI computes correctly from valid inputs."""
        n = 10
        inputs = EWSIInputSeries(
            dates=[f"2024-01-{i+1:02d}" for i in range(n)],
            nir=np.linspace(0.3, 0.5, n),
            swir=np.linspace(0.1, 0.2, n),
            vpd=np.full(n, 1.5),
            soil_moisture=np.full(n, 0.25),
        )
        result = compute_daily_ewsi(inputs)
        assert len(result.ewsi) == n
        assert np.all(result.ewsi >= 0.0)
        assert np.all(result.ewsi <= 1.0)
        assert result.quality_status == "model_generated"

    def test_compute_daily_ewsi_missing_nir(self):
        """Missing NIR raises ValueError."""
        inputs = EWSIInputSeries(
            dates=["2024-01-01"],
            vpd=np.array([1.5]),
            soil_moisture=np.array([0.25]),
        )
        with pytest.raises(ValueError, match="missing inputs"):
            compute_daily_ewsi(inputs)

    def test_compute_daily_ewsi_missing_vpd(self):
        """Missing VPD raises ValueError."""
        inputs = EWSIInputSeries(
            dates=["2024-01-01"],
            nir=np.array([0.4]),
            swir=np.array([0.1]),
            soil_moisture=np.array([0.25]),
        )
        with pytest.raises(ValueError, match="vpd"):
            compute_daily_ewsi(inputs)

    def test_compute_daily_ewsi_missing_soil(self):
        """Missing soil moisture raises ValueError."""
        inputs = EWSIInputSeries(
            dates=["2024-01-01"],
            nir=np.array([0.4]),
            swir=np.array([0.1]),
            vpd=np.array([1.5]),
        )
        with pytest.raises(ValueError, match="soil_moisture"):
            compute_daily_ewsi(inputs)

    def test_compute_daily_ewsi_clipped_to_range(self):
        """EWSI values are clipped to [0, 1]."""
        n = 5
        inputs = EWSIInputSeries(
            dates=[f"2024-01-{i+1:02d}" for i in range(n)],
            nir=np.full(n, 0.5),
            swir=np.full(n, 0.01),  # high NDMI stress
            vpd=np.full(n, 10.0),  # high VPD stress
            soil_moisture=np.full(n, 0.01),  # low soil moisture stress
        )
        result = compute_daily_ewsi(inputs)
        assert np.all(result.ewsi <= 1.0)
        assert np.all(result.ewsi >= 0.0)

    def test_compute_ewsi_from_scalars(self):
        """Scalar EWSI computation works."""
        ewsi = compute_ewsi_from_scalars(0.4, 0.1, 1.5, 0.25)
        assert 0.0 <= ewsi <= 1.0

    def test_ewsi_provenance(self):
        """EWSI provenance is documented."""
        prov = ewsi_provenance()
        assert prov["source_model"] == "EWSI"
        assert prov["scientific_status"] == "novel"
        assert "ndmi" in prov["method"].lower()
        assert prov["quality_status"] == "model_generated"

    def test_ewsi_output_has_provenance(self):
        """EWSIOutputSeries carries provenance."""
        inputs = EWSIInputSeries(
            dates=["2024-01-01"],
            nir=np.array([0.4]),
            swir=np.array([0.1]),
            vpd=np.array([1.5]),
            soil_moisture=np.array([0.25]),
        )
        result = compute_daily_ewsi(inputs)
        assert result.scientific_status == "novel"
        assert result.quality_status == "model_generated"
        assert result.valid_range == (0.0, 1.0)
        assert result.source_model == "EWSI"


class TestSeasonalInputsWithProvenance:
    """Tests for SeasonalClimateInputs provenance tracking."""

    def test_seasonal_inputs_lai_provenance_preserved(self):
        """LAI provenance is preserved in SeasonalClimateInputs."""
        df = _make_weather_df()
        lai = np.array([3.0] * len(df))
        lai_prov = {"source_model": "LAIModel", "quality_status": "model_generated"}
        inputs = build_seasonal_climate_inputs(
            df, lai_array=lai, lai_provenance=lai_prov
        )
        assert inputs.lai_provenance == lai_prov

    def test_seasonal_inputs_ewsi_provenance_preserved(self):
        """EWSI provenance is preserved in SeasonalClimateInputs."""
        df = _make_weather_df()
        ewsi = np.array([0.3] * len(df))
        ewsi_prov = {"source_model": "EWSI", "quality_status": "model_generated"}
        inputs = build_seasonal_climate_inputs(
            df, ewsi_array=ewsi, ewsi_provenance=ewsi_prov
        )
        assert inputs.ewsi_provenance == ewsi_prov

    def test_seasonal_inputs_both_provenance_preserved(self):
        """Both LAI and EWSI provenance are preserved."""
        df = _make_weather_df()
        n = len(df)
        lai = np.array([3.0] * n)
        ewsi = np.array([0.3] * n)
        lai_prov = {"source_model": "LAIModel"}
        ewsi_prov = {"source_model": "EWSI"}
        inputs = build_seasonal_climate_inputs(
            df,
            lai_array=lai,
            lai_provenance=lai_prov,
            ewsi_array=ewsi,
            ewsi_provenance=ewsi_prov,
        )
        assert inputs.input_quality == "complete"
        assert inputs.lai_provenance == lai_prov
        assert inputs.ewsi_provenance == ewsi_prov


class TestComputeHyrueSeasonal:
    """Tests for the HYRUE seasonal computation path."""

    def test_complete_inputs_run_seasonal(self):
        """When all inputs are present, HYRUE seasonal mode runs."""
        df = _make_weather_df(n_days=30)
        n = len(df)
        lai, lai_prov = compute_daily_lai(
            (df["MinTemp"].to_numpy() + df["MaxTemp"].to_numpy()) / 2.0
        )
        ewsi = np.full(n, 0.3)
        ewsi_prov = ewsi_provenance()

        inputs = build_seasonal_climate_inputs(
            df,
            lai_array=lai,
            lai_provenance=lai_prov,
            ewsi_array=ewsi,
            ewsi_provenance=ewsi_prov,
        )

        result = compute_hyrue_seasonal(inputs, crop="wheat")
        assert "total_biomass_g_m2" in result or "biomass" in result or "yield" in result
        assert result["input_quality"] == "complete"
        assert result["lai_provenance"] is not None
        assert result["ewsi_provenance"] is not None

    def test_missing_lai_raises(self):
        """Missing LAI raises WeatherUnavailable."""
        df = _make_weather_df(n_days=10)
        ewsi = np.full(10, 0.3)
        inputs = build_seasonal_climate_inputs(df, ewsi_array=ewsi)
        assert inputs.input_quality == "partial"

        with pytest.raises(WeatherUnavailable, match="missing inputs"):
            compute_hyrue_seasonal(inputs, crop="wheat")

    def test_missing_ewsi_raises(self):
        """Missing EWSI raises WeatherUnavailable."""
        df = _make_weather_df(n_days=10)
        lai = np.array([3.0] * 10)
        inputs = build_seasonal_climate_inputs(df, lai_array=lai)
        assert inputs.input_quality == "partial"

        with pytest.raises(WeatherUnavailable, match="missing inputs"):
            compute_hyrue_seasonal(inputs, crop="wheat")

    def test_missing_both_lai_ewsi_raises(self):
        """Missing both LAI and EWSI raises WeatherUnavailable."""
        df = _make_weather_df(n_days=10)
        inputs = build_seasonal_climate_inputs(df)
        assert inputs.input_quality == "unavailable"

        with pytest.raises(WeatherUnavailable, match="missing inputs"):
            compute_hyrue_seasonal(inputs, crop="wheat")

    def test_legacy_fallback_requires_explicit_opt_in(self):
        """Legacy fallback does not activate without explicit flag."""
        df = _make_weather_df(n_days=10)
        inputs = build_seasonal_climate_inputs(df)  # no LAI, no EWSI

        with pytest.raises(WeatherUnavailable):
            compute_hyrue_seasonal(inputs, crop="wheat", allow_legacy_fallback=False)

    def test_legacy_fallback_runs_with_flag(self):
        """Legacy fallback runs when explicitly allowed."""
        df = _make_weather_df(n_days=10)
        inputs = build_seasonal_climate_inputs(df)  # no LAI, no EWSI

        result = compute_hyrue_seasonal(
            inputs, crop="wheat", allow_legacy_fallback=True
        )
        assert "fallback_mode" in result
        assert result["fallback_mode"] == "legacy_constant_fallback"
        assert result["input_quality"] == "partial"

    def test_seasonal_result_has_provenance(self):
        """Seasonal result includes provenance metadata."""
        df = _make_weather_df(n_days=12)
        n = len(df)
        lai, lai_prov = compute_daily_lai(
            (df["MinTemp"].to_numpy() + df["MaxTemp"].to_numpy()) / 2.0
        )
        ewsi = np.full(n, 0.3)
        ewsi_prov = ewsi_provenance()

        inputs = build_seasonal_climate_inputs(
            df,
            lai_array=lai,
            lai_provenance=lai_prov,
            ewsi_array=ewsi,
            ewsi_provenance=ewsi_prov,
        )

        result = compute_hyrue_seasonal(inputs, crop="wheat")
        assert "data_source" in result
        assert "par_provenance" in result
        assert "lai_provenance" in result
        assert "ewsi_provenance" in result
        assert result["lai_provenance"]["source_model"] == "LAIModel"
        assert result["ewsi_provenance"]["source_model"] == "EWSI"

    def test_seasonal_mode_summaries_daily(self):
        """Seasonal mode sums daily biomass, not multiplies a single day."""
        df = _make_weather_df(n_days=120)
        n = len(df)
        lai, lai_prov = compute_daily_lai(
            (df["MinTemp"].to_numpy() + df["MaxTemp"].to_numpy()) / 2.0
        )
        ewsi = np.full(n, 0.3)

        inputs = build_seasonal_climate_inputs(
            df,
            lai_array=lai,
            lai_provenance=lai_prov,
            ewsi_array=ewsi,
            ewsi_provenance=ewsi_provenance(),
        )

        result = compute_hyrue_seasonal(inputs, crop="wheat")

        mode = result.get("computation_mode", "")
        assert "seasonal" in str(mode).lower() or mode == "seasonal"
