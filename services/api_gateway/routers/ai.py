"""API endpoints for the AI knowledge assistant."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from engine.hydroma.ai_assistant.rag_engine import get_engine

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])


def _auto_citations(question: str) -> list[dict]:
    """Attach honest model-registry citations matching the query keywords."""
    from services.science.citations import citation_index

    q = question.lower()
    hits = []
    for item in citation_index()["items"]:
        hay = " ".join(
            [
                str(item.get("name_en", "")),
                str(item.get("name_fa", "")),
                str(item.get("domain", "")),
                str(item.get("reference", "")),
            ]
        ).lower()
        if any(word in hay for word in q.split() if len(word) > 2):
            hits.append(
                {
                    "slug": item.get("slug"),
                    "title": item.get("title"),
                    "doi": item.get("doi"),
                    "reference": item.get("reference"),
                }
            )
        if len(hits) >= 3:
            break
    return hits


class QueryRequest(BaseModel):
    """User query for the knowledge assistant."""

    question: str = Field(..., min_length=3, max_length=1000)


class SourceResponse(BaseModel):
    """Reference source for the answer."""

    id: str
    title: str
    source: str
    category: str
    relevance: float


class QueryResponse(BaseModel):
    """Response from the knowledge assistant."""

    query: str
    answer: str
    sources: list[SourceResponse]
    confidence: float
    citations: list[dict] = []


@router.post("/chat", response_model=QueryResponse)
def chat_endpoint(payload: QueryRequest):
    """Ask the AI assistant a question about agriculture or ecology."""
    engine = get_engine()
    result = engine.generate_response(payload.question)
    result["citations"] = _auto_citations(payload.question)
    return QueryResponse(**result)


@router.get("/health")
def ai_health():
    """Check AI assistant availability."""
    engine = get_engine()
    return {
        "status": "operational",
        "documents_loaded": len(engine.documents),
        "engine_type": "TF-IDF RAG",
    }
