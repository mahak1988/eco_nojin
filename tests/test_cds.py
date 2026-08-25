import os
"""CDS client tests (offline, mocked httpx)."""
import pytest

from services.satellite.cds import (
    CDS_API_URL,
    CdsClient,
    CdsNotConfigured,
    CdsRequestError,
    DATA_STORES,
    DataStoreClient,
    DataStoreNotConfigured,
    all_stores_status,
)


class FakeResp:
    def __init__(self, status=200, text="{}", headers=None, content=b"data"):
        self.status_code = status
        self.text = text
        self.headers = headers or {}
        self.content = content

    def json(self):
        import json

        return json.loads(self.text)

    def raise_for_status(self):
        pass


class TestConfigured:
    def test_not_configured_without_credentials(self):
        client = CdsClient(uid="", api_key="")
        assert client.configured is False
        assert client.status()["configured"] is False
        with pytest.raises(CdsNotConfigured):
            client.submit_request({"x": 1})

    def test_configured_with_credentials(self):
        client = CdsClient(uid="u", api_key = os.getenv("API_KEY", ""))
        assert client.configured is True


class TestJobFlow:
    def test_full_flow(self, monkeypatch):
        client = CdsClient(uid="u", api_key = os.getenv("API_KEY", ""), timeout=5)

        calls = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            calls["post"] = (url, json)
            return FakeResp(status=202, headers={"location": "https://cds/task/1"})

        def fake_get(url, headers=None, timeout=None):
            calls["get"] = calls.get("get", 0) + 1
            if calls["get"] <= 2:
                return FakeResp(status=202, text='{"state": "queued"}')
            return FakeResp(status=200, text='{"state": "completed"}')

        monkeypatch.setattr("services.satellite.cds.httpx.post", fake_post)
        monkeypatch.setattr("services.satellite.cds.httpx.get", fake_get)

        params = {"product_type": "reanalysis", "variable": ["2m_temperature"]}
        task_url = client.submit_request(params)
        assert task_url == "https://cds/task/1"
        assert client.poll_task(task_url) == "completed"
        assert client.download(task_url) == b"data"
        # 3 poll gets (queued, queued, completed) + 1 download get
        assert calls["get"] == 4

    def test_submit_error(self, monkeypatch):
        client = CdsClient(uid="u", api_key = os.getenv("API_KEY", ""), timeout=5)

        def fake_post(url, headers=None, json=None, timeout=None):
            return FakeResp(status=401, text="unauthorized")

        monkeypatch.setattr("services.satellite.cds.httpx.post", fake_post)
        with pytest.raises(CdsRequestError) as exc:
            client.submit_request({"x": 1})
        assert "401" in str(exc.value)

    def test_status_never_leaks_key(self):
        client = CdsClient(uid="secret-uid", api_key = os.getenv("API_KEY", ""))
        s = client.status()
        assert "secret" not in str(s).lower()
        assert s["api_url"] == CDS_API_URL


class TestDataStores:
    def test_all_stores_registered(self):
        assert set(DATA_STORES) == {"cds", "ewds", "ads"}
        for name, spec in DATA_STORES.items():
            assert spec["key_url"].startswith("https://")
            assert spec["key_url"].endswith("how-to-api")

    def test_ewds_and_ads_config(self):
        for name in ("ewds", "ads"):
            client = DataStoreClient(store=name, uid="", api_key="")
            assert client.configured is False
            with pytest.raises(DataStoreNotConfigured):
                client.submit_request({"x": 1})
            s = client.status()
            assert s["store"] == name
            assert "how-to-api" in s["key_url"]

    def test_unknown_store_rejected(self):
        with pytest.raises(ValueError):
            DataStoreClient(store="nope")

    def test_stores_status_has_sepal(self):
        out = all_stores_status()
        assert set(out["stores"]) == {"cds", "ewds", "ads", "sepal"}
        assert out["stores"]["sepal"]["key_url"] == "https://sepal.io"

    def test_data_store_job_flow(self, monkeypatch):
        client = DataStoreClient(store="ewds", uid="u", api_key = os.getenv("API_KEY", ""), timeout=5)
        calls = {"get": 0}

        def fake_post(url, headers=None, json=None, timeout=None):
            return FakeResp(status=202, headers={"location": "https://ewds/task/9"})

        def fake_get(url, headers=None, timeout=None):
            calls["get"] += 1
            return FakeResp(status=200, text='{"state": "completed"}')

        monkeypatch.setattr("services.satellite.cds.httpx.post", fake_post)
        monkeypatch.setattr("services.satellite.cds.httpx.get", fake_get)
        task = client.submit_request({"dataset": "x"})
        assert task == "https://ewds/task/9"
        assert client.poll_task(task) == "completed"
        assert client.download(task) == b"data"
