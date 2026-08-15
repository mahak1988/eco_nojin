"""API endpoints for the AI knowledge assistant."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from engine.hydroma.ai_assistant.rag_engine import get_engine

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])


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


@router.post("/chat", response_model=QueryResponse)
def chat_endpoint(payload: QueryRequest):
    """Ask the AI assistant a question about agriculture or ecology."""
    engine = get_engine()
    result = engine.generate_response(payload.question)
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
