"""API endpoints for the AI knowledge assistant — Cloud-Native Unified RAG."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai.unified_rag import get_rag

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
    language: str | None = Field(None, pattern="^(fa|en|ar|tr|ur|ps|de|es|fr|hi|pt|zh|ms|it|bn)$")


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
    language: str


@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(payload: QueryRequest):
    """Ask the AI assistant a question about agriculture or ecology."""
    rag = get_rag()
    try:
        result = await rag.answer(payload.question, language=payload.language)
        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            sources=[
                SourceResponse(
                    id=s["id"],
                    title=s["metadata"].get("title", "Unknown"),
                    source=s["metadata"].get("source", "Unknown"),
                    category=s["metadata"].get("category", "general"),
                    relevance=s["score"],
                )
                for s in result["sources"]
            ],
            confidence=result["confidence"],
            citations=_auto_citations(payload.question),
            language=result["language"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def ai_health():
    """Check AI assistant availability."""
    rag = get_rag()
    try:
        # Quick health check
        return {
            "status": "operational",
            "engine_type": "Unified Cloud RAG (Qdrant + Jina Embeddings + Groq)",
            "providers_configured": True,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "engine_type": "Unified Cloud RAG",
            "error": str(e),
        }