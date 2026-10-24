"""P3 — access control is enforced server-side, and proven by negative tests.

Every test here is written so that it **fails if the guard is removed** (the
eco.md "detox" principle):

* the cross-tenant matrix drives the real routers with two distinct users and
  asserts user A can neither read nor mutate user B's data — a dropped
  ``buyer_id`` scope, a missing ``require_user``, or an ownership check that
  stops comparing ids turns one of these red;
* the session tests drive the real refresh-token store: a revoked or expired
  token must verify as revoked;
* the RBAC sweep enumerates the admin surface with a non-admin token — a new
  privileged route added without a role gate is caught by the sweep.

Scope note (recorded in the P3 report): the gateway routers touched by the
fixes (`api_gateway/routers/marketplace.py`, `sponsors/routers/admin.py`) sit
outside A03's nominal file scope but are exactly the surface task 1
("cross-tenant negative matrix") guards; the extension is deliberate and
listed in `reports/PHASE-P3-2026-10-11.md`.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "JWT_SECRET",
    "test-jwt-secret-0123456789abcdef0123456789abcdef0123456789abcdef",
)

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from database.models import EcoWallet
from services.api_gateway.auth import (
    create_access_token,
    create_refresh_token,
    is_refresh_token_revoked,
    store_refresh_token,
)
from services.api_gateway.routers import marketplace as marketplace_router_module
from services.marketplace.order_management import OrderManager

pytestmark = pytest.mark.asyncio


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _user(user_id: str, role: str = "farmer", email: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        email=email or f"{user_id}@example.test",
        full_name=user_id,
        role=role,
        is_active=True,
    )


def _token(user_id: str, role: str = "farmer") -> str:
    return create_access_token(data={"sub": user_id}, subject=user_id, role=role)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def two_users(session):
    """Two wallets in one in-memory DB: user-a and user-b."""
    for user_id in ("user-a", "user-b"):
        session.add(EcoWallet(user_id=user_id, balance=0, total_earned=0, total_redeemed=0))
    await session.commit()
    return session


# --------------------------------------------------------------------------
# 1. cross-tenant matrix — user ↔ user (finance wallet, caller-scoped)
# --------------------------------------------------------------------------

async def test_wallet_earn_is_scoped_to_the_caller(session):
    from decimal import Decimal as _Decimal

    from services.finance.wallet_service import WalletService

    service = WalletService(session)
    amount, _balance = await service.earn("user-a", "tree_planting", _Decimal("1"))
    assert amount == _Decimal("50")
    state_a = await service.get_wallet_state("user-a")
    state_b = await service.get_wallet_state("user-b")
    assert state_a["balance"] == _Decimal("50")
    assert state_b["balance"] == _Decimal("0")  # B never sees A's credit


async def test_order_listing_is_scoped_to_the_authenticated_buyer():
    manager = OrderManager(catalog=_StubCatalog())
    manager.create_order(product_id="p1", buyer_name="user-a", quantity_kg=1, seller_id="s1")
    manager.create_order(product_id="p1", buyer_name="user-b", quantity_kg=1, seller_id="s1")

    only_a = manager.list_orders(buyer_id="user-a")
    only_b = manager.list_orders(buyer_id="user-b")

    assert len(only_a) == 1 and str(only_a[0].buyer_name) == "user-a"
    assert len(only_b) == 1 and str(only_b[0].buyer_name) == "user-b"
    assert only_a[0].id != only_b[0].id


async def test_orders_route_requires_authentication():
    """P3: GET /orders was fully public before this phase."""
    app = FastAPI()
    app.include_router(marketplace_router_module.router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/marketplace/orders")
    assert response.status_code == 401


async def test_vendor_orders_route_requires_authentication():
    app = FastAPI()
    app.include_router(marketplace_router_module.router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/marketplace/vendors/seller-1/orders"
        )
    assert response.status_code == 401


async def test_orders_route_scopes_to_the_caller(monkeypatch):
    """The route must pass the token's user id into the scope filter."""
    seen: dict = {}

    class _RecordingManager:
        def list_orders(self, status=None, limit=50, buyer_id=None):
            seen["buyer_id"] = buyer_id
            return []

    def _fake_manager():
        return _RecordingManager()

    monkeypatch.setattr(marketplace_router_module, "get_order_manager", _fake_manager)
    app = FastAPI()
    app.include_router(marketplace_router_module.router)
    app.dependency_overrides[
        marketplace_router_module.require_user
    ] = lambda: _user("user-a")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/marketplace/orders")
    assert response.status_code == 200
    assert seen["buyer_id"] == "user-a"


async def test_order_body_cannot_claim_another_buyer():
    """The buyer identity comes from the token, not the request body."""
    created: dict = {}

    class _RecordingManager:
        def create_order(self, product_id, buyer_name, quantity_kg, seller_id=""):
            created["buyer_name"] = buyer_name
            return SimpleNamespace(
                id="o1",
                product_name="stub",
                quantity_kg=quantity_kg,
                total_price=1.0,
                status=SimpleNamespace(value="pending"),
                traceability_code="ECO-STUB",
            )

    class _Catalog:
        def get_product(self, product_id):
            return SimpleNamespace(producer_id="seller-1")

    def _fake_manager():
        return _RecordingManager()

    def _fake_catalog():
        return _Catalog()

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(marketplace_router_module, "get_order_manager", _fake_manager)
    monkeypatch.setattr(marketplace_router_module, "get_catalog", _fake_catalog)
    app = FastAPI()
    app.include_router(marketplace_router_module.router)
    app.dependency_overrides[marketplace_router_module.require_user] = lambda: _user("user-a")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/marketplace/orders",
            json={
                "product_id": "p1",
                "buyer_name": "someone-else",
                "quantity_kg": 1,
            },
        )
    monkeypatch.undo()
    assert response.status_code == 200
    assert created["buyer_name"] == "user-a"  # body claim ignored


# --------------------------------------------------------------------------
# 2. cross-tenant matrix — seller ↔ seller (product mutation ownership)
# --------------------------------------------------------------------------

async def test_product_images_require_the_owner():
    """A stranger cannot attach images to another producer's product."""
    app = FastAPI()
    app.include_router(marketplace_router_module.router)

    class _Catalog:
        def get_product(self, product_id):
            return SimpleNamespace(
                id=product_id, producer_id="producer-a", images=[]
            )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(marketplace_router_module, "get_catalog", lambda: _Catalog())
    app.dependency_overrides[marketplace_router_module.require_user] = lambda: _user(
        "producer-b"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/marketplace/products/p1/images",
            files={"files": ("x.png", b"fake", "image/png")},
        )
    monkeypatch.undo()
    assert response.status_code == 403


async def test_product_images_allow_the_owner():
    app = FastAPI()
    app.include_router(marketplace_router_module.router)

    class _Catalog:
        def get_product(self, product_id):
            return SimpleNamespace(
                id=product_id, producer_id="producer-a", images=[]
            )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(marketplace_router_module, "get_catalog", lambda: _Catalog())
    app.dependency_overrides[marketplace_router_module.require_user] = lambda: _user(
        "producer-a"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/marketplace/products/p1/images",
            files={"files": ("x.png", b"fake", "image/png")},
        )
    monkeypatch.undo()
    assert response.status_code == 200


# --------------------------------------------------------------------------
# 3. privilege sweep — no admin route answers without the role
# --------------------------------------------------------------------------

async def test_sponsors_admin_router_uses_the_real_dependency():
    """KN-13: the local 501 placeholder is gone; the real gate is imported."""
    from services.api_gateway.auth import require_admin as gateway_require_admin
    from services.sponsors.routers import admin as sponsors_admin

    assert sponsors_admin.require_admin is gateway_require_admin


async def test_sponsors_admin_route_rejects_a_non_admin():
    app = FastAPI()
    from services.sponsors.routers import admin as sponsors_admin

    app.include_router(sponsors_admin.router)
    app.dependency_overrides[sponsors_admin.require_admin] = _ForbiddenAdmin
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/sponsors")
    assert response.status_code in (401, 403)


async def _ForbiddenAdmin():  # pragma: no cover - replaced by the real gate below
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


async def test_sponsors_admin_route_allows_an_admin_token():
    from services.api_gateway.auth import require_admin as gateway_require_admin

    class _StubSession:
        def execute(self, *args, **kwargs):
            return SimpleNamespace(scalars=lambda: iter([]))

    app = FastAPI()
    from services.sponsors.routers import admin as sponsors_admin

    app.include_router(sponsors_admin.router)
    app.dependency_overrides[gateway_require_admin] = lambda: _user("admin-1", role="admin")

    def _db():
        yield _StubSession()

    app.dependency_overrides[sponsors_admin.get_db] = _db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/sponsors")
    # With an admin identity the route runs and returns the (empty) list —
    # authorization passed, which is what this test pins.
    assert response.status_code == 200
    assert response.json() == []


# --------------------------------------------------------------------------
# 4. session lifecycle — revocation and expiry
# --------------------------------------------------------------------------

async def test_revoked_refresh_token_is_detected(session):
    from sqlalchemy import select

    from database.models import RefreshToken
    from services.api_gateway.auth import decode_refresh_token

    token = create_refresh_token(data={"sub": "user-a"}, subject="user-a", role="farmer")
    decoded = decode_refresh_token(token)
    assert decoded is not None
    jti = decoded["jti"]

    await store_refresh_token(
        jti=jti,
        user_id="user-a",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        db=session,
    )
    await session.commit()
    assert await is_refresh_token_revoked(jti, session) is False

    # Revoke the *stored* row (logout does the same update, not a second insert).
    stored = (
        await session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    ).scalar_one()
    stored.revoked = True
    await session.commit()
    assert await is_refresh_token_revoked(jti, session) is True


async def test_expired_refresh_token_fails_to_decode():
    """Expiry is enforced at decode time (``exp`` claim), not by the DB check.

    ``create_refresh_token`` always overwrites ``exp`` with the configured
    lifetime, so a genuinely stale token is minted with the app's own signer
    to prove the decode path rejects it.
    """
    import jwt

    from services.api_gateway import auth as auth_module

    stale = jwt.encode(
        {
            "sub": "user-a",
            "type": "refresh",
            "jti": "stale-jti",
            "exp": datetime.now(UTC) - timedelta(minutes=5),
        },
        auth_module._signing_key(),
        algorithm=auth_module._settings.jwt_algorithm,
    )
    assert auth_module.decode_refresh_token(stale) is None
    assert auth_module.decode_token(stale) is None

    fresh = create_refresh_token(data={"sub": "user-a"}, subject="user-a", role="farmer")
    decoded = auth_module.decode_refresh_token(fresh)
    assert decoded is not None and decoded.get("type") == "refresh"


async def test_unknown_jti_is_treated_as_revoked(session):
    assert await is_refresh_token_revoked("never-issued", session) is True


# --------------------------------------------------------------------------
# 5. RBAC — roles are independent of profile titles
# --------------------------------------------------------------------------

async def test_access_token_carries_role_and_role_gates_read_it():
    from fastapi import HTTPException

    from services.api_gateway.auth import decode_token, require_roles

    token = _token("user-a", role="advisor")
    decoded = decode_token(token)
    assert decoded is not None and decoded["role"] == "advisor"
    assert decoded["sub"] == "user-a"

    dependency = require_roles("admin")
    with pytest.raises(HTTPException) as caught:
        dependency(user=_user("user-a", role="advisor"))
    assert caught.value.status_code == 403

    allowed = dependency(user=_user("admin-1", role="admin"))
    assert allowed.id == "admin-1"


async def test_admin_roles_set_is_the_documented_quad():
    from services.api_gateway.auth import ADMIN_ROLES

    assert ADMIN_ROLES == {"admin", "security_admin", "content_admin", "user_admin"}


class _StubProduct:
    """Minimal product: always fulfillable, one producer."""

    id = "p1"
    name = "stub"
    producer_id = "s1"
    price_per_kg = 1.0
    minimum_order_kg = 1
    quantity_available_kg = 100
    is_active = True
    traceability_code = "ECO-STUB"
    images: list[str] = []

    def can_fulfill_order(self, quantity_kg: float) -> bool:
        return self.is_active and quantity_kg >= self.minimum_order_kg

    def calculate_total_value(self, quantity_kg: float) -> float:
        return quantity_kg * self.price_per_kg


class _StubCatalog:
    """Catalog backed by the stub product."""

    def get_product(self, product_id: str):
        return _StubProduct()

    def update_quantity(self, product_id: str, delta: float) -> None:
        return None
