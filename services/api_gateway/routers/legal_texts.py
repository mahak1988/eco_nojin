"""Legal Texts API — versioned legal documents per locale (Phase 2 prerequisite).

S-STRUCT compliant: all DB access delegated to ``services.legal.service.LegalTextService``
which uses ``services.legal.repository.LegalTextRepository``.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from database.hub import hub
from services.api_gateway.auth import require_admin
from services.api_gateway.errors import domain_detail
from services.legal.service import LegalTextService

router = APIRouter(prefix="/api/v1/legal-texts", tags=["legal-texts"])


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


def get_service(db: Annotated[Any, Depends(get_db)]) -> LegalTextService:
    return LegalTextService(db)


@router.get("", response_model=dict)
def list_legal_texts(
    locale: Annotated[str | None, Query(max_length=8)] = None,
    slug: Annotated[str | None, Query(max_length=64)] = None,
    status: Annotated[str | None, Query(pattern="^(draft|published|archived)$")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: Annotated[LegalTextService, Depends(get_service)] = None,
):
    """List legal texts with optional filters."""
    texts = service.list(locale, slug, status, limit, offset)
    return {"count": len(texts), "legal_texts": texts}


@router.get("/locales", response_model=list[str])
def list_legal_locales(service: Annotated[LegalTextService, Depends(get_service)]):
    """Get all locales that have legal texts."""
    return service.list_locales()


@router.get("/slugs", response_model=list[str])
def list_legal_slugs(service: Annotated[LegalTextService, Depends(get_service)]):
    """Get all available legal text slugs."""
    return service.list_slugs()


@router.get("/{locale}/{slug}", response_model=dict)
def get_legal_text(
    locale: str,
    slug: str,
    version: Annotated[int | None, Query(ge=1)] = None,
    service: Annotated[LegalTextService, Depends(get_service)] = None,
):
    """Get a specific legal text by locale and slug (latest version by default)."""
    try:
        return service.get(locale, slug, version)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=domain_detail(e, 404)) from e


@router.get("/{locale}/{slug}/versions", response_model=list[dict])
def get_legal_text_versions(
    locale: str,
    slug: str,
    service: Annotated[LegalTextService, Depends(get_service)],
):
    """Get all versions of a legal text."""
    try:
        return service.list_versions(locale, slug)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=domain_detail(e, 404)) from e


@router.post("", response_model=dict, status_code=201)
def create_legal_text(
    payload: LegalTextCreate,
    service: Annotated[LegalTextService, Depends(get_service)],
    user: Annotated[Any, Depends(require_admin)],
):
    """Create a new legal text (auto-increments version if not specified)."""
    try:
        return service.create(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=domain_detail(e, 409)) from e


@router.patch("/{locale}/{slug}/{version}", response_model=dict)
def update_legal_text(
    locale: str,
    slug: str,
    version: int,
    payload: LegalTextUpdate,
    service: Annotated[LegalTextService, Depends(get_service)],
    user: Annotated[Any, Depends(require_admin)],
):
    """Update a legal text (only title, body, status, effective_at)."""
    try:
        return service.update(locale, slug, version, payload.model_dump(exclude_none=True))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=domain_detail(e, 404)) from e


@router.delete("/{locale}/{slug}/{version}", response_model=dict)
def delete_legal_text(
    locale: str,
    slug: str,
    version: int,
    service: Annotated[LegalTextService, Depends(get_service)],
    user: Annotated[Any, Depends(require_admin)],
):
    """Delete a specific legal text version."""
    try:
        return service.remove(locale, slug, version)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=domain_detail(e, 404)) from e
