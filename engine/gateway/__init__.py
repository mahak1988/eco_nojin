"""Engine Gateway -- Controlled entry point for scientific computation.

Thin facade over the four implementation modules (A-1 remediation step 5): the
data contracts live in :mod:engine.gateway.contracts, input validation and
the required-input contract in :mod:engine.gateway.input_validator, the
`si_equivalent` unit machinery in :mod:engine.gateway.unit_converter, and
the model-dispatch route table and `_route_*` computations in
:mod:engine.gateway.model_dispatcher. `EngineGateway` here wires them
together; the public surface is byte-identical to the pre-split module.
"""

from __future__ import annotations

import math  # noqa: F401  -- public-surface compatibility
from collections.abc import Callable
from collections.abc import Mapping as _Mapping
from dataclasses import dataclass, field  # noqa: F401  -- public-surface compatibility
from datetime import datetime  # noqa: F401  -- public-surface compatibility
from typing import Any, cast  # noqa: F401  -- cast kept for public-surface compatibility
from uuid import uuid4  # noqa: F401  -- public-surface compatibility

# ``_Mapping`` is an implementation detail of ``EngineGateway.make_decision``
# below. It is aliased to a private name on purpose: the pre-split module
# exported ``Callable`` but not ``Mapping``, and the facade's contract is a
# byte-identical public surface (``engine/tests/test_gateway_package_split.py``
# pins ``dir(engine.gateway)``), which a bare import here would break.
import engine.gateway.model_dispatcher as _md
import engine.gateway.unit_converter as _unit_converter  # noqa: F401  -- loads the unit module
from engine.gateway.contracts import (
    ExecutionMetadata,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    InputSpec,
    ModelSpec,
    ProvenanceSpec,
    UncertaintySpec,
    UnitSpec,
    ValidationResult,
)
from engine.gateway.input_validator import REQUIRED_INPUTS as REQUIRED_INPUTS  # surface
from engine.gateway.input_validator import _normalize_inputs as _iv_normalize_inputs
from engine.gateway.model_dispatcher import (
    _ROUTE_TARGETS as _ROUTE_TARGETS,  # re-exported private hook
)
from engine.gateway.model_dispatcher import (
    _ROUTES_FOR_REGISTERED_IDS,
)
from engine.gateway.model_dispatcher import (
    _import_failure_message as _import_failure_message,  # re-exported private hook
)

# Drop the internal submodule attributes so dir(engine.gateway) matches the pre-split surface.
for _submodule in (
    "contracts", "unit_converter", "input_validator", "model_dispatcher", "pint_audit"
):
    globals().pop(_submodule, None)
del _submodule, _unit_converter

__all__ = [
    "GatewayRequest",
    "GatewayResult",
    "GatewayError",
    "EngineGateway",
    "ModelSpec",
    "InputSpec",
    "UnitSpec",
    "ProvenanceSpec",
    "UncertaintySpec",
    "ExecutionMetadata",
    "ValidationResult",
]


def _routed(
    route: Callable[[str, dict[str, Any], dict[str, Any], dict[str, Any]], Any],
    model_id: str,
    inputs: dict[str, Any],
    parameters: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Call a ``model_dispatcher`` route and assert the gateway's own contract.

    ``engine/gateway/model_dispatcher.py`` carries the route bodies and is not
    annotated, so every route returns ``Any``. The gateway's dispatch contract
    is ``dict[str, Any]``, so that contract is asserted once here rather than at
    each of the sixty call sites in :meth:`EngineGateway._dispatch_by_type`,
    which stay as explicit ``model_id`` comparisons because the model-registry
    wiring audit scans this file for them.
    """
    return cast("dict[str, Any]", route(model_id, inputs, parameters, result))


class EngineGateway:
    """Engine Gateway implementation.

    This is the SINGLE entry point between services and the scientific engine.
    All engine calls MUST go through this gateway.

    The gateway also provides access to Evidence and Knowledge engines,
    which are injectable collaborators. By default, lightweight in-memory
    instances are created.

    Usage:
        gateway = EngineGateway()
        request = GatewayRequest(...)
        result = gateway.execute(request)

        # Evidence and knowledge engines are accessible:
        evidence = gateway.evidence_engine  # knowledge = gateway.knowledge_engine
    """

    def __init__(
        self,
        model_registry=None,
        evidence_engine: Any = None,
        knowledge_engine: Any = None,
        decision_engine: Any = None,
        evidence_adapter: Any = None,
    ) -> None:
        from engine.models import get_registry

        # Duck-typed by contract: the injected registry either exposes
        # register() (ModelRegistry) or supports item assignment (a plain
        # mapping), so the attribute is Any rather than ModelRegistry.
        self._model_registry: Any = (
            model_registry if model_registry is not None else get_registry()
        )
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._version = "1.0.0"

        # Inject or lazily create Knowledge Engine (created before Evidence
        # Engine so that EvidenceEngine.to_fact() can assert facts directly).
        if knowledge_engine is not None:
            self._knowledge_engine = knowledge_engine
        else:
            from engine.knowledge import KnowledgeEngine

            self._knowledge_engine = KnowledgeEngine()

        # Inject or lazily create Evidence Engine
        if evidence_engine is not None:
            self._evidence_engine = evidence_engine
        else:
            from engine.evidence import EvidenceEngine

            self._evidence_engine = EvidenceEngine(
                knowledge_engine=self._knowledge_engine
            )

        # Inject the evidence persistence adapter (optional). When present,
        # each execution is persisted as a ComputationRecord keyed by trace_id.
        self._evidence_adapter = evidence_adapter

        # Inject or lazily create Decision Engine
        if decision_engine is not None:
            self._decision_engine = decision_engine
        else:
            from engine.tasmimyar import DecisionEngine

            self._decision_engine = DecisionEngine(
                knowledge_engine=self._knowledge_engine,
                evidence_engine=self._evidence_engine,
            )

    @property
    def evidence_engine(self) -> Any:
        """Access the Evidence Engine instance."""
        return self._evidence_engine

    @property
    def knowledge_engine(self) -> Any:
        """Access the Knowledge Engine instance."""
        return self._knowledge_engine

    @property
    def decision_engine(self) -> Any:
        """Access the Decision Engine instance."""
        return self._decision_engine

    @property
    def evidence_adapter(self) -> Any:
        """Access the injected EvidenceAdapter, or None if not configured."""
        return self._evidence_adapter

    def register_model(self, model: ModelSpec) -> None:
        """Register a scientific model with the gateway.
        
        Also registers with the ModelRegistry if one is in use.
        """
        if hasattr(self._model_registry, 'register'):
            self._model_registry.register(model)
        else:
            self._model_registry[model.model_id] = model

    def execute(self, request: GatewayRequest) -> GatewayResult | GatewayError:
        """Execute a model through the gateway.

        Thin wrapper: the full execution pipeline lives verbatim in
        :func:`engine.gateway.model_dispatcher._execute`.
        """
        return _md._execute(self, request)

    def register_evidence(self, evidence: Any) -> Any:
        """Register an Evidence item through the gateway.

        Delegates to the Evidence Engine. Returns the collected Evidence
        with its generated ID.
        """
        return self._evidence_engine.collect(evidence)

    def evaluate_claim(
        self,
        claim_id: str,
        supporting_evidence: list[str],
        contradicting_evidence: list[str],
    ) -> Any:
        """Evaluate a Claim against supporting and contradicting evidence.

        Converts evidence IDs to fact IDs and delegates to the Knowledge
        Engine. Returns the updated Claim.
        """
        fact_ids = [f"fact_{eid}" for eid in supporting_evidence]
        contradict_fact_ids = [f"fact_{eid}" for eid in contradicting_evidence]
        return self._knowledge_engine.evaluate_claim(
            claim_id, fact_ids, contradict_fact_ids
        )

    def make_decision(
        self,
        claim_id: str,
        supporting_facts: list[Any] | None = None,
        contradicting_facts: list[Any] | None = None,
        criteria: list[Any] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> Any:
        """Make a traceable decision via the Decision Engine.

        Delegates to the Decision Engine which evaluates the claim against
        evidence and produces a Decision with full traceability. The resulting
        Decision is linked back to its originating Evidence items so the full
        Evidence -> Fact -> Decision chain is recoverable through the Evidence
        Engine.
        """
        from engine.knowledge import Claim, Fact

        def normalize_facts(items: list[Any] | None) -> list[Any]:
            normalized: list[Any] = []
            for item in items or []:
                if isinstance(item, _Mapping):
                    required = ("id", "statement", "source_id", "confidence")
                    if any(key not in item for key in required):
                        raise ValueError(
                            "Decision evidence requires id, statement, source_id, and confidence"
                        )
                    item = Fact(
                        id=item["id"],
                        statement=item["statement"],
                        source_id=item["source_id"],
                        confidence=item["confidence"],
                    )
                    self._knowledge_engine.assert_fact(item)
                normalized.append(item)
            return normalized

        supporting_facts = normalize_facts(supporting_facts)
        contradicting_facts = normalize_facts(contradicting_facts)
        if self._knowledge_engine.get_claim(claim_id) is None:
            self._knowledge_engine.register_claim(Claim(id=claim_id, text=claim_id))

        decision = self._decision_engine.make_decision(
            claim_id,
            supporting_facts,
            contradicting_facts,
            criteria,
            parameters,
        )
        # Link the decision to every evidence item behind its supporting facts.
        fact_ids = list(getattr(getattr(decision, "trace", None), "fact_ids", []) or [])
        for fact_id in fact_ids:
            self._evidence_engine.register_decision(decision, fact_id)
        return decision

    def _normalize_inputs(
        self, request: GatewayRequest, model: ModelSpec
    ) -> tuple[dict[str, Any], list[ValidationResult]]:
        """Normalize input units to SI.

        Thin wrapper: delegates to
        :func:`engine.gateway.input_validator._normalize_inputs`.
        """
        return _iv_normalize_inputs(request, model)

    def _dispatch_to_model(
        self, model: ModelSpec, inputs: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatch to the appropriate model implementation.

        Thin wrapper: the handler-first then type-based dispatch lives in
        :func:`engine.gateway.model_dispatcher._dispatch_to_model`.
        """
        return _md._dispatch_to_model(self, model, inputs, parameters)

    def _dispatch_by_type(
        self, model_id: str, model_type: str, inputs: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatch by model ID.

        The routing comparisons stay here because the model-registry wiring audit
        scans this file for them; each delegates to ``model_dispatcher``.
        """
        result: dict[str, Any] = {"model_id": model_id, "model_type": model_type}
        if model_id in ('CANON-001', 'CANON-002', 'CANON-003', 'CANON-011_RAD'):
            return _routed(_md._route_et_pm_group, model_id, inputs, parameters, result)
        if model_id == 'ROTHTC_TEMP_FACTOR':
            return _routed(_md._route_rothtc_temp_factor, model_id, inputs, parameters, result)
        if model_id == 'CANON-004':
            return _routed(_md._route_canon_004, model_id, inputs, parameters, result)
        if model_id == 'CANON-005':
            return _routed(_md._route_canon_005, model_id, inputs, parameters, result)
        if model_id == 'CANON-006':
            return _routed(_md._route_canon_006, model_id, inputs, parameters, result)
        if model_id == 'CANON-016':
            return _routed(_md._route_canon_016, model_id, inputs, parameters, result)
        if model_id == 'CANON-017':
            return _routed(_md._route_canon_017, model_id, inputs, parameters, result)
        if model_id == 'SOIL_CEC':
            return _routed(_md._route_soil_cec, model_id, inputs, parameters, result)
        if model_id == 'SOIL_ESP':
            return _routed(_md._route_soil_esp, model_id, inputs, parameters, result)
        if model_id == 'SOIL_SAR':
            return _routed(_md._route_soil_sar, model_id, inputs, parameters, result)
        if model_id == 'SOIL_HEALTH':
            return _routed(_md._route_soil_health, model_id, inputs, parameters, result)
        if model_id == 'SOIL_AWC':
            return _routed(_md._route_soil_awc, model_id, inputs, parameters, result)
        if model_id == 'SOIL_WATER_CONTENT':
            return _routed(_md._route_soil_water_content, model_id, inputs, parameters, result)
        if model_id == 'SOIL_LEACHING':
            return _routed(_md._route_soil_leaching, model_id, inputs, parameters, result)
        if model_id == 'SOIL_AMENDMENT':
            return _routed(_md._route_soil_amendment, model_id, inputs, parameters, result)
        if model_id == 'SOIL_SALINITY_CLASSIFY':
            return _routed(_md._route_soil_salinity_classify, model_id, inputs, parameters, result)
        if model_id == 'SOIL_TAXONOMY':
            return _routed(_md._route_soil_taxonomy, model_id, inputs, parameters, result)
        if model_id == 'SOIL_TEXTURE':
            return _routed(_md._route_soil_texture, model_id, inputs, parameters, result)
        if model_id == 'SOIL_TEXTURE_COORDS':
            return _routed(_md._route_soil_texture_coords, model_id, inputs, parameters, result)
        if model_id == 'SOIL_WATER_RETENTION':
            return _routed(_md._route_soil_water_retention, model_id, inputs, parameters, result)
        if model_id == 'SOIL_VG_PARAMETERS':
            return _routed(_md._route_soil_vg_parameters, model_id, inputs, parameters, result)
        if model_id == 'SOIL_PEDOTRANSFER':
            return _routed(_md._route_soil_pedotransfer, model_id, inputs, parameters, result)
        if model_id == 'CARBON_SEQ':
            return _routed(_md._route_carbon_seq, model_id, inputs, parameters, result)
        if model_id == 'ECON_NPV':
            return _routed(_md._route_econ_npv, model_id, inputs, parameters, result)
        if model_id == 'ECON_PAYBACK':
            return _routed(_md._route_econ_payback, model_id, inputs, parameters, result)
        if model_id == 'ECON_AG_COST':
            return _routed(_md._route_econ_ag_cost, model_id, inputs, parameters, result)
        if model_id == 'ECON_AG_REVENUE':
            return _routed(_md._route_econ_ag_revenue, model_id, inputs, parameters, result)
        if model_id == 'ECON_PRICE_RISK':
            return _routed(_md._route_econ_price_risk, model_id, inputs, parameters, result)
        if model_id == 'ECON_YIELD_RISK':
            return _routed(_md._route_econ_yield_risk, model_id, inputs, parameters, result)
        if model_id == 'ECON_FINANCIAL':
            return _routed(_md._route_econ_financial, model_id, inputs, parameters, result)
        if model_id in ('WATERSHED_STRUCT', 'CANON-015'):
            return _routed(_md._route_watershed_struct, model_id, inputs, parameters, result)
        if model_id == 'WATERSHED_CHECK_DAM':
            return _routed(_md._route_watershed_check_dam, model_id, inputs, parameters, result)
        if model_id == 'WATERSHED_CONTOUR_TRENCH':
            return _routed(
                _md._route_watershed_contour_trench, model_id, inputs, parameters, result
            )
        if model_id == 'WATERSHED_HALF_MOON':
            return _routed(_md._route_watershed_half_moon, model_id, inputs, parameters, result)
        if model_id == 'PLANT_NEURO':
            return _routed(_md._route_plant_neuro, model_id, inputs, parameters, result)
        if model_id == 'MRV_METRICS':
            return _routed(_md._route_mrv_metrics, model_id, inputs, parameters, result)
        if model_id == 'MRV_DASHBOARD':
            return _routed(_md._route_mrv_dashboard, model_id, inputs, parameters, result)
        if model_id == 'MRV_VALIDATE':
            return _routed(_md._route_mrv_validate, model_id, inputs, parameters, result)
        if model_id == 'MRV_VALIDATE_SAT':
            return _routed(_md._route_mrv_validate_sat, model_id, inputs, parameters, result)
        if model_id == 'COMPOST_CN':
            return _routed(_md._route_compost_cn, model_id, inputs, parameters, result)
        if model_id == 'SCENARIO':
            return _routed(_md._route_scenario, model_id, inputs, parameters, result)
        if model_id == 'CLIMATE_SCENARIO':
            return _routed(_md._route_climate_scenario, model_id, inputs, parameters, result)
        if model_id == 'CLIMATE_PROJECTION':
            return _routed(_md._route_climate_projection, model_id, inputs, parameters, result)
        if model_id == 'CROP_COMPARE':
            return _routed(_md._route_crop_compare, model_id, inputs, parameters, result)
        if model_id == 'CROP_YIELD':
            return _routed(_md._route_crop_yield, model_id, inputs, parameters, result)
        if model_id == 'DATA_PIPELINE':
            return _routed(_md._route_data_pipeline, model_id, inputs, parameters, result)
        if model_id == 'IRRIGATION_DEPTH':
            return _routed(_md._route_irrigation_depth, model_id, inputs, parameters, result)
        if model_id == 'IRRIGATION_INTERVAL':
            return _routed(_md._route_irrigation_interval, model_id, inputs, parameters, result)
        if model_id == 'SIM_CHAIN':
            return _routed(_md._route_sim_chain, model_id, inputs, parameters, result)
        if model_id == 'SIM_ORCHESTRATE':
            return _routed(_md._route_sim_orchestrate, model_id, inputs, parameters, result)
        if model_id == 'RECOMMEND':
            return _routed(_md._route_recommend, model_id, inputs, parameters, result)
        if model_id == 'SOIL_RECOMMENDATIONS':
            return _routed(_md._route_soil_recommendations, model_id, inputs, parameters, result)
        if model_id.startswith('EWSI'):
            return _routed(_md._route_ewsi_family, model_id, inputs, parameters, result)
        if model_id.startswith('HYRUE'):
            return _routed(_md._route_hyrue_family, model_id, inputs, parameters, result)
        if model_id.startswith('ECSI'):
            return _routed(_md._route_ecsi_family, model_id, inputs, parameters, result)
        if model_id.startswith('EPIA'):
            return _routed(_md._route_epia_family, model_id, inputs, parameters, result)
        if model_id.startswith('HDVI'):
            return _routed(_md._route_hdvi_family, model_id, inputs, parameters, result)
        if model_id.startswith('ESRI'):
            return _routed(_md._route_esri_family, model_id, inputs, parameters, result)
        if model_id.startswith('HLHS'):
            return _routed(_md._route_hlhs_family, model_id, inputs, parameters, result)
        if model_id.startswith('HPheno'):
            return _routed(_md._route_hpheno_family, model_id, inputs, parameters, result)
        route = _ROUTES_FOR_REGISTERED_IDS.get(model_id)
        if route is not None:
            routed = route(inputs, parameters)
            result.update(routed)
            return result
        raise NotImplementedError(
            f"Model '{model_id}' (type '{model_type}') is registered but "
            f"not yet wired to a computation handler. "
            f"Register a handler via register_handler('{model_id}', handler)."
        )

    def register_handler(self, model_id: str, handler: Callable[..., Any]) -> None:
        """Register a computation handler for a specific model.
        
        Args:
            model_id: The model identifier to handle
            handler: Callable that takes (inputs, parameters) and returns dict
        """
        self._handlers[model_id] = handler
