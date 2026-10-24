"""Guards for the CDSE (Copernicus Data Space Ecosystem) connector.

Covers the two things a network-free test *can* cover honestly:

1. the request builders — STAC payloads, the RFC 3339 datetime
   normalisation the live API demands (it rejects date-only ranges with
   HTTP 400), and the OData ``$value`` URL built from ``s3://eodata/...``
   asset hrefs;
2. the failure contract — missing credentials raise ``ConnectorUnavailable``
   naming ``CDS_CLIENT_ID``/``CDS_CLIENT_SECRET`` rather than returning an
   empty result that would look like "no imagery".

No test in this module performs a network call: ``requests.post``/``get``
are replaced with fakes.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable
from engine.hydroma.data_pipeline.connectors.cds_connector import (
    CLIENT_ID_ENV,
    CLIENT_SECRET_ENV,
    ODATA_URL,
    STAC_CATALOG_URL,
    CDSEConnector,
)

_JP2 = b"\x00\x00\x00\x0cjP  \r\n\x87\n" + b"jp2-payload"


def _connector(tmp_path: Path) -> CDSEConnector:
    return CDSEConnector(cache_dir=tmp_path / "cds", client_id="id", client_secret="secret")


# ── credentials ────────────────────────────────────────────────────


def test_missing_credentials_name_the_environment_variables(tmp_path, monkeypatch):
    monkeypatch.delenv(CLIENT_ID_ENV, raising=False)
    monkeypatch.delenv(CLIENT_SECRET_ENV, raising=False)
    connector = CDSEConnector(cache_dir=tmp_path / "cds")

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector._credentials()

    message = str(excinfo.value)
    assert CLIENT_ID_ENV in message
    assert CLIENT_SECRET_ENV in message


def test_partial_credentials_name_the_missing_variable(tmp_path, monkeypatch):
    monkeypatch.delenv(CLIENT_ID_ENV, raising=False)
    monkeypatch.setenv(CLIENT_SECRET_ENV, "only-secret")
    connector = CDSEConnector(cache_dir=tmp_path / "cds")

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector._credentials()

    assert CLIENT_ID_ENV in str(excinfo.value)


def test_credentials_are_read_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv(CLIENT_ID_ENV, "env-id")
    monkeypatch.setenv(CLIENT_SECRET_ENV, "env-secret")
    connector = CDSEConnector(cache_dir=tmp_path / "cds")
    assert connector._credentials() == ("env-id", "env-secret")


# ── request builders ───────────────────────────────────────────────


def test_datetime_is_normalised_to_rfc3339():
    """The live API rejects date-only ranges with HTTP 400."""
    assert CDSEConnector.normalize_datetime("2021-01-01/2021-03-31") == (
        "2021-01-01T00:00:00Z/2021-03-31T23:59:59Z"
    )
    assert CDSEConnector.normalize_datetime("2021-01-01") == (
        "2021-01-01T00:00:00Z/2021-01-01T23:59:59Z"
    )
    # Already-RFC3339 input passes through unchanged.
    rfc = "2021-01-01T06:00:00Z/2021-06-01T06:00:00Z"
    assert CDSEConnector.normalize_datetime(rfc) == rfc
    # An open-ended range keeps its ".." bound.
    assert CDSEConnector.normalize_datetime("2021-01-01/..") == "2021-01-01T00:00:00Z/.."


def test_build_search_payload_shape():
    payload = CDSEConnector._build_search_payload(
        bbox=[51.0, 35.0, 52.0, 36.0],
        datetime_range="2021-01-01/2021-01-31",
        collections=["sentinel-2-l2a"],
        limit=7,
    )
    assert payload == {
        "bbox": [51.0, 35.0, 52.0, 36.0],
        "datetime": "2021-01-01T00:00:00Z/2021-01-31T23:59:59Z",
        "collections": ["sentinel-2-l2a"],
        "limit": 7,
    }


def test_build_product_filter_uses_startswith():
    """An exact Name match returned zero rows for a live item; startswith works."""
    params = CDSEConnector._build_product_filter("S2A_MSIL2A_20210129T071141")
    assert params == {
        "$filter": "startswith(Name,'S2A_MSIL2A_20210129T071141')",
        "$top": "1",
    }


def test_build_asset_download_url_from_s3_href():
    url = CDSEConnector._build_asset_download_url(
        "46b694a3-f734",
        "s3://eodata/Sentinel-2/MSI/L2A/2021/01/29/SCENE.SAFE/GRANULE/T39SWV/IMG_DATA/R10m/T39SWV_TCI_10m.jp2",
    )
    assert url == (
        f"{ODATA_URL}/Products(46b694a3-f734)"
        "/Nodes('Sentinel-2')/Nodes('MSI')/Nodes('L2A')/Nodes('2021')"
        "/Nodes('01')/Nodes('29')/Nodes('SCENE.SAFE')/Nodes('GRANULE')"
        "/Nodes('T39SWV')/Nodes('IMG_DATA')/Nodes('R10m')"
        "/Nodes('T39SWV_TCI_10m.jp2')/$value"
    )


def test_build_asset_download_url_passes_http_hrefs_through():
    https = "https://example.org/scene.jp2"
    assert CDSEConnector._build_asset_download_url("id", https) == https


def test_build_asset_download_url_rejects_unknown_scheme():
    with pytest.raises(ConnectorUnavailable):
        CDSEConnector._build_asset_download_url("id", "ftp://eodata/scene.jp2")


# ── fetch with the network faked ───────────────────────────────────


def _fake_response(*, status: int = 200, payload: dict | None = None, chunks=None) -> MagicMock:
    """A ``requests`` response double wired for both with-blocks and .json()."""
    response = MagicMock()
    response.status_code = status
    if payload is not None:
        response.json.return_value = payload
    if chunks is not None:
        response.iter_content.return_value = chunks
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.raise_for_status.return_value = None
    return response


def _stub_cdse(monkeypatch, items: list[dict], product_id: str = "uuid-1") -> dict:
    """Fake the token, search, product lookup and download calls."""
    calls: dict[str, list] = {"post": [], "get": []}

    def fake_post(url, **kwargs):
        calls["post"].append(url)
        if url.endswith("/token"):
            return _fake_response(payload={"access_token": "token-abc"})
        return _fake_response(payload={"features": items})

    def fake_get(url, **kwargs):
        calls["get"].append(url)
        if url.endswith("/$value"):
            return _fake_response(chunks=[_JP2])
        if "/Products" in url:
            return _fake_response(payload={"value": [{"Id": product_id}]})
        return _fake_response(payload={"value": []})

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def _item(asset_key: str = "TCI_10m") -> dict:
    return {
        "id": "S2A_MSIL2A_20210129T071141_N0500_R106_T39SWV",
        "collection": "sentinel-2-l2a",
        "assets": {
            asset_key: {
                "href": "s3://eodata/Sentinel-2/L2A/SCENE.SAFE/TCI_10m.jp2",
                "type": "image/jp2",
            }
        },
    }


def test_fetch_downloads_one_asset_per_item(tmp_path, monkeypatch):
    connector = _connector(tmp_path)
    calls = _stub_cdse(monkeypatch, [_item()])

    assets = connector.fetch(
        {"bbox": [51.0, 35.0, 52.0, 36.0], "datetime": "2021-01-01/2021-01-31"}
    )

    assert len(assets) == 1
    asset = assets[0]
    assert asset.source_id == "cdse_sentinel"
    assert asset.format == "geotiff"
    assert asset.file_path.exists() and asset.file_path.stat().st_size > 0
    assert asset.metadata["product_id"] == "uuid-1"
    assert asset.metadata["item_id"] == "S2A_MSIL2A_20210129T071141_N0500_R106_T39SWV"
    assert asset.provenance["stac_catalog"] == STAC_CATALOG_URL
    # token + search posted, product lookup + download fetched
    assert calls["post"][-1] == f"{STAC_CATALOG_URL}/search"
    assert any("/Products" in url for url in calls["get"])
    assert any(url.endswith("/$value") for url in calls["get"])


def test_fetch_skips_items_without_the_requested_asset(tmp_path, monkeypatch):
    connector = _connector(tmp_path)
    _stub_cdse(monkeypatch, [{"id": "no-assets", "assets": {"thumbnail": {"href": "s3://eodata/t.jpg"}}}])

    assert connector.fetch({"asset_key": "TCI_10m"}) == []


def test_fetch_raises_when_token_endpoint_fails(tmp_path, monkeypatch):
    connector = _connector(tmp_path)

    def boom(url, **kwargs):
        raise requests.ConnectionError("identity unreachable")

    monkeypatch.setattr(requests, "post", boom)

    with pytest.raises(ConnectorUnavailable) as excinfo:
        connector.fetch({})

    assert "identity" in str(excinfo.value)


def test_fetch_raises_when_token_response_has_no_token(tmp_path, monkeypatch):
    connector = _connector(tmp_path)

    monkeypatch.setattr(
        requests, "post", lambda url, **kw: _fake_response(payload={"error": "invalid_client"})
    )

    with pytest.raises(ConnectorUnavailable):
        connector.fetch({})


# ── validation ─────────────────────────────────────────────────────


def test_validate_accepts_jpeg2000_and_tiff_only(tmp_path):
    from engine.hydroma.data_pipeline.pipeline import DataAsset

    connector = _connector(tmp_path)

    def make(payload: bytes) -> DataAsset:
        path = tmp_path / "probe.bin"
        path.write_bytes(payload)
        return DataAsset(
            asset_id="x",
            source_id="cdse_sentinel",
            name="x",
            description="x",
            file_path=path,
            format="geotiff",
            size_bytes=len(payload),
            checksum="0" * 32,
        )

    assert connector.validate(make(_JP2)) is True
    assert connector.validate(make(b"II*\x00tiff")) is True
    assert connector.validate(make(b"MM\x00*tiff")) is True
    assert connector.validate(make(b"not a raster at all")) is False
    assert connector.validate(make(b"")) is False
