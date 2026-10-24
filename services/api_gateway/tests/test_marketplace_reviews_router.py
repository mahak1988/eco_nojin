"""HTTP regression tests for the marketplace reviews router (SA-V).

Covers the end-to-end buyer flow the e-commerce side was missing entirely:
``POST create -> (pending, not public) -> moderator approve -> public listing ->
summary -> helpful marks``, plus the refusals that keep the rating trustworthy
(undelivered order, duplicate, unknown product/review, non-admin moderation).

The router takes an ``AsyncSession`` (its service is an async-session service),
so the fixture is the dependency-override pattern of
``services/api_gateway/tests/test_http_village_hub.py``: a minimal app over a
private in-memory SQLite engine, with the auth dependencies replaced by plain
principals. The other marketplace router tests repoint
``database.config.SessionLocal`` instead, because those routes open their own
*sync* ``hub.get_session()``.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.api_gateway.auth import get_current_user, require_admin, require_user
from services.api_gateway.routers.marketplace_reviews import get_db, router
from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderStatus,
    MarketplaceProduct,
    MarketplaceProductStatus,
)

BUYER = "buyer-1"
OTHER_BUYER = "buyer-2"
ADMIN = "admin-1"


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


def _build_app(session, *, user_id: str = BUYER, role: str = "buyer", admin: bool = True):
    app = FastAPI()
    app.include_router(router)

    async def db_override():
        yield session

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id=user_id, role=role)
    if admin:
        app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id=ADMIN, role="admin")
    else:
        # Leave ``require_admin`` real so the RBAC guard itself is exercised.
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=user_id, role=role
        )
    return app


async def _request(app, method: str, path: str, payload: dict | None = None, params=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path, json=payload, params=params)


async def _seed_product(session, product_id: str = "product-1") -> None:
    session.add(
        MarketplaceProduct(
            id=product_id,
            seller_id="seller-1",
            name="عسل طبیعی",
            slug=f"asal-{product_id}",
            category="food",
            price=Decimal("350000.00"),
            stock=10,
            unit="piece",
            village_id="village-1",
            status=MarketplaceProductStatus.APPROVED,
        )
    )
    await session.commit()


async def _seed_order(
    session,
    *,
    order_id: str = "order-1",
    buyer_id: str = BUYER,
    status: MarketplaceOrderStatus = MarketplaceOrderStatus.DELIVERED,
) -> None:
    session.add(
        MarketplaceOrder(
            id=order_id,
            order_number=f"ORD-{order_id}",
            buyer_id=buyer_id,
            village_id="village-1",
            subtotal=Decimal("350000.00"),
            total=Decimal("350000.00"),
            status=status,
            payment_status="paid" if status is not MarketplaceOrderStatus.PENDING else "pending",
        )
    )
    await session.commit()


async def _seed_reviewable_product(session, product_id: str = "product-1") -> None:
    await _seed_product(session, product_id)
    await _seed_order(session, order_id=f"order-{product_id}", buyer_id=BUYER)


REVIEW_PATH = "/api/v1/marketplace/products/{product_id}/reviews"


def _create_payload(
    rating: int = 5,
    title: str = "کیفیت عالی",
    order_id: str = "order-product-1",
) -> dict:
    return {
        "order_id": order_id,
        "rating": rating,
        "title": title,
        "body": "عسل خوشمزه و سالمی بود.",
    }


# JSON object keys are strings, so the {1..5} histogram crosses the wire with
# string keys — the counts and the 2-dp average are what matter.
def _histogram(counts: dict[int, int] | None = None) -> dict:
    histogram = {str(rating): 0 for rating in range(1, 6)}
    for rating, count in (counts or {}).items():
        histogram[str(rating)] = count
    return histogram


_EMPTY_HISTOGRAM = _histogram()


# --- the happy path the marketplace was missing ---


async def test_create_review_is_pending_until_a_moderator_approves_it(session):
    """create -> invisible -> approve -> visible."""
    await _seed_reviewable_product(session)
    app = _build_app(session)

    created = await _request(
        app, "POST", REVIEW_PATH.format(product_id="product-1"), _create_payload()
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "pending"
    review = body["review"]
    assert review["rating"] == 5
    assert review["language"] == "fa"
    assert review["is_verified_purchase"] is True
    assert review["helpful_count"] == 0
    review_id = review["id"]

    # Pending: not public yet.
    listing = await _request(app, "GET", REVIEW_PATH.format(product_id="product-1"))
    assert listing.status_code == 200
    assert listing.json()["count"] == 0

    approved = await _request(
        app,
        "POST",
        f"/api/v1/marketplace/products/product-1/reviews/{review_id}/approve",
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["review"]["status"] == "approved"

    listing = await _request(app, "GET", REVIEW_PATH.format(product_id="product-1"))
    assert listing.status_code == 200
    reviews = listing.json()["reviews"]
    assert [r["id"] for r in reviews] == [review_id]
    assert reviews[0]["status"] == "approved"
    assert reviews[0]["title"] == "کیفیت عالی"


async def test_full_flow_create_approve_list_summary_helpful(session):
    """The documented end-to-end flow, exercised over one product."""
    await _seed_reviewable_product(session)
    app = _build_app(session)

    created = await _request(
        app, "POST", REVIEW_PATH.format(product_id="product-1"), _create_payload()
    )
    assert created.status_code == 201, created.text
    review_id = created.json()["review"]["id"]

    # Summary counts the review before moderation (the aggregate is over every
    # review for the product, so the figure a buyer reads is not delayed by it).
    summary = await _request(app, "GET", REVIEW_PATH.format(product_id="product-1") + "/summary")
    assert summary.status_code == 200
    assert summary.json() == {
        "product_id": "product-1",
        "count": 1,
        "average_rating": 5.0,
        "histogram": _histogram({5: 1}),
    }

    approve_path = f"/api/v1/marketplace/products/product-1/reviews/{review_id}/approve"
    await _request(app, "POST", approve_path)
    listing = await _request(app, "GET", REVIEW_PATH.format(product_id="product-1"))
    assert listing.json()["count"] == 1

    helpful = await _request(
        app, "POST", f"/api/v1/marketplace/products/product-1/reviews/{review_id}/helpful"
    )
    assert helpful.status_code == 200, helpful.text
    assert helpful.json()["helpful_count"] == 1

    # One helpful mark per user: a second one by the same user changes nothing.
    again = await _request(
        app, "POST", f"/api/v1/marketplace/products/product-1/reviews/{review_id}/helpful"
    )
    assert again.status_code == 200
    assert again.json()["helpful_count"] == 1

    # A different user is a new mark.
    other_app = _build_app(session, user_id=OTHER_BUYER)
    other = await _request(
        other_app, "POST", f"/api/v1/marketplace/products/product-1/reviews/{review_id}/helpful"
    )
    assert other.json()["helpful_count"] == 2

    listing = await _request(app, "GET", REVIEW_PATH.format(product_id="product-1"))
    assert listing.json()["reviews"][0]["helpful_count"] == 2


async def test_summary_average_matches_a_hand_computation(session):
    """The SQL aggregate agrees with the arithmetic a buyer would do."""
    await _seed_reviewable_product(session)
    await _seed_order(session, order_id="order-other-1", buyer_id=OTHER_BUYER)
    await _seed_order(session, order_id="order-other-2", buyer_id="buyer-3")
    app = _build_app(session)

    ratings = [5, 4, 2]  # average 3.67 (11 / 3 rounded to 2 dp)
    order_ids = ["order-product-1", "order-other-1", "order-other-2"]
    for rating, order_id in zip(ratings, order_ids, strict=True):
        created = await _request(
            app,
            "POST",
            REVIEW_PATH.format(product_id="product-1"),
            _create_payload(rating=rating, title="نقد", order_id=order_id),
        )
        assert created.status_code == 201, created.text

    summary = await _request(app, "GET", REVIEW_PATH.format(product_id="product-1") + "/summary")
    body = summary.json()
    assert body["count"] == 3
    assert body["average_rating"] == round(sum(ratings) / len(ratings), 2)
    assert body["average_rating"] == 3.67
    assert body["histogram"] == _histogram({2: 1, 4: 1, 5: 1})


# --- refusals ---


async def test_create_review_requires_an_authenticated_user(session):
    await _seed_reviewable_product(session)
    app = FastAPI()
    app.include_router(router)

    async def db_override():
        yield session

    app.dependency_overrides[get_db] = db_override
    # No auth override at all: the real dependency must refuse.
    response = await _request(
        app, "POST", REVIEW_PATH.format(product_id="product-1"), _create_payload()
    )
    assert response.status_code == 401


async def test_rating_outside_1_to_5_is_rejected(session):
    await _seed_reviewable_product(session)
    app = _build_app(session)

    for rating in (0, 6, -2):
        response = await _request(
            app,
            "POST",
            REVIEW_PATH.format(product_id="product-1"),
            _create_payload(rating=rating),
        )
        assert response.status_code == 422, (rating, response.text)


async def test_review_of_an_undelivered_order_is_rejected(session):
    await _seed_product(session)
    await _seed_order(session, order_id="order-pending", status=MarketplaceOrderStatus.PENDING)
    app = _build_app(session)

    response = await _request(
        app,
        "POST",
        REVIEW_PATH.format(product_id="product-1"),
        {"order_id": "order-pending", "rating": 5, "title": "هنوز نرسیده"},
    )
    assert response.status_code == 400, response.text


async def test_duplicate_review_is_a_conflict(session):
    await _seed_reviewable_product(session)
    app = _build_app(session)

    first = await _request(
        app, "POST", REVIEW_PATH.format(product_id="product-1"), _create_payload()
    )
    assert first.status_code == 201

    duplicate = await _request(
        app, "POST", REVIEW_PATH.format(product_id="product-1"), _create_payload(rating=3)
    )
    assert duplicate.status_code == 409, duplicate.text


async def test_review_of_an_unknown_product_is_404(session):
    await _seed_reviewable_product(session)
    app = _build_app(session)

    response = await _request(
        app,
        "POST",
        REVIEW_PATH.format(product_id="no-such-product"),
        {"order_id": "order-product-1", "rating": 5},
    )
    assert response.status_code == 404, response.text


async def test_moderating_an_unknown_review_is_404(session):
    await _seed_reviewable_product(session)
    app = _build_app(session)

    for action in ("approve", "reject", "helpful"):
        response = await _request(
            app,
            "POST",
            f"/api/v1/marketplace/products/product-1/reviews/no-such-review/{action}",
        )
        assert response.status_code == 404, (action, response.text)


async def test_only_an_admin_may_moderate(session):
    await _seed_reviewable_product(session)
    admin_app = _build_app(session)
    created = await _request(
        admin_app, "POST", REVIEW_PATH.format(product_id="product-1"), _create_payload()
    )
    review_id = created.json()["review"]["id"]

    buyer_app = _build_app(session, user_id=BUYER, role="buyer", admin=False)
    response = await _request(
        buyer_app, "POST", f"/api/v1/marketplace/products/product-1/reviews/{review_id}/approve"
    )
    assert response.status_code == 403, response.text


async def test_rejected_review_is_not_listed(session):
    await _seed_reviewable_product(session)
    app = _build_app(session)

    created = await _request(
        app, "POST", REVIEW_PATH.format(product_id="product-1"), _create_payload()
    )
    review_id = created.json()["review"]["id"]

    rejected = await _request(
        app, "POST", f"/api/v1/marketplace/products/product-1/reviews/{review_id}/reject",
        params={"reason": "spam"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["review"]["status"] == "rejected"

    listing = await _request(app, "GET", REVIEW_PATH.format(product_id="product-1"))
    assert listing.json()["count"] == 0


# --- language filter + paging ---


async def test_language_filter_and_paging(session):
    await _seed_reviewable_product(session)
    await _seed_order(session, order_id="order-en", buyer_id=OTHER_BUYER)
    app = _build_app(session)

    persian = await _request(
        app,
        "POST",
        REVIEW_PATH.format(product_id="product-1"),
        _create_payload(title="خوب بود"),
    )
    assert persian.status_code == 201
    english = await _request(
        app,
        "POST",
        REVIEW_PATH.format(product_id="product-1"),
        {
            "order_id": "order-en",
            "rating": 3,
            "title": "Decent",
            "body": "Good honey, slow delivery.",
        },
    )
    assert english.status_code == 201
    assert english.json()["review"]["language"] == "en"

    fa_id = persian.json()["review"]["id"]
    en_id = english.json()["review"]["id"]

    for review_id in (fa_id, en_id):
        approved = await _request(
            app, "POST", f"/api/v1/marketplace/products/product-1/reviews/{review_id}/approve"
        )
        assert approved.status_code == 200

    listing_path = REVIEW_PATH.format(product_id="product-1")

    fa_only = await _request(app, "GET", listing_path, params={"lang": "fa"})
    assert [r["id"] for r in fa_only.json()["reviews"]] == [fa_id]

    en_only = await _request(app, "GET", listing_path, params={"lang": "en"})
    assert [r["id"] for r in en_only.json()["reviews"]] == [en_id]

    page_one = await _request(app, "GET", listing_path, params={"limit": 1})
    assert page_one.json()["count"] == 1
    page_two = await _request(app, "GET", listing_path, params={"limit": 1, "offset": 1})
    assert page_two.json()["count"] == 1
    assert page_one.json()["reviews"][0]["id"] != page_two.json()["reviews"][0]["id"]

    bad_lang = await _request(app, "GET", listing_path, params={"lang": "de"})
    assert bad_lang.status_code == 422


async def test_summary_of_an_unreviewed_product_is_zeroed(session):
    app = _build_app(session)
    summary = await _request(app, "GET", REVIEW_PATH.format(product_id="product-9") + "/summary")
    assert summary.status_code == 200
    assert summary.json() == {
        "product_id": "product-9",
        "count": 0,
        "average_rating": 0.0,
        "histogram": _EMPTY_HISTOGRAM,
    }
