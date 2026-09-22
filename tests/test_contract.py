"""
Contract tests for Eco Nojin API using schemathesis.

Tests the OpenAPI schema compliance for sync and realtime endpoints.
Run with: pytest tests/test_contract.py -v
"""

import pytest
import schemathesis

# Load the OpenAPI schema
schema = schemathesis.openapi.from_path("D:/eco_nojin/openapi_schema.json")


# Test specific endpoints with direct calls (more reliable than schemathesis parametrize)
def test_sync_status_endpoint():
    """Test /api/v1/sync/status endpoint specifically."""
    from fastapi.testclient import TestClient
    import sys

    sys.path.insert(0, "D:/eco_nojin")
    from services.api_gateway.main import app

    client = TestClient(app)
    response = client.get("/api/v1/sync/status")

    assert response.status_code == 200
    data = response.json()

    # Validate required fields per schema
    assert "status" in data
    assert "mode" in data
    assert "cloud" in data
    assert "local_pending_events" in data
    assert "supabase_connected" in data
    assert "supabase_error" in data
    assert "note" in data

    # Validate types
    assert isinstance(data["status"], str)
    assert isinstance(data["mode"], str)
    assert isinstance(data["cloud"], str)
    assert isinstance(data["local_pending_events"], int)
    assert isinstance(data["supabase_connected"], bool)
    assert data["supabase_error"] is None or isinstance(data["supabase_error"], str)
    assert isinstance(data["note"], str)


def test_sync_trigger_endpoint():
    """Test /api/v1/sync/trigger endpoint specifically."""
    from fastapi.testclient import TestClient
    import sys

    sys.path.insert(0, "D:/eco_nojin")
    from services.api_gateway.main import app

    client = TestClient(app)
    response = client.post("/api/v1/sync/trigger")

    # Should return 200 (ok) or 503 (Supabase unavailable)
    assert response.status_code in (200, 503)

    if response.status_code == 200:
        data = response.json()
        assert "ok" in data
        assert "synced" in data
        assert "failed" in data
        assert "total_pending" in data
        assert isinstance(data["ok"], bool)
        assert isinstance(data["synced"], int)
        assert isinstance(data["failed"], int)
        assert isinstance(data["total_pending"], int)


def test_sync_pending_endpoint():
    """Test /api/v1/sync/pending endpoint specifically."""
    from fastapi.testclient import TestClient
    import sys

    sys.path.insert(0, "D:/eco_nojin")
    from services.api_gateway.main import app

    client = TestClient(app)
    response = client.get("/api/v1/sync/pending")

    assert response.status_code == 200
    data = response.json()

    assert "ok" in data
    assert "count" in data
    assert "events" in data
    assert isinstance(data["ok"], bool)
    assert isinstance(data["count"], int)
    assert isinstance(data["events"], list)


def test_realtime_health_endpoint():
    """Test /api/v1/realtime/health endpoint specifically."""
    from fastapi.testclient import TestClient
    import sys

    sys.path.insert(0, "D:/eco_nojin")
    from services.api_gateway.main import app

    client = TestClient(app)
    response = client.get("/api/v1/realtime/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "service" in data
    assert data["status"] == "ok"
    assert data["service"] == "realtime-sse"


def test_realtime_stream_validation():
    """Test /api/v1/realtime/stream validates user_key format."""
    from fastapi.testclient import TestClient
    import sys

    sys.path.insert(0, "D:/eco_nojin")
    from services.api_gateway.main import app

    client = TestClient(app)

    # Invalid user_key (too short)
    response = client.get("/api/v1/realtime/stream", params={"user_key": "short"})
    assert response.status_code == 400
    assert "Invalid user key format" in response.json()["detail"]

    # Invalid user_key (special chars)
    response = client.get("/api/v1/realtime/stream", params={"user_key": "user@domain"})
    assert response.status_code == 400

    # Valid user_key format (alphanumeric, underscore, hyphen, 8+ chars)
    # Note: This would return streaming response, hard to test with TestClient


def test_openapi_schema_validity():
    """Test that the OpenAPI schema itself is valid."""
    import json

    with open("D:/eco_nojin/openapi_schema.json") as f:
        schema = json.load(f)

    # Basic structure validation
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert "components" in schema

    # Check our new endpoints exist
    assert "/api/v1/sync/status" in schema["paths"]
    assert "/api/v1/sync/trigger" in schema["paths"]
    assert "/api/v1/sync/pending" in schema["paths"]
    assert "/api/v1/realtime/health" in schema["paths"]
    assert "/api/v1/realtime/stream" in schema["paths"]

    # Check they have proper response schemas
    for path in [
        "/api/v1/sync/status",
        "/api/v1/sync/trigger",
        "/api/v1/sync/pending",
        "/api/v1/realtime/health",
        "/api/v1/realtime/stream",
    ]:
        path_obj = schema["paths"][path]
        for method, method_obj in path_obj.items():
            assert "responses" in method_obj
            assert "200" in method_obj["responses"] or "400" in method_obj["responses"]


def test_schemathesis_schema_loading():
    """Test that schemathesis can load and parse the schema."""
    # This validates the schema is parseable by schemathesis
    assert schema is not None
    assert hasattr(schema, "get_all_operations")

    # Get all operations from schema (wrapped in Ok results)
    operations = list(schema.get_all_operations())
    assert len(operations) > 0

    # Extract actual APIOperation objects
    op_paths = {op.ok().path for op in operations}
    assert "/api/v1/sync/status" in op_paths
    assert "/api/v1/sync/trigger" in op_paths
    assert "/api/v1/sync/pending" in op_paths
    assert "/api/v1/realtime/health" in op_paths
    assert "/api/v1/realtime/stream" in op_paths


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
