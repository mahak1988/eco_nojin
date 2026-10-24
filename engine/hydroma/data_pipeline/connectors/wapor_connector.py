"""FAO WaPOR v3 connector — water productivity rasters (GISMGR 2.0 API).

Source
------
* API documentation (OpenAPI 3.1.1, verified live):
  ``https://data.apps.fao.org/gismgr/shared/docs/api-reference/``
* API root (from the spec's ``servers``, verified live):
  ``https://data.apps.fao.org/gismgr/api/v2``
* Workspaces: ``WAPOR-3`` (WaPOR version 3, current) and ``WAPOR-2``
  (version 2, Africa and Near East) — both verified to list mapsets and
  rasters anonymously.

Credentials — none
------------------
The current WaPOR v3 API is **open data and needs no API key or token**.
FAO's data-access page (updated 2025-08) states: "you do not need an API
key/token or any credentials … That used to be the case for WaPOR version
2." This connector therefore works anonymously. If a ``WAPOR_API_KEY``
environment variable (or constructor argument) *is* set, it is forwarded as
the ``X-GISMGR-API-KEY`` header documented by the API spec's
``signInWithApiKey`` operation — it is never required, and its absence is
not an error condition.

What was verified against the live service (2026-10-10)
-------------------------------------------------------
* ``GET /catalog/workspaces`` lists 97 workspaces including ``WAPOR-3`` and
  ``WAPOR-2``.
* ``GET /catalog/workspaces/WAPOR-3/mapsets?size=100`` lists 100 mapsets
  (cubes) with captions such as ``L1-AETI-D — Actual EvapoTranspiration and
  Interception (Global - Dekadal - 300m)``.
* ``GET /catalog/workspaces/WAPOR-3/mapsets/L2-AETI-D/rasters`` returns
  raster documents carrying ``downloadUrl`` (public Google Cloud Storage
  HTTPS), ``measureUnit``, ``scale``/``offset``, ``extent``, ``srs`` and a
  DEKAD dimension member with ``startDate``/``endDate``.
* ``filter=time:OVERLAPS:<start>:<end>`` selects rasters overlapping a
  period; ``sort=code:DESC`` orders newest first (both documented in the
  spec's ``filter``/``sort`` parameter descriptions and verified live).
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.pipeline import DataAsset, DataConnector, DataSource

logger = logging.getLogger(__name__)

#: GISMGR 2.0 API root (from the published OpenAPI spec, verified live).
API_URL = "https://data.apps.fao.org/gismgr/api/v2"

#: Optional API-key header name from the spec (``signInWithApiKey``).
API_KEY_ENV = "WAPOR_API_KEY"
API_KEY_HEADER = "X-GISMGR-API-KEY"

#: WaPOR workspaces.
WAPOR_V3 = "WAPOR-3"
WAPOR_V2 = "WAPOR-2"

#: Default cube: actual evapotranspiration and interception, global,
#: dekadal, 300 m — the WaPOR layer closest to a water-balance ET term.
DEFAULT_MAPSET = "L1-AETI-D"
DEFAULT_WORKSPACE = WAPOR_V3

#: Page size used when listing (the API caps ``size`` at 100).
MAX_PAGE_SIZE = 100

#: Cloud-Optimized GeoTIFF magic bytes accepted by :meth:`validate`.
_TIFF_MAGICS = (b"II*\x00", b"MM\x00*")


class WaPORConnector(DataConnector):
    """FAO WaPOR water-productivity rasters via the GISMGR 2.0 API.

    Registered in ``engine.hydroma.data_pipeline.pipeline`` under the
    source id ``wapor``. Anonymous access; ``WAPOR_API_KEY`` is optional.

    Args:
        cache_dir: Where downloaded rasters are written.
        workspace: WaPOR workspace (``WAPOR-3`` or ``WAPOR-2``).
        api_key: Optional API key, forwarded as ``X-GISMGR-API-KEY``.
            Defaults to the ``WAPOR_API_KEY`` environment variable.
        timeout: Per-request timeout in seconds.
        max_retries: Retries for transient ``requests`` failures.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache/wapor"),
        workspace: str = DEFAULT_WORKSPACE,
        api_key: str | None = None,
        timeout: float = 120.0,
        max_retries: int = 2,
    ):
        self.source = DataSource(
            source_id="wapor",
            name="FAO WaPOR v3",
            description=(
                "FAO Water Productivity Open-access portal rasters via the "
                "GISMGR 2.0 REST API. Open data: no API key required."
            ),
            base_url=API_URL,
            auth_type="none",
            format="geotiff",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.workspace = workspace
        self._api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    # ── request plumbing ─────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        """Request headers; adds the API key only when one is configured."""
        api_key = self._api_key or os.environ.get(API_KEY_ENV, "")
        if api_key:
            return {API_KEY_HEADER: api_key}
        return {}

    def _retry(self, fn):
        """Wrap *fn* with the shared retry helper (network errors only)."""
        import requests

        from engine.resilience import with_retry

        return with_retry(
            max_retries=self.max_retries,
            backoff_factor=0.5,
            exceptions=(requests.RequestException,),
        )(fn)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET one GISMGR endpoint and return its ``response`` payload.

        The API answers HTTP 200 with a body of the form
        ``{"status": 200, "message": "OK", "response": {...}}``. Two things
        are reported as errors rather than read as data: an HTTP error
        status (the FAO body then explains *what* was not found, e.g.
        ``item not found {workspaceCode=..., mapstoreCode=...}``), and a
        non-200 ``status`` inside an otherwise successful HTTP response.
        """

        def _do() -> Any:
            import requests

            response = requests.get(
                f"{API_URL}{path}",
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                # The FAO error body is the honest description; keep it.
                detail = response.text[:300]
                raise ConnectorUnavailable(
                    f"WaPOR GISMGR answered HTTP {response.status_code} for "
                    f"{path}: {detail}"
                )
            return response.json()

        try:
            body = self._retry(_do)()
        except ConnectorUnavailable:
            raise
        except Exception as exc:
            raise ConnectorUnavailable(
                f"WaPOR GISMGR request failed for {API_URL}{path} "
                f"({type(exc).__name__}: {exc}). The FAO API was unreachable "
                f"from this host."
            ) from exc

        status = body.get("status")
        if status != 200:
            raise ConnectorUnavailable(
                f"WaPOR GISMGR returned status {status!r} for {path}: "
                f"{body.get('message', body)}"
            )
        return body.get("response") or {}

    # ── catalogue discovery ──────────────────────────────────────

    @staticmethod
    def _mapsets_url(workspace: str) -> str:
        return f"/catalog/workspaces/{workspace}/mapsets"

    @staticmethod
    def _rasters_url(workspace: str, mapset: str) -> str:
        return f"/catalog/workspaces/{workspace}/mapsets/{mapset}/rasters"

    @staticmethod
    def _build_rasters_params(
        start_date: str | None,
        end_date: str | None,
        limit: int,
    ) -> dict[str, str]:
        """Build the rasters query parameters (pure, network-free).

        With dates, the documented ``time:OVERLAPS:<start>:<end>`` filter is
        applied; without them the newest rasters are returned first.
        """
        params: dict[str, str] = {
            "size": str(min(limit, MAX_PAGE_SIZE)),
            "sort": "code:DESC",
        }
        if start_date and end_date:
            params["filter"] = f"time:OVERLAPS:{start_date}:{end_date}"
        elif start_date:
            params["filter"] = f"time:OVERLAPS:{start_date}"
        return params

    def list_mapsets(self) -> list[dict[str, str]]:
        """List the workspace's mapsets (cubes) as ``code``/``caption`` pairs."""
        response = self._get(self._mapsets_url(self.workspace), {"size": MAX_PAGE_SIZE})
        return [
            {"code": item.get("code", ""), "caption": item.get("caption", "")}
            for item in response.get("items", [])
        ]

    def list_rasters(
        self,
        mapset: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List rasters for one mapset, newest first."""
        mapset = mapset or DEFAULT_MAPSET
        params = self._build_rasters_params(start_date, end_date, limit)
        response = self._get(self._rasters_url(self.workspace, mapset), params)
        return list(response.get("items", []))

    @staticmethod
    def _raster_period(raster: dict[str, Any]) -> tuple[str | None, str | None]:
        """Extract ``(start_date, end_date)`` from a raster's dimensions."""
        for dimension in raster.get("dimensions", []):
            member = dimension.get("member") or {}
            if member.get("startDate"):
                return member.get("startDate"), member.get("endDate")
        return None, None

    # ── DataConnector API ────────────────────────────────────────

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Download WaPOR rasters for one cube and period.

        query: {
            "workspace": "WAPOR-3",           # or "WAPOR-2"
            "mapset": "L1-AETI-D",            # cube code
            "start_date": "YYYY-MM-DD",       # optional period filter
            "end_date": "YYYY-MM-DD",
            "limit": 10,                      # rasters listed per request
            "max_downloads": 1,               # cap on files fetched
        }

        Raises:
            ConnectorUnavailable: the FAO API is unreachable, the workspace
                or mapset does not exist, or a raster download fails.
                Individual rasters that fail are logged and skipped.
        """
        workspace = query.get("workspace", self.workspace)
        mapset = query.get("mapset", DEFAULT_MAPSET)
        start_date = query.get("start_date")
        end_date = query.get("end_date")
        limit = query.get("limit", 10)
        max_downloads = query.get("max_downloads", 1)

        rasters = self.list_rasters(mapset, start_date, end_date, limit)
        if not rasters:
            logger.warning(
                "WaPOR workspace %s mapset %s has no rasters for %s..%s",
                workspace,
                mapset,
                start_date,
                end_date,
            )
            return []

        assets: list[DataAsset] = []
        for raster in rasters[:max_downloads]:
            code = raster.get("code", "")
            download_url = raster.get("downloadUrl")
            if not download_url:
                logger.warning("WaPOR raster %s carries no downloadUrl; skipping", code)
                continue

            asset_id = f"wapor_{code}"
            file_path = self.cache_dir / f"{asset_id}.tif"
            try:
                self._download(download_url, file_path)
            except ConnectorUnavailable as exc:
                logger.warning("WaPOR raster %s skipped: %s", code, exc)
                continue

            period_start, period_end = self._raster_period(raster)
            extent = raster.get("extent") or {}
            assets.append(
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"WaPOR {mapset} {period_start or code}",
                    description=(
                        f"{raster.get('measureCaption', mapset)} "
                        f"({raster.get('measureUnit', '')}) — {code}"
                    ),
                    file_path=file_path,
                    format="geotiff",
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "workspace": workspace,
                        "mapset": mapset,
                        "raster_code": code,
                        "period_start": period_start,
                        "period_end": period_end,
                        "measure": raster.get("measureCaption"),
                        "unit": raster.get("measureUnit"),
                        "scale": raster.get("scale"),
                        "offset": raster.get("offset"),
                        "extent_wgs84": extent.get("wgs84"),
                        "crs_epsg": (raster.get("srs") or {}).get("epsg"),
                        "width": raster.get("width"),
                        "height": raster.get("height"),
                        "no_data_value": raster.get("noDataValue"),
                    },
                    provenance={
                        "source_url": download_url,
                        "gismgr_api": f"{API_URL}{self._rasters_url(workspace, mapset)}",
                        "fetched_at": datetime.now(UTC).isoformat(),
                        "citation": (
                            "FAO WaPOR (Water Productivity through Open-access "
                            "of Remotely sensed derived data), GISMGR 2.0 API"
                        ),
                    },
                )
            )

        return assets

    def _download(self, url: str, target: Path) -> Path:
        """Stream one raster to *target* and return its path."""
        import requests

        def _get() -> Any:
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout * 5,
                stream=True,
            )
            response.raise_for_status()
            return response

        try:
            with self._retry(_get)() as response:
                with target.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1 << 20):
                        handle.write(chunk)
        except Exception as exc:
            target.unlink(missing_ok=True)
            raise ConnectorUnavailable(
                f"WaPOR raster download failed for {url} "
                f"({type(exc).__name__}: {exc})."
            ) from exc
        return target

    def validate(self, asset: DataAsset) -> bool:
        """Validate a downloaded raster by its GeoTIFF magic bytes."""
        if not asset.file_path.exists() or asset.file_path.stat().st_size == 0:
            return False
        return asset.file_path.read_bytes()[:4] in _TIFF_MAGICS
