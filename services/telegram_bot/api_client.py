"""HTTP client for Eco Nojin Platform API."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import config

logger = logging.getLogger("econojin.bot.api")


class PlatformAPIClient:
    """Async client for platform API."""

    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.timeout = config.REQUEST_TIMEOUT

    async def analyze_land(
        self,
        name: str,
        latitude: float,
        longitude: float,
        area_ha: float,
    ) -> dict[str, Any] | None:
        """Call /api/v1/platform/analyze endpoint."""
        url = f"{self.base_url}/api/v1/platform/analyze"
        payload = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "area_ha": area_ha,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("API request timeout")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if API is healthy."""
        url = f"{self.base_url}/api/v1/platform/health"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def list_landscapes(self) -> dict[str, Any] | None:
        """List all landscapes."""
        url = f"{self.base_url}/api/v1/platform/landscapes"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"List landscapes failed: {e}")
            return None

    async def get_stats(self) -> dict[str, Any] | None:
        """Get platform statistics."""
        url = f"{self.base_url}/api/v1/platform/stats"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return None


# Singleton
api_client = PlatformAPIClient()
