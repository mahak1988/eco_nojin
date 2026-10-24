"""Persistence for the admin content plane.

Moved here following the same pattern as ``services/api_gateway/settings_repository.py``:
the router must not issue SQL. Each method owns its transaction boundary.

Uses ``AsyncSession`` (the router used ``hub.get_async_session`` originally), and
all queries are ``async`` so they do not block the event loop.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import ContentItem, ContentTranslation, ContentVersion


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with hub.get_async_session() as session:
        yield session


class ContentRepository:
    """Every ``ContentItem`` / ``ContentVersion`` / ``ContentTranslation`` statement.

    Constructed per request from the request's session. Each method owns its
    transaction: the router cannot stage a write and forget to commit it.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_items(
        self,
        status: str | None = None,
        language: str | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContentItem]:
        stmt = select(ContentItem)
        if status:
            stmt = stmt.where(ContentItem.status == status)
        if language:
            stmt = stmt.where(ContentItem.language == language)
        if category:
            stmt = stmt.where(ContentItem.category == category)
        stmt = stmt.order_by(desc(ContentItem.updated_at)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_item(self, item_id: int) -> ContentItem | None:
        return await self.db.get(ContentItem, item_id)

    async def create_item(
        self,
        title: str,
        body: str,
        category: str,
        status: str,
        language: str,
        access_level: str,
    ) -> ContentItem:
        existing = await self.db.execute(
            select(ContentItem).where(ContentItem.title == title)
        )
        if existing.scalar_one_or_none():
            return None  # type: ignore[return-value]
        content = ContentItem(
            title=title,
            body=body,
            category=category,
            status=status,
            language=language,
            access_level=access_level,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def update_item(
        self, item_id: int, update_data: dict[str, Any]
    ) -> ContentItem | None:
        content = await self.db.get(ContentItem, item_id)
        if not content:
            return None
        for field, value in update_data.items():
            setattr(content, field, value)
        content.updated_at = datetime.now(UTC).isoformat()
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def publish_item(self, item_id: int) -> ContentItem | None:
        content = await self.db.get(ContentItem, item_id)
        if not content:
            return None
        content.status = "published"
        content.published_at = datetime.now(UTC).isoformat()
        content.updated_at = datetime.now(UTC).isoformat()
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def archive_item(self, item_id: int) -> bool:
        content = await self.db.get(ContentItem, item_id)
        if not content:
            return False
        content.status = "archived"
        content.updated_at = datetime.now(UTC).isoformat()
        await self.db.commit()
        return True

    async def get_versions(self, item_id: int) -> list[ContentVersion]:
        stmt = (
            select(ContentVersion)
            .where(ContentVersion.content_id == item_id)
            .order_by(desc(ContentVersion.version))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_translations(self, item_id: int) -> list[ContentTranslation]:
        stmt = select(ContentTranslation).where(ContentTranslation.content_id == item_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def translation_exists(
        self, item_id: int, locale: str
    ) -> ContentTranslation | None:
        stmt = select(ContentTranslation).where(
            ContentTranslation.content_id == item_id,
            ContentTranslation.locale == locale,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_translation(
        self,
        content_id: int,
        locale: str,
        title: str,
        body: str,
        source: str = "ai",
    ) -> ContentTranslation:
        translation = ContentTranslation(
            content_id=content_id,
            locale=locale,
            title=title,
            body=body,
            source=source,
        )
        self.db.add(translation)
        await self.db.commit()
        await self.db.refresh(translation)
        return translation

    async def schedule_publish(
        self, item_id: int, publish_at: str
    ) -> ContentItem | None:
        content = await self.db.get(ContentItem, item_id)
        if not content:
            return None
        content.status = "scheduled"
        content.published_at = publish_at
        content.updated_at = datetime.now(UTC).isoformat()
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def cancel_schedule(self, item_id: int) -> ContentItem | None:
        content = await self.db.get(ContentItem, item_id)
        if not content:
            return None
        content.status = "draft"
        content.published_at = None
        content.updated_at = datetime.now(UTC).isoformat()
        await self.db.commit()
        await self.db.refresh(content)
        return content


def get_content_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ContentRepository:
    """FastAPI dependency: bind the request's session to the repository."""
    return ContentRepository(db)
