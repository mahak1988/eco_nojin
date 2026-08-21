"""Unit + integration tests for the CDSE Sentinel-2 NDVI pipeline (offline).

All HTTP interaction is mocked (FakeSession/FakeResponse); NDVI statistics
are computed on synthetic GeoTIFFs written into pytest-managed temp dirs.
The live-refresh endpoint is tested for its disabled and failure paths only.
"""

import io
from uuid import uuid4

import numpy as np
import pytest
import rasterio
from fastapi.testclient import TestClient

from engine.hydroma.config.settings import get_settings
from engine.hydroma.mrv import satellite_cdse
from engine.hydroma.mrv.satellite_cdse import CdseConfig, CdseUnavailable

from services.api_gateway.main import app

client = TestClient(app)


class FakeResponse:
    """Minimal stand-in for requests.Response (json + streaming context)."""

    def __init__(self, status_code=200, json_data=None, content=b""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self._content = content

    def json(self):
        return self._json

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size=1024):
        yield self._content


class FakeSession:
    """Fake requests.Session serving token, search, and band downloads."""

    def __init__(self, features=None, assets=None, token="tok", fail_token=False, fail_search=False):
        self._features = features or []
        self._assets = assets or {}
        self._token = token
        self._fail_token = fail_token
        self._fail_search = fail_search

    def post(self, url, **kwargs):
        if "token" in url:
            if self._fail_token:
                return FakeResponse(500)
            return FakeResponse(200, {"access_token": self._token})
        if self._fail_search:
            return FakeResponse(500)
        return FakeResponse(200, {"features": self._features})

    def get(self, url, **kwargs):
        return FakeResponse(200, content=self._assets.get(url, b""))


def _cfg(**overrides) -> CdseConfig:
    base = dict(
        base_url="https://catalogue.example",
        identity_url="https://identity.example",
        client_id="cid",
        client_secret="csec",
    )
    base.update(overrides)
    return CdseConfig(**base)


def _band_bytes(value: float, nodata: float | None = None) -> bytes:
    """Write a 4x4 float64 GeoTIFF band into a BytesIO and return bytes."""
    buf = io.BytesIO()
    profile = dict(driver="GTiff", height=4, width=4, count=1, dtype="float64")
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(buf, "w", **profile) as ds:
        arr = np.full((4, 4), value, dtype="float64")
        if nodata is not None:
            arr[0, 0] = nodata
        ds.write(arr, 1)
    return buf.getvalue()


def _scene_feature(scene_id="S2A_1", b04="https://x/B04.tif", b08="https://x/B08.tif"):
    return {
        "id": scene_id,
        "properties": {"datetime": "2026-07-15T09:10:00Z", "eo:cloud_cover": 8.2},
        "assets": {"B04": {"href": b04}, "B08": {"href": b08}},
    }


class TestToken:
    def test_success(self):
        session = FakeSession()
        assert satellite_cdse.get_token(session, _cfg()) == "tok"

    def test_http_failure_raises(self):
        session = FakeSession(fail_token=True)
        with pytest.raises(CdseUnavailable):
            satellite_cdse.get_token(session, _cfg())

    def test_missing_token_raises(self):
        session = FakeSession(token="")
        with pytest.raises(CdseUnavailable):
            satellite_cdse.get_token(session, _cfg())


class TestSearch:
    def test_parses_scene_with_both_bands(self):
        session = FakeSession(features=[_scene_feature()])
        scenes = satellite_cdse.search_l2a(session, _cfg(), "tok", [54.0, 36.0, 54.1, 36.1], "2026-07-01T00:00:00Z", "2026-08-01T00:00:00Z")
        assert len(scenes) == 1
        assert scenes[0]["scene_id"] == "S2A_1"
        assert scenes[0]["cloud_cover"] == 8.2

    def test_skips_scene_missing_nir_band(self):
        feature = _scene_feature()
        del feature["assets"]["B08"]
        session = FakeSession(features=[feature])
        scenes = satellite_cdse.search_l2a(session, _cfg(), "tok", [0, 0, 1, 1], "s", "e")
        assert scenes == []

    def test_search_failure_raises(self):
        session = FakeSession(fail_search=True)
        with pytest.raises(CdseUnavailable):
            satellite_cdse.search_l2a(session, _cfg(), "tok", [0, 0, 1, 1], "s", "e")


class TestComputeNdvi:
    def test_uniform_scene(self, tmp_path):
        b04 = tmp_path / "B04.tif"
        b08 = tmp_path / "B08.tif"
        b04.write_bytes(_band_bytes(0.1))
        b08.write_bytes(_band_bytes(0.5))
        stats = satellite_cdse.compute_ndvi(str(b04), str(b08))
        assert stats["ndvi_mean"] == pytest.approx(0.6667, abs=1e-3)
        assert stats["ndvi_min"] == pytest.approx(0.6667, abs=1e-3)
        assert stats["ndvi_max"] == pytest.approx(0.6667, abs=1e-3)
        assert stats["pct_valid_pixels"] == 100.0

    def test_nodata_pixels_masked(self, tmp_path):
        b04 = tmp_path / "B04.tif"
        b08 = tmp_path / "B08.tif"
        b04.write_bytes(_band_bytes(0.1, nodata=-9999.0))
        b08.write_bytes(_band_bytes(0.5, nodata=-9999.0))
        stats = satellite_cdse.compute_ndvi(str(b04), str(b08))
        assert stats["pct_valid_pixels"] == pytest.approx(93.75)
        assert stats["ndvi_mean"] == pytest.approx(0.6667, abs=1e-3)


class TestRetrieve:
    def test_end_to_end(self, tmp_path):
        b04 = _band_bytes(0.2)
        b08 = _band_bytes(0.8)
        session = FakeSession(
            features=[_scene_feature("S2A_E2E", "https://x/B04.tif", "https://x/B08.tif")],
            assets={"https://x/B04.tif": b04, "https://x/B08.tif": b08},
        )
        result = satellite_cdse.retrieve_ndvi(session, _cfg(), [54.0, 36.0, 54.1, 36.1], "s", "e")
        assert result["data_source"] == "real"
        assert result["index"] == "NDVI"
        assert result["value"] == pytest.approx(0.6, abs=1e-3)
        assert result["payload"]["scene_id"] == "S2A_E2E"
        assert result["payload"]["provenance"] == "CDSE Sentinel-2 L2A (10 m)"

    def test_no_scene_raises(self):
        session = FakeSession(features=[])
        with pytest.raises(CdseUnavailable):
            satellite_cdse.retrieve_ndvi(session, _cfg(), [0, 0, 1, 1], "s", "e")

    def test_config_missing_env_raises(self):
        with pytest.raises(CdseUnavailable):
            CdseConfig.from_env(env={})

    def test_build_bbox_shape(self):
        bbox = satellite_cdse.build_bbox(36.0, 54.0, half_side_km=0.5)
        assert len(bbox) == 4
        assert bbox[0] < bbox[2] and bbox[1] < bbox[3]


class TestRefreshEndpoint:
    def test_disabled_returns_503(self, monkeypatch):
        monkeypatch.setattr(get_settings(), "enable_satellite_real", "false")
        response = client.post(
            "/api/v1/mrv/satellite-refresh",
            json={
                "site_id": f"cdse-{uuid4().hex[:8]}",
                "lat": 36.5,
                "lon": 54.0,
                "start": "2026-07-01T00:00:00Z",
                "end": "2026-08-01T00:00:00Z",
            },
        )
        assert response.status_code == 503

    def test_cdse_failure_returns_502(self, monkeypatch):
        monkeypatch.setattr(get_settings(), "enable_satellite_real", "true")

        def _boom(*args, **kwargs):
            raise CdseUnavailable("no scene found")

        monkeypatch.setattr(satellite_cdse, "retrieve_ndvi", _boom)
        response = client.post(
            "/api/v1/mrv/satellite-refresh",
            json={
                "site_id": f"cdse-{uuid4().hex[:8]}",
                "lat": 36.5,
                "lon": 54.0,
                "start": "2026-07-01T00:00:00Z",
                "end": "2026-08-01T00:00:00Z",
            },
        )
        assert response.status_code == 502
        assert "CDSE retrieval failed" in response.json()["detail"]
