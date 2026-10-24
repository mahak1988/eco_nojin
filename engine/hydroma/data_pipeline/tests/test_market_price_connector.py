"""Guards for the World Bank Pink Sheet market-price connector.

Everything here runs with ``requests`` faked out, so the suite has no network
dependency. The fixtures are a small, faithful slice of the *live* Pink Sheet
``Monthly Prices`` worksheet captured on 2026-10-10 — the real column names
(``Urea `` with its trailing space, ``Potassium chloride **``), the real unit
row ``($/mt)``, the ``...`` the sheet uses for not-yet-quoted months, and the
genuine ``2024M12`` values (DAP 568.33, Urea 352, MOP 292.5, TSP 477.5). The
xlsx path is exercised through a real workbook built with openpyxl, so the two
parse paths are checked against the same data.

What is pinned:

1. the documented workbook / CSV-mirror URLs, and that a fetch is a plain
   static-file GET with no invented query parameters;
2. the parsed per-commodity series shape, the verbatim unit, and the
   ``reference_basket`` column mapping;
3. the honest typed failure when the source is unreachable, answers an error
   status, or the body is truncated of a required series column;
4. that the registry registers ``market_price`` and goes from 20 to 21;
5. the cross-check that this parser and ``reference_basket.parse_pink_sheet_csv``
   read the very same value off the very same sheet — the proof the connector
   is not a second, divergent reference-price implementation.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.connectors.market_price_connector import (
    PINK_SHEET_MONTHLY_CSV_URL,
    PINK_SHEET_MONTHLY_XLSX_URL,
    MarketPriceConnector,
)
from engine.hydroma.data_pipeline.pipeline import DataAsset, DataPipeline, get_pipeline
from engine.hydroma.economics.reference_basket import parse_pink_sheet_csv

# ── live-shaped fixtures ────────────────────────────────────────────────────
#
# A faithful slice of the live ``Monthly Prices`` worksheet: the commodity-name
# header (row 4), the unit row (row 5), one pre-trading month the sheet marks
# with ``...``, and the six most recent complete months through ``2024M12``.
# The published header keeps its quirks (trailing space on ``Urea `` and the
# ``**`` footnote marker on ``Potassium chloride``).
_HEADER = ["", "Crude oil, average", "DAP", "Urea ", "Potassium chloride **", "TSP"]
# The flattened CSV names the unnamed period column ``Unnamed: 0`` (pandas).
_HEADER_FLAT = ["Unnamed: 0", "Crude oil, average", "DAP", "Urea ", "Potassium chloride **", "TSP"]
_UNITS = [None, "($/bbl)", "($/mt)", "($/mt)", "($/mt)", "($/mt)"]
_UNITS_FLAT = ["", "($/bbl)", "($/mt)", "($/mt)", "($/mt)", "($/mt)"]
_DATA = [
    ["1960M02", "1.63000011444", "...", "42.25", "28.5", "53"],
    ["2024M07", "83.25866666667", "539.4", "342.5", "300.63", "505.75"],
    ["2024M08", "78.121", "546", "342.5", "294", "507.2"],
    ["2024M09", "72.42433333333", "554.75", "337.5", "286.88", "504.38"],
    ["2024M10", "73.97066666667", "573.44", "374.75", "278.13", "503.75"],
    ["2024M11", "72.29166666667", "574.5", "352.3", "281", "491"],
    ["2024M12", "72.311", "568.33", "352", "292.5", "477.5"],
]
_MOP_COLUMN = "Potassium chloride **"


def _fixture_csv() -> str:
    """The flattened Pink-Sheet CSV exactly as ``to_csv`` would emit it."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in [_HEADER_FLAT, _UNITS_FLAT, *_DATA]:
        writer.writerow(row)
    return buffer.getvalue()


def _truncated_csv() -> str:
    """The fixture with the MOP (``Potassium chloride``) column removed."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in [_HEADER_FLAT, _UNITS_FLAT, *_DATA]:
        writer.writerow([cell for idx, cell in enumerate(row) if idx != 4])
    return buffer.getvalue()


def _fixture_xlsx_bytes() -> bytes:
    """A real ``Monthly Prices`` workbook rebuilt from the slice with openpyxl.

    The title block occupies rows 1-4, the commodity header row 5 (index 4, the
    row ``header=4`` reads), the unit row 6, then the monthly data — mirroring
    the live workbook's layout so ``read_excel(header=4)`` sees it correctly.
    """
    import openpyxl

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Monthly Prices"
    sheet.append(["World Bank Commodity Price Data (The Pink Sheet)"])
    sheet.append(["monthly prices in nominal US dollars, 1960 to present"])
    sheet.append(["(monthly series are available only in nominal US dollars)"])
    sheet.append(["Updated on fixture"])
    sheet.append(_HEADER)
    sheet.append(_UNITS)
    for row in _DATA:
        sheet.append(list(row))
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def _fake_response(*, status: int = 200, text: str = "", content: bytes | None = None) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.content = content
    response.text = text or (content.decode("utf-8", "ignore") if content is not None else "")
    response.json.return_value = None
    response.raise_for_status.return_value = None
    return response


def _connector(tmp_path: Path, **kwargs) -> MarketPriceConnector:
    kwargs.setdefault("cache_dir", tmp_path / "market_price")
    return MarketPriceConnector(**kwargs)


def _asset(path: Path) -> DataAsset:
    """A minimal DataAsset pointing at *path* (validate only reads the file)."""
    return DataAsset(
        asset_id="probe",
        source_id="market_price",
        name="probe",
        description="probe",
        file_path=path,
        format="csv",
        size_bytes=path.stat().st_size,
        checksum="0" * 32,
    )


# ── documented URLs and request shape ───────────────────────────────────────


def test_documented_urls_are_the_world_bank_pink_sheet():
    assert PINK_SHEET_MONTHLY_XLSX_URL.endswith("/CMO-Historical-Data-Monthly.xlsx")
    assert PINK_SHEET_MONTHLY_CSV_URL.endswith("/CMO-Historical-Data-Monthly.csv")
    assert "thedocs.worldbank.org" in PINK_SHEET_MONTHLY_XLSX_URL


def test_resolve_format_prefers_the_workbook_and_honours_an_override():
    # pandas + openpyxl are installed here, so the default is the workbook.
    assert MarketPriceConnector.resolve_format({}) == "xlsx"
    assert MarketPriceConnector.resolve_format({"format": "csv"}) == "csv"

    connector = _connector(Path("data/cache/_probe"))
    assert connector.source_url("csv") == PINK_SHEET_MONTHLY_CSV_URL
    assert connector.source_url("xlsx") == PINK_SHEET_MONTHLY_XLSX_URL


def test_fetch_is_a_plain_static_file_get_with_no_query_params(tmp_path, monkeypatch):
    calls: dict[str, object] = {}

    def fake_get(url, **kwargs):
        calls["url"] = url
        calls["params"] = kwargs.get("params")
        return _fake_response(text=_fixture_csv())

    monkeypatch.setattr(requests, "get", fake_get)
    _connector(tmp_path).fetch({"format": "csv"})

    assert calls["url"] == PINK_SHEET_MONTHLY_CSV_URL
    assert not calls["params"]  # a static file download, no invented query string


# ── parsing ─────────────────────────────────────────────────────────────────


def test_parse_maps_the_reference_basket_columns_units_and_latest():
    result = MarketPriceConnector.parse_pink_sheet(_fixture_csv())

    assert set(result["series"]) == {"dap", "urea", "mop", "tsp"}
    assert set(result["quotes"]) == {"dap", "urea", "mop", "tsp"}
    assert result["as_of"] == "2024M12"
    # The last month all four series published, carried verbatim (nominal USD/mt).
    assert result["quotes"] == {"dap": 568.33, "urea": 352.0, "mop": 292.5, "tsp": 477.5}
    # Units are read off the sheet's own unit row, not assumed.
    assert result["units"] == {
        "dap": "($/mt)",
        "urea": "($/mt)",
        "mop": "($/mt)",
        "tsp": "($/mt)",
    }
    # The published column names (quirks preserved) that each key mapped to.
    assert result["columns"]["mop"] == _MOP_COLUMN
    assert result["columns"]["urea"] == "Urea "


def test_parse_skips_the_unit_row_and_the_not_yet_quoted_marker():
    result = MarketPriceConnector.parse_pink_sheet(_fixture_csv())

    dap = result["series"]["dap"]
    # DAP was unquoted in 1960M02 (the ``...`` marker), so its series starts 2024.
    assert [period for period, _ in dap] == [
        "2024M07",
        "2024M08",
        "2024M09",
        "2024M10",
        "2024M11",
        "2024M12",
    ]
    assert dap[-1] == ("2024M12", 568.33)
    assert len(dap) == 6

    # Urea WAS quoted in 1960M02, so its series spans 1960 -> 2024 (7 points).
    urea = result["series"]["urea"]
    assert urea[0] == ("1960M02", 42.25)
    assert len(urea) == 7


def test_parse_reports_a_missing_required_series_names_it():
    with pytest.raises(ConnectorUnavailable) as excinfo:
        MarketPriceConnector.parse_pink_sheet(_truncated_csv())
    message = str(excinfo.value)
    assert "World Bank Pink Sheet" in message
    assert "mop" in message  # the missing series is named
    assert "DAP" in message  # ... alongside the columns that were seen


def test_parse_reports_an_empty_body():
    with pytest.raises(ConnectorUnavailable):
        MarketPriceConnector.parse_pink_sheet("")


# ── fetch (csv path) ─────────────────────────────────────────────────────────


def test_fetch_emits_one_asset_per_commodity_with_unit_and_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kw: _fake_response(text=_fixture_csv()))
    assets = _connector(tmp_path).fetch({"format": "csv"})

    assert len(assets) == 4  # DAP, Urea, MOP, TSP — one asset per reference series
    by_key = {asset.metadata["series_key"]: asset for asset in assets}

    dap = by_key["dap"]
    assert dap.source_id == "market_price"
    assert dap.format == "csv"
    assert dap.metadata["commodity"] == "DAP"
    assert dap.metadata["unit"] == "($/mt)"  # nominal USD per metric ton, verbatim
    assert dap.metadata["latest_price"] == 568.33
    assert dap.metadata["as_of_month"] == "2024M12"
    assert dap.metadata["series_years"] == [2024, 2024]  # DAP unquoted before 2024
    assert dap.metadata["observation_count"] == 6
    assert dap.metadata["source_url"] == PINK_SHEET_MONTHLY_CSV_URL
    assert dap.metadata["licence"] == "CC BY 4.0 (World Bank terms of use)"
    assert dap.metadata["retrieved_at"]
    assert "thedocs.worldbank.org" in dap.provenance["source_url"]

    # Urea's series really does span the early month in this fixture.
    assert by_key["urea"].metadata["series_years"] == [1960, 2024]
    assert by_key["mop"].metadata["latest_price"] == 292.5
    assert by_key["tsp"].metadata["latest_price"] == 477.5

    assert dap.file_path.exists() and dap.file_path.stat().st_size > 0
    lines = dap.file_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "period,value,unit,series"
    assert _connector(tmp_path).validate(dap) is True


def test_fetch_can_subset_commodities(tmp_path, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kw: _fake_response(text=_fixture_csv()))
    only_dap = _connector(tmp_path).fetch({"format": "csv", "commodities": ["dap"]})
    assert [asset.metadata["series_key"] for asset in only_dap] == ["dap"]


def test_fetch_rejects_unknown_commodities(tmp_path, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kw: _fake_response(text=_fixture_csv()))
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"commodities": ["cocoa"]})
    assert "cocoa" in str(excinfo.value)


# ── fetch (xlsx path: real workbook via pandas/openpyxl) ──────────────────────


def test_fetch_reads_the_workbook_and_agrees_with_the_csv_path(tmp_path, monkeypatch):
    pytest.importorskip("openpyxl")

    def fake_get(url, **kwargs):
        assert url == PINK_SHEET_MONTHLY_XLSX_URL
        return _fake_response(content=_fixture_xlsx_bytes())

    monkeypatch.setattr(requests, "get", fake_get)
    assets = _connector(tmp_path).fetch({"format": "xlsx"})

    by_key = {asset.metadata["series_key"]: asset for asset in assets}
    assert by_key["dap"].metadata["latest_price"] == 568.33
    assert by_key["dap"].metadata["unit"] == "($/mt)"
    assert by_key["mop"].metadata["latest_price"] == 292.5
    assert by_key["urea"].metadata["series_years"] == [1960, 2024]


# ── typed failures ──────────────────────────────────────────────────────────


def test_fetch_surfaces_a_network_failure_naming_the_source(tmp_path, monkeypatch):
    def boom(url, **kwargs):
        raise requests.ConnectionError("pink sheet unreachable")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({})
    message = str(excinfo.value)
    assert "World Bank Pink Sheet" in message
    assert "thedocs.worldbank.org" in message
    assert "no price was substituted" in message


def test_fetch_surfaces_an_error_status(tmp_path, monkeypatch):
    def boom(url, **kwargs):
        return _fake_response(status=404, text="<h1>404 Not Found</h1>")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"format": "csv"})
    assert "404" in str(excinfo.value)
    assert PINK_SHEET_MONTHLY_CSV_URL in str(excinfo.value)


def test_fetch_surfaces_an_empty_body(tmp_path, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kw: _fake_response(text="   "))
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"format": "csv"})
    assert "empty body" in str(excinfo.value)


def test_fetch_surfaces_a_truncated_series(tmp_path, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kw: _fake_response(text=_truncated_csv()))
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"format": "csv"})
    assert "mop" in str(excinfo.value)


def test_validate_rejects_a_table_without_a_usable_header(tmp_path):
    connector = _connector(tmp_path)
    path = tmp_path / "probe.csv"

    path.write_text("date,price\n2024M12,1\n", encoding="utf-8")
    assert connector.validate(_asset(path)) is False

    path.write_text("period,value,unit,series\n2024M12,568.33,($/mt),DAP\n", encoding="utf-8")
    assert connector.validate(_asset(path)) is True


# ── registry ──────────────────────────────────────────────────────────────────


def test_market_price_is_registered_in_the_pipeline():
    pipeline = get_pipeline()
    assert "market_price" in pipeline.connectors
    assert isinstance(pipeline.connectors["market_price"], MarketPriceConnector)


def test_registry_count_grew_by_exactly_one():
    # The documented 20 -> 21 growth from adding this single connector.
    assert "market_price" in DataPipeline().connectors
    assert len(DataPipeline().connectors) == 21


# ── cross-check against reference_basket ──────────────────────────────────────


def test_parser_agrees_with_reference_basket_on_the_same_sheet():
    """The two parsers must not diverge on a shared commodity.

    ``reference_basket.parse_pink_sheet_csv`` is the authority the input-credit
    instrument prices against. If this connector selected a different column,
    skipped a different row, or normalised a label differently, the values below
    would differ and this guard would fail — that is the whole point.
    """
    fixture = _fixture_csv()
    reference = parse_pink_sheet_csv(fixture)
    connector = MarketPriceConnector.parse_pink_sheet(fixture)

    # Every shared commodity agrees, DAP included.
    assert connector["quotes"] == reference
    assert connector["quotes"]["dap"] == reference["dap"] == 568.33
    assert connector["as_of"] == "2024M12"
