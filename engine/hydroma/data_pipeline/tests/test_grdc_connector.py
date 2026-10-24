"""Guards for the GRDC river-discharge connector.

Everything here runs with ``requests`` faked out, so the suite has no network
dependency. The GRDC Data Portal was verified **unreachable** from this
environment on 2026-10-10 (BfG serves an IT-outage announcement; the successor
host answers but serves no application; ``portal.grdc.sr.unh.edu`` does not
resolve), so the flat-file *shape* below is the documented format, and the
fixture values are arbitrary test values — never presented as GRDC
observations. The connector's contract is what is pinned:

1. the request builder — the documented ``/files/<id>.<Day|Month>`` URL and
   the resolution whitelist;
2. the honest typed failure (``ConnectorUnavailable`` naming GRDC and all
   three hosts) for every way the source can fail: network error, non-200,
   empty body, a header block with no column row, and a table with neither a
   date nor a value column — and never a substituted observation;
3. the flat-file parser: ``# Key: Value`` header extraction, delimiter
   detection on the column-header row, case/punctuation folding of column
   aliases, and verbatim rows;
4. the fetched asset: unit traced to the file's own header (or explicitly
   to the documented default), date-range filtering, provenance (source URL,
   citation, fetched-at) and the ``validate`` header check.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.connectors.grdc_connector import (
    DISCHARGE_UNIT,
    GRDC_PORTAL_ALT_URL,
    GRDC_PORTAL_URL,
    GRDC_SITE_URL,
    TEMPORAL_RESOLUTIONS,
    GRDCConnector,
)

# ── documented-shape fixture ───────────────────────────────────────────────


def _flat_file() -> str:
    """A GRDC flat file in the documented self-describing shape.

    Header block + tab-separated column row + two observations. The values are
    arbitrary test values, not GRDC discharge.
    """
    return (
        "# GRDC-No.: 1150025\n"
        "# River: RHINE\n"
        "# Country: DE\n"
        "# Latitude: 47.5317\n"
        "# Longitude: 8.4575\n"
        "# Catchment area: 34691\n"
        "# Altitude: 403\n"
        "# Unit: m3/s\n"
        "YYYY-MM-DD\tValue\n"
        "2020-01-01\t1100.5\n"
        "2020-01-02\t980.0\n"
        "2020-01-03\t1234.0\n"
    )


def _response(status_code: int = 200, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    return response


def _connector(tmp_path: Path) -> GRDCConnector:
    return GRDCConnector(cache_dir=tmp_path / "cache", max_retries=0)


# ── request building ───────────────────────────────────────────────────────


def test_file_url_uses_documented_pattern() -> None:
    c = _connector(Path("."))
    base = GRDC_PORTAL_URL.rstrip("/")
    assert c.file_url("1150025", "daily") == f"{base}/files/1150025.Day"
    assert c.file_url("1150025", "monthly") == f"{base}/files/1150025.Month"


def test_file_url_rejects_unknown_resolution() -> None:
    c = _connector(Path("."))
    with pytest.raises(ConnectorUnavailable) as err:
        c.file_url("1150025", "hourly")
    assert "daily and monthly" in str(err.value)


def test_resolutions_are_daily_and_monthly() -> None:
    assert TEMPORAL_RESOLUTIONS == {"daily": "Day", "monthly": "Month"}


# ── parser ─────────────────────────────────────────────────────────────────


def test_parse_flat_file_extracts_header_columns_and_rows() -> None:
    header, columns, rows = GRDCConnector.parse_flat_file(_flat_file())
    assert header["GRDC-No."] == "1150025"
    assert header["River"] == "RHINE"
    assert header["Unit"] == "m3/s"
    assert columns == ["YYYY-MM-DD", "Value"]
    assert len(rows) == 3
    assert rows[0] == "2020-01-01\t1100.5"


def test_parse_flat_file_accepts_alias_column_names() -> None:
    text = (
        "# GRDC-No.: 1\n"
        "Date;Discharge\n"
        "2020-01-01;10.0\n"
    )
    header, columns, rows = GRDCConnector.parse_flat_file(text)
    assert columns == ["Date", "Discharge"]
    assert rows == ["2020-01-01;10.0"]


def test_parse_flat_file_rejects_missing_value_column() -> None:
    text = "# GRDC-No.: 1\nDate\tComment\n2020-01-01\tnone\n"
    with pytest.raises(ConnectorUnavailable) as err:
        GRDCConnector.parse_flat_file(text)
    assert "value column" in str(err.value)
    assert "was fabricated" in str(err.value)


def test_parse_flat_file_rejects_header_without_column_row() -> None:
    with pytest.raises(ConnectorUnavailable) as err:
        GRDCConnector.parse_flat_file("# only metadata\n# nothing else\n")
    assert "column-header row" in str(err.value)


def test_parse_flat_file_rejects_single_column_table() -> None:
    with pytest.raises(ConnectorUnavailable) as err:
        GRDCConnector.parse_flat_file("# GRDC-No.: 1\nValue\n10.0\n")
    assert "more than one discharge" in str(err.value)


# ── fetch and asset ────────────────────────────────────────────────────────


def test_fetch_builds_unit_carrying_csv_with_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c = _connector(tmp_path)
    monkeypatch.setattr(requests, "get", lambda *a, **k: _response(text=_flat_file()))

    assets = c.fetch({"station_id": "1150025", "temporal_resolution": "daily"})
    assert len(assets) == 1
    asset = assets[0]

    assert asset.source_id == "grdc"
    assert asset.format == "csv"
    assert asset.metadata["observations"] == 3
    assert asset.metadata["unit"] == "m3/s"
    assert asset.metadata["unit_source"] == "header"
    assert asset.metadata["river_name"] == "RHINE"
    assert asset.metadata["catchment_area_km2"] == "34691"
    assert asset.metadata["source_columns"] == ["YYYY-MM-DD", "Value"]
    assert asset.provenance["source_url"] == (
        f"{GRDC_PORTAL_URL.rstrip('/')}/files/1150025.Day"
    )
    assert "GRDC" in asset.provenance["citation"]
    assert asset.provenance["fetched_at"]

    body = asset.file_path.read_text(encoding="utf-8").splitlines()
    assert body[0] == "station_id,date,value,unit"
    assert body[1] == "1150025,2020-01-01,1100.5,m3/s"
    assert c.validate(asset) is True


def test_fetch_falls_back_to_documented_unit_when_header_has_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = "# GRDC-No.: 7\nDate\tValue\n2020-01-01\t5.0\n"
    monkeypatch.setattr(requests, "get", lambda *a, **k: _response(text=text))
    assets = _connector(tmp_path).fetch({"station_id": "7"})
    assert assets[0].metadata["unit"] == DISCHARGE_UNIT
    assert assets[0].metadata["unit_source"] == "documented_default"


def test_fetch_applies_inclusive_date_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(requests, "get", lambda *a, **k: _response(text=_flat_file()))
    assets = _connector(tmp_path).fetch(
        {"station_id": "1150025", "start_date": "2020-01-02", "end_date": "2020-01-02"}
    )
    body = assets[0].file_path.read_text(encoding="utf-8").splitlines()
    assert len(body) == 2
    assert body[1] == "1150025,2020-01-02,980.0,m3/s"


def test_fetch_requires_station_id(tmp_path: Path) -> None:
    with pytest.raises(ConnectorUnavailable) as err:
        _connector(tmp_path).fetch({})
    assert "station id" in str(err.value)


def test_fetch_reports_unreachable_source_with_all_hosts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*args, **kwargs):
        raise requests.ConnectionError("dns failure")

    monkeypatch.setattr(requests, "get", _boom)
    with pytest.raises(ConnectorUnavailable) as err:
        _connector(tmp_path).fetch({"station_id": "1150025"})
    message = str(err.value)
    assert "GRDC (Global Runoff Data Centre)" in message
    assert GRDC_PORTAL_URL in message
    assert GRDC_PORTAL_ALT_URL in message
    assert GRDC_SITE_URL in message
    assert "No discharge was substituted" in message


def test_fetch_reports_non_200(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(requests, "get", lambda *a, **k: _response(404, "not found"))
    with pytest.raises(ConnectorUnavailable) as err:
        _connector(tmp_path).fetch({"station_id": "1150025"})
    assert "HTTP 404" in str(err.value)


def test_fetch_reports_empty_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(requests, "get", lambda *a, **k: _response(200, "   \n"))
    with pytest.raises(ConnectorUnavailable) as err:
        _connector(tmp_path).fetch({"station_id": "1150025"})
    assert "empty body" in str(err.value)


def test_validate_rejects_missing_or_wrong_header(tmp_path: Path) -> None:
    c = _connector(tmp_path)
    good = tmp_path / "good.csv"
    good.write_text("station_id,date,value,unit\n1,2020-01-01,1.0,m3/s\n", encoding="utf-8")
    assert c.validate(_asset(good)) is True

    wrong = tmp_path / "wrong.csv"
    wrong.write_text("a,b\n1,2\n", encoding="utf-8")
    assert c.validate(_asset(wrong)) is False

    assert c.validate(_asset(tmp_path / "absent.csv")) is False


def _asset(path: Path):
    from engine.hydroma.data_pipeline.pipeline import DataAsset

    return DataAsset(
        asset_id="probe",
        source_id="grdc",
        name="probe",
        description="probe",
        file_path=path,
        format="csv",
        size_bytes=path.stat().st_size if path.exists() else 0,
        checksum="0",
        metadata={},
        provenance={},
    )
