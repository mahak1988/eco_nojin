"""Integration tests for satellite API endpoints."""

from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)


def test_satellite_health():
    """Verify satellite health endpoint."""
    response = client.get("/api/v1/satellite/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "NDVI" in data["supported_indices"]


def test_analyze_farm_field():
    """Test analysis of a typical agricultural field."""
    # Example: Golestan province, Iran (agricultural area)
    payload = {
        "lat": 36.8,
        "lon": 54.4,
    }

    response = client.post("/api/v1/satellite/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "ndvi" in data
    assert "recommendation" in data
    assert -1 <= data["ndvi"] <= 1
    assert len(data["recommendation"]) > 0


def test_analyze_invalid_coords():
    """Verify validation rejects invalid coordinates."""
    payload = {
        "lat": 100.0,  # Invalid: > 90
        "lon": 54.4,
    }

    response = client.post("/api/v1/satellite/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_with_date():
    """Test analysis with specific date."""
    from datetime import date, timedelta

    target_date = (date.today() - timedelta(days=10)).isoformat()

    payload = {
        "lat": 36.8,
        "lon": 54.4,
        "analysis_date": target_date,
    }

    response = client.post("/api/v1/satellite/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_date"] == target_date
