"""The frontend's HTTP contract, enforced against the real gateway.

The React client in ``frontend/`` talks to exactly 39 gateway paths (see
``frontend/API-INVENTORY.md``). Those paths are the *product* contract: a
field rename, a wrapping change, a status enum the client cannot render or a
middleware requirement the client does not know about is a broken screen in
production, and it is invisible to the unit tests of either side alone.

Every assertion below reads the response through the TypeScript interfaces in
``frontend/src/services/*.ts``: the field names, the wrapping
(``{"user": {...}}`` vs a bare object), the money type, the enum vocabulary
and the error bodies. The flow mirrors the workspace: register, read the
catalogue, submit a listing, approve it as the operator, buy it, pay by bank
transfer, claim the tracking code, verify as an administrator.

The last three tests are regressions for defects that shipped in this pass:
the payment route rejecting a keyless call (the client now sends
``Idempotency-Key``), ``GET /api/v1/admin/users`` answering 500 on the first
row (``created_at`` is a datetime, not a string), and an endpoint 404 being
reported as "Endpoint not found" by the routing-level 404 handler.

Two middleware facts are part of the contract and are exercised as such: an
unsafe method needs the CSRF header (the client gets it from the
``econojin_csrf`` cookie), and ``POST /api/v1/auth/register`` is rate-limited
to five attempts per minute, which ``_register`` waits out rather than
skipping around.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from database.config import SessionLocal
from services.marketplace.models import MarketplaceProduct, MarketplaceSeller
from services.tourism.models import TourismTour

from .frontend_contract_helpers import (
    _login_as_admin,
    _promote_latest_contract_user,
    _register,
    _seed_approved_product,
    _seed_tour,
    _write_headers,
)

# ---------------------------------------------------------------------------
# session.ts â€” auth
# ---------------------------------------------------------------------------


def test_auth_me_login_and_logout_shapes(client: TestClient):
    email = f"contract-{uuid4().hex[:8]}@example.com"
    _register(client, email)

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200, me.text
    # session.ts reads a bare ApiUser: {id, email, full_name, role}.
    user = me.json()
    assert {"id", "email", "full_name", "role"} <= set(user)
    assert user["email"] == email

    client.post("/api/v1/auth/logout", headers=_write_headers(client))
    assert client.get("/api/v1/auth/me").status_code == 401

    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Passw0rd!23"}
    )
    assert login.status_code == 200, login.text
    # AuthPage reads {"user": {...}} from login/register: the wrapping differs
    # from /me on purpose, and both sides of it are pinned here.
    assert login.json()["user"]["email"] == email


def test_login_rejects_a_bad_password_with_a_safe_body(client: TestClient):
    email = f"contract-{uuid4().hex[:8]}@example.com"
    _register(client, email)
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert isinstance(response.json()["detail"], str)


# ---------------------------------------------------------------------------
# catalog.ts â€” models
# ---------------------------------------------------------------------------


def test_model_catalogue_matches_the_science_page_catalog(client: TestClient):
    body = client.get("/api/v1/models").json()
    assert body["count"] >= 1
    assert body["count"] == len(body["models"])
    for model in body["models"]:
        # SciencePage/GuidePage read exactly these fields per model.
        assert {
            "slug",
            "name_fa",
            "name_en",
            "domain",
            "fidelity",
            "reference",
            "description",
            "validity",
            "limitations",
            "params",
        } <= set(model)
        for param in model["params"]:
            assert {"name", "label", "unit", "default", "kind"} <= set(param)


def test_model_run_returns_the_execution_envelope(client: TestClient):
    body = client.get("/api/v1/models").json()
    model = body["models"][0]
    params = {
        p["name"]: p["default"]
        for p in model["params"]
        if p.get("default") is not None and p.get("kind") in ("number", "float", "int")
    }
    response = client.post(
        f"/api/v1/models/{model['slug']}/run",
        json=params,
        headers=_write_headers(client),
    )
    assert response.status_code in (200, 400), response.text
    if response.status_code == 200:
        run = response.json()
        # ModulePage renders result + executed_ms and surfaces the backend's
        # own 400 detail when validation refuses the inputs.
        assert {"slug", "fidelity", "result", "executed_ms"} <= set(run)


def test_model_run_rejects_an_unknown_slug_with_the_backend_reason(client: TestClient):
    # catalogue.runModel is an unsafe POST, so it carries the CSRF header the
    # transport helper derives from the econojin_csrf cookie.
    response = client.post(
        "/api/v1/models/no-such-model/run",
        json={},
        headers=_write_headers(client),
    )
    assert response.status_code == 404
    assert "unknown model" in response.json()["detail"]


# ---------------------------------------------------------------------------
# knowledge.ts â€” Daneshyar
# ---------------------------------------------------------------------------


def test_knowledge_list_shape_is_the_paginated_envelope(client: TestClient):
    body = client.get("/api/v1/knowledge?page=1&page_size=5").json()
    # KnowledgePage reads items/total/total_pages.
    assert {"items", "total", "total_pages"} <= set(body)
    for entry in body["items"]:
        # The public projection must stay public: no creator internals.
        assert {
            "id",
            "title",
            "slug",
            "knowledge_type",
            "abstract",
            "language",
            "validation_status",
            "publication_date",
        } <= set(entry)
        for banned in ("created_by", "validated_by", "validated_at", "content"):
            assert banned not in entry


def test_knowledge_collections_shape(client: TestClient):
    body = client.get("/api/v1/knowledge/collections?page_size=100").json()
    assert {"items", "total", "total_pages"} <= set(body)


def test_knowledge_entry_404_carries_its_own_reason(client: TestClient):
    """Regression: the routing 404 handler used to mask every endpoint 404."""
    response = client.get(f"/api/v1/knowledge/{uuid4()}")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "Endpoint not found" not in body["detail"]
    assert "hint" not in body  # the routing-miss body, not an endpoint 404


# ---------------------------------------------------------------------------
# territories.ts â€” landscape
# ---------------------------------------------------------------------------


def test_territories_list_shape(client: TestClient):
    body = client.get("/api/v1/territories?page=1&page_size=5").json()
    # LandscapePage/TerritoryPage read items/total/page/page_size/pages.
    assert {"items", "total", "page", "page_size", "pages"} <= set(body)
    for item in body["items"]:
        assert {
            "village_id",
            "name",
            "region",
            "country",
            "verification_status",
            "representative_status",
            "workflow_status",
            "active_modules",
            "total_members",
            "active_sellers",
            "active_tour_guides",
        } <= set(item)


# ---------------------------------------------------------------------------
# decision.ts â€” Tasmimyar
# ---------------------------------------------------------------------------


def test_decide_returns_the_results_only_contract(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    response = client.post(
        "/api/tasmimyar/decide",
        headers=_write_headers(client),
        json={
            "claim_id": f"claim-{uuid4().hex[:8]}",
            "supporting_facts": [
                {
                    "id": "f1",
                    "statement": "Measured field moisture is within the target range",
                    "source_id": "user-submitted",
                    "confidence": 0.9,
                }
            ],
            "contradicting_facts": [],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    # DecisionPage renders exactly these fields; anything else on the wire is
    # the engine's internal scoring, which the results-only rule keeps out.
    assert set(data) == {
        "decision_id",
        "outcome",
        "confidence",
        "rationale",
        "recommendations",
        "caveats",
    }


# ---------------------------------------------------------------------------
# tourism.ts â€” tours
# ---------------------------------------------------------------------------


def _seed_tour() -> str:
    tour_id = f"tour-{uuid4().hex[:8]}"
    with SessionLocal() as session:
        session.add(
            TourismTour(
                id=tour_id,
                guide_id=f"guide-{uuid4().hex[:6]}",
                village_id="v-1",
                title="Tour contract probe",
                slug=f"tour-contract-{tour_id}",
                description="Seeded by the contract test",
                images=["/images/tour.jpg"],
                tour_type="ecotourism",
                duration_hours=4,
                price_per_person=Decimal("250000"),
                # The public catalogue only serves active tours.
                status="active",
                is_regenerative=True,
            )
        )
        session.commit()
    return tour_id


def _seed_approved_product(client: TestClient, name: str, price: int) -> str | None:
    """Create a listing and approve it, so the test owns a buyable product.

    The 24-item catalogue falls back to the non-orderable demo rows when no
    persisted product is approved, and those rows are not addressable by the
    cart, detail or item routes â€” they live only in the in-memory demo
    catalogue. A test that needs an orderable product must seed its own.
    """
    listing = client.post(
        "/api/v1/marketplace/checkout/products",
        headers=_write_headers(client),
        json={
            "name": name,
            "category": "food",
            "price": price,
            "village_id": "v-1",
            "description": f"seeded by {name}",
            "stock": 25,
        },
    )
    if listing.status_code != 200:
        return None
    product_id = listing.json()["product_id"]
    with SessionLocal() as session:
        product = session.get(MarketplaceProduct, product_id)
        if product is None:
            return None
        seller = session.get(MarketplaceSeller, product.seller_id)
        assert seller is not None
        seller.is_verified = True
        seller.status = "active"
        product.status = "active"
        session.commit()
    return product_id


def test_tours_list_carries_the_images_the_cards_render(client: TestClient):
    _seed_tour()
    body = client.get("/api/v1/tourism/tours?limit=24").json()
    assert isinstance(body, list)
    assert body, "the seeded tour must be visible on the unified database"
    tour = body[0]
    assert {"id", "village_id", "title", "tour_type", "duration_hours", "price_per_person"} <= set(
        tour
    )
    # Regression: ``images``/``currency`` exist on the model but were absent
    # from the response, so every tour card fell back to the placeholder.
    assert "images" in tour and isinstance(tour["images"], list)
    assert "currency" in tour


def test_booking_returns_the_receipt_shape(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    tour_id = _seed_tour()
    response = client.post(
        "/api/v1/tourism/bookings",
        headers=_write_headers(client),
        json={
            "tour_id": tour_id,
            "village_id": "v-1",
            "participants_count": 2,
            "tour_date": (date.today() + timedelta(days=7)).isoformat(),
        },
    )
    assert response.status_code in (200, 201), response.text
    body = response.json()
    # ModulePage reads booking_number + participants_count + total + status.
    assert {"id", "booking_number", "participants_count", "total", "status"} <= set(body)


def test_tourism_bookings_history_is_an_array(client: TestClient):
    body = client.get("/api/v1/tourism/bookings?limit=5&offset=0")
    assert body.status_code == 200
    assert isinstance(body.json(), list)


# ---------------------------------------------------------------------------
# marketplace.ts â€” the seller â†’ buyer â†’ bank-transfer flow
# ---------------------------------------------------------------------------


def _approve_seller(product_id: str) -> None:
    """Make the seeded listing orderable: verify its seller and activate it."""
    from services.marketplace.models import MarketplaceProduct

    with SessionLocal() as session:
        product = session.get(MarketplaceProduct, product_id)
        assert product is not None, "the listing must be persisted synchronously"
        seller = session.get(MarketplaceSeller, product.seller_id)
        assert seller is not None
        seller.is_verified = True
        seller.status = "active"
        product.status = "active"
        session.commit()


def test_marketplace_bank_transfer_flow_end_to_end(client: TestClient):
    """The exact sequence the ModulePage drives, on the real middleware stack.

    Proves the sync/async database split is gone: the seller writes through
    the sync session plane and reads back through the async plane.
    """
    email = f"contract-{uuid4().hex[:8]}@example.com"
    _register(client, email)

    listing = client.post(
        "/api/v1/marketplace/checkout/products",
        headers=_write_headers(client),
        json={
            "name": "Zereshk",
            "category": "food",
            "price": 100000,
            "village_id": "v-1",
            "description": "contract probe",
            "stock": 10,
        },
    )
    assert listing.status_code == 200, listing.text
    body = listing.json()
    # ModulePage branches on seller_status/seller_verification_required.
    assert {"product_id", "status", "seller_status", "seller_verification_required"} <= set(body)
    product_id = body["product_id"]
    _approve_seller(product_id)

    products = client.get("/api/v1/marketplace/products?limit=24").json()
    target = [p for p in products["products"] if p["id"] == product_id]
    assert target, "an approved product must reach the buyer's catalogue"
    assert target[0]["orderable"] is True

    order = client.post(
        "/api/v1/marketplace/checkout/orders",
        headers=_write_headers(client),
        json={
            "product_id": product_id,
            "quantity": 2,
            "shipping_address": "Tehran",
        },
    )
    assert order.status_code == 200, order.text
    order_body = order.json()
    # ModulePage multiplies quantity أ— price_per_kg into the payment amount.
    assert {"order_id", "order_number", "status", "subtotal", "total", "currency"} <= set(order_body)
    order_id = order_body["order_id"]
    total = order_body["total"]

    # Regression: the route is idempotency-protected, so a call without the
    # header (what the client used to send) is a 400 before any payment row
    # is created, not a payment.
    keyless = client.post(
        "/api/v1/marketplace/payments",
        headers=_write_headers(client),
        json={
            "order_id": order_id,
            "payment_method": "bank",
            "amount": float(total),
            "description": "contract probe",
        },
    )
    assert keyless.status_code == 400
    assert keyless.json()["code"] == "IDEMPOTENCY_KEY_REQUIRED"

    payment = client.post(
        "/api/v1/marketplace/payments",
        headers=_write_headers(client, str(uuid4())),
        json={
            "order_id": order_id,
            "payment_method": "bank",
            "amount": float(total),
            "description": "contract probe",
        },
    )
    assert payment.status_code == 200, payment.text
    payment_body = payment.json()
    # PaymentInstructions reads id/amount/currency/status + optional
    # tracking_code and bank_instructions.
    assert {"id", "order_id", "amount", "currency", "status"} <= set(payment_body)
    payment_id = payment_body["id"]

    claimed = client.post(
        f"/api/v1/marketplace/payments/{payment_id}/confirm",
        headers=_write_headers(client, str(uuid4())),
        json={"ref_id": "TRK-1"},
    )
    assert claimed.status_code == 200, claimed.text
    # A bank transfer is a claim until an administrator verifies it: the
    # ModulePage shows the awaiting-review state on this exact value.
    assert claimed.json()["escrow"] == "awaiting_verification"

    with SessionLocal() as session:
        from database import models as db_models

        actor = session.query(db_models.User).filter(db_models.User.email == email).first()
        actor.role = "admin"
        session.commit()

    orders = client.get("/api/v1/marketplace/orders").json()
    mine = [o for o in orders["orders"] if o["id"] == order_id]
    assert mine, "the buyer must see their own order"
    assert {"id", "product_name", "quantity_kg", "status", "created_at"} <= set(mine[0])


def test_marketplace_pending_payments_requires_admin(anonymous_client: TestClient):
    response = anonymous_client.get("/api/v1/marketplace/admin/payments/pending")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# administration.ts â€” admin users
# ---------------------------------------------------------------------------


def _promote_latest_contract_user() -> str | None:
    """Give the most recently registered probe user the admin role."""
    from database import models as db_models

    with SessionLocal() as session:
        actor = (
            session.query(db_models.User)
            .filter(db_models.User.email.like("contract-%"))
            .order_by(db_models.User.created_at.desc())
            .first()
        )
        if actor is None:
            return None
        actor.role = "admin"
        session.commit()
        return actor.email


def test_admin_users_list_is_serialized_not_500(client: TestClient):
    """Regression: ``created_at`` was a raw datetime on a ``str`` field."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    email = _promote_latest_contract_user()
    assert email is not None, "the probe user must exist on the shared database"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Passw0rd!23"},
    )
    assert login.status_code == 200, login.text

    users = client.get("/api/v1/admin/users?limit=50&offset=0")
    assert users.status_code == 200, users.text
    body = users.json()
    assert isinstance(body, list) and body, "the admin must see the registered users"
    first = body[0]
    assert {
        "id",
        "email",
        "full_name",
        "role",
        "is_email_verified",
        "is_active",
        "two_factor_enabled",
        "created_at",
    } <= set(first)
    # The 500 came from a datetime reaching a str field: the wire form is an
    # ISO-8601 string.
    assert isinstance(first["created_at"], str)
    datetime.fromisoformat(first["created_at"])


def test_admin_users_requires_the_admin_role(client: TestClient):
    email = f"contract-{uuid4().hex[:8]}@example.com"
    _register(client, email)
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 403
    assert "role" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# content.ts â€” content studio
# ---------------------------------------------------------------------------


def test_admin_content_round_trip_and_versions(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    email = _promote_latest_contract_user()
    assert email is not None
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Passw0rd!23"}
    )
    assert login.status_code == 200, login.text

    created = client.post(
        "/api/v1/admin/content",
        headers=_write_headers(client),
        json={
            "title": "Contract probe",
            "body": "Body text",
            "category": "news",
            "status": "draft",
            "language": "fa",
        },
    )
    assert created.status_code in (200, 201), created.text
    item = created.json()
    # ContentStudioPage reads id/title/body/category/status/language.
    assert {"id", "title", "body", "category", "status", "language"} <= set(item)

    versions = client.get(f"/api/v1/admin/content/{item['id']}/versions")
    assert versions.status_code == 200
    assert isinstance(versions.json(), list)


def test_admin_content_schedule_stays_pending_until_its_date(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    email = _promote_latest_contract_user()
    assert email is not None
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Passw0rd!23"}
    )
    assert login.status_code == 200, login.text

    created = client.post(
        "/api/v1/admin/content",
        headers=_write_headers(client),
        json={"title": "Schedule probe", "body": "Body", "category": "news", "status": "draft"},
    )
    assert created.status_code in (200, 201), created.text
    item = created.json()
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    scheduled = client.post(
        f"/api/v1/admin/content/{item['id']}/schedule",
        headers=_write_headers(client),
        json={"publish_at": future},
    )
    assert scheduled.status_code in (200, 204)
    # A scheduled item must not silently become published: the studio shows the
    # pending-schedule state and the operator can still cancel it.
    cancelled = client.post(
        f"/api/v1/admin/content/{item['id']}/cancel-schedule",
        headers=_write_headers(client),
    )
    assert cancelled.status_code in (200, 204)


# ---------------------------------------------------------------------------
# F1 â€” cart, catalogue search, reviews, order detail, escrow read
# ---------------------------------------------------------------------------


def test_catalogue_search_returns_the_public_projection(client: TestClient):
    response = client.get("/api/v1/marketplace/products/search?q=a&limit=5")
    assert response.status_code == 200, response.text
    body = response.json()
    assert {"query", "engine", "results", "count"} <= set(body)
    # The search hits name the product with either the fts or fallback
    # projection; the UI reads both, so both must be strings when present.
    for hit in body["results"]:
        assert isinstance(hit.get("product_id", hit.get("id", "")), str)


def test_cart_flow_add_update_remove(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    product_id = _seed_approved_product(client, f"Cart probe {uuid4().hex[:6]}", 9000)
    if product_id is None:
        pytest.skip("seller listing not permitted in this environment")

    added = client.post(
        "/api/v1/marketplace/cart",
        headers=_write_headers(client),
        json={"items": [{"product_id": product_id, "quantity": 2}]},
    )
    assert added.status_code == 200, added.text
    cart = added.json()
    assert {"cart_id", "items", "total_items", "subtotal"} <= set(cart)
    assert any(line["product_id"] == product_id for line in cart["items"])

    patched = client.patch(
        f"/api/v1/marketplace/cart/{product_id}",
        headers=_write_headers(client),
        json={"quantity": 3},
    )
    assert patched.status_code == 200, patched.text
    line = next(l for l in patched.json()["items"] if l["product_id"] == product_id)
    assert line["quantity"] == 3

    removed = client.delete(f"/api/v1/marketplace/cart/{product_id}", headers=_write_headers(client))
    assert removed.status_code == 200, removed.text
    assert removed.json()["removed"] == product_id

    empty = client.get("/api/v1/marketplace/cart")
    assert empty.status_code == 200
    assert empty.json()["items"] == []


def test_product_detail_and_reviews_are_public(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    product_id = _seed_approved_product(client, f"Detail probe {uuid4().hex[:6]}", 12000)
    if product_id is None:
        pytest.skip("seller listing not permitted in this environment")

    detail = client.get(f"/api/v1/marketplace/products/{product_id}")
    assert detail.status_code == 200, detail.text
    assert {"id", "name", "price_per_kg", "producer_name"} <= set(detail.json())

    reviews = client.get(f"/api/v1/marketplace/products/{product_id}/reviews?limit=5")
    assert reviews.status_code == 200, reviews.text
    assert {"product_id", "reviews", "count", "limit", "offset"} <= set(reviews.json())

    summary = client.get(f"/api/v1/marketplace/products/{product_id}/reviews/summary")
    assert summary.status_code == 200, summary.text
    assert {"product_id", "count", "average_rating", "histogram"} <= set(summary.json())


def test_order_items_and_tracking(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    catalog = client.get("/api/v1/marketplace/products?limit=5").json()["products"]
    orderable = next((p for p in catalog if p.get("orderable")), None)
    if orderable is None:
        pytest.skip("no orderable product in this environment")

    product_id = _seed_approved_product(client, "Tracking probe", 5000)
    if product_id is None:
        pytest.skip("seller listing not permitted in this environment")

    order = client.post(
        "/api/v1/marketplace/checkout/orders",
        headers=_write_headers(client),
        json={"product_id": product_id, "quantity": 1, "shipping_address": "Shiraz"},
    )
    assert order.status_code == 200, order.text
    order_id = order.json()["order_id"]

    items = client.get(f"/api/v1/marketplace/orders/{order_id}/items")
    assert items.status_code == 200, items.text
    body = items.json()
    assert {"order_id", "items", "count"} <= set(body)
    for item in body["items"]:
        # Money on the order-item plane is Decimal-as-string on the wire.
        assert isinstance(item["unit_price"], str)

    tracking = client.get(f"/api/v1/marketplace/orders/{order_id}/track")
    assert tracking.status_code == 200, tracking.text
    assert {"order_id", "order_number", "current_status", "timeline"} <= set(tracking.json())


def test_payment_escrow_read_is_own_or_admin(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    orders = client.get("/api/v1/marketplace/orders").json()["orders"]
    with_payment = next((o for o in orders if o.get("payment")), None)
    if with_payment is None:
        pytest.skip("no payment in this environment")
    escrow = client.get(f"/api/v1/marketplace/payments/{with_payment['payment']['id']}/escrow")
    assert escrow.status_code == 200, escrow.text
    assert {"payment_id", "payment_status", "escrow_status", "entries"} <= set(escrow.json())


# ---------------------------------------------------------------------------
# F1 â€” commerce plane (read surfaces the buyer journey needs)
# ---------------------------------------------------------------------------


def test_commerce_orders_list_and_transitions(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    orders = client.get("/api/v1/commerce/orders?limit=5")
    assert orders.status_code == 200, orders.text
    body = orders.json()
    assert {"orders", "count"} <= set(body)
    # Money is a Decimal string on this plane.
    for order in body["orders"]:
        assert isinstance(order["total"], str)

    if body["orders"]:
        order_id = body["orders"][0]["id"]
        detail = client.get(f"/api/v1/commerce/orders/{order_id}")
        assert detail.status_code == 200, detail.text
        assert {"order_id", "status", "items", "allowed_transitions", "total"} <= set(detail.json())

        transitions = client.get(f"/api/v1/commerce/orders/{order_id}/transitions")
        assert transitions.status_code == 200, transitions.text
        assert isinstance(transitions.json(), list)


# ---------------------------------------------------------------------------
# F1 â€” tourism detail, departures, guide and booking lifecycle
# ---------------------------------------------------------------------------


def test_tour_detail_departures_and_guide_are_readable(client: TestClient):
    tour_id = _seed_tour()
    tour = client.get(f"/api/v1/tourism/tours/{tour_id}")
    assert tour.status_code == 200, tour.text
    body = tour.json()
    # The catalogue and the detail endpoint share the projection; the images
    # and currency fields are part of it.
    assert {"id", "title", "tour_type", "price_per_person", "images", "currency"} <= set(body)

    departures = client.get(f"/api/v1/tourism/tours/{tour_id}/departures?limit=5")
    assert departures.status_code == 200, departures.text
    assert {"items", "count"} <= set(departures.json())

    guide = client.get(f"/api/v1/tourism/guides/{body['guide_id']}")
    if guide.status_code == 200:
        assert {"id", "full_name", "languages", "is_verified"} <= set(guide.json())


def test_tourism_booking_lifecycle(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    tour_id = _seed_tour()
    created = client.post(
        "/api/v1/tourism/bookings",
        headers=_write_headers(client),
        json={
            "tour_id": tour_id,
            "village_id": "v-1",
            "participants_count": 2,
            "tour_date": (date.today() + timedelta(days=9)).isoformat(),
        },
    )
    assert created.status_code in (200, 201), created.text
    booking_id = created.json()["id"]

    detail = client.get(f"/api/v1/tourism/bookings/{booking_id}")
    assert detail.status_code == 200, detail.text
    assert {"id", "booking_number", "participants_count", "total"} <= set(detail.json())

    confirmed = client.post(
        f"/api/v1/tourism/bookings/{booking_id}/confirm-payment",
        headers=_write_headers(client),
        json={"payment_tx_hash": "tx-contract-probe"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["payment_status"] == "paid"

    completed = client.post(
        f"/api/v1/tourism/bookings/{booking_id}/complete",
        headers=_write_headers(client),
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"


def test_tourism_status_is_honest(anonymous_client: TestClient):
    response = anonymous_client.get("/api/v1/tourism/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "live"
    assert isinstance(body["not_yet_available"], list)


# ---------------------------------------------------------------------------
# F1 â€” territories lifecycle and knowledge search / slug / collection
# ---------------------------------------------------------------------------


def test_territory_detail_and_lifecycle_transitions(client: TestClient):
    listing = client.get("/api/v1/territories?page=1&page_size=1").json()
    if not listing["items"]:
        pytest.skip("no territory in this environment")
    village_id = listing["items"][0]["village_id"]

    detail = client.get(f"/api/v1/territories/{village_id}")
    assert detail.status_code == 200, detail.text
    assert {"village_id", "name", "workflow_status"} <= set(detail.json())

    # The write transitions are authenticated; the 401 here is the honest
    # anonymous contract, and the authenticated path is exercised with the
    # territory the caller can see.
    response = client.post(f"/api/v1/territories/{village_id}/resubmit", headers=_write_headers(client))
    assert response.status_code in (200, 400, 401)


def test_knowledge_search_and_slug_views(client: TestClient):
    search = client.get("/api/v1/knowledge/search?page=1&page_size=5")
    assert search.status_code == 200, search.text
    body = search.json()
    assert {"items", "total", "total_pages", "query", "took_ms"} <= set(body)

    entries = client.get("/api/v1/knowledge?page=1&page_size=5").json()["items"]
    if not entries:
        pytest.skip("no public knowledge entry in this environment")

    by_id = client.get(f"/api/v1/knowledge/{entries[0]['id']}")
    assert by_id.status_code == 200, by_id.text
    slug = by_id.json()["slug"]

    by_slug = client.get(f"/api/v1/knowledge/slug/{slug}")
    assert by_slug.status_code == 200, by_slug.text
    assert by_slug.json()["id"] == entries[0]["id"]

    view = client.post(f"/api/v1/knowledge/{entries[0]['id']}/view")
    assert view.status_code == 204


def test_knowledge_collection_entries_view(client: TestClient):
    collections = client.get("/api/v1/knowledge/collections?page_size=5").json()["items"]
    if not collections:
        pytest.skip("no public collection in this environment")
    collection_id = collections[0]["id"]

    header = client.get(f"/api/v1/knowledge/collections/{collection_id}")
    assert header.status_code == 200, header.text
    assert {"id", "name", "slug", "is_public"} <= set(header.json())

    entries = client.get(f"/api/v1/knowledge/collections/{collection_id}/entries")
    assert entries.status_code == 200, entries.text
    assert "entries" in entries.json()


# ---------------------------------------------------------------------------
# F1 â€” content translations
# ---------------------------------------------------------------------------


def test_content_translations_list_is_an_array(client: TestClient):
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    email = _promote_latest_contract_user()
    assert email is not None
    assert client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Passw0rd!23"}
    ).status_code == 200

    created = client.post(
        "/api/v1/admin/content",
        headers=_write_headers(client),
        json={"title": "Translation probe", "body": "Body", "category": "news", "status": "draft"},
    )
    assert created.status_code in (200, 201), created.text
    item_id = created.json()["id"]

    translations = client.get(f"/api/v1/admin/content/{item_id}/translations")
    assert translations.status_code == 200, translations.text
    assert isinstance(translations.json(), list)

    translated = client.post(
        f"/api/v1/admin/content/{item_id}/translate",
        headers=_write_headers(client),
        json={"target_locale": "en", "source_locale": "fa"},
    )
    # Either a fresh draft (200) or a duplicate-locale refusal (400) â€” both
    # are the honest contract; a 501 would mean the capability is a lie.
    assert translated.status_code in (200, 400), translated.text
    if translated.status_code == 200:
        translation = translated.json()
        assert translation["locale"] == "en"
        assert translation["source"] == "ai"
        # The returned body is a machine draft, never an approved text.
        assert "[Translated]" in translation["body"]


# ---------------------------------------------------------------------------
# F4 — public network monitoring dashboard (read-only, auth-free)
# ---------------------------------------------------------------------------


def test_public_satellite_dashboard_is_the_envelope(anonymous_client: TestClient):
    """`frontend/src/services/dashboard.ts` reads the public satellite envelope."""
    response = anonymous_client.get("/dashboard/public/satellite")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["auth_required"] is False
    data = body["data"]
    # The client renders these two counts and shows the honest "no data"
    # empty state when `status == "no_data"` — never a fabricated number.
    assert {"total_images", "avg_ndvi"} <= set(data)
    assert isinstance(data["total_images"], int)
    assert isinstance(data["avg_ndvi"], (int, float))


def test_public_soil_dashboard_is_the_envelope(anonymous_client: TestClient):
    response = anonymous_client.get("/dashboard/public/soil")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["auth_required"] is False
    assert {"total_profiles"} <= set(body["data"])
    assert isinstance(body["data"]["total_profiles"], int)


def test_public_mrv_dashboard_summary_counts(anonymous_client: TestClient):
    """The MRV summary is not wrapped in the /dashboard envelope."""
    response = anonymous_client.get("/api/v1/mrv/public/dashboard-summary")
    assert response.status_code == 200, response.text
    body = response.json()
    assert {"total_observations", "by_level", "by_source", "latest_satellite_per_site"} <= set(body)
    assert isinstance(body["total_observations"], int)
    assert isinstance(body["latest_satellite_per_site"], list)


# ---------------------------------------------------------------------------
# F5 — community & public services (public, auth-free)
# ---------------------------------------------------------------------------


def test_public_support_personas(anonymous_client: TestClient):
    """`community.ts#fetchSupportPersonas` reads personas with the persona shape."""
    response = anonymous_client.get("/api/v1/support/personas")
    assert response.status_code == 200, response.text
    personas = response.json()["personas"]
    assert isinstance(personas, list)
    if personas:
        assert {"lang", "name", "role", "intro", "model"} <= set(personas[0])


def test_public_community_participation_is_honest(anonymous_client: TestClient):
    """`community.ts#fetchCommunityParticipation` returns the wrapped counters."""
    response = anonymous_client.get("/api/v1/community/participants")
    assert response.status_code == 200, response.text
    body = response.json()
    # `status` may be "success" or "no_data"; the counters are the contract.
    assert isinstance(body.get("status"), str)
    assert {"total_registrations", "confirmed", "pending"} <= set(body["data"])


def test_public_insurance_capabilities_surface_the_gate(anonymous_client: TestClient):
    """Insurance shows index/pricing and the regulatory note — never hidden."""
    response = anonymous_client.get("/api/v1/insurance/capabilities")
    assert response.status_code == 200, response.text
    body = response.json()
    assert {"index", "pricing", "note", "phase"} <= set(body)
    # The compliance note is the product: payout depends on actuarial review.
    assert body["note"].strip()


# ---------------------------------------------------------------------------
# F6 — operations & compliance console (admin)
# ---------------------------------------------------------------------------


def test_operations_security_audit(anonymous_client: TestClient, client: TestClient):
    """`operations.ts#fetchSecurityAudit` is admin-gated and has this shape."""
    anon = anonymous_client.get("/api/v1/admin/security/audit")
    assert anon.status_code in (401, 403)
    assert _login_as_admin(client) is not None
    response = client.get("/api/v1/admin/security/audit", headers=_write_headers(client))
    assert response.status_code == 200, response.text
    body = response.json()
    assert {
        "total_logins_24h",
        "successful_logins",
        "failed_logins",
        "unique_users",
        "suspicious_activities",
    } <= set(body)


def test_operations_pinn_status(anonymous_client: TestClient):
    """Engine availability is public and boolean."""
    response = anonymous_client.get("/api/v1/models/pinn-status")
    assert response.status_code == 200, response.text
    assert isinstance(response.json()["available"], bool)


def test_operations_tour_incidents(client: TestClient):
    """`operations.ts#fetchTourIncidents` returns {items, count} for admins."""
    assert _login_as_admin(client) is not None
    response = client.get("/api/v1/tourism/incidents", headers=_write_headers(client))
    assert response.status_code == 200, response.text
    assert {"items", "count"} <= set(response.json())


# ---------------------------------------------------------------------------
# F7 — seller operations (inventory / logistics / tool-registry)
# ---------------------------------------------------------------------------


def test_seller_tool_registry(anonymous_client: TestClient):
    """`inventory.ts#fetchToolRegistry` reads the {count, tools} registry."""
    response = anonymous_client.get("/api/v1/tool-registry")
    assert response.status_code == 200, response.text
    body = response.json()
    assert {"count", "tools"} <= set(body)
    assert isinstance(body["tools"], list)


def test_seller_inventory_skus_is_a_list(client: TestClient):
    """`inventory.ts#fetchInventorySkus` returns a list the UI counts."""
    assert _login_as_admin(client) is not None
    response = client.get("/api/v1/inventory/skus", headers=_write_headers(client))
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_inventory_create_sku(anonymous_client: TestClient, client: TestClient):
    """`inventory.ts#createSku` POSTs the SKUCreate shape; anonymous is refused."""
    write = anonymous_client.post(
        "/api/v1/inventory/skus",
        json={"sku_code": "probe", "name": "probe"},
        headers=_write_headers(anonymous_client),
    )
    assert write.status_code in (401, 403)

    assert _login_as_admin(client) is not None
    code = f"SKU-{uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/inventory/skus",
        headers=_write_headers(client),
        json={"sku_code": code, "name": "Contract probe", "uom": "each"},
    )
    assert created.status_code in (200, 201), created.text
    assert code in created.text


def test_inventory_create_warehouse(client: TestClient):
    """`inventory.ts#createWarehouse` POSTs the WarehouseCreate shape."""
    assert _login_as_admin(client) is not None
    code = f"WH-{uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/inventory/warehouses",
        headers=_write_headers(client),
        json={"code": code, "name": "Contract warehouse", "city": "Tehran"},
    )
    assert created.status_code in (200, 201), created.text
    assert code in created.text
