"""Contract Tests for Admin API Endpoints.

Tests admin endpoints against their OpenAPI schema using FastAPI TestClient.
Run with: pytest tests/contract/test_admin_contract.py -v
"""

import pytest
from fastapi.testclient import TestClient
from services.api_gateway.main import app

client = TestClient(app)


def test_openapi_schema_valid():
    """Test that OpenAPI schema is valid and contains admin endpoints."""
    schema = app.openapi()
    assert "openapi" in schema
    assert "paths" in schema
    
    # Check admin endpoints exist in schema
    admin_paths = [p for p in schema["paths"] if p.startswith("/api/v1/admin/")]
    assert len(admin_paths) > 0, "No admin endpoints found in OpenAPI schema"
    
    # Check key admin endpoints
    expected_endpoints = [
        "/api/v1/admin/overview",
        "/api/v1/admin/overview/health",
        "/api/v1/admin/overview/metrics",
        "/api/v1/admin/security/logins",
        "/api/v1/admin/security/audit",
        "/api/v1/admin/users",
        "/api/v1/admin/content",
        "/api/v1/admin/bots",
        "/api/v1/admin/errors",
        "/api/v1/admin/settings",
        "/api/v1/admin/models",
    ]
    
    for endpoint in expected_endpoints:
        assert endpoint in schema["paths"], f"Missing endpoint in schema: {endpoint}"


def test_admin_health_endpoint():
    """Test the admin health endpoint."""
    response = client.get("/api/v1/admin/overview/health")
    assert response.status_code in (200, 401, 403)  # 401/403 if auth required
    
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data["status"] in ("operational", "degraded")


def test_admin_overview_endpoint():
    """Test the admin overview endpoint."""
    response = client.get("/api/v1/admin/overview")
    assert response.status_code in (200, 401, 403, 422)  # 422 if validation error


def test_admin_security_endpoint():
    """Test the admin security audit endpoint."""
    response = client.get("/api/v1/admin/security/audit")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_users_endpoint():
    """Test the admin users list endpoint."""
    response = client.get("/api/v1/admin/users")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_content_endpoint():
    """Test the admin content list endpoint."""
    response = client.get("/api/v1/admin/content")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_bots_endpoint():
    """Test the admin bots list endpoint."""
    response = client.get("/api/v1/admin/bots")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_errors_endpoint():
    """Test the admin errors list endpoint."""
    response = client.get("/api/v1/admin/errors")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_settings_endpoint():
    """Test the admin settings list endpoint."""
    response = client.get("/api/v1/admin/settings")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_models_endpoint():
    """Test the admin models list endpoint."""
    response = client.get("/api/v1/admin/models")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_overview_metrics_endpoint():
    """Test the admin overview metrics endpoint."""
    response = client.get("/api/v1/admin/overview/metrics")
    assert response.status_code in (200, 401, 403, 422)


def test_admin_security_logins_endpoint():
    """Test the admin security logins endpoint."""
    response = client.get("/api/v1/admin/security/logins")
    assert response.status_code in (200, 401, 403, 422)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])