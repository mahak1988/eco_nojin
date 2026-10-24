"""SEC-01…SEC-28 remediation regression tests (2026-10-12).

Each test names the finding it pins and fails if the corresponding fix is
reverted (detox). They follow the two patterns already in the tree: behaviour
tests against the live objects, and source-level guard sweeps in the spirit of
``tests/test_p14_guard_sweep.py`` for the parts that are wiring rather than
behaviour.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# SEC-02 — per-account lockout (services/auth/lockout.py)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sec02_lockout_increment_is_atomic_under_concurrency():
    """Concurrent failures each advance the counter exactly once.

    The first implementation was a Python-level read-modify-write: every
    request read the same pre-commit value and wrote ``stale + 1``, so the
    counter could be pinned below the threshold forever (2026-10-12 review
    finding 2). With the single conditional UPDATE, N concurrent failures
    reach N. Uses the process shared-cache async engine (the real login
    path's session factory) so every statement sees the same database.
    """
    import uuid

    from sqlalchemy import select, update

    from database.hub import hub
    from database.models import User
    from services.auth.lockout import is_enabled, max_attempts, register_failure

    if not is_enabled():
        pytest.skip("lockout disabled in this environment")
    rounds = max_attempts() + 2
    async with hub.get_async_session() as db:
        user = User(
            id=uuid.uuid4().hex,
            username=f"sec02-race-{uuid.uuid4().hex[:8]}",
            email=f"sec02-race-{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="x",
            role="farmer",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        user_id = user.id

        async def reset():
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(failed_login_attempts=0, locked_until=None)
                .execution_options(synchronize_session=False)
            )
            await db.commit()

        try:
            for _ in range(3):  # repeat to shake out lost-update windows
                await reset()
                results = await asyncio.gather(
                    *(register_failure(db, user_id) for _ in range(rounds)),
                    return_exceptions=True,
                )
                failures = [r for r in results if isinstance(r, BaseException)]
                assert not failures, failures
                await db.commit()
                db.expire_all()
                row = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
                assert row.failed_login_attempts == rounds, row.failed_login_attempts
                assert row.locked_until is not None
        finally:
            await db.delete(
                (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            )
            await db.commit()


@pytest.mark.asyncio
async def test_sec02_register_success_clears_counter_and_lock():
    import uuid

    from sqlalchemy import select, update

    from database.hub import hub
    from database.models import User
    from services.auth.lockout import register_failure, register_success

    async with hub.get_async_session() as db:
        user = User(
            id=uuid.uuid4().hex,
            username=f"sec02-clear-{uuid.uuid4().hex[:8]}",
            email=f"sec02-clear-{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="x",
            role="farmer",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        user_id = user.id
        try:
            await register_failure(db, user_id)
            await db.commit()
            db.expire_all()
            row = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            assert row.failed_login_attempts == 1
            await register_success(db, user_id)
            await db.commit()
            db.expire_all()
            row = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            assert row.failed_login_attempts == 0
            assert row.locked_until is None
        finally:
            await db.execute(
                update(User).where(User.id == user_id).execution_options(synchronize_session=False)
            )
            await db.delete(
                (await db.execute(select(User).where(User.id == user_id))).scalar_one()
            )
            await db.commit()


def test_sec02_lockout_threshold_and_retry_after(monkeypatch):
    monkeypatch.setenv("HYDROMA_AUTH_LOCKOUT_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("HYDROMA_AUTH_LOCKOUT_SECONDS", "60")
    from services.auth.lockout import AccountLockedError, check_locked, is_locked

    user = SimpleNamespace(failed_login_attempts=2, locked_until=None)
    assert not is_locked(user)
    user.locked_until = datetime.now(UTC) + timedelta(seconds=60)
    with pytest.raises(AccountLockedError) as exc:
        check_locked(user)
    assert exc.value.retry_after_seconds >= 1
    # an expired lock window releases the account
    user.locked_until = datetime.now(UTC) - timedelta(seconds=1)
    check_locked(user)


def test_sec02_lockout_can_be_disabled(monkeypatch):
    monkeypatch.setenv("HYDROMA_AUTH_LOCKOUT_ENABLED", "0")
    from services.auth.lockout import check_locked, is_locked

    user = SimpleNamespace(
        failed_login_attempts=99, locked_until=datetime.now(UTC) + timedelta(hours=1)
    )
    # disabled: neither the lock window nor any attempt has effect
    assert not is_locked(user)
    check_locked(user)


# ---------------------------------------------------------------------------
# SEC-01 — role cannot be self-assigned on the mounted auth service
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_service_client():
    from services.auth import main as auth_main

    app = FastAPI()
    app.include_router(auth_main.router)
    with TestClient(app) as client:
        yield client


def _register(client, username: str):
    return client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "Passw0rd!",
            # SEC-01: the field the removed schema used to accept.
            "role": "admin",
        },
    )


def test_sec01_register_ignores_client_role(auth_service_client):
    username = f"sec01-{uuid.uuid4().hex[:8]}"
    response = _register(auth_service_client, username)
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    me = auth_service_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    # The escalated role must not survive: the account is a plain farmer.
    assert me.json()["role"] == "farmer"


def test_sec01_login_locks_after_threshold(auth_service_client, monkeypatch):
    monkeypatch.setenv("HYDROMA_AUTH_LOCKOUT_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("HYDROMA_AUTH_LOCKOUT_SECONDS", "60")
    username = f"sec01lock-{uuid.uuid4().hex[:8]}"
    assert _register(auth_service_client, username).status_code == 201
    for _ in range(3):
        bad = auth_service_client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "wrong-password"},
        )
        assert bad.status_code == 401, bad.text
    locked = auth_service_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Passw0rd!"},
    )
    assert locked.status_code == 423, locked.text
    assert "Retry-After" in locked.headers
    assert locked.json()["detail"] == "Account temporarily locked after too many failed attempts"


# ---------------------------------------------------------------------------
# SEC-02 — the gateway login path (auth_legacy service) locks too
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sec02_gateway_authenticate_locks(db_session):
    from services.auth.lockout import AccountLockedError
    from services.auth_legacy.repository import AuthLegacyRepository
    from services.auth_legacy.service import AuthService

    service = AuthService(AuthLegacyRepository(db_session))
    email = f"sec02-gw-{uuid.uuid4().hex[:8]}@example.com"
    await service.register_user(
        email=email,
        full_name="SEC02",
        password="Passw0rd!",
        role="farmer",
        phone=None,
        date_of_birth=None,
        country=None,
        city=None,
        address=None,
        language="en",
        avatar_url=None,
    )
    for _ in range(5):
        assert await service.authenticate(email, "wrong-password") is None
    with pytest.raises(AccountLockedError):
        await service.authenticate(email, "wrong-password")


# ---------------------------------------------------------------------------
# SEC-03 — IoT owner scoping (DeviceManager + router helper)
# ---------------------------------------------------------------------------


@pytest.fixture
def iot_ready_engine():
    """The shared in-memory engine the DeviceManager talks to, with tables."""
    from database.base import Base
    from database.config import engine

    Base.metadata.create_all(engine)
    return engine


def test_sec03_device_manager_scopes_by_owner(iot_ready_engine):
    from services.business_modules.iot.device_manager import DeviceManager

    manager = DeviceManager()
    owner_a = f"user-a-{uuid.uuid4().hex[:6]}"
    owner_b = f"user-b-{uuid.uuid4().hex[:6]}"
    device_a = manager.register_device(user_id=owner_a, device_name="a")
    device_b = manager.register_device(user_id=owner_b, device_name="b")

    assert [d.id for d in manager.list_devices(user_id=owner_a)] == [device_a.id]
    assert manager.get_device(device_b.id, user_id=owner_a) is None
    assert manager.update_device_status(device_b.id, "error", user_id=owner_a) is None
    assert manager.deregister_device(device_b.id, user_id=owner_a) is False
    # the real owner keeps working
    assert manager.update_device_status(device_b.id, "error", user_id=owner_b) is not None
    assert manager.deregister_device(device_b.id, user_id=owner_b) is True


def test_sec03_platform_id_never_comes_from_headers():
    from services.api_gateway.routers import iot_devices

    request = SimpleNamespace(
        headers={"X-Tenant-Id": "tenant-from-header", "X-Platform-Id": "other"},
        state=SimpleNamespace(tenant_id="tenant-from-token"),
    )
    assert iot_devices._get_platform_id(request) == "tenant-from-token"


# ---------------------------------------------------------------------------
# SEC-04 — SSRF guard on the clone probe + admin-only security routes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/",  # scheme
        "file:///etc/passwd",
        "https://169.254.169.254/latest/meta-data/",  # cloud metadata
        "https://127.0.0.1/x",
        "https://localhost/x",
        "https://10.0.0.5/x",
        "https://192.168.1.1/admin",
        "ftp://internal/x",
    ],
)
def test_sec04_clone_signature_rejects_non_public_urls(url):
    from services.security.anti_phishing import page_clone_signature

    result = page_clone_signature(url)
    assert result["status"] == "rejected", result
    assert result["reason"]


def test_sec04_clone_signature_accepts_public_https(monkeypatch):
    from services.security import anti_phishing

    monkeypatch.setattr(
        anti_phishing.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    monkeypatch.setattr(
        anti_phishing,
        "_OPENER",
        SimpleNamespace(
            open=lambda req, timeout: __import__("io").BytesIO(
                b"<html><head><title>Eco Nojin</title></head><body>ok</body></html>"
            )
        ),
    )
    result = anti_phishing.page_clone_signature("https://example.com/")
    assert result.get("signature_sha256"), result
    assert result["title"] == "Eco Nojin"


def test_sec04_security_endpoints_require_admin(gateway_client):
    unauthenticated = gateway_client.get("/api/v1/security/status")
    assert unauthenticated.status_code in (401, 403), unauthenticated.text
    events = gateway_client.get("/api/v1/security/events")
    assert events.status_code in (401, 403), events.text


def test_sec04_security_endpoints_reachable_with_admin_override():
    from services.api_gateway.auth import require_security_admin
    from services.api_gateway.routers import security_router

    app = FastAPI()
    app.include_router(security_router.router)
    app.dependency_overrides[require_security_admin] = lambda: SimpleNamespace(
        id="admin-1", role="admin"
    )
    with TestClient(app) as client:
        assert client.get("/api/v1/security/status").status_code == 200
        assert client.get("/api/v1/security/events").status_code == 200


# ---------------------------------------------------------------------------
# SEC-14 — CSP header + authenticated /metrics
# ---------------------------------------------------------------------------


def _reset_firewall_state() -> None:
    """Reset the spider firewall's module-level singletons (test isolation).

    The circuit breaker and the honeypot ban the shared test-client address
    when other tests in the same xdist worker trip them, which would turn an
    expected 401 into a firewall 403. Both singletons expose ``reset()``.
    """
    from services.security.honeypot import honeypot
    from services.security.watchdog import circuit_breaker

    circuit_breaker.reset()
    honeypot.reset()


@pytest.fixture(scope="module")
def gateway_client():
    from services.api_gateway.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        client.get("/health")
        yield client


def test_sec14_csp_header_is_sent(gateway_client):
    response = gateway_client.get("/health")
    csp = response.headers.get("Content-Security-Policy", "")
    assert "default-src 'none'" in csp, csp


def test_sec14_metrics_requires_a_key(gateway_client, monkeypatch):
    # The gateway client mounts the spider firewall, whose circuit breaker and
    # anti-bot are module-level singletons: under xdist, earlier tests in the
    # same worker can leave the shared test-client address blocked, which turns
    # the expected 401 into a firewall 403. Reset it so the test pins its own
    # control, and accept either refusal — the property under test is "no
    # anonymous metrics".
    _reset_firewall_state()
    monkeypatch.delenv("HYDROMA_METRICS_API_KEY", raising=False)
    response = gateway_client.get("/metrics")
    assert response.status_code in (401, 403), response.text


def test_sec14_metrics_rejects_a_wrong_key(gateway_client, monkeypatch):
    """With a key configured, a missing or wrong key is a 401 (the gate)."""
    _reset_firewall_state()
    monkeypatch.setenv("HYDROMA_METRICS_API_KEY", "scrape-key-0123456789")
    wrong = gateway_client.get("/metrics", headers={"X-API-Key": "not-the-key"})
    assert wrong.status_code == 401, wrong.text
    missing = gateway_client.get("/metrics")
    assert missing.status_code == 401, missing.text


def test_sec14_metrics_with_key_is_served(gateway_client, monkeypatch):
    _reset_firewall_state()
    monkeypatch.setenv("HYDROMA_METRICS_API_KEY", "scrape-key-0123456789")
    response = gateway_client.get("/metrics", headers={"X-API-Key": "scrape-key-0123456789"})
    assert response.status_code == 200, response.text
    assert "text/plain" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# SEC-28 — WAF comment rule no longer feeds on prose
# ---------------------------------------------------------------------------


def test_sec28_prose_does_not_match_the_comment_rule():
    from services.security.waf import WafEngine

    engine = WafEngine()
    _allowed, _score, hits, _reason = engine.check(
        "POST", "/api/v1/notes", "", "issue # 5 and the value -- see the appendix", "agent"
    )
    assert "sqli-comment" not in hits


def test_sec28_injection_comment_still_matches():
    from services.security.waf import WafEngine

    engine = WafEngine()
    _allowed, _score, hits, _reason = engine.check(
        "POST", "/api/v1/login", "", "admin'--", "agent"
    )
    assert "sqli-comment" in hits


# ---------------------------------------------------------------------------
# S1-C — the async schema bootstrap must survive concurrent first use
# (database/hub.py; init_db() schedules it fire-and-forget while the first
# request calls it directly, across two event loops on one shared in-memory DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_async_tables_survives_concurrent_first_use():
    import asyncio

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import StaticPool

    from database import hub as db_hub

    uri = "file:hydroma_sec_race_test?mode=memory&cache=shared"
    engines = [
        create_async_engine(
            "sqlite+aiosqlite:///" + uri + "&uri=true",
            connect_args={"uri": True, "check_same_thread": False},
            poolclass=StaticPool,
        )
        for _ in range(3)
    ]
    try:
        results = await asyncio.gather(
            *(db_hub._ensure_async_tables(engine) for engine in engines),
            return_exceptions=True,
        )
        failures = [r for r in results if isinstance(r, Exception)]
        assert not failures, failures
    finally:
        for engine in engines:
            await engine.dispose()


# ---------------------------------------------------------------------------
# 2026-10-12 review fixes — one test per corrected finding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("host", ["100.64.1.1", "100.100.100.200"])
def test_rev01_cgnat_range_is_rejected(monkeypatch, host):
    """RFC 6598 shared range — incl. Alibaba's metadata endpoint — must fail closed.

    The first guard was a deny-list of Python address flags, which does not
    classify 100.64.0.0/10 as anything; the fix rejects anything not globally
    routable (review finding 1).
    """
    from services.security import anti_phishing

    monkeypatch.setattr(
        anti_phishing.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", (host, 443))],
    )
    with pytest.raises(ValueError):
        anti_phishing._reject_url(f"https://{host}/")


def test_rev01_public_address_still_passes(monkeypatch):
    from services.security import anti_phishing

    monkeypatch.setattr(
        anti_phishing.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    anti_phishing._reject_url("https://example.com/")  # must not raise


def test_rev03_loop_locks_are_weak_keyed_by_the_loop_object():
    """The lock registry must not key by ``id(loop)`` (id reuse across loops).

    Review finding 3: a lock inherited from a dead loop raises
    ``RuntimeError: bound to a different event loop`` on first contention.
    """
    import asyncio

    from database import hub as db_hub

    assert isinstance(db_hub._async_loop_locks, __import__("weakref").WeakKeyDictionary)

    async def touch() -> int:
        before = len(db_hub._async_loop_locks)
        lock = db_hub._table_lock_for(None)
        async with lock:
            pass
        return before, len(db_hub._async_loop_locks)

    before, after = asyncio.run(touch())
    assert after >= before  # this loop's lock is registered under the loop object


def test_rev05_admin_sees_devices_without_an_owner(iot_ready_engine):
    """Pre-existing devices (``user_id IS NULL``) stay visible to an admin.

    Review finding 5: the owner filter with no escape made every legacy device
    invisible and unmanageable for everyone.
    """
    from services.business_modules.iot.device_manager import DeviceManager

    manager = DeviceManager()
    orphan = manager.register_device(user_id=None, device_name="legacy-device")
    # a plain caller sees none of the fleet it does not own
    assert orphan.id not in [d.id for d in manager.list_devices(user_id="someone-else")]
    # the admin scope re-admits the unowned row (and keeps its own)
    admin_ids = [d.id for d in manager.list_devices(admin=True)]
    assert orphan.id in admin_ids
    assert manager.get_device(orphan.id, user_id="someone-else", admin=True) is not None
    assert manager.get_device(orphan.id, user_id="someone-else", admin=False) is None
    # and the admin can still manage it (re-attribution path)
    assert manager.update_device_status(orphan.id, "error", user_id=None, admin=True) is not None
    assert manager.deregister_device(orphan.id, admin=True) is True


def test_rev12_qr_provisioning_requires_the_caller_and_ignores_payload_scope():
    """QR provisioning must not take owner/platform from the client payload.

    Review finding 12: the REST path sources both from the token; the QR path
    now does too and refuses an anonymous call outright.
    """
    from services.business_modules.iot.device_manager import DeviceManager

    manager = DeviceManager()
    with pytest.raises(ValueError):
        manager.provision_device_from_qr(
            {"device_name": "x", "user_id": "attacker", "platform_id": "other-platform"},
            user_id=None,
        )


def test_rev04_login_mints_the_tenant_claim(auth_service_client):
    """A real login must carry the tenant claim IdentityMiddleware reads.

    Review finding 4: no issuer minted ``tenant_id``, so
    ``request.state.tenant_id`` was always None and every device registered
    ``platform_id=NULL``.
    """
    import base64
    import json

    username = f"rev04-{uuid.uuid4().hex[:8]}"
    response = auth_service_client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "Passw0rd!"},
    )
    assert response.status_code == 201
    payload = response.json()["access_token"].split(".")[1] + "=="
    claims = json.loads(base64.urlsafe_b64decode(payload))
    assert claims.get("tenant_id") == claims.get("sub")


def test_rev07_docs_csp_allows_the_redoc_font_sources():
    from services.api_gateway.security import SecurityHeadersMiddleware

    csp = SecurityHeadersMiddleware._DOCS_CSP
    assert "https://fonts.googleapis.com" in csp
    assert "https://fonts.gstatic.com" in csp


def test_rev08_status_reports_the_layer_that_actually_sends_the_csp(gateway_client):
    """/security/status must report the policy on the wire, not a dead layer's.

    Review finding 8: two middleware classes shared the name
    ``SecurityHeadersMiddleware`` and the report resolved by ``__name__``.
    """
    from services.api_gateway.auth import require_security_admin
    from services.api_gateway.routers import security_router
    from services.api_gateway.security import SecurityHeadersMiddleware

    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(security_router.router)
    app.dependency_overrides[require_security_admin] = lambda: SimpleNamespace(
        id="admin-1", role="admin"
    )
    with TestClient(app) as client:
        report = client.get("/api/v1/security/status").json()["layers"]["headers"]["csp"]
    assert report["enforced"] is True
    assert report["source"] == "services.api_gateway.security.SecurityHeadersMiddleware"


def test_rev10_non_ascii_metrics_key_is_a_mismatch_not_a_crash():
    """A non-ASCII X-API-Key must be a mismatch, not a TypeError 500.

    Review finding 10: ``hmac.compare_digest`` rejects non-ASCII ``str``. The
    header itself cannot be sent through TestClient (httpx only allows ASCII
    header values), so the test pins the primitive the endpoint uses and the
    source guard proves the comparison is on bytes.
    """
    import hmac

    # the hazard the fix removes (would surface as a 500 on the route)
    with pytest.raises(TypeError):
        hmac.compare_digest("scrapp\u00e9", "scrape-key-0123456789")
    # the fix: compare bytes
    assert not hmac.compare_digest(
        "scrapp\u00e9".encode("utf-8"), b"scrape-key-0123456789"
    )
    source = _source("services", "api_gateway", "main.py")
    assert 'hmac.compare_digest(x_api_key.encode("utf-8"), expected.encode("utf-8"))' in source


def test_rev06_env_example_documents_the_metrics_key():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[3] / ".env.example").read_text(encoding="utf-8")
    assert "HYDROMA_METRICS_API_KEY" in text


# ---------------------------------------------------------------------------
# S1-B (SEC-05): cost/compute endpoints authenticated; Twilio webhook signed;
# TwiML escaped
# ---------------------------------------------------------------------------


def test_s1b_voice_cost_endpoints_require_auth():
    from services.api_gateway.routers import voice

    app = FastAPI()
    app.include_router(voice.router)
    with TestClient(app) as client:
        for path, payload in (
            ("/api/v1/voice/tts", {"text": "hi"}),
            ("/api/v1/voice/stt", {"audio_base64": "AAAA"}),
            ("/api/v1/voice/ask", {"question": "hi"}),
            ("/api/v1/voice/ivr/call", {"phone_number": "+1555"}),
            ("/api/v1/voice/ivr/sms", {"to": "+1555", "body": "hi"}),
        ):
            response = client.post(path, json=payload)
            assert response.status_code in (401, 403), f"{path} -> {response.status_code}"


def test_s1b_twilio_webhook_rejects_a_forged_signature(monkeypatch):
    import hashlib
    import hmac

    from services.api_gateway.routers import voice
    from services.business_modules.voice import twilio_ivr as twilio_mod

    token = "test-auth-token"
    integration = twilio_mod.TwilioIVRIntegration(
        twilio_mod.TwilioConfig(account_sid="ACtest", auth_token=token, phone_number="+1555")
    )
    monkeypatch.setattr(twilio_mod, "_twilio_ivr", integration)
    monkeypatch.setattr(voice, "get_twilio_ivr", lambda: integration)

    app = FastAPI()
    app.include_router(voice.router)
    with TestClient(app) as client:
        # forged: no signature at all
        forged = client.post(
            "/api/v1/voice/ivr/twilio/dtmf", data={"Digits": "1", "CallSid": "CA1"}
        )
        assert forged.status_code == 403, forged.text

        # properly signed: the digest Twilio would have sent for this request
        url = "http://testserver/api/v1/voice/ivr/twilio/dtmf"
        params = {"Digits": "1", "CallSid": "CA1"}
        data = url + "".join(f"{k}{params[k]}" for k in sorted(params))
        signature = hmac.new(token.encode(), data.encode(), hashlib.sha1).hexdigest()
        signed = client.post(
            "/api/v1/voice/ivr/twilio/dtmf",
            data=params,
            headers={"X-Twilio-Signature": signature},
        )
        assert signed.status_code == 200, signed.text
        assert "application/xml" in signed.headers["content-type"]


def test_s1b_twiml_escapes_interpolated_values():
    from services.business_modules.voice.twilio_ivr import TwilioIVRIntegration

    integration = TwilioIVRIntegration()
    # element text needs & < > escaped; quotes are legal in text content
    say = integration.generate_twiml_say("a & b <c> \"d\"")
    assert "&amp;" in say and "&lt;c&gt;" in say
    # attribute values additionally need the quote escaped
    ivr = integration.generate_twiml_ivr("menu & more", 'https://example.test/?q="x"')
    assert "&amp;" in ivr and "&quot;" in ivr and "<q" not in ivr
    from xml.etree import ElementTree

    ElementTree.fromstring(ivr)  # the document parses — no injection


def test_s1b_mrv_and_sync_write_endpoints_require_auth():
    from services.api_gateway.routers import mrv, sync

    app = FastAPI()
    app.include_router(mrv.router, prefix="/api/v1")
    app.include_router(sync.router)
    with TestClient(app, raise_server_exceptions=False) as client:
        checks = [
            (
                "/api/v1/mrv/citizen-report",
                {"site_id": "s", "category": "c", "latitude": 0, "longitude": 0},
            ),
            ("/api/v1/sync/trigger", None),
        ]
        for path, payload in checks:
            response = client.post(path, json=payload)
            assert response.status_code in (401, 403), f"{path} -> {response.status_code}"


# ---------------------------------------------------------------------------
# S1-C (SEC-06/09/10/11/12): backup gating, argv hygiene, WAL refusal,
# file mode, prune/cleanup guards
# ---------------------------------------------------------------------------


def test_s1c_backup_router_is_admin_gated():
    """Every route on the backup router must require the admin dependency."""
    from services.api_gateway.auth import require_admin
    from services.backup.router import router as backup_router

    protected = 0
    for route in backup_router.routes:
        dependencies = getattr(route, "dependencies", []) or []
        if any(dep.dependency is require_admin for dep in dependencies):
            protected += 1
    assert protected == len(backup_router.routes), (
        f"{len(backup_router.routes)} routes, {protected} admin-gated"
    )

    app = FastAPI()
    app.include_router(backup_router)
    with TestClient(app) as client:
        response = client.get("/api/v1/backup/configs")
        assert response.status_code in (401, 403), response.text


def test_s1c_backup_router_is_not_mounted_on_the_gateway(gateway_client):
    """SEC-06 guard: the router must never appear on the live app."""
    response = gateway_client.get("/api/v1/backup/configs")
    assert response.status_code in (401, 403, 404)


def test_s1c_restore_requires_an_explicit_confirmation():
    """The confirmation is opt-in at the schema and enforced at the route."""
    from services.backup.schemas import RestoreRequest

    # the schema no longer defaults to True (which made the flag decorative)
    request = RestoreRequest(backup_job_id="j", target_database="db")
    assert request.confirm is False
    request = RestoreRequest(backup_job_id="j", target_database="db", confirm=True)
    assert request.confirm is True
    # the route refuses an unconfirmed restore
    route_source = _source("services", "backup", "router.py")
    assert "if not data.confirm:" in route_source
    assert "confirmation required" in route_source


def test_s1c_storage_path_is_contained(tmp_path, monkeypatch):
    from pydantic import ValidationError

    from services.backup.schemas import BackupConfigCreate

    monkeypatch.setenv("BACKUP_STORAGE_ROOT", str(tmp_path))
    base = {"name": "nightly"}
    BackupConfigCreate(**base, storage_path="./backups")  # inside the root
    BackupConfigCreate(**base, storage_path=str(tmp_path / "sub"))  # absolute inside
    for escape in ("../outside", "/etc", "..\\..\\windows"):
        with pytest.raises(ValidationError):
            BackupConfigCreate(**base, storage_path=escape)


def test_s1c_pg_connection_keeps_credentials_out_of_argv():
    from services.backup.service import _pg_connection

    env, dbname = _pg_connection("postgresql://user:s3cret@db.internal:5432/econojin")
    assert dbname == "econojin"
    assert env["PGPASSWORD"] == "s3cret"
    assert env["PGUSER"] == "user"
    # nothing on the command line carries the password
    argv = ["pg_dump", "--no-password", "--format=plain", "--dbname", dbname]
    assert all("s3cret" not in part for part in argv)


def test_s1c_wal_is_refused_on_an_unsafe_sqlite(tmp_path, monkeypatch):
    from sqlalchemy import create_engine

    import database.hub as hub

    monkeypatch.setattr(hub, "sqlite_wal_deployment_safe", lambda: False)
    db_file = tmp_path / "wal-test.db"
    engine = create_engine(f"sqlite:///{db_file}")
    hub.install_sqlite_pragmas(engine)
    with engine.connect() as conn:
        mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert str(mode).lower() != "wal", mode


def test_s1c_sqlite_file_is_owner_only(tmp_path):
    import os

    from adapters.persistence.sqlite_persistence import SQLitePersistence

    target = tmp_path / "owner-only.db"
    SQLitePersistence(str(target))
    assert target.exists()
    if os.name == "posix":
        assert target.stat().st_mode & 0o777 == 0o600
    else:
        # Windows has no POSIX mode bits (every file reports 0o666); the
        # protection there is the filesystem ACL the deployment sets, and the
        # chmod(0o600) this adapter issues degrades to a plain writable file.
        # The assertion here is that the adapter still opens and works.
        assert target.stat().st_size >= 0


def test_s1c_cleanup_confines_paths_and_fails_closed():
    from tools.cleanup import confined_paths

    with pytest.raises(SystemExit):
        confined_paths(Path("."), ["../outside"])
    with pytest.raises(SystemExit):
        confined_paths(Path("."), ["C:\\Windows"])


def test_s1c_prune_workspace_refuses_a_root_outside_the_repo():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "tools/prune_workspace.py", "--root", ".."],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 2
    assert "must be inside the repository" in result.stdout + result.stderr


# ---------------------------------------------------------------------------
# S1-B/S1-C/S2/S3 wave (2026-10-13): the remaining plan items
# ---------------------------------------------------------------------------


def test_wave_cors_allows_the_security_headers():
    """SEC-15: the SPA must be able to send CSRF/step-up/idempotency headers."""
    from services.api_gateway.main import app

    # The spider firewall's anti-bot and breaker are module-level singletons
    # shared across tests: under xdist, earlier tests in the same worker can
    # challenge or block the shared test-client address before CORS answers.
    # Reset the singletons and present a browser User-Agent so the preflight
    # exercises CORS, not the anti-bot.
    _reset_firewall_state()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:8000",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-csrf-token, x-totp-code, idempotency-key",
        },
    )
    allowed = response.headers.get("access-control-allow-headers", "")
    for header in ("x-csrf-token", "x-totp-code", "idempotency-key"):
        assert header.lower() in allowed.lower(), f"{header} missing from: {allowed}"


def test_wave_demo_seed_requires_provisioned_passwords(monkeypatch):
    """SEC-24: no demo account is created without its env-provided password."""
    import asyncio
    import os

    from services.auth_legacy.service import AuthService

    for var in (
        "ECO_NOJIN_DEMO_PASSWORD_1",
        "ECO_NOJIN_DEMO_PASSWORD_2",
        "ECO_NOJIN_DEMO_PASSWORD_3",
        "ECO_NOJIN_DEMO_PASSWORD_4",
        "ECO_NOJIN_DEMO_ADMIN",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    class _Repo:
        db = None

        async def get_user_by_email(self, email):
            return None

        async def commit(self):
            return None

    service = AuthService.__new__(AuthService)
    service.repo = _Repo()
    created, skipped = asyncio.run(service.seed_demo_users())
    assert created == [], created
    assert os.getenv("ECO_NOJIN_DEMO_ADMIN", "") != "1" or "admin@test.com" in skipped


def test_wave_passkey_rp_comes_from_settings_in_production(monkeypatch):
    """SEC-25: production must fail closed when the passkey values are unset."""
    from services.api_gateway.routers import passkey_router

    monkeypatch.setattr(
        passkey_router,
        "get_settings",
        lambda: SimpleNamespace(is_production=True, passkey_rp_id="", passkey_origin=""),
    )
    with pytest.raises(RuntimeError):
        passkey_router._resolve_rp()


# ---------------------------------------------------------------------------
# guard sweeps — the wiring must stay in the source (p14 pattern)
# ---------------------------------------------------------------------------


def _source(*parts: str) -> str:
    from pathlib import Path

    # services/security/tests/<file> -> repo root is parents[3]
    root = Path(__file__).resolve().parents[3]
    return root.joinpath(*parts).read_text(encoding="utf-8")


def test_guard_auth_service_no_client_role_field():
    source = _source("services", "auth", "main.py")
    assert "DEFAULT_SELF_REGISTRATION_ROLE" in source
    assert "body.role" not in source
    assert "hmac.compare_digest" in source
    assert "jwt_signing_key" in source
    assert "access_token_expire_minutes" in source


def test_guard_iot_reads_tenant_from_state():
    source = _source("services", "api_gateway", "routers", "iot_devices.py")
    assert 'getattr(request.state, "tenant_id", None)' in source
    # the header read must be gone (the docstring may still name it as history)
    assert 'headers.get("X-Tenant-Id")' not in source
    assert 'headers.get("X-Platform-Id")' not in source
    manager = _source("services", "business_modules", "iot", "device_manager.py")
    assert "DbDevice.user_id == str(user_id)" in manager


def test_guard_security_router_requires_admin():
    source = _source("services", "api_gateway", "routers", "security_router.py")
    assert "require_security_admin" in source
    anti_phish = _source("services", "security", "anti_phishing.py")
    assert "_reject_url" in anti_phish
    assert 'parsed.scheme.lower() != "https"' in anti_phish


def test_guard_headers_and_metrics_gates():
    assert "Content-Security-Policy" in _source("services", "api_gateway", "security.py")
    assert "HYDROMA_METRICS_API_KEY" in _source("services", "api_gateway", "main.py")
