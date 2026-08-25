"""Integration tests for Phase-2 completion: LoRaWAN webhook, batch sync,
public dashboard, and the IoT/MQTT ingestion helpers.

Note: TELCO_WEBHOOK_KEY is injected through the settings singleton (cached at
import time), so we patch it via monkeypatch instead of relying on env order.
"""

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from engine.hydroma.config.settings import get_settings
from engine.hydroma.mrv import iot_ingest
from engine.hydroma.mrv.schemas import IoTReading

from services.api_gateway.main import app

client = TestClient(app)


def _site() -> str:
    """Return a unique site id so repeated runs never collide."""
    return f"mrv-p2c-{uuid4().hex[:12]}"


@pytest.fixture(autouse=True)
def _webhook_key(monkeypatch):
    """Set a known webhook key on the cached settings singleton."""
    monkeypatch.setattr(get_settings(), "telco_webhook_key", "test-webhook-key")


class TestLoRaWanWebhook:
    """TTN v3 webhook ingestion (level 2)."""

    def test_direct_shape_with_valid_key(self):
        site = _site()
        response = client.post(
            "/api/v1/mrv/lorawan-webhook",
            json={"site_id": site, "sensor_type": "soil_moisture", "value": 30.0, "unit": "%"},
            headers={"X-Webhook-Key": "test-webhook-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["observations"][0]["qa_status"] == "ok"

    def test_decoded_payload_shape(self):
        site = _site()
        payload = {"uplink_message": {"decoded_payload": {"site_id": site, "temp": 21.5, "soil_moisture": 42.0}}}
        response = client.post(
            "/api/v1/mrv/lorawan-webhook",
            json=payload,
            headers={"X-Webhook-Key": "test-webhook-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        types = {o["sensor_type"] for o in data["observations"]}
        assert types == {"temp", "soil_moisture"}

    def test_wrong_key_rejected(self):
        response = client.post(
            "/api/v1/mrv/lorawan-webhook",
            json={"site_id": _site(), "sensor_type": "temp", "value": 20.0, "unit": "°C"},
            headers={"X-Webhook-Key": "wrong-key"},
        )
        assert response.status_code == 401

    def test_missing_key_rejected(self):
        response = client.post(
            "/api/v1/mrv/lorawan-webhook",
            json={"site_id": _site(), "sensor_type": "temp", "value": 20.0, "unit": "°C"},
        )
        assert response.status_code == 401

    def test_unreadable_payload_rejected(self):
        response = client.post(
            "/api/v1/mrv/lorawan-webhook",
            json={"uplink_message": {"decoded_payload": {"battery": 3.9}}},
            headers={"X-Webhook-Key": "test-webhook-key"},
        )
        assert response.status_code == 422


class TestCitizenBatch:
    """Offline queue sync (level 3)."""

    def test_batch_stores_all_reports(self):
        site = _site()
        response = client.post(
            "/api/v1/mrv/citizen-reports/batch",
            json={
                "reports": [
                    {"site_id": site, "observer": "f1", "category": "pest", "note": "A"},
                    {"site_id": site, "observer": "f2", "category": "plant_growth", "note": "B"},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == 2
        assert len(data["observations"]) == 2

    def test_batch_empty_rejected(self):
        response = client.post("/api/v1/mrv/citizen-reports/batch", json={"reports": []})
        assert response.status_code == 422


class TestPublicDashboard:
    """PII-free public aggregates."""

    def test_summary_never_leaks_pii(self):
        site = _site()
        client.post(
            "/api/v1/mrv/citizen-report",
            json={"site_id": site, "observer": "farmer-secret-99", "category": "pest", "note": "private note"},
        )
        client.post(
            "/api/v1/mrv/iot-reading",
            json={"site_id": site, "sensor_type": "soil_moisture", "value": 33.0, "unit": "%"},
        )
        client.post(
            "/api/v1/mrv/satellite-index",
            json={"site_id": site, "index": "NDVI", "value": 0.62, "data_source": "simulated"},
        )
        response = client.get("/api/v1/mrv/public/dashboard-summary")
        assert response.status_code == 200
        body = response.json()
        # the summary is a global aggregate; assert invariants + our site's row
        assert body["total_observations"] >= 3
        assert set(body["by_level"]) == {"1", "2", "3"}
        assert body["by_source"]["citizen"] >= 1
        sat = next(s for s in body["latest_satellite_per_site"] if s["site_id"] == site)
        assert sat["data_source"] == "simulated"
        assert sat["index"] == "NDVI"
        # no PII anywhere in the Integerized response
        raw = json.dumps(body)
        assert "farmer-secret-99" not in raw
        assert "private note" not in raw


class TestIotIngestHelpers:
    """Unit-level checks for the shared IoT ingest helpers."""

    def test_parse_ttn_direct(self):
        readings = iot_ingest.parse_ttn_v3({"site_id": "s1", "sensor_type": "ec", "value": 2.1, "unit": "dS/m"})
        assert len(readings) == 1
        assert readings[0].sensor_type == "ec"

    def test_parse_ttn_decoded_skips_unknown(self):
        readings = iot_ingest.parse_ttn_v3(
            {"uplink_message": {"decoded_payload": {"site_id": "s1", "temp": 18.0, "voltage": 3.3}}}
        )
        assert len(readings) == 1
        assert readings[0].sensor_type == "temp"
        assert readings[0].unit == "°C"

    def test_parse_ttn_missing_site_empty(self):
        assert iot_ingest.parse_ttn_v3({"temp": 18.0}) == []

    def test_webhook_key_ok(self):
        assert iot_ingest.webhook_key_ok("abc", "abc") is True
        assert iot_ingest.webhook_key_ok("abc", "abd") is False
        assert iot_ingest.webhook_key_ok("abc", "") is False
        assert iot_ingest.webhook_key_ok(None, "abc") is False

    def test_mqtt_on_message_persists(self):
        stored: list[IoTReading] = []
        consumer = iot_ingest.MqttIotConsumer(
            broker_host="unused.invalid", store=stored.append
        )
        message = type("Msg", (), {"payload": b'{"site_id": "s1", "sensor_type": "flow", "value": 12.5, "unit": "L/s"}'})
        consumer._on_message(None, None, message)
        assert len(stored) == 1
        assert stored[0].sensor_type == "flow"

    def test_mqtt_on_message_drops_malformed(self):
        stored: list[IoTReading] = []
        consumer = iot_ingest.MqttIotConsumer(
            broker_host="unused.invalid", store=stored.append
        )
        consumer._on_message(None, None, type("Msg", (), {"payload": b"not-json"}))
        assert stored == []
