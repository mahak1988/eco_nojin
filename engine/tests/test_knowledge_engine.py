"""Tests for the Knowledge Engine, forward-chaining inference, provenance,
and PersistencePort round-tripping.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from engine.evidence import (
    Evidence,
    EvidenceEngine,
    EvidenceSource,
    EvidenceType,
)
from engine.knowledge import (
    Fact,
    KnowledgeEngine,
    Rule,
)
from engine.ports.persistence import (
    FileBackedPersistence,
    InMemoryPersistence,
)
from engine.tasmimyar import (
    Decision,
    DecisionCriterion,
    DecisionStatus,
    DecisionTrace,
)

# ── Fact assertion & query ───────────────────────────────────────────────────


class TestFactAssertion:
    """Tests for assert_fact and querying methods."""

    def test_assert_fact_registers_fact(self) -> None:
        ke = KnowledgeEngine()
        fact = Fact(
            id="f1",
            statement="soil pH is 6.5",
            source_id="obs-001",
            confidence=0.9,
        )
        ke.assert_fact(fact)
        retrieved = ke.get_fact("f1")
        assert retrieved is not None
        assert retrieved.statement == "soil pH is 6.5"
        assert retrieved.confidence == 0.9

    def test_assert_fact_seeds_provenance_chain(self) -> None:
        ke = KnowledgeEngine()
        fact = Fact(
            id="f1",
            statement="rainfall 120mm",
            source_id="station-42",
        )
        ke.assert_fact(fact)
        chain = ke.get_provenance_chain("f1")
        assert chain == ["station-42"]

    def test_assert_fact_preserves_explicit_provenance(self) -> None:
        ke = KnowledgeEngine()
        fact = Fact(
            id="f1",
            statement="temp 25C",
            source_id="src-a",
            provenance_chain=["src-a", "preprocess-1"],
        )
        ke.assert_fact(fact)
        assert ke.get_provenance_chain("f1") == ["src-a", "preprocess-1"]

    def test_query_by_source(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="a", source_id="sensor-A", confidence=0.8)
        )
        ke.assert_fact(
            Fact(id="f2", statement="b", source_id="sensor-B", confidence=0.9)
        )
        ke.assert_fact(
            Fact(id="f3", statement="c", source_id="sensor-A", confidence=0.7)
        )
        results = ke.query_by_source("sensor-A")
        ids = {f.id for f in results}
        assert ids == {"f1", "f3"}

    def test_query_by_statement_substring(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="soil clay content is 30%", source_id="s1")
        )
        ke.assert_fact(
            Fact(id="f2", statement="sand content is 40%", source_id="s1")
        )
        ke.assert_fact(
            Fact(id="f3", statement="clay drainage is poor", source_id="s2")
        )
        results = ke.query_by_statement("clay")
        ids = {f.id for f in results}
        assert ids == {"f1", "f3"}

    def test_query_by_statement_case_insensitive(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="SOIL pH is neutral", source_id="s1")
        )
        results = ke.query_by_statement("soil")
        assert len(results) == 1
        assert results[0].id == "f1"

    def test_query_by_statement_no_match(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="soil clay", source_id="s1")
        )
        assert ke.query_by_statement("sand") == []

    def test_query_by_statement_empty_pattern(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="soil clay", source_id="s1")
        )
        assert ke.query_by_statement("") == []

    def test_register_fact_backward_compatible(self) -> None:
        ke = KnowledgeEngine()
        fact = Fact(id="f1", statement="test", source_id="s1")
        ke.register_fact(fact)
        assert ke.get_fact("f1") is not None
        assert ke.get_provenance_chain("f1") == ["s1"]


# ── Forward-chaining derivation ──────────────────────────────────────────────


class TestForwardChaining:
    """Tests for Rule-based forward-chaining inference."""

    def test_derive_single_rule(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="soil clay content exceeds 30%", source_id="s1", confidence=0.9)
        )
        rule = Rule(
            id="r1",
            premise=["soil clay content exceeds 30%"],
            conclusion="gypsum application recommended",
            confidence_boost=0.1,
        )
        ke.add_rule(rule)
        derived = ke.derive()
        assert len(derived) == 1
        assert derived[0].statement == "gypsum application recommended"
        assert derived[0].id.startswith("derived_r1_")
        # confidence = 0.9 * (1 + 0.1) = 0.99
        assert derived[0].confidence == pytest.approx(0.99)

    def test_derive_requires_all_premises(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="soil is clay", source_id="s1", confidence=0.9)
        )
        rule = Rule(
            id="r1",
            premise=["soil is clay", "rainfall exceeds 1000mm"],
            conclusion="deep drainage needed",
            confidence_boost=0.0,
        )
        ke.add_rule(rule)
        derived = ke.derive()
        assert len(derived) == 0

    def test_derive_multiple_rules(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="soil pH below 5.5", source_id="s1", confidence=0.8)
        )
        ke.assert_fact(
            Fact(id="f2", statement="organic matter below 2%", source_id="s2", confidence=0.9)
        )
        ke.add_rule(Rule(
            id="r1",
            premise=["soil pH below 5.5"],
            conclusion="limestone needed",
            confidence_boost=0.05,
        ))
        ke.add_rule(Rule(
            id="r2",
            premise=["organic matter below 2%"],
            conclusion="organic fertilizer needed",
            confidence_boost=0.05,
        ))
        derived = ke.derive()
        assert len(derived) == 2
        statements = {f.statement for f in derived}
        assert statements == {"limestone needed", "organic fertilizer needed"}

    def test_derive_chained_rules(self) -> None:
        """A rule's conclusion can satisfy another rule's premise."""
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="deep drainage needed", source_id="s1", confidence=0.9)
        )
        ke.add_rule(Rule(
            id="r1",
            premise=["deep drainage needed"],
            conclusion="install subsurface drains",
            confidence_boost=0.0,
        ))
        ke.add_rule(Rule(
            id="r2",
            premise=["install subsurface drains"],
            conclusion="design drain spacing",
            confidence_boost=0.0,
        ))
        derived = ke.derive()
        assert len(derived) == 2
        ids = {f.id for f in derived}
        assert any("r1" in i for i in ids)
        assert any("r2" in i for i in ids)

    def test_derive_clamps_confidence(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="x", source_id="s1", confidence=0.99)
        )
        rule = Rule(
            id="r1",
            premise=["x"],
            conclusion="y",
            confidence_boost=0.5,
        )
        ke.add_rule(rule)
        derived = ke.derive()
        assert derived[0].confidence <= 1.0

    def test_derive_does_not_rederive_existing(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="clay soil", source_id="s1", confidence=0.9)
        )
        ke.add_rule(Rule(
            id="r1",
            premise=["clay soil"],
            conclusion="needs amendment",
            confidence_boost=0.0,
        ))
        first = ke.derive()
        assert len(first) == 1
        # Running derive again should not produce duplicates
        second = ke.derive()
        assert len(second) == 0

    def test_premise_matches_by_fact_id(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="some statement", source_id="s1", confidence=0.9)
        )
        ke.add_rule(Rule(
            id="r1",
            premise=["f1"],
            conclusion="derived from id",
            confidence_boost=0.0,
        ))
        derived = ke.derive()
        assert len(derived) == 1
        assert derived[0].statement == "derived from id"

    def test_get_rule(self) -> None:
        ke = KnowledgeEngine()
        rule = Rule(id="r1", premise=["x"], conclusion="y", confidence_boost=0.1)
        ke.add_rule(rule)
        assert ke.get_rule("r1") is rule
        assert ke.get_rule("nonexistent") is None


# ── Provenance chain ─────────────────────────────────────────────────────────


class TestProvenanceChain:
    """Tests for get_provenance_chain on asserted and derived facts."""

    def test_provenance_for_asserted_fact(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="a", source_id="source-1", confidence=0.8)
        )
        assert ke.get_provenance_chain("f1") == ["source-1"]

    def test_provenance_for_derived_fact(self) -> None:
        ke = KnowledgeEngine()
        ke.assert_fact(
            Fact(id="f1", statement="soil clay", source_id="s1", confidence=0.9)
        )
        ke.assert_fact(
            Fact(id="f2", statement="low OM", source_id="s2", confidence=0.8)
        )
        ke.add_rule(Rule(
            id="r1",
            premise=["soil clay", "low OM"],
            conclusion="amendment needed",
            confidence_boost=0.05,
        ))
        derived = ke.derive()
        assert len(derived) == 1
        chain = ke.get_provenance_chain(derived[0].id)
        assert chain == ["f1", "f2", "r1"]

    def test_provenance_unknown_fact(self) -> None:
        ke = KnowledgeEngine()
        assert ke.get_provenance_chain("nonexistent") == []

    def test_provenance_empty_chain_falls_back_to_source(self) -> None:
        ke = KnowledgeEngine()
        fact = Fact(
            id="f1",
            statement="test",
            source_id="src-x",
            provenance_chain=[],
        )
        ke._facts["f1"] = fact
        assert ke.get_provenance_chain("f1") == ["src-x"]


# ── EvidenceEngine.to_fact integration ──────────────────────────────────────


class TestEvidenceEngineIntegration:
    """Tests that EvidenceEngine.to_fact() integrates with KnowledgeEngine."""

    def test_to_fact_asserts_into_knowledge_engine(self) -> None:
        ke = KnowledgeEngine()
        ee = EvidenceEngine(knowledge_engine=ke)
        evidence = ee.collect(Evidence(
            source=EvidenceSource.MEASUREMENT,
            value=42.5,
            confidence=0.95,
            provenance=["obs-001"],
        ))
        fact = ee.to_fact(evidence.id, "soil moisture is 42.5%")
        assert ke.get_fact(fact.id) is not None
        assert fact.id == f"fact_{evidence.id}"
        assert fact.provenance_chain == ["obs-001"]

    def test_to_fact_without_knowledge_engine(self) -> None:
        ee = EvidenceEngine()
        evidence = ee.collect(Evidence(
            source=EvidenceSource.MODEL,
            value={"result": 1.0},
            confidence=0.8,
        ))
        fact = ee.to_fact(evidence.id, "model says ok")
        assert fact.statement == "model says ok"
        assert fact.confidence == 0.8

    def test_to_fact_passes_explicit_knowledge_engine(self) -> None:
        ke = KnowledgeEngine()
        ee = EvidenceEngine()
        evidence = ee.collect(Evidence(
            source=EvidenceSource.FIELD_OBSERVATION,
            value=0.5,
            confidence=0.7,
            provenance=["field-1"],
        ))
        fact = ee.to_fact(evidence.id, "observed growth 0.5", knowledge_engine=ke)
        assert ke.get_fact(fact.id) is not None


# ── Persistence round-trip ──────────────────────────────────────────────────


class TestPersistenceRoundTrip:
    """Tests for PersistencePort implementations (in-memory + file-backed)."""

    def test_persistence_port_protocol(self) -> None:
        """InMemoryPersistence satisfies the PersistencePort Protocol."""
        mem = InMemoryPersistence()
        assert hasattr(mem, "save_evidence")
        assert hasattr(mem, "load_evidence")
        assert hasattr(mem, "save_fact")
        assert hasattr(mem, "load_fact")
        assert hasattr(mem, "save_decision")
        assert hasattr(mem, "load_decision")
        assert hasattr(mem, "list_evidence")

    def test_in_memory_fact_round_trip(self) -> None:
        mem = InMemoryPersistence()
        fact = Fact(
            id="fact-1",
            statement="soil clay 30%",
            source_id="src-1",
            confidence=0.85,
            provenance_chain=["src-1"],
            metadata={"param": "value"},
        )
        mem.save_fact(fact)
        loaded = mem.load_fact("fact-1")
        assert loaded is not None
        assert loaded.id == fact.id
        assert loaded.statement == fact.statement
        assert loaded.source_id == fact.source_id
        assert loaded.confidence == fact.confidence
        assert loaded.provenance_chain == fact.provenance_chain
        assert loaded.metadata == fact.metadata

    def test_in_memory_fact_not_found(self) -> None:
        mem = InMemoryPersistence()
        assert mem.load_fact("missing") is None

    def test_in_memory_evidence_round_trip(self) -> None:
        mem = InMemoryPersistence()
        evidence = Evidence(
            id="ev-1",
            source=EvidenceSource.MEASUREMENT,
            evidence_type=EvidenceType.QUANTITATIVE,
            value=25.4,
            confidence=0.9,
            provenance=["obs-chain"],
            metadata={"unit": "mm"},
        )
        mem.save_evidence(evidence)
        loaded = mem.load_evidence("ev-1")
        assert loaded is not None
        assert loaded.id == evidence.id
        assert loaded.source == EvidenceSource.MEASUREMENT
        assert loaded.evidence_type == EvidenceType.QUANTITATIVE
        assert loaded.value == 25.4
        assert loaded.provenance == ["obs-chain"]

    def test_in_memory_decision_round_trip(self) -> None:
        mem = InMemoryPersistence()
        decision = Decision(
            decision_id="dec-1",
            claim_id="claim-1",
            outcome="recommend",
            confidence=0.85,
            criteria=[DecisionCriterion(name="quality", weight=0.5, threshold=0.6, direction="maximize")],
            trace=DecisionTrace(
                trace_id="trace-1",
                decision_id="dec-1",
                claim_id="claim-1",
                fact_ids=["f1", "f2"],
                evidence_weights={"quality": 0.5},
                claim_status="supported",
                claim_confidence=0.9,
                criterion_scores={"quality": 0.9},
                aggregate_score=0.9,
                outcome="recommend",
            ),
            rationale="Good evidence.",
            recommendations=["Proceed."],
            caveats=["None."],
        )
        mem.save_decision(decision)
        loaded = mem.load_decision("dec-1")
        assert loaded is not None
        assert loaded.decision_id == decision.decision_id
        assert loaded.outcome == "recommend"
        assert loaded.confidence == 0.85
        assert len(loaded.criteria) == 1
        assert loaded.criteria[0].name == "quality"
        assert loaded.trace.trace_id == "trace-1"
        assert loaded.trace.fact_ids == ["f1", "f2"]

    def test_list_evidence_with_filters(self) -> None:
        mem = InMemoryPersistence()
        mem.save_evidence(Evidence(
            id="ev-1", source=EvidenceSource.MEASUREMENT, value=1.0,
            metadata={"crop": "wheat", "region": "north"},
        ))
        mem.save_evidence(Evidence(
            id="ev-2", source=EvidenceSource.MODEL, value=2.0,
            metadata={"crop": "corn", "region": "north"},
        ))
        mem.save_evidence(Evidence(
            id="ev-3", source=EvidenceSource.MEASUREMENT, value=3.0,
            metadata={"crop": "wheat", "region": "south"},
        ))
        results = mem.list_evidence({"crop": "wheat"})
        assert len(results) == 2
        ids = {e.id for e in results}
        assert ids == {"ev-1", "ev-3"}
        results = mem.list_evidence({"crop": "wheat", "region": "north"})
        assert len(results) == 1
        assert results[0].id == "ev-1"
        results = mem.list_evidence({})
        assert len(results) == 3

    def test_file_backed_fact_round_trip(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        fact = Fact(
            id="f1",
            statement="clay soil requires gypsum",
            source_id="lab-1",
            confidence=0.92,
            provenance_chain=["lab-1"],
            metadata={"depth_cm": 30},
        )
        fb.save_fact(fact)
        loaded = fb.load_fact("f1")
        assert loaded is not None
        assert loaded.id == "f1"
        assert loaded.statement == fact.statement
        assert loaded.source_id == "lab-1"
        assert loaded.confidence == 0.92
        assert loaded.provenance_chain == ["lab-1"]
        assert loaded.metadata == {"depth_cm": 30}
        assert isinstance(loaded.timestamp, datetime)

    def test_file_backed_evidence_round_trip(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        evidence = Evidence(
            id="ev-1",
            source=EvidenceSource.SIMULATION,
            evidence_type=EvidenceType.QUANTITATIVE,
            value=15.7,
            confidence=0.88,
            provenance=["sim-run-1"],
            metadata={"model": "aquacrop"},
        )
        fb.save_evidence(evidence)
        loaded = fb.load_evidence("ev-1")
        assert loaded is not None
        assert loaded.source == EvidenceSource.SIMULATION
        assert loaded.evidence_type == EvidenceType.QUANTITATIVE
        assert loaded.value == 15.7
        assert loaded.provenance == ["sim-run-1"]
        assert loaded.metadata == {"model": "aquacrop"}
        assert isinstance(loaded.timestamp, datetime)

    def test_file_backed_evidence_not_found(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        fb.save_evidence(Evidence(id="ev-1", source=EvidenceSource.MEASUREMENT, value=1.0))
        assert fb.load_evidence("missing") is None

    def test_file_backed_decision_round_trip(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        decision = Decision(
            decision_id="dec-1",
            claim_id="c1",
            outcome="caution",
            confidence=0.65,
            criteria=[DecisionCriterion(name="quality", weight=0.5, threshold=0.6, direction="maximize")],
            trace=DecisionTrace(
                trace_id="t1", decision_id="dec-1", claim_id="c1", fact_ids=["f1"],
                evidence_weights={"quality": 0.5}, claim_status="supported",
                claim_confidence=0.9, criterion_scores={"quality": 0.9},
                aggregate_score=0.45, outcome="caution",
            ),
        )
        fb.save_decision(decision)
        loaded = fb.load_decision("dec-1")
        assert loaded is not None
        assert loaded.decision_id == "dec-1"
        assert loaded.outcome == "caution"
        assert loaded.confidence == 0.65
        assert loaded.status == DecisionStatus.EVALUATED
        assert loaded.trace.aggregate_score == 0.45
        assert loaded.criteria[0].weight == 0.5

    def test_file_backed_list_evidence(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        fb.save_evidence(Evidence(id="ev-1", source=EvidenceSource.MEASUREMENT, value=1.0, metadata={"crop": "wheat"}))
        fb.save_evidence(Evidence(id="ev-2", source=EvidenceSource.MODEL, value=2.0, metadata={"crop": "corn"}))
        results = fb.list_evidence({"crop": "wheat"})
        assert len(results) == 1
        assert results[0].id == "ev-1"
        results = fb.list_evidence({})
        assert len(results) == 2

    def test_file_backed_save_overwrites(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        fb.save_fact(Fact(id="f1", statement="old", source_id="s1", confidence=0.5))
        fb.save_fact(Fact(id="f1", statement="new", source_id="s1", confidence=0.9))
        loaded = fb.load_fact("f1")
        assert loaded is not None
        assert loaded.statement == "new"
        assert loaded.confidence == 0.9

    def test_file_backed_creates_file_if_missing(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        assert not path.exists()
        fb.save_evidence(Evidence(id="ev-1", source=EvidenceSource.MEASUREMENT, value=1.0))
        assert path.exists()

    def test_file_backed_empty_store(self, tmp_path) -> None:
        path = tmp_path / "persist.json"
        fb = FileBackedPersistence(path)
        assert fb.load_fact("any") is None
        assert fb.load_evidence("any") is None
        assert fb.list_evidence({}) == []


# ── KnowledgeEngine.end-to-end via Gateway ──────────────────────────────────


class TestEndToEndIntegration:
    """End-to-end: evidence → fact → rule derivation → provenance."""

    def test_full_pipeline(self) -> None:
        from engine.gateway import EngineGateway

        gateway = EngineGateway()
        ke = gateway.knowledge_engine
        ee = gateway.evidence_engine

        # Collect evidence
        evidence = Evidence(
            source=EvidenceSource.MEASUREMENT,
            value=35.0,
            confidence=0.9,
            provenance=["probe-A"],
            metadata={"depth_cm": 30},
        )
        ee.collect(evidence)

        # Convert to fact (auto-asserted into KE)
        fact = ee.to_fact(evidence.id, "clay content is 35%")
        assert ke.get_fact(fact.id) is not None

        # Register a rule
        ke.add_rule(Rule(
            id="r_clay",
            premise=["clay content is 35%"],
            conclusion="apply gypsum",
            confidence_boost=0.05,
        ))

        # Derive
        derived = ke.derive()
        assert len(derived) == 1
        assert derived[0].statement == "apply gypsum"

        # Check provenance chain
        chain = ke.get_provenance_chain(derived[0].id)
        assert fact.id in chain
        assert "r_clay" in chain
