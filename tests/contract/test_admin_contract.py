"""Contract Tests for Admin API Endpoints using Schemathesis.

Tests all admin endpoints against their OpenAPI schema.
Run with: pytest tests/contract/test_admin_contract.py -v
"""

import pytest
import schemathesis
from hypothesis import given, settings

# Create schemathesis schema from OpenAPI spec
schema = schemathesis.openapi.from_path("openapi.json")

# Configure test settings
settings.register_profile("ci", max_examples=10, deadline=None)
settings.load_profile("ci")


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_users_endpoints(case):
    """Test /api/v1/admin/users* endpoints."""
    # Only test if the path matches our admin users endpoints
    if not case.path.startswith("/api/v1/admin/users"):
        pytest.skip("Not a users endpoint")
    
    # Call the endpoint
    response = case.call()
    
    # Validate response
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_content_endpoints(case):
    """Test /api/v1/admin/content* endpoints."""
    if not case.path.startswith("/api/v1/admin/content"):
        pytest.skip("Not a content endpoint")
    
    response = case.call()
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_bots_endpoints(case):
    """Test /api/v1/admin/bots* endpoints."""
    if not case.path.startswith("/api/v1/admin/bots"):
        pytest.skip("Not a bots endpoint")
    
    response = case.call()
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_errors_endpoints(case):
    """Test /api/v1/admin/errors* endpoints."""
    if not case.path.startswith("/api/v1/admin/errors"):
        pytest.skip("Not an errors endpoint")
    
    response = case.call()
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_settings_endpoints(case):
    """Test /api/v1/admin/settings* endpoints."""
    if not case.path.startswith("/api/v1/admin/settings"):
        pytest.skip("Not a settings endpoint")
    
    response = case.call()
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_models_endpoints(case):
    """Test /api/v1/admin/models* endpoints."""
    if not case.path.startswith("/api/v1/admin/models"):
        pytest.skip("Not a models endpoint")
    
    response = case.call()
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_overview_endpoints(case):
    """Test /api/v1/admin/overview* endpoints."""
    if not case.path.startswith("/api/v1/admin/overview"):
        pytest.skip("Not an overview endpoint")
    
    response = case.call()
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
def test_admin_security_endpoints(case):
    """Test /api/v1/admin/security* endpoints."""
    if not case.path.startswith("/api/v1/admin/security"):
        pytest.skip("Not a security endpoint")
    
    response = case.call()
    case.validate_response(response)


# Test all admin endpoints with a single parametrized test
@schema.parametrize()
@settings(max_examples=3, deadline=None)
def test_all_admin_endpoints(case):
    """Test all admin endpoints."""
    # Skip non-admin paths
    if not case.path.startswith("/api/v1/admin/"):
        pytest.skip("Not an admin endpoint")
    
    # Skip paths that require specific IDs we can't generate
    if "{error_id}" in case.path or "{item_id}" in case.path or "{user_id}" in case.path or "{key}" in case.path or "{name}" in case.path:
        pytest.skip("Path requires specific ID")
    
    response = case.call()
    case.validate_response(response)


# Health endpoint test
def test_admin_health_endpoint():
    """Test the admin health endpoint separately."""
    from fastapi.testclient import TestClient
    from services.api_gateway.main import app
    
    client = TestClient(app)
    response = client.get("/api/v1/admin/overview/health")
    assert response.status_code in (200, 401, 403)  # 401/403 if auth required


if __name__ == "__main__":
    pytest.main([__file__, "-v"])