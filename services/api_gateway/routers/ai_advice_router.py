"""AI advice endpoint (RAG → NLG/LLM) — Phase 8-C."""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.ai.nlg import advise

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class AdviceRequest(BaseModel):
    question: str
    lat: Optional[float] = None
    lon: Optional[float] = None


@router.post("/advise")
async def advise_endpoint(payload: AdviceRequest):
    """Natural-language recommendation with retrieval evidence.

    When AI_LLM_KEY is configured a real LLM answers; otherwise the free
    local NLG engine answers (provider field is always honest).
    """
    question = payload.question.strip()
    if not question:
        return {"status": "error", "error": "question خالی است"}
    metrics = None
    if payload.lat is not None and payload.lon is not None:
        try:
            from services.scientific_motors.drought_motor import run_drought

            drought = run_drought(lat=payload.lat, lon=payload.lon, timescale_months=6)
            if drought.get("status") == "ok" and drought.get("latest", {}).get("spi") is not None:
                metrics = {"spi": round(drought["latest"]["spi"], 3)}
        except Exception:
            metrics = None
    result = advise(question, metrics)
    result["status"] = "ok"
    return result
