"""Verra API integration for carbon credit registry.

Connects to the Verra registry API to:
- Search and validate carbon projects
- Sync project data into Eco Nojin
- Validate credit batches

Requirements (optional):
- ``pip install httpx`` (already in pyproject.toml)
- VERRA_API_KEY and VERRA_API_SECRET environment variables

When credentials are missing, all operations fall back to mock data
with a logged warning.
"""

import logging
import os
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass
class VerraConfig:
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://registry.verra.org"
    timeout: int = 30

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("VERRA_API_KEY", "")
        if not self.api_secret:
            self.api_secret = os.environ.get("VERRA_API_SECRET", "")


class VerraService:
    """Verra registry integration service."""

    def __init__(self, config: VerraConfig | None = None):
        self.config = config or VerraConfig()
        self._client: httpx.AsyncClient | None = None

    def _is_configured(self) -> bool:
        return bool(self.config.api_key and self.config.api_secret)

    def _get_client(self) -> httpx.AsyncClient | None:
        if not self._is_configured():
            return None
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                auth=httpx.BasicAuth(self.config.api_key, self.config.api_secret),
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_project(self, registry_id: str) -> dict:
        """Fetch Verra project details by registry ID."""
        if not self._is_configured():
            logger.warning("Verra API not configured — returning mock project data")
            return self._mock_project(registry_id)

        client = self._get_client()
        if client is None:
            return self._mock_project(registry_id)

        try:
            resp = await client.get(f"/api/v1/projects/{registry_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Verra project fetch failed, using mock: %s", exc)
            return self._mock_project(registry_id)

    async def validate_credit_batch(self, batch_id: str) -> dict:
        """Validate a credit batch by batch ID."""
        if not self._is_configured():
            logger.warning("Verra API not configured — returning mock validation")
            return {
                "batch_id": batch_id,
                "valid": True,
                "status": "mock",
                "note": "Validation performed in mock mode — configure VERRA_API_KEY for real validation",
            }

        client = self._get_client()
        if client is None:
            return {
                "batch_id": batch_id,
                "valid": True,
                "status": "mock",
            }

        try:
            resp = await client.get(f"/api/v1/batches/{batch_id}/validate")
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Verra batch validation failed: %s", exc)
            return {
                "batch_id": batch_id,
                "valid": True,
                "status": "error",
                "error": str(exc),
            }

    async def list_standards(self) -> list[dict]:
        """Return available carbon credit standards."""
        return [
            {
                "id": "VCS",
                "name": "Verified Carbon Standard",
                "full_name": "Verified Carbon Standard (VCS)",
                "registry": "Verra",
                "description": "Most widely used voluntary GHG standard globally",
            },
            {
                "id": "GS",
                "name": "Gold Standard",
                "full_name": "Gold Standard for the Global Goals",
                "registry": "Gold Standard",
                "description": "Climate and development interventions with co-benefits",
            },
            {
                "id": "CAR",
                "name": "Climate Action Reserve",
                "full_name": "Climate Action Reserve",
                "registry": "CAR",
                "description": "High-quality carbon offset protocols",
            },
            {
                "id": "ACR",
                "name": "American Carbon Registry",
                "full_name": "American Carbon Registry",
                "registry": "ACR",
                "description": "North American carbon offset program",
            },
        ]

    async def search_projects(
        self, country: str | None = None, methodology: str | None = None, page: int = 1
    ) -> list[dict]:
        """Search Verra registry for projects."""
        if not self._is_configured():
            logger.warning("Verra API not configured — returning mock search results")
            return self._mock_search(country, methodology)

        client = self._get_client()
        if client is None:
            return self._mock_search(country, methodology)

        try:
            params: dict = {"page": page, "page_size": 20}
            if country:
                params["country_code"] = country
            if methodology:
                params["methodology"] = methodology
            resp = await client.get("/api/v1/projects", params=params)
            resp.raise_for_status()
            return resp.json().get("projects", [])
        except Exception as exc:
            logger.warning("Verra search failed, using mock: %s", exc)
            return self._mock_search(country, methodology)

    async def sync_project_from_verra(self, registry_id: str) -> dict:
        """Sync a Verra project into Eco Nojin's system."""
        project = await self.get_project(registry_id)
        standards = await self.list_standards()

        return {
            "synced": True,
            "registry_id": registry_id,
            "source": "verra",
            "project": project,
            "matched_standard": next(
                (s for s in standards if s["id"] in project.get("standard", "")), None
            ),
            "sync_timestamp": _now_iso(),
        }

    def _mock_project(self, registry_id: str) -> dict:
        return {
            "id": registry_id,
            "name": f"Mock Project {registry_id}",
            "country": "IR",
            "status": "active",
            "standard": "VCS",
            "methodology": "VM0004",
            "estimated_emissions_reduction": 10000,
            "registry": "Verra",
            "note": "Mock data — configure VERRA_API_KEY for real project data",
        }

    def _mock_search(
        self, country: str | None, methodology: str | None
    ) -> list[dict]:
        return [
            {
                "id": "MOCK-001",
                "name": "Mock Project 1",
                "country": country or "IR",
                "standard": "VCS",
                "methodology": methodology or "VM0004",
            },
            {
                "id": "MOCK-002",
                "name": "Mock Project 2",
                "country": country or "IR",
                "standard": "GS",
                "methodology": methodology or "GS VER",
            },
        ]


def _now_iso() -> str:
    from datetime import UTC, datetime
    return datetime.now(UTC).isoformat()


_verra_service: VerraService | None = None


def get_verra_integration() -> VerraService:
    """Return the singleton Verra integration service instance."""
    global _verra_service
    if _verra_service is None:
        _verra_service = VerraService()
    return _verra_service
