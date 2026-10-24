"""Admin Content Router - Content management endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select

from database.hub import hub
from database.models import ContentItem, ContentTranslation, ContentVersion
from services.api_gateway.auth import require_content_admin
from services.api_gateway.errors import safe_detail_for_status

logger = logging.getLogger(__name__)


class ContentCreate(BaseModel):
    title: str
    body: str
    category: str = "general"
    status: str = "draft"
    language: str = "fa"


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    category: str | None = None
    status: str | None = None


class ContentResponse(BaseModel):
    id: int
    title: str
    body: str
    category: str
    status: str
    language: str
    created_at: str
    updated_at: str
    published_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ContentVersionResponse(BaseModel):
    id: int
    content_id: int
    version: int
    title: str
    body: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ContentTranslationResponse(BaseModel):
    id: int
    content_id: int
    locale: str
    title: str
    body: str
    source: str
    is_published: bool

    model_config = ConfigDict(from_attributes=True)


class TranslateRequest(BaseModel):
    target_locale: str
    source_locale: str = "fa"


class ScheduleRequest(BaseModel):
    publish_at: datetime


# The single router declaration for this module. It used to appear twice -- an
# identical `router = APIRouter(prefix="/content", tags=["admin-content"])` at
# the top of the file and again here -- and the second assignment silently
# replaced the first, so any decorator added above this line would have been
# discarded at import time with no error.
router = APIRouter(prefix="/content", tags=["admin-content"])


async def get_db():
    """Async session dependency.

    FastAPI wraps a *raw* async generator dependency in
    ``asynccontextmanager`` itself (``fastapi.dependencies.utils._solve_generator``),
    so ``Depends(get_db)`` â€” an already-wrapped
    ``@asynccontextmanager`` â€” gets wrapped a second time and raises
    ``TypeError: '_AsyncGeneratorContextManager' object is not an async
    iterator`` inside ``__aenter__``, i.e. HTTP 500 on every content route.
    This generator form is the one the dependency machinery accepts; the
    marketplace router's ``get_async_db`` is the same pattern.
    """
    async with hub.get_async_session() as session:
        yield session


@router.get("", response_model=list[ContentResponse])
async def list_content(
    status: Annotated[str | None, Query()] = None,
    language: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: Annotated[Any, Depends(require_content_admin)] = None,
    db: Annotated[Any, Depends(get_db)] = None,
):
    """List content items with filters."""
    stmt = select(ContentItem)

    if status:
        stmt = stmt.where(ContentItem.status == status)
    if language:
        stmt = stmt.where(ContentItem.language == language)
    if category:
        stmt = stmt.where(ContentItem.category == category)

    stmt = stmt.order_by(desc(ContentItem.updated_at)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return items


@router.post("", response_model=ContentResponse, status_code=201)
async def create_content(
    payload: ContentCreate,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Create new content (draft)."""
    existing = await db.execute(select(ContentItem).where(ContentItem.title == payload.title))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Content with this title already exists")

    content = ContentItem(
        title=payload.title,
        body=payload.body,
        category=payload.category,
        status=payload.status,
        language=payload.language,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content


@router.put("/{item_id}", response_model=ContentResponse)
async def update_content(
    item_id: int,
    payload: ContentUpdate,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Update content item."""
    content = await db.get(ContentItem, item_id)
    if not content:
        raise HTTPException(404, "Content not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)

    content.updated_at = datetime.now(UTC).isoformat()
    await db.commit()
    await db.refresh(content)
    return content


@router.post("/{item_id}/publish", response_model=ContentResponse)
async def publish_content(
    item_id: int,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Publish content."""
    content = await db.get(ContentItem, item_id)
    if not content:
        raise HTTPException(404, "Content not found")

    content.status = "published"
    content.published_at = datetime.now(UTC).isoformat()
    content.updated_at = datetime.now(UTC).isoformat()
    await db.commit()
    await db.refresh(content)
    return content


@router.delete("/{item_id}")
async def delete_content(
    item_id: int,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Archive content (soft delete)."""
    content = await db.get(ContentItem, item_id)
    if not content:
        raise HTTPException(404, "Content not found")

    content.status = "archived"
    content.updated_at = datetime.now(UTC).isoformat()
    await db.commit()
    return {"message": "Content archived"}


@router.get("/{item_id}/versions", response_model=list[ContentVersionResponse])
async def get_content_versions(
    item_id: int,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Get version history for content."""
    stmt = (
        select(ContentVersion)
        .where(ContentVersion.content_id == item_id)
        .order_by(desc(ContentVersion.version))
    )
    result = await db.execute(stmt)
    versions = result.scalars().all()
    return versions


@router.get("/{item_id}/translations", response_model=list[ContentTranslationResponse])
async def get_content_translations(
    item_id: int,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Get translations for content."""
    stmt = select(ContentTranslation).where(ContentTranslation.content_id == item_id)
    result = await db.execute(stmt)
    translations = result.scalars().all()
    return translations


@router.post("/{item_id}/translate", response_model=ContentTranslationResponse)
async def translate_content(
    item_id: int,
    payload: TranslateRequest,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """AI translate content to target locale."""
    # Check source content exists
    content = await db.get(ContentItem, item_id)
    if not content:
        raise HTTPException(404, "Content not found")

    # Check if translation already exists
    existing = await db.execute(
        select(ContentTranslation).where(
            ContentTranslation.content_id == item_id,
            ContentTranslation.locale == payload.target_locale,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Translation already exists for this locale")

    # Mock translation (replace with actual AI call)
    translation = ContentTranslation(
        content_id=item_id,
        locale=payload.target_locale,
        title=f"[Translated] {content.title}",
        body=f"[Translated] {content.body}",
        source="ai",
    )
    db.add(translation)
    await db.commit()
    await db.refresh(translation)
    return translation


@router.post("/{item_id}/schedule")
async def schedule_publish(
    item_id: int,
    payload: ScheduleRequest,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Schedule content publishing."""
    content = await db.get(ContentItem, item_id)
    if not content:
        raise HTTPException(404, "Content not found")

    content.status = "scheduled"
    content.published_at = payload.publish_at.isoformat()
    content.updated_at = datetime.now(UTC).isoformat()
    await db.commit()
    return {"message": f"Content scheduled for {payload.publish_at.isoformat()}"}


@router.post("/{item_id}/cancel-schedule")
async def cancel_schedule(
    item_id: int,
    current_user: Annotated[Any, Depends(require_content_admin)],
    db: Annotated[Any, Depends(get_db)],
):
    """Cancel scheduled publishing."""
    content = await db.get(ContentItem, item_id)
    if not content:
        raise HTTPException(404, "Content not found")

    content.status = "draft"
    content.published_at = None
    content.updated_at = datetime.now(UTC).isoformat()
    await db.commit()
    return {"message": "Schedule cancelled"}


@router.post("/generate-draft")
async def generate_draft(
    prompt: str,
    language: str = "fa",
    category: str = "general",
    current_user: Annotated[Any, Depends(require_content_admin)] = None,
):
    """Generate content draft using AI."""
    try:
        from services.ai.unified_rag import get_rag

        rag = get_rag()
        result = await rag.answer(prompt, language=language)
        return {
            "title": f"Draft: {prompt[:50]}...",
            "body": result["answer"],
            "slug": f"draft-{language}-{abs(hash(prompt)) % 10000}",
            "category": category,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=safe_detail_for_status(e, 503),
        ) from e
