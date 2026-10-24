"""Tests for SA-V: buyer ratings & reviews (``MarketplaceReviewService``).

The e-commerce side had no rating model at all — the seller side carried a
rating column and the ecosystem a trust score, but a buyer could not rate a
purchase. These tests pin the rules that make such a rating trustworthy:

* the model round-trips on the shared ``Base`` with its defaults and its
  CHECK/UNIQUE constraints (rating 1..5, known status, one review per
  (order, reviewer, product));
* ``create_review`` refuses a rating outside 1..5, refuses an order that is not
  delivered, and refuses a duplicate of an existing (order, reviewer, product);
* ``approve``/``reject`` follow the documented status machine;
* ``mark_helpful`` counts one mark per user and no more;
* ``product_summary`` computes the average and the histogram in SQL, matching a
  hand computation;
* Persian and English reviews are both created, with the language detected.

Runs on an in-memory SQLite database with the shared Base metadata, async to
match the async service layer.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderStatus,
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceReview,
    MarketplaceReviewHelpful,
)
from services.marketplace.models.marketplace_review import detect_review_language
from services.marketplace.reviews import (
    DuplicateReviewError,
    MarketplaceReviewService,
    OrderNotDeliveredError,
    ReviewNotFoundError,
    ReviewStateError,
    ReviewValidationError,
)

BUYER = "buyer-1"
OTHER_BUYER = "buyer-2"
MODERATOR = "moderator-1"


@pytest.fixture
async def db_session():
    """An async in-memory SQLite session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def service(db_session):
    return MarketplaceReviewService(db_session)


async def _seed_product(db_session, product_id: str = "product-1") -> MarketplaceProduct:
    product = MarketplaceProduct(
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
    db_session.add(product)
    await db_session.commit()
    return product


async def _seed_order(
    db_session,
    *,
    order_id: str = "order-1",
    buyer_id: str = BUYER,
    status: MarketplaceOrderStatus = MarketplaceOrderStatus.DELIVERED,
) -> MarketplaceOrder:
    order = MarketplaceOrder(
        id=order_id,
        order_number=f"ORD-{order_id}",
        buyer_id=buyer_id,
        village_id="village-1",
        subtotal=Decimal("350000.00"),
        total=Decimal("350000.00"),
        status=status,
        payment_status="paid" if status is not MarketplaceOrderStatus.PENDING else "pending",
    )
    db_session.add(order)
    await db_session.commit()
    return order


async def _delivered_pair(
    service: MarketplaceReviewService,
    db_session,
    *,
    product_id: str = "product-1",
    order_id: str = "order-1",
    buyer_id: str = BUYER,
) -> tuple[str, str]:
    await _seed_product(db_session, product_id)
    await _seed_order(db_session, order_id=order_id, buyer_id=buyer_id)
    return product_id, order_id


# --- model round-trip on the shared Base ---


async def test_model_round_trip_on_shared_base(db_session):
    """A review row persists with its defaults and survives a reload."""
    await _seed_product(db_session)
    await _seed_order(db_session)

    review = MarketplaceReview(
        id="review-rt",
        product_id="product-1",
        order_id="order-1",
        reviewer_id=BUYER,
        rating=5,
        title="خوب بود",
        body="کیفیت عسل بالا بود.",
    )
    db_session.add(review)
    await db_session.commit()

    reloaded = await db_session.get(MarketplaceReview, "review-rt")
    assert reloaded is not None
    assert reloaded.product_id == "product-1"
    assert reloaded.order_id == "order-1"
    assert reloaded.reviewer_id == BUYER
    assert reloaded.rating == 5
    assert reloaded.language == "fa"  # column default: the platform's primary language
    assert reloaded.status == "pending"  # pending until a moderator decides it
    assert reloaded.helpful_count == 0
    assert reloaded.is_verified_purchase is False
    assert reloaded.created_at is not None
    assert reloaded.to_dict()["rating"] == 5


async def test_model_check_constraint_rejects_out_of_range_rating(db_session):
    """The CHECK backstop refuses a rating outside 1..5 at the DB level."""
    await _seed_product(db_session)
    await _seed_order(db_session)

    db_session.add(
        MarketplaceReview(
            id="review-bad",
            product_id="product-1",
            order_id="order-1",
            reviewer_id=BUYER,
            rating=9,
            status="pending",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_model_check_constraint_rejects_unknown_status(db_session):
    """The CHECK backstop refuses a status outside the lifecycle."""
    await _seed_product(db_session)
    await _seed_order(db_session)

    db_session.add(
        MarketplaceReview(
            id="review-bad-status",
            product_id="product-1",
            order_id="order-1",
            reviewer_id=BUYER,
            rating=4,
            status="published",  # not in (pending, approved, rejected)
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_model_unique_constraint_on_order_reviewer_product(db_session):
    """Two reviews for the same (order, reviewer, product) cannot exist."""
    await _seed_product(db_session)
    await _seed_order(db_session)

    for review_id in ("review-a", "review-b"):
        db_session.add(
            MarketplaceReview(
                id=review_id,
                product_id="product-1",
                order_id="order-1",
                reviewer_id=BUYER,
                rating=4,
                status="pending",
            )
        )
        try:
            await db_session.commit()
        except IntegrityError:
            await db_session.rollback()
            break
    else:  # pragma: no cover - the constraint must fire
        pytest.fail("the second review for the same triple was accepted")

    rows = await db_session.execute(select(func.count(MarketplaceReview.id)))
    assert rows.scalar_one() == 1


# --- create_review ---


async def test_create_review_defaults_to_pending_verified(service, db_session):
    """A review for a delivered order is created pending, language detected."""
    product_id, order_id = await _delivered_pair(service, db_session)

    review = await service.create_review(
        product_id=product_id,
        order_id=order_id,
        reviewer_id=BUYER,
        rating=5,
        title="کیفیت عالی",
        body="عسل خوشمزه و سالمی بود، حتما دوباره خرید می کنم.",
    )

    assert review.id
    assert review.status == "pending"
    assert review.is_verified_purchase is True  # set by the service from the order state
    assert review.language == "fa"
    assert review.helpful_count == 0


@pytest.mark.parametrize("rating", [0, 6, -1, 100])
async def test_create_review_rejects_out_of_range_rating(service, db_session, rating):
    product_id, order_id = await _delivered_pair(service, db_session)

    with pytest.raises(ReviewValidationError):
        await service.create_review(
            product_id=product_id,
            order_id=order_id,
            reviewer_id=BUYER,
            rating=rating,
        )


@pytest.mark.parametrize("rating", [4.5, "5", True, None])
async def test_create_review_rejects_non_integer_rating(service, db_session, rating):
    """A rating is an integer 1..5: a float, a string or a bool is refused."""
    product_id, order_id = await _delivered_pair(service, db_session)

    with pytest.raises(ReviewValidationError):
        await service.create_review(
            product_id=product_id,
            order_id=order_id,
            reviewer_id=BUYER,
            rating=rating,
        )


@pytest.mark.parametrize(
    "status",
    [
        MarketplaceOrderStatus.PENDING,
        MarketplaceOrderStatus.PAID,
        MarketplaceOrderStatus.PROCESSING,
        MarketplaceOrderStatus.SHIPPED,
        MarketplaceOrderStatus.CANCELLED,
        MarketplaceOrderStatus.REFUNDED,
    ],
)
async def test_create_review_rejects_undelivered_order(service, db_session, status):
    """Only a delivered order may be reviewed — every other state is refused."""
    product_id, order_id = await _delivered_pair(service, db_session)
    await _seed_order(
        db_session, order_id="order-undelivered", buyer_id=BUYER, status=status
    )

    with pytest.raises(OrderNotDeliveredError):
        await service.create_review(
            product_id=product_id,
            order_id="order-undelivered",
            reviewer_id=BUYER,
            rating=5,
        )


async def test_create_review_rejects_unknown_order(service, db_session):
    product_id, _ = await _delivered_pair(service, db_session)

    with pytest.raises(ReviewNotFoundError):
        await service.create_review(
            product_id=product_id,
            order_id="no-such-order",
            reviewer_id=BUYER,
            rating=5,
        )


async def test_create_review_rejects_duplicate(service, db_session):
    """One review per (order, reviewer, product)."""
    product_id, order_id = await _delivered_pair(service, db_session)

    await service.create_review(
        product_id=product_id,
        order_id=order_id,
        reviewer_id=BUYER,
        rating=4,
    )
    with pytest.raises(DuplicateReviewError):
        await service.create_review(
            product_id=product_id,
            order_id=order_id,
            reviewer_id=BUYER,
            rating=2,
        )


async def test_same_buyer_may_review_a_different_product_or_order(service, db_session):
    """The uniqueness is per (order, reviewer, product), not per reviewer."""
    product_id, order_id = await _delivered_pair(service, db_session)
    await _seed_product(db_session, "product-2")
    await _seed_order(db_session, order_id="order-2")

    first = await service.create_review(
        product_id=product_id, order_id=order_id, reviewer_id=BUYER, rating=4
    )
    second = await service.create_review(
        product_id="product-2", order_id=order_id, reviewer_id=BUYER, rating=3
    )
    third = await service.create_review(
        product_id=product_id, order_id="order-2", reviewer_id=BUYER, rating=5
    )
    assert len({first.id, second.id, third.id}) == 3


async def test_different_reviewers_may_review_the_same_order(service, db_session):
    """The triple is (order, reviewer, product): another buyer is a new triple."""
    product_id, order_id = await _delivered_pair(service, db_session)

    mine = await service.create_review(
        product_id=product_id, order_id=order_id, reviewer_id=BUYER, rating=4
    )
    theirs = await service.create_review(
        product_id=product_id, order_id=order_id, reviewer_id=OTHER_BUYER, rating=2
    )
    assert mine.id != theirs.id


# --- moderation status machine ---


async def test_approve_publishes_a_pending_review(service, db_session):
    product_id, order_id = await _delivered_pair(service, db_session)
    review = await service.create_review(
        product_id=product_id, order_id=order_id, reviewer_id=BUYER, rating=5
    )

    approved = await service.approve(review.id, MODERATOR)

    assert approved.status == "approved"
    assert approved.moderated_by == MODERATOR


async def test_reject_hides_a_pending_review(service, db_session):
    product_id, order_id = await _delivered_pair(service, db_session)
    review = await service.create_review(
        product_id=product_id, order_id=order_id, reviewer_id=BUYER, rating=1,
        title="بد", body="محصول مطابق توضیحات نبود.",
    )

    rejected = await service.reject(review.id, MODERATOR, reason="off-topic")

    assert rejected.status == "rejected"
    assert rejected.moderated_by == MODERATOR
    assert rejected.body  # the buyer's text is never rewritten by the moderator


async def test_double_approval_is_refused(service, db_session):
    """A decided review cannot be re-decided into the state it is already in."""
    product_id, order_id = await _delivered_pair(service, db_session)
    review = await service.create_review(
        product_id=product_id, order_id=order_id, reviewer_id=BUYER, rating=5
    )
    await service.approve(review.id, MODERATOR)

    with pytest.raises(ReviewStateError):
        await service.approve(review.id, MODERATOR)

    # Re-moderation may reverse a decision, but only into the other state.
    re_rejected = await service.reject(review.id, MODERATOR)
    assert re_rejected.status == "rejected"

    with pytest.raises(ReviewStateError):
        await service.reject(review.id, MODERATOR)

    re_approved = await service.approve(review.id, MODERATOR)
    assert re_approved.status == "approved"


async def test_moderating_an_unknown_review_is_a_typed_404(service, db_session):
    with pytest.raises(ReviewNotFoundError):
        await service.approve("no-such-review", MODERATOR)
    with pytest.raises(ReviewNotFoundError):
        await service.reject("no-such-review", MODERATOR)


# --- helpful marks ---


async def test_mark_helpful_counts_one_per_user(service, db_session):
    product_id, order_id = await _delivered_pair(service, db_session)
    review = await service.create_review(
        product_id=product_id, order_id=order_id, reviewer_id=BUYER, rating=5
    )

    assert await service.mark_helpful(review.id, "reader-1") == 1
    assert await service.mark_helpful(review.id, "reader-1") == 1  # no double counting
    assert await service.mark_helpful(review.id, "reader-2") == 2

    reloaded = await service.get_review(review.id)
    assert reloaded.helpful_count == 2

    marks = await db_session.execute(select(func.count(MarketplaceReviewHelpful.id)))
    assert marks.scalar_one() == 2


async def test_mark_helpful_on_unknown_review_is_a_typed_404(service, db_session):
    with pytest.raises(ReviewNotFoundError):
        await service.mark_helpful("no-such-review", "reader-1")


# --- aggregates computed in SQL ---


async def test_product_summary_matches_a_hand_computation(service, db_session):
    """count / average / histogram come from SQL and match the hand maths."""
    product_id, order_id = await _delivered_pair(service, db_session)
    await _seed_order(db_session, order_id="order-2", buyer_id=OTHER_BUYER)
    await _seed_product(db_session, "other-product")

    ratings = [4, 5, 5, 2, 1]
    for index, rating in enumerate(ratings):
        await service.create_review(
            product_id=product_id,
            order_id="order-2" if index == 4 else order_id,
            reviewer_id=f"buyer-{index}",
            rating=rating,
        )
    # A review on another product must not leak into this product's aggregates.
    await service.create_review(
        product_id="other-product",
        order_id="order-2",
        reviewer_id=OTHER_BUYER,
        rating=5,
    )

    summary = await service.product_summary(product_id)

    assert summary["count"] == 5
    assert summary["average_rating"] == round(sum(ratings) / len(ratings), 2)
    assert summary["average_rating"] == 3.4  # 17 / 5, rounded to 2 dp
    assert summary["histogram"] == {1: 1, 2: 1, 3: 0, 4: 1, 5: 2}


async def test_product_summary_of_an_unrated_product_is_zeroed(service, db_session):
    summary = await service.product_summary("product-nobody-reviewed")

    assert summary == {
        "product_id": "product-nobody-reviewed",
        "count": 0,
        "average_rating": 0.0,
        "histogram": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
    }


# --- languages ---


def test_detect_review_language_persian_and_english():
    assert detect_review_language("این عسل خیلی خوب بود") == "fa"
    assert detect_review_language("Great honey, fast delivery") == "en"
    assert detect_review_language("12345 !!!") == "en"  # no script: the platform default
    # dominant script wins a mixed text
    assert detect_review_language("سلام hello سلام hello سلام") == "fa"


async def test_create_review_detects_persian_and_english(service, db_session):
    product_id, order_id = await _delivered_pair(service, db_session)
    await _seed_order(db_session, order_id="order-en", buyer_id=OTHER_BUYER)

    fa = await service.create_review(
        product_id=product_id,
        order_id=order_id,
        reviewer_id=BUYER,
        rating=5,
        title="کیفیت عالی",
        body="عسل خوشمزه و با کیفیت.",
    )
    en = await service.create_review(
        product_id=product_id,
        order_id="order-en",
        reviewer_id=OTHER_BUYER,
        rating=3,
        title="Decent",
        body="Good honey but the delivery was slow.",
    )

    assert (fa.language, en.language) == ("fa", "en")

    # Only a moderated review is public, so the listing sees neither yet.
    assert await service.list_product_reviews(product_id, language="fa") == []

    await service.approve(fa.id, MODERATOR)
    await service.approve(en.id, MODERATOR)

    listed_fa = await service.list_product_reviews(product_id, language="fa")
    assert [r.id for r in listed_fa] == [fa.id]
    listed_en = await service.list_product_reviews(product_id, language="en")
    assert [r.id for r in listed_en] == [en.id]


async def test_create_review_rejects_an_unsupported_language(service, db_session):
    product_id, order_id = await _delivered_pair(service, db_session)

    with pytest.raises(ReviewValidationError):
        await service.create_review(
            product_id=product_id,
            order_id=order_id,
            reviewer_id=BUYER,
            rating=5,
            language="de",
        )


# --- listing ---


async def test_listing_shows_only_approved_reviews_with_paging(service, db_session):
    product_id, order_id = await _delivered_pair(service, db_session)
    extra_orders = ["order-a", "order-b", "order-c"]
    for extra in extra_orders:
        await _seed_order(db_session, order_id=extra, buyer_id=f"buyer-{extra}")
    for extra in extra_orders:
        await service.create_review(
            product_id=product_id,
            order_id=extra,
            reviewer_id=f"buyer-{extra}",
            rating=5,
            title=f"review-{extra}",
        )

    pending = await service.list_product_reviews(product_id)
    assert pending == []  # nothing is public before moderation

    review_rows = (await db_session.execute(select(MarketplaceReview))).scalars().all()
    for row in review_rows:
        await service.approve(row.id, MODERATOR)

    approved = await service.list_product_reviews(product_id)
    assert len(approved) == len(extra_orders)

    page = await service.list_product_reviews(product_id, limit=2, offset=0)
    assert len(page) == 2
    second_page = await service.list_product_reviews(product_id, limit=2, offset=2)
    assert len(second_page) == 1
    assert not {r.id for r in page} & {r.id for r in second_page}

    pending_rows = await service.list_product_reviews(product_id, status="pending")
    assert pending_rows == []
