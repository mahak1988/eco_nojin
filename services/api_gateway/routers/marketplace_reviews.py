"""Buyer ratings & reviews endpoints for the marketplace (plan v2.1, SA-V).

Mounted under the marketplace prefix, next to the catalogue it belongs to:

* ``POST   /products/{product_id}/reviews``              — write a review (auth)
* ``GET    /products/{product_id}/reviews``              — approved listing (public)
* ``GET    /products/{product_id}/reviews/summary``      — count / average / histogram
* ``POST   /products/{product_id}/reviews/{id}/helpful`` — mark helpful (auth)
* ``POST   /products/{product_id}/reviews/{id}/approve`` — moderator only
* ``POST   /products/{product_id}/reviews/{id}/reject``  — moderator only

The rules live in ``MarketplaceReviewService``; this layer is transport only —
the same auth dependencies (``require_user`` / ``require_admin``) and the same
error mapping as ``routers/marketplace.py``. The service needs an
``AsyncSession``, so the db dependency is the async one (the pattern of
``routers/village_hub.py``).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.errors import safe_detail_for_status
from services.marketplace.models import MarketplaceProduct
from services.marketplace.reviews import (
    DuplicateReviewError,
    MarketplaceReviewService,
    ReviewError,
    ReviewNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace-reviews"])


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async session: the review service is an async-session service."""
    async with hub.get_async_session() as session:
        yield session


def _service(db: AsyncSession) -> MarketplaceReviewService:
    return MarketplaceReviewService(db)


def _raise_review_error(exc: ReviewError) -> HTTPException:
    """Map the review domain errors onto honest HTTP statuses.

    Typed, so the status never depends on parsing a Persian message.
    """
    if isinstance(exc, ReviewNotFoundError):
        return HTTPException(status_code=404, detail=safe_detail_for_status(exc, 404))
    if isinstance(exc, DuplicateReviewError):
        return HTTPException(status_code=409, detail=safe_detail_for_status(exc, 409))
    return HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400))


async def _review_for_product(
    service: MarketplaceReviewService, product_id: str, review_id: str
) -> Any:
    """One review, checked to belong to the product in the path."""
    review = await service.get_review(review_id)
    if str(review.product_id) != str(product_id):
        raise ReviewNotFoundError(f"review {review_id} is not for product {product_id}")
    return review


# --- Request models ---


class ReviewCreateRequest(BaseModel):
    order_id: str = Field(..., min_length=1, max_length=36)
    rating: int = Field(..., ge=1, le=5)
    title: str | None = Field(default=None, max_length=200)
    body: str | None = Field(default=None, max_length=5000)
    language: str | None = Field(default=None, pattern="^(fa|en)$")


def _serialize(review: Any) -> dict:
    return {
        "id": review.id,
        "product_id": review.product_id,
        "order_id": review.order_id,
        "reviewer_id": review.reviewer_id,
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
        "language": review.language,
        "is_verified_purchase": bool(review.is_verified_purchase),
        "helpful_count": int(review.helpful_count or 0),
        "status": review.status,
        "moderated_by": review.moderated_by,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None,
    }


# --- Review endpoints ---


@router.post("/products/{product_id}/reviews", status_code=201)
async def create_review(
    product_id: str,
    payload: ReviewCreateRequest,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Write a review for a product from one of the buyer's delivered orders.

    The product must exist, the order must be delivered, and the reviewer gets
    one review per (order, product). The row is ``pending`` until a moderator
    decides it, so it is not in the public listing yet.
    """
    product = await db.get(MarketplaceProduct, str(product_id))
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    service = _service(db)
    try:
        review = await service.create_review(
            product_id=product_id,
            order_id=payload.order_id,
            reviewer_id=str(user.id),
            rating=payload.rating,
            title=payload.title,
            body=payload.body,
            language=payload.language,
        )
    except ReviewError as exc:
        await db.rollback()
        raise _raise_review_error(exc) from exc
    return {"review": _serialize(review), "status": review.status}


@router.get("/products/{product_id}/reviews")
async def list_reviews(
    product_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    lang: Annotated[str | None, Query(pattern="^(fa|en)$")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Public listing of a product's approved reviews (``?lang=`` + paging)."""
    service = _service(db)
    reviews = await service.list_product_reviews(
        product_id, language=lang, status="approved", limit=limit, offset=offset
    )
    return {
        "product_id": product_id,
        "reviews": [_serialize(r) for r in reviews],
        "count": len(reviews),
        "limit": limit,
        "offset": offset,
    }


@router.get("/products/{product_id}/reviews/summary")
async def review_summary(
    product_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Count, average rating (2dp) and the {1..5} histogram for a product."""
    service = _service(db)
    return await service.product_summary(product_id)


@router.post("/products/{product_id}/reviews/{review_id}/helpful")
async def mark_review_helpful(
    product_id: str,
    review_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a review helpful — one mark per user, no double counting."""
    service = _service(db)
    try:
        await _review_for_product(service, product_id, review_id)
        helpful_count = await service.mark_helpful(review_id, str(user.id))
    except ReviewError as exc:
        await db.rollback()
        raise _raise_review_error(exc) from exc
    return {
        "review_id": review_id,
        "product_id": product_id,
        "helpful_count": helpful_count,
    }


@router.post("/products/{product_id}/reviews/{review_id}/approve")
async def approve_review(
    product_id: str,
    review_id: str,
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Moderator: publish a pending review."""
    service = _service(db)
    try:
        await _review_for_product(service, product_id, review_id)
        review = await service.approve(review_id, str(user.id))
    except ReviewError as exc:
        await db.rollback()
        raise _raise_review_error(exc) from exc
    return {"review": _serialize(review), "status": review.status}


@router.post("/products/{product_id}/reviews/{review_id}/reject")
async def reject_review(
    product_id: str,
    review_id: str,
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: Annotated[str | None, Query(max_length=500)] = None,
):
    """Moderator: hide a pending review."""
    service = _service(db)
    try:
        await _review_for_product(service, product_id, review_id)
        review = await service.reject(review_id, str(user.id), reason=reason)
    except ReviewError as exc:
        await db.rollback()
        raise _raise_review_error(exc) from exc
    return {"review": _serialize(review), "status": review.status}
