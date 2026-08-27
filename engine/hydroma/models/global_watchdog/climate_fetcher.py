"""
Climate Data Fetcher — Open-Meteo Archive API
=============================================

Fetches monthly temperature and precipitation data from real climate records.

Source: Open-Meteo Archive API (ERA5 reanalysis, 1950-present)
URL: https://open-meteo.com/
"""
from __future__ import annotations

from typing import Any

import numpy as np


class ClimateFetcher:
    """Fetch monthly climate data from Open-Meteo Archive API."""

    URL = "https://archive-api.open-meteo.com/v1/archive"

    @classmethod
    def fetch_monthly(
        cls,
        lat: float,
        lon: float,
        year: int = 2020,
    ) -> dict[str, Any] | None:
        """
        Fetch monthly climate data for a single year.

        Parameters
        ----------
        lat, lon : float
            Geographic coordinates (WGS84)
        year : int
            Year to fetch (default: 2020)

        Returns
        -------
        dict with keys:
            t_min, t_max, p : np.ndarray (12 monthly values)
            t_ann_mean : float
            p_ann : float
        None if fetch fails
        """
        try:
            import requests
        except ImportError:
            return None

        params = {
            "latitude": lat, "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
        }

        try:
            resp = requests.get(cls.URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                return None

            daily = data.get("daily", {})
            dates = daily.get("time", [])
            t_max_arr = np.array(daily.get("temperature_2m_max", []))
            t_min_arr = np.array(daily.get("temperature_2m_min", []))
            p_arr = np.array(daily.get("precipitation_sum", []))

            # Aggregate daily to monthly
            months = [int(d.split("-")[1]) for d in dates]
            t_min_m, t_max_m, p_m = [], [], []
            for m in range(1, 13):
                mask = [i for i, mo in enumerate(months) if mo == m]
                if mask:
                    t_max_m.append(float(np.nanmax(t_max_arr[mask])))
                    t_min_m.append(float(np.nanmin(t_min_arr[mask])))
                    p_m.append(float(np.nansum(p_arr[mask])))
                else:
                    t_max_m.append(0.0)
                    t_min_m.append(0.0)
                    p_m.append(0.0)

            return {
                "t_min": np.array(t_min_m),
                "t_max": np.array(t_max_m),
                "p": np.array(p_m),
                "t_ann_mean": float(np.nanmean((t_min_arr + t_max_arr) / 2)),
                "p_ann": float(np.nansum(p_arr)),
                "source": "open-meteo-era5",
                "year": year,
            }
        except Exception as e:
            print(f"ClimateFetcher error: {e}")
            return None
