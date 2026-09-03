"""Integration tests for the API Gateway."""

from fastapi.testclient import TestClient

from database.base import Base
from database.config import engine
from services.api_gateway.main import app

client = TestClient(app)


def setup_function():
    """Reset database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_health_check():
    """Verify that the API gateway is reachable."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"


def test_create_and_get_soil_profile():
    """Test soil profile registration and retrieval flow."""
    payload = {
        "name": "Field A - Clay Loam",
        "texture": "Clay Loam",
        "ph": 7.8,
        "ec": 2.1,
        "organic_matter": 1.8,
    }

    # Create profile
    response = client.post("/api/v1/soil/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["id"] is not None

    # Retrieve list
    response = client.get("/api/v1/soil/")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_calculate_compost_optimal():
    """Test compost formulation API with optimal inputs."""
    payload = {
        "materials": [
            {"name": "Straw", "mass_kg": 100, "carbon_content": 40.0, "nitrogen_content": 0.5},
            {"name": "Cow Manure", "mass_kg": 50, "carbon_content": 20.0, "nitrogen_content": 2.0},
        ]
    }

    response = client.post("/api/v1/materials/calculate-compost", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cn_ratio"] == 33.33
    assert data["status"] == "Optimal"
