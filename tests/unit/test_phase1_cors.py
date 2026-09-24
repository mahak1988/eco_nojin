"""Phase 1 security tests - H1: CORS hardening."""

from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)


def test_no_acao_header_for_unknown_origin():
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") is None


def test_preflight_allowed_origin_still_works():
    r = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_preflight_disallowed_origin_gets_no_acao():
    r = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert r.headers.get("access-control-allow-origin") in (None, "")
