"""MarketplaceReviewService — buyer ratings & reviews (plan v2.1, SA-V).

The e-commerce side had no way for a buyer to rate a purchase, while the
seller side already carried a rating column and the ecosystem a trust score.
This service is the missing half, and it keeps the trust rules server-side:

* a rating is an integer 1..5 — the CheckConstraint on the row is the backstop,
  the validation here is the honest, typed refusal;
* a review may only exist for a **delivered** order
  (``MarketplaceOrderStatus.DELIVERED``), so ``is_verified_purchase`` is set by
  the service from the order state instead of being asserted by the client;
* one review per (order, reviewer, product) — the unique constraint is the
  backstop, the explicit check here is the typed refusal;
* ``pending`` by default, and only a moderator moves a review to
  ``approved`` (public) or ``rejected`` (hidden);
* one "helpful" mark per user per review — the unique constraint on
  ``MarketplaceReviewHelpful`` is the guarantee, the count is denormalised on
  the review for cheap reads;
* aggregates (count / average / histogram) are computed in SQL.
"""

from __future__ import annotations

import logging

from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderStatus,
    MarketplaceReview,
    MarketplaceReviewHelpful,
)
from services.marketplace.models.marketplace_review import (
    REVIEW_MAX_RATING,
    REVIEW_MIN_RATING,
    REVIEW_STATUSES,
    detect_review_language,
)

logger = logging.getLogger(__name__)

#: Languages a review may be written in, matching the platform's bilingual
#: (Persian-first / English) public surface.
SUPPORTED_REVIEW_LANGUAGES = ("fa", "en")


class ReviewError(ValueError):
    """Base typed error for the review flow."""


class ReviewValidationError(ReviewError):
    """The payload itself is invalid (rating, language)."""


class OrderNotDeliveredError(ReviewError):
    """A review may only be written for a delivered order."""


class DuplicateReviewError(ReviewError):
    """The (order, reviewer, product) triple already has a review."""


class ReviewNotFoundError(ReviewError):
    """No review (or row a review depends on) with that id."""


class ReviewStateError(ReviewError):
    """The status machine refuses the requested transition."""


#: The moderation status machine. A review is born ``pending``; a decided
#: review may be re-decided in the opposite direction (a moderator reversing a
#: mistake) but never re-decided into the state it is already in.
REVIEW_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"approved", "rejected"}),
    "approved": frozenset({"rejected"}),
    "rejected": frozenset({"approved"}),
}


class MarketplaceReviewService:
    """Ratings and reviews for marketplace products, over an ``AsyncSession``."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- reads -------------------------------------------------------------

    async def get_review(self, review_id: str) -> MarketplaceReview:
        """One review by id, or a typed 404-style error."""
        review = await self.db.get(MarketplaceReview, str(review_id))
        if review is None:
            raise ReviewNotFoundError(f"review not found: {review_id}")
        return review

    async def list_product_reviews(
        self,
        product_id: str,
        *,
        language: str | None = None,
        status: str = "approved",
        limit: int = 20,
        offset: int = 0,
    ) -> list[MarketplaceReview]:
        """Approved-by-default listing of a product's reviews, newest first.

        ``language`` filters on the detected review language (``fa``/``en``) and
        ``status`` is a parameter so a moderator surface can read ``pending``
        without a second method.
        """
        stmt = select(MarketplaceReview).where(
            MarketplaceReview.product_id == str(product_id),
            MarketplaceReview.status == status,
        )
        if language:
            stmt = stmt.where(MarketplaceReview.language == language)
        stmt = stmt.order_by(
            MarketplaceReview.created_at.desc(), MarketplaceReview.id.desc()
        ).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def product_summary(self, product_id: str) -> dict:
        """Count, average rating and the {1..5} histogram for a product.

        The three aggregates are computed in SQL (``func.count`` /
        ``func.avg`` / ``GROUP BY``), never by pulling rows into Python. The
        average covers every review for the product regardless of moderation
        status — the same population the histogram counts.
        """
        product_id = str(product_id)

        totals = (
            await self.db.execute(
                select(
                    func.count(MarketplaceReview.id),
                    func.avg(MarketplaceReview.rating),
                ).where(MarketplaceReview.product_id == product_id)
            )
        ).one()
        count = int(totals[0] or 0)
        average = totals[1]
        average_rating = round(float(average), 2) if average is not None else 0.0

        histogram_rows = (
            await self.db.execute(
                select(MarketplaceReview.rating, func.count(MarketplaceReview.id))
                .where(MarketplaceReview.product_id == product_id)
                .group_by(MarketplaceReview.rating)
            )
        ).all()
        histogram = dict.fromkeys(range(REVIEW_MIN_RATING, REVIEW_MAX_RATING + 1), 0)
        for rating, bucket_count in histogram_rows:
            if rating is None:
                continue
            histogram[int(rating)] = int(bucket_count)

        return {
            "product_id": product_id,
            "count": count,
            "average_rating": average_rating,
            "histogram": histogram,
        }

    # --- writes ------------------------------------------------------------

    async def create_review(
        self,
        product_id: str,
        order_id: str,
        reviewer_id: str,
        rating: int,
        title: str | None = None,
        body: str | None = None,
        language: str | None = None,
    ) -> MarketplaceReview:
        """Write a buyer review for one product from one delivered order.

        Refuses a rating outside 1..5, an order that is not delivered, and a
        second review for the same (order, reviewer, product). The new row is
        ``pending`` until a moderator decides it.
        """
        if isinstance(rating, bool) or not isinstance(rating, int):
            raise ReviewValidationError(
                f"rating must be an integer between {REVIEW_MIN_RATING} and {REVIEW_MAX_RATING}"
            )
        if not REVIEW_MIN_RATING <= rating <= REVIEW_MAX_RATING:
            raise ReviewValidationError(
                f"rating must be between {REVIEW_MIN_RATING} and {REVIEW_MAX_RATING}, got {rating}"
            )

        detected_language = self._resolve_language(language, title, body)

        order = await self.db.get(MarketplaceOrder, str(order_id))
        if order is None:
            raise ReviewNotFoundError(f"order not found: {order_id}")
        if order.status != MarketplaceOrderStatus.DELIVERED:
            raise OrderNotDeliveredError(
                f"order {order_id} is {order.status}, not "
                f"{MarketplaceOrderStatus.DELIVERED}; only a delivered order may be reviewed"
            )

        await self._assert_no_duplicate(order_id, reviewer_id, product_id)

        # Set from the order state, never from the request: a review that
        # exists has already been accepted against a delivered order.
        review = MarketplaceReview(
            product_id=str(product_id),
            order_id=str(order_id),
            reviewer_id=str(reviewer_id),
            rating=rating,
            title=title,
            body=body,
            language=detected_language,
            is_verified_purchase=order.status == MarketplaceOrderStatus.DELIVERED,
            helpful_count=0,
            status="pending",
        )
        self.db.add(review)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            # Only a unique violation on the triple is the race; anything else
            # (an FK-enforcing deployment rejecting a product that does not
            # exist) is the real error and must surface as itself.
            try:
                await self._assert_no_duplicate(order_id, reviewer_id, product_id)
            except DuplicateReviewError as duplicate:
                raise duplicate from exc
            raise
        await self.db.refresh(review)
        return review

    async def approve(self, review_id: str, moderator_id: str) -> MarketplaceReview:
        """Moderator: publish a pending review."""
        return await self._moderate(review_id, moderator_id, "approved")

    async def reject(
        self, review_id: str, moderator_id: str, reason: str | None = None
    ) -> MarketplaceReview:
        """Moderator: hide a pending review. ``reason`` is logged, never written
        over the buyer's text."""
        return await self._moderate(review_id, moderator_id, "rejected", reason=reason)

    async def mark_helpful(self, review_id: str, user_id: str) -> int:
        """Mark a review helpful; one mark per user, and return the new count.

        A repeat mark by the same user is a no-op that returns the unchanged
        count — "no double counting" is enforced by the unique constraint on
        (review, user), so even a racing pair of marks cannot inflate it, and
        the tally itself is incremented in SQL rather than read-modify-written.
        """
        review = await self.get_review(review_id)
        already = await self.db.execute(
            select(MarketplaceReviewHelpful.id).where(
                and_(
                    MarketplaceReviewHelpful.review_id == review.id,
                    MarketplaceReviewHelpful.user_id == str(user_id),
                )
            )
        )
        if already.scalar_one_or_none() is not None:
            return await self._helpful_count(review_id)

        self.db.add(MarketplaceReviewHelpful(review_id=review.id, user_id=str(user_id)))
        try:
            await self.db.execute(
                update(MarketplaceReview)
                .where(MarketplaceReview.id == review.id)
                .values(helpful_count=MarketplaceReview.helpful_count + 1)
            )
            await self.db.commit()
        except IntegrityError:
            # Lost a race with an identical mark: the row already exists, so
            # keep the count as the unique constraint left it.
            await self.db.rollback()
        return await self._helpful_count(review_id)

    # --- internals ---------------------------------------------------------

    async def _helpful_count(self, review_id: str) -> int:
        """Read the tally straight from the row (never a cached attribute)."""
        count = (
            await self.db.execute(
                select(MarketplaceReview.helpful_count).where(
                    MarketplaceReview.id == str(review_id)
                )
            )
        ).scalar_one_or_none()
        return int(count or 0)

    async def _assert_no_duplicate(
        self, order_id: str, reviewer_id: str, product_id: str
    ) -> None:
        existing = await self.db.execute(
            select(MarketplaceReview.id).where(
                and_(
                    MarketplaceReview.order_id == str(order_id),
                    MarketplaceReview.reviewer_id == str(reviewer_id),
                    MarketplaceReview.product_id == str(product_id),
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateReviewError(
                f"a review for order {order_id} by {reviewer_id} on product "
                f"{product_id} already exists"
            )

    async def _moderate(
        self, review_id: str, moderator_id: str, target: str, reason: str | None = None
    ) -> MarketplaceReview:
        review = await self.get_review(review_id)
        allowed = REVIEW_TRANSITIONS.get(str(review.status), frozenset())
        if target not in allowed:
            raise ReviewStateError(
                f"review {review_id} is {review.status}; the status machine allows "
                f"{sorted(allowed) or 'no further transitions'}, not {target}"
            )
        await self.db.execute(
            update(MarketplaceReview)
            .where(MarketplaceReview.id == review.id)
            .values(status=target, moderated_by=str(moderator_id))
        )
        await self.db.commit()
        await self.db.refresh(review)
        if target == "rejected":
            logger.info(
                "review %s rejected by %s: %s", review.id, moderator_id, reason or "no reason given"
            )
        return review

    @staticmethod
    def _resolve_language(
        language: str | None, title: str | None, body: str | None
    ) -> str:
        """Explicit language if supported, else the detected one."""
        if language is not None:
            if language not in SUPPORTED_REVIEW_LANGUAGES:
                raise ReviewValidationError(
                    f"language must be one of {list(SUPPORTED_REVIEW_LANGUAGES)}, got {language!r}"
                )
            return language
        return detect_review_language(f"{title or ''} {body or ''}")


def get_review_service(db: AsyncSession) -> MarketplaceReviewService:
    """A review service bound to one session (no singleton: the session is
    per-request state, so sharing one service across requests would share it)."""
    return MarketplaceReviewService(db)


__all__ = [
    "REVIEW_STATUSES",
    "SUPPORTED_REVIEW_LANGUAGES",
    "DuplicateReviewError",
    "MarketplaceReviewService",
    "OrderNotDeliveredError",
    "ReviewError",
    "ReviewNotFoundError",
    "ReviewStateError",
    "ReviewValidationError",
    "get_review_service",
]
