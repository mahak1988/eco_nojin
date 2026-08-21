"""Tests for the real-weather source (Open-Meteo + FAO-56 Hargreaves ET0)."""

import pytest

from engine.hydroma.simulation.weather_source import (
    WeatherUnavailable,
    fetch_daily_weather,
    growing_season_window,
    hargreaves_et0,
)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, response):
        self._response = response
        self.params = None

    def get(self, url, params=None, **kwargs):
        self.params = params
        return self._response


def _archive_body(n_days=3, start="2026-06-01"):
    import datetime

    dates = []
    for i in range(n_days):
        d = datetime.date.fromisoformat(start) + datetime.timedelta(days=i)
        dates.append(d.isoformat())
    return {
        "daily": {
            "time": dates,
            "temperature_2m_min": [12.0, 13.0, 11.0],
            "temperature_2m_max": [28.0, 30.0, 26.0],
            "precipitation_sum": [0.0, 5.2, 1.0],
        }
    }


class TestHargreaves:
    def test_summer_et0_exceeds_winter(self):
        summer = hargreaves_et0(15.0, 30.0, 40.0, 166)  # mid-June, 40N
        winter = hargreaves_et0(-2.0, 8.0, 40.0, 349)  # mid-December, 40N
        assert summer > winter
        assert summer > 0.0

    def test_never_negative(self):
        assert hargreaves_et0(0.0, 5.0, 60.0, 1) >= 0.0

    def test_equator_stable(self):
        mar = hargreaves_et0(20.0, 32.0, 0.0, 80)
        sep = hargreaves_et0(20.0, 32.0, 0.0, 263)
        assert abs(mar - sep) < 1.0


class TestFetch:
    def test_success_builds_aquacrop_frame(self):
        session = FakeSession(FakeResponse(200, _archive_body()))
        df = fetch_daily_weather(36.5, 54.0, "2026-06-01", "2026-06-03", session=session)
        assert list(df.columns) == ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]
        assert len(df) == 3
        assert df["ReferenceET"].iloc[0] > 0.0
        assert df["Date"].iloc[0] == pytest.importorskip("pandas").Timestamp("2026-06-01")

    def test_http_error_raises(self):
        session = FakeSession(FakeResponse(500, {}))
        with pytest.raises(WeatherUnavailable):
            fetch_daily_weather(36.5, 54.0, "2026-06-01", "2026-06-03", session=session)

    def test_missing_arrays_raises(self):
        session = FakeSession(FakeResponse(200, {"daily": {}}))
        with pytest.raises(WeatherUnavailable):
            fetch_daily_weather(36.5, 54.0, "2026-06-01", "2026-06-03", session=session)

    def test_window_too_long_rejected(self):
        with pytest.raises(ValueError, match="too long"):
            fetch_daily_weather(36.5, 54.0, "2026-01-01", "2027-06-01")

    def test_params_sent(self):
        session = FakeSession(FakeResponse(200, _archive_body()))
        fetch_daily_weather(36.5, 54.0, "2026-06-01", "2026-06-03", session=session)
        assert session.params["latitude"] == 36.5
        assert session.params["daily"].startswith("temperature_2m_min")


class TestWindow:
    def test_growing_season_window(self):
        start, end = growing_season_window("2020/03/01", "2020/07/20")
        assert start.isoformat() == "2020-03-01"
        assert end.isoformat() == "2020-08-04"  # harvest + 15 days
