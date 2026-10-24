"""World Bank Pink Sheet connector — monthly commodity reference prices.

Source
------
* World Bank Commodity Markets "Pink Sheet" (CMO) historical monthly data,
  the machine-readable workbook:
  ``https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx``
* Commodity Markets landing page:
  ``https://www.worldbank.org/en/research/commodity-markets``

Credentials — none
-----------------
The Pink Sheet is free, key-less, published monthly under CC BY 4.0. No API
key, token, or registration is requested or supplied by this connector.

What was verified against the live service (2026-10-10)
------------------------------------------------------
* ``HEAD`` and ``GET`` on the workbook URL above both answer **HTTP 200**
  (~0.7 MB OpenXML workbook, 765,246 bytes).
* The workbook ships the worksheets ``["AFOSHEET", "Monthly Prices",
  "Monthly Indices", "Description", "Index Weights"]``. The monthly prices
  live in ``Monthly Prices``: row 4 (0-based) is the commodity-name header,
  row 5 is a unit row (``($/bbl)``, ``($/mt)``, ``($/mmbtu)`` …), and every
  following row is one month with the period in the first column (``2024M12``
  form). Prices are quoted only in **nominal US dollars** — the sheet says so
  in its own title block — so no FX or deflation conversion is applied here.
* The fertilizer references the platform already models in
  ``engine.hydroma.economics.reference_basket`` are columns ``DAP``,
  ``Urea `` (note the trailing space the published sheet carries),
  ``Potassium chloride **`` and ``TSP``, each in ``($/mt)`` — metric tonne,
  nominal. The most recent complete month in the live workbook is ``2024M12``.
* The CSV mirror under the same docs path (``…-CMO-Historical-Data-Monthly.csv``)
  answers **HTTP 404** at the time of writing; it is the documented fallback
  only, used when neither pandas nor openpyxl is installed.

Parser path taken
-----------------
pandas (2.3.3) and openpyxl (3.1.5) are installed, so the workbook is read
with ``pandas.read_excel(sheet_name="Monthly Prices", header=4)`` and
flattened to CSV text with ``DataFrame.to_csv(index=False)`` — the same text
«shape» ``reference_basket.parse_pink_sheet_csv`` consumes. That flattened
text flows through one parser, :meth:`parse_pink_sheet`, so the xlsx and
stdlib-csv paths can never diverge. On a host without pandas/openpyxl the
connector fetches the CSV mirror and parses it with the stdlib ``csv`` module
through that very same parser.

Honesty contract
---------------
This connector carries prices published by the World Bank verbatim. When the
sheet cannot be reached, answers a non-200, or does not parse into the
documented commodity columns, it raises :class:`ConnectorUnavailable` naming
the source and the missing series — it never fabricates, interpolates, or
converts a price. It is a reference-price feed, not a valuation.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.pipeline import DataAsset, DataConnector, DataSource
from engine.hydroma.economics.reference_basket import FERTILIZER_SERIES, PINK_SHEET_ATTRIBUTION

logger = logging.getLogger(__name__)

#: World Bank CMO Pink Sheet historical monthly workbook (verified live 200).
PINK_SHEET_MONTHLY_XLSX_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
#: Same document as CSV — the stdlib fallback mirror, used only when
#: pandas/openpyxl are unavailable. (Answers HTTP 404 at time of writing, so it
#: is not the default path here.)
PINK_SHEET_MONTHLY_CSV_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.csv"
)

#: Worksheet holding the monthly prices.
PINK_SHEET_WORKSHEET = "Monthly Prices"

#: Zero-based row of that worksheet that carries the commodity-name header. The
#: row above is the sheet title block; the row below it is the unit row.
PINK_SHEET_HEADER_ROW = 4

#: Commodity Markets landing page, recorded in provenance.
COMMODITY_MARKETS_URL = "https://www.worldbank.org/en/research/commodity-markets"

#: Licence carried onto every asset.
LICENCE = "CC BY 4.0 (World Bank terms of use)"

#: Unit shown when the sheet itself carried no unit cell for a series. Traced
#: as a documented default in metadata so a caller can tell it apart from a
#: value read verbatim off the sheet; it is never silently substituted.
NOMINAL_UNIT_LABEL = "USD per metric ton (nominal; no FX or deflation applied)"

#: Fetch formats.
FORMAT_XLSX = "xlsx"
FORMAT_CSV = "csv"

#: The columns of the per-commodity asset written by :meth:`fetch`.
_ASSET_FORMAT = "csv"
_ASSET_SUFFIX = ".csv"


def _normalise_label(name: Any) -> str:
    """Fold a header the way :mod:`reference_basket` does.

    Spaces, parentheses, and case are removed; nothing else. This is exactly
    the folding ``reference_basket.parse_pink_sheet_csv`` applies to a column
    before matching it against a published series label, so the two parsers
    select the same columns from the same sheet and the value a market-price
    consumer reads here cannot drift from the value the reference basket
    prices against.
    """
    return str(name).replace(" ", "").replace("(", "").replace(")", "").strip().lower()


def _pandas_available() -> bool:
    """True when both pandas and its openpyxl Excel engine import."""
    try:
        return (
            importlib.util.find_spec("pandas") is not None
            and importlib.util.find_spec("openpyxl") is not None
        )
    except Exception:  # pragma: no cover - find_spec rarely raises
        return False


def _is_number(text: str) -> bool:
    """Whether *text* parses as a float (prices); ``…``/``($/mt)`` do not."""
    try:
        float(text)
    except ValueError:
        return False
    return True


def _looks_like_unit(text: str) -> bool:
    """A Pink Sheet unit cell is parenthesised, e.g. ``($/mt)``."""
    return len(text) >= 2 and text.startswith("(") and text.endswith(")")


class MarketPriceConnector(DataConnector):
    """World Bank Pink Sheet monthly prices for the fertilizer reference basket.

    Registered in ``engine.hydroma.data_pipeline.pipeline`` under the source
    id ``market_price``. No credentials: the Pink Sheet is free, key-less,
    CC BY 4.0.

    The commodities emitted are exactly the four fertilizer references
    ``engine.hydroma.economics.reference_basket`` already models — DAP, urea,
    MOP (potassium chloride) and TSP. Their canonical keys, published series
    labels and terminal are reused from that module's ``FERTILIZER_SERIES``
    rather than re-invented here, and the columns are selected with
    ``reference_basket``'s own label folding, so the two parsers agree by
    construction (the cross-check test pins that they do).

    Prices are nominal US dollars carried verbatim; the unit string read off
    the sheet (``($/mt)`` for these series) travels with every asset. No FX,
    inflation, deflation, or currency conversion is ever applied.

    Args:
        cache_dir: Where the per-commodity price CSVs are written.
        xlsx_url: Workbook URL (documented default, verified live 200).
        csv_url: CSV mirror URL (stdlib fallback, currently 404 live).
        timeout: Per-request timeout in seconds.
        max_retries: Retries for transient ``requests`` failures.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache/market_price"),
        xlsx_url: str = PINK_SHEET_MONTHLY_XLSX_URL,
        csv_url: str = PINK_SHEET_MONTHLY_CSV_URL,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        self.source = DataSource(
            source_id="market_price",
            name="World Bank Pink Sheet (CMO monthly commodity prices)",
            description=(
                "World Bank Commodity Markets 'Pink Sheet' historical monthly "
                "prices in nominal USD. Free, no API key. Fertilizer reference "
                "series (DAP, urea, MOP, TSP) carried verbatim; no conversion."
            ),
            base_url=xlsx_url.rstrip("/"),
            auth_type="none",
            format=_ASSET_FORMAT,
        )
        self.xlsx_url = xlsx_url
        self.csv_url = csv_url
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

    def _get_response(self, url: str):
        """GET one Pink Sheet file, raising :class:`ConnectorUnavailable`.

        Every offline condition — DNS failure, connection error, timeout, or a
        non-200 status — is reported naming the World Bank source and the URL,
        because a commission or credit price that failed to fetch a reference
        must fail loudly rather than fall back to a fabricated number.
        """

        def _do():
            import requests

            return requests.get(
                url,
                headers={"User-Agent": "HyDroMA data pipeline (World Bank open data)"},
                timeout=self.timeout,
            )

        try:
            response = self._retry(_do)()
        except Exception as exc:
            raise ConnectorUnavailable(
                f"The World Bank Pink Sheet at {url} is unreachable "
                f"({type(exc).__name__}: {exc}). The reference-price source "
                f"could not be consulted; no price was substituted for it."
            ) from exc

        status = getattr(response, "status_code", None)
        if status != 200:
            detail = str(getattr(response, "text", ""))[:300].replace("\n", " ")
            raise ConnectorUnavailable(
                f"The World Bank Pink Sheet answered HTTP {status} for {url}: {detail}"
            )
        return response

    # ── format selection and workbook flattening ──────────────────

    @staticmethod
    def resolve_format(query: dict[str, Any]) -> str:
        """Pick ``xlsx`` when pandas/openpyxl are present, else the CSV mirror.

        An explicit ``query["format"]`` of ``"xlsx"`` or ``"csv"`` overrides the
        automatic choice (pure, network-free).
        """
        requested = str(query.get("format", "")).strip().lower()
        if requested in (FORMAT_XLSX, FORMAT_CSV):
            return requested
        return FORMAT_XLSX if _pandas_available() else FORMAT_CSV

    def source_url(self, fmt: str) -> str:
        """The documented URL for the chosen format (pure)."""
        return self.csv_url if fmt == FORMAT_CSV else self.xlsx_url

    def _workbook_csv_text(self, content: bytes) -> str:
        """Read ``Monthly Prices`` and flatten it to CSV text.

        The ``header=4`` row is the commodity-name header, so ``to_csv`` emits
        the unit row as the first data row and one line per month after it —
        the same text the stdlib-csv path parses, and the text
        ``reference_basket.parse_pink_sheet_csv`` also accepts.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ConnectorUnavailable(
                "pandas (or its openpyxl engine) is not installed, so the Pink "
                "Sheet workbook cannot be read. Install pandas and openpyxl, or "
                f"force the CSV mirror with query format={FORMAT_CSV!r}."
            ) from exc
        try:
            frame = pd.read_excel(
                io.BytesIO(content),
                sheet_name=PINK_SHEET_WORKSHEET,
                header=PINK_SHEET_HEADER_ROW,
            )
        except Exception as exc:
            raise ConnectorUnavailable(
                f"The World Bank Pink Sheet workbook at {self.xlsx_url} could not "
                f"be read as the documented monthly-prices workbook (missing the "
                f"'{PINK_SHEET_WORKSHEET}' worksheet at header row "
                f"{PINK_SHEET_HEADER_ROW}?): {type(exc).__name__}: {exc}"
            ) from exc
        return str(frame.to_csv(index=False))

    # ── response parsing (pure) ───────────────────────────────────

    @staticmethod
    def parse_pink_sheet(payload: str) -> dict[str, Any]:
        """Parse flattened Pink-Sheet CSV text into per-series monthly prices.

        The columns are selected with :func:`_normalise_label` against
        ``FERTILIZER_SERIES`` — the identical folding
        ``reference_basket.parse_pink_sheet_csv`` applies — so this parser and
        that one pick the same columns. The returned ``quotes`` is the last
        month in which *every* selected series carries a numeric value, which
        is precisely the month ``reference_basket.parse_pink_sheet_csv``
        returns; the per-key ``series`` are that commodity's own monthly points.

        Returns dict with keys:
            ``quotes``: ``{key: price}`` at the last fully-published month, or
                ``None`` if no month published all four series.
            ``as_of``: that month's period label (e.g. ``"2024M12"``) or ``None``.
            ``units``: ``{key: unit-cell}`` (e.g. ``"($/mt)"``) read off the sheet.
            ``series``: ``{key: [(period, value), …]}`` own numeric points.
            ``columns``: ``{key: published-column-name}`` actually matched.

        Raises:
            ConnectorUnavailable: the body has no rows, or one of the four
                required series columns is absent (the missing series and the
                columns that *were* seen are named).
        """
        label_to_key: dict[str, str] = {
            spec["pink_sheet_series"]: key for key, spec in FERTILIZER_SERIES.items()
        }

        rows = list(csv.reader(io.StringIO(payload)))
        if not rows:
            raise ConnectorUnavailable(
                "The World Bank Pink Sheet body carried no rows, so no commodity "
                "price column could be located."
            )
        header = rows[0]

        column_of: dict[int, str] = {}
        for idx, name in enumerate(header):
            flat = _normalise_label(name)
            for label, key in label_to_key.items():
                if _normalise_label(label) in flat and key not in column_of.values():
                    column_of[idx] = key

        missing = sorted(set(label_to_key.values()) - set(column_of.values()))
        if missing:
            raise ConnectorUnavailable(
                "The World Bank Pink Sheet is missing the required price series "
                f"{missing}; columns seen: {header}. No reference price was "
                "fabricated to fill the column."
            )

        all_keys = set(label_to_key.values())
        period_index = 0
        series: dict[str, list[tuple[str, float]]] = {key: [] for key in all_keys}
        units: dict[str, str] = {}
        quotes: dict[str, float] | None = None
        as_of: str | None = None
        for row in rows[1:]:
            period = row[period_index].strip() if len(row) > period_index else ""
            parsed: dict[str, float] = {}
            for idx, key in column_of.items():
                cell = row[idx].strip() if idx < len(row) else ""
                if not cell:
                    continue
                if key not in units and _looks_like_unit(cell):
                    units[key] = cell
                    continue
                if not _is_number(cell):
                    continue
                value = float(cell)
                series[key].append((period, value))
                parsed[key] = value
            if set(parsed) == all_keys:
                quotes = parsed
                as_of = period

        return {
            "quotes": quotes,
            "as_of": as_of,
            "units": units,
            "series": series,
            "columns": {key: header[idx] for idx, key in column_of.items()},
        }

    # ── DataConnector API ────────────────────────────────────────

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch the monthly fertilizer reference prices, one asset per series.

        query: {
            "commodities": ["dap", "urea", "mop", "tsp"],  # subset, optional
            "format": "xlsx" | "csv",   # override the auto path choice
            "source_url": "...",        # override the URL for the chosen format
        }

        Raises:
            ConnectorUnavailable: the Pink Sheet is unreachable or answers a
                non-200; the workbook is empty or unreadable; a required price
                column is absent; or a selected series carries no numeric
                monthly price. No price is ever substituted for a failed fetch.
        """
        normalized = dict(query)

        requested = [
            str(key).strip().lower()
            for key in normalized.get("commodities", list(FERTILIZER_SERIES))
        ]
        unknown = sorted(set(requested) - set(FERTILIZER_SERIES))
        if unknown:
            raise ConnectorUnavailable(
                f"The World Bank Pink Sheet connector prices the reference inputs "
                f"{list(FERTILIZER_SERIES)}; requested unknown commodities {unknown}."
            )
        commodities = [key for key in FERTILIZER_SERIES if key in requested] or list(
            FERTILIZER_SERIES
        )

        fmt = self.resolve_format(normalized)
        url = str(normalized.get("source_url") or self.source_url(fmt))
        response = self._get_response(url)

        if fmt == FORMAT_CSV:
            text = str(getattr(response, "text", ""))
            if not text.strip():
                raise ConnectorUnavailable(
                    f"The World Bank Pink Sheet returned an empty body for {url}; "
                    "no monthly commodity prices could be read from it."
                )
            csv_text = text
        else:
            content = getattr(response, "content", None)
            if not content:
                raise ConnectorUnavailable(
                    f"The World Bank Pink Sheet returned an empty body for {url}; "
                    "no monthly workbook could be read from it."
                )
            csv_text = self._workbook_csv_text(content)

        retrieved_at = datetime.now(UTC).isoformat()
        parsed = self.parse_pink_sheet(csv_text)
        quotes = parsed["quotes"]
        as_of = parsed["as_of"]
        units = parsed["units"]
        series = parsed["series"]

        assets: list[DataAsset] = []
        for key in commodities:
            spec = FERTILIZER_SERIES[key]
            points: list[tuple[str, float]] = series.get(key) or []
            if not points:
                raise ConnectorUnavailable(
                    f"The World Bank Pink Sheet carried no numeric monthly price "
                    f"for series {key!r} (published '{spec['pink_sheet_series']}'). "
                    "No reference price was fabricated to fill the series."
                )

            years = sorted({int(period[:4]) for period, _ in points if period[:4].isdigit()})
            series_years: list[int] | None = [years[0], years[-1]] if years else None
            unit = units.get(key, NOMINAL_UNIT_LABEL)
            unit_source = "sheet" if key in units else "documented_default"
            latest = quotes.get(key) if quotes else None

            buffer = io.StringIO()
            writer = csv.writer(buffer, lineterminator="\n")
            writer.writerow(["period", "value", "unit", "series"])
            for period, value in points:
                writer.writerow([period, value, unit, spec["pink_sheet_series"]])

            asset_id = f"market_price_{key}_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            file_path = self.cache_dir / f"{asset_id}{_ASSET_SUFFIX}"
            file_path.write_text(buffer.getvalue(), encoding="utf-8")

            assets.append(
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"World Bank Pink Sheet {spec['pink_sheet_series']} monthly price",
                    description=(
                        f"{spec['label']} ({spec['terminal']}) monthly price in {unit}, "
                        f"nominal USD, from the World Bank Commodity Markets "
                        f"Outlook. No FX or deflation conversion applied."
                    ),
                    file_path=file_path,
                    format=_ASSET_FORMAT,
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "commodity": spec["pink_sheet_series"],
                        "series_key": key,
                        "series_label": spec["label"],
                        "terminal": spec["terminal"],
                        "unit": unit,
                        "unit_source": unit_source,
                        "price_basis": (
                            "nominal USD, monthly; no FX or deflation conversion applied"
                        ),
                        "series_years": series_years,
                        "as_of_month": as_of,
                        "latest_price": latest,
                        "observation_count": len(points),
                        "source_url": url,
                        "retrieved_at": retrieved_at,
                        "licence": LICENCE,
                    },
                    provenance={
                        "source_url": url,
                        "publisher": PINK_SHEET_ATTRIBUTION,
                        "landing_page": COMMODITY_MARKETS_URL,
                        "parser": f"{fmt}",
                        "fetched_at": retrieved_at,
                        "citation": PINK_SHEET_ATTRIBUTION,
                    },
                )
            )

        return assets

    def validate(self, asset: DataAsset) -> bool:
        """Validate a fetched price table by its CSV header and data rows."""
        if not asset.file_path.exists():
            return False
        try:
            lines = asset.file_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return False
        if not lines:
            return False
        head = next(csv.reader([lines[0]]))
        return head[:4] == ["period", "value", "unit", "series"] and len(lines) > 1
