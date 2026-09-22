"""Workflow Service — orchestrates multi-step agricultural analysis pipelines.

Stages:
1. Ingest raw farmer data (field, crop, soil, weather)
2. Run physics simulations (water balance, crop growth)
3. Generate actionable recommendations
4. Log the full pipeline trace for auditability
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub.hub import hub
from database.models import WorkflowRun, WorkflowStatus

logger = logging.getLogger(__name__)


class WorkflowStageResult(BaseModel):
    stage: str
    status: str  # success | failed | skipped
    duration_ms: float = 0.0
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class WorkflowRequest(BaseModel):
    farmer_id: str
    field_id: str | None = None
    crop_type: str | None = None
    stages: list[str] = Field(default_factory=lambda: ["ingest", "simulate", "recommend"])
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    run_id: str
    status: str
    stages: list[WorkflowStageResult]
    started_at: str
    completed_at: str | None = None


class WorkflowService:
    """Orchestrates end-to-end agricultural analysis workflows."""

    def __init__(self, db: Any = None, session: AsyncSession | None = None) -> None:
        self.db = db
        self.session = session

    async def _get_session(self) -> AsyncSession:
        if self.session is not None:
            return self.session
        return hub.get_async_session()

    async def run(self, request: WorkflowRequest) -> WorkflowResponse:
        """Execute a full workflow pipeline and persist the trace."""
        run_id = f"wf_{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
        started = datetime.now(UTC)
        stage_results: list[WorkflowStageResult] = []

        for stage_name in request.stages:
            stage_start = datetime.now(UTC)
            try:
                output = await self._run_stage(stage_name, request)
                stage_results.append(
                    WorkflowStageResult(
                        stage=stage_name,
                        status="success",
                        duration_ms=(datetime.now(UTC) - stage_start).total_seconds() * 1000,
                        output=output,
                    )
                )
            except Exception as exc:
                logger.exception("Stage %s failed", stage_name)
                stage_results.append(
                    WorkflowStageResult(
                        stage=stage_name,
                        status="failed",
                        duration_ms=(datetime.now(UTC) - stage_start).total_seconds() * 1000,
                        error=str(exc),
                    )
                )

        overall = "success" if all(s.status == "success" for s in stage_results) else "partial"
        await self._persist_run(run_id, request, stage_results, overall)

        return WorkflowResponse(
            run_id=run_id,
            status=overall,
            stages=stage_results,
            started_at=started.isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
        )

    async def _run_stage(self, stage_name: str, request: WorkflowRequest) -> dict[str, Any]:
        """Execute a single pipeline stage."""
        if stage_name == "ingest":
            return await self._stage_ingest(request)
        elif stage_name == "simulate":
            return await self._stage_simulate(request)
        elif stage_name == "recommend":
            return await self._stage_recommend(request)
        else:
            raise ValueError(f"Unknown stage: {stage_name}")

    async def _stage_ingest(self, request: WorkflowRequest) -> dict[str, Any]:
        """Ingest farmer and field data into the working set."""
        return {
            "farmer_id": request.farmer_id,
            "field_id": request.field_id,
            "crop_type": request.crop_type,
            "ingested_at": datetime.now(UTC).isoformat(),
        }

    async def _stage_simulate(self, request: WorkflowRequest) -> dict[str, Any]:
        """Run physics simulations on the ingested data."""
        from engine.hydroma.simulation.orchestrator import SimulationOrchestrator

        orchestrator = SimulationOrchestrator()
        result = await orchestrator.run(
            farmer_id=request.farmer_id,
            field_id=request.field_id,
            crop_type=request.crop_type,
        )
        return result if isinstance(result, dict) else {"result": str(result)}

    async def _stage_recommend(self, request: WorkflowRequest) -> dict[str, Any]:
        """Generate actionable recommendations from simulation output."""
        from engine.hydroma.decision_support.recommender import RecommenderEngine

        engine = RecommenderEngine()
        recs = await engine.recommend(
            farmer_id=request.farmer_id,
            context=request.metadata,
        )
        return {"recommendations": recs if isinstance(recs, list) else [str(recs)]}

    async def _persist_run(
        self,
        run_id: str,
        request: WorkflowRequest,
        stages: list[WorkflowStageResult],
        status: str,
    ) -> None:
        """Persist workflow run to the database."""
        try:
            async with await self._get_session() as session:
                run = WorkflowRun(
                    run_id=run_id,
                    farmer_id=request.farmer_id,
                    field_id=request.field_id,
                    crop_type=request.crop_type,
                    status=WorkflowStatus(status),
                    stages=[s.model_dump() for s in stages],
                    started_at=datetime.now(UTC).replace(tzinfo=None),
                    completed_at=datetime.now(UTC).replace(tzinfo=None),
                )
                session.add(run)
                await session.commit()
        except Exception:
            logger.warning("Failed to persist workflow run %s", run_id, exc_info=True)

    async def health(self) -> str:
        """Service health check."""
        return "ok"


async def get_workflow_service() -> WorkflowService:
    """FastAPI dependency."""
    return WorkflowService()


def main() -> None:
    """Run the workflow service as a standalone FastAPI app."""
    import uvicorn
    from fastapi import APIRouter, Depends, FastAPI

    app = FastAPI(title="Eco Nojin Workflow Service", version="1.0.0")
    router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])

    @router.post("/run", response_model=WorkflowResponse)
    async def run_workflow(
        body: WorkflowRequest,
        service: WorkflowService = Depends(get_workflow_service),
    ):
        return await service.run(body)

    @router.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8005)


if __name__ == "__main__":
    main()
