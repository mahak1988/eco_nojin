"""Integration tests for AI API endpoints."""

from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)


def test_ai_health_endpoint():
    """Verify AI health endpoint returns operational status."""
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["documents_loaded"] > 0


def test_ai_chat_endpoint():
    """Verify chat endpoint returns valid response."""
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": "What is the best C/N ratio for compost?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert len(data["sources"]) > 0
    assert data["confidence"] > 0


def test_ai_chat_short_query_rejected():
    """Verify short queries are rejected."""
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": "hi"},
    )
    assert response.status_code == 422  # Validation error
