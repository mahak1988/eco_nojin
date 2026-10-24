"""Guards for the FAO WaPOR connector (GISMGR 2.0 API).

The WaPOR v3 API is open data — no API key or token — so there is no
missing-credential path to test here; what is pinned instead is:

1. the request builders (``time:OVERLAPS`` filter, page-size cap, headers);
2. the anonymous-by-default header contract, with ``WAPOR_API_KEY``
   forwarded (never required) when it happens to be set;
3. the honest failure when the FAO API answers HTTP 404 for an unknown
   mapset — the FAO error body is surfaced, not swallowed;
4. asset metadata mapped from the real raster document shape.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.connectors.wapor_connector import (
    API_KEY_ENV,
    API_KEY_HEADER,
    API_URL,
    WaPORConnector,
)

_TIFF = b"II*\x00" + b"cog-payload"


def _connector(tmp_path: Path, **kwargs) -> WaPORConnector:
    kwargs.setdefault("cache_dir", tmp_path / "wapor")
    return WaPORConnector(**kwargs)


def _raster(code: str = "WAPOR-3.L1-AETI-D.2024-01-D1") -> dict:
    return {
        "workspaceCode": "WAPOR-3",
        "mapsetCode": "L1-AETI-D",
        "code": code,
        "dimensions": [
            {
                "code": "DEKAD",
                "member": {
                    "code": "2024-01-D1",
                    "startDate": "2024-01-01",
                    "endDate": "2024-01-10",
                },
            }
        ],
        "measureCaption": "Actual EvapoTranspiration and Interception",
        "measureUnit": "mm/day",
        "scale": 0.1,
        "offset": 0.0,
        "downloadUrl": "https://storage.googleapis.com/fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET/L1-AETI-D/x.tif",
        "gsutilUri": "gs://fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET/L1-AETI-D/x.tif",
        "width": 368640,
        "height": 122880,
        "srs": {"epsg": 4326},
        "extent": {"wgs84": [-180.0, -60.0, 180.0, 60.0]},
        "noDataValue": 255.0,
        "size": {"bytes": 4096, "humanReadable": "4.00 KB"},
    }


def _fake_response(
    *, status: int = 200, payload: dict | None = None, body: str = "", chunks=None
) -> MagicMock:
    """A ``requests`` response double wired for with-blocks, .json() and .text."""
    response = MagicMock()
    response.status_code = status
    if payload is not None:
        response.json.return_value = payload
    response.text = body
    if chunks is not None:
        response.iter_content.return_value = chunks
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.raise_for_status.return_value = None
    return response


def _stub_gismgr(
    monkeypatch, items: list[dict], status: int = 200, body: dict | None = None
) -> dict:
    """Fake the GISMGR API: catalogue calls plus the raster download."""
    calls: dict[str, list] = {"get": []}
    payload = body if body is not None else {
        "status": 200,
        "message": "OK",
        "response": {"items": items},
    }

    def fake_get(url, **kwargs):
        calls["get"].append((url, kwargs.get("params"), kwargs.get("headers")))
        if url.endswith(".tif"):
            return _fake_response(chunks=[_TIFF])
        return _fake_response(status=status, payload=payload, body=json.dumps(payload))

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


# ── request builders ───────────────────────────────────────────────


def test_rasters_params_use_the_documented_overlaps_filter():
    params = WaPORConnector._build_rasters_params("2024-01-01", "2024-03-31", limit=10)
    assert params == {
        "filter": "time:OVERLAPS:2024-01-01:2024-03-31",
        "size": "10",
        "sort": "code:DESC",
    }
    # One-sided period and the default (newest first, no filter).
    assert WaPORConnector._build_rasters_params("2024-01-01", None, 5)["filter"] == (
        "time:OVERLAPS:2024-01-01"
    )
    assert "filter" not in WaPORConnector._build_rasters_params(None, None, 5)


def test_rasters_params_cap_page_size_at_100():
    assert WaPORConnector._build_rasters_params(None, None, 500)["size"] == "100"


def test_headers_are_anonymous_without_a_key(tmp_path, monkeypatch):
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    assert _connector(tmp_path)._headers() == {}


def test_optional_api_key_is_forwarded_when_present(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV, "optional-key")
    assert _connector(tmp_path)._headers() == {API_KEY_HEADER: "optional-key"}


def test_raster_period_comes_from_the_time_dimension():
    assert WaPORConnector._raster_period(_raster()) == ("2024-01-01", "2024-01-10")


# ── catalogue calls ────────────────────────────────────────────────


def test_list_mapsets_reads_the_documented_endpoint(tmp_path, monkeypatch):
    calls = _stub_gismgr(
        monkeypatch,
        [],
        body={"status": 200, "response": {"items": [{"code": "L1-AETI-D", "caption": "AETI"}]}},
    )
    connector = _connector(tmp_path)

    mapsets = connector.list_mapsets()

    url, params, _ = calls["get"][0]
    assert url == f"{API_URL}/catalog/workspaces/WAPOR-3/mapsets"
    assert params == {"size": 100}
    assert mapsets == [{"code": "L1-AETI-D", "caption": "AETI"}]


def test_list_rasters_hits_the_mapset_rasters_endpoint(tmp_path, monkeypatch):
    calls = _stub_gismgr(monkeypatch, [_raster()])
    connector = _connector(tmp_path)

    rasters = connector.list_rasters("L1-AETI-D", "2024-01-01", "2024-03-31", 10)

    url, params, _ = calls["get"][0]
    assert url == f"{API_URL}/catalog/workspaces/WAPOR-3/mapsets/L1-AETI-D/rasters"
    assert params["filter"] == "time:OVERLAPS:2024-01-01:2024-03-31"
    assert len(rasters) == 1


# ── fetch ──────────────────────────────────────────────────────────


def test_fetch_downloads_the_raster_and_maps_metadata(tmp_path, monkeypatch):
    calls = _stub_gismgr(monkeypatch, [_raster()])
    connector = _connector(tmp_path)

    assets = connector.fetch(
        {"mapset": "L1-AETI-D", "start_date": "2024-01-01", "end_date": "2024-03-31"}
    )

    assert len(assets) == 1
    asset = assets[0]
    assert asset.source_id == "wapor"
    assert asset.format == "geotiff"
    assert asset.file_path.exists() and asset.file_path.stat().st_size > 0
    assert asset.metadata["measure"] == "Actual EvapoTranspiration and Interception"
    assert asset.metadata["unit"] == "mm/day"
    assert asset.metadata["period_start"] == "2024-01-01"
    assert asset.metadata["period_end"] == "2024-01-10"
    assert asset.metadata["scale"] == 0.1
    assert asset.metadata["crs_epsg"] == 4326
    assert asset.provenance["source_url"].endswith(".tif")
    # The download used no credential header (open data).
    assert calls["get"][-1][2] == {}


def test_fetch_returns_empty_when_no_raster_matches_the_period(tmp_path, monkeypatch):
    _stub_gismgr(monkeypatch, [])
    connector = _connector(tmp_path)

    assert connector.fetch({"start_date": "1990-01-01", "end_date": "1990-03-31"}) == []


def test_fetch_surfaces_a_404_for_an_unknown_mapset(tmp_path, monkeypatch):
    _stub_gismgr(
        monkeypatch,
        items=[],
        status=404,
        body={"status": 404, "error": "Not Found", "message": "item not found {mapstoreCode=NOPE}"},
    )
    connector = _connector(tmp_path)

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector.fetch({"mapset": "NOPE"})

    message = str(excinfo.value)
    assert "404" in message
    assert "item not found" in message


def test_fetch_surfaces_network_failures(tmp_path, monkeypatch):
    def boom(url, **kwargs):
        raise requests.ConnectionError("fao api unreachable")

    monkeypatch.setattr(requests, "get", boom)
    connector = _connector(tmp_path)

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector.fetch({"mapset": "L1-AETI-D"})

    assert "unreachable" in str(excinfo.value)


def test_validate_accepts_tiff_magic_only(tmp_path):
    from engine.hydroma.data_pipeline.pipeline import DataAsset

    connector = _connector(tmp_path)

    def make(payload: bytes) -> DataAsset:
        path = tmp_path / "probe.tif"
        path.write_bytes(payload)
        return DataAsset(
            asset_id="x",
            source_id="wapor",
            name="x",
            description="x",
            file_path=path,
            format="geotiff",
            size_bytes=len(payload),
            checksum="0" * 32,
        )

    assert connector.validate(make(_TIFF)) is True
    assert connector.validate(make(b"MM\x00*cog")) is True
    assert connector.validate(make(b"not a raster")) is False
    assert connector.validate(make(b"")) is False
