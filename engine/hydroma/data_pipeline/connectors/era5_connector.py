"""ERA5 reanalysis via the Copernicus Climate Data Store (CDS) retrieve API.

Source
------
* API root (verified live, answers HTTP 202 "Welcome to the Climate Data
  Store API root endpoint"): ``https://cds.climate.copernicus.eu/api``
* API how-to: https://cds.climate.copernicus.eu/api-how-to

Credentials
-----------
The CDS key is the ``<UID>:<API-KEY>`` string issued by the CDS profile
page. It is read from, in order:

1. the ``CDS_KEY`` environment variable,
2. the ``CDSAPI_KEY`` environment variable (the variable the official
   ``cdsapi`` client reads),
3. the ``~/.cdsapirc`` file (override its location with ``CDSAPI_RC``),
   which holds ``key: <UID>:<API-KEY>`` and optionally
   ``url: https://cds.climate.copernicus.eu/api``.

With no key from any of those sources, every method that needs one raises
``ConnectorUnavailable`` naming all three places to look.

Protocol
--------
This connector implements the CDS REST protocol directly with ``requests``
(the same sequence the official ``cdsapi`` client performs, so no CDS
licence terms are bypassed):

1. ``POST {api}/resources/{dataset}`` with the request document as the JSON
   body and HTTP Basic auth — returns a task reply carrying ``state`` and
   ``request_id``.
2. ``GET {api}/tasks/{request_id}`` until ``state`` is ``completed`` (or a
   terminal failure state, which is reported as an error).
3. Stream the reply's ``location`` URL to the cache file.

Note that ERA5 use requires accepting the CDS licence terms for the
dataset; the API reports unmet terms in the task reply, and that reply is
surfaced verbatim rather than being papered over.
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

#: Default CDS API root (the URL ``.cdsapirc`` documents).
CDS_API_URL = "https://cds.climate.copernicus.eu/api"

#: Environment variables consulted for the CDS key, in order.
KEY_ENV_VARS = ("CDS_KEY", "CDSAPI_KEY")
#: Default location of the cdsapi credentials file.
CDSAPIRC_PATH = Path.home() / ".cdsapirc"

#: Datasets this connector is documented against.
SUPPORTED_DATASETS: dict[str, str] = {
    "reanalysis-era5-land": "ERA5-Land (9 km, hourly, 1950-present)",
    "reanalysis-era5-single-levels": "ERA5 (31 km, hourly, 1940-present)",
}

#: Variables offered as the default when the caller names none.
DEFAULT_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "total_precipitation",
    "surface_solar_radiation_downwards",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "surface_pressure",
]

#: Six-hourly sampling keeps a request small while still resolving the
#: diurnal cycle the ET models need.
DEFAULT_TIMES = ["00:00", "06:00", "12:00", "18:00"]

#: Terminal task states that mean "this request will never complete".
_FAILED_STATES = ("failed", "aborted", "rejected")

#: NetCDF headers: classic (``CDF\x01``/``CDF\x02``) and NetCDF-4 (HDF5).
_NETCDF_CLASSIC_MAGICS = (b"CDF\x01", b"CDF\x02")
_NETCDF4_MAGIC = b"\x89HDF\r\n\x1a\n"


class ERA5Connector(DataConnector):
    """ERA5 / ERA5-Land subsets from the Climate Data Store.

    Registered in ``engine.hydroma.data_pipeline.pipeline`` under the
    source id ``era5``.

    Args:
        cache_dir: Where retrieved NetCDF files are written.
        api_key: ``<UID>:<API-KEY>`` string. Defaults to the ``CDS_KEY`` /
            ``CDSAPI_KEY`` environment variables, then ``~/.cdsapirc``.
        api_url: CDS API root. Defaults to the ``CDS_URL`` / ``CDSAPI_URL``
            environment variables, then ``~/.cdsapirc``, then
            ``CDS_API_URL``.
        timeout: Per-request timeout in seconds.
        poll_interval: Seconds between task-status polls.
        max_wait: Maximum seconds to wait for a task to complete.
        max_retries: Retries for transient ``requests`` failures.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache/era5"),
        api_key: str | None = None,
        api_url: str | None = None,
        timeout: float = 60.0,
        poll_interval: float = 5.0,
        max_wait: float = 1800.0,
        max_retries: int = 2,
    ):
        self.source = DataSource(
            source_id="era5",
            name="ERA5 (Copernicus Climate Data Store)",
            description=(
                "ERA5-Land / ERA5 reanalysis subsets via the CDS retrieve "
                "API. Requires a CDS key (CDS_KEY env var or ~/.cdsapirc)."
            ),
            base_url=CDS_API_URL,
            auth_type="api_key",
            format="netcdf",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._api_key = api_key
        self._api_url = api_url
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_wait = max_wait
        self.max_retries = max_retries

    # ── credentials ──────────────────────────────────────────────

    @staticmethod
    def _read_cdsapirc(path: Path) -> dict[str, str]:
        """Read ``key:``/``url:`` lines from a ``.cdsapirc`` file."""
        if not path.is_file():
            return {}
        config: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            name, _, value = line.partition(":")
            if name.strip() in ("url", "key"):
                config[name.strip()] = value.strip()
        return config

    def _credentials(self) -> tuple[str, str]:
        """Return ``(api_url, key)`` or raise ``ConnectorUnavailable``.

        Resolution order — environment ``CDS_KEY`` (documented for this
        deployment), environment ``CDSAPI_KEY``, then the ``.cdsapirc``
        file the official client uses. The URL follows the same order with
        ``CDS_URL`` / ``CDSAPI_URL``.
        """
        rc_path = Path(os.environ.get("CDSAPI_RC", str(CDSAPIRC_PATH)))
        rc = self._read_cdsapirc(rc_path)

        key = self._api_key
        if not key:
            for env_var in KEY_ENV_VARS:
                key = os.environ.get(env_var, "")
                if key:
                    break
        if not key:
            key = rc.get("key", "")

        url = self._api_url
        if not url:
            for env_var in ("CDS_URL", "CDSAPI_URL"):
                url = os.environ.get(env_var, "")
                if url:
                    break
        if not url:
            url = rc.get("url", "")
        if not url:
            url = CDS_API_URL

        if not key:
            raise ConnectorUnavailable(
                "CDS (ERA5) requires an API key in the form '<UID>:<API-KEY>'. "
                "None was found in the CDS_KEY or CDSAPI_KEY environment "
                f"variables or in {rc_path}. Get the key from "
                "https://cds.climate.copernicus.eu/profile and either export "
                "CDS_KEY or write ~/.cdsapirc with 'key: <UID>:<API-KEY>'."
            )
        if key.count(":") != 1:
            raise ConnectorUnavailable(
                f"CDS key is malformed: expected exactly one ':' separating "
                f"UID and API key (the format is '<UID>:<API-KEY>'); got a "
                f"value with {key.count(':')} colon(s)."
            )
        return url.rstrip("/"), key

    def _auth(self) -> tuple[str, str]:
        """HTTP Basic credentials for the CDS API."""
        _, key = self._credentials()
        uid, _, api_key = key.partition(":")
        return uid, api_key

    # ── request building ─────────────────────────────────────────

    @staticmethod
    def _dates_between(start_date: str, end_date: str) -> list[str]:
        """Inclusive list of ``YYYY-MM-DD`` strings between two dates."""
        from datetime import date, timedelta

        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if end < start:
            raise ValueError(f"end_date {end_date} is before start_date {start_date}")
        days = (end - start).days
        return [(start + timedelta(days=i)).isoformat() for i in range(days + 1)]

    def build_request(self, query: dict[str, Any]) -> dict[str, Any]:
        """Build the CDS request document (pure, network-free).

        query: {
            "dataset": "reanalysis-era5-land",
            "variables": ["2m_temperature", ...],
            "bbox": [lon_min, lat_min, lon_max, lat_max],
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "time": ["00:00", ...],          # optional
            "download_format": "unarchived", # or "zip"
            "extra": {...},                  # merged into the request
        }

        The CDS API takes the AOI as ``area = [North, West, South, East]``
        (WGS 84 degrees), which is the reverse order of the ``bbox`` this
        pipeline uses everywhere else, so the conversion happens here once.
        """
        dataset = query.get("dataset", "reanalysis-era5-land")
        variables = query.get("variables", DEFAULT_VARIABLES)
        bbox = query.get("bbox", [-180.0, -90.0, 180.0, 90.0])
        start_date = query.get("start_date", "2020-01-01")
        end_date = query.get("end_date", "2020-12-31")
        times = query.get("time", DEFAULT_TIMES)

        if len(bbox) != 4:
            raise ValueError(f"bbox must be [lon_min, lat_min, lon_max, lat_max]; got {bbox!r}")
        lon_min, lat_min, lon_max, lat_max = (float(v) for v in bbox)

        days = self._dates_between(start_date, end_date)
        request: dict[str, Any] = {
            "variable": list(variables),
            "year": sorted({d[:4] for d in days}),
            "month": sorted({d[5:7] for d in days}),
            "day": sorted({d[8:10] for d in days}),
            "time": list(times),
            "area": [lat_max, lon_min, lat_min, lon_max],
            "data_format": "netcdf",
            "download_format": query.get("download_format", "unarchived"),
        }
        request.update(query.get("extra", {}) or {})
        self._dataset = dataset
        return request

    # ── CDS REST protocol ────────────────────────────────────────

    def _retry(self, fn):
        """Wrap *fn* with the shared retry helper (network errors only)."""
        import requests

        from engine.resilience import with_retry

        return with_retry(
            max_retries=self.max_retries,
            backoff_factor=0.5,
            exceptions=(requests.RequestException,),
        )(fn)

    def _submit_task(self, dataset: str, request: dict[str, Any]) -> dict[str, Any]:
        """POST the request and return the task reply."""
        import requests

        url, _ = self._credentials()

        def _post() -> Any:
            response = requests.post(
                f"{url}/resources/{dataset}",
                json=request,
                auth=self._auth(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        try:
            reply: dict[str, Any] = self._retry(_post)()
            return reply
        except Exception as exc:
            raise ConnectorUnavailable(
                f"CDS task submission failed for dataset {dataset!r} "
                f"({type(exc).__name__}: {exc}). The API may be unreachable, "
                f"the key may be wrong, or the licence terms for the dataset "
                f"may not have been accepted."
            ) from exc

    def _wait_for_completion(self, request_id: str) -> dict[str, Any]:
        """Poll the task until it completes; return the final reply."""
        import time

        import requests

        url, _ = self._credentials()
        task_url = f"{url}/tasks/{request_id}"
        deadline = datetime.now(UTC).timestamp() + self.max_wait

        while True:
            response = self._retry(
                lambda: requests.get(task_url, auth=self._auth(), timeout=self.timeout)
            )()
            reply: dict[str, Any] = response.json()
            state = str(reply.get("state", "")).lower()

            if state in _FAILED_STATES or "error" in reply:
                detail = reply.get("error") or reply.get("message") or reply
                raise ConnectorUnavailable(
                    f"CDS task {request_id} ended in state {state!r}: {detail}"
                )
            if state == "completed":
                return reply
            if datetime.now(UTC).timestamp() >= deadline:
                raise ConnectorUnavailable(
                    f"CDS task {request_id} did not complete within "
                    f"{self.max_wait:.0f}s (last state: {state!r}). CDS queues "
                    f"long requests; raise max_wait or retry later."
                )
            logger.info("CDS task %s is %s; sleeping %.0fs", request_id, state, self.poll_interval)
            time.sleep(self.poll_interval)

    def _download(self, location: str, target: Path) -> Path:
        """Stream the task result to *target*."""
        import requests

        def _get() -> Any:
            response = requests.get(
                location,
                auth=self._auth(),
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
                f"CDS result download failed for {location} "
                f"({type(exc).__name__}: {exc})."
            ) from exc
        return target

    # ── DataConnector API ────────────────────────────────────────

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Retrieve an ERA5 subset and return it as one asset.

        query keys are documented on :meth:`build_request`.

        Raises:
            ConnectorUnavailable: no CDS key, malformed key, failed task
                submission, task failure (including unaccepted licence
                terms), or download failure.
        """
        request = self.build_request(query)
        dataset = self._dataset
        reply = self._submit_task(dataset, request)

        request_id = reply.get("request_id")
        if not request_id:
            raise ConnectorUnavailable(
                f"CDS task reply for {dataset!r} carried no request_id "
                f"(keys: {sorted(reply)})."
            )

        final = self._wait_for_completion(request_id)
        location = final.get("location")
        if not location:
            raise ConnectorUnavailable(
                f"CDS task {request_id} completed without a download location "
                f"(reply keys: {sorted(final)})."
            )

        asset_id = (
            f"era5_{dataset}_{query.get('start_date', '')}_{query.get('end_date', '')}_"
            f"{hashlib.md5(str(request).encode()).hexdigest()[:8]}"
        )
        file_path = self.cache_dir / f"{asset_id}.nc"
        self._download(location, file_path)

        return [
            DataAsset(
                asset_id=asset_id,
                source_id=self.source.source_id,
                name=f"ERA5 {dataset} {query.get('start_date', '')} to {query.get('end_date', '')}",
                description=(
                    f"CDS retrieve subset of {dataset} for bbox "
                    f"{query.get('bbox')} ({', '.join(request['variable'])})"
                ),
                file_path=file_path,
                format="netcdf",
                size_bytes=file_path.stat().st_size,
                checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                metadata={
                    "dataset": dataset,
                    "variables": request["variable"],
                    "bbox": query.get("bbox"),
                    "area_n_w_s_e": request["area"],
                    "start_date": query.get("start_date"),
                    "end_date": query.get("end_date"),
                    "time": request["time"],
                    "request_id": request_id,
                    "content_length": final.get("content_length"),
                },
                provenance={
                    "source_url": location,
                    "cds_api_request": request,
                    "request_id": request_id,
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "citation": (
                        "Copernicus Climate Change Service (C3S) ERA5 / "
                        "ERA5-Land via the Climate Data Store"
                    ),
                },
            )
        ]

    def validate(self, asset: DataAsset) -> bool:
        """Validate a retrieved NetCDF file by its header magic bytes."""
        if not asset.file_path.exists() or asset.file_path.stat().st_size == 0:
            return False
        head = asset.file_path.read_bytes()[:8]
        return head[:4] in _NETCDF_CLASSIC_MAGICS or head.startswith(_NETCDF4_MAGIC)
