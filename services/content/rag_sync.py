"""
RAG sync for editorial content (Phase 6).

Phase 6 keeps RAG sync honest: publishing a content item marks it
``rag_synced=True`` and makes it searchable through the public
``GET /api/v1/content/search`` endpoint (keyword index over published
items). Real embedding/vector retrieval arrives in Phase 9 — until then
no fake embeddings are claimed.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import models

logger = logging.getLogger(__name__)


def sync_content_to_rag(db: Session) -> int:
    """Mark all published items as RAG-synced; returns the count synced now."""
    pending = (
        db.query(models.ContentItem)
        .filter(
            models.ContentItem.status == "published",
            models.ContentItem.rag_synced.is_(False),
        )
        .all()
    )
    for item in pending:
        item.rag_synced = True
    db.commit()
    for item in pending:
        logger.info("RAG sync: content:%s «%s»", item.id, item.title[:60])
    return len(pending)


def search_published_content(
    db: Session, q: str, limit: int = 10
) -> List[models.ContentItem]:
    """Keyword search over published content (title + body)."""
    query = db.query(models.ContentItem).filter(
        models.ContentItem.status == "published"
    )
    term = f"%{q.strip()}%"
    query = query.filter(
        or_(
            models.ContentItem.title.ilike(term),
            models.ContentItem.body.ilike(term),
        )
    )
    return (
        query.order_by(models.ContentItem.published_at.desc())
        .limit(limit)
        .all()
    )


def snapshot_version(db: Session, item: models.ContentItem) -> None:
    """Save the current state as the next version (before an update)."""
    last = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.content_id == item.id)
        .order_by(models.ContentVersion.version.desc())
        .first()
    )
    version = (last.version + 1) if last else 1
    db.add(
        models.ContentVersion(
            content_id=item.id,
            version=version,
            title=item.title,
            body=item.body,
        )
    )
