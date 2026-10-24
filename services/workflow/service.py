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

from database.hub import hub
from database.models import WorkflowRun, WorkflowStatus
from services.api_gateway.errors import safe_error_detail

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


#: AquaCrop names its crops in title case ("Wheat", "Maize", ...). The
#: workflow's requests carry the lower-case agronomic name ("wheat"), so the
#: name is mapped into AquaCrop's vocabulary. An unknown crop is passed
#: through unchanged so that AquaCrop raises its own error naming the
#: crops it knows -- the workflow does not guess.
_AQUACROP_CROP_ALIASES = {
    "wheat": "Wheat",
    "maize": "Maize",
    "corn": "Maize",
    "barley": "Barley",
    "sorghum": "Sorghum",
    "millet": "Millet",
    "potato": "Potato",
    "cotton": "Cotton",
    "quinoa": "Quinoa",
    "paddy_rice": "PaddyRice",
    "rice": "PaddyRice",
    "dry_bean": "DryBean",
    "chickpea": "Chickpea",
}


def _aquacrop_crop_name(crop_type: str | None) -> str | None:
    """Map a lower-case crop name onto AquaCrop's title-case vocabulary."""
    if not crop_type:
        return None
    return _AQUACROP_CROP_ALIASES.get(crop_type.strip().lower(), crop_type)


def _stage_error_detail(exc: Exception) -> str:
    """A client-safe detail for a failed stage.

    A *validation* failure names the inputs the caller has to supply. That
    list is composed from the caller's own request, so it carries no
    internals and is exactly what the caller needs -- hiding it behind
    "internal_error" made the workflow impossible to use. Every other
    exception keeps the generic safe detail.
    """
    from services.api_gateway.errors_gateway import GatewayCallError

    if isinstance(exc, GatewayCallError):
        if exc.validation_errors:
            fields = ", ".join(
                str(err.get("field", "?")) if isinstance(err, dict) else str(err)
                for err in exc.validation_errors
            )
            return f"invalid_request: missing or invalid inputs: {fields}"
        # The gateway's own validation message names only the fields the
        # caller supplied (it is a pydantic field report), so it is safe to
        # surface. Any other gateway message keeps the generic detail.
        message = str(exc.message or "")
        if "validation error" in message:
            return f"invalid_request: {message}"
    return safe_error_detail(exc)


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
                        error=_stage_error_detail(exc),
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
        """Run physics simulations on the ingested data.

        ``SimulationOrchestrator.run`` takes a *config mapping* (the gateway
        contract: ``{"chains": [...]}``), not ``farmer_id`` / ``field_id`` /
        ``crop_type`` keywords. The stage used to call it with those
        keywords, so it raised ``TypeError`` on every run and the default
        three-stage workflow always reported "partial" with two failed
        stages.
        """
        from services._gateway_facade import SimulationOrchestrator

        orchestrator = SimulationOrchestrator()
        # The request's metadata *is* the simulation configuration: the caller
        # supplies the erosion factors (R/K/LS/C), the initial soil carbon
        # and the clay fraction. The workflow does not invent them -- the
        # engine's validation names every missing one.
        chain: dict[str, Any] = {
            **request.metadata,
            "site_id": request.farmer_id,
            "crop": _aquacrop_crop_name(request.crop_type),
            # The scenario preset names the CN / cover / practice factors.
            "scenario": request.metadata.get("scenario", "Baseline"),
        }
        chain = {k: v for k, v in chain.items() if v is not None}
        # ``SimulationOrchestrator.run`` is a *synchronous* facade method (it
        # returns the gateway's dict), so it must not be awaited.
        result = orchestrator.run({"chains": [chain]})
        return result if isinstance(result, dict) else {"result": str(result)}

    async def _stage_recommend(self, request: WorkflowRequest) -> dict[str, Any]:
        """Generate actionable recommendations from simulation output.

        ``RecommenderEngine.recommend`` takes a single *context mapping*.
        The stage used to call it with ``farmer_id=`` / ``context=``
        keywords, so it raised ``TypeError`` on every run. The engine refuses
        a context that carries no optimisation or scenario data rather than
        inventing a recommendation, and that refusal is recorded as a failed
        stage -- which is the honest outcome.
        """
        from services._gateway_facade import RecommenderEngine

        engine = RecommenderEngine()
        context = {
            "project_id": request.farmer_id,
            **request.metadata,
        }
        recs = engine.recommend(context)
        if isinstance(recs, dict) and "recommendations" in recs:
            return recs
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
