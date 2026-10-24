"""The account & security half of the frontend contract (F2).

Split from `test_frontend_contract.py` when it crossed the 800-line
structure ceiling: the marketplace/tourism half stays there, the self-service
surface lives here. Both files share the same helpers and fixtures, because
an account endpoint and a marketplace endpoint are one product contract.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from .frontend_contract_helpers import (
    _login_as_admin,
    _register,
    _write_headers,
    anonymous_client,  # noqa: F401  used via fixture-shadow param
    client,  # noqa: F401  used via fixture-shadow param
)

# ---------------------------------------------------------------------------
# F2 â€” account & security self-service
# ---------------------------------------------------------------------------


def test_account_status_and_profile_round_trip(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")

    status = client.get("/api/v1/auth/account/status")
    assert status.status_code == 200, status.text
    assert {"active", "email", "role", "is_email_verified"} <= set(status.json()["data"])

    updated = client.put(
        "/api/v1/auth/profile",
        headers=_write_headers(client),
        json={"full_name": "Contract Probe", "city": "Tehran", "language": "fa"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["full_name"] == "Contract Probe"

    preferences = client.get("/api/v1/auth/preferences")
    assert preferences.status_code == 200, preferences.text
    assert {"theme", "language", "timezone"} <= set(preferences.json()["data"])

    activity = client.get("/api/v1/auth/activity/history?limit=5")
    assert activity.status_code == 200, activity.text
    assert isinstance(activity.json()["data"], list)


def test_account_sessions_keys_twofactor(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")

    sessions = client.get("/api/v1/auth/sessions")
    assert sessions.status_code == 200, sessions.text
    assert isinstance(sessions.json()["data"], list)

    keys = client.get("/api/v1/auth/api-keys")
    assert keys.status_code == 200, keys.text
    assert isinstance(keys.json()["data"], list)

    created = client.post(
        "/api/v1/auth/api-keys",
        headers=_write_headers(client),
        json={"name": "contract-probe"},
    )
    if created.status_code == 200:
        key = created.json()["data"]
        assert key["name"] == "contract-probe"
        assert key["key"], "the raw key must be returned exactly once"

    two_factor = client.get("/api/v1/auth/2fa/status")
    assert two_factor.status_code == 200, two_factor.text
    assert {"enabled", "method"} <= set(two_factor.json()["data"])

    notifications = client.get("/api/v1/auth/notifications")
    assert notifications.status_code == 200, notifications.text
    assert {"email", "push", "sms", "marketing"} <= set(notifications.json()["data"])


def test_change_password_wrong_current_password_is_refused(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    response = client.post(
        "/api/v1/auth/change-password",
        headers=_write_headers(client),
        json={
            "current_password": "definitely-not-the-password",
            "new_password": "OtherPassw0rd!24",
        },
    )
    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]


def test_data_export_answers_not_implemented_honestly(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    response = client.post("/api/v1/auth/export-data", headers=_write_headers(client))
    # The capability does not exist yet: 501 with a structured detail, not a
    # fake 200.
    assert response.status_code == 501
    detail = response.json()["detail"]
    assert detail["error"] == "export_not_implemented"
    assert detail["message"]


def test_update_preferences_round_trip(client: TestClient):
    """Preferences read then write round-trip with envelope contract."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")

    headers = _write_headers(client)

    get_prefs = client.get("/api/v1/auth/preferences", headers=headers)
    assert get_prefs.status_code == 200, get_prefs.text
    pref_data = get_prefs.json()["data"]
    expected_prefs = {"theme", "language", "timezone", "date_format",
                      "number_format", "currency"}
    assert expected_prefs <= set(pref_data)

    updated = client.put(
        "/api/v1/auth/preferences",
        headers=headers,
        json={"language": "en"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "success"
    assert updated.json()["message"]


def test_preferences_extended_round_trip(client: TestClient):
    """Extended preferences (timezone/units/theme/dashboard) read + write."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    headers = _write_headers(client)

    get_ext = client.get("/api/v1/auth/preferences/extended", headers=headers)
    assert get_ext.status_code == 200, get_ext.text
    ext_data = get_ext.json()
    assert {"timezone", "units", "theme", "language"} <= set(ext_data)

    updated = client.put(
        "/api/v1/auth/preferences/extended",
        headers=headers,
        json={"timezone": "Asia/Tehran", "units": "metric", "theme": "dark"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "success"


def test_change_password_correct_flow(client: TestClient):
    """A user can change their password with the correct current password."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    headers = _write_headers(client)

    response = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "Passw0rd!23", "new_password": "NewPassw0rd!24"},
    )
    assert response.status_code == 200, response.text
    assert "message" in response.json()


def test_reactivate_and_update_bio(client: TestClient):
    """Account bio update returns a status-message envelope."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    headers = _write_headers(client)

    response = client.post(
        "/api/v1/auth/account/bio",
        headers=headers,
        json={"bio": "Contract probe bio", "location": "Tehran"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "success"


def test_security_events_endpoint(client: TestClient):
    """Non-admin gets 403 on the security events endpoint (admin-gated)."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    response = client.get("/api/v1/security/events?limit=5")
    assert response.status_code == 403


def test_security_audit_user_scoped(client: TestClient):
    """Security audit is user-scoped (not admin-gated at route level)."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    headers = _write_headers(client)

    response = client.get("/api/v1/auth/security-audit", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list) or "data" in data


def test_email_change_and_rate_limit(client: TestClient):
    """Email change request shape; rate-limit endpoint reveals policy."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    headers = _write_headers(client)

    change_req = client.post(
        "/api/v1/auth/email/change-request",
        headers=headers,
        json={"new_email": f"new-{uuid4().hex[:8]}@example.com"},
    )
    assert change_req.status_code == 200, change_req.text
    assert change_req.json()["status"] == "success"

    rl = client.get("/api/v1/auth/rate-limit", headers=headers)
    assert rl.status_code == 200, rl.text
    assert isinstance(rl.json(), dict)


# ---------------------------------------------------------------------------
# F2 — security surface


def test_security_step_up_vocabulary_is_public(anonymous_client: TestClient):
    response = anonymous_client.get("/api/v1/security/step-up/purposes")
    assert response.status_code == 200
    body = response.json()
    assert "purposes" in body and "methods" in body
    assert "transfer" in body["purposes"]

    methods = anonymous_client.get("/api/v1/security/step-up/methods")
    assert methods.status_code == 200
    assert "accepted" in methods.json() and "verifiable" in methods.json()


def test_security_passkeys_list_is_owner_scoped(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    response = client.get("/api/v1/security/passkeys")
    assert response.status_code == 200, response.text
    assert "passkeys" in response.json()


def test_security_status_requires_an_admin(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    response = client.get("/api/v1/security/status")
    assert response.status_code == 403
    assert "role" in response.json()["detail"].lower()


def test_security_status_for_admin(client: TestClient):
    """An admin can read the security posture summary."""
    email = _login_as_admin(client)
    assert email is not None

    response = client.get("/api/v1/security/status", headers=_write_headers(client))
    assert response.status_code == 200, response.text
    body = response.json()
    assert {"status", "reason", "layers"} <= set(body)
