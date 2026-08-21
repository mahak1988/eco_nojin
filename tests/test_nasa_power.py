"""Tests for the Phase 4 NASA POWER client (offline, mocked HTTP, asyncio.run)."""
import asyncio
import datetime
from typing import Optional

import httpx

from services.satellite.nasa_power import (
    fetch_climate_with_et0,
    fetch_nasa_power_data,
    get_daily_climate,
    hargreaves_et0,
    validate_climate_value,
)


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Pure math: Hargreaves ET0
# ---------------------------------------------------------------------------

def test_hargreaves_known_regime():
    # Warm, dry day -> clearly positive ET0
    et0 = hargreaves_et0(tmax=30.0, tmin=15.0, tmean=22.5, doy=180, lat=35.0)
    assert 3.0 <= et0 <= 10.0


def test_hargreaves_cold_day_low_et0():
    et0 = hargreaves_et0(tmax=8.0, tmin=2.0, tmean=5.0, doy=15, lat=35.0)
    assert 0.0 <= et0 < 3.0


def test_hargreaves_invalid_inputs_return_zero():
    assert hargreaves_et0(20, 10, 15, 0, 35) == 0.0       # doy out of range
    assert hargreaves_et0(20, 10, 15, 180, 95) == 0.0     # lat out of range
    assert hargreaves_et0(10, 20, 15, 180, 35) == 0.0     # tmax < tmin
    assert hargreaves_et0(20, 20, 20, 180, 35) == 0.0     # tmax == tmin


def test_validate_climate_value():
    assert validate_climate_value("15.5") == 15.5
    assert validate_climate_value(None, 3.0) == 3.0
    assert validate_climate_value(float("nan"), 3.0) == 3.0
    assert validate_climate_value(float("inf"), 3.0) == 3.0
    assert validate_climate_value("junk", 3.0) == 3.0
    # NASA POWER no-data fill value must be treated as missing
    assert validate_climate_value(-999.0, 3.0) == 3.0
    assert validate_climate_value(-9999.0, 3.0) == 3.0


# ---------------------------------------------------------------------------
# HTTP layer (mocked)
# ---------------------------------------------------------------------------

class FakeAsyncResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=None, response=None
            )

    def json(self):
        return self._json


class FakeAsyncClient:
    def __init__(self, response, timeout=None):
        self._response = response
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None, headers=None):
        self.calls.append((url, params))
        return self._response


def _power_payload():
    return {
        "properties": {
            "parameter": {
                "T2M": {"20260701": 25.0, "20260702": 26.0},
                "T2M_MAX": {"20260701": 32.0, "20260702": 33.0},
                "T2M_MIN": {"20260701": 18.0, "20260702": 19.0},
                "PRECTOTCORR": {"20260701": 0.0, "20260702": 5.0},
                "ALLSKY_SFC_SW_DWN": {"20260701": 22.0, "20260702": 20.0},
            }
        }
    }


def test_fetch_nasa_power_success(monkeypatch):
    fake = FakeAsyncClient(FakeAsyncResponse(200, _power_payload()))
    monkeypatch.setattr(
        "services.satellite.nasa_power.httpx.AsyncClient",
        lambda timeout=None: fake,
    )
    result = run(fetch_nasa_power_data(35.0, 51.0, "20260701", "20260702"))
    assert result["status"] == "success"
    assert result["source"] == "NASA POWER"
    assert result["temp_c"]["20260701"] == 25.0
    assert fake.calls[0][1]["latitude"] == 35.0


def test_fetch_nasa_power_http_error_is_honest(monkeypatch):
    fake = FakeAsyncClient(FakeAsyncResponse(500, {}))
    monkeypatch.setattr(
        "services.satellite.nasa_power.httpx.AsyncClient",
        lambda timeout=None: fake,
    )
    result = run(fetch_nasa_power_data(35.0, 51.0, "20260701", "20260702"))
    assert result["status"] == "error"
    assert "message" in result


def test_get_daily_climate_computes_et0(monkeypatch):
    fake = FakeAsyncClient(FakeAsyncResponse(200, _power_payload()))
    monkeypatch.setattr(
        "services.satellite.nasa_power.httpx.AsyncClient",
        lambda timeout=None: fake,
    )
    start = datetime.date(2026, 7, 1)
    end = datetime.date(2026, 7, 2)
    daily = run(get_daily_climate(35.0, 51.0, start, end))
    assert len(daily) == 2
    day = daily["20260701"]
    assert day["temp_mean_c"] == 25.0
    assert day["precipitation_mm"] == 0.0
    assert day["et0_mm"] > 0.0


def test_get_daily_climate_skips_nasa_fill_days(monkeypatch):
    """Days with -999 fill values must be skipped, never averaged in."""
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"20260701": 25.0, "20260702": -999.0},
                "T2M_MAX": {"20260701": 32.0, "20260702": -999.0},
                "T2M_MIN": {"20260701": 18.0, "20260702": -999.0},
                "PRECTOTCORR": {"20260701": 0.0, "20260702": -999.0},
                "ALLSKY_SFC_SW_DWN": {"20260701": 22.0, "20260702": -999.0},
            }
        }
    }
    fake = FakeAsyncClient(FakeAsyncResponse(200, payload))
    monkeypatch.setattr(
        "services.satellite.nasa_power.httpx.AsyncClient",
        lambda timeout=None: fake,
    )
    daily = run(
        get_daily_climate(
            35.0, 51.0,
            datetime.date(2026, 7, 1),
            datetime.date(2026, 7, 2),
        )
    )
    assert list(daily.keys()) == ["20260701"]
    assert daily["20260701"]["temp_mean_c"] == 25.0


def test_fetch_climate_with_et0_summary(monkeypatch):
    fake = FakeAsyncClient(FakeAsyncResponse(200, _power_payload()))
    monkeypatch.setattr(
        "services.satellite.nasa_power.httpx.AsyncClient",
        lambda timeout=None: fake,
    )
    start = datetime.date(2026, 7, 1)
    end = datetime.date(2026, 7, 2)
    result = run(fetch_climate_with_et0(35.0, 51.0, start, end))
    assert result["status"] == "success"
    assert result["days"] == 2
    assert result["summary"]["total_precipitation_mm"] == 5.0
    assert result["summary"]["mean_temp_c"] == 25.5
    assert result["source"] == "NASA POWER + Hargreaves ET0"


def test_fetch_climate_error_returns_error_status(monkeypatch):
    fake = FakeAsyncClient(FakeAsyncResponse(503, {}))
    monkeypatch.setattr(
        "services.satellite.nasa_power.httpx.AsyncClient",
        lambda timeout=None: fake,
    )
    start = datetime.date(2026, 7, 1)
    end = datetime.date(2026, 7, 2)
    result = run(fetch_climate_with_et0(35.0, 51.0, start, end))
    assert result["status"] == "error"
