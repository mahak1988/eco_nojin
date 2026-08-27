"""Zenodo DOI integration (Phase 9, star 9).

Honest client: without ZENODO_TOKEN the platform reports
``status="not_configured"`` and never fakes a DOI. With a token it uses the
official Zenodo API (depositions) to publish a dataset record and returns the
DOI. Publishing is an explicit, user-confirmed action (write path).
"""

from __future__ import annotations

import os
from typing import Any

ZENODO_API = "https://zenodo.org/api"
SANDBOX_API = "https://sandbox.zenodo.org/api"


class ZenodoClient:
    """Minimal Zenodo deposition client (metadata-only by default)."""

    def __init__(self, token: str | None = None, sandbox: bool = False) -> None:
        self.token = token or os.getenv("ZENODO_TOKEN", "")
        self.base = SANDBOX_API if (sandbox or os.getenv("ZENODO_SANDBOX") == "1") else ZENODO_API

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def status(self) -> dict[str, Any]:
        """Honest capability status."""
        if not self.configured:
            return {
                "configured": False,
                "status": "not_configured",
                "message": "ZENODO_TOKEN تنظیم نشده است؛ DOI واقعی صادر نمی‌شود.",
                "endpoint": self.base,
            }
        return {
            "configured": True,
            "status": "ready",
            "endpoint": self.base,
            "sandbox": self.base == SANDBOX_API,
        }

    def create_deposition(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Create an empty deposition. Raises ZenodoError on failure."""
        import httpx

        resp = httpx.post(f"{self.base}/deposit/depositions", headers=self._headers(), json=metadata, timeout=30)
        if resp.status_code not in (200, 201):
            raise ZenodoError(f"Zenodo API {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def publish(self, deposition_id: str) -> dict[str, Any]:
        """Publish a deposition (irreversible in Zenodo)."""
        import httpx

        resp = httpx.post(
            f"{self.base}/deposit/depositions/{deposition_id}/actions/publish",
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code not in (200, 202):
            raise ZenodoError(f"Zenodo publish {resp.status_code}: {resp.text[:200]}")
        return resp.json()


class ZenodoError(RuntimeError):
    """Raised when the Zenodo API rejects a request."""


def dataset_zenodo_metadata(slug: str, title: str, description: str, creators: list[str]) -> dict[str, Any]:
    """Build Zenodo metadata payload from dataset fields."""
    return {
        "metadata": {
            "title": title,
            "description": description,
            "upload_type": "dataset",
            "creators": [{"name": c} for c in creators],
            "keywords": ["climate-smart agriculture", "NDVI", "soil", "water", "carbon", "Iran"],
            "license": "cc-by-4.0",
            "access_right": "open",
            "prereserve_doi": True,
        },
        "slug": slug,
    }


def default_zenodo_client() -> ZenodoClient:
    """Client configured from environment (ZENODO_TOKEN / ZENODO_SANDBOX)."""
    return ZenodoClient()
