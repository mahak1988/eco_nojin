"""
Tasmimyar Service Layer
=======================

Service wrapper around the Decision Engine that provides HTTP/API access
to decision-making capabilities. This is the service-layer entry point
for applications that need traceable decisions based on scientific evidence.

The service routes all engine access through the Engine Gateway — it never
imports from engine.hydroma, engine.cpp_core, or engine.knowledge directly
per INV-003.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.gateway import EngineGateway


@dataclass
class ServiceResponse:
    """Standard response from Tasmimyar service."""
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    error_code: str | None = None
    request_id: str | None = None


@dataclass 
class DecisionRequest:
    """Request to make a decision via Tasmimyar.
    
    Attributes:
        claim_id: The claim being evaluated.
        supporting_facts: Fact objects from Knowledge Engine (serialized).
        contradicting_facts: Conflicting fact objects.
        criteria: Decision criteria weights and thresholds.
        parameters: Optional parameters for decision tuning.
    """
    claim_id: str
    supporting_facts: list[dict[str, Any]] = field(default_factory=list)
    contradicting_facts: list[dict[str, Any]] = field(default_factory=list)
    criteria: list[dict[str, Any]] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdviceRequest:
    """One decision-support recommendation, to be built under the P11 contract.

    The fields are the explainability contract: ``explainable_advice`` refuses
    advice that cannot name its goal, assumptions, uncertainty, limits, or the
    accountable decision-maker, so a recommendation reaching a user is always
    auditable — and never auto-applied.
    """

    goal: str
    recommendation: str
    model_id: str
    accountable_user_id: str
    inputs_used: dict[str, Any] = field(default_factory=dict)
    inputs_ignored: dict[str, Any] = field(default_factory=dict)
    criteria: list[dict[str, Any]] = field(default_factory=list)
    scenarios: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    uncertainty: str = ""
    limits: str = ""


class TasmimyarService:
    """Service-layer wrapper for the Decision Engine.
    
    All access to the Decision Engine goes through this service, which
    delegates to EngineGateway. This enforces the architectural boundary:
    services → gateway → engine.
    """
    
    def __init__(self, gateway: EngineGateway | None = None) -> None:
        self._gateway = gateway or EngineGateway()
    
    @property
    def gateway(self) -> EngineGateway:
        """Access the underlying Engine Gateway."""
        return self._gateway
    
    def decide(self, request: DecisionRequest) -> ServiceResponse:
        """Make a traceable decision based on evidence.

        The engine still builds its full scoring trace server-side (and
        :meth:`explain` exists for operators), but it is not serialized to
        HTTP clients: the results-only contract for this API sends the
        outcome, confidence, rationale, recommendations and caveats — never
        criterion weights, aggregate scores or the internal scoring path.
        """
        try:
            decision = self._gateway.make_decision(
                claim_id=request.claim_id,
                supporting_facts=request.supporting_facts,
                contradicting_facts=request.contradicting_facts,
                criteria=request.criteria,
                parameters=request.parameters,
            )
            
            return ServiceResponse(
                success=True,
                data={
                    "decision_id": decision.decision_id,
                    "outcome": decision.outcome,
                    "confidence": decision.confidence,
                    "rationale": decision.rationale,
                    "recommendations": decision.recommendations,
                    "caveats": decision.caveats,
                },
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=str(e),
                error_code="DECISION_ERROR",
            )
    
    def explain(self, decision_id: str) -> ServiceResponse:
        """Retrieve and explain a prior decision.
        
        Args:
            decision_id: ID of the decision to retrieve.
            
        Returns:
            ServiceResponse with decision explanation or error.
        """
        # Access the decision through the gateway's decision engine
        engine = self._gateway.decision_engine
        decision = engine.get_decision(decision_id)
        
        if decision is None:
            return ServiceResponse(
                success=False,
                error=f"Decision {decision_id} not found",
                error_code="NOT_FOUND",
            )
        
        return ServiceResponse(
            success=True,
            data={
                "decision_id": decision.decision_id,
                "claim_id": decision.claim_id,
                "outcome": decision.outcome,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
                "recommendations": decision.recommendations,
                "caveats": decision.caveats,
                "status": decision.status.value,
                "timestamp": decision.timestamp,
            },
        )


    def advise(self, request: AdviceRequest) -> ServiceResponse:
        """Build one explainable recommendation under the P11 contract.

        The builder (``services.tasmimyar.explainability``) is the one source
        of the auditable advice shape; a recommendation it refuses is a
        recommendation the service does not return.
        """
        from services.tasmimyar.explainability import AdviceError, explainable_advice

        try:
            advice = explainable_advice(
                goal=request.goal,
                inputs_used=request.inputs_used,
                inputs_ignored=request.inputs_ignored,
                criteria=request.criteria,
                scenarios=request.scenarios,
                assumptions=request.assumptions,
                uncertainty=request.uncertainty,
                limits=request.limits,
                model_id=request.model_id,
                accountable_user_id=request.accountable_user_id,
                recommendation=request.recommendation,
            )
        except AdviceError as e:
            return ServiceResponse(
                success=False,
                error=str(e),
                error_code="ADVICE_REFUSED",
            )
        return ServiceResponse(success=True, data={"advice": advice})


# FastAPI integration (lazy import to avoid hard dependency)
try:
    from typing import Annotated

    from fastapi import APIRouter, Depends, HTTPException

    from services.api_gateway.auth import require_user
    
    router = APIRouter(prefix="/api/v1/tasmimyar", tags=["tasmimyar"])
    
    @router.post("/decide")
    def api_decide(
        request: DecisionRequest,
        user: Annotated[Any, Depends(require_user)],
    ) -> ServiceResponse:
        """Make a decision via HTTP API."""
        service = TasmimyarService()
        return service.decide(request)
    
    @router.get("/explain/{decision_id}")
    def api_explain(
        decision_id: str,
        user: Annotated[Any, Depends(require_user)],
    ) -> ServiceResponse:
        """Explain a previously made decision."""
        service = TasmimyarService()
        result = service.explain(decision_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="Decision not found")
        return result

    @router.post("/advice")
    def api_advice(
        request: AdviceRequest,
        user: Annotated[Any, Depends(require_user)],
    ) -> ServiceResponse:
        """Return one auditable, never-auto-applied recommendation (P11)."""
        request.accountable_user_id = str(user.id)
        service = TasmimyarService()
        return service.advise(request)
    
    HAS_ROUTER = True
except ImportError:
    HAS_ROUTER = False
    router = None