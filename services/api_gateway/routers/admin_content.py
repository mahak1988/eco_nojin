"""Admin Content Router - Content management endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import ContentItem, ContentVersion, ContentTranslation
from services.api_gateway.auth import require_content_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["admin-content"])


class ContentCreate(BaseModel):
    title: str
    body: str
    category: str = "general"
    status: str = "draft"
    language: str = "fa"


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class ContentResponse(BaseModel):
    id: int
    title: str
    body: str
    category: str
    status: str
    language: str
    created_at: str
    updated_at: str
    published_at: Optional[str] = None

    class Config:
        from_attributes = True


class ContentVersionResponse(BaseModel):
    id: int
    content_id: int
    version: int
    title: str
    body: str
    created_at: str

    class Config:
        from_attributes = True


class ContentTranslationResponse(BaseModel):
    id: int
    content_id: int
    locale: str
    title: str
    body: str
    source: str
    is_published: bool

    class Config:
        from_attributes = True


class TranslateRequest(BaseModel):
    target_locale: str
    source_locale: str = "fa"


class ScheduleRequest(BaseModel):
    publish_at: datetime


router = APIRouter(prefix="/content", tags=["admin-content"])


@router.get("", response_model=List[ContentResponse])
async def list_content(
    status: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
):
    """Archive content (soft delete)."""
    content = await db.get(ContentItem, item_id)
    if not content:
        raise HTTPException(404, "Content not found")

    content.status = "archived"
    content.updated_at = datetime.now(UTC).isoformat()
    await db.commit()
    return {"message": "Content archived"}


@router.get("/{item_id}/versions", response_model=List[ContentVersionResponse])
async def get_content_versions(
    item_id: int,
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
):
    """Get version history for content."""
    stmt = select(ContentVersion).where(ContentVersion.content_id == item_id).order_by(desc(ContentVersion.version))
    result = await db.execute(stmt)
    versions = result.scalars().all()
    return versions


@router.get("/{item_id}/translations", response_model=List[ContentTranslationResponse])
async def get_content_translations(
    item_id: int,
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
    db: AsyncSession = Depends(hub.get_async_session),
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
    current_user=Depends(require_content_admin),
):
    """Generate content draft using AI."""
    # Mock AI generation
    return {
        "title": f"Draft: {prompt[:50]}...",
        "body": f"AI-generated content for: {prompt}",
        "slug": f"draft-{language}-{abs(hash(prompt)) % 10000}",
        "category": category,
    }