"""Tests for satellite data providers."""

from unittest.mock import MagicMock, patch

import numpy as np

from engine.hydroma.satellite.providers.base import SatelliteProvider, SatelliteTile
from engine.hydroma.satellite.providers.earth_search import _CLOUD_SCL_CLASSES, EarthSearchProvider


class ConcreteProvider(SatelliteProvider):
    """Concrete implementation for testing abstract base."""

    @property
    def available_bands(self):
        return ["red", "green", "blue"]

    def search(self, lat, lon, start_date, end_date, max_cloud_cover=20.0, limit=10):
        return []

    def fetch_tile(self, item_id):
        return None


class TestSatelliteTile:
    """Tests for SatelliteTile dataclass."""

    def test_defaults(self):
        tile = SatelliteTile(
            provider="test",
            collection="test-collection",
            datetime=MagicMock(),
            bbox=(0, 0, 1, 1),
            cloud_cover=10.0,
            bands={},
        )
        assert tile.crs == "EPSG:4326"
        assert tile.data_source == "real"
        assert tile.quality_flags is None

    def test_custom_data_source(self):
        tile = SatelliteTile(
            provider="test",
            collection="test-collection",
            datetime=MagicMock(),
            bbox=(0, 0, 1, 1),
            cloud_cover=10.0,
            bands={},
            data_source="simulated",
        )
        assert tile.data_source == "simulated"

    def test_quality_flags(self):
        flags = {"downloaded_bands": ["red"], "fallback_bands": []}
        tile = SatelliteTile(
            provider="test",
            collection="test-collection",
            datetime=MagicMock(),
            bbox=(0, 0, 1, 1),
            cloud_cover=10.0,
            bands={},
            quality_flags=flags,
        )
        assert tile.quality_flags == flags


class TestEarthSearchProviderSearch:
    """Tests for EarthSearchProvider.search()."""

    def setup_method(self):
        self.provider = EarthSearchProvider()

    @patch("engine.hydroma.satellite.providers.earth_search.requests.post")
    def test_search_returns_features(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": [{"id": "item1"}]}
        mock_post.return_value = mock_response

        results = self.provider.search(36.0, 54.0, MagicMock(), MagicMock())
        assert len(results) == 1
        assert results[0]["id"] == "item1"

    @patch("engine.hydroma.satellite.providers.earth_search.requests.post")
    def test_search_handles_network_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.RequestException("network error")
        results = self.provider.search(36.0, 54.0, MagicMock(), MagicMock())
        assert results == []


class TestEarthSearchProviderCloudMask:
    """Tests for cloud mask logic."""

    def setup_method(self):
        self.provider = EarthSearchProvider()

    def test_cloud_scl_classes(self):
        assert 0 in _CLOUD_SCL_CLASSES
        assert 3 in _CLOUD_SCL_CLASSES
        assert 8 in _CLOUD_SCL_CLASSES
        assert 9 in _CLOUD_SCL_CLASSES
        assert 10 in _CLOUD_SCL_CLASSES
        assert 11 in _CLOUD_SCL_CLASSES
        assert 4 not in _CLOUD_SCL_CLASSES  # vegetation

    @patch.object(EarthSearchProvider, "_download_asset")
    def test_build_cloud_mask_success(self, mock_download):
        mock_download.return_value = np.array([[0, 3], [8, 4]], dtype=np.int16)
        assets = {"scl": {"href": "http://example.com/scl.tif"}}
        bands = {"red": np.ones((2, 2))}
        mask = self.provider._build_cloud_mask(assets, bands)
        assert mask is not None
        assert mask[0, 0] is np.True_  # class 0 = no data
        assert mask[0, 1] is np.True_  # class 3 = cloud shadow
        assert mask[1, 0] is np.True_  # class 8 = cloud medium prob
        assert mask[1, 1] is np.False_  # class 4 = vegetation

    @patch.object(EarthSearchProvider, "_download_asset")
    def test_build_cloud_mask_no_scl_asset(self, mock_download):
        assets = {"red": {"href": "http://example.com/red.tif"}}
        bands = {"red": np.ones((2, 2))}
        mask = self.provider._build_cloud_mask(assets, bands)
        assert mask is None

    @patch.object(EarthSearchProvider, "_download_asset")
    def test_build_cloud_mask_download_fails(self, mock_download):
        mock_download.side_effect = RuntimeError("download failed")
        assets = {"scl": {"href": "http://example.com/scl.tif"}}
        bands = {"red": np.ones((2, 2))}
        mask = self.provider._build_cloud_mask(assets, bands)
        assert mask is None


class TestEarthSearchProviderBandDownload:
    """Tests for band download and fallback logic."""

    def setup_method(self):
        self.provider = EarthSearchProvider()

    @patch.object(EarthSearchProvider, "_download_asset")
    def test_download_bands_success(self, mock_download):
        mock_download.return_value = np.ones((64, 64), dtype=np.float32)
        assets = {
            "red": {"href": "http://example.com/red.tif"},
            "green": {"href": "http://example.com/green.tif"},
            "blue": {"href": "http://example.com/blue.tif"},
        }
        bands, data_source, flags = self.provider._download_bands(assets, "test-item")
        assert data_source == "real"
        assert "red" in flags["downloaded_bands"]
        assert "green" in flags["downloaded_bands"]
        assert "blue" in flags["downloaded_bands"]
        assert flags["fallback_bands"] == []
        assert bands["red"].shape == (64, 64)

    @patch.object(EarthSearchProvider, "_download_asset")
    def test_download_bands_partial_failure(self, mock_download):
        def side_effect(href):
            if "red" in href:
                return np.ones((64, 64), dtype=np.float32)
            raise RuntimeError("download failed")

        mock_download.side_effect = side_effect
        assets = {
            "red": {"href": "http://example.com/red.tif"},
            "green": {"href": "http://example.com/green.tif"},
        }
        bands, _data_source, flags = self.provider._download_bands(assets, "test-item")
        assert "red" in flags["downloaded_bands"]
        assert "green" in flags["fallback_bands"]
        assert bands["red"].shape == (64, 64)
        assert bands["green"].shape == (64, 64)

    @patch.object(EarthSearchProvider, "_download_asset")
    def test_download_bands_all_failed(self, mock_download):
        mock_download.side_effect = RuntimeError("all failed")
        assets = {
            "red": {"href": "http://example.com/red.tif"},
        }
        bands, data_source, _flags = self.provider._download_bands(assets, "test-item")
        assert bands is None
        assert data_source == "simulated"


class TestEarthSearchProviderFetchTile:
    """Tests for fetch_tile integration."""

    def setup_method(self):
        self.provider = EarthSearchProvider()

    @patch.object(EarthSearchProvider, "_get_item")
    def test_fetch_tile_item_not_found(self, mock_get_item):
        mock_get_item.return_value = None
        tile = self.provider.fetch_tile("nonexistent-id")
        assert tile is not None
        assert tile.data_source == "simulated"

    @patch.object(EarthSearchProvider, "_get_item")
    @patch.object(EarthSearchProvider, "_download_bands")
    def test_fetch_tile_propagates_quality_flags(self, mock_download_bands, mock_get_item):
        mock_get_item.return_value = {
            "id": "test-id",
            "bbox": [54, 36, 55, 37],
            "properties": {"eo:cloud_cover": 5.0, "datetime": "2024-01-01T00:00:00Z"},
            "assets": {},
        }
        mock_download_bands.return_value = (
            {"red": np.ones((64, 64))},
            "real",
            {
                "downloaded_bands": ["red"],
                "fallback_bands": [],
                "real_download": True,
                "cloud_masked": False,
                "scl_available": False,
            },
        )
        tile = self.provider.fetch_tile("test-id")
        assert tile is not None
        assert tile.data_source == "real"
        assert tile.quality_flags is not None
        assert tile.quality_flags["real_download"] is True
