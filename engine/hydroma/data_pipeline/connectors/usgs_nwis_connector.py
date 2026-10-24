"""USGS NWIS connector — real instantaneous and daily streamflow observations.

Source
------
* USGS National Water Information System (NWIS) Instantaneous/Daily Values
  web service: ``https://waterservices.usgs.gov/nwis/iv`` and
  ``https://waterservices.usgs.gov/nwis/dv``
* NWIS Site web service (station metadata):
  ``https://waterservices.usgs.gov/nwis/site``

Credentials — none
-----------------
NWIS is US federal open data: no API key, token or registration is
requested or supplied by this connector.

What was verified against the live service (2026-10-10)
------------------------------------------------------
* ``GET /nwis/iv/?format=json&sites=09380000&startDT=…&endDT=…`` and
  ``GET /nwis/dv/?…`` both answer HTTP 200 with
  ``{"value": {"timeSeries": [ … ]}}``. Each series carries
  ``sourceInfo`` (``siteName``, ``siteCode``, ``geoLocation.geogLocation``
  with ``latitude``/``longitude``/``srs``, ``siteProperty``), ``variable``
  (``variableCode``, ``variableName``, ``variableDescription``, and the
  unit at ``variable.unit.unitCode``) and ``values[].value[]`` entries with
  ``value``, ``dateTime`` and ``qualifiers``.
* Discharge is parameter code ``00060`` ("Discharge, cubic feet per
  second") reported as ``unitCode: "ft3/s"``; the daily-mean statistic is
  code ``00003``.
* **The site service's JSON output is currently broken**: both
  ``?format=json&sites=09380000&siteOutput=expanded`` and
  ``?format=json&stateCd=az&siteType=ST`` answer HTTP 400 with
  "unrecognized output format for query=basic, server=[caas01]". The
  documented tab-delimited RDB output of the same request works, so station
  metadata is read from ``format=rdb&siteOutput=expanded`` — whose column
  names are taken from the service's own header row, never assumed.
* ``statCd`` belongs to the daily service only; the instantaneous service
  has no statistic to select.

The date-time strings arrive as the site's local time (the service reports
the zone in ``sourceInfo.timeZoneInfo``); they are carried through verbatim
with no timezone conversion or resampling applied here.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.pipeline import DataAsset, DataConnector, DataSource

logger = logging.getLogger(__name__)

#: NWIS web-service root (verified live).
NWIS_BASE_URL = "https://waterservices.usgs.gov/nwis"

#: Service path: instantaneous values (``iv``) or daily values (``dv``).
SERIES_SERVICE_PATH = "{service}"

#: Site service path for station metadata.
SITE_SERVICE_PATH = "site"

#: NWIS parameter code for river discharge, cubic feet per second.
DISCHARGE_PARAMETER_CODE = "00060"

#: NWIS statistic code for the daily mean.
DAILY_MEAN_STATISTIC_CODE = "00003"

#: Services this connector implements, and which of them accept a statistic.
SUPPORTED_SERVICES = ("iv", "dv")

#: Output format requested for the time-series service.
JSON_FORMAT = "json"

#: Output format requested for the site service, because its JSON output is
#: currently rejected (see module docstring).
RDB_FORMAT = "rdb"

#: Rows of the site-file response whose agency code is not this value are
#: the RDB column-format row (``5s 15s …``) or a separator, not a station.
_AGENCY_CODE = "USGS"

_ASSET_FORMAT = "csv"
_ASSET_SUFFIX = ".csv"


class USGSNWISConnector(DataConnector):
    """Instantaneous/daily USGS discharge observations and site metadata.

    Registered in ``engine.hydroma.data_pipeline.pipeline`` under the source
    id ``usgs_nwis``. US-only coverage, no credentials. When NWIS cannot be
    reached, answers with an error status, or returns a body without a
    ``timeSeries`` list, :class:`ConnectorUnavailable` is raised naming NWIS
    — never a fabricated rating curve.

    Args:
        cache_dir: Where fetched site tables are written.
        base_url: NWIS web-service root (documented default, verified live).
        timeout: Per-request timeout in seconds.
        max_retries: Retries for transient ``requests`` failures.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache/usgs_nwis"),
        base_url: str = NWIS_BASE_URL,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        self.source = DataSource(
            source_id="usgs_nwis",
            name="USGS NWIS Instantaneous / Daily Values",
            description=(
                "USGS National Water Information System instantaneous and "
                "daily values plus site metadata. US coverage, open data, "
                "no API key."
            ),
            base_url=base_url.rstrip("/"),
            auth_type="none",
            format=_ASSET_FORMAT,
        )
        self.base_url = base_url.rstrip("/")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_retries = max_retries

    # ── request plumbing ──────────────────────────────────────────

    def _retry(self, fn):
        """Wrap *fn* with the shared retry helper (network errors only)."""
        import requests

        from engine.resilience import with_retry

        return with_retry(
            max_retries=self.max_retries,
            backoff_factor=0.5,
            exceptions=(requests.RequestException,),
        )(fn)

    def _get_response(self, path: str, params: dict[str, Any]):
        """GET one NWIS endpoint, raising :class:`ConnectorUnavailable`.

        NWIS answers some refusals with an HTTP 400 body that is HTML rather
        than JSON; the status and the body's first characters are reported so
        the operator sees what the service actually said.
        """

        def _do():
            import requests

            return requests.get(
                f"{self.base_url}/{path}",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "HyDroMA data pipeline (USGS open data)"},
            )

        try:
            response = self._retry(_do)()
        except Exception as exc:
            raise ConnectorUnavailable(
                f"USGS NWIS was unreachable for {self.base_url}/{path} "
                f"({type(exc).__name__}: {exc}). No discharge was "
                f"substituted for it."
            ) from exc

        status = getattr(response, "status_code", None)
        if status != 200:
            detail = str(getattr(response, "text", ""))[:300].replace("\n", " ")
            raise ConnectorUnavailable(
                f"USGS NWIS answered HTTP {status} for "
                f"{self.base_url}/{path} with parameters {params}: {detail}"
            )
        return response

    def _get_json(self, path: str, params: dict[str, Any]) -> Any:
        response = self._get_response(path, params)
        try:
            return response.json()
        except ValueError as exc:
            raise ConnectorUnavailable(
                f"USGS NWIS returned a body that is not JSON for "
                f"{self.base_url}/{path}: {exc}"
            ) from exc

    # ── request builders (pure) ───────────────────────────────────

    @staticmethod
    def _sites_param(sites: Any) -> str:
        """Normalise the ``sites`` query key to a comma-separated string."""
        if sites is None:
            return ""
        if isinstance(sites, str):
            cells = sites.split(",")
        elif isinstance(sites, (list, tuple, set)):
            cells = list(sites)
        else:
            cells = [sites]
        return ",".join(str(cell).strip() for cell in cells if str(cell).strip())

    @classmethod
    def build_series_params(cls, query: dict[str, Any]) -> dict[str, Any]:
        """Build the NWIS ``iv``/``dv`` query parameters (pure, network-free).

        query: {
            "sites": ["09380000"] | "09380000,01646500",
            "service": "iv" | "dv",
            "parameterCd": "00060",
            "statCd": "00003",       # daily service only
            "startDT": "YYYY-MM-DD",
            "endDT": "YYYY-MM-DD",
        }
        """
        service = str(query.get("service", "dv")).lower()
        if service not in SUPPORTED_SERVICES:
            raise ConnectorUnavailable(
                f"USGS NWIS exposes {SUPPORTED_SERVICES}; {service!r} is not "
                "one of them."
            )
        params: dict[str, Any] = {
            "format": JSON_FORMAT,
            "sites": cls._sites_param(query.get("sites")),
            "parameterCd": str(query.get("parameterCd", DISCHARGE_PARAMETER_CODE)),
        }
        if query.get("startDT"):
            params["startDT"] = str(query["startDT"])
        if query.get("endDT"):
            params["endDT"] = str(query["endDT"])
        # ``statCd`` selects a statistic and therefore only applies to the
        # daily service; sending it to ``iv`` is meaningless.
        if service == "dv":
            params["statCd"] = str(query.get("statCd", DAILY_MEAN_STATISTIC_CODE))
        return params

    @staticmethod
    def build_site_params(sites: Any) -> dict[str, Any]:
        """Build the NWIS site-service parameters (pure, network-free).

        RDB rather than JSON: the service's JSON output is currently
        rejected with HTTP 400 (see the module docstring).
        """
        return {
            "format": RDB_FORMAT,
            "siteOutput": "expanded",
            "sites": USGSNWISConnector._sites_param(sites),
        }

    # ── response parsing (pure) ───────────────────────────────────

    @staticmethod
    def parse_series(payload: Any) -> list[dict[str, Any]]:
        """Parse an NWIS ``iv``/``dv`` JSON body into per-site series.

        Every name read here is taken from the response document; nothing is
        assumed about it beyond the documented ``value.timeSeries`` envelope.
        """
        if not isinstance(payload, dict) or "value" not in payload:
            raise ConnectorUnavailable(
                "USGS NWIS returned a body without the documented 'value' "
                f"envelope (keys: {sorted(payload) if isinstance(payload, dict) else payload!r})."
            )
        time_series = payload["value"].get("timeSeries")
        if not isinstance(time_series, list):
            raise ConnectorUnavailable(
                "USGS NWIS returned a body whose 'value' envelope carries no "
                f"'timeSeries' list (envelope keys: {sorted(payload['value'])})."
            )
        return list(time_series)

    @staticmethod
    def series_site_code(series: dict[str, Any]) -> str:
        """Return the site number of one parsed NWIS series."""
        source_info = series.get("sourceInfo") or {}
        codes = source_info.get("siteCode") or []
        if codes and isinstance(codes, list):
            return str(codes[0].get("value", ""))
        return ""

    @staticmethod
    def series_unit(series: dict[str, Any]) -> str | None:
        """Return the unit code of one parsed NWIS series (e.g. ``ft3/s``)."""
        variable = series.get("variable") or {}
        unit = variable.get("unit") or {}
        code = unit.get("unitCode") if isinstance(unit, dict) else None
        return str(code) if code else None

    @staticmethod
    def series_points(series: dict[str, Any]) -> list[dict[str, Any]]:
        """Flatten one NWIS series into value points.

        Qualifiers, methods and sources are taken from the response document
        so the approval state a calibration run depends on is not lost.
        """
        points: list[dict[str, Any]] = []
        for value_set in series.get("values") or []:
            methods = value_set.get("method") or []
            method_ids = ",".join(str(m.get("methodID", "")) for m in methods)
            for point in value_set.get("value") or []:
                points.append(
                    {
                        "dateTime": point.get("dateTime"),
                        "value": point.get("value"),
                        "qualifiers": ",".join(point.get("qualifiers") or []),
                        "method": method_ids,
                    }
                )
        return points

    @staticmethod
    def parse_site_rdb(text: str) -> tuple[list[str], list[dict[str, str]]]:
        """Parse the NWIS site-file RDB response (pure).

        The column names come from the response's own header row. The
        ``#``-prefixed comment block, the blank separator line and the RDB
        column-format row (``5s 15s 50s …``) are recognised by their first
        field, so a station row is only ever a row whose agency code is USGS.
        """
        header: list[str] | None = None
        stations: list[dict[str, str]] = []
        for raw_line in text.splitlines():
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                continue
            fields = [cell.strip() for cell in line.split("\t")]
            if header is None:
                if fields[0] == "agency_cd":
                    header = fields
                continue
            if fields[0] != _AGENCY_CODE:
                continue
            stations.append(dict(zip(header, fields, strict=False)))
        if header is None:
            raise ConnectorUnavailable(
                "USGS NWIS site-file response carried no 'agency_cd' header "
                "row, so no station metadata could be read from it."
            )
        return header, stations

    # ── live requests ─────────────────────────────────────────────

    def fetch_series(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Request the NWIS ``iv``/``dv`` series and return them parsed."""
        params = self.build_series_params(query)
        payload = self._get_json(SERIES_SERVICE_PATH.format(service=str(query.get("service", "dv")).lower()), params)
        return self.parse_series(payload)

    def fetch_sites(self, sites: Any) -> list[dict[str, str]]:
        """Request NWIS station metadata (RDB) and return it parsed."""
        params = self.build_site_params(sites)
        response = self._get_response(SITE_SERVICE_PATH, params)
        _, stations = self.parse_site_rdb(str(response.text))
        return stations

    # ── DataConnector API ────────────────────────────────────────

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch USGS discharge observations as one CSV asset per site.

        query: {
            "sites": ["09380000", "01646500"],
            "service": "iv" | "dv",
            "parameterCd": "00060",
            "statCd": "00003",          # daily service only
            "startDT": "YYYY-MM-DD",   # or start_date / end_date
            "endDT": "YYYY-MM-DD",
            "with_station_metadata": true,
        }

        Raises:
            ConnectorUnavailable: NWIS is unreachable, answers with an error
                status (including the site service's current HTTP 400 for
                ``format=json``), returns a body without a ``timeSeries``
                list, or no site number was supplied.
        """
        normalized = dict(query)
        normalized.setdefault("startDT", query.get("start_date"))
        normalized.setdefault("endDT", query.get("end_date"))
        sites = self._sites_param(normalized.get("sites"))
        if not sites:
            raise ConnectorUnavailable(
                "USGS NWIS requires at least one site number (e.g. "
                "'09380000') to name the discharge to fetch; none was "
                "supplied."
            )

        service = str(normalized.get("service", "dv")).lower()
        series_by_site: dict[str, dict[str, Any]] = {}
        for series in self.fetch_series(normalized):
            code = self.series_site_code(series)
            if code:
                series_by_site[code] = series

        if not series_by_site:
            raise ConnectorUnavailable(
                f"USGS NWIS returned no time series for sites {sites} with "
                f"parameter {normalized.get('parameterCd', DISCHARGE_PARAMETER_CODE)} "
                f"for {normalized.get('startDT')} to {normalized.get('endDT')}. "
                "The source reported no discharge for that request."
            )

        station_metadata: dict[str, dict[str, str]] = {}
        if normalized.get("with_station_metadata", True):
            for station in self.fetch_sites(list(series_by_site)):
                station_metadata[station.get("site_no", "")] = station

        params = self.build_series_params(normalized)
        assets: list[DataAsset] = []
        for site_code, series in series_by_site.items():
            unit = self.series_unit(series)
            variable = series.get("variable") or {}
            source_info = series.get("sourceInfo") or {}
            geog = (source_info.get("geoLocation") or {}).get("geogLocation") or {}
            station = station_metadata.get(site_code, {})

            buffer = io.StringIO()
            writer = csv.writer(buffer, lineterminator="\n")
            writer.writerow(["site_no", "dateTime", "value", "unit", "qualifiers", "method"])
            point_count = 0
            for point in self.series_points(series):
                writer.writerow(
                    [
                        site_code,
                        point["dateTime"],
                        point["value"],
                        unit,
                        point["qualifiers"],
                        point["method"],
                    ]
                )
                point_count += 1

            asset_id = (
                f"nwis_{service}_{site_code}_"
                f"{hashlib.md5(str(params).encode()).hexdigest()[:8]}"
            )
            file_path = self.cache_dir / f"{asset_id}{_ASSET_SUFFIX}"
            file_path.write_text(buffer.getvalue(), encoding="utf-8")

            assets.append(
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"NWIS {source_info.get('siteName', site_code)} {service} discharge",
                    description=(
                        f"USGS NWIS {service} {variable.get('variableDescription', 'discharge')} "
                        f"at site {site_code} ({unit or 'unit not reported'})"
                    ),
                    file_path=file_path,
                    format=_ASSET_FORMAT,
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "site_no": site_code,
                        "site_name": source_info.get("siteName"),
                        "station_name": station.get("station_nm")
                        or source_info.get("siteName"),
                        "longitude": geog.get("longitude"),
                        "latitude": geog.get("latitude"),
                        "geodetic_datum": station.get("dec_coord_datum_cd")
                        or geog.get("srs"),
                        "altitude_m": _to_float(station.get("alt_va")),
                        "altitude_datum": station.get("alt_datum_cd"),
                        "huc_code": station.get("huc_cd"),
                        "drainage_area_km2": _to_float(station.get("drain_area_va")),
                        "time_zone": station.get("tz_cd"),
                        "service": service,
                        "parameter_code": str(
                            (variable.get("variableCode") or [{}])[0].get(
                                "value", normalized.get("parameterCd", DISCHARGE_PARAMETER_CODE)
                            )
                        ),
                        "parameter_name": variable.get("variableName"),
                        "statistic": (
                            variable.get("options", {}).get("option", [{}])[0].get("value")
                            if service == "dv"
                            else None
                        ),
                        "unit": unit,
                        "unit_code": unit,
                        "no_data_value": variable.get("noDataValue"),
                        "observation_count": point_count,
                    },
                    provenance={
                        "source_url": (
                            f"{self.base_url}/{SERIES_SERVICE_PATH.format(service=service)}"
                        ),
                        "query_params": params,
                        "station_metadata_source": (
                            f"{self.base_url}/{SITE_SERVICE_PATH}" if station else None
                        ),
                        "fetched_at": datetime.now(UTC).isoformat(),
                        "citation": (
                            "U.S. Geological Survey National Water Information "
                            "System (public domain)"
                        ),
                    },
                )
            )

        return assets

    def validate(self, asset: DataAsset) -> bool:
        """Validate a fetched NWIS table by its CSV header and site column."""
        if not asset.file_path.exists():
            return False
        try:
            lines = asset.file_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return False
        if not lines:
            return False
        head = next(csv.reader([lines[0]]))
        return (
            head[:6] == ["site_no", "dateTime", "value", "unit", "qualifiers", "method"]
            and len(lines) > 1
        )


def _to_float(value: Any) -> float | None:
    """Best-effort numeric conversion of an RDB cell; ``None`` when absent."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
