"""Phase 1 security tests - C1: /auth/seed-demo hard guard."""

import uuid

import pytest


DEMO_EMAIL = "farmer@test.com"
PASSWORD = "SeedGuardPass123"  # nosec (مقدار ساختگی تست)


def _ensure_demo_account(client) -> None:
    """Make sure the demo email exists with our known password."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": DEMO_EMAIL,
            "full_name": "Seed Guard",
            "password": PASSWORD,
            "accept_tos": True,
            "accept_privacy": True,
        },
    )
    if r.status_code != 200:
        r = client.post(
            "/api/v1/auth/login",
            json={"email": DEMO_EMAIL, "password": PASSWORD},
        )
        if r.status_code != 200:
            pytest.skip("demo account exists with an unknown password")


def _login(client) -> int:
    return client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": PASSWORD},
    ).status_code


def test_seed_demo_disabled_without_optin(client, monkeypatch):
    """Without ECO_NOJIN_ALLOW_SEED=1 the endpoint must 404 even in development."""
    monkeypatch.delenv("ECO_NOJIN_ALLOW_SEED", raising=False)
    response = client.post("/api/v1/auth/seed-demo")
    assert response.status_code == 404


def test_seed_demo_never_overwrites_existing_account(client, monkeypatch):
    """With the opt-in flag, existing accounts keep their password/role."""
    monkeypatch.setenv("ECO_NOJIN_ALLOW_SEED", "1")
    _ensure_demo_account(client)
    assert _login(client) == 200

    response = client.post("/api/v1/auth/seed-demo")
    assert response.status_code == 200
    data = response.json()["data"]
    # No credentials are ever returned anymore.
    assert "credentials" not in (data or {})

    # The pre-existing account's password was not reset.
    assert _login(client) == 200
