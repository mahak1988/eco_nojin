"""Phase 4 tests: Copernicus STAC + real band sampling (synthetic COG)."""
import asyncio

import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile

from services.satellite.copernicus import (
    CopernicusBandError,
    CopernicusClient,
    CopernicusNotConfigured,
    Scene,
    evi_from_bands,
    health_from_ndvi,
    ndvi_from_bands,
    savi_from_bands,
)


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Spectral math
# ---------------------------------------------------------------------------

def test_ndvi_healthy_vegetation():
    assert ndvi_from_bands(0.6, 0.1) == pytest.approx(0.7143, abs=1e-3)


def test_ndvi_degenerate_denominator():
    assert ndvi_from_bands(0.0, 0.0) == 0.0


def test_ndvi_rejects_out_of_range():
    with pytest.raises(ValueError):
        ndvi_from_bands(1.5, 0.2)


def test_evi_savi_range_and_health():
    assert -1.0 <= evi_from_bands(0.5, 0.2, 0.1) <= 1.0
    assert -1.0 <= savi_from_bands(0.5, 0.2) <= 1.0
    assert health_from_ndvi(0.1) == "poor"
    assert health_from_ndvi(0.8) == "good"


# ---------------------------------------------------------------------------
# Credential gating
# ---------------------------------------------------------------------------

def test_unconfigured_raises_on_all_network_paths(monkeypatch):
    monkeypatch.delenv("CDSE_CLIENT_ID", raising=False)
    monkeypatch.delenv("CDSE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("CDSE_USERNAME", raising=False)
    monkeypatch.delenv("CDSE_PASSWORD", raising=False)
    client = CopernicusClient()
    assert client.configured is False
    with pytest.raises(CopernicusNotConfigured):
        client.search_stac(35.0, 51.0)
    with pytest.raises(CopernicusNotConfigured):
        run(client.analyze_location(35.0, 51.0))


# ---------------------------------------------------------------------------
# STAC search (mocked HTTP)
# ---------------------------------------------------------------------------

class FakeSyncResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


def test_stac_search_builds_request_and_parses_items(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return FakeSyncResponse(
            200,
            {
                "features": [
                    {
                        "id": "S2A_T39SWH_20260705",
                        "properties": {"datetime": "2026-07-05T06:00:00Z", "eo:cloud_cover": 5.0},
                        "assets": {"B04": {"href": "https://x/B04.tif"}, "B08": {"href": "https://x/B08.tif"}},
                    },
                    {
                        "id": "S2A_T39SWH_20260706",
                        "properties": {"datetime": "2026-07-06T06:00:00Z", "eo:cloud_cover": 90.0},
                        "assets": {"B04": {"href": "https://x/B04b.tif"}},
                    },
                ]
            },
        )

    monkeypatch.setattr("services.satellite.copernicus.httpx.post", fake_post)
    monkeypatch.setattr(
        "services.satellite.copernicus.CopernicusClient.get_token",
        lambda self, force=False: "tok123",
    )
    client = CopernicusClient(
        client_id="cid", client_secret="csecret",
        identity_url="https://identity.test", stac_url="https://stac.test",
    )
    scenes = client.search_stac(35.0, 51.0)
    assert captured["url"].endswith("/v1/search")
    assert captured["json"]["collections"] == ["sentinel-2-l2a"]
    assert captured["headers"]["Authorization"] == "Bearer tok123"
    assert len(scenes) == 2
    assert scenes[0].is_usable is True
    assert scenes[1].is_usable is False
    assert scenes[0].assets["B04"] == "https://x/B04.tif"


# ---------------------------------------------------------------------------
# Band sampling with a synthetic in-memory COG (EPSG:4326, deterministic)
# ---------------------------------------------------------------------------

def _make_cog_4326(red_value_dn: int, nir_value_dn: int) -> dict:
    """Build tiny single-band COGs in EPSG:4326 anchored at the sample point."""
    out = {}
    for name, value in (("red", red_value_dn), ("nir", nir_value_dn)):
        arr = np.full((4, 4), value, dtype=np.uint16)
        with MemoryFile() as mem:
            with mem.open(
                driver="GTiff",
                height=4,
                width=4,
                count=1,
                dtype="uint16",
                crs="EPSG:4326",
                transform=rasterio.transform.from_origin(51.279, 35.218, 0.001, 0.001),
            ) as dst:
                dst.write(arr, 1)
            out[name] = mem.read()
    return out


class FakeStreamResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class FakeAsyncClient:
    def __init__(self, responses, timeout=None):
        self._responses = list(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, href, headers=None):
        self.calls.append(href)
        return self._responses.pop(0)


def test_sample_bands_computes_real_ndvi(monkeypatch):
    cogs = _make_cog_4326(red_value_dn=1000, nir_value_dn=6000)
    fake = FakeAsyncClient([FakeStreamResponse(cogs["red"]), FakeStreamResponse(cogs["nir"])])
    monkeypatch.setattr("services.satellite.copernicus.httpx.AsyncClient", lambda timeout=None: fake)
    monkeypatch.setattr(
        "services.satellite.copernicus.CopernicusClient.get_token",
        lambda self, force=False: "tok123",
    )
    client = CopernicusClient(
        client_id="cid", client_secret="csecret",
        identity_url="https://identity.test", stac_url="https://stac.test",
    )
    scene = Scene(
        id="S2A_1", datetime="2026-07-05T06:00:00Z", cloud_cover=5.0,
        assets={"B04": "https://x/B04.tif", "B08": "https://x/B08.tif"},
    )
    bands = run(client.sample_bands(scene, 35.218, 51.279))
    # DN 6000/10000 = 0.6 NIR, DN 1000/10000 = 0.1 RED -> NDVI ~ 0.7143
    assert bands["red"] == pytest.approx(0.1, abs=1e-3)
    assert bands["nir"] == pytest.approx(0.6, abs=1e-3)
    ndvi = ndvi_from_bands(bands["nir"], bands["red"])
    assert ndvi == pytest.approx(0.7143, abs=1e-3)


def test_sample_bands_missing_asset_raises():
    client = CopernicusClient(
        client_id="cid", client_secret="csecret",
        identity_url="https://identity.test", stac_url="https://stac.test",
    )
    scene = Scene(id="S2A_1", datetime="2026-07-05T06:00:00Z", cloud_cover=5.0, assets={})
    with pytest.raises(CopernicusBandError):
        run(client.sample_bands(scene, 35.0, 51.0))


def test_analyze_location_no_scene_is_honest(monkeypatch):
    def fake_search(latitude, longitude, start_date=None, end_date=None,
                    max_cloud_cover=20.0, max_records=5):
        return []

    monkeypatch.setattr(
        "services.satellite.copernicus.CopernicusClient.search_stac", fake_search
    )
    client = CopernicusClient(
        client_id="cid", client_secret="csecret",
        identity_url="https://identity.test", stac_url="https://stac.test",
    )
    result = run(client.analyze_location(35.0, 51.0))
    assert result["status"] == "no_scene"
    assert result["ndvi"] is None
    assert result["data_source"] == "copernicus"
