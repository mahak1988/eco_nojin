"""
Decision Engine (Tasmimyar)
============================

The Decision Engine evaluates claims, manages decision criteria, and produces
traceable decisions that link back to evidence, uncertainty, and provenance.

Architecture:
    - DecisionEngine: orchestrates decision computation from claims + evidence
    - Decision: a single decision with full traceability
    - DecisionCriterion: configurable weighting of evidence dimensions
    - DecisionTrace: immutable record of how a decision was reached

Integration:
    - Consumes Fact objects from KnowledgeEngine
    - Produces Decision objects consumed by services/tasmimyar
    - Connects to EvidenceEngine for provenance tracking

Design principle: The Decision Engine never imports `database`. All
persistence is via PersistencePort injection.

Optional economic/social criteria:
    Three further criteria -- ``economic_npv``, ``economic_risk`` and
    ``social_employment`` -- are available but DISABLED by default. They are
    never part of ``DecisionEngine._default_criteria``; a caller opts in per
    decision by passing the list returned by :func:`economic_criteria_weights`
    together with ``make_decision(..., economic_context={...})``. The default
    scientific path is byte-for-byte unchanged.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import uuid4


class DecisionOutcome(StrEnum):
    """Possible outcomes a decision can reach."""
    
    RECOMMEND = "recommend"
    CAUTION = "caution"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class DecisionStatus(StrEnum):
    """Lifecycle status of a decision."""
    
    PENDING = "pending"
    EVALUATED = "evaluated"
    FINALIZED = "finalized"
    ARCHIVED = "archived"


# =====================================================================
# Optional economic / social criteria -- configuration and choices
# =====================================================================
# These values are GOVERNANCE CHOICES, not scientific constants: no
# derivation makes 10 FTE reference employment or 0.2 weight on NPV the
# "correct" posture for a project decision. They are documented here so
# that every number in the economic/social scores can be audited in one
# place, and so a caller can override them per decision through
# ``make_decision(..., parameters={"npv_base": ..., "fte_reference": ...})``.
#
# The three scientific criteria (evidence_count / evidence_quality /
# confidence) remain the engine's only defaults; nothing below changes
# them or their weights (see decision/weights.yaml, brake 8).

#: The criteria variants :func:`economic_criteria_weights` understands.
CRITERIA_VARIANTS: tuple[str, ...] = (
    "scientific",
    "economic",
    "social",
    "composite",
)

#: The keys each optional criterion reads out of ``economic_context``.
#: A criterion is scored only when every one of its keys is present.
ECONOMIC_CONTEXT_KEYS: dict[str, tuple[str, ...]] = {
    "economic_npv": ("npv_irr",),
    "economic_risk": ("npv_irr", "value_at_risk_irr"),
    "social_employment": ("direct_employment_fte",),
}

#: Reference net present value (currency units) for the ``economic_npv``
#: saturating map. The ramp is linear around zero and antisymmetric about the
#: neutral 0.5 at break-even: half of ``npv_base`` scores 0.75, minus half
#: scores 0.25, and it saturates at 1.0 for ``npv_irr >= +npv_base`` and at
#: 0.0 for ``npv_irr <= -npv_base``. The scale is a governance choice: the
#: projects this engine decides about are valued in the millions.
DEFAULT_NPV_BASE = 10_000_000.0

#: Reference direct employment (full-time equivalents) for the
#: ``social_employment`` saturation. 10 FTE is a small-project scale kept
#: deliberately modest so that labour-intensive projects of the sizes this
#: engine studies (per-plot to per-cooperative) score in the usable middle
#: of the band instead of saturating near 1.0.
DEFAULT_FTE_REFERENCE = 10.0

#: Epsilon that keeps the ``economic_risk`` loss fraction well defined when
#: both the NPV and the Value at Risk are zero.
ECONOMIC_RISK_EPS = 1e-9


def _clip_unit(value: float) -> float:
    """Clamp *value* into the closed unit interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _economic_value(context: Any, key: str) -> float | None:
    """Read one economic input from *context*, or ``None`` when absent.

    A present-but-non-numeric or non-finite value raises ``ValueError``
    instead of being coerced to 0.0: a silently zeroed NPV would fabricate a
    score out of data the caller never sent.
    """
    if context is None:
        return None
    if not isinstance(context, dict):
        raise ValueError(
            f"economic_context must be a mapping or None, got "
            f"{type(context).__name__}"
        )
    if key not in context or context[key] is None:
        return None
    raw = context[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ValueError(
            f"economic_context[{key!r}] must be a number or None, got "
            f"{raw!r} ({type(raw).__name__})"
        )
    value: float = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"economic_context[{key!r}] must be finite, got {value!r}")
    return value


def _positive_parameter(value: Any, key: str, default: float) -> float:
    """Resolve a strictly positive scoring parameter from *value*."""
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"parameters[{key!r}] must be a positive number or None, got {value!r}"
        )
    resolved: float = float(value)
    if not math.isfinite(resolved) or resolved <= 0.0:
        raise ValueError(
            f"parameters[{key!r}] must be a positive finite number, got {resolved!r}"
        )
    return resolved


@dataclass
class DecisionCriterion:
    """A single criterion for decision evaluation.
    
    Attributes:
        name: Unique identifier for the criterion.
        weight: Relative importance in [0, 1].
        threshold: Minimum score for accept recommendation.
        direction: "maximize" or "minimize" - whether higher values are better.
    """
    name: str
    weight: float = 0.0
    threshold: float = 0.0
    direction: str = "maximize"


def _scientific_criteria() -> list[DecisionCriterion]:
    """The three default scientific criteria, built fresh on every call.

    evidence_count 0.3 / evidence_quality 0.4 / confidence 0.3 with
    thresholds 0.5 / 0.6 / 0.5, all direction "maximize". These are the
    values recorded verbatim in ``decision/weights.yaml``; the engine's
    ``_default_criteria`` and the "scientific" variant of
    :func:`economic_criteria_weights` share this factory so they can never
    drift apart.
    """
    return [
        DecisionCriterion(
            name="evidence_count",
            weight=0.3,
            threshold=0.5,
            direction="maximize",
        ),
        DecisionCriterion(
            name="evidence_quality",
            weight=0.4,
            threshold=0.6,
            direction="maximize",
        ),
        DecisionCriterion(
            name="confidence",
            weight=0.3,
            threshold=0.5,
            direction="maximize",
        ),
    ]


def economic_criteria_weights(variant: str = "economic") -> list[DecisionCriterion]:
    """Return an opt-in criteria set for a decision variant.

    Variants:

    * ``"scientific"`` -- the engine defaults, the three scientific criteria
      (weights 0.3 / 0.4 / 0.3, thresholds 0.5 / 0.6 / 0.5). This is what
      ``make_decision`` uses when ``criteria`` is omitted.
    * ``"economic"`` -- ``economic_npv`` 0.5 + ``economic_risk`` 0.5
      (thresholds 0.5 each): value creation and value-at-risk share the
      scoreboard evenly.
    * ``"social"`` -- ``social_employment`` 1.0 (threshold 0.5).
    * ``"composite"`` -- all six criteria, scientific 0.2 / 0.25 / 0.15
      (count / quality / confidence) plus economic 0.2 / 0.1 / 0.1
      (NPV / risk / employment), summing to exactly 1.0.

    Every weight above 0.3 / 0.4 / 0.3 is a documented GOVERNANCE CHOICE,
    not a derivation: the composite keeps the proven scientific majority
    (60%) while giving the economic and social dimensions a 40% voice, and
    inside that voice value-at-risk and employment are weighted half of what
    NPV carries because a losing project is a stronger disqualifier than a
    low headcount is a weak recommender.

    The returned criteria are inert without evidence: the three economic and
    social criteria only produce a score when the caller also passes a
    matching ``economic_context`` to :meth:`DecisionEngine.make_decision`.
    With no context (or a weight of 0) they contribute nothing.

    Args:
        variant: One of ``CRITERIA_VARIANTS``.

    Returns:
        A fresh list of :class:`DecisionCriterion` objects, safe to mutate.

    Raises:
        ValueError: *variant* is not a known criteria variant.
    """
    name = str(variant).strip().lower()
    if name == "scientific":
        return _scientific_criteria()
    if name == "economic":
        return [
            DecisionCriterion(
                name="economic_npv", weight=0.5, threshold=0.5, direction="maximize"
            ),
            DecisionCriterion(
                name="economic_risk", weight=0.5, threshold=0.5, direction="minimize"
            ),
        ]
    if name == "social":
        return [
            DecisionCriterion(
                name="social_employment",
                weight=1.0,
                threshold=0.5,
                direction="maximize",
            )
        ]
    if name == "composite":
        # Re-weighted scientific block (0.2 / 0.25 / 0.15) plus the three
        # optional dimensions (0.2 / 0.1 / 0.1): total 1.0.
        return [
            DecisionCriterion(
                name="evidence_count", weight=0.2, threshold=0.5, direction="maximize"
            ),
            DecisionCriterion(
                name="evidence_quality", weight=0.25, threshold=0.6, direction="maximize"
            ),
            DecisionCriterion(
                name="confidence", weight=0.15, threshold=0.5, direction="maximize"
            ),
            DecisionCriterion(
                name="economic_npv", weight=0.2, threshold=0.5, direction="maximize"
            ),
            DecisionCriterion(
                name="economic_risk", weight=0.1, threshold=0.5, direction="minimize"
            ),
            DecisionCriterion(
                name="social_employment",
                weight=0.1,
                threshold=0.5,
                direction="maximize",
            ),
        ]
    raise ValueError(
        f"unknown criteria variant {variant!r}; expected one of "
        f"{', '.join(CRITERIA_VARIANTS)}"
    )


@dataclass
class DecisionTrace:
    """Immutable record of how a decision was computed.
    
    Provides traceable lineage from evidence facts through claim evaluation
    to final decision.
    
    Additive fields (optional economic/social provenance, never set by the
    default scientific path beyond ``criterion_directions``):
    
    * ``economic_context`` -- the economic inputs the decision consumed, so a
      score can be recomputed from the trace alone. ``None`` when the caller
      supplied none; the criterion scores are then ``None`` too.
    * ``criterion_directions`` -- criterion name -> "maximize"/"minimize", so
      the inversion applied to a ``minimize`` criterion is auditable from the
      trace without re-reading the criteria list.
    """
    trace_id: str
    decision_id: str
    claim_id: str
    fact_ids: list[str]
    evidence_weights: dict[str, float]
    claim_status: str
    claim_confidence: float
    #: Criterion name -> score in [0, 1] (already direction-adjusted), or
    #: ``None`` when the criterion carried weight but could not be scored
    #: (an economic criterion without matching ``economic_context``).
    criterion_scores: dict[str, float | None]
    aggregate_score: float
    outcome: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    economic_context: dict[str, Any] | None = None
    criterion_directions: dict[str, str] | None = None


@dataclass
class Decision:
    """A single decision produced by the Decision Engine.
    
    Attributes:
        decision_id: Unique identifier for this decision.
        claim_id: The claim being decided upon.
        outcome: One of DecisionOutcome values.
        confidence: Confidence in the decision, [0, 1].
        criteria: List of criteria that were evaluated.
        trace: Full trace of the decision computation.
        rationale: Human-readable explanation of the decision.
        recommendations: Actionable recommendations if outcome is RECOMMEND.
        caveats: Scientific or data limitations affecting this decision.
    """
    decision_id: str
    claim_id: str
    outcome: str
    confidence: float
    criteria: list[DecisionCriterion]
    trace: DecisionTrace
    rationale: str = ""
    recommendations: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    status: DecisionStatus = DecisionStatus.EVALUATED
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DecisionEngine:
    """Decision Engine for traceable decision-making.
    
    The Decision Engine evaluates claims against supporting and contradicting
    evidence (as Fact objects from the Knowledge Engine), applies configurable
    criteria weights, and produces traceable Decision objects.
    
    Integration points:
        - KnowledgeEngine.evaluate_claim() → claim status + confidence
        - EvidenceEngine → provenance tracking of decision inputs
        - EngineGateway → scientific computation as decision inputs
        
    Usage:
        engine = DecisionEngine(knowledge_engine=ke, evidence_engine=ee)
        decision = engine.make_decision(
            claim_id="claim_001",
            supporting_facts=[fact1, fact2],
            contradicting_facts=[fact3],
            criteria=[criterion1, criterion2]
        )
    """
    
    def __init__(
        self,
        knowledge_engine: Any = None,
        evidence_engine: Any = None,
    ) -> None:
        self._knowledge_engine = knowledge_engine
        self._evidence_engine = evidence_engine
        self._decisions: dict[str, Decision] = {}
        # The scientific criteria only. The economic/social criteria are
        # never defaults: they are opted into per decision via
        # economic_criteria_weights() + make_decision(economic_context=...).
        self._default_criteria: list[DecisionCriterion] = _scientific_criteria()
    
    @property
    def knowledge_engine(self) -> Any:
        """Access the Knowledge Engine instance."""
        return self._knowledge_engine
    
    @property
    def evidence_engine(self) -> Any:
        """Access the Evidence Engine instance."""
        return self._evidence_engine
    
    def make_decision(
        self,
        claim_id: str,
        supporting_facts: list[Any] | None = None,
        contradicting_facts: list[Any] | None = None,
        criteria: list[DecisionCriterion] | None = None,
        parameters: dict[str, Any] | None = None,
        economic_context: dict[str, Any] | None = None,
    ) -> Decision:
        """Make a traceable decision about a claim.
        
        Args:
            claim_id: ID of the claim to decide upon.
            supporting_facts: Facts supporting the claim.
            contradicting_facts: Facts contradicting the claim.
            criteria: Decision criteria (defaults to the scientific set).
            parameters: Optional parameters for decision tuning. The optional
                economic/social criteria additionally read ``"npv_base"`` and
                ``"fte_reference"`` from here (both must be positive
                numbers; they default to ``DEFAULT_NPV_BASE`` and
                ``DEFAULT_FTE_REFERENCE``).
            economic_context: Optional economic/social inputs for the
                optional criteria, e.g. ``{"npv_irr": ..., "value_at_risk_irr":
                ..., "direct_employment_fte": ...}``. Each optional criterion
                reads only its own keys (see ``ECONOMIC_CONTEXT_KEYS``) and
                returns ``None`` -- contributing nothing at all, neither to
                the weighted sum nor to its normalisation -- when the context
                is missing, when the criterion's weight is 0, or when a
                required key is absent. Economic criteria are therefore inert
                unless the caller both opts in *and* supplies the data, and a
                decision made without ``economic_context`` matches one made
                before this parameter existed: the only new trace field it
                populates is ``criterion_directions``, a restatement of data
                the criteria already carried.
            
        Returns:
            A Decision with full traceability.
            
        Raises:
            ValueError: ``economic_context`` is not a mapping, holds a
                non-numeric or non-finite value for a key an active criterion
                reads, or ``parameters`` holds a non-positive
                ``npv_base`` / ``fte_reference``.
        """
        supporting_facts = supporting_facts or []
        contradicting_facts = contradicting_facts or []
        criteria = criteria or self._default_criteria
        parameters = parameters or {}
        
        # Get claim evaluation from Knowledge Engine
        claim_status = "INSUFFICIENT_EVIDENCE"
        claim_confidence = 0.0
        
        if self._knowledge_engine is not None:
            try:
                fact_support = [f.id for f in supporting_facts if hasattr(f, 'id')]
                fact_contradict = [f.id for f in contradicting_facts if hasattr(f, 'id')]
                result = self._knowledge_engine.evaluate_claim(
                    claim_id, fact_support, fact_contradict
                )
                if hasattr(result, 'status'):
                    claim_status = result.status.value if hasattr(result.status, 'value') else str(result.status)
                if hasattr(result, 'confidence'):
                    claim_confidence = result.confidence
            except Exception:
                claim_status = "INSUFFICIENT_EVIDENCE"
                claim_confidence = 0.0
        
        # Compute criterion scores
        criterion_scores = self._compute_criterion_scores(
            criteria, supporting_facts, contradicting_facts, claim_confidence,
            economic_context=economic_context, parameters=parameters,
        )
        
        # Aggregate score
        aggregate_score = self._aggregate_score(criteria, criterion_scores)
        
        # Determine outcome
        outcome = self._determine_outcome(
            aggregate_score,
            claim_status,
            claim_confidence,
            criteria,
            criterion_scores=criterion_scores,
        )
        
        # Build trace
        decision_id = f"dec_{uuid4().hex[:12]}"
        evidence_weights = {c.name: c.weight for c in criteria}
        unscored_economic = self._missing_economic_inputs(criteria, economic_context)
        
        trace = DecisionTrace(
            trace_id=f"trace_{uuid4().hex[:12]}",
            decision_id=decision_id,
            claim_id=claim_id,
            fact_ids=[f.id for f in supporting_facts + contradicting_facts if hasattr(f, 'id')],
            evidence_weights=evidence_weights,
            claim_status=claim_status,
            claim_confidence=claim_confidence,
            criterion_scores=criterion_scores,
            aggregate_score=aggregate_score,
            outcome=outcome,
            economic_context=dict(economic_context) if isinstance(economic_context, dict) else None,
            criterion_directions={c.name: c.direction for c in criteria},
        )
        
        # Build rationale
        rationale = self._build_rationale(
            outcome, claim_status, claim_confidence, criterion_scores
        )
        
        # Build recommendations
        recommendations = self._build_recommendations(outcome, aggregate_score)
        
        # Build caveats
        caveats = self._build_caveats(
            claim_status, claim_confidence, unscored_criteria=unscored_economic
        )
        
        decision = Decision(
            decision_id=decision_id,
            claim_id=claim_id,
            outcome=outcome,
            confidence=claim_confidence,
            criteria=criteria,
            trace=trace,
            rationale=rationale,
            recommendations=recommendations,
            caveats=caveats,
            status=DecisionStatus.FINALIZED,
        )
        
        self._decisions[decision_id] = decision
        return decision
    
    def _compute_criterion_scores(
        self,
        criteria: list[DecisionCriterion],
        supporting: list[Any],
        contradicting: list[Any],
        confidence: float,
        economic_context: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, float | None]:
        """Compute normalized score for each criterion.
        
        Scientific criteria always score. The optional economic/social
        criteria (``economic_npv``, ``economic_risk``, ``social_employment``)
        score ``None`` when they carry no weight, when no ``economic_context``
        was supplied, or when a required key is missing -- a criterion without
        data is never scored 0.0 on the caller's behalf.
        """
        scores: dict[str, float | None] = {}
        total_evidence = len(supporting) + len(contradicting)
        parameters = parameters or {}
        
        for criterion in criteria:
            if criterion.name == "evidence_count":
                if total_evidence == 0:
                    score = 0.0
                else:
                    support_ratio = len(supporting) / max(total_evidence, 1)
                    score = support_ratio if criterion.direction == "maximize" else 1 - support_ratio
                scores[criterion.name] = score
                
            elif criterion.name == "evidence_quality":
                # Use average confidence of supporting facts
                if not supporting:
                    score = 0.0
                else:
                    confidences = [f.confidence for f in supporting if hasattr(f, 'confidence')]
                    score = sum(confidences) / len(confidences) if confidences else 0.0
                scores[criterion.name] = score
                
            elif criterion.name == "confidence":
                score = confidence if criterion.direction == "maximize" else 1 - confidence
                scores[criterion.name] = score
                
            elif criterion.name in ECONOMIC_CONTEXT_KEYS:
                scores[criterion.name] = self._economic_score(
                    criterion, economic_context, parameters
                )
                
            else:
                # Unknown criterion - neutral score
                scores[criterion.name] = 0.5

        return scores
    
    def _economic_score(
        self,
        criterion: DecisionCriterion,
        economic_context: dict[str, Any] | None,
        parameters: dict[str, Any],
    ) -> float | None:
        """Score one optional economic/social criterion, or ``None``.
        
        DIRECTION. Every score in the engine means "higher = better", so the
        ``direction`` field is honoured exactly as it is for the scientific
        criteria: the raw quantity is mapped into [0, 1] by the criterion's
        documented formula and then, for a ``"minimize"`` criterion, inverted
        (``1 - raw``) *before* aggregation. ``economic_risk`` is the only
        minimize criterion in the engine and is scored below as
        ``1 - loss_fraction``, so a project with a larger Value at Risk
        always contributes a lower score to the aggregate. The trace records
        every criterion's ``criterion_directions`` next to its score so the
        inversion stays auditable.
        
        RAW SCORES (monotone, saturating, no scientific derivation -- these
        are documented scoring choices):
        
        * ``economic_npv`` (maximize)
          ``s = clip(0.5 + npv_irr / (2 * npv_base), 0, 1)``: a linear ramp
          around zero, antisymmetric about the neutral 0.5 at break-even,
          scoring 0.75 at ``npv_irr = npv_base / 2`` and 0.25 at
          ``npv_irr = -npv_base / 2``, and saturating at 1.0 for
          ``npv_irr >= +npv_base`` and at 0.0 for
          ``npv_irr <= -npv_base``. Saturating on purpose: a project already
          at the reference scale gains nothing by tripling it.
        * ``economic_risk`` (minimize) -- a loss-fraction proxy for Value at
          Risk: ``raw = clip(value_at_risk_irr / (npv_irr +
          value_at_risk_irr + eps), 0, 1)``, i.e. the share of the gross
          exposure that is at risk; the reported score is ``1 - raw``. The
          denominator is floored at 0, so a project whose net exposure is not
          positive can never look safe. No VaR input -> no score.
        * ``social_employment`` (maximize)
          ``s = clip(direct_employment_fte / fte_reference, 0, 1)``: 0 FTE
          scores 0, the reference employment scores 1.0 and beyond. Negative
          headcount (nonsense input) clips to 0.0.
        
        Returns:
            The direction-adjusted score in [0, 1], or ``None`` when the
            criterion is disabled, the context is missing, or a required key
            is absent.
        """
        if criterion.weight <= 0 or economic_context is None:
            return None
        if criterion.name not in ECONOMIC_CONTEXT_KEYS:
            raise ValueError(f"unknown economic criterion {criterion.name!r}")
        
        values = [
            _economic_value(economic_context, key)
            for key in ECONOMIC_CONTEXT_KEYS[criterion.name]
        ]
        
        raw: float | None
        if criterion.name == "economic_npv":
            npv = values[0]
            if npv is None:
                return None
            npv_base = _positive_parameter(parameters.get("npv_base"), "npv_base", DEFAULT_NPV_BASE)
            raw = _clip_unit(0.5 + npv / (2.0 * npv_base))
        elif criterion.name == "economic_risk":
            npv, value_at_risk = values
            if npv is None or value_at_risk is None:
                return None
            exposure = max(npv + value_at_risk, 0.0)
            raw = _clip_unit(value_at_risk / (exposure + ECONOMIC_RISK_EPS))
        else:  # social_employment
            fte = values[0]
            if fte is None:
                return None
            fte_reference = _positive_parameter(
                parameters.get("fte_reference"), "fte_reference", DEFAULT_FTE_REFERENCE
            )
            raw = _clip_unit(fte / fte_reference)
        
        if criterion.direction == "maximize":
            return raw
        return 1.0 - raw
    
    def _missing_economic_inputs(
        self,
        criteria: list[DecisionCriterion],
        economic_context: dict[str, Any] | None,
    ) -> dict[str, str]:
        """Explain why each weighted economic criterion is unscorable.
        
        Only criteria that carry weight and still cannot be scored are
        reported: a caller who explicitly disabled one (weight 0) does not
        need a caveat for a criterion they switched off.
        """
        reasons: dict[str, str] = {}
        for criterion in criteria:
            if criterion.weight <= 0 or criterion.name not in ECONOMIC_CONTEXT_KEYS:
                continue
            keys = ECONOMIC_CONTEXT_KEYS[criterion.name]
            if not isinstance(economic_context, dict):
                reasons[criterion.name] = "no economic_context was supplied"
                continue
            missing = [key for key in keys if _economic_value(economic_context, key) is None]
            if missing:
                reasons[criterion.name] = "economic_context is missing " + ", ".join(
                    repr(key) for key in missing
                )
        return reasons
    
    def _aggregate_score(
        self,
        criteria: list[DecisionCriterion],
        scores: dict[str, float | None],
    ) -> float:
        """Aggregate criterion scores into a weighted score.
        
        Only criteria that actually carry a score take part in the
        normalisation: a disabled criterion (weight 0) or an unscorable one
        (score ``None``) contributes to neither the numerator nor the
        denominator, so it can never deform the aggregate. With the default
        scientific criteria this is exactly the historical weighted mean
        ``sum(w_i s_i) / sum(w_i)``.
        """
        weighted_sum = 0.0
        total_weight = 0.0
        for criterion in criteria:
            if criterion.weight <= 0:
                continue
            score = scores.get(criterion.name)
            if score is None:
                continue
            weighted_sum += criterion.weight * score
            total_weight += criterion.weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _determine_outcome(
        self,
        score: float,
        claim_status: str,
        confidence: float,
        criteria: list[DecisionCriterion],
        criterion_scores: dict | None = None,
    ) -> str:
        """Determine the decision outcome from scores.

        Verdict bands (unchanged):

        * ``confidence < 0.2``                  -> INSUFFICIENT_EVIDENCE
        * aggregate ``score >= 0.7``            -> RECOMMEND
        * aggregate ``score >= 0.4``            -> CAUTION
        * otherwise                             -> REJECT

        Threshold gate (implemented): every criterion's ``threshold`` is now
        actually evaluated against its OWN score (previously this loop forced
        ``threshold_met = threshold_met and True`` so ``DecisionCriterion.threshold``
        was dead). If any *weighted* criterion (``weight > 0``) scores below its
        threshold, the aggregate is no longer allowed to reach RECOMMEND -- the
        outcome is capped at CAUTION. It never lowers a verdict that the
        aggregate band already places below CAUTION. An unscorable criterion
        (score ``None`` -- an economic criterion with no matching
        ``economic_context``) gates nothing: it has no score to compare.
        """
        if confidence < 0.2:
            return DecisionOutcome.INSUFFICIENT_EVIDENCE.value

        if score >= 0.7:
            outcome = DecisionOutcome.RECOMMEND.value
        elif score >= 0.4:
            outcome = DecisionOutcome.CAUTION.value
        else:
            outcome = DecisionOutcome.REJECT.value

        # Threshold gate: a weighted criterion below its own threshold blocks a
        # RECOMMEND (the strongest claim) even when the weighted aggregate is
        # high -- e.g. strong-but-low-quality evidence must not be RECOMMEND.
        if outcome == DecisionOutcome.RECOMMEND.value:
            scores = criterion_scores or {}
            for criterion in criteria:
                if criterion.weight > 0 and criterion.name in scores:
                    own = scores[criterion.name]
                    if own is not None and own < criterion.threshold:
                        return DecisionOutcome.CAUTION.value
        return outcome
    
    def _build_rationale(
        self,
        outcome: str,
        claim_status: str,
        confidence: float,
        scores: dict[str, float | None],
    ) -> str:
        """Build human-readable decision rationale."""
        parts = [
            f"Decision outcome: {outcome}.",
            f"Claim status: {claim_status}.",
            f"Confidence: {confidence:.2f}.",
        ]
        for name, score in scores.items():
            if score is None:
                parts.append(f"Criterion '{name}' was not scored (no economic context).")
            else:
                parts.append(f"Criterion '{name}' score: {score:.2f}.")
        return " ".join(parts)
    
    def _build_recommendations(self, outcome: str, score: float) -> list[str]:
        """Build actionable recommendations based on outcome."""
        if outcome == DecisionOutcome.RECOMMEND.value:
            return [
                f"Proceed with recommended action (confidence score: {score:.2f}).",
                "Monitor key indicators for validation."
            ]
        elif outcome == DecisionOutcome.CAUTION.value:
            return [
                f"Proceed with caution (confidence score: {score:.2f}).",
                "Consider additional evidence before final decision."
            ]
        else:
            return [
                "Do not proceed with recommended action.",
                "Gather additional evidence or revise criteria."
            ]
    
    def _build_caveats(
        self,
        claim_status: str,
        confidence: float,
        unscored_criteria: dict[str, str] | None = None,
    ) -> list[str]:
        """Build scientific caveats for the decision."""
        caveats = []

        # The claim status arrives as the enum's *value* ("insufficient_evidence",
        # lowercase from ClaimStatus); comparing against the member NAME never
        # matched, so this caveat -- the honesty headline for a decision made on
        # no evidence -- was silently dropped (S23 defect D-T03).
        if str(claim_status).lower() == "insufficient_evidence":
            caveats.append("Decision based on insufficient evidence.")
        
        if confidence < 0.5:
            caveats.append(
                f"Low confidence ({confidence:.2f}) — decision should be reviewed "
                "with additional evidence."
            )
        
        if self._knowledge_engine is None:
            caveats.append("Decision Engine operating without Knowledge Engine integration.")
        
        if self._evidence_engine is None:
            caveats.append("Evidence Engine not connected — provenance tracking unavailable.")
        
        # Honesty for the optional economic/social criteria: a criterion the
        # caller switched on (weight > 0) but could not score must be declared,
        # never silently replaced by a neutral 0.5.
        for name, reason in (unscored_criteria or {}).items():
            caveats.append(f"Criterion '{name}' not scored: {reason}.")
        
        return caveats
    
    def get_decision(self, decision_id: str) -> Decision | None:
        """Retrieve a decision by ID."""
        return self._decisions.get(decision_id)
    
    def all_decisions(self) -> list[Decision]:
        """Get all decisions."""
        return list(self._decisions.values())


# Convenience function
def create_decision_engine(
    knowledge_engine: Any = None,
    evidence_engine: Any = None,
) -> DecisionEngine:
    """Create a DecisionEngine with optional injected dependencies."""
    return DecisionEngine(
        knowledge_engine=knowledge_engine,
        evidence_engine=evidence_engine,
    )