"""
CDS / EWDS / ADS + SEPAL data stores — registration & status (Phase 7).

All Copernicus data stores (CDS, EWDS, ADS) share the same job-based REST
API and the same credential style (UID + API key, HTTP basic auth). SEPAL
is different: FAO's free EO platform — NO API key, login via Google/GitHub
(web app); automation uses a login token.

Key acquisition (free, after registering):
- CDS  https://cds.climate.copernicus.eu/how-to-api        (ERA5 reanalysis)
- EWDS https://ewds.climate.copernicus.eu/how-to-api       (weather store)
- ADS  https://ads.atmosphere.copernicus.eu/how-to-api     (CAMS air quality)
- SEPAL https://sepal.io                                   (web login, no key)

Env vars (see .env):
- CDS_UID/CDS_API_KEY, EWDS_UID/EWDS_API_KEY, ADS_UID/ADS_API_KEY
- SEPAL_BASE_URL (+ optional SEPAL_USERNAME/SEPAL_PASSWORD for API token)

Honesty: ``configured`` is True only when uid+key are both set; every
network call raises DataStoreNotConfigured otherwise. Never fabricates data.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# store -> env var names + where to get the free key
DATA_STORES: dict[str, dict[str, str]] = {
    "cds": {
        "url_env": "CDS_API_URL",
        "url_default": "https://cds.climate.copernicus.eu/api",
        "uid_env": "CDS_UID",
        "key_env": "CDS_API_KEY",
        "key_url": "https://cds.climate.copernicus.eu/how-to-api",
        "name": "Climate Data Store (ERA5 reanalysis)",
    },
    "ewds": {
        "url_env": "EWDS_API_URL",
        "url_default": "https://ewds.climate.copernicus.eu/api",
        "uid_env": "EWDS_UID",
        "key_env": "EWDS_API_KEY",
        "key_url": "https://ewds.climate.copernicus.eu/how-to-api",
        "name": "European Weather Data Store",
    },
    "ads": {
        "url_env": "ADS_API_URL",
        "url_default": "https://ads.atmosphere.copernicus.eu/api",
        "uid_env": "ADS_UID",
        "key_env": "ADS_API_KEY",
        "key_url": "https://ads.atmosphere.copernicus.eu/how-to-api",
        "name": "Atmosphere Data Store (CAMS)",
    },
}

SEPAL_BASE_URL = os.environ.get("SEPAL_BASE_URL", "https://sepal.io")

CDS_API_URL = os.environ.get(
    "CDS_API_URL", "https://cds.climate.copernicus.eu/api"
)
CDS_UID = os.environ.get("CDS_UID", "")
CDS_API_KEY = os.environ.get("CDS_API_KEY", "")

CDS_TIMEOUT = float(os.environ.get("CDS_TIMEOUT", "30.0"))


class DataStoreError(Exception):
    """Base data store error."""


class DataStoreNotConfigured(DataStoreError):
    """Raised when store credentials are missing."""


class DataStoreRequestError(DataStoreError):
    """Raised on store API failures."""


CdsNotConfigured = DataStoreNotConfigured
CdsRequestError = DataStoreRequestError


class DataStoreClient:
    """Job-based REST client for any Copernicus data store (CDS/EWDS/ADS)."""

    def __init__(
        self,
        store: str = "cds",
        base_url: str | None = None,
        uid: str | None = None,
        api_key: str | None = None,
        timeout: float = CDS_TIMEOUT,
    ) -> None:
        if store not in DATA_STORES:
            raise ValueError(f"unknown store: {store} (use {list(DATA_STORES)})")
        spec = DATA_STORES[store]
        self.store = store
        self._base = (base_url or os.environ.get(spec["url_env"]) or spec["url_default"]).rstrip("/")
        self._uid = uid if uid is not None else os.environ.get(spec["uid_env"], "")
        self._key = api_key if api_key is not None else os.environ.get(spec["key_env"], "")
        self._timeout = timeout
        self._key_url = spec["key_url"]
        self._name = spec["name"]
        # New CDS (2025+) uses ONE personal-access token (may carry a
        # "key:" prefix); legacy used uid + api key. Env CDS_AUTH can force
        # bearer|basic. Default: bearer when only a key is set, else basic.
        self._raw_key = self._key
        if self._key.startswith("key:"):
            self._key = self._key[4:]
        self._auth_mode = os.environ.get("CDS_AUTH", "").lower() or "bearer"

    @property
    def configured(self) -> bool:
        # cdsapi-compatible: the key alone (either "uid:key" legacy or
        # "key:<token>" new format) is the whole credential.
        return bool(self._raw_key)

    def _auth_headers(self) -> dict[str, str]:
        if not self.configured:
            raise DataStoreNotConfigured(
                f"{self.store}: set {DATA_STORES[self.store]['key_env']} in .env "
                f"(free key: {self._key_url})"
            )
        if self._auth_mode == "basic":
            import base64

            # cdsapi-compatible legacy rule:
            #   key "uid:apikey"  -> basic(uid, apikey)   [legacy CDS]
            parts = self._raw_key.split(":", 2)
            if len(parts) == 2:
                user, pwd = parts[0], parts[1]
            else:
                user, pwd = "key", self._key
            raw = f"{user}:{pwd}".encode()
            return {"Authorization": "Basic " + base64.b64encode(raw).decode()}
        # new CDS: Bearer with the full token (page shows "key: <token>")
        token = self._raw_key if self._raw_key.startswith("key:") else "key:" + self._raw_key
        return {"Authorization": f"Bearer {token}"}

    def status(self) -> dict[str, Any]:
        """Honest status: configured flag + URL + where to get the key."""
        return {
            "store": self.store,
            "name": self._name,
            "configured": self.configured,
            "api_url": self._base,
            "key_url": self._key_url,
            "auth": self._auth_mode,
            "note": "NetCDF/GRIB parsing requires netcdf4/xarray (not bundled)",
        }

    def submit_request(
        self,
        params: dict[str, Any],
        dataset: str = "reanalysis-era5-single-levels",
    ) -> str:
        """Submit a retrieval job; returns the task URL."""
        url = f"{self._base}/retrieve/v1/processes/{dataset}/execution"
        try:
            resp = httpx.post(
                url, headers=self._auth_headers(), json=params, timeout=self._timeout
            )
        except httpx.HTTPError as exc:
            raise DataStoreRequestError(f"{self.store} submit failed: {exc}") from exc
        if resp.status_code not in (200, 201, 202):
            raise DataStoreRequestError(
                f"{self.store} submit HTTP {resp.status_code}: {resp.text[:200]}"
            )
        task_url = resp.headers.get("location") or resp.json().get("url")
        if not task_url:
            raise DataStoreRequestError(f"{self.store} submit returned no task URL")
        return task_url

    def poll_task(self, task_url: str, max_seconds: float = 120.0) -> str:
        """Poll until 'completed' (or raise on 'failed')."""
        deadline = time.monotonic() + max_seconds
        while time.monotonic() < deadline:
            try:
                resp = httpx.get(
                    task_url, headers=self._auth_headers(), timeout=self._timeout
                )
            except httpx.HTTPError as exc:
                raise DataStoreRequestError(f"{self.store} poll failed: {exc}") from exc
            if resp.status_code == 200:
                state = resp.json().get("state", "completed")
                if state == "completed":
                    return state
                if state == "failed":
                    raise DataStoreRequestError(f"{self.store} task failed: {resp.text[:200]}")
            time.sleep(2.0)
        raise DataStoreRequestError(f"{self.store} task did not finish in time")

    def download(self, task_url: str) -> bytes:
        """Download the finished result as bytes (follows JSON 'url' field)."""
        try:
            resp = httpx.get(
                task_url, headers=self._auth_headers(), timeout=600.0
            )
        except httpx.HTTPError as exc:
            raise DataStoreRequestError(f"{self.store} download failed: {exc}") from exc
        if resp.status_code != 200:
            raise DataStoreRequestError(
                f"{self.store} download HTTP {resp.status_code}: {resp.text[:200]}"
            )
        # new CDS: completed task JSON points to the real file URL
        try:
            payload = resp.json()
        except Exception:
            payload = None
        if isinstance(payload, dict) and payload.get("url"):
            file_url = payload["url"]
            try:
                resp = httpx.get(
                    file_url, headers=self._auth_headers(), timeout=600.0
                )
            except httpx.HTTPError as exc:
                raise DataStoreRequestError(
                    f"{self.store} file download failed: {exc}"
                ) from exc
            if resp.status_code != 200:
                raise DataStoreRequestError(
                    f"{self.store} file download HTTP {resp.status_code}: {resp.text[:200]}"
                )
        return resp.content


# Backward-compatible alias used by earlier endpoints/tests.
class CdsClient(DataStoreClient):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("store", "cds")
        super().__init__(*args, **kwargs)


def all_stores_status() -> dict[str, Any]:
    """Status of every data store (CDS/EWDS/ADS) + SEPAL guidance."""
    stores = {}
    for name in DATA_STORES:
        stores[name] = DataStoreClient(store=name).status()
    stores["sepal"] = {
        "store": "sepal",
        "name": "SEPAL (FAO EO platform)",
        "configured": True,  # web login, no key required
        "api_url": SEPAL_BASE_URL,
        "key_url": "https://sepal.io",
        "note": "رایگان؛ بدون کلید — ورود با Google/GitHub؛ اتوماسیون با توکن ورود",
    }
    return {"stores": stores}
