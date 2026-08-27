"""
Copernicus CDS API Integration - ERA5-Land & ERA5 Data Access.

This module provides tier-1 climate data access using Copernicus CDS API.

Datasets available:
- reanalysis-era5-land (9km, hourly, 1950-now)
- reanalysis-era5-single-levels (31km, hourly, 1940-now)
- satellite-soil-moisture
- sis-agrometeorological-indicators

Usage:
    from services.data_sources.copernicus_cds import CopernicusCDSClient
    client = CopernicusCDSClient()
    data = client.fetch_era5_land(
        latitude=float(os.getenv('DEFAULT_LATITUDE', '35.6892')),
        longitude=float(os.getenv('DEFAULT_LONGITUDE', '51.3890')),
        start_date="2023-01-01",
        end_date="2023-12-31",
        variables=["2m_temperature", "total_precipitation"]
    )
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("econojin.copernicus")

# Cache directory for downloaded data
CACHE_DIR = Path("data/copernicus_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class CopernicusCDSClient:
    """Client for Copernicus Climate Data Store API."""

    def __init__(self, api_key: str | None = None, api_url: str | None = None):
        """Initialize CDS client with credentials."""
        self.api_key = api_key or os.getenv("COPERNICUS_CDS_API_KEY")
        self.api_url = api_url or os.getenv("COPERNICUS_CDS_URL", "https://cds.climate.copernicus.eu/api")

        if not self.api_key:
            logger.warning("COPERNICUS_CDS_API_KEY not set")
            self._client = None
        else:
            try:
                import cdsapi
                self._client = cdsapi.Client(
                    url=self.api_url,
                    key=self.api_key,
                    quiet=True,
                )
                logger.info("CDS client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize CDS client: {e}")
                self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def _cache_key(self, dataset: str, params: dict) -> str:
        """Generate cache key for request."""
        key_str = json.dumps({"dataset": dataset, **params}, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        return CACHE_DIR / f"{cache_key}.nc"

    def _is_cached(self, cache_key: str, max_age_hours: int = 24) -> bool:
        """Check if data is cached and fresh."""
        path = self._get_cache_path(cache_key)
        if not path.exists():
            return False
        age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
        return age_hours < max_age_hours

    def fetch_era5_land(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        variables: list[str] | None = None,
        area: list[float] | None = None,
    ) -> dict[str, Any] | None:
        """
        Fetch ERA5-Land data (9km resolution, highest quality).
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            variables: List of variables to fetch
            area: [north, west, south, east] bounding box (default: 0.5deg)
        
        Returns:
            Dictionary with downloaded data or None on failure
        """
        if not self.is_available:
            logger.warning("CDS client not available")
            return None

        if variables is None:
            variables = [
                "2m_temperature",
                "2m_dewpoint_temperature",
                "total_precipitation",
                "surface_solar_radiation_downwards",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "surface_pressure",
            ]

        if area is None:
            # 0.5 degree box around point (~55km)
            area = [
                latitude + 0.25,
                longitude - 0.25,
                latitude - 0.25,
                longitude + 0.25,
            ]

        # Generate date list
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        request_params = {
            "variable": variables,
            "year": list(set(d.split("-")[0] for d in dates)),
            "month": list(set(d.split("-")[1] for d in dates)),
            "day": list(set(d.split("-")[2] for d in dates)),
            "time": [f"{h:02d}:00" for h in range(0, 24, 6)],  # Every 6 hours
            "data_format": "netcdf",
            "area": area,
        }

        cache_key = self._cache_key("reanalysis-era5-land", request_params)

        if self._is_cached(cache_key, max_age_hours=168):  # 7 days
            logger.info("Using cached ERA5-Land data")
            return {"cache_path": str(self._get_cache_path(cache_key)), "from_cache": True}

        try:
            target_path = str(self._get_cache_path(cache_key))
            logger.info(f"Downloading ERA5-Land data for {len(dates)} days...")

            self._client.retrieve(
                "reanalysis-era5-land",
                request_params,
                target_path
            )

            logger.info(f"Downloaded to: {target_path}")
            return {
                "cache_path": target_path,
                "from_cache": False,
                "days": len(dates),
                "variables": variables,
            }
        except Exception as e:
            logger.error(f"CDS download failed: {e}")
            return None

    def fetch_soil_moisture(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any] | None:
        """Fetch soil moisture data from satellite observations."""
        if not self.is_available:
            return None

        request_params = {
            "variable": "volumetric_surface_soil_moisture",
            "satellite": "combined",
            "sensor": "active_passive",
            "year": start_date.split("-")[0],
            "month": start_date.split("-")[1],
            "day": start_date.split("-")[2],
            "time": "00:00",
            "data_format": "netcdf",
            "area": [latitude + 0.25, longitude - 0.25, latitude - 0.25, longitude + 0.25],
        }

        cache_key = self._cache_key("satellite-soil-moisture", request_params)

        if self._is_cached(cache_key):
            return {"cache_path": str(self._get_cache_path(cache_key)), "from_cache": True}

        try:
            target_path = str(self._get_cache_path(cache_key))
            self._client.retrieve(
                "satellite-soil-moisture",
                request_params,
                target_path
            )
            return {"cache_path": target_path, "from_cache": False}
        except Exception as e:
            logger.error(f"Soil moisture download failed: {e}")
            return None


# Singleton instance
_cds_client = None

def get_cds_client() -> CopernicusCDSClient:
    """Get singleton CDS client."""
    global _cds_client
    if _cds_client is None:
        _cds_client = CopernicusCDSClient()
    return _cds_client
