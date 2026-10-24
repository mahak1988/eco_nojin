"""Phase E — Evidence & Provenance Chain test suite.

Verifies the traceability contract:

    data -> transforms -> model -> parameters -> execution -> result
        -> interpretation -> decision

Covers:
  * Gateway-generated Evidence on every execute() (success + error paths)
  * Input -> output provenance chain preservation
  * evidence_engine.trace() / export_chain() retrieval
  * EvidenceAdapter (store / retrieve / list) + ComputationRecord round-trip
  * Cross-engine provenance: Evidence -> Fact -> Decision
  * Chain integrity validation (dangling-link detection)
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from engine.evidence import (
    Evidence,
    EvidenceEngine,
    EvidenceSource,
    EvidenceType,
    ValidationResult,
)
from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    ProvenanceSpec,
    UnitSpec,
)
from engine.knowledge import Claim, KnowledgeEngine
from engine.ports.evidence_adapter import (
    ComputationRecord,
    EvidenceAdapter,
    default_evidence_adapter,
)
from engine.tasmimyar import DecisionEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_HANDLER_RESULTS = {
    "cec": 15.0,
    "units": "cmol_c/kg",
}


def _cecect_handler(inputs, parameters):
    """Deterministic stand-in for the SOIL_CEC scientific computation."""
    return dict(SAMPLE_HANDLER_RESULTS)


def _make_gateway(handler=None, evidence_adapter=None) -> EngineGateway:
    """Build an EngineGateway wired with an optional handler + adapter."""
    gw = EngineGateway(evidence_adapter=evidence_adapter)
    if handler is not None:
        gw.register_handler("SOIL_CEC", handler)
    return gw


def _measurement_evidence(**overrides) -> Evidence:
    base: dict[str, Any] = {
        "source": EvidenceSource.MEASUREMENT,
        "evidence_type": EvidenceType.QUANTITATIVE,
        "value": 30.0,
        "confidence": 0.95,
        "metadata": {"param": "clay_pct", "location": "EPSG:4326"},
    }
    base.update(overrides)
    return Evidence(**base)


# ---------------------------------------------------------------------------
# EvidenceAdapter port
# ---------------------------------------------------------------------------


class _InMemoryAdapter:
    """Minimal durable adapter exercising the EvidenceAdapter protocol."""

    def __init__(self) -> None:
        self._records: dict[str, ComputationRecord] = {}

    def store_computation_record(self, record: ComputationRecord) -> str:
        self._records[record.trace_id] = record
        return record.trace_id

    def retrieve_by_trace(self, trace_id: str) -> ComputationRecord:
        return self._records[trace_id]

    def list_records_by_model(self, model_id: str) -> list[str]:
        return [
            r.trace_id
            for r in self._records.values()
            if r.model_id == model_id
        ]


class TestEvidenceAdapterPort:
    def test_adapter_protocol_is_runtime_checkable(self) -> None:
        assert isinstance(_InMemoryAdapter(), EvidenceAdapter)

    def test_default_stub_raises_when_unconfigured(self) -> None:
        stub = default_evidence_adapter()
        with pytest.raises(RuntimeError):
            stub.retrieve_by_trace("anything")

    def test_computation_record_roundtrip(self) -> None:
        adapter = _InMemoryAdapter()
        record = ComputationRecord(
            trace_id="trace_demo",
            model_id="CANON-006",
            model_name="Van Genuchten",
            model_version="1.0.0",
            inputs={"vg_alpha": 0.01},
            parameters={"theta_s": 0.45},
            outputs={"theta": 0.30},
            evidence_id="ev-1234",
        )
        trace_id = adapter.store_computation_record(record)
        assert trace_id == "trace_demo"

        fetched = adapter.retrieve_by_trace(trace_id)
        assert fetched.model_id == "CANON-006"
        assert fetched.outputs == {"theta": 0.30}
        assert fetched.evidence_id == "ev-1234"

        assert adapter.list_records_by_model("CANON-006") == ["trace_demo"]
        assert adapter.list_records_by_model("OTHER") == []

    def test_computation_record_is_json_serializable(self) -> None:
        record = ComputationRecord(
            trace_id="trace_json",
            model_id="CANON-004",
            inputs={"precipitation": 50.0},
            outputs={"runoff": 5.8},
            status="success",
        )
        serialized = record.to_dict()
        restored = ComputationRecord.from_dict(serialized)
        assert restored.trace_id == "trace_json"
        assert restored.outputs == {"runoff": 5.8}
        # The whole export must survive a JSON round-trip.
        assert json.loads(json.dumps(serialized))["model_id"] == "CANON-004"


# ---------------------------------------------------------------------------
# Every Gateway.execute() generates an Evidence item
# ---------------------------------------------------------------------------


class TestGatewayEmitsEvidence:
    def test_successful_execute_generates_evidence(self) -> None:
        gw = _make_gateway(handler=_cecect_handler)
        before = len(gw.evidence_engine.all())

        request = GatewayRequest(
            model_id="SOIL_CEC",
            inputs={"clay_pct": 30.0, "organic_matter_pct": 2.0, "ph": 7.0},
            input_units={},
            provenance=ProvenanceSpec(source="svc", source_type="SERVICE_CALL"),
            parameters={},
        )
        result = gw.execute(request)

        assert not isinstance(result, GatewayError)
        assert result.evidence_id is not None
        assert len(gw.evidence_engine.all()) == before + 1
        evidence = gw.evidence_engine.get(result.evidence_id)
        assert evidence is not None
        assert evidence.source == EvidenceSource.MODEL
        assert evidence.confidence == 1.0
        assert evidence.metadata["status"] == "success"
        assert evidence.metadata["model_id"] == "SOIL_CEC"

    def test_error_path_also_generates_evidence(self) -> None:
        """execute() must emit Evidence even on the error path."""
        gw = _make_gateway(handler=_cecect_handler)
        before = len(gw.evidence_engine.all())

        # Model not registered -> MODEL_NOT_FOUND gateway error
        request = GatewayRequest(
            model_id="DOES_NOT_EXIST",
            inputs={"a": 1.0},
            input_units={},
            provenance=ProvenanceSpec(source="svc", source_type="SERVICE_CALL"),
            parameters={},
        )
        error = gw.execute(request)

        assert isinstance(error, GatewayError)
        assert len(gw.evidence_engine.all()) == before + 1
        assert error.evidence_id is not None
        evidence = gw.evidence_engine.get(error.evidence_id)
        assert evidence is not None
        assert evidence.confidence == 0.0
        assert evidence.metadata["status"] == "error"

    def test_error_path_execution_exception_generates_evidence(self) -> None:
        def failing_handler(inputs, parameters):
            raise ValueError("boom")

        gw = _make_gateway(handler=failing_handler)
        request = GatewayRequest(
            model_id="SOIL_CEC",
            inputs={"clay_pct": 30.0},
            input_units={},
            provenance=ProvenanceSpec(source="svc", source_type="SERVICE_CALL"),
            parameters={},
        )
        error = gw.execute(request)
        assert isinstance(error, GatewayError)
        assert error.error_code == "EXECUTION_ERROR"
        assert error.evidence_id is not None
        assert gw.evidence_engine.get(error.evidence_id) is not None

    def test_trace_id_and_execution_id_populated(self) -> None:
        gw = _make_gateway(handler=_cecect_handler)
        request = GatewayRequest(
            model_id="SOIL_CEC",
            inputs={"clay_pct": 30.0},
            input_units={},
            provenance=ProvenanceSpec(source="svc", source_type="SERVICE_CALL"),
            parameters={},
        )
        result = gw.execute(request)
        assert result.execution is not None
        assert result.execution.trace_id is not None
        assert result.execution.execution_id is not None
        # trace_id is shared between evidence metadata and execution metadata
        evidence = gw.evidence_engine.get(result.evidence_id)
        assert evidence.metadata["trace_id"] == result.execution.trace_id
        assert evidence.metadata["execution_id"] == result.execution.execution_id

    def test_recorded_under_adapter_when_configured(self) -> None:
        adapter = _InMemoryAdapter()
        gw = _make_gateway(handler=_cecect_handler, evidence_adapter=adapter)
        request = GatewayRequest(
            model_id="SOIL_CEC",
            inputs={"clay_pct": 30.0},
            input_units={},
            provenance=ProvenanceSpec(source="svc", source_type="SERVICE_CALL"),
            parameters={},
        )
        result = gw.execute(request)
        assert result.execution is not None
        assert result.execution.trace_id is not None
        fetched = adapter.retrieve_by_trace(result.execution.trace_id)
        assert fetched.model_id == "SOIL_CEC"
        assert fetched.evidence_id == result.evidence_id
        assert fetched.status == "success"


# ---------------------------------------------------------------------------
# Input -> output provenance chain preservation
# ---------------------------------------------------------------------------


class TestProvenanceChainPreservation:
    def test_output_evidence_links_to_input_evidence(self) -> None:
        gw = _make_gateway(handler=_cecect_handler)

        # Step 1: an input measurement is recorded as Evidence.
        input_ev = gw.evidence_engine.collect(
            _measurement_evidence(value=30.0, metadata={"param": "clay_pct"})
        )

        # Step 2: the request's provenance points at the input evidence.
        request = GatewayRequest(
            model_id="SOIL_CEC",
            inputs={"clay_pct": 30.0, "organic_matter_pct": 2.0, "ph": 7.0},
            input_units={"clay_pct": UnitSpec(unit="percent")},
            provenance=ProvenanceSpec(
                source="svc",
                source_type="SERVICE_CALL",
                provenance_id=input_ev.id,
            ),
            parameters={},
        )
        result = gw.execute(request)

        output_ev = gw.evidence_engine.get(result.evidence_id)
        assert output_ev is not None
        # The output evidence provenance must reference the input evidence.
        assert input_ev.id in output_ev.provenance

        # trace() resolves the output evidence and walks back to the input.
        chain = gw.evidence_engine.trace(output_ev.id)
        assert chain[0].id == output_ev.id
        assert chain[-1].id == input_ev.id
        assert input_ev.id in {e.id for e in chain}

        # Integrity is satisfied because both links resolve.
        assert gw.evidence_engine.validate_chain_integrity() is True

    def test_trace_resolves_fact_id_alias(self) -> None:
        gw = _make_gateway(handler=_cecect_handler)
        input_ev = gw.evidence_engine.collect(
            _measurement_evidence(value=30.0)
        )
        request = GatewayRequest(
            model_id="SOIL_CEC",
            inputs={"clay_pct": 30.0},
            input_units={},
            provenance=ProvenanceSpec(
                source="svc", source_type="SERVICE_CALL",
                provenance_id=input_ev.id,
            ),
            parameters={},
        )
        result = gw.execute(request)
        output_ev = gw.evidence_engine.get(result.evidence_id)

        # The derived fact is named fact_<evidence_id>; trace() accepts either.
        fact_id = f"fact_{output_ev.id}"
        chain = gw.evidence_engine.trace(fact_id)
        assert any(e.id == output_ev.id for e in chain)
        assert any(e.id == input_ev.id for e in chain)

    def test_export_chain_is_json_serializable(self) -> None:
        gw = _make_gateway(handler=_cecect_handler)
        input_ev = gw.evidence_engine.collect(_measurement_evidence(value=30.0))
        request = GatewayRequest(
            model_id="SOIL_CEC",
            inputs={"clay_pct": 30.0},
            input_units={},
            provenance=ProvenanceSpec(
                source="svc", source_type="SERVICE_CALL",
                provenance_id=input_ev.id,
            ),
            parameters={},
        )
        result = gw.execute(request)
        assert result.execution is not None
        export = gw.evidence_engine.export_chain(result.evidence_id)

        assert export["evidence_id"] == result.evidence_id
        assert export["trace_id"] == result.execution.trace_id
        assert export["integrity"] is True
        # Must round-trip through JSON for external verifiers.
        json.loads(json.dumps(export))
        chain_ids = {entry["id"] for entry in export["chain"]}
        assert result.evidence_id in chain_ids
        assert input_ev.id in chain_ids


# ---------------------------------------------------------------------------
# Cross-engine provenance: Evidence -> Fact -> Decision
# ---------------------------------------------------------------------------


class TestCrossEngineProvenance:
    def _fresh_engines(self):
        ke = KnowledgeEngine()
        ee = EvidenceEngine(knowledge_engine=ke)
        de = DecisionEngine(knowledge_engine=ke, evidence_engine=ee)
        return ke, ee, de

    def test_evidence_to_fact_to_decision_chain(self) -> None:
        ke, ee, de = self._fresh_engines()

        # Evidence: model output with a measurement upstream.
        measurement = ee.collect(
            Evidence(
                source=EvidenceSource.MEASUREMENT,
                value=30.0,
                confidence=0.95,
                provenance=[],
                metadata={"param": "clay_pct"},
            )
        )
        model_ev = ee.collect(
            Evidence(
                source=EvidenceSource.MODEL,
                value={"cec": 15.0},
                confidence=0.9,
                provenance=[measurement.id],
                metadata={"model_id": "CANON-006"},
            )
        )

        # Evidence -> Fact: to_fact asserts into the knowledge base and records
        # the derivation link in the evidence engine.
        fact = ee.to_fact(model_ev.id, "CEC is high and supports fertility")
        assert fact.id == f"fact_{model_ev.id}"
        assert ke.get_fact(fact.id) is not None
        # Knowledge provenance chain resolves back to the measurement.
        kp = ke.resolve_provenance(fact.id)
        assert any(f.id == fact.id for f in kp)

        # Fact -> Decision: register the claim, then decide.
        claim = Claim(id="claim_fertility", text="Soil is fertile")
        ke.register_claim(claim)
        decision = de.make_decision(
            claim_id="claim_fertility", supporting_facts=[fact]
        )
        assert decision.outcome == "recommend"
        assert fact.id in decision.trace.fact_ids

        # Decision links back to evidence (via fact) for the decision engine.
        ee.register_decision(decision, fact.id)

        # The full export_chain shows evidence -> fact -> decision.
        export = ee.export_chain(model_ev.id)
        derived_fact_ids = {f["fact_id"] for f in export["derived_facts"]}
        derived_decision_ids = {d["decision_id"] for d in export["derived_decisions"]}
        assert fact.id in derived_fact_ids
        assert decision.decision_id in derived_decision_ids

        # And trace() walks evidence + ancestors.
        chain = ee.trace(model_ev.id)
        assert {e.id for e in chain} == {model_ev.id, measurement.id}

    def test_gateway_make_decision_auto_links_evidence(self) -> None:
        """The gateway wires Evidence -> Fact -> Decision without manual glue."""
        gw = EngineGateway()
        ee = gw.evidence_engine
        ke = gw.knowledge_engine

        ev = ee.collect(
            Evidence(
                source=EvidenceSource.MODEL,
                value={"cec": 15.0},
                confidence=0.9,
            )
        )
        fact = ee.to_fact(ev.id, "CEC supports fertility")
        claim = Claim(id="claim_gateway_fertility", text="Soil is fertile")
        ke.register_claim(claim)

        decision = gw.make_decision(
            claim_id="claim_gateway_fertility", supporting_facts=[fact]
        )
        # make_decision should have registered the decision link itself.
        export = ee.export_chain(ev.id)
        assert any(
            d["decision_id"] == decision.decision_id
            for d in export["derived_decisions"]
        )
        assert fact.id in {f["fact_id"] for f in export["derived_facts"]}

    def test_gateway_registers_serialized_decision_facts(self) -> None:
        """API-shaped evidence becomes registered, traceable knowledge facts."""
        gw = EngineGateway()
        decision = gw.make_decision(
            claim_id="claim_api",
            supporting_facts=[
                {
                    "id": "api-fact-1",
                    "statement": "Field moisture is in range",
                    "source_id": "user-submitted",
                    "confidence": 0.7,
                }
            ],
        )

        assert decision.trace.fact_ids == ["api-fact-1"]
        assert decision.confidence == pytest.approx(0.7)
        assert decision.trace.criterion_scores["evidence_quality"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Chain integrity validation
# ---------------------------------------------------------------------------


class TestChainIntegrity:
    def test_clean_chain_is_valid(self) -> None:
        ee = EvidenceEngine()
        a = ee.collect(Evidence(source=EvidenceSource.MEASUREMENT, value=1.0))
        b = ee.collect(Evidence(source=EvidenceSource.MODEL, value=2.0, provenance=[a.id]))
        c = ee.collect(Evidence(source=EvidenceSource.SIMULATION, value=3.0, provenance=[b.id]))
        assert ee.validate_chain_integrity() is True
        assert ee.trace(c.id)[0].id == c.id

    def test_dangling_provenance_link_is_invalid(self) -> None:
        ee = EvidenceEngine()
        ee.collect(
            Evidence(
                source=EvidenceSource.MODEL,
                value=1.0,
                provenance=["nonexistent-evidence-id"],
            )
        )
        assert ee.validate_chain_integrity() is False

    def test_chain_integrity_reflects_in_export(self) -> None:
        ee = EvidenceEngine()
        ee.collect(
            Evidence(
                source=EvidenceSource.MODEL,
                value=1.0,
                provenance=["dangling"],
            )
        )
        export = ee.export_chain(ee.all()[0].id)
        assert export["integrity"] is False

    def test_empty_engine_is_intact(self) -> None:
        ee = EvidenceEngine()
        assert ee.validate_chain_integrity() is True

    def test_validation_result_stored_and_retrievable(self) -> None:
        ee = EvidenceEngine()
        ev = ee.collect(Evidence(source=EvidenceSource.MEASUREMENT, value=1.0))
        result = ee.validate(ev.id)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert ee.get_validation(ev.id) is result
