"""Legal Texts API — versioned legal documents per locale (Phase 2 prerequisite)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import LegalText
from services.api_gateway.auth import require_admin

router = APIRouter(prefix="/api/v1/legal-texts", tags=["legal-texts"])


# Valid slugs for legal texts
VALID_SLUGS = {
    "terms",
    "privacy",
    "cookies",
    "ecommerce_rules",
    "buy_sell_rules",
    "marketplace_rules",
    "vendor_agreement",
    "data_processing_addendum",
}


class LegalTextCreate(BaseModel):
    locale: str = Field(
        ..., min_length=2, max_length=8, description="Locale code (e.g., fa, en, ar)"
    )
    slug: str = Field(..., min_length=1, max_length=64, description="Document identifier")
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    version: int | None = Field(default=None, ge=1)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    effective_at: str | None = None


class LegalTextUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, pattern="^(draft|published|archived)$")
    effective_at: str | None = None


class LegalTextResponse(BaseModel):
    id: str
    locale: str
    slug: str
    title: str
    body: str
    version: int
    status: str
    effective_at: str | None
    created_at: str
    updated_at: str


def get_db():
    with hub.get_session() as session:
        yield session


def _validate_slug(slug: str) -> str:
    if slug not in VALID_SLUGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid slug '{slug}'. Valid slugs: {', '.join(sorted(VALID_SLUGS))}",
        )
    return slug


def _to_response(text: LegalText) -> dict:
    return {
        "id": text.id,
        "locale": text.locale,
        "slug": text.slug,
        "title": text.title,
        "body": text.body,
        "version": text.version,
        "status": text.status,
        "effective_at": text.effective_at.isoformat() if text.effective_at else None,
        "created_at": text.created_at.isoformat() if text.created_at else None,
        "updated_at": text.updated_at.isoformat() if text.updated_at else None,
    }


# --- Public read endpoints ---


@router.get("", response_model=dict)
def list_legal_texts(
    locale: str | None = Query(None, max_length=8),
    slug: str | None = Query(None, max_length=64),
    status: str | None = Query(None, pattern="^(draft|published|archived)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List legal texts with optional filters."""
    stmt = select(LegalText)

    if locale:
        stmt = stmt.where(LegalText.locale == locale)
    if slug:
        _validate_slug(slug)
        stmt = stmt.where(LegalText.slug == slug)
    if status:
        stmt = stmt.where(LegalText.status == status)

    stmt = stmt.order_by(LegalText.locale, LegalText.slug, LegalText.version.desc())
    stmt = stmt.limit(limit).offset(offset)

    results = db.execute(stmt).scalars().all()
    return {"count": len(results), "legal_texts": [_to_response(t) for t in results]}


@router.get("/locales", response_model=list[str])
def list_legal_locales(db: Session = Depends(get_db)):
    """Get all locales that have legal texts."""
    stmt = select(LegalText.locale).distinct()
    return [row[0] for row in db.execute(stmt).all()]


@router.get("/slugs", response_model=list[str])
def list_legal_slugs(db: Session = Depends(get_db)):
    """Get all available legal text slugs."""
    stmt = select(LegalText.slug).distinct()
    return [row[0] for row in db.execute(stmt).all()]


@router.get("/{locale}/{slug}", response_model=dict)
def get_legal_text(
    locale: str,
    slug: str,
    version: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    """Get a specific legal text by locale and slug (latest version by default)."""
    _validate_slug(slug)

    stmt = select(LegalText).where(LegalText.locale == locale, LegalText.slug == slug)

    if version:
        stmt = stmt.where(LegalText.version == version)
    else:
        stmt = stmt.order_by(LegalText.version.desc())

    text = db.execute(stmt).scalars().first()
    if not text:
        raise HTTPException(
            status_code=404,
            detail=f"Legal text not found: locale={locale}, slug={slug}"
            + (f", version={version}" if version else " (latest)"),
        )

    return _to_response(text)


@router.get("/{locale}/{slug}/versions", response_model=list[dict])
def get_legal_text_versions(
    locale: str,
    slug: str,
    db: Session = Depends(get_db),
):
    """Get all versions of a legal text."""
    _validate_slug(slug)

    stmt = (
        select(LegalText)
        .where(LegalText.locale == locale, LegalText.slug == slug)
        .order_by(LegalText.version.desc())
    )

    texts = db.execute(stmt).scalars().all()
    if not texts:
        raise HTTPException(
            status_code=404,
            detail=f"Legal text not found: locale={locale}, slug={slug}",
        )

    return [
        {
            "version": t.version,
            "status": t.status,
            "effective_at": t.effective_at.isoformat() if t.effective_at else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in texts
    ]


# --- Admin write endpoints ---


@router.post("", response_model=dict, status_code=201)
def create_legal_text(
    payload: LegalTextCreate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Create a new legal text (auto-increments version if not specified)."""
    _validate_slug(payload.locale)
    _validate_slug(payload.slug)

    # Determine version
    if payload.version is None:
        existing = (
            db.execute(
                select(LegalText)
                .where(LegalText.locale == payload.locale, LegalText.slug == payload.slug)
                .order_by(LegalText.version.desc())
            )
            .scalars()
            .first()
        )
        version = (existing.version + 1) if existing else 1
    else:
        version = payload.version
        # Check for duplicate version
        existing = db.execute(
            select(LegalText).where(
                LegalText.locale == payload.locale,
                LegalText.slug == payload.slug,
                LegalText.version == version,
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Legal text version {version} already exists for locale={payload.locale}, slug={payload.slug}",
            )

    text = LegalText(
        locale=payload.locale,
        slug=payload.slug,
        title=payload.title,
        body=payload.body,
        version=version,
        status=payload.status,
    )
    db.add(text)
    db.commit()
    db.refresh(text)
    return _to_response(text)


@router.patch("/{locale}/{slug}/{version}", response_model=dict)
def update_legal_text(
    locale: str,
    slug: str,
    version: int,
    payload: LegalTextUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Update a legal text (only title, body, status, effective_at)."""
    _validate_slug(slug)

    text = db.execute(
        select(LegalText).where(
            LegalText.locale == locale, LegalText.slug == slug, LegalText.version == version
        )
    ).scalar_one_or_none()

    if not text:
        raise HTTPException(
            status_code=404,
            detail=f"Legal text not found: locale={locale}, slug={slug}, version={version}",
        )

    if payload.title is not None:
        text.title = payload.title
    if payload.body is not None:
        text.body = payload.body
    if payload.status is not None:
        text.status = payload.status
    if payload.effective_at is not None:
        from datetime import datetime

        text.effective_at = datetime.fromisoformat(payload.effective_at)

    db.commit()
    db.refresh(text)
    return _to_response(text)


@router.delete("/{locale}/{slug}/{version}", response_model=dict)
def delete_legal_text(
    locale: str,
    slug: str,
    version: int,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Delete a specific legal text version."""
    _validate_slug(slug)

    text = db.execute(
        select(LegalText).where(
            LegalText.locale == locale, LegalText.slug == slug, LegalText.version == version
        )
    ).scalar_one_or_none()

    if not text:
        raise HTTPException(
            status_code=404,
            detail=f"Legal text not found: locale={locale}, slug={slug}, version={version}",
        )

    db.delete(text)
    db.commit()
    return {"deleted": True, "locale": locale, "slug": slug, "version": version}
