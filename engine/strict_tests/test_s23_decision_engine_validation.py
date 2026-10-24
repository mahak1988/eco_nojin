"""S23 -- Decision-support layer validation: DecisionEngine (Tasmimyar)
and the Evidence engine.

The decision engine is an **engineering scoring rule**, not a validated
scientific model (HYDROMA-QA-001 section 10). What is validated here is
therefore its arithmetic, its gates, its honesty contract and its
traceability -- each against a criterion derived from the module's own
documented rule, never from its output:

* aggregation  : the weighted mean sum(w_i s_i) / sum(w_i)
* count score  : n_support / (n_support + n_contradict) on its declared side
* quality score: arithmetic mean of the supporting confidences
* gates        : RECOMMEND at >= 0.7, CAUTION at >= 0.4, REJECT below; the
                 claim-confidence floor of 0.2 that forces
                 INSUFFICIENT_EVIDENCE
* honesty      : no evidence -> INSUFFICIENT_EVIDENCE with confidence 0.0
                 and explicit caveats; never a confident verdict on nothing
* traceability: every fact id, every criterion score, the weights and the
                 claim status are recoverable from the decision's trace, and
                 the aggregate recomputes from them
* evidence     : confidence bounds, provenance resolution, chain integrity
                 against dangling references, and the documented scope of
                 that integrity check (reference resolution, not content
                 hashing -- see the recorded-limitation test)
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.evidence import Evidence, EvidenceEngine, EvidenceSource, EvidenceType
from engine.knowledge import Claim, Fact, KnowledgeEngine
from engine.tasmimyar import DecisionCriterion, DecisionEngine

DEFAULT_WEIGHTS = {"evidence_count": 0.3, "evidence_quality": 0.4, "confidence": 0.3}


def _fact(fid: str, confidence: float = 1.0) -> Fact:
    return Fact(id=fid, statement=f"fact {fid}", source_id="s23", confidence=confidence)


def _engine() -> tuple[DecisionEngine, KnowledgeEngine, EvidenceEngine]:
    """A fully wired engine with the claim registered but no knowledge facts.

    Facts are asserted through :func:`_pair`, because ``make_decision``
    recomputes the claim's own confidence through
    ``KnowledgeEngine.evaluate_claim``: the mean of the *contradicting* facts
    when any exist, otherwise of the supporting ones.
    """
    ke = KnowledgeEngine()
    ke.register_claim(Claim(id="claim-s23", text="s23 claim"))
    ee = EvidenceEngine()
    return DecisionEngine(knowledge_engine=ke, evidence_engine=ee), ke, ee


def _pair(ke: KnowledgeEngine, fid: str, confidence: float = 1.0) -> Fact:
    """Assert a fact into the knowledge engine and return the same object."""
    fact = _fact(fid, confidence)
    ke.assert_fact(fact)
    return fact


class TestScoringMath:
    """The aggregate must be the documented weighted mean, recomputed."""

    def test_aggregate_is_the_weighted_mean(self) -> None:
        engine, ke, _ = _engine()
        supporting = [_pair(ke, "f1", 0.8), _pair(ke, "f2", 0.6)]
        decision = engine.make_decision("claim-s23", supporting, [])
        trace = decision.trace
        total_weight = sum(trace.evidence_weights.values())
        expected = sum(
            trace.evidence_weights[name] * score
            for name, score in trace.criterion_scores.items()
            if score is not None
        ) / total_weight
        # count 1.0, quality 0.7, claim confidence 0.6
        assert expected == pytest.approx(0.3 * 1.0 + 0.4 * 0.7 + 0.3 * 0.7, rel=1e-12)
        assert trace.aggregate_score == pytest.approx(expected, rel=1e-12)

    def test_count_score_is_the_support_ratio(self) -> None:
        engine, ke, _ = _engine()
        supporting = [_pair(ke, f"s{i}") for i in range(7)]
        contradicting = [_pair(ke, f"c{i}") for i in range(3)]
        decision = engine.make_decision("claim-s23", supporting, contradicting)
        assert decision.trace.criterion_scores["evidence_count"] == pytest.approx(0.7)

    def test_count_score_inverts_under_a_minimize_direction(self) -> None:
        criteria = [DecisionCriterion(name="evidence_count", weight=0.5, direction="minimize")]
        engine, ke, _ = _engine()
        decision = engine.make_decision(
            "claim-s23", [_pair(ke, "s1")], [_pair(ke, "c1")], criteria=criteria
        )
        assert decision.trace.criterion_scores["evidence_count"] == pytest.approx(0.5)

    def test_quality_score_is_the_mean_supporting_confidence(self) -> None:
        engine, ke, _ = _engine()
        decision = engine.make_decision(
            "claim-s23", [_pair(ke, "s1", 0.8), _pair(ke, "s2", 0.6)], []
        )
        assert decision.trace.criterion_scores["evidence_quality"] == pytest.approx(0.7)

    def test_confidence_criterion_carries_the_claim_confidence(self) -> None:
        engine, ke, _ = _engine()
        decision = engine.make_decision("claim-s23", [_pair(ke, "s1", 0.55)], [])
        assert decision.trace.criterion_scores["confidence"] == pytest.approx(0.55)

    def test_zero_weights_yield_zero_not_a_division_error(self) -> None:
        criteria = [
            DecisionCriterion(name="evidence_count", weight=0.0),
            DecisionCriterion(name="confidence", weight=0.0),
        ]
        engine, ke, _ = _engine()
        decision = engine.make_decision(
            "claim-s23", [_pair(ke, "s1")], [], criteria=criteria
        )
        assert decision.trace.aggregate_score == 0.0


class TestOutcomeGates:
    """The documented thresholds: 0.7 RECOMMEND, 0.4 CAUTION, and the
    claim-confidence floor of 0.2 that forces INSUFFICIENT_EVIDENCE."""

    def test_exactly_the_recommend_threshold_recommends(self) -> None:
        """7 supporting (0.7) + 3 contradicting (0.7): count 0.7, quality 0.7,
        claim confidence 0.7 (mean of the contradicting facts) -> aggregate
        exactly 0.7, and >= is inclusive."""
        engine, ke, _ = _engine()
        supporting = [_pair(ke, f"s{i}", 0.7) for i in range(7)]
        contradicting = [_pair(ke, f"c{i}", 0.7) for i in range(3)]
        decision = engine.make_decision("claim-s23", supporting, contradicting)
        assert decision.trace.aggregate_score == pytest.approx(0.7, abs=1e-12)
        assert decision.outcome == "recommend"

    def test_exactly_the_caution_threshold_cautions(self) -> None:
        """count 0.4 (2 support / 3 contradict), quality 0.4, claim confidence
        0.4 -> aggregate exactly 0.4, and 0.4 is not below the 0.2 floor."""
        engine, ke, _ = _engine()
        supporting = [_pair(ke, "s1", 0.4), _pair(ke, "s2", 0.4)]
        contradicting = [_pair(ke, f"c{i}", 0.4) for i in range(3)]
        decision = engine.make_decision("claim-s23", supporting, contradicting)
        assert decision.trace.aggregate_score == pytest.approx(0.4, abs=1e-12)
        assert decision.outcome == "caution"

    def test_below_the_caution_threshold_rejects(self) -> None:
        engine, ke, _ = _engine()
        decision = engine.make_decision(
            "claim-s23", [_pair(ke, "s1", 0.2)], [_pair(ke, f"c{i}", 0.2) for i in range(3)]
        )
        assert decision.trace.aggregate_score < 0.4
        assert decision.outcome == "reject"

    def test_confidence_floor_is_inclusive_at_0_2(self) -> None:
        """A claim confidence of exactly 0.2 is not below the floor, so the
        score decides; 0.199 is."""
        engine, ke, _ = _engine()
        at_floor = engine.make_decision("claim-s23", [_pair(ke, "s1", 0.2)], [])
        assert at_floor.outcome != "insufficient_evidence"

        below_engine, below_ke, _ = _engine()
        below = below_engine.make_decision("claim-s23", [_pair(below_ke, "s1", 0.199)], [])
        assert below.outcome == "insufficient_evidence"
        assert below.caveats

    def test_contradicting_evidence_caps_the_outcome_below_recommend(self) -> None:
        """Heavy contradiction cannot leave a RECOMMEND. With the default
        weights the count score collapses to 0.1 and the aggregate lands at
        0.3*0.1 + 0.4*0.9 + 0.3*0.9 = 0.66 -- CAUTION, not REJECT: the count
        criterion carries only a third of the weight, so a high-quality
        minority still keeps a decision out of the reject band. The law being
        pinned is that RECOMMEND is unreachable here."""
        engine, ke, _ = _engine()
        decision = engine.make_decision(
            "claim-s23", [_pair(ke, "s1", 0.9)], [_pair(ke, f"c{i}", 0.9) for i in range(9)]
        )
        assert decision.trace.aggregate_score == pytest.approx(0.66, abs=1e-12)
        assert decision.outcome == "caution"

    def test_per_criterion_threshold_gates_the_recommend(self) -> None:
        """S23 defect D-T02, fixed: a criterion carrying weight but scoring
        below its own declared threshold must block RECOMMEND. The field used
        to be decorative -- the enforcement loop evaluated ``threshold_met and
        True`` and never read ``criterion.threshold``.
        """
        criteria = [
            DecisionCriterion(name="evidence_count", weight=0.3, threshold=0.5),
            DecisionCriterion(name="evidence_quality", weight=0.4, threshold=0.6),
            DecisionCriterion(name="confidence", weight=0.3, threshold=0.5),
        ]
        engine, ke, _ = _engine()
        clean = engine.make_decision("claim-s23", [_pair(ke, "s1", 0.95)], [], criteria=criteria)
        assert clean.outcome == "recommend"  # 1.0 / 0.95 / 0.95 all above
        gated = engine.make_decision(
            "claim-s23", [_pair(ke, "s2", 0.95)], [_pair(ke, "c1", 0.95)], criteria=criteria
        )
        # count 0.5 (boundary, still meets its 0.5 threshold) -- push it below
        # with two contradicting facts.
        gated = engine.make_decision(
            "claim-s23",
            [_pair(ke, "s2", 0.95)],
            [_pair(ke, "c1", 0.95), _pair(ke, "c2", 0.95)],
            criteria=criteria,
        )
        evidence_count_score = gated.trace.criterion_scores["evidence_count"]
        assert evidence_count_score is not None
        assert evidence_count_score < 0.5
        assert gated.outcome != "recommend", (
            "a sub-threshold criterion must cap the outcome below recommend"
        )


class TestHonestyContract:
    """No evidence must not become a verdict."""

    def test_no_facts_is_insufficient_evidence(self) -> None:
        engine, _, _ = _engine()
        decision = engine.make_decision("claim-s23", [], [])
        assert decision.outcome == "insufficient_evidence"
        assert decision.confidence == 0.0
        assert any("insufficient" in c.lower() for c in decision.caveats)

    def test_missing_knowledge_engine_is_declared_in_the_caveats(self) -> None:
        engine = DecisionEngine()
        decision = engine.make_decision("claim-s23", [_fact("s1", 0.5)], [])
        assert any("knowledge engine" in c.lower() for c in decision.caveats)

    def test_wrong_confidence_bound_is_rejected_by_the_evidence_model(self) -> None:
        with pytest.raises(ValueError):
            Evidence(
                id="e",
                confidence=1.5,
                source=EvidenceSource.MEASUREMENT,
                evidence_type=EvidenceType.QUANTITATIVE,
                value=1.0,
                provenance=[],
                metadata={},
            )


class TestTraceabilityAndDeterminism:
    def test_trace_records_every_fact_weight_and_score(self) -> None:
        engine, ke, _ = _engine()
        supporting = [_pair(ke, "s1", 0.8)]
        contradicting = [_pair(ke, "c1", 0.2)]
        decision = engine.make_decision("claim-s23", supporting, contradicting)
        trace = decision.trace
        assert set(trace.fact_ids) == {"s1", "c1"}
        assert trace.evidence_weights == DEFAULT_WEIGHTS
        assert set(trace.criterion_scores) == set(DEFAULT_WEIGHTS)
        assert trace.claim_id == "claim-s23"
        assert trace.trace_id.startswith("trace_")
        assert trace.decision_id == decision.decision_id

    def test_decisions_are_deterministic_modulo_identifiers(self) -> None:
        engine, ke, _ = _engine()
        facts = [_pair(ke, "s1", 0.8), _pair(ke, "s2", 0.6)]
        a = engine.make_decision("claim-s23", facts, [])
        b = engine.make_decision("claim-s23", list(reversed(facts)), [])
        assert a.outcome == b.outcome
        assert a.trace.aggregate_score == b.trace.aggregate_score
        assert a.rationale == b.rationale
        assert a.recommendations == b.recommendations

    def test_rationale_reports_every_criterion(self) -> None:
        engine, ke, _ = _engine()
        decision = engine.make_decision("claim-s23", [_pair(ke, "s1", 0.8)], [])
        for name in DEFAULT_WEIGHTS:
            assert name in decision.rationale

    def test_decision_is_retrievable_by_id(self) -> None:
        engine, ke, _ = _engine()
        decision = engine.make_decision("claim-s23", [_pair(ke, "s1")], [])
        assert engine.get_decision(decision.decision_id) is decision
        assert engine.get_decision("nope") is None
        assert decision in engine.all_decisions()


class TestEvidenceEngine:
    """Provenance resolution, chain integrity and its documented scope."""

    @staticmethod
    def _collect(engine: EvidenceEngine, eid: str, provenance: list[str]) -> Evidence:
        return engine.collect(
            Evidence(
                id=eid,
                source=EvidenceSource.MEASUREMENT,
                evidence_type=EvidenceType.QUANTITATIVE,
                value=1.0,
                confidence=1.0,
                provenance=provenance,
                metadata={},
            )
        )

    def test_collect_get_validate_round_trip(self) -> None:
        engine = EvidenceEngine()
        stored = self._collect(engine, "e1", [])
        assert engine.get("e1") is stored
        assert engine.validate("e1").is_valid

    def test_resolved_provenance_chain_passes_integrity(self) -> None:
        engine = EvidenceEngine()
        self._collect(engine, "root", [])
        self._collect(engine, "child", ["root"])
        assert engine.validate_chain_integrity() is True

    def test_dangling_provenance_fails_integrity(self) -> None:
        engine = EvidenceEngine()
        self._collect(engine, "orphan", ["no-such-evidence"])
        assert engine.validate_chain_integrity() is False

    def test_trace_resolves_fact_prefixed_references(self) -> None:
        engine = EvidenceEngine()
        self._collect(engine, "root", [])
        self._collect(engine, "leaf", ["fact_root"])
        assert [e.id for e in engine.trace("leaf")] == ["leaf", "root"]

    def test_trace_survives_a_provenance_cycle(self) -> None:
        engine = EvidenceEngine()
        self._collect(engine, "a", ["b"])
        self._collect(engine, "b", ["a"])
        assert {e.id for e in engine.trace("a")} == {"a", "b"}

    def test_export_chain_shape_and_unknown_id(self) -> None:
        engine = EvidenceEngine()
        self._collect(engine, "e1", [])
        export = engine.export_chain("e1")
        assert export["evidence_id"] == "e1"
        assert export["chain"][0]["id"] == "e1"
        assert export["integrity"] is True
        assert export["derived_facts"] == []
        with pytest.raises(KeyError):
            engine.export_chain("missing")

    def test_integrity_is_reference_resolution_not_content_hashing(self) -> None:
        """Recorded limitation, pinned deliberately: the documented contract
        of ``validate_chain_integrity`` is that every provenance link RESOLVES.
        It is not a tamper seal -- a mutated value with intact references still
        reports True. Anyone relying on content immutability must add a digest;
        this test fails the moment that changes, so the limit cannot be
        silently forgotten."""
        engine = EvidenceEngine()
        self._collect(engine, "root", [])
        self._collect(engine, "child", ["root"])
        root = engine.get("root")
        assert root is not None
        root.value = 999.0  # tamper; references still resolve
        assert engine.validate_chain_integrity() is True

    def test_decision_and_evidence_link_through_register_decision(self) -> None:
        """``register_decision`` reads the decision's ``decision_id`` /
        ``claim_id`` / ``outcome`` attributes, so the snapshot it stores is
        the decision object itself (as ``DecisionEngine`` produces), not a
        dict."""
        engine = EvidenceEngine()
        self._collect(engine, "e1", [])
        fact = engine.to_fact("e1", statement="derived fact")
        decision = SimpleNamespace(
            decision_id="d1",
            claim_id="claim-s23",
            outcome="recommend",
            confidence=0.8,
        )
        engine.register_decision(decision, fact.id)
        export = engine.export_chain("e1")
        assert any(f["fact_id"] == fact.id for f in export["derived_facts"])
        assert any(d.get("decision_id") == "d1" for d in export["derived_decisions"])
