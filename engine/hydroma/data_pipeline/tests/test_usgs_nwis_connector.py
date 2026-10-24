"""Guards for the USGS NWIS connector (instantaneous / daily values).

Everything here runs with ``requests`` faked out, so the suite has no network
dependency. The fixtures are built from the field names of a **live**
NWIS response captured on 2026-10-10 (site 09380000, parameter 00060,
statistic 00003) — the numbers themselves are arbitrary test values, and the
*shape* is the one the service actually answers.

What is pinned:

1. the request builders — ``format=json``, the ``sites`` list → comma string
   normalisation, and that ``statCd`` is sent only to the daily service;
2. the honest typed failure when NWIS is unreachable, answers an error
   status, or returns a body with no documented ``timeSeries`` list;
3. the RDB site-file parser, whose column names come from the service's own
   header row and skips the ``#`` comment block and the ``5s 15s …``
   column-format row;
4. asset metadata and the unit-carrying CSV built from a parsed response.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.connectors.usgs_nwis_connector import (
    DAILY_MEAN_STATISTIC_CODE,
    DISCHARGE_PARAMETER_CODE,
    NWIS_BASE_URL,
    USGSNWISConnector,
)

# ── live-shaped fixtures ────────────────────────────────────────────────


def _series(site_no: str = "09380000") -> dict:
    """One NWIS ``timeSeries`` entry, shaped like a live 2026-10-10 response."""
    return {
        "sourceInfo": {
            "siteName": "COLORADO RIVER AT LEES FERRY, AZ",
            "siteCode": [{"value": site_no, "network": "NWIS", "agencyCode": "USGS"}],
            "timeZoneInfo": {
                "defaultTimeZone": {"zoneOffset": "-07:00", "zoneAbbreviation": "MST"},
                "siteUsesDaylightSavingsTime": False,
            },
            "geoLocation": {
                "geogLocation": {
                    "srs": "EPSG:4326",
                    "latitude": 36.86433333,
                    "longitude": -111.58787222,
                },
                "localSiteXY": [],
            },
            "siteProperty": [
                {"value": "ST", "name": "siteTypeCd"},
                {"value": "140700061105", "name": "hucCd"},
            ],
        },
        "variable": {
            "variableCode": [
                {
                    "value": DISCHARGE_PARAMETER_CODE,
                    "network": "NWIS",
                    "vocabulary": "NWIS:UnitValues",
                    "variableID": 45807197,
                    "default": True,
                }
            ],
            "variableName": "Streamflow, ft&#179;/s",
            "variableDescription": "Discharge, cubic feet per second",
            "valueType": "Derived Value",
            "unit": {"unitCode": "ft3/s"},
            "options": {
                "option": [
                    {"value": "Mean", "name": "Statistic", "optionCode": DAILY_MEAN_STATISTIC_CODE}
                ]
            },
            "noDataValue": -999999.0,
        },
        "values": [
            {
                "value": [
                    {"value": "18000", "qualifiers": ["A"], "dateTime": "2023-06-01T00:00:00.000"},
                    {"value": "18300", "qualifiers": ["A"], "dateTime": "2023-06-02T00:00:00.000"},
                ],
                "qualifier": [
                    {
                        "qualifierCode": "A",
                        "qualifierDescription": (
                            "Approved for publication -- Processing and review completed."
                        ),
                        "network": "NWIS",
                        "vocabulary": "uv_rmk_cd",
                    }
                ],
                "method": [{"methodDescription": "", "methodID": 5189}],
                "source": [],
                "offset": [],
                "sample": [],
                "censorCode": [],
            }
        ],
        "name": "USGS:09380000:00060:00003",
    }


def _payload(*series: dict) -> dict:
    return {"name": "ns1:timeSeriesResponseType", "declaredType": "org.cuahsi.waterml.TimeSeriesResponseType", "value": {"timeSeries": list(series) or [_series()]}}


_SITE_RDB = """#
#
# US Geological Survey
# retrieved: 2026-10-09 21:37:48 -04:00\t(caas01)
#
# The Site File stores location and general information about groundwater,
# surface water, and meteorological sites
# for sites in USA.
#
# File-format description:  http://help.waterdata.usgs.gov/faq/about-tab-delimited-output
#
agency_cd\tsite_no\tstation_nm\tsite_tp_cd\tdec_lat_va\tdec_long_va\tdec_coord_datum_cd\talt_va\talt_datum_cd\thuc_cd\ttz_cd\tdrain_area_va
5s\t15s\t50s\t7s\t8s\t8s\t10s\t8s\t8s\t16s\t7s\t8s
USGS\t09380000\tCOLORADO RIVER AT LEES FERRY, AZ\tST\t36.86433333\t-111.58787222\tNAD83\t3109.13\tNAVD88\t140700061105\tMST\t111800.0
USGS\t01646500\tPOTOMAC RIVER NEAR WASH, DC LITTLE FALLS PUMP STA\tST\t38.94977778\t-77.12763889\tNAD83\t37.04\tNAVD88\t020700081005\tEST\t11560.0
"""


def _fake_response(*, status: int = 200, payload: dict | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.text = text or (json.dumps(payload) if payload is not None else "")
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def _connector(tmp_path: Path, **kwargs) -> USGSNWISConnector:
    kwargs.setdefault("cache_dir", tmp_path / "nwis")
    return USGSNWISConnector(**kwargs)


def _stub_nwis(monkeypatch, *, site_rows: str = _SITE_RDB) -> dict:
    """Fake the NWIS endpoints: series (JSON) plus site file (RDB)."""
    calls: dict[str, list] = {"iv_dv": [], "site": []}

    def fake_get(url, **kwargs):
        if url.endswith("/site"):
            calls["site"].append((url, kwargs.get("params")))
            return _fake_response(text=site_rows)
        calls["iv_dv"].append((url, kwargs.get("params")))
        return _fake_response(payload=_payload())

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


# ── request builders ────────────────────────────────────────────────────


def test_series_params_use_json_and_the_documented_codes():
    params = USGSNWISConnector.build_series_params(
        {
            "sites": ["09380000", "01646500"],
            "service": "dv",
            "startDT": "2023-06-01",
            "endDT": "2023-06-03",
        }
    )
    assert params == {
        "format": "json",
        "sites": "09380000,01646500",
        "parameterCd": DISCHARGE_PARAMETER_CODE,
        "statCd": DAILY_MEAN_STATISTIC_CODE,
        "startDT": "2023-06-01",
        "endDT": "2023-06-03",
    }


def test_series_params_normalise_a_comma_separated_sites_string():
    assert USGSNWISConnector.build_series_params({"sites": "09380000, 01646500"})["sites"] == (
        "09380000,01646500"
    )


def test_statistic_is_only_sent_to_the_daily_service():
    """``statCd`` selects a daily statistic; ``iv`` has none to select."""
    assert "statCd" in USGSNWISConnector.build_series_params({"sites": "1", "service": "dv"})
    assert "statCd" not in USGSNWISConnector.build_series_params({"sites": "1", "service": "iv"})


def test_unknown_service_is_a_typed_error():
    with pytest.raises(ConnectorUnavailable) as excinfo:
        USGSNWISConnector.build_series_params({"sites": "1", "service": "monthly"})
    assert "monthly" in str(excinfo.value)


def test_site_params_request_the_rdb_format():
    """The service's JSON output is currently rejected with HTTP 400."""
    assert USGSNWISConnector.build_site_params(["09380000"]) == {
        "format": "rdb",
        "siteOutput": "expanded",
        "sites": "09380000",
    }


# ── site-file RDB parsing ───────────────────────────────────────────────


def test_site_rdb_parser_reads_columns_skips_comments_and_format_row():
    header, stations = USGSNWISConnector.parse_site_rdb(_SITE_RDB)
    assert header[:3] == ["agency_cd", "site_no", "station_nm"]
    assert [station["site_no"] for station in stations] == ["09380000", "01646500"]
    assert stations[0]["station_nm"] == "COLORADO RIVER AT LEES FERRY, AZ"
    assert stations[0]["dec_coord_datum_cd"] == "NAD83"


def test_site_rdb_without_a_header_row_fails_typed():
    with pytest.raises(ConnectorUnavailable) as excinfo:
        USGSNWISConnector.parse_site_rdb("# only comments\n# here\n")
    assert "agency_cd" in str(excinfo.value)


# ── series parsing ──────────────────────────────────────────────────────


def test_parse_series_reads_site_code_unit_and_points():
    series = USGSNWISConnector.parse_series(_payload())[0]
    assert USGSNWISConnector.series_site_code(series) == "09380000"
    assert USGSNWISConnector.series_unit(series) == "ft3/s"
    points = USGSNWISConnector.series_points(series)
    assert len(points) == 2
    assert points[0]["dateTime"] == "2023-06-01T00:00:00.000"
    assert points[0]["value"] == "18000"
    assert points[0]["qualifiers"] == "A"
    assert points[0]["method"] == "5189"


@pytest.mark.parametrize("payload", [None, {}, {"name": "x"}, {"value": {"nil": "true"}}])
def test_parse_series_rejects_bodies_without_a_time_series_list(payload):
    with pytest.raises(ConnectorUnavailable):
        USGSNWISConnector.parse_series(payload)


# ── fetch ───────────────────────────────────────────────────────────────


def test_fetch_requests_the_documented_endpoint(tmp_path, monkeypatch):
    calls = _stub_nwis(monkeypatch)
    assets = _connector(tmp_path).fetch(
        {
            "sites": ["09380000", "01646500"],
            "startDT": "2023-06-01",
            "endDT": "2023-06-03",
            "with_station_metadata": False,
        }
    )

    url, params = calls["iv_dv"][0]
    assert url == f"{NWIS_BASE_URL}/dv"
    assert params["format"] == "json"
    assert params["statCd"] == DAILY_MEAN_STATISTIC_CODE
    assert len(assets) == 1  # the stub answers one series, so one asset


def test_fetch_builds_a_unit_carrying_csv_and_maps_metadata(tmp_path, monkeypatch):
    _stub_nwis(monkeypatch)
    assets = _connector(tmp_path).fetch(
        {"sites": ["09380000"], "startDT": "2023-06-01", "endDT": "2023-06-03"}
    )

    assert len(assets) == 1
    asset = assets[0]
    assert asset.source_id == "usgs_nwis"
    assert asset.format == "csv"
    assert asset.file_path.exists() and asset.file_path.stat().st_size > 0

    metadata = asset.metadata
    assert metadata["site_no"] == "09380000"
    assert metadata["station_name"] == "COLORADO RIVER AT LEES FERRY, AZ"
    assert metadata["latitude"] == 36.86433333
    assert metadata["longitude"] == -111.58787222
    # Station metadata comes from the RDB site file; the datum stays visible.
    assert metadata["geodetic_datum"] == "NAD83"
    assert metadata["altitude_m"] == 3109.13
    assert metadata["altitude_datum"] == "NAVD88"
    assert metadata["huc_code"] == "140700061105"
    assert metadata["drainage_area_km2"] == 111800.0
    assert metadata["time_zone"] == "MST"
    # Unit travels with the data, from the response document.
    assert metadata["unit"] == "ft3/s"
    assert metadata["parameter_code"] == DISCHARGE_PARAMETER_CODE
    assert metadata["statistic"] == "Mean"
    assert metadata["observation_count"] == 2

    lines = asset.file_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "site_no,dateTime,value,unit,qualifiers,method"
    assert lines[1].startswith("09380000,2023-06-01T00:00:00.000,18000,ft3/s,A,5189")
    assert "usgs.gov" in asset.provenance["source_url"]
    assert _connector(tmp_path).validate(asset) is True


def test_fetch_accepts_an_instantaneous_service_request(tmp_path, monkeypatch):
    calls = _stub_nwis(monkeypatch)
    _connector(tmp_path).fetch(
        {"sites": ["09380000"], "service": "iv", "with_station_metadata": False}
    )
    url, params = calls["iv_dv"][0]
    assert url == f"{NWIS_BASE_URL}/iv"
    assert "statCd" not in params


def test_fetch_requires_a_site_number(tmp_path, monkeypatch):
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({})
    assert "site number" in str(excinfo.value)


def test_fetch_surfaces_an_error_status(tmp_path, monkeypatch):
    def boom(url, **kwargs):
        return _fake_response(
            status=400,
            text="<h1>HTTP Status 400 - unrecognized output format for query=basic</h1>",
        )

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"sites": ["09380000"]})
    assert "400" in str(excinfo.value)


def test_fetch_surfaces_network_failures(tmp_path, monkeypatch):
    def boom(url, **kwargs):
        raise requests.ConnectionError("nwis unreachable")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch({"sites": ["09380000"]})
    assert "nwis unreachable" in str(excinfo.value)


def test_fetch_reports_an_empty_time_series_list(tmp_path, monkeypatch):
    def empty_series(url, **kwargs):
        return _fake_response(payload={"value": {"timeSeries": []}})

    monkeypatch.setattr(requests, "get", empty_series)
    with pytest.raises(ConnectorUnavailable) as excinfo:
        _connector(tmp_path).fetch(
            {"sites": ["09380000"], "with_station_metadata": False}
        )
    assert "no time series" in str(excinfo.value)


def test_validate_rejects_a_table_without_a_usable_header(tmp_path):
    connector = _connector(tmp_path)
    path = tmp_path / "probe.csv"
    path.write_text("station_id,date,value\n1,2020-01-01,3\n", encoding="utf-8")
    asset = connector_asset(path)
    assert connector.validate(asset) is False

    path.write_text(
        "site_no,dateTime,value,unit,qualifiers,method\n" "09380000,2023-06-01T00:00:00.000,18000,ft3/s,A,5189\n",
        encoding="utf-8",
    )
    assert connector.validate(asset) is True

    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    assert connector.validate(connector_asset(empty)) is False


def connector_asset(path: Path):
    """A minimal DataAsset pointing at *path* (validate only reads the file)."""
    from engine.hydroma.data_pipeline.pipeline import DataAsset

    return DataAsset(
        asset_id="probe",
        source_id="usgs_nwis",
        name="probe",
        description="probe",
        file_path=path,
        format="csv",
        size_bytes=path.stat().st_size,
        checksum="0" * 32,
    )
