"""IGRAC connector — global groundwater level observations (GGIS).

Source
------
* IGRAC (International Groundwater Resources Assessment Centre):
  ``https://igrac.org/`` (verified live, HTTP 200).
* Global Groundwater Information System (GGIS) — the IGRAC data portal, a
  GeoNode catalogue fronting a GeoServer instance:
  ``https://ggis.un-igrac.org``

Credentials — none
-----------------
Every endpoint used here answers anonymously; no key, token or login is
requested or supplied.

What was verified against the live service (2026-10-10)
------------------------------------------------------
* ``GET /api/v2/datasets/?search=groundwater`` returns a GeoNode v2 page
  (``{"total": …, "datasets": [{ "pk", "title", "name", "uuid", "subtype",
  "workspace", "store", "download_url", "attribute_set", …}]}``); 579
  datasets match the word "groundwater".
* ``GET /api/v2/datasets/2689`` is "GGMN Levels Data" (the Global Groundwater
  Monitoring Network well layer, workspace ``groundwater``, layer
  ``GGMN_Levels_Data``) and publishes the well attribute schema through
  ``attribute_set`` — 28 documented fields including ``id``, ``ggis_uid``,
  ``name``, ``feature_type``, ``country``, ``aquifer_name``, ``status``,
  ``first_recorded_measurement`` and ``last_recorded_measurement``.
* ``GET /geoserver/groundwater/wfs`` with
  ``request=GetFeature&typeName=groundwater:GGMN_Levels_Data&
  outputFormat=application/json`` returns GeoJSON features: well metadata in
  ``properties``, point geometry as ``[longitude, latitude]``. ``CQL_FILTER``
  (e.g. ``id=831568``) and ``bbox`` both restrict the result set. A layer
  that does not exist answers HTTP **200** with an OGC
  ``ServiceExceptionReport`` XML body, which this connector detects and
  raises as an error instead of reading as "no wells".
* ``GET /groundwater/record/831568/measurements/WellLevelMeasurement/data``
  returns the well's level series as
  ``{"data": [{"dt": <epoch seconds>, "par": <parameter name>,
  "u": <unit>, "v": <value>}]}``. The body is served with a ``text/html``
  content type but is JSON, so the body is decoded from text rather than
  trusted by its declared type.

What the measurements *are*
---------------------------
The parameter the GGIS level endpoint exposes is **"Water depth [from the
top of the well]"**, reported in metres — a depth to water, not a head
elevation. It is carried with its own parameter name and unit verbatim, so
a calibration routine sees which quantity it was handed rather than
assuming one. No conversion, gap-filling, interpolation or resampling is
performed here: rows arrive as the source reported them.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.pipeline import DataAsset, DataConnector, DataSource

logger = logging.getLogger(__name__)

#: IGRAC GGIS base (verified live).
GGIS_BASE_URL = "https://ggis.un-igrac.org"

#: GeoNode v2 dataset API (catalogue search and per-dataset detail).
DATASETS_PATH = "/api/v2/datasets/"

#: GeoServer OGC Web Feature Service path, one per workspace.
WFS_PATH = "/geoserver/{workspace}/wfs"

#: Per-well level series path. ``{station_id}`` is the GGIS well id and
#: ``{measurement_type}`` the GWML2 measurement kind.
MEASUREMENTS_PATH = "/groundwater/record/{station_id}/measurements/{measurement_type}/data"

#: WFS parameters needed for a JSON GetFeature request.
WFS_REQUEST_PARAMS: dict[str, str] = {
    "service": "WFS",
    "version": "1.0.0",
    "request": "GetFeature",
    "outputFormat": "application/json",
}

#: The GWML2 measurement kind carrying water levels.
LEVEL_MEASUREMENT = "WellLevelMeasurement"

#: Default catalogue entry: the Global Groundwater Monitoring Network well
#: layer, whose attribute schema is published by the API (verified live).
DEFAULT_DATASET_PK = 2689
DEFAULT_MEASUREMENT_TYPE = LEVEL_MEASUREMENT

#: Units are carried from the source; no unit conversion is performed.
_ASSET_FORMAT = "csv"
_ASSET_SUFFIX = ".csv"


class IGRACGroundwaterConnector(DataConnector):
    """Global groundwater level records from the IGRAC GGIS portal.

    Registered in ``engine.hydroma.data_pipeline.pipeline`` under the source
    id ``igrac_groundwater``. Anonymous access throughout; the only failure
    modes are that the portal cannot be reached, the dataset or well does
    not exist, or the well carries no level series — each reported as
    :class:`ConnectorUnavailable` naming the missing data source.

    Args:
        cache_dir: Where fetched well tables are written.
        base_url: GGIS base URL (documented default, verified live).
        dataset_pk: GeoNode dataset id of the well layer to read.
        timeout: Per-request timeout in seconds.
        max_retries: Retries for transient ``requests`` failures.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache/igrac"),
        base_url: str = GGIS_BASE_URL,
        dataset_pk: int = DEFAULT_DATASET_PK,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        self.source = DataSource(
            source_id="igrac_groundwater",
            name="IGRAC Global Groundwater Levels (GGIS)",
            description=(
                "Global groundwater level records from the IGRAC Global "
                "Groundwater Information System (GeoNode catalogue + "
                "GeoServer WFS). Open data, anonymous access, no API key."
            ),
            base_url=base_url.rstrip("/"),
            auth_type="none",
            format=_ASSET_FORMAT,
        )
        self.base_url = base_url.rstrip("/")
        self.dataset_pk = dataset_pk
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

    def _get_text(self, url: str, params: dict[str, Any]) -> str:
        """GET one endpoint and return its body, raising on failure.

        The body's *declared* content type is not trusted: the level-series
        endpoint serves JSON as ``text/html``, so the text is returned and
        decoded by the caller.
        """

        def _do():
            import requests

            response = requests.get(
                url, params=params, timeout=self.timeout, allow_redirects=True
            )
            if response.status_code >= 400:
                detail = str(response.text)[:300]
                raise ConnectorUnavailable(
                    f"IGRAC GGIS answered HTTP {response.status_code} for "
                    f"{url}: {detail}"
                )
            return response

        try:
            response = self._retry(_do)()
        except ConnectorUnavailable:
            raise
        except Exception as exc:
            raise ConnectorUnavailable(
                f"IGRAC (Global Groundwater Information System at "
                f"{self.base_url}) was unreachable for {url} "
                f"({type(exc).__name__}: {exc})."
            ) from exc
        return str(response.text)

    def _get_json(self, url: str, params: dict[str, Any]) -> Any:
        """GET one endpoint and decode its body as JSON."""
        text = self._get_text(url, params)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConnectorUnavailable(
                f"IGRAC GGIS returned a body that is not JSON for {url} "
                f"({exc}). The data source could not be read."
            ) from exc

    # ── catalogue: dataset metadata (station-layer discovery) ─────

    def dataset(self, dataset_pk: int | None = None) -> dict[str, Any]:
        """Return one GeoNode dataset document.

        Raises:
            ConnectorUnavailable: the dataset does not exist or the catalogue
                cannot be read.
        """
        pk = dataset_pk if dataset_pk is not None else self.dataset_pk
        body = self._get_json(f"{self.base_url}{DATASETS_PATH}{pk}/", {})
        document = body.get("dataset")
        if not isinstance(document, dict):
            raise ConnectorUnavailable(
                f"IGRAC GGIS dataset {pk} carried no 'dataset' document "
                f"(response keys: {sorted(body)})."
            )
        return document

    @staticmethod
    def layer_for_dataset(document: dict[str, Any]) -> str:
        """Build the WFS ``typeName`` from a dataset document.

        The workspace and layer name are read from the document itself
        (``workspace``, then ``name`` or ``store``); a document that declares
        neither cannot be turned into a WFS query, and that is an error
        rather than a silent skip.
        """
        workspace = str(document.get("workspace") or document.get("store") or "").strip()
        layer = str(document.get("name") or document.get("store") or "").strip()
        if not workspace or not layer:
            raise ConnectorUnavailable(
                "IGRAC GGIS dataset document declares no workspace/layer "
                f"pair (workspace={workspace!r}, name={layer!r}); no WFS "
                "feature type could be derived from it."
            )
        return f"{workspace}:{layer}"

    def search_datasets(self, keyword: str, page_size: int = 20) -> list[dict[str, Any]]:
        """Search the GGIS catalogue and return dataset summaries."""
        body = self._get_json(
            f"{self.base_url}{DATASETS_PATH}", {"search": keyword, "page_size": page_size}
        )
        datasets = body.get("datasets")
        if not isinstance(datasets, list):
            raise ConnectorUnavailable(
                f"IGRAC GGIS catalogue search for {keyword!r} returned no "
                f"'datasets' list (response keys: {sorted(body)})."
            )
        return list(datasets)

    # ── station metadata (WFS) ────────────────────────────────────

    def _wfs_url(self, workspace: str) -> str:
        return f"{self.base_url}{WFS_PATH.format(workspace=workspace)}"

    @staticmethod
    def _build_wfs_params(
        type_name: str,
        max_features: int | None = None,
        cql_filter: str | None = None,
        bbox: list[float] | None = None,
    ) -> dict[str, str]:
        """Build the WFS ``GetFeature`` parameters (pure, network-free)."""
        params: dict[str, str] = dict(WFS_REQUEST_PARAMS)
        params["typeName"] = type_name
        if max_features is not None:
            params["maxFeatures"] = str(int(max_features))
        if cql_filter:
            params["CQL_FILTER"] = cql_filter
        if bbox:
            if len(bbox) != 4:
                raise ValueError(
                    f"bbox must be [lon_min, lat_min, lon_max, lat_max]; got {bbox!r}"
                )
            params["bbox"] = ",".join(str(float(v)) for v in bbox)
        return params

    def _request_features(
        self,
        type_name: str,
        max_features: int | None = None,
        cql_filter: str | None = None,
        bbox: list[float] | None = None,
    ) -> list[dict[str, Any]]:
        """Return GeoJSON features for one layer, raising on an OGC error."""
        workspace = type_name.split(":", 1)[0]
        params = self._build_wfs_params(type_name, max_features, cql_filter, bbox)
        text = self._get_text(self._wfs_url(workspace), params)
        body = _decode_wfs_body(text, type_name)
        features = body.get("features")
        if not isinstance(features, list):
            raise ConnectorUnavailable(
                f"IGRAC GGIS WFS answered for {type_name} but carried no "
                f"'features' list (response keys: {sorted(body)})."
            )
        # An OGC ServiceExceptionReport is reported as a missing data source
        # by :func:`_decode_wfs_body` above, so an empty result set here is a
        # genuine "no wells matched", which the caller may filter away.
        return list(features)

    def list_wells(
        self,
        station_id: str | None = None,
        bbox: list[float] | None = None,
        max_features: int | None = 50,
        dataset_pk: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch well (station) metadata as a list of GeoJSON features.

        Args:
            station_id: When given, WFS ``CQL_FILTER`` restricts to it.
            bbox: Optional ``[lon_min, lat_min, lon_max, lat_max]`` filter.
            max_features: Cap on returned wells.
            dataset_pk: Override the dataset whose layer is queried.

        Raises:
            ConnectorUnavailable: the catalogue/WFS cannot be reached, the
                layer does not exist, or the dataset document declares no
                feature type.
        """
        type_name = self.resolve_feature_type(dataset_pk)
        cql_filter = f"id={station_id}" if station_id else None
        return self._request_features(
            type_name, max_features=max_features, cql_filter=cql_filter, bbox=bbox
        )

    def resolve_feature_type(self, dataset_pk: int | None = None) -> str:
        """Return the WFS ``typeName`` of the configured well layer."""
        return self.layer_for_dataset(self.dataset(dataset_pk))

    # ── time series (per-well measurements) ───────────────────────

    def measurements_url(
        self, station_id: str, measurement_type: str = DEFAULT_MEASUREMENT_TYPE
    ) -> str:
        """Build the documented per-well level-series URL (pure)."""
        return f"{self.base_url}" + MEASUREMENTS_PATH.format(
            station_id=station_id, measurement_type=measurement_type
        )

    @staticmethod
    def parse_level_series(payload: Any) -> list[dict[str, Any]]:
        """Parse a level-series payload into records.

        The documented shape is ``{"data": [{"dt", "par", "u", "v"}]}``:
        ``dt`` is epoch seconds, ``par`` the source's parameter name, ``u``
        its unit and ``v`` the value. A payload that is not this shape raises
        :class:`ConnectorUnavailable` rather than yielding records with
        invented timestamps.
        """
        if not isinstance(payload, dict) or "data" not in payload:
            raise ConnectorUnavailable(
                "IGRAC GGIS returned a level series without the documented "
                f"'data' key (payload keys: "
                f"{sorted(payload) if isinstance(payload, dict) else type(payload).__name__})."
            )
        records: list[dict[str, Any]] = []
        for entry in payload["data"]:
            if not isinstance(entry, dict) or "dt" not in entry or "v" not in entry:
                raise ConnectorUnavailable(
                    f"IGRAC GGIS level record is missing 'dt' or 'v': {entry!r}"
                )
            records.append(
                {
                    "dt": entry["dt"],
                    "datetime": datetime.fromtimestamp(
                        float(entry["dt"]), tz=UTC
                    ).isoformat(),
                    "parameter": entry.get("par"),
                    "unit": entry.get("u"),
                    "value": entry["v"],
                }
            )
        return records

    def fetch_level_series(
        self,
        station_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        measurement_type: str = DEFAULT_MEASUREMENT_TYPE,
    ) -> list[dict[str, Any]]:
        """Fetch one well's level records, optionally date-filtered.

        Timestamps are epoch seconds in the source payload, so the filter is
        applied on the ISO date derived from them; no resampling occurs.
        """
        payload = self._get_json(
            self.measurements_url(station_id, measurement_type), {}
        )
        records = self.parse_level_series(payload)
        return [
            record
            for record in records
            if _matches_date_range(record["datetime"], start_date, end_date)
        ]

    # ── DataConnector API ────────────────────────────────────────

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch one well's groundwater levels as a CSV asset.

        query: {
            "station_id": "831568",   # GGIS well id — required
            "start_date": "YYYY-MM-DD",  # optional inclusive filter
            "end_date": "YYYY-MM-DD",    # optional inclusive filter
            "with_station_metadata": true,  # WFS lookup of the well layer
            "dataset_pk": 2689,        # override the well layer
            "measurement_type": "WellLevelMeasurement",
        }

        Raises:
            ConnectorUnavailable: the portal is unreachable, the station id
                is missing, the well layer cannot be resolved, or the well
                carries no published level series.
        """
        station_id = str(query.get("station_id", "")).strip()
        if not station_id:
            raise ConnectorUnavailable(
                "IGRAC GGIS requires a well id (the GGIS station id, e.g. "
                "'831568') to name the level series to fetch; none was "
                "supplied."
            )

        measurement_type = str(
            query.get("measurement_type", DEFAULT_MEASUREMENT_TYPE)
        )
        records = self.fetch_level_series(
            station_id,
            query.get("start_date"),
            query.get("end_date"),
            measurement_type,
        )

        if not records:
            raise ConnectorUnavailable(
                f"IGRAC GGIS published no {measurement_type} records for well "
                f"{station_id}"
                + (
                    f" between {query.get('start_date')} and {query.get('end_date')}"
                    if query.get("start_date") or query.get("end_date")
                    else ""
                )
                + ". The source reported no groundwater level for that well."
            )

        station: dict[str, Any] = {}
        feature_type: str | None = None
        if query.get("with_station_metadata", True):
            feature_type = self.resolve_feature_type(query.get("dataset_pk"))
            features = self.list_wells(
                station_id, dataset_pk=query.get("dataset_pk")
            )
            if features:
                properties = features[0].get("properties") or {}
                geometry = features[0].get("geometry") or {}
                coordinates = geometry.get("coordinates") or [None, None]
                station = {
                    "station_id": station_id,
                    "name": properties.get("name"),
                    "original_id": properties.get("original_id"),
                    "ggis_uid": properties.get("ggis_uid"),
                    "feature_type": properties.get("feature_type"),
                    "purpose": properties.get("purpose"),
                    "status": properties.get("status"),
                    "country": properties.get("country"),
                    "organisation": properties.get("organisation"),
                    "aquifer_name": properties.get("aquifer_name"),
                    "aquifer_type": properties.get("aquifer_type"),
                    "longitude": coordinates[0],
                    "latitude": coordinates[1],
                    "dem_elevation": properties.get("dem_elevation"),
                    "dem_elevation_unit": properties.get("dem_elevation_unit"),
                    "first_recorded_measurement": properties.get(
                        "first_recorded_measurement"
                    ),
                    "last_recorded_measurement": properties.get(
                        "last_recorded_measurement"
                    ),
                    "measurements_count": properties.get("groundwater_level_data"),
                }

        unit = _first_unit(records)
        parameter = _first_parameter(records)

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["station_id", "datetime", "value", "unit", "parameter"])
        for record in records:
            writer.writerow(
                [
                    station_id,
                    record["datetime"],
                    record["value"],
                    record["unit"],
                    record["parameter"],
                ]
            )

        asset_id = (
            f"igrac_{station_id}_{hashlib.md5(str(records).encode()).hexdigest()[:8]}"
        )
        file_path = self.cache_dir / f"{asset_id}{_ASSET_SUFFIX}"
        file_path.write_text(buffer.getvalue(), encoding="utf-8")

        return [
            DataAsset(
                asset_id=asset_id,
                source_id=self.source.source_id,
                name=f"GGIS well {station_id} groundwater level",
                description=(
                    f"{parameter or 'Groundwater level'} at GGIS well "
                    f"{station_id}"
                    + (f" ({station.get('country', '')})" if station.get("country") else "")
                ),
                file_path=file_path,
                format=_ASSET_FORMAT,
                size_bytes=file_path.stat().st_size,
                checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                metadata={
                    "station": station,
                    "station_id": station_id,
                    "parameter": parameter,
                    "unit": unit,
                    "observation_count": len(records),
                    "measurement_type": measurement_type,
                    "first_observation": records[0]["datetime"] if records else None,
                    "last_observation": records[-1]["datetime"] if records else None,
                },
                provenance={
                    "source_url": self.measurements_url(station_id, measurement_type),
                    "wfs_feature_type": feature_type,
                    "wfs_url": (
                        self._wfs_url(feature_type.split(":", 1)[0])
                        if feature_type
                        else None
                    ),
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "citation": (
                        "IGRAC — Global Groundwater Monitoring Network (GGMN) "
                        "levels, via the Global Groundwater Information System"
                    ),
                },
            )
        ]

    def validate(self, asset: DataAsset) -> bool:
        """Validate a fetched well table by its CSV header and unit column."""
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
            head[:5] == ["station_id", "datetime", "value", "unit", "parameter"]
            and len(lines) > 1
        )


def _decode_wfs_body(text: str, type_name: str) -> dict[str, Any]:
    """Decode a WFS response, reporting an OGC ``ServiceExceptionReport``.

    GeoServer reports an unknown feature type (or a malformed filter) with
    HTTP **200** and an XML ``ServiceExceptionReport`` body. Reading that as
    JSON would fail with a decode error that hides the actual reason, so the
    XML body is recognised first and its service-exception text is surfaced,
    naming the feature type that could not be read.
    """
    stripped = text.lstrip()
    if stripped.startswith("<?xml") or "ServiceExceptionReport" in stripped:
        # The lookahead keeps ``ServiceExceptionReport`` from matching as a
        # ``ServiceException`` tag.
        for match in re.finditer(
            r"<ServiceException(?=[\s/>])[^>]*>(.*?)</ServiceException>", stripped
        ):
            detail = match.group(1).strip()
            if detail:
                raise ConnectorUnavailable(
                    f"IGRAC GGIS WFS refused the request for feature type "
                    f"{type_name!r} with a service exception: {detail}. The "
                    f"layer does not exist on the portal, or the query was "
                    f"invalid."
                )
        raise ConnectorUnavailable(
            f"IGRAC GGIS WFS returned an OGC ServiceExceptionReport for "
            f"feature type {type_name!r} with no readable exception text. "
            f"The layer does not exist on the portal, or the query was "
            f"invalid."
        )
    try:
        body = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConnectorUnavailable(
            f"IGRAC GGIS WFS returned a body that is neither a GeoJSON "
            f"feature collection nor an OGC service exception for "
            f"{type_name!r}: {exc}"
        ) from exc
    if not isinstance(body, dict):
        raise ConnectorUnavailable(
            f"IGRAC GGIS WFS returned a {type(body).__name__} instead of a "
            f"feature collection for feature type {type_name!r}."
        )
    return body


def _matches_date_range(
    iso_datetime: str, start_date: str | None, end_date: str | None
) -> bool:
    """Inclusive YYYY-MM-DD filter on an ISO-8601 datetime string."""
    candidate = str(iso_datetime)[:10]
    if start_date and candidate < str(start_date)[:10]:
        return False
    if end_date and candidate > str(end_date)[:10]:
        return False
    return True


def _first_unit(records: list[dict[str, Any]]) -> str | None:
    """Unit carried verbatim from the source's own records."""
    for record in records:
        if record.get("unit"):
            return str(record["unit"])
    return None


def _first_parameter(records: list[dict[str, Any]]) -> str | None:
    """Parameter name carried verbatim from the source's own records."""
    for record in records:
        if record.get("parameter"):
            return str(record["parameter"])
    return None
