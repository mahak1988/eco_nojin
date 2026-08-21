"""Tests for Offline Sync endpoint."""

from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)


def test_sync_batch_success():
    """Verify batch sync processes items successfully."""
    payload = {
        "device_id": "test-device-123",
        "items": [
            {
                "client_id": "q_1",
                "endpoint": "/api/v1/soil/",
                "method": "POST",
                "payload": {"name": "Offline Soil", "texture": "Loam"},
                "timestamp": 1700000000000,
            },
            {
                "client_id": "q_2",
                "endpoint": "/api/v1/soil/",
                "method": "POST",
                "payload": {"name": "Offline Soil 2", "texture": "Clay"},
                "timestamp": 1700000001000,
            },
        ],
    }

    response = client.post("/api/v1/sync/batch", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "test-device-123"
    assert data["summary"]["total"] == 2
    assert data["summary"]["success"] == 2
    assert len(data["results"]) == 2


def test_sync_empty_batch_rejected():
    """Verify empty batch is rejected."""
    payload = {
        "device_id": "test-device",
        "items": [],
    }

    response = client.post("/api/v1/sync/batch", json=payload)
    assert response.status_code == 422


def test_sync_invalid_method_rejected():
    """Verify invalid HTTP method is rejected."""
    payload = {
        "device_id": "test-device",
        "items": [
            {
                "client_id": "q_1",
                "endpoint": "/api/v1/soil/",
                "method": "GET",  # Invalid - must be POST/PUT/DELETE
                "payload": {},
                "timestamp": 1700000000000,
            },
        ],
    }

    response = client.post("/api/v1/sync/batch", json=payload)
    assert response.status_code == 422


def test_sync_stats():
    """Verify sync stats endpoint."""
    response = client.get("/api/v1/sync/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_syncs" in data
    assert "unique_devices" in data


def test_sync_history():
    """Verify sync history endpoint."""
    # First sync something
    client.post(
        "/api/v1/sync/batch",
        json={
            "device_id": "history-test-device",
            "items": [
                {
                    "client_id": "q_hist_1",
                    "endpoint": "/api/v1/soil/",
                    "method": "POST",
                    "payload": {"name": "Test"},
                    "timestamp": 1700000000000,
                },
            ],
        },
    )

    response = client.get("/api/v1/sync/history/history-test-device")
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "history-test-device"
    assert data["count"] >= 1


def test_health_reports_mobile_features():
    """Verify health endpoint reports mobile features."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "inclusive_access" in data
    assert data["inclusive_access"]["web_app"] is True
    assert data["inclusive_access"]["pwa_offline"] is True
