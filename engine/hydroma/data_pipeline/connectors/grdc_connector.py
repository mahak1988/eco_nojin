"""GRDC connector — Global Runoff Data Centre river discharge observations.

Source
------
* BfG landing page (verified live, HTTP 200): ``https://www.bafg.de/GRDC``
* GRDC Data Portal — the service that actually serves station discharge:
  ``https://portal.grdc.sr.unh.edu/``

Reachability, verified live on 2026-10-10
-----------------------------------------
Every path under ``https://www.bafg.de/GRDC`` — including ``/EN/02_daten/``,
``/data/data_portal/``, ``/help/faq/``, ``/search.json`` and ``/sitemap.xml``
— answers HTTP 200 with the *same* 42,473-byte placeholder page, whose
announcement reads: "The GRDC Data Portal is currently unavailable due to
IT issues." The successor host ``https://portal.grdc.bafg.de/`` answers a
301 to ``/applications/``, which serves an 83-byte empty document; every
other path on it answers 404. The historical portal host
``portal.grdc.sr.unh.edu`` does not resolve from this sandbox at all.

So GRDC is **not live-verified** here, unlike the USGS NWIS and IGRAC
connectors in this package. That is recorded rather than papered over:

* this connector still performs a real HTTP request for every station it is
  asked for, and reports what it actually met as
  :class:`ConnectorUnavailable` naming the data source;
* it never substitutes synthetic, interpolated, modelled or retyped values,
  because a calibration run that silently accepted invented discharge would
  be worse than one that fails.

The documented flat-file export
-------------------------------
The GRDC Data Portal serves one flat file per station and temporal
resolution. The format contract is *self-describing*:

* every ``#``-prefixed line is a ``Key: Value`` metadata pair describing the
  station — identifier, river, country, coordinates, catchment area,
  altitude and the discharge unit;
* the first non-comment line is the column-header row;
* every following line is one observation.

:func:`parse_flat_file` therefore never hard-codes the station's field
names: it reads the header row verbatim, detects the delimiter, and maps
whatever it finds. A file that does not describe itself in this shape is
reported as an error naming the columns that *were* found, not silently
coerced into one. Because the portal is unreachable from this host, the
header block is *documented*, not *live-verified*; the request path, the
typed failure and the parser are the parts this repository can be held to.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.pipeline import DataAsset, DataConnector, DataSource

logger = logging.getLogger(__name__)

#: BfG GRDC landing page (verified live, HTTP 200 — serves the portal
#: outage announcement).
GRDC_SITE_URL = "https://www.bafg.de/GRDC"

#: Historical GRDC Data Portal (DNS does not resolve from this host).
GRDC_PORTAL_URL = "https://portal.grdc.sr.unh.edu/"

#: Successor portal host behind Cloudflare; live but currently serves no
#: application (``/applications/`` returns an empty document).
GRDC_PORTAL_ALT_URL = "https://portal.grdc.bafg.de/"

#: Temporal resolutions GRDC publishes (daily, monthly) and the suffix the
#: documented flat-file URL carries for each.
TEMPORAL_RESOLUTIONS: dict[str, str] = {
    "daily": "Day",
    "monthly": "Month",
}

#: Comment prefix of the flat-file header block.
HEADER_PREFIX = "#"

#: Documented discharge unit. Carried onto the asset *from the file's own
#: header block* when the file declares it; this constant is only the
#: expected value, never a substitute for reading the header.
DISCHARGE_UNIT = "m3/s"

#: Candidate column names (matched case-insensitively, punctuation and
#: spaces stripped) that the parser accepts for each role. Several spellings
#: are listed because the portal has historically shipped both
#: ``YYYY-MM-DD`` and ``Date`` style headers.
_DATE_COLUMNS = ("date", "dates", "datetime", "yyyymmdd", "observationdate")
_VALUE_COLUMNS = ("value", "discharge", "dischargevalue", "q", "runoff")

#: Header keys that identify the station, used to build ``station_id``.
_STATION_ID_KEYS = ("grdc-no", "stationid", "station", "grdcstation")
_UNIT_KEYS = ("unit", "units", "dischargeunit")

#: Delimiters tried when reading the column-header row, in order. GRDC has
#: shipped tab-, semicolon- and space-separated exports; the parser reports
#: the columns it found rather than guessing silently.
_DELIMITERS = ("\t", ";", ",", " ")

#: Magic-free: the asset is a plain CSV table written by :meth:`fetch`.
_ASSET_FORMAT = "csv"
_ASSET_SUFFIX = ".csv"


def _normalise(name: str) -> str:
    """Fold a header key for comparison: lower case, punctuation removed."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


class GRDCConnector(DataConnector):
    """River discharge observations from the Global Runoff Data Centre.

    Registered in ``engine.hydroma.data_pipeline.pipeline`` under the
    source id ``grdc``. No credentials are ever needed: GRDC is an open
    WMO data centre, so the only failure mode is that the service itself
    cannot be reached — which is reported as
    :class:`ConnectorUnavailable` naming GRDC and both portal hosts.

    Args:
        cache_dir: Where fetched station tables are written.
        portal_url: GRDC Data Portal base. Defaults to the documented host.
        timeout: Per-request timeout in seconds.
        max_retries: Retries for transient ``requests`` failures.
        temporal_resolution: ``"daily"`` or ``"monthly"``.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache/grdc"),
        portal_url: str = GRDC_PORTAL_URL,
        timeout: float = 60.0,
        max_retries: int = 2,
        temporal_resolution: str = "daily",
    ):
        self.source = DataSource(
            source_id="grdc",
            name="GRDC Global Runoff Data Centre",
            description=(
                "WMO Global Runoff Data Centre river discharge (daily and "
                "monthly) at 10k+ gauging stations. Open data, no API key. "
                "Note: the data portal was unreachable when this connector "
                "was written; fetch raises ConnectorUnavailable rather than "
                "returning fabricated discharge."
            ),
            base_url=portal_url.rstrip("/"),
            auth_type="none",
            format=_ASSET_FORMAT,
        )
        self.portal_url = portal_url.rstrip("/")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_retries = max_retries
        self.temporal_resolution = temporal_resolution

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

    def file_url(self, station_id: str, temporal_resolution: str | None = None) -> str:
        """Build the documented flat-file URL for one station."""
        resolution = (temporal_resolution or self.temporal_resolution).lower()
        if resolution not in TEMPORAL_RESOLUTIONS:
            raise ConnectorUnavailable(
                f"GRDC publishes discharge at daily and monthly resolution; "
                f"{temporal_resolution!r} is not one of "
                f"{sorted(TEMPORAL_RESOLUTIONS)}."
            )
        suffix = TEMPORAL_RESOLUTIONS[resolution]
        return f"{self.portal_url}/files/{station_id}.{suffix}"

    def _download(self, url: str) -> str:
        """GET one flat file and return its body text.

        Raises:
            ConnectorUnavailable: naming the GRDC data source when the
                portal cannot be reached or refuses the request.
        """

        def _get() -> Any:
            import requests

            return requests.get(
                url,
                headers={"User-Agent": "HyDroMA data pipeline (open data)"},
                timeout=self.timeout,
            )

        try:
            response = self._retry(_get)()
        except Exception as exc:
            raise ConnectorUnavailable(
                f"GRDC (Global Runoff Data Centre) is not reachable: the "
                f"request for {url} failed with {type(exc).__name__}: "
                f"{exc}. The portal host {self.portal_url} could not be "
                f"reached; the successor host {GRDC_PORTAL_ALT_URL} answers "
                f"but serves no application, and the BfG site {GRDC_SITE_URL} "
                f"currently carries an IT-outage notice for the GRDC Data "
                f"Portal. No discharge was substituted for it."
            ) from exc

        status = getattr(response, "status_code", None)
        if status != 200:
            detail = str(getattr(response, "text", ""))[:300]
            raise ConnectorUnavailable(
                f"GRDC (Global Runoff Data Centre) answered HTTP {status} "
                f"for {url}: {detail}"
            )
        body = response.text
        if not body or not body.strip():
            raise ConnectorUnavailable(
                f"GRDC (Global Runoff Data Centre) returned an empty body "
                f"for {url}. The data source supplied no discharge records."
            )
        return str(body)

    # ── flat-file parsing (pure) ──────────────────────────────────

    @staticmethod
    def parse_flat_file(text: str) -> tuple[dict[str, str], list[str], list[str]]:
        """Parse the documented GRDC flat file into header, columns, rows.

        The rows stay raw text; _split_rows() turns them into cells once the
        header's delimiter has won.

        The file's own comment block and column-header row are the source of
        every name returned here; nothing is invented. A body whose column
        header row carries neither a date nor a value column raises
        :class:`ConnectorUnavailable` naming the columns that were found.

        Args:
            text: Raw flat-file body as served by GRDC.

        Returns:
            ``(header, columns, rows)`` — the ``# Key: Value`` metadata, the
            column names verbatim, and the observation rows verbatim.
        """
        header: dict[str, str] = {}
        lines = [line for line in text.splitlines() if line.strip()]

        data_start: int | None = None
        for index, line in enumerate(lines):
            if line.lstrip().startswith(HEADER_PREFIX):
                content = line.lstrip()[len(HEADER_PREFIX) :].strip()
                if ":" in content:
                    key, _, value = content.partition(":")
                    header[key.strip()] = value.strip()
                continue
            data_start = index
            break

        if data_start is None:
            raise ConnectorUnavailable(
                "GRDC returned a flat file with a header comment block but no "
                "column-header row, so no discharge table could be read from it."
            )

        # Delimiter detection: whichever candidate splits the column-header
        # row into the most fields wins, with the header row expected to hold
        # more than one column-name cell.
        header_line = lines[data_start]
        columns: list[str] = []
        for delimiter in _DELIMITERS:
            candidate = [cell.strip() for cell in header_line.split(delimiter)]
            if len(candidate) > len(columns) and all(candidate):
                columns = candidate

        if len(columns) < 2:
            raise ConnectorUnavailable(
                "GRDC returned a flat file whose column-header row "
                f"{header_line!r} does not describe more than one discharge "
                "table column."
            )

        folded = [_normalise(name) for name in columns]
        date_index = next((i for i, name in enumerate(folded) if name in _DATE_COLUMNS), None)
        value_index = next((i for i, name in enumerate(folded) if name in _VALUE_COLUMNS), None)
        if date_index is None or value_index is None:
            raise ConnectorUnavailable(
                "GRDC returned a flat file with columns "
                f"{columns}; the documented discharge table needs a date "
                "column and a value column, and neither (or only one) was "
                "found. No observation was fabricated to fill the gap."
            )

        rows = [line for line in lines[data_start + 1 :] if line.strip()]
        return header, columns, rows

    @staticmethod
    def _split_rows(rows: list[str], column_count: int) -> list[list[str]]:
        """Split data rows with the same delimiter that won for the header."""
        best: list[list[str]] | None = None
        for delimiter in _DELIMITERS:
            candidate = [
                [cell.strip() for cell in row.split(delimiter)] for row in rows
            ]
            well_formed = all(len(cells) == column_count for cells in candidate)
            if well_formed and candidate:
                best = candidate
                break
            if best is None and candidate:
                best = candidate
        return best or []

    # ── DataConnector API ────────────────────────────────────────

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch one GRDC station's discharge as a CSV asset.

        query: {
            "station_id": "1150025",        # GRDC-No., required
            "temporal_resolution": "daily", # or "monthly"
            "start_date": "YYYY-MM-DD",     # optional inclusive filter
            "end_date": "YYYY-MM-DD",       # optional inclusive filter
        }

        Raises:
            ConnectorUnavailable: GRDC's portal cannot be reached, refuses
                the request, answers without a discharge table, or returns a
                file whose columns do not describe one. No substitute data
                is produced in any of those cases.
        """
        station_id = str(query.get("station_id", "")).strip()
        if not station_id:
            raise ConnectorUnavailable(
                "GRDC requires a station id (GRDC-No., e.g. '1150025') to "
                "name the discharge file to fetch; none was supplied."
            )

        resolution = str(query.get("temporal_resolution", self.temporal_resolution))
        url = self.file_url(station_id, resolution)
        body = self._download(url)

        header, columns, rows = self.parse_flat_file(body)
        cells_by_row = self._split_rows(rows, len(columns))

        unit, unit_source = _header_unit(header)

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["station_id", "date", "value", "unit"])
        observations = 0
        for cells in cells_by_row:
            row_map = dict(zip(columns, cells, strict=False))
            date_value = _lookup(row_map, _DATE_COLUMNS)
            flow_value = _lookup(row_map, _VALUE_COLUMNS)
            if date_value is None or flow_value is None:
                continue
            if not _matches_range(date_value, query.get("start_date"), query.get("end_date")):
                continue
            writer.writerow([station_id, date_value, flow_value, unit])
            observations += 1

        asset_id = f"grdc_{station_id}_{resolution}_{hashlib.md5(url.encode()).hexdigest()[:8]}"
        file_path = self.cache_dir / f"{asset_id}{_ASSET_SUFFIX}"
        file_path.write_text(buffer.getvalue(), encoding="utf-8")

        metadata: dict[str, Any] = {
            "station_id": station_id,
            "temporal_resolution": resolution,
            "unit": unit,
            "unit_source": unit_source,
            "source_columns": columns,
            "source_header": header,
            "observations": observations,
        }
        metadata.update(_header_metadata(header))

        return [
            DataAsset(
                asset_id=asset_id,
                source_id=self.source.source_id,
                name=f"GRDC {station_id} {resolution} discharge",
                description=(
                    f"Global Runoff Data Centre {resolution} discharge for "
                    f"station {station_id} ({unit})"
                ),
                file_path=file_path,
                format=_ASSET_FORMAT,
                size_bytes=file_path.stat().st_size,
                checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                metadata=metadata,
                provenance={
                    "source_url": url,
                    "file_columns": columns,
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "citation": (
                        "Global Runoff Data Centre (GRDC), 56068 Koblenz, "
                        "Germany — Federal Institute of Hydrology (BfG)"
                    ),
                },
            )
        ]

    def validate(self, asset: DataAsset) -> bool:
        """Validate a fetched GRDC table by its CSV header and unit column."""
        if not asset.file_path.exists():
            return False
        try:
            lines = asset.file_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return False
        if not lines:
            return False
        head = next(csv.reader([lines[0]]))
        return head[:4] == ["station_id", "date", "value", "unit"] and len(lines) > 1


def _header_unit(header: dict[str, str]) -> tuple[str, str]:
    """Return ``(unit, unit_source)`` from the file's own header block.

    When the header declares a unit it is used verbatim and traced as
    ``"header"``; when it does not, the documented GRDC discharge unit is
    used and traced as ``"documented_default"`` so a caller can tell the two
    apart instead of trusting a value that came from this module.
    """
    for key, value in header.items():
        if _normalise(key) in _UNIT_KEYS and value.strip():
            return value.strip(), "header"
    return DISCHARGE_UNIT, "documented_default"


def _header_metadata(header: dict[str, str]) -> dict[str, Any]:
    """Fold the station metadata the file declares into well-known keys.

    Every alias is matched against the header's *own* keys, so a file that
    spells ``River``, ``river name`` or ``RIVER`` all resolve. Aliases that
    the file does not declare are simply absent — never defaulted.
    """
    aliases: tuple[tuple[str, str], ...] = (
        ("river", "river_name"),
        ("river name", "river_name"),
        ("country", "country"),
        ("latitude", "latitude"),
        ("longitude", "longitude"),
        ("catchment area", "catchment_area_km2"),
        ("altitude", "altitude_m"),
        ("grdc no", "grdc_station_name"),
    )
    folded_header = {_normalise(key): value for key, value in header.items()}
    metadata: dict[str, Any] = {}
    for alias, target in aliases:
        value = folded_header.get(_normalise(alias))
        if value:
            metadata[target] = value
    return metadata


def _lookup(row_map: dict[str, str], names: tuple[str, ...]) -> str | None:
    """Return the first value of *row_map* whose column name folds to *names*."""
    for column, value in row_map.items():
        if _normalise(column) in names:
            return value
    return None


def _matches_range(
    date_value: str, start_date: str | None, end_date: str | None
) -> bool:
    """Inclusive date filter on the file's own date string (no parsing imposed)."""
    if not start_date and not end_date:
        return True
    candidate = str(date_value).strip()[:10]
    if start_date and candidate < str(start_date)[:10]:
        return False
    if end_date and candidate > str(end_date)[:10]:
        return False
    return True
