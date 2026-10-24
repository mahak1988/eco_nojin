"""Tests for the weather data pipeline's shortwave-to-PAR converter.

Tests cover:
- Unit conversion (MJ/m²/day and kW-hr/m²/day → MJ/m²/day)
- PAR fraction application (0.5 default)
- Double-conversion guard (already_par)
- NaN and Infinity handling
- Unrecognised unit rejection
- Weather DataFrame shortwave fetch and provenance
- SeasonalClimateInputs assembly
"""

from __future__ import annotations

import math
from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from engine.hydroma.simulation.par_pipeline import (
    DEFAULT_PAR_SPEC,
    SeasonalClimateInputs,
    build_seasonal_climate_inputs,
    convert_shortwave_to_par,
)
from engine.hydroma.simulation.radiation_units import DEFAULT_PAR_FRACTION
from engine.hydroma.simulation.weather_source import (
    KWH_TO_MJ,
    WEATHER_COLUMNS,
    fetch_daily_weather,
)


class TestShortwaveToPAR:
    """Tests for the convert_shortwave_to_par function."""

    def test_basic_mj_conversion(self):
        """10 MJ/m²/day shortwave → 5 MJ/m²/day PAR (0.5 fraction)."""
        par, spec = convert_shortwave_to_par(10.0, "MJ/m^2/day")
        assert par == pytest.approx(5.0)
        assert spec is not None
        assert spec.frac_par == DEFAULT_PAR_FRACTION
        assert spec.status == "estimated"

    def test_basic_kwh_conversion(self):
        """10 kW-hr/m²/day → 36 MJ/m²/day shortwave → 18 MJ/m²/day PAR."""
        par, spec = convert_shortwave_to_par(10.0, "kW-hr/m^2/day")
        expected_sw_mj = 10.0 * KWH_TO_MJ  # 36 MJ/m²/day
        expected_par = expected_sw_mj * DEFAULT_PAR_FRACTION  # 18
        assert par == pytest.approx(expected_par)
        assert spec is not None
        assert spec.frac_par == DEFAULT_PAR_FRACTION

    def test_kwh_to_mj_factor(self):
        """Verify the kwh→MJ conversion factor is 3.6."""
        assert KWH_TO_MJ == 3.6

    def test_default_par_fraction(self):
        """Default PAR fraction must be 0.5 (not a measured crop parameter)."""
        assert DEFAULT_PAR_FRACTION == 0.5

    def test_unit_normalization_whitespace(self):
        """Whitespace and dot variations in unit string are normalised."""
        par1, _ = convert_shortwave_to_par(10.0, "MJ/m^2/day")
        par2, _ = convert_shortwave_to_par(10.0, " MJ / m2 / day ")
        assert par1 == pytest.approx(par2)

    def test_unit_normalization_dotless(self):
        """Dotless unit variant 'kw-hr/m2/day' is accepted."""
        par, spec = convert_shortwave_to_par(10.0, "kw-hr/m2/day")
        assert par == pytest.approx(10.0 * KWH_TO_MJ * DEFAULT_PAR_FRACTION)

    def test_nan_input_returns_nan(self):
        """NaN input → NaN output, no spec."""
        par, spec = convert_shortwave_to_par(float("nan"), "MJ/m^2/day")
        assert math.isnan(par)
        assert spec is None

    def test_infinity_input_returns_infinity(self):
        """Infinity input → Infinity output, no spec."""
        par, spec = convert_shortwave_to_par(float("inf"), "MJ/m^2/day")
        assert math.isinf(par)
        assert spec is None

    def test_already_par_no_conversion(self):
        """When already_par=True, no fraction is applied."""
        par, spec = convert_shortwave_to_par(5.0, "MJ/m^2/day", already_par=True)
        assert par == pytest.approx(5.0)
        assert spec is not None
        assert spec.frac_par == 1.0
        assert spec.status == "observed"
        assert "already" in spec.method.lower()

    def test_custom_spec(self):
        """A custom spec overrides the default fraction."""
        custom = DEFAULT_PAR_SPEC.__class__(
            frac_par=0.45,
            method="custom",
            reference="test",
            status="documented",
            coeff_source="test_source",
        )
        par, spec = convert_shortwave_to_par(10.0, "MJ/m^2/day", spec=custom)
        assert par == pytest.approx(4.5)
        assert spec.frac_par == 0.45
        assert spec.status == "documented"

    def test_unrecognised_unit_raises(self):
        """An unrecognised unit raises ValueError."""
        with pytest.raises(ValueError, match="Unrecognised shortwave unit"):
            convert_shortwave_to_par(10.0, "bogons/m²/day")

    def test_zero_shortwave(self):
        """Zero shortwave → zero PAR."""
        par, spec = convert_shortwave_to_par(0.0, "MJ/m^2/day")
        assert par == 0.0
        assert spec is not None


class TestWeatherFetchShortwave:
    """Tests for shortwave radiation inclusion in fetch_daily_weather."""

    def _make_daily_df(self, with_shortwave: bool = True) -> pd.DataFrame:
        """Build a minimal weather DataFrame."""
        dates = [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
        data = {
            "MinTemp": [5.0, 6.0, 4.0],
            "MaxTemp": [15.0, 16.0, 14.0],
            "Precipitation": [0.0, 1.5, 0.0],
            "ReferenceET": [2.5, 2.7, 2.3],
            "Date": dates,
        }
        if with_shortwave:
            data["ShortwaveRadiation"] = [10.5, 12.0, 8.5]
        df = pd.DataFrame(data, columns=WEATHER_COLUMNS)
        df["Date"] = pd.to_datetime(df["Date"])
        df.attrs["shortwave_unit"] = "MJ/m^2/day"
        df.attrs["shortwave_source"] = "test_source"
        df.attrs["shortwave_source_parameter"] = "shortwave_radiation_sum"
        return df

    def test_weather_columns_include_shortwave(self):
        """WEATHER_COLUMNS must include ShortwaveRadiation."""
        assert "ShortwaveRadiation" in WEATHER_COLUMNS

    def test_build_seasonal_inputs_complete(self):
        """All inputs provided → input_quality='complete'."""
        df = self._make_daily_df()
        lai = np.array([3.0, 3.2, 3.5])
        ewsi = np.array([0.5, 0.4, 0.3])

        inputs = build_seasonal_climate_inputs(df, lai_array=lai, ewsi_array=ewsi)

        assert inputs.input_quality == "complete"
        assert inputs.missing_fields == []
        assert inputs.par is not None
        assert inputs.par_provenance == "converted_documented"
        assert inputs.lai is not None
        assert inputs.ewsi is not None
        assert inputs.t_mean is not None
        assert len(inputs.dates) == 3
        # PAR should be shortwave * 0.5
        assert inputs.par[0] == pytest.approx(10.5 * DEFAULT_PAR_FRACTION)

    def test_build_seasonal_inputs_partial_missing_lai(self):
        """Missing LAI → input_quality='partial'."""
        df = self._make_daily_df()
        ewsi = np.array([0.5, 0.4, 0.3])

        inputs = build_seasonal_climate_inputs(df, ewsi_array=ewsi)

        assert inputs.input_quality == "partial"
        assert "lai" in inputs.missing_fields
        assert inputs.lai is None

    def test_build_seasonal_inputs_partial_missing_ewsi(self):
        """Missing EWSI → input_quality='partial'."""
        df = self._make_daily_df()
        lai = np.array([3.0, 3.2, 3.5])

        inputs = build_seasonal_climate_inputs(df, lai_array=lai)

        assert inputs.input_quality == "partial"
        assert "ewsi" in inputs.missing_fields
        assert inputs.ewsi is None

    def test_build_seasonal_inputs_unavailable_missing_both(self):
        """Missing both LAI and EWSI → input_quality='unavailable'."""
        df = self._make_daily_df()

        inputs = build_seasonal_climate_inputs(df)

        assert inputs.input_quality == "unavailable"
        assert set(inputs.missing_fields) == {"lai", "ewsi"}

    def test_build_seasonal_inputs_no_shortwave_raises(self):
        """No ShortwaveRadiation column (or all-NaN) → WeatherUnavailable."""
        df = self._make_daily_df(with_shortwave=True)
        # Replace shortwave data with NaN to simulate missing data
        df["ShortwaveRadiation"] = float("nan")

        with pytest.raises(Exception, match="ShortwaveRadiation"):
            build_seasonal_climate_inputs(df)

    def test_build_seasonal_inputs_t_mean_calculation(self):
        """T_mean = (Tmin + Tmax) / 2 with optional offset."""
        df = self._make_daily_df()
        inputs_default = build_seasonal_climate_inputs(df)
        expected = (np.array([5.0, 6.0, 4.0]) + np.array([15.0, 16.0, 14.0])) / 2.0
        assert np.allclose(inputs_default.t_mean, expected)

        inputs_offset = build_seasonal_climate_inputs(df, t_mean_offset_c=2.0)
        assert np.allclose(inputs_offset.t_mean, expected + 2.0)

    def test_build_seasonal_inputs_length_mismatch_lai(self):
        """LAI array length mismatch raises ValueError."""
        df = self._make_daily_df()
        lai = np.array([3.0, 3.2])  # wrong length

        with pytest.raises(ValueError, match="lai_array length"):
            build_seasonal_climate_inputs(df, lai_array=lai)

    def test_build_seasonal_inputs_length_mismatch_ewsi(self):
        """EWSI array length mismatch raises ValueError."""
        df = self._make_daily_df()
        ewsi = np.array([0.5, 0.4, 0.3, 0.2])  # wrong length

        with pytest.raises(ValueError, match="ewsi_array length"):
            build_seasonal_climate_inputs(df, ewsi_array=ewsi)

    def test_build_seasonal_inputs_preserves_shortwave_raw(self):
        """Raw shortwave values are preserved in shortwave_raw."""
        df = self._make_daily_df()
        lai = np.array([3.0, 3.2, 3.5])
        ewsi = np.array([0.5, 0.4, 0.3])

        inputs = build_seasonal_climate_inputs(df, lai_array=lai, ewsi_array=ewsi)

        assert inputs.shortwave_raw is not None
        assert inputs.shortwave_raw[0] == pytest.approx(10.5)
        assert inputs.shortwave_raw[1] == pytest.approx(12.0)
        assert inputs.shortwave_source == "test_source (shortwave_radiation_sum)"


class TestSeasonalClimateInputsDataclass:
    """Tests for the SeasonalClimateInputs dataclass."""

    def test_defaults(self):
        """Dataclass has sensible defaults."""
        inputs = SeasonalClimateInputs(dates=["2024-01-01"])
        assert inputs.par is None
        assert inputs.lai is None
        assert inputs.ewsi is None
        assert inputs.t_mean is None
        assert inputs.input_quality == "unavailable"
        assert inputs.missing_fields == []

    def test_provenance_field(self):
        """Provenance field defaults to 'estimated'."""
        inputs = SeasonalClimateInputs(dates=["2024-01-01"], par=np.array([5.0]))
        assert inputs.par_provenance == "estimated"

    def test_conversion_spec_field(self):
        """Conversion spec can be attached."""
        inputs = SeasonalClimateInputs(
            dates=["2024-01-01"],
            par=np.array([5.0]),
            par_conversion_spec=DEFAULT_PAR_SPEC,
        )
        assert inputs.par_conversion_spec == DEFAULT_PAR_SPEC
        assert inputs.par_conversion_spec.frac_par == 0.5


class TestFetchDailyWeatherIntegration:
    """Integration tests for the fetch_daily_weather fallback chain."""

    @patch("engine.hydroma.simulation.weather_source.requests.Session")
    def test_open_meteo_returns_shortwave_column(self, mock_session_cls):
        """Open-Meteo fetch includes ShortwaveRadiation column."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "daily": {
                "time": ["2024-01-01", "2024-01-02"],
                "temperature_2m_min": [5.0, 6.0],
                "temperature_2m_max": [15.0, 16.0],
                "precipitation_sum": [0.0, 1.5],
                "shortwave_radiation_sum": [10.5, 12.0],
            }
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        df = fetch_daily_weather(40.0, -105.0, "2024-01-01", "2024-01-02")

        assert "ShortwaveRadiation" in df.columns
        assert df["ShortwaveRadiation"].iloc[0] == pytest.approx(10.5)
        assert df["ShortwaveRadiation"].iloc[1] == pytest.approx(12.0)
        assert df.attrs["shortwave_unit"] == "MJ/m^2/day"
        assert df.attrs["shortwave_source"] == "Open-Meteo ERA5"

    @patch("engine.hydroma.simulation.weather_source.requests.Session")
    def test_nasa_power_converts_kwh_to_mj(self, mock_session_cls):
        """NASA POWER shortwave (kW-hr) is converted to MJ before storing."""
        om_resp = MagicMock()
        om_resp.status_code = 500
        om_resp.json.return_value = {"error": "mock"}

        power_resp = MagicMock()
        power_resp.status_code = 200
        power_resp.json.return_value = {
            "properties": {
                "parameter": {
                    "T2M_MIN": {"20240101": 5.0, "20240102": 6.0},
                    "T2M_MAX": {"20240101": 15.0, "20240102": 16.0},
                    "PRECTOTCORR": {"20240101": 0.0, "20240102": 1.5},
                    "ALLSKY_SFC_SW_DWN": {"20240101": 2.78, "20240102": 3.33},
                }
            }
        }

        def mock_get(url, **kwargs):
            if "power.larc.nasa.gov" in url:
                return power_resp
            return om_resp

        mock_session = MagicMock()
        mock_session.get.side_effect = mock_get
        mock_session_cls.return_value = mock_session

        df = fetch_daily_weather(40.0, -105.0, "2024-01-01", "2024-01-02")

        # 2.78 kW-hr/m²/day = 2.78 * 3.6 = 10.008 MJ/m²/day (rounded to 2 dp in code)
        assert df["ShortwaveRadiation"].iloc[0] == pytest.approx(2.78 * KWH_TO_MJ, abs=0.01)
        assert df.attrs["shortwave_source"] == "NASA POWER"
