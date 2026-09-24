"""Drought Analysis Agent — SPI/SPEI calculation with NASA POWER & Open-Meteo."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import httpx
import numpy as np
import pandas as pd
import xarray as xr
from xclim.indices import standardized_precipitation_index as spi, standardized_precipitation_evapotranspiration_index as spei


@dataclass
class DroughtConfig:
    nasa_power_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    open_meteo_url: str = "https://archive-api.open-meteo.com/v1/era5"
    default_months: int = 6


class DroughtAgent:
    """Analyzes drought conditions using SPI (Standardized Precipitation Index)
    and SPEI (Standardized Precipitation Evapotranspiration Index)."""

    def __init__(self, config: DroughtConfig | None = None):
        self.config = config or DroughtConfig()
        self._client = httpx.AsyncClient(timeout=30.0)

    async def _fetch_nasa_power(
        self, lat: float, lon: float, start: date, end: date
    ) -> pd.DataFrame:
        """Fetch daily weather from NASA POWER."""
        params = {
            "parameters": "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN",
            "community": "AG",
            "latitude": lat,
            "longitude": lon,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "format": "JSON",
        }
        response = await self._client.get(self.config.nasa_power_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Parse NASA POWER response
        records = data.get("properties", {}).get("parameter", {})
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame({
            "date": pd.date_range(start, end, freq="D"),
            "precip": [records.get("PRECTOTCORR", {}).get(d.strftime("%Y%m%d"), np.nan) for d in pd.date_range(start, end)],
            "t2m": [records.get("T2M", {}).get(d.strftime("%Y%m%d"), np.nan) for d in pd.date_range(start, end)],
            "t2m_max": [records.get("T2M_MAX", {}).get(d.strftime("%Y%m%d"), np.nan) for d in pd.date_range(start, end)],
            "t2m_min": [records.get("T2M_MIN", {}).get(d.strftime("%Y%m%d"), np.nan) for d in pd.date_range(start, end)],
            "solar": [records.get("ALLSKY_SFC_SW_DWN", {}).get(d.strftime("%Y%m%d"), np.nan) for d in pd.date_range(start, end)],
        })
        df["date"] = pd.to_datetime(df["date"])
        return df.dropna()

    async def _fetch_open_meteo(
        self, lat: float, lon: float, start: date, end: date
    ) -> pd.DataFrame:
        """Fetch daily weather from Open-Meteo ERA5 archive."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,temperature_2m_mean,et0_fao_evapotranspiration",
            "timezone": "UTC",
        }
        response = await self._client.get(self.config.open_meteo_url, params=params)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        if not daily:
            return pd.DataFrame()

        df = pd.DataFrame({
            "date": pd.to_datetime(daily.get("time", [])),
            "precip": daily.get("precipitation_sum", []),
            "t2m_max": daily.get("temperature_2m_max", []),
            "t2m_min": daily.get("temperature_2m_min", []),
            "t2m_mean": daily.get("temperature_2m_mean", []),
            "et0": daily.get("et0_fao_evapotranspiration", []),
        })
        return df.dropna()

    async def _fetch_weather(
        self, lat: float, lon: float, months: int
    ) -> pd.DataFrame:
        """Try Open-Meteo first (free, no key), fallback to NASA POWER."""
        end = date.today() - timedelta(days=1)  # Open-Meteo archive lags 1 day
        start = end - timedelta(days=months * 30)

        # Try Open-Meteo first
        try:
            df = await self._fetch_open_meteo(lat, lon, start, end)
            if not df.empty:
                return df
        except Exception:
            pass

        # Fallback to NASA POWER
        try:
            df = await self._fetch_nasa_power(lat, lon, start, end)
            if not df.empty:
                return df
        except Exception:
            pass

        return pd.DataFrame()

    def _calculate_spi(self, precip: np.ndarray, scale: int = 3) -> float:
        """Calculate SPI using xclim."""
        # xclim expects xarray DataArray with time dimension
        da = xr.DataArray(precip, dims=["time"], coords={"time": np.arange(len(precip))})
        result = spi(da, freq=f"{scale}MS")
        return float(result.values[-1]) if result.size > 0 else 0.0

    def _calculate_spei(
        self, precip: np.ndarray, pet: np.ndarray, scale: int = 3
    ) -> float:
        """Calculate SPEI using xclim."""
        da_precip = xr.DataArray(precip, dims=["time"], coords={"time": np.arange(len(precip))})
        da_pet = xr.DataArray(pet, dims=["time"], coords={"time": np.arange(len(precip))})
        result = spei(da_precip, da_pet, freq=f"{scale}MS")
        return float(result.values[-1]) if result.size > 0 else 0.0

    def _interpret_spi(self, spi_value: float) -> str:
        if spi_value >= 2.0:
            return "بسیار مرطوب (Extremely Wet)"
        elif spi_value >= 1.5:
            return "مرطوب (Very Wet)"
        elif spi_value >= 1.0:
            return "نسبتاً مرطوب (Moderately Wet)"
        elif spi_value >= -1.0:
            return "طبیعی (Near Normal)"
        elif spi_value > -1.5:
            return "نسبتاً خشک (Moderately Dry)"
        elif spi_value > -2.0:
            return "خشک (Severely Dry)"
        else:
            return "بسیار خشک (Extremely Dry)"

    def _interpret_spei(self, spei_value: float) -> str:
        # Same thresholds as SPI
        return self._interpret_spi(spei_value)

    async def analyze(
        self,
        lat: float,
        lon: float,
        months: int = 6,
        scales: list[int] = [1, 3, 6, 12],
    ) -> dict[str, Any]:
        """Main analysis entry point."""
        df = await self._fetch_weather(lat, lon, months)

        if df.empty:
            return {
                "error": "No weather data available for this location",
                "lat": lat,
                "lon": lon,
            }

        precip = df["precip"].values
        pet = df.get("et0", df.get("solar", np.zeros_like(precip))).values
        # If PET not available, estimate from temperature (Thornthwaite approximation)
        if "et0" not in df.columns and "solar" in df.columns:
            # Rough estimation: PET ≈ 0.0023 * (T+17.8) * sqrt(Tmax-Tmin) * Ra
            tmax = df["t2m_max"].values
            tmin = df["t2m_min"].values
            tmean = df.get("t2m_mean", (tmax + tmin) / 2).values
            ra = df["solar"].values * 0.0864  # Convert W/m2 to MJ/m2/day
            pet = 0.0023 * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0)) * ra

        results = {
            "location": {"lat": lat, "lon": lon},
            "period": {"months": months, "data_points": len(df)},
            "spi": {},
            "spei": {},
            "summary": "",
        }

        for scale in scales:
            if len(precip) >= scale * 30:
                spi_val = self._calculate_spi(precip, scale)
                spei_val = self._calculate_spei(precip, pet, scale)
                results["spi"][f"{scale}month"] = {
                    "value": round(spi_val, 2),
                    "interpretation": self._interpret_spi(spi_val),
                }
                results["spei"][f"{scale}month"] = {
                    "value": round(spei_val, 2),
                    "interpretation": self._interpret_spei(spei_val),
                }

        # Summary
        latest_spi = results["spi"].get("3month", {}).get("value", 0)
        latest_spei = results["spei"].get("3month", {}).get("value", 0)
        results["summary"] = (
            f"SPI (3-month): {latest_spi:.2f} — {self._interpret_spi(latest_spi)}. "
            f"SPEI (3-month): {latest_spei:.2f} — {self._interpret_spei(latest_spei)}."
        )

        return results

    async def close(self):
        await self._client.aclose()


# Singleton
_drought_agent: DroughtAgent | None = None


def get_drought_agent() -> DroughtAgent:
    global _drought_agent
    if _drought_agent is None:
        _drought_agent = DroughtAgent()
    return _drought_agent