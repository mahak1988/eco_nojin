"""Public content search (Phase 6 RAG surface)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.config import get_db
from services.content.rag_sync import search_published_content

router = APIRouter(prefix="/api/v1/content", tags=["content"])


@router.get("/search", response_model=dict)
def search_content(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Keyword search over published content (honest RAG surface)."""
    results = search_published_content(db, q, limit)
    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "id": r.id,
                "title": r.title,
                "category": r.category,
                "language": r.language,
                "published_at": r.published_at.isoformat() if r.published_at else None,
                "snippet": r.body[:200],
            }
            for r in results
        ],
    }
