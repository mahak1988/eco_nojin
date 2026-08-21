"""Tests: SCL cloud masking (pure helpers + window sampling + cloudy path)."""
import asyncio

import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile

from services.satellite.copernicus import (
    S2_ASSET_SCL,
    CopernicusClient,
    Scene,
    clear_ratio_from_scl,
    scl_is_clear,
)


def _make_cog(values: np.ndarray, nodata: int = 0) -> bytes:
    """Build a tiny single-band COG in memory, centred on (36N, 51E) UTM 39N."""
    height, width = values.shape
    from rasterio.warp import transform

    (xs,), (ys,) = transform("EPSG:4326", "EPSG:32639", [51.0], [36.0])
    origin_x = xs - (width // 2) * 10
    origin_y = ys + (height // 2) * 10
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype=values.dtype,
            crs="EPSG:32639",
            transform=rasterio.transform.from_origin(origin_x, origin_y, 10, 10),
        ) as dst:
            dst.write(values, 1)
        return mem.read()


class TestSclHelpers:
    def test_scl_is_clear_classes(self):
        assert scl_is_clear(4) is True
        assert scl_is_clear(5) is True
        assert scl_is_clear(6) is True
        for cloudy in (0, 1, 2, 3, 7, 8, 9, 10, 11):
            assert scl_is_clear(cloudy) is False

    def test_clear_ratio_mixed(self):
        window = np.array([[4, 9, 4], [8, 4, 6], [0, 0, 5]], dtype=np.uint8)
        ratio = clear_ratio_from_scl(window)
        # valid: 7 pixels (non-zero); clear (4/5/6): 4,4,6,5 = 5 -> 5/7
        assert ratio == pytest.approx(5 / 7)

    def test_clear_ratio_all_cloud(self):
        window = np.full((3, 3), 9, dtype=np.uint8)
        assert clear_ratio_from_scl(window) == 0.0

    def test_clear_ratio_all_nodata(self):
        window = np.zeros((3, 3), dtype=np.uint8)
        assert clear_ratio_from_scl(window) is None


def _scene(assets):
    return Scene(
        id="scene-1",
        datetime="2026-01-01T09:00:00Z",
        cloud_cover=5.0,
        assets=assets,
    )


class TestSclWindowSampling:
    def test_window_sampling_and_cloudy_path(self, monkeypatch):
        client = CopernicusClient()
        # B04/B08 -> some reflectance; SCL -> mostly cloudy (value 9)
        scene = _scene(
            {
                "B04": "http://fake/B04.tif",
                "B08": "http://fake/B08.tif",
                S2_ASSET_SCL: "http://fake/SCL.tif",
            }
        )
        calls = {}

        async def fake_download(href: str, token: str) -> bytes:
            calls[href] = token
            if href.endswith("SCL.tif"):
                scl = np.full((9, 9), 9, dtype=np.uint8)  # cloud
                scl[4, 4] = 4  # center pixel clear
                return _make_cog(scl)
            vals = np.full((9, 9), 3000, dtype=np.uint16)
            return _make_cog(vals, nodata=0)

        monkeypatch.setattr(client, "_ensure_configured", lambda: None)
        monkeypatch.setattr(client, "search_stac", lambda lat, lon, **kw: [scene])
        monkeypatch.setattr(client, "_download_band", fake_download)
        monkeypatch.setattr(client, "get_token", lambda force=False: "tok")

        async def run():
            bands = await client.sample_bands(scene, 36.0, 51.0)
            assert bands["scl_clear_ratio"] is not None
            # 5x5 window around the point: only the centre pixel is clear
            assert bands["scl_clear_ratio"] == pytest.approx(1 / 25)
            result = await client.analyze_location(36.0, 51.0)
            return bands, result

        bands, result = asyncio.run(run())
        assert result["status"] == "cloudy"
        assert result["ndvi"] is None
        assert result["scl_clear_ratio"] == pytest.approx(1 / 25)
        assert result["data_source"] == "copernicus"

    def test_clear_scene_passes_through(self, monkeypatch):
        client = CopernicusClient()
        scene = _scene(
            {
                "B04": "http://fake/B04.tif",
                "B08": "http://fake/B08.tif",
                S2_ASSET_SCL: "http://fake/SCL.tif",
            }
        )

        async def fake_download(href: str, token: str) -> bytes:
            if href.endswith("SCL.tif"):
                return _make_cog(np.full((9, 9), 4, dtype=np.uint8))  # all clear
            vals = np.full((9, 9), 3000, dtype=np.uint16)
            if href.endswith("B08.tif"):
                vals = np.full((9, 9), 6000, dtype=np.uint16)
            return _make_cog(vals, nodata=0)

        monkeypatch.setattr(client, "_ensure_configured", lambda: None)
        monkeypatch.setattr(client, "search_stac", lambda lat, lon, **kw: [scene])
        monkeypatch.setattr(client, "_download_band", fake_download)
        monkeypatch.setattr(client, "get_token", lambda force=False: "tok")

        async def run():
            result = await client.analyze_location(36.0, 51.0)
            return result

        result = asyncio.run(run())
        assert result["status"] == "ok"
        assert result["ndvi"] is not None and result["ndvi"] > 0.2
        assert result["scl_clear_ratio"] == 1.0

    def test_scl_missing_means_no_masking(self, monkeypatch):
        client = CopernicusClient()
        scene = _scene({"B04": "http://fake/B04.tif", "B08": "http://fake/B08.tif"})

        async def fake_download(href: str, token: str) -> bytes:
            vals = np.full((9, 9), 3000, dtype=np.uint16)
            return _make_cog(vals, nodata=0)

        monkeypatch.setattr(client, "_ensure_configured", lambda: None)
        monkeypatch.setattr(client, "search_stac", lambda lat, lon, **kw: [scene])
        monkeypatch.setattr(client, "_download_band", fake_download)
        monkeypatch.setattr(client, "get_token", lambda force=False: "tok")

        async def run():
            result = await client.analyze_location(36.0, 51.0)
            return result

        result = asyncio.run(run())
        assert result["status"] == "ok"
        assert result["scl_clear_ratio"] is None
