"""Tests for the Copernicus Climate Data Store client.

The client is *optional*: without ``COPERNICUS_CDS_API_KEY`` it has no
backend, and the tests pin that it says so rather than pretending to serve
data.
"""


import pytest

from services.data_sources import copernicus_cds
from services.data_sources.copernicus_cds import CopernicusCDSClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("COPERNICUS_CDS_API_KEY", raising=False)
    return CopernicusCDSClient()


class TestConstruction:
    """Tests for the client's construction."""

    def test_without_a_key_the_client_is_unavailable(self, client):
        assert client.is_available is False

    def test_the_api_url_has_a_default(self, client):
        assert client.api_url.startswith("https://")

    def test_the_api_url_can_be_overridden(self, monkeypatch):
        monkeypatch.delenv("COPERNICUS_CDS_API_KEY", raising=False)
        custom = CopernicusCDSClient(api_url="https://example.test/api")
        assert custom.api_url == "https://example.test/api"

    def test_an_explicit_key_is_stored(self, monkeypatch):
        monkeypatch.delenv("COPERNICUS_CDS_API_KEY", raising=False)
        custom = CopernicusCDSClient(api_key="secret")
        assert custom.api_key == "secret"


class TestCacheKey:
    """Tests for the cache key."""

    def test_the_key_is_stable(self, client):
        a = client._cache_key("era5-land", {"year": 2024, "month": 1})
        b = client._cache_key("era5-land", {"year": 2024, "month": 1})
        assert a == b

    def test_different_parameters_give_different_keys(self, client):
        a = client._cache_key("era5-land", {"year": 2024})
        b = client._cache_key("era5-land", {"year": 2025})
        assert a != b

    def test_a_different_dataset_gives_a_different_key(self, client):
        a = client._cache_key("era5-land", {"year": 2024})
        b = client._cache_key("soil-moisture", {"year": 2024})
        assert a != b

    def test_the_key_is_a_hex_digest(self, client):
        key = client._cache_key("era5-land", {"year": 2024})
        assert len(key) == 64
        int(key, 16)  # raises if it is not hex


class TestCacheFreshness:
    """Tests for the on-disk cache."""

    def test_an_absent_file_is_not_cached(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(copernicus_cds, "CACHE_DIR", tmp_path)
        assert client._is_cached("nothing-here") is False

    def test_a_fresh_file_is_cached(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(copernicus_cds, "CACHE_DIR", tmp_path)
        key = client._cache_key("era5-land", {"year": 2024})
        path = client._get_cache_path(key)
        path.write_bytes(b"data")
        assert client._is_cached(key) is True

    def test_a_stale_file_is_not_cached(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(copernicus_cds, "CACHE_DIR", tmp_path)
        import os
        import time

        key = client._cache_key("era5-land", {"year": 2024})
        path = client._get_cache_path(key)
        path.write_bytes(b"data")
        # 48 hours old, and the cache only lives for 24.
        old = time.time() - 48 * 3600
        os.utime(path, (old, old))
        assert client._is_cached(key, max_age_hours=24) is False

    def test_the_cache_path_is_under_the_cache_dir(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(copernicus_cds, "CACHE_DIR", tmp_path)
        path = client._get_cache_path("abc")
        assert path.parent == tmp_path
        assert path.suffix == ".nc"
