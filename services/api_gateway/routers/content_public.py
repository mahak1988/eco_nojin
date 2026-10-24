"""Public content search (RAG surface)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from services.content.rag_sync import search_published_content


# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session



router = APIRouter(prefix="/api/v1/content", tags=["content"])


class ContentSearchHit(BaseModel):
    """One published document returned by the search surface."""

    id: str
    title: str
    category: str
    language: str
    published_at: str | None = None
    snippet: str


class ContentSearchResponse(BaseModel):
    """Search over published content.

    `response_model=dict` published an empty object schema, so a client could not
    type the query it sent or a single result field. Every field here is set by
    the route below, so the declaration states what the search actually returns.
    """

    query: str
    count: int
    results: list[ContentSearchHit] = Field(default_factory=list)


@router.get("/search", response_model=ContentSearchResponse)
def search_content(
    q: Annotated[str, Query(min_length=1, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    db: Annotated[Session, Depends(get_db)] = None,
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
