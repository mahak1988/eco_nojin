"""MarketplaceReview — buyer ratings & reviews for marketplace products.

Closes the e-commerce trust gap: the seller side already carried a rating
column on ``MarketplaceProduct``/``MarketplaceSeller`` and the ecosystem a
trust score, but nothing let a buyer rate a purchase. A review is anchored to
the order that delivered it, so ``is_verified_purchase`` is decided from the
order state by the service rather than asserted by the client.

Two tables:
* ``MarketplaceReview`` — the review itself, one per
  (order, reviewer, product), pending moderation by default.
* ``MarketplaceReviewHelpful`` — one "helpful" mark per user per review. The
  unique constraint is the no-double-counting guarantee; ``helpful_count`` on
  the review is the denormalised tally the listing reads.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from database.base import Base

#: Review lifecycle. A review starts ``pending`` and only a moderator moves it
#: to ``approved`` (public) or ``rejected`` (hidden).
REVIEW_STATUSES = ("pending", "approved", "rejected")

#: Rating bounds shared by the model CHECK constraint and the service.
REVIEW_MIN_RATING = 1
REVIEW_MAX_RATING = 5


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


#: Script its text actually uses, never from the field it came from, so a title
#: that grows a Persian sentence later is labelled ``fa`` without a code change.
#: Mirrors ``services/ai/hydroma_rag.py:_detect_language`` (same corpus-wide
#: convention, no new dependency).
_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF]")
_LATIN_SCRIPT = re.compile(r"[A-Za-z]")


def detect_review_language(text: str) -> str:
    """``"fa"`` when Arabic-script characters outnumber Latin ones, else ``"en"``.

    A mixed text keeps the label of its dominant script, and a text with
    neither (symbols and digits only) is ``en`` — that is the platform default.
    """
    arabic = len(_ARABIC_SCRIPT.findall(text))
    latin = len(_LATIN_SCRIPT.findall(text))
    return "fa" if arabic > latin else "en"


class MarketplaceReview(Base):
    """A buyer's rating (1..5) and review for one product from one order."""

    __tablename__ = "marketplace_reviews"

    id = Column(String(36), primary_key=True, default=_uid)
    product_id = Column(
        String(36), ForeignKey("marketplace_products.id"), nullable=False, index=True
    )
    order_id = Column(String(36), ForeignKey("marketplace_orders.id"), nullable=False, index=True)
    reviewer_id = Column(String(36), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)
    language = Column(String(2), nullable=False, default="fa", index=True)
    is_verified_purchase = Column(Boolean, nullable=False, default=False)
    helpful_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pending", index=True)
    moderated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_now, index=True)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        Index("idx_review_product", "product_id"),
        Index("idx_review_reviewer", "reviewer_id"),
        Index("idx_review_order", "order_id"),
        UniqueConstraint(
            "order_id", "reviewer_id", "product_id", name="uq_review_order_reviewer_product"
        ),
        CheckConstraint(
            f"rating >= {REVIEW_MIN_RATING} AND rating <= {REVIEW_MAX_RATING}",
            name="ck_review_rating",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in REVIEW_STATUSES)})", name="ck_review_status"
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "order_id": self.order_id,
            "reviewer_id": self.reviewer_id,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "language": self.language,
            "is_verified_purchase": bool(self.is_verified_purchase),
            "helpful_count": int(self.helpful_count or 0),
            "status": self.status,
            "moderated_by": self.moderated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MarketplaceReviewHelpful(Base):
    """One user's "helpful" mark on one review.

    The unique constraint on (review_id, user_id) is what makes a second mark
    impossible; the service keeps ``MarketplaceReview.helpful_count`` equal to
    the number of rows here.
    """

    __tablename__ = "marketplace_review_helpful"

    id = Column(String(36), primary_key=True, default=_uid)
    review_id = Column(
        String(36),
        ForeignKey("marketplace_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="uq_review_helpful_voter"),
    )
