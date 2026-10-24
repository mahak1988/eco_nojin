"""Optional economic/social criteria for the Decision Engine (Tasmimyar).

Pure additive contract of ``engine/tasmimyar/__init__.py``:

* ``economic_criteria_weights(variant)`` returns opt-in criteria sets for the
  "scientific" (engine defaults), "economic", "social" and "composite"
  variants, and rejects anything else;
* ``make_decision(..., economic_context={...})`` scores ``economic_npv``,
  ``economic_risk`` (direction *minimize*) and ``social_employment``
  (default weight 0.0, i.e. disabled unless opted into);
* the default scientific path is unchanged: same outcome, same aggregate,
  same criterion scores, same rationale, same caveats, same trace fields.

The laws pinned here, in the order of the change description:

1. default behaviour is byte-compatible with the pre-change engine for a
   supported, high-confidence chain (``recommend`` preserved);
2. with an economic context, a high-NPV case aggregates higher than a
   low-NPV case;
3. the ``minimize`` direction inverts the risk criterion, so a higher
   Value at Risk lowers the aggregate;
4. a zero-weight criterion changes nothing at all;
5. ``DecisionTrace`` records the criterion scores, the direction of every
   criterion and the economic context consumed -- additively, so a trace
   built with the historical fields still deserialises.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any, cast

import pytest

from engine.knowledge import Claim, Fact, KnowledgeEngine
from engine.tasmimyar import (
    CRITERIA_VARIANTS,
    DEFAULT_FTE_REFERENCE,
    DEFAULT_NPV_BASE,
    ECONOMIC_RISK_EPS,
    DecisionCriterion,
    DecisionEngine,
    DecisionTrace,
    economic_criteria_weights,
)

# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

SUPPORTING_CONFIDENCE = 0.95


def _wire() -> tuple[DecisionEngine, KnowledgeEngine, Fact]:
    """A fully wired engine plus one asserted supporting fact."""
    ke = KnowledgeEngine()
    ke.register_claim(Claim(id="claim-eco", text="The project is viable"))
    ke.assert_fact(
        Fact(
            id="f1",
            statement="independent measurements support viability",
            source_id="src-eco",
            confidence=SUPPORTING_CONFIDENCE,
        )
    )
    fact = ke.get_fact("f1")
    assert fact is not None
    return DecisionEngine(knowledge_engine=ke), ke, fact


def _economic_variant() -> list[DecisionCriterion]:
    return economic_criteria_weights("economic")


def _decision_snapshot(decision: Any) -> tuple:
    """Everything a caller could observe, excluding identifiers and time."""
    trace = decision.trace
    return (
        decision.outcome,
        decision.confidence,
        decision.status.value,
        trace.claim_status,
        trace.claim_confidence,
        trace.aggregate_score,
        tuple(trace.criterion_scores.items()),
        dict(trace.evidence_weights),
        tuple(trace.fact_ids),
        decision.rationale,
        tuple(decision.recommendations),
        tuple(decision.caveats),
    )


# --------------------------------------------------------------------------- #
# 1. Backward compatibility: the default path is unchanged                     #
# --------------------------------------------------------------------------- #


class TestBackwardCompatibility:
    """The scientific path must be byte-compatible with the pre-change engine."""

    def test_supported_high_confidence_chain_still_recommends(self) -> None:
        engine, _, fact = _wire()
        decision = engine.make_decision("claim-eco", [fact], [])

        # count 1.0 (one supporting, no contradicting), quality 0.95,
        # claim confidence 0.95 (mean of the supporting facts):
        # 0.3*1.0 + 0.4*0.95 + 0.3*0.95 = 0.965 >= 0.7, every default
        # threshold (0.5 / 0.6 / 0.5) met -> RECOMMEND.
        assert decision.outcome == "recommend"
        assert decision.trace.aggregate_score == pytest.approx(
            0.3 * 1.0 + 0.4 * 0.95 + 0.3 * 0.95, rel=1e-12
        )
        assert decision.trace.criterion_scores == {
            "evidence_count": pytest.approx(1.0),
            "evidence_quality": pytest.approx(SUPPORTING_CONFIDENCE),
            "confidence": pytest.approx(SUPPORTING_CONFIDENCE),
        }

    def test_default_decision_has_no_economic_footprint(self) -> None:
        engine, _, fact = _wire()
        decision = engine.make_decision("claim-eco", [fact], [])

        # No economic context was consumed, so none is recorded ...
        assert decision.trace.economic_context is None
        # ... the only new field that is always populated is the direction
        # map, and it restates the existing criteria.
        assert decision.trace.criterion_directions == {
            "evidence_count": "maximize",
            "evidence_quality": "maximize",
            "confidence": "maximize",
        }
        # Default criteria are still exactly the three scientific ones with
        # their governance-recorded weights and thresholds.
        assert [c.name for c in engine._default_criteria] == [
            "evidence_count",
            "evidence_quality",
            "confidence",
        ]
        assert [(c.weight, c.threshold) for c in engine._default_criteria] == [
            (0.3, 0.5),
            (0.4, 0.6),
            (0.3, 0.5),
        ]

    def test_legacy_positional_call_is_unchanged(self) -> None:
        """The gateway calls make_decision positionally with five arguments."""
        engine, _, fact = _wire()
        legacy = engine.make_decision("claim-eco", [fact], [], None, None)
        explicit = engine.make_decision("claim-eco", [fact], [])
        assert legacy.outcome == explicit.outcome
        assert legacy.trace.aggregate_score == explicit.trace.aggregate_score
        assert legacy.rationale == explicit.rationale
        assert legacy.caveats == explicit.caveats
        assert legacy.trace.criterion_scores == explicit.trace.criterion_scores

    def test_omitting_economic_context_matches_the_historical_snapshot(self) -> None:
        """A default decision is identical to what the old code produced.

        ``economic_context`` is a new optional parameter with a ``None``
        default, and every new trace field is either ``None`` or a restatement
        of data the trace already carried. Both facts are asserted here by
        rebuilding the decision with the scientific criteria *and* an
        explicitly ``None`` economic context.
        """
        engine, _, fact = _wire()
        before = engine.make_decision("claim-eco", [fact], [])
        after = engine.make_decision(
            "claim-eco",
            [fact],
            [],
            criteria=economic_criteria_weights("scientific"),
            parameters=None,
            economic_context=None,
        )
        assert _decision_snapshot(after) == _decision_snapshot(before)

    def test_rationale_is_byte_identical_on_the_default_path(self) -> None:
        engine, _, fact = _wire()
        decision = engine.make_decision("claim-eco", [fact], [])
        assert decision.rationale == (
            "Decision outcome: recommend. "
            "Claim status: supported. "
            "Confidence: 0.95. "
            "Criterion 'evidence_count' score: 1.00. "
            "Criterion 'evidence_quality' score: 0.95. "
            "Criterion 'confidence' score: 0.95."
        )

    def test_gateway_style_decision_is_still_evidence_linked(self) -> None:
        """The Evidence -> Fact -> Decision chain is untouched."""
        from engine.evidence import Evidence, EvidenceEngine, EvidenceSource

        ke = KnowledgeEngine()
        ke.register_claim(Claim(id="claim-eco-chain", text="Chain survives"))
        ee = EvidenceEngine(knowledge_engine=ke)
        measurement = ee.collect(
            Evidence(source=EvidenceSource.MEASUREMENT, value=30.0, confidence=0.95)
        )
        model_ev = ee.collect(
            Evidence(
                source=EvidenceSource.MODEL,
                value={"cec": 15.0},
                confidence=0.9,
                provenance=[measurement.id],
            )
        )
        fact = ee.to_fact(model_ev.id, "CEC is high and supports viability")
        decision = DecisionEngine(knowledge_engine=ke, evidence_engine=ee).make_decision(
            "claim-eco-chain", [fact], []
        )
        assert decision.outcome == "recommend"
        assert fact.id in decision.trace.fact_ids
        ee.register_decision(decision, fact.id)
        export = ee.export_chain(model_ev.id)
        assert any(
            d["decision_id"] == decision.decision_id
            for d in export["derived_decisions"]
        )


# --------------------------------------------------------------------------- #
# 2. The opt-in criteria table                                                 #
# --------------------------------------------------------------------------- #


class TestCriteriaVariants:
    """``economic_criteria_weights`` is the single opt-in surface."""

    def test_variants_are_exactly_four_and_documented(self) -> None:
        assert CRITERIA_VARIANTS == ("scientific", "economic", "social", "composite")
        for variant in CRITERIA_VARIANTS:
            assert economic_criteria_weights(variant), variant

    def test_default_variant_is_economic(self) -> None:
        assert [c.name for c in economic_criteria_weights()] == [
            "economic_npv",
            "economic_risk",
        ]

    def test_scientific_variant_equals_the_engine_defaults(self) -> None:
        engine = DecisionEngine()
        recorded = economic_criteria_weights("scientific")
        assert [(c.name, c.weight, c.threshold, c.direction) for c in recorded] == [
            (c.name, c.weight, c.threshold, c.direction) for c in engine._default_criteria
        ]

    def test_economic_variant_splits_npv_and_risk_evenly(self) -> None:
        criteria = {c.name: c for c in _economic_variant()}
        assert set(criteria) == {"economic_npv", "economic_risk"}
        assert criteria["economic_npv"].weight == 0.5
        assert criteria["economic_npv"].direction == "maximize"
        assert criteria["economic_npv"].threshold == 0.5
        assert criteria["economic_risk"].weight == 0.5
        # The one minimize criterion in the engine.
        assert criteria["economic_risk"].direction == "minimize"
        assert criteria["economic_risk"].threshold == 0.5

    def test_social_variant_optimum(self) -> None:
        (criterion,) = economic_criteria_weights("social")
        assert criterion.name == "social_employment"
        assert criterion.weight == 1.0
        assert criterion.direction == "maximize"
        assert criterion.threshold == 0.5

    def test_composite_variant_carres_six_criteria_and_sums_to_one(self) -> None:
        criteria = {c.name: c for c in economic_criteria_weights("composite")}
        assert set(criteria) == {
            "evidence_count",
            "evidence_quality",
            "confidence",
            "economic_npv",
            "economic_risk",
            "social_employment",
        }
        weights = {name: c.weight for name, c in criteria.items()}
        assert weights == {
            "evidence_count": 0.2,
            "evidence_quality": 0.25,
            "confidence": 0.15,
            "economic_npv": 0.2,
            "economic_risk": 0.1,
            "social_employment": 0.1,
        }
        assert sum(weights.values()) == pytest.approx(1.0)
        # Scientific evidence keeps the majority of the scoreboard.
        assert sum(
            weights[n] for n in ("evidence_count", "evidence_quality", "confidence")
        ) == pytest.approx(0.6)
        # Thresholds survive the re-weighting.
        assert criteria["evidence_quality"].threshold == 0.6
        assert criteria["economic_risk"].direction == "minimize"

    def test_variant_is_case_and_whitespace_insensitive(self) -> None:
        assert [c.name for c in economic_criteria_weights(" Economic ")] == [
            "economic_npv",
            "economic_risk",
        ]

    def test_unknown_variant_raises_and_names_the_valid_ones(self) -> None:
        with pytest.raises(ValueError) as err:
            economic_criteria_weights("utopian")
        message = str(err.value)
        assert "utopian" in message
        for variant in CRITERIA_VARIANTS:
            assert variant in message

    def test_returned_lists_are_independent_objects(self) -> None:
        """A caller mutating one variant's weights cannot poison the engine."""
        first = economic_criteria_weights("composite")
        first[0].weight = 99.0
        second = economic_criteria_weights("composite")
        assert second[0].weight == 0.2
        assert DecisionEngine()._default_criteria[0].weight == 0.3


# --------------------------------------------------------------------------- #
# 3. The score mappings, pinned to their documented formulas                    #
# --------------------------------------------------------------------------- #


class TestNpvMapping:
    """``economic_npv = clip(0.5 + npv_irr / (2 * npv_base), 0, 1)``."""

    @staticmethod
    def _score(npv: float, npv_base: float | None = None) -> float:
        engine, _, fact = _wire()
        parameters = {"npv_base": npv_base} if npv_base is not None else None
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(),
            parameters=parameters,
            economic_context={"npv_irr": npv, "value_at_risk_irr": 0.0},
        )
        score = decision.trace.criterion_scores["economic_npv"]
        assert score is not None
        return score

    def test_break_even_is_neutral(self) -> None:
        assert self._score(0.0) == pytest.approx(0.5)

    def test_positive_npv_lerps_upwards(self) -> None:
        assert self._score(0.5 * DEFAULT_NPV_BASE) == pytest.approx(0.75)
        assert self._score(DEFAULT_NPV_BASE) == pytest.approx(1.0)

    def test_negative_npv_lerps_downwards_to_zero(self) -> None:
        assert self._score(-0.5 * DEFAULT_NPV_BASE) == pytest.approx(0.25)
        assert self._score(-DEFAULT_NPV_BASE) == pytest.approx(0.0)

    def test_saturates_both_ways(self) -> None:
        assert self._score(1e15) == pytest.approx(1.0)
        assert self._score(-1e15) == pytest.approx(0.0)

    def test_is_monotone_increasing(self) -> None:
        samples = [-1e7, -5e6, 0.0, 1e6, 5e6, 1e7, 5e7]
        scores = [self._score(value) for value in samples]
        assert scores == sorted(scores)
        assert scores == pytest.approx(
            [0.0, 0.25, 0.5, 0.55, 0.75, 1.0, 1.0]
        )

    def test_npv_base_is_configurable(self) -> None:
        """A small ``npv_base`` makes a smaller project look good."""
        assert self._score(1.0e6, npv_base=2.0e6) == pytest.approx(0.75)
        assert self._score(1.0e6) < self._score(1.0e6, npv_base=2.0e6)

    def test_non_positive_npv_base_is_rejected(self) -> None:
        engine, _, fact = _wire()
        with pytest.raises(ValueError):
            engine.make_decision(
                "claim-eco", [fact], [], criteria=_economic_variant(),
                parameters={"npv_base": 0.0},
                economic_context={"npv_irr": 1.0e6},
            )


class TestRiskMapping:
    """``economic_risk = 1 - clip(var_irr / (npv_irr + var_irr + eps), 0, 1)``."""

    @staticmethod
    def _score(npv: float, value_at_risk: float) -> float:
        engine, _, fact = _wire()
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(),
            economic_context={"npv_irr": npv, "value_at_risk_irr": value_at_risk},
        )
        score = decision.trace.criterion_scores["economic_risk"]
        assert score is not None
        return score

    def test_no_loss_is_a_perfect_score(self) -> None:
        assert self._score(5.0e6, 0.0) == pytest.approx(1.0)

    def test_loss_equals_gain_is_neutral(self) -> None:
        assert self._score(5.0e6, 5.0e6) == pytest.approx(0.5)

    def test_loss_dominates_exposure(self) -> None:
        # var / (npv + var) = 20 / 25 = 0.8 -> score 0.2
        assert self._score(5.0e6, 20.0e6) == pytest.approx(1.0 - 20.0 / 25.0)

    def test_is_monotone_decreasing_in_value_at_risk(self) -> None:
        samples = [0.0, 1.0e6, 5.0e6, 20.0e6]
        scores = [self._score(5.0e6, value) for value in samples]
        assert scores == sorted(scores, reverse=True)
        for low, high in zip(samples, samples[1:], strict=False):
            assert self._score(5.0e6, low) > self._score(5.0e6, high)

    def test_direction_is_inverted_relative_to_the_raw_loss_fraction(self) -> None:
        """The minimize direction is honoured, not hardcoded into the formula."""
        engine, _, fact = _wire()
        context = {"npv_irr": 5.0e6, "value_at_risk_irr": 1.0e6}
        minimize = DecisionCriterion(
            name="economic_risk", weight=1.0, threshold=0.0, direction="minimize"
        )
        maximize = DecisionCriterion(
            name="economic_risk", weight=1.0, threshold=0.0, direction="maximize"
        )
        inverted = engine.make_decision(
            "claim-eco", [fact], [], criteria=[minimize], economic_context=context
        ).trace.criterion_scores["economic_risk"]  # type: ignore[union-attr]
        raw = engine.make_decision(
            "claim-eco", [fact], [], criteria=[maximize], economic_context=context
        ).trace.criterion_scores["economic_risk"]  # type: ignore[union-attr]
        # The criterion is explicitly selected above, so both scores exist.
        assert inverted is not None
        assert raw is not None
        loss_fraction = 1.0e6 / (5.0e6 + 1.0e6 + ECONOMIC_RISK_EPS)
        assert inverted == pytest.approx(1.0 - loss_fraction)
        assert raw == pytest.approx(loss_fraction)
        assert inverted + raw == pytest.approx(1.0)

    def test_non_positive_exposure_cannot_look_safe(self) -> None:
        """A project whose NPV is already worse than its exposure scores 0."""
        assert self._score(-5.0e6, 5.0e6) == pytest.approx(0.0)

    def test_requires_both_keys(self) -> None:
        engine, _, fact = _wire()
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(),
            economic_context={"npv_irr": 5.0e6},
        )
        assert decision.trace.criterion_scores["economic_risk"] is None
        assert any("value_at_risk_irr" in c for c in decision.caveats)


class TestEmploymentMapping:
    """``social_employment = clip(direct_employment_fte / 10, 0, 1)``."""

    @staticmethod
    def _score(fte: float, fte_reference: float | None = None) -> float:
        engine, _, fact = _wire()
        parameters = {"fte_reference": fte_reference} if fte_reference is not None else None
        decision = engine.make_decision(
            "claim-eco", [fact], [],
            criteria=economic_criteria_weights("social"),
            parameters=parameters,
            economic_context={"direct_employment_fte": fte},
        )
        score = decision.trace.criterion_scores["social_employment"]
        assert score is not None
        return score

    def test_reference_employment_saturates(self) -> None:
        assert self._score(DEFAULT_FTE_REFERENCE) == pytest.approx(1.0)
        assert self._score(100.0) == pytest.approx(1.0)

    def test_half_the_reference_is_neutral(self) -> None:
        assert self._score(0.5 * DEFAULT_FTE_REFERENCE) == pytest.approx(0.5)

    def test_no_employment_is_zero_and_negative_is_clipped(self) -> None:
        assert self._score(0.0) == pytest.approx(0.0)
        assert self._score(-5.0) == pytest.approx(0.0)

    def test_is_monotone_increasing_and_saturating(self) -> None:
        scores = [self._score(value) for value in (0.0, 2.5, 5.0, 10.0, 50.0)]
        assert scores == sorted(scores)
        assert scores[-1] == pytest.approx(1.0)
        assert all(
            low <= high for low, high in zip(scores, scores[1:], strict=False)
        )

    def test_reference_is_configurable(self) -> None:
        assert self._score(4.0, fte_reference=8.0) == pytest.approx(0.5)
        assert self._score(4.0) == pytest.approx(0.4)

    def test_non_positive_reference_is_rejected(self) -> None:
        engine, _, fact = _wire()
        with pytest.raises(ValueError):
            engine.make_decision(
                "claim-eco", [fact], [],
                criteria=economic_criteria_weights("social"),
                parameters={"fte_reference": -1.0},
                economic_context={"direct_employment_fte": 4.0},
            )


# --------------------------------------------------------------------------- #
# 4. Opt-in scoring: NPV, risk (minimize) and the composite scoreboard          #
# --------------------------------------------------------------------------- #


class TestEconomicOptIn:
    """A caller must both opt in and supply the context."""

    def test_high_npv_aggregates_above_low_npv(self) -> None:
        engine, _, fact = _wire()
        criteria = _economic_variant()
        high = engine.make_decision(
            "claim-eco", [fact], [], criteria=criteria,
            economic_context={"npv_irr": 5.0e6, "value_at_risk_irr": 1.0e6},
        )
        low = engine.make_decision(
            "claim-eco", [fact], [], criteria=criteria,
            economic_context={"npv_irr": 1.0e6, "value_at_risk_irr": 1.0e6},
        )
        assert high.trace.criterion_scores["economic_npv"] == pytest.approx(0.75)
        assert low.trace.criterion_scores["economic_npv"] == pytest.approx(0.55)
        assert high.trace.aggregate_score > low.trace.aggregate_score
        assert high.trace.aggregate_score == pytest.approx(
            0.5 * 0.75 + 0.5 * (1.0 - 1.0e6 / (5.0e6 + 1.0e6 + ECONOMIC_RISK_EPS))
        )
        # The same facts, the same scientific evidence, a different verdict.
        assert high.outcome == "recommend"
        assert low.outcome == "caution"

    def test_higher_value_at_risk_lowers_the_aggregate(self) -> None:
        engine, _, fact = _wire()
        criteria = _economic_variant()
        modest = engine.make_decision(
            "claim-eco", [fact], [], criteria=criteria,
            economic_context={"npv_irr": 5.0e6, "value_at_risk_irr": 5.0e6},
        )
        severe = engine.make_decision(
            "claim-eco", [fact], [], criteria=criteria,
            economic_context={"npv_irr": 5.0e6, "value_at_risk_irr": 20.0e6},
        )
        severe_risk = severe.trace.criterion_scores["economic_risk"]
        modest_risk = modest.trace.criterion_scores["economic_risk"]
        assert severe_risk is not None and modest_risk is not None
        assert severe_risk < modest_risk
        assert severe.trace.aggregate_score < modest.trace.aggregate_score
        assert modest.trace.aggregate_score == pytest.approx(0.625)
        assert severe.trace.aggregate_score == pytest.approx(0.475)

    def test_npv_still_wins_over_risk_when_the_numbers_are_mild(self) -> None:
        """The 0.5 / 0.5 economic split keeps value creation decisive."""
        engine, _, fact = _wire()
        criteria = _economic_variant()
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=criteria,
            economic_context={"npv_irr": 8.0e6, "value_at_risk_irr": 8.0e6},
        )
        # NPV 0.9, risk 1 - 0.5 = 0.5 -> aggregate 0.7 exactly, recomended.
        assert decision.trace.criterion_scores["economic_npv"] == pytest.approx(0.9)
        assert decision.trace.aggregate_score == pytest.approx(0.7)
        assert decision.outcome == "recommend"

    def test_composite_blends_scientific_and_economic_dimensions(self) -> None:
        engine, _, fact = _wire()
        context = {
            "npv_irr": 5.0e6,
            "value_at_risk_irr": 1.0e6,
            "direct_employment_fte": 4.0,
        }
        decision = engine.make_decision(
            "claim-eco", [fact], [],
            criteria=economic_criteria_weights("composite"),
            economic_context=context,
        )
        scores = decision.trace.criterion_scores
        assert scores["evidence_count"] == pytest.approx(1.0)
        assert scores["evidence_quality"] == pytest.approx(0.95)
        assert scores["economic_npv"] == pytest.approx(0.75)
        assert scores["economic_risk"] == pytest.approx(1.0 - 1.0 / 6.0)
        assert scores["social_employment"] == pytest.approx(0.4)
        expected = (
            0.2 * 1.0
            + 0.25 * 0.95
            + 0.15 * 0.95
            + 0.2 * 0.75
            + 0.1 * (1.0 - 1.0 / 6.0)
            + 0.1 * 0.4
        )
        assert decision.trace.aggregate_score == pytest.approx(expected)
        assert decision.trace.evidence_weights == {
            "evidence_count": 0.2,
            "evidence_quality": 0.25,
            "confidence": 0.15,
            "economic_npv": 0.2,
            "economic_risk": 0.1,
            "social_employment": 0.1,
        }

    def test_composite_threshold_gate_still_bites(self) -> None:
        """A sub-threshold economic criterion must cap a RECOMMEND."""
        engine, _, fact = _wire()
        criteria = economic_criteria_weights("composite")
        weak = DecisionCriterion(
            name="economic_npv", weight=0.2, threshold=0.9, direction="maximize"
        )
        blended = [weak if c.name == "economic_npv" else c for c in criteria]
        rich_context = {
            "npv_irr": 5.0e6,
            "value_at_risk_irr": 1.0e6,
            "direct_employment_fte": 4.0,
        }
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=blended,
            economic_context=rich_context,
        )
        assert decision.trace.aggregate_score >= 0.7
        npv_score = decision.trace.criterion_scores["economic_npv"]
        assert npv_score is not None
        assert npv_score < 0.9
        assert decision.outcome == "caution"

    def test_economic_context_without_opt_in_changes_nothing(self) -> None:
        """Supplying context to the default criteria must be inert."""
        engine, _, fact = _wire()
        context = {"npv_irr": -1e9, "value_at_risk_irr": 1e9, "direct_employment_fte": 0.0}
        swept = engine.make_decision("claim-eco", [fact], [], economic_context=context)
        default = engine.make_decision("claim-eco", [fact], [])
        assert _decision_snapshot(swept) == _decision_snapshot(default)

    def test_missing_context_is_declared_not_invented(self) -> None:
        engine, _, fact = _wire()
        decision = engine.make_decision("claim-eco", [fact], [], criteria=_economic_variant())
        assert decision.trace.criterion_scores == {
            "economic_npv": None,
            "economic_risk": None,
        }
        # Nothing was scored, so nothing is aggregated: the historical
        # all-zero-weight guard returns 0.0 rather than dividing by zero.
        assert decision.trace.aggregate_score == 0.0
        assert decision.rationale.count("was not scored") == 2
        caveats = " ".join(decision.caveats)
        assert "economic_npv" in caveats and "economic_risk" in caveats

    def test_partial_context_renormalises_over_the_scored_criteria(self) -> None:
        """Only the criteria with data are normalised, and it is declared."""
        engine, _, fact = _wire()
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(),
            economic_context={"npv_irr": 5.0e6},
        )
        assert decision.trace.criterion_scores == {
            "economic_npv": pytest.approx(0.75),
            "economic_risk": None,
        }
        assert decision.trace.aggregate_score == pytest.approx(0.75)
        assert any("value_at_risk_irr" in c for c in decision.caveats)


class TestZeroWeightDisabled:
    """Weight 0.0 means inert: no score, no aggregation, no gate."""

    def test_zero_weight_economic_criteria_change_nothing(self) -> None:
        engine, _, fact = _wire()
        disabled = [
            DecisionCriterion(
                name="economic_npv", weight=0.0, threshold=0.5, direction="maximize"
            ),
            DecisionCriterion(
                name="economic_risk", weight=0.0, threshold=0.5, direction="minimize"
            ),
        ]
        context = {"npv_irr": -1e9, "value_at_risk_irr": 1e9}
        silenced = engine.make_decision(
            "claim-eco", [fact], [], criteria=disabled, economic_context=context
        )
        assert silenced.trace.criterion_scores == {"economic_npv": None, "economic_risk": None}
        assert silenced.trace.aggregate_score == 0.0
        assert silenced.outcome == "reject"
        # A disabled criterion is not caveated: the caller opted out of it.
        assert not any("economic" in c for c in silenced.caveats)
        assert silenced.trace.evidence_weights == {"economic_npv": 0.0, "economic_risk": 0.0}

    def test_zero_weight_alongside_scientific_criteria_is_inert(self) -> None:
        engine, _, fact = _wire()
        blended = economic_criteria_weights("scientific") + [
            DecisionCriterion(
                name="economic_npv", weight=0.0, threshold=0.5, direction="maximize"
            ),
            DecisionCriterion(
                name="economic_risk", weight=0.0, threshold=0.5, direction="minimize"
            ),
            DecisionCriterion(
                name="social_employment", weight=0.0, threshold=0.5, direction="maximize"
            ),
        ]
        context = {"npv_irr": 1e9, "value_at_risk_irr": 1e9, "direct_employment_fte": 999.0}
        with_disabled = engine.make_decision(
            "claim-eco", [fact], [], criteria=blended, economic_context=context
        )
        baseline = engine.make_decision(
            "claim-eco", [fact], [], criteria=economic_criteria_weights("scientific")
        )
        assert with_disabled.outcome == baseline.outcome
        assert with_disabled.trace.aggregate_score == baseline.trace.aggregate_score
        assert with_disabled.trace.aggregate_score == pytest.approx(
            0.3 * 1.0 + 0.4 * 0.95 + 0.3 * 0.95
        )
        # The disabled criteria are recorded as unscored and puzzle nothing.
        assert with_disabled.trace.criterion_scores["economic_npv"] is None
        assert with_disabled.trace.criterion_scores["social_employment"] is None
        assert with_disabled.rationale.count("was not scored") == 3

    def test_zero_weight_gates_nothing(self) -> None:
        """A zero-weight criterion below threshold cannot cap a RECOMMEND."""
        engine, _, fact = _wire()
        criteria = economic_criteria_weights("scientific") + [
            DecisionCriterion(
                name="economic_npv", weight=0.0, threshold=0.99, direction="maximize"
            )
        ]
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=criteria,
            economic_context={"npv_irr": 0.0},
        )
        assert decision.outcome == "recommend"


# --------------------------------------------------------------------------- #
# 5. Traceability                                                              #
# --------------------------------------------------------------------------- #


class TestTraceRecordsScores:
    """The trace carries the scores, the directions and the raw context."""

    def test_trace_records_economic_scores_and_directions(self) -> None:
        engine, _, fact = _wire()
        context = {"npv_irr": 5.0e6, "value_at_risk_irr": 1.0e6}
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(), economic_context=context
        )
        trace = decision.trace
        assert trace.criterion_scores == {
            "economic_npv": pytest.approx(0.75),
            "economic_risk": pytest.approx(1.0 - 1.0e6 / (5.0e6 + 1.0e6 + ECONOMIC_RISK_EPS)),
        }
        assert trace.criterion_directions == {
            "economic_npv": "maximize",
            "economic_risk": "minimize",
        }
        assert trace.evidence_weights == {"economic_npv": 0.5, "economic_risk": 0.5}
        assert trace.economic_context == context
        assert trace.economic_context is not context, "the caller's dict must be copied"
        # The aggregate recomputes from the recorded weights and scores.
        recomputed = sum(
            trace.evidence_weights[name] * score
            for name, score in trace.criterion_scores.items()
            if score is not None
        ) / sum(trace.evidence_weights.values())
        assert trace.aggregate_score == pytest.approx(recomputed)
        assert trace.outcome == decision.outcome
        assert trace.decision_id == decision.decision_id

    def test_trace_fields_are_additive(self) -> None:
        """``DecisionTrace`` gained fields; it lost none and reordered none."""
        names = [f.name for f in fields(DecisionTrace)]
        assert names[:11] == [
            "trace_id",
            "decision_id",
            "claim_id",
            "fact_ids",
            "evidence_weights",
            "claim_status",
            "claim_confidence",
            "criterion_scores",
            "aggregate_score",
            "outcome",
            "timestamp",
        ]
        assert names[11:] == ["economic_context", "criterion_directions"]
        by_name = {f.name: f for f in fields(DecisionTrace)}
        assert by_name["economic_context"].default is None
        assert by_name["criterion_directions"].default is None

    def test_historical_trace_construction_still_works(self) -> None:
        """A trace serialised before this change still deserialises."""
        from engine.tasmimyar import DecisionTrace

        historical: dict[str, Any] = {
            "trace_id": "trace_old",
            "decision_id": "dec_old",
            "claim_id": "claim-eco",
            "fact_ids": ["f1"],
            "evidence_weights": {"quality": 0.5},
            "claim_status": "supported",
            "claim_confidence": 0.9,
            "criterion_scores": {"quality": 0.9},
            "aggregate_score": 0.9,
            "outcome": "recommend",
        }
        trace = DecisionTrace(**historical)
        assert trace.economic_context is None
        assert trace.criterion_directions is None

    def test_decision_survives_a_serialisation_round_trip(self) -> None:
        """``asdict``/``DecisionTrace(**data)`` keeps the new fields."""
        from dataclasses import asdict

        from engine.tasmimyar import DecisionTrace

        engine, _, fact = _wire()
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=economic_criteria_weights("composite"),
            economic_context={
                "npv_irr": 5.0e6,
                "value_at_risk_irr": 1.0e6,
                "direct_employment_fte": 4.0,
            },
        )
        restored = DecisionTrace(**asdict(decision.trace))
        assert restored.criterion_scores == decision.trace.criterion_scores
        assert restored.economic_context == decision.trace.economic_context
        assert restored.criterion_directions == decision.trace.criterion_directions

    def test_decisions_are_deterministic_across_economic_calls(self) -> None:
        engine, _, fact = _wire()
        context = {"npv_irr": 5.0e6, "value_at_risk_irr": 1.0e6}
        first = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(), economic_context=context
        )
        second = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(), economic_context=dict(context)
        )
        assert first.outcome == second.outcome
        assert first.trace.aggregate_score == second.trace.aggregate_score
        assert first.rationale == second.rationale


# --------------------------------------------------------------------------- #
# 6. Validation: a malformed context never fabricates a score                 #
# --------------------------------------------------------------------------- #


class TestInvalidEconomicInput:
    @pytest.mark.parametrize("bad", ["lots", "1e6", None.__class__, [1e6], {"irr": 1}])
    def test_non_numeric_values_are_rejected(self, bad: Any) -> None:
        engine, _, fact = _wire()
        with pytest.raises(ValueError):
            engine.make_decision(
                "claim-eco", [fact], [], criteria=_economic_variant(),
                economic_context={"npv_irr": bad, "value_at_risk_irr": 1.0e6},
            )

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_values_are_rejected(self, bad: float) -> None:
        engine, _, fact = _wire()
        with pytest.raises(ValueError):
            engine.make_decision(
                "claim-eco", [fact], [], criteria=_economic_variant(),
                economic_context={"npv_irr": bad, "value_at_risk_irr": 1.0e6},
            )

    def test_booleans_are_not_economic_quantities(self) -> None:
        engine, _, fact = _wire()
        with pytest.raises(ValueError):
            engine.make_decision(
                "claim-eco", [fact], [],
                criteria=economic_criteria_weights("social"),
                economic_context={"direct_employment_fte": True},
            )

    def test_non_mapping_context_is_rejected(self) -> None:
        engine, _, fact = _wire()
        with pytest.raises(ValueError):
            engine.make_decision(
                "claim-eco", [fact], [], criteria=_economic_variant(),
                # Deliberately malformed input: a list of pairs is not a
                # mapping, and the call must be rejected.
                economic_context=cast("Any", [("npv_irr", 5.0e6)]),
            )

    def test_none_values_are_missing_data_not_an_error(self) -> None:
        engine, _, fact = _wire()
        decision = engine.make_decision(
            "claim-eco", [fact], [], criteria=_economic_variant(),
            economic_context={"npv_irr": None, "value_at_risk_irr": None},
        )
        assert decision.trace.criterion_scores == {"economic_npv": None, "economic_risk": None}

    def test_validation_only_applies_to_active_criteria(self) -> None:
        """A malformed key for a disabled criterion is never read."""
        engine, _, fact = _wire()
        decision = engine.make_decision(
            "claim-eco", [fact], [],
            criteria=[DecisionCriterion(name="economic_npv", weight=0.0)],
            economic_context={"npv_irr": "not a number"},
        )
        assert decision.trace.criterion_scores == {"economic_npv": None}
