"""AI Analysis Router — Drought, Scenario, Advisory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/ai/analysis", tags=["ai-analysis"])


class DroughtRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    months: int = Field(6, ge=1, le=24, description="Analysis period in months")
    scales: list[int] = Field([1, 3, 6, 12], description="SPI/SPEI time scales")


class ScenarioRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    precip_change_pct: float = Field(0.0, ge=-100, le=100)
    temp_change_c: float = Field(0.0, ge=-20, le=20)
    months: int = Field(6, ge=1, le=24)


class MultiScenarioRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    scenarios: list[ScenarioRequest]
    months: int = Field(6, ge=1, le=24)


class AdvisoryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    language: str | None = Field(None, pattern="^(fa|en|ar|tr|ur|ps|de|es|fr|hi|pt|zh|ms|it|bn)$")


class DroughtReportRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    months: int = Field(6, ge=1, le=24)
    language: str = Field("fa", pattern="^(fa|en|ar|tr|ur|ps|de|es|fr|hi|pt|zh|ms|it|bn)$")


@router.post("/drought")
async def analyze_drought(request: DroughtRequest):
    """Analyze drought conditions using SPI/SPEI indices."""
    from services.analysis.drought_agent import get_drought_agent
    
    agent = get_drought_agent()
    try:
        result = await agent.analyze(
            lat=request.lat,
            lon=request.lon,
            months=request.months,
            scales=request.scales,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await agent.close()


@router.post("/scenario")
async def run_scenario(request: ScenarioRequest):
    """Run a single what-if scenario."""
    from services.analysis.scenario_agent import get_scenario_agent
    
    agent = get_scenario_agent(request.lat, request.lon)
    try:
        result = await agent.run_scenario(
            precip_change_pct=request.precip_change_pct,
            temp_change_c=request.temp_change_c,
            months=request.months,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await agent.drought_agent.close()


@router.post("/scenarios")
async def run_multiple_scenarios(request: MultiScenarioRequest):
    """Run multiple scenarios and rank by severity."""
    from services.analysis.scenario_agent import get_scenario_agent
    
    agent = get_scenario_agent(request.lat, request.lon)
    try:
        scenarios = [
            {
                "name": s.scenarios.index(s) + 1,
                "precip_change_pct": s.precip_change_pct,
                "temp_change_c": s.temp_change_c,
            }
            for s in request.scenarios
        ]
        result = await agent.run_multiple_scenarios(scenarios, request.months)
        return {"scenarios": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await agent.drought_agent.close()


@router.post("/advise")
async def get_advice(request: AdvisoryRequest):
    """Get advisory answer for a farmer question."""
    from services.analysis.advisory_agent import get_advisory_agent
    
    agent = get_advisory_agent()
    try:
        result = await agent.process_question(
            question=request.question,
            lat=request.lat,
            lon=request.lon,
            language=request.language,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await agent.close()


@router.post("/drought-report")
async def get_drought_report(request: DroughtReportRequest):
    """Get comprehensive drought report with recommendations."""
    from services.analysis.advisory_agent import get_advisory_agent
    
    agent = get_advisory_agent()
    try:
        result = await agent.get_drought_report(
            lat=request.lat,
            lon=request.lon,
            months=request.months,
            language=request.language,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await agent.close()


@router.get("/providers")
async def list_providers():
    """List available LLM and embedding providers with quota status."""
    from services.ai.llm_router import get_router
    from services.ai.embedding_service import get_embedding_service
    
    llm_router = get_router()
    embedding_service = get_embedding_service()
    
    return {
        "llm_providers": llm_router.get_available_providers(),
        "embedding_providers": [
            {
                "provider": p.name.value,
                "available": embedding_service.quota.can_use(p.name),
                "model": p.model,
                "dimensions": p.dimensions,
            }
            for p in embedding_service._clients.keys()
        ],
    }