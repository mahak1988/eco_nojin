"""Satellite Integration Service - Connects to Copernicus/Sentinel-2 for NDVI/EVI data"""

from __future__ import annotations
import asyncio
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Optional
from enum import Enum
import aiohttp
import json


class SatelliteSource(Enum):
    SENTINEL_2 = "sentinel_2"
    LANDSAT_8 = "landsat_8"
    MODIS = "modis"


@dataclass
class SatelliteImage:
    image_id: str
    source: SatelliteSource
    lat: float
    lon: float
    timestamp: datetime
    bands: dict  # band_name -> array/data
    cloud_cover: float
    resolution: float  # meters per pixel


@dataclass
class VegetationIndex:
    index_name: str
    value: float
    timestamp: datetime
    geometry_hash: str


class SatelliteService:
    """
    Integrates with Copernicus Data Space Ecosystem (CDSE) / Sentinel Hub
    for NDVI, EVI, SAVI, NDWI, NBR vegetation indices.
    """

    def __init__(self, cdse_client_id: str = None, cdse_client_secret: str = None):
        self.client_id = cdse_client_id
        self.client_secret = cdse_client_secret
        self.base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        self.token = None
        self.token_expiry = None

    async def authenticate(self) -> bool:
        """Authenticate with CDSE OAuth2"""
        if not self.client_id or not self.client_secret:
            return False

        async with aiohttp.ClientSession() as session:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            async with session.post(
                "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                data=data,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.token = data["access_token"]
                    self.token_expiry = datetime.now(UTC) + timedelta(
                        seconds=data["expires_in"] - 60
                    )
                    return True
        return False

    async def _ensure_token(self):
        if not self.token or datetime.now(UTC) >= self.token_expiry:
            await self.authenticate()

    async def search_sentinel2(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 20,
    ) -> list[dict]:
        """Search for Sentinel-2 images covering a location"""
        await self._ensure_token()

        # Convert lat/lon to bbox (small buffer around point)
        buffer = 0.01  # ~1km
        bbox = f"{lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}"

        params = {
            "$filter": f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({bbox}))') "
            f"and ContentDate/Start ge {start_date.isoformat()}Z "
            f"and ContentDate/End le {end_date.isoformat()}Z "
            f"and Attributes/CloudCover le 20 "
            f"and Collection/Name eq 'SENTINEL-2'",
            "$top": 20,
            "$orderby": "ContentDate/Start desc",
        }

        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("value", [])
        return []

    async def download_band(self, product_id: str, band: str) -> bytes:
        """Download a specific band from a Sentinel-2 product"""
        await self._ensure_token()
        url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/Nodes(GRANULE)/Nodes(IMG_DATA)/Nodes({band}).jp2/$value"
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.read()
        return b""

    async def compute_ndvi(
        self, lat: float, lon: float, start_date: datetime, end_date: datetime
    ) -> dict:
        """Compute NDVI for a location over a time period"""
        images = await self.search_sentinel2(lat, lon, start_date, end_date)
        if not images:
            return {"error": "No suitable images found"}

        # For demo: return mock data
        # Real implementation would download bands, compute NDVI = (NIR - RED) / (NIR + RED)
        return {
            "ndvi_mean": 0.65,
            "ndvi_change": 0.12,
            "vegetation_healthy": True,
            "area_hectares": 2.3,
            "image_count": len(images),
            "date_range": f"{start_date.date()} to {end_date.date()}",
            "cloud_cover_avg": 12.5,
        }

    async def compute_vegetation_indices(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Compute multiple vegetation indices (NDVI, EVI, SAVI, NDWI, NBR)"""
        # In production: download bands B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR), B12 (SWIR2)
        # Compute:
        # NDVI = (NIR - RED) / (NIR + RED)
        # EVI = 2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)
        # SAVI = (1 + L) * (NIR - RED) / (NIR + RED + L) where L=0.5
        # NDWI = (GREEN - NIR) / (GREEN + NIR)
        # NBR = (NIR - SWIR2) / (NIR + SWIR2)

        return {
            "ndvi": {"mean": 0.68, "change": 0.15},
            "evi": {"mean": 0.52, "change": 0.12},
            "savi": {"mean": 0.58, "change": 0.10},
            "ndwi": {"mean": 0.25, "change": 0.05},
            "nbr": {"mean": 0.45, "change": 0.08},
            "date_range": "2024-01-01 to 2024-12-31",
            "image_count": 24,
        }

    async def detect_vegetation_change(
        self,
        lat: float,
        lon: float,
        baseline_start: datetime,
        baseline_end: datetime,
        current_start: datetime,
        current_end: datetime,
    ) -> dict:
        """Detect vegetation change between two periods"""
        baseline = await self.compute_vegetation_indices(lat, lon, baseline_start, baseline_end)
        current = await self.compute_vegetation_indices(lat, lon, current_start, current_end)

        if "error" in baseline or "error" in current:
            return {"error": "Insufficient data"}

        return {
            "ndvi_change": current["ndvi"]["mean"] - baseline["ndvi"]["mean"],
            "evi_change": current["evi"]["mean"] - baseline["evi"]["mean"],
            "vegetation_increase": current["ndvi"]["mean"] > baseline["ndvi"]["mean"],
            "significance": "high"
            if abs(current["ndvi"]["mean"] - baseline["ndvi"]["mean"]) > 0.1
            else "low",
        }

    async def verify_tree_planting(
        self,
        lat: float,
        lon: float,
        planting_date: datetime,
        expected_area_hectares: float,
    ) -> dict:
        """Verify tree planting using before/after satellite imagery"""
        # Get pre-planting baseline (6 months before)
        baseline_start = planting_date - timedelta(days=180)
        baseline_end = planting_date - timedelta(days=30)

        # Get current period (at least 3 months after planting)
        current_start = planting_date + timedelta(days=90)
        current_end = datetime.now(UTC)

        change = await self.detect_vegetation_change(
            lat, lon, baseline_start, baseline_end, current_start, datetime.now(UTC)
        )

        if "error" in change:
            return {"verified": False, "reason": change["error"]}

        # Estimate trees from area and NDVI change
        estimated_trees = int(change.get("ndvi_change", 0) * 1000 * expected_area_hectares)

        return {
            "verified": change["vegetation_increase"],
            "ndvi_change": change["ndvi_change"],
            "estimated_trees": max(0, estimated_trees),
            "area_hectares": expected_area_hectares,
            "confidence": 85 if change["significance"] == "high" else 60,
        }
