"""Unit tests for the Copernicus CDSE client v2 (offline, no credentials)."""
import datetime

import pytest

from services.satellite.copernicus import (
    CopernicusClient,
    CopernicusFetchError,
    CopernicusNotConfigured,
)


@pytest.fixture(autouse=True)
def _no_creds(monkeypatch):
    """Guarantee the client under test is unconfigured (offline-safe)."""
    monkeypatch.delenv("CDSE_CLIENT_ID", raising=False)
    monkeypatch.delenv("CDSE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("CDSE_USERNAME", raising=False)
    monkeypatch.delenv("CDSE_PASSWORD", raising=False)


# ---------------------------------------------------------------------------
# Client config gating
# ---------------------------------------------------------------------------

def test_unconfigured_reports_false():
    assert CopernicusClient().configured is False


def test_configured_client_credentials(monkeypatch):
    monkeypatch.setenv("CDSE_CLIENT_ID", "x")
    monkeypatch.setenv("CDSE_CLIENT_SECRET", "y")
    assert CopernicusClient().configured is True


def test_configured_password_grant(monkeypatch):
    monkeypatch.setenv("CDSE_USERNAME", "u")
    monkeypatch.setenv("CDSE_PASSWORD", "p")
    assert CopernicusClient().configured is True


def test_token_raises_when_unconfigured():
    with pytest.raises(CopernicusNotConfigured):
        CopernicusClient().get_token()


def test_search_raises_when_unconfigured():
    with pytest.raises(CopernicusNotConfigured):
        CopernicusClient().search_stac(35.0, 51.0)


# ---------------------------------------------------------------------------
# Token requests (mocked HTTP)
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


def test_client_credentials_token_shape_and_cache(monkeypatch):
    calls = []

    def fake_post(url, data=None, timeout=None):
        calls.append((url, data))
        return FakeResponse(200, {"access_token": "tok123", "expires_in": 3600})

    monkeypatch.setattr("services.satellite.copernicus.httpx.post", fake_post)
    client = CopernicusClient(
        client_id="cid", client_secret="csecret",
        identity_url="https://identity.test",
    )
    assert client.get_token() == "tok123"
    assert client.get_token() == "tok123"  # cached -> single HTTP call
    assert len(calls) == 1
    url, data = calls[0]
    assert "identity.test" in url
    assert data["grant_type"] == "client_credentials"
    assert data["client_id"] == "cid"
    assert data["client_secret"] == "csecret"


def test_password_grant_token_uses_cdse_public(monkeypatch):
    calls = []

    def fake_post(url, data=None, timeout=None):
        calls.append(data)
        return FakeResponse(200, {"access_token": "tok123", "expires_in": 3600})

    monkeypatch.setattr("services.satellite.copernicus.httpx.post", fake_post)
    client = CopernicusClient(
        username="farmer", password="secret",
        identity_url="https://identity.test",
    )
    assert client.get_token() == "tok123"
    assert calls[0]["grant_type"] == "password"
    assert calls[0]["client_id"] == "cdse-public"
    assert calls[0]["username"] == "farmer"


def test_token_failure_raises_fetch_error(monkeypatch):
    def fake_post(url, data=None, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr("services.satellite.copernicus.httpx.post", fake_post)
    client = CopernicusClient(
        client_id="cid", client_secret="csecret",
        identity_url="https://identity.test",
    )
    with pytest.raises(CopernicusFetchError):
        client.get_token()


def test_stac_search_sends_auth_and_datetime_window(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return FakeResponse(200, {"features": []})

    monkeypatch.setattr("services.satellite.copernicus.httpx.post", fake_post)
    monkeypatch.setattr(
        "services.satellite.copernicus.CopernicusClient.get_token",
        lambda self, force=False: "tok123",
    )
    client = CopernicusClient(
        client_id="cid", client_secret="csecret",
        identity_url="https://identity.test", stac_url="https://stac.test",
    )
    client.search_stac(
        35.0, 51.0,
        start_date=datetime.date(2026, 7, 1),
        end_date=datetime.date(2026, 7, 10),
    )
    assert captured["url"].endswith("/v1/search")
    assert captured["headers"]["Authorization"] == "Bearer tok123"
    body = captured["json"]
    assert body["collections"] == ["sentinel-2-l2a"]
    assert "2026-07-01" in body["datetime"] and "2026-07-10" in body["datetime"]
    assert body["bbox"] == [51.0, 35.0, 51.0, 35.0]
