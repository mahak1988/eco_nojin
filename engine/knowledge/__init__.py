"""Knowledge Engine: structured knowledge representation and retrieval.

The Knowledge Engine represents scientific facts, claims, and their
justification in a form the Decision Engine can reason over. It does not
perform storage (that's handled by PersistencePort) — it defines the
knowledge model and provides query/inference capabilities.

Architecture (ECO-04 §5):
    - KnowledgeEngine: orchestrates fact registration and claim evaluation
    - Fact: an atomic, sourced piece of knowledge
    - Rule: a forward-chaining inference rule linking premises to a conclusion
    - Claim: a proposition whose support is being evaluated
    - KnowledgeGraph: stores facts and claims with dependency edges

Design principle: The Knowledge Engine never imports `database`. All
persistence is via PersistencePort injection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any


class ClaimStatus(StrEnum):
    """Evaluation status of a Claim against known Facts."""

    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass
class Fact:
    """An atomic, sourced piece of knowledge.

    Attributes:
        id: Stable identifier for the fact.
        statement: Human-readable description of what is known.
        source_id: Identifier of the evidence source.
        confidence: Calibration confidence in [0, 1].
        timestamp: When the fact was asserted.
        provenance_chain: Ordered chain of fact_ids / source_ids that
            justify this fact. Empty for directly-asserted facts.
        metadata: Arbitrary additional context (strain codes, parameters).
    """

    id: str
    statement: str
    source_id: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    provenance_chain: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")


@dataclass
class Rule:
    """A forward-chaining inference rule.

    A rule fires when every entry in *premise* is matched by an existing
    Fact — either by exact fact-ID match or by case-insensitive substring
    match against a Fact's ``statement``. When the rule fires a new derived
    Fact is created whose ``statement`` is *conclusion* and whose
    ``provenance_chain`` records the premise fact IDs and the rule ID.

    Attributes:
        id: Stable identifier for the rule.
        premise: List of patterns (statement substrings) or fact IDs that
            must all be present for the rule to fire.
        conclusion: The statement of the Fact derived when the rule fires.
        confidence_boost: Multiplicative boost applied to the minimum
            premise confidence. Clamped so the result stays in [0, 1].
        metadata: Arbitrary additional context (rule author, references).
    """

    id: str
    premise: list[str]
    conclusion: str
    confidence_boost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    """A proposition whose support is being evaluated against Facts.

    Attributes:
        id: Stable identifier for the claim.
        text: The proposition text.
        status: Current evaluation status.
        supporting_facts: IDs of facts that support this claim.
        contradicting_facts: IDs of facts that contradict this claim.
        confidence: Aggregated confidence after evaluation.
        metadata: Additional context.
    """

    id: str
    text: str
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    supporting_facts: list[str] = field(default_factory=list)
    contradicting_facts: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeEngine:
    """In-memory knowledge representation engine.

    The engine holds Facts, Rules, and Claims in memory and provides query
    and forward-chaining inference capabilities. Persistence is delegated
    to a PersistencePort that can be injected via the Gateway.

    The engine maintains a provenance graph: every Fact carries a
    ``provenance_chain`` listing the fact IDs (and ultimately source IDs)
    that led to it, enabling full traceability from derived knowledge back
    to original evidence.
    """

    def __init__(self) -> None:
        self._facts: dict[str, Fact] = {}
        self._claims: dict[str, Claim] = {}
        self._rules: dict[str, Rule] = {}
        self._derived_counter: int = 0

    # ------------------------------------------------------------------
    # Fact management
    # ------------------------------------------------------------------

    def assert_fact(self, fact: Fact) -> None:
        """Assert a Fact into the knowledge base.

        Ensures the fact's ``provenance_chain`` is populated: if empty,
        it is seeded with the fact's ``source_id`` so that every fact
        has a traceable origin.
        """
        if not fact.provenance_chain:
            fact.provenance_chain = [fact.source_id]
        self._facts[fact.id] = fact

    def register_fact(self, fact: Fact) -> None:
        """Register a Fact in the knowledge base (backward-compatible alias).

        Delegates to :meth:`assert_fact` so provenance is normalised
        consistently regardless of the entry point.
        """
        self.assert_fact(fact)

    def add_rule(self, rule: Rule) -> None:
        """Register an inference :class:`Rule` with the knowledge base."""
        self._rules[rule.id] = rule

    def register_claim(self, claim: Claim) -> None:
        """Register a Claim in the knowledge base."""
        self._claims[claim.id] = claim

    def get_fact(self, fact_id: str) -> Fact | None:
        """Retrieve a Fact by ID."""
        return self._facts.get(fact_id)

    def get_claim(self, claim_id: str) -> Claim | None:
        """Retrieve a Claim by ID."""
        return self._claims.get(claim_id)

    def get_rule(self, rule_id: str) -> Rule | None:
        """Retrieve a Rule by ID."""
        return self._rules.get(rule_id)

    def all_facts(self) -> list[Fact]:
        """Return all registered Facts."""
        return list(self._facts.values())

    def all_claims(self) -> list[Claim]:
        """Return all registered Claims."""
        return list(self._claims.values())

    def all_rules(self) -> list[Rule]:
        """Return all registered Rules."""
        return list(self._rules.values())

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query_by_source(self, source_id: str) -> list[Fact]:
        """Return all Facts whose ``source_id`` matches.

        Args:
            source_id: The identifier of the evidence source.
        """
        return [f for f in self._facts.values() if f.source_id == source_id]

    def query_by_statement(self, pattern: str) -> list[Fact]:
        """Return all Facts whose ``statement`` contains *pattern*.

        The match is case-insensitive substring matching, supporting
        partial and fuzzy lookups against the knowledge base.

        Args:
            pattern: Substring (or regex when *regex* is used) to search
                for in fact statements.
        """
        if not pattern:
            return []
        regex = re.compile(re.escape(pattern), re.IGNORECASE)
        return [f for f in self._facts.values() if regex.search(f.statement)]

    # ------------------------------------------------------------------
    # Forward-chaining inference
    # ------------------------------------------------------------------

    def _match_premise(self, entry: str) -> list[Fact]:
        """Find all facts matching a single premise entry.

        A premise entry matches a fact if it equals the fact's ID exactly
        or if it appears (case-insensitive) as a substring of the fact's
        statement.
        """
        matched: list[Fact] = []
        for fact in self._facts.values():
            if fact.id == entry:
                matched.append(fact)
            elif entry.lower() in fact.statement.lower():
                matched.append(fact)
        return matched

    def _rule_fires(self, rule: Rule) -> list[Fact] | None:
        """Return matching premise facts if *rule* fires, else ``None``.

        A rule fires when every premise entry matches at least one fact.
        Returns the list of *first-matching* premise facts (one per entry)
        so the caller can build the derived fact's provenance chain.
        """
        matches: list[Fact] = []
        for entry in rule.premise:
            candidates = self._match_premise(entry)
            if not candidates:
                return None
            matches.append(candidates[0])
        return matches

    def derive(self) -> list[Fact]:
        """Run forward-chaining inference to a fixpoint.

        Repeatedly evaluates every registered rule against the current
        set of Facts. When all premises of a rule are satisfied a new
        derived Fact is asserted. The process repeats until no new Facts
        can be derived (fixpoint reached).

        Returns:
            The list of Facts that were newly derived in this run (across
            all fixpoint iterations).
        """
        derived_all: list[Fact] = []
        while True:
            newly_derived: list[Fact] = []
            for rule in self._rules.values():
                if rule.conclusion in (f.statement for f in self._facts.values()):
                    continue
                matches = self._rule_fires(rule)
                if matches is None:
                    continue
                min_confidence = min(f.confidence for f in matches) if matches else 0.0
                derived_confidence = min_confidence * (1.0 + rule.confidence_boost)
                derived_confidence = max(0.0, min(1.0, derived_confidence))
                self._derived_counter += 1
                derived_fact = Fact(
                    id=f"derived_{rule.id}_{self._derived_counter}",
                    statement=rule.conclusion,
                    source_id=f"rule:{rule.id}",
                    confidence=derived_confidence,
                    provenance_chain=[f.id for f in matches] + [rule.id],
                    metadata={
                        **rule.metadata,
                        "rule_id": rule.id,
                        "derived": True,
                    },
                )
                derived_fact.provenance_chain = [f.id for f in matches] + [rule.id]
                self._facts[derived_fact.id] = derived_fact
                newly_derived.append(derived_fact)

            if not newly_derived:
                break
            derived_all.extend(newly_derived)
        return derived_all

    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------

    def get_provenance_chain(self, fact_id: str) -> list[str]:
        """Return the provenance chain for a Fact.

        For asserted facts this is ``[source_id]``. For derived facts this
        is the list of premise fact IDs followed by the rule ID that
        produced the fact. Returns an empty list if the fact ID is unknown.
        """
        fact = self._facts.get(fact_id)
        if fact is None:
            return []
        if fact.provenance_chain:
            return list(fact.provenance_chain)
        return [fact.source_id]

    def resolve_provenance(self, fact_id: str) -> list[Fact]:
        """Resolve a fact's provenance chain into the actual Fact objects.

        Walks the provenance chain recursively, returning every ancestor
        fact that contributed to *fact_id*.
        """
        resolved: list[Fact] = []
        seen: set[str] = set()

        def _walk(fid: str) -> None:
            if fid in seen:
                return
            fact = self._facts.get(fid)
            if fact is None:
                return
            seen.add(fid)
            for ancestor_id in fact.provenance_chain:
                _walk(ancestor_id)
            if fid not in resolved_ids:
                resolved.append(fact)

        resolved_ids: set[str] = set()
        _walk(fact_id)
        return resolved

    # ------------------------------------------------------------------
    # Claim evaluation
    # ------------------------------------------------------------------

    def evaluate_claim(
        self,
        claim_id: str,
        fact_ids: list[str],
        contradict_ids: list[str],
    ) -> Claim:
        """Evaluate a Claim against supporting/contradicting Facts.

        Args:
            claim_id: ID of the claim to evaluate.
            fact_ids: IDs of facts supporting the claim.
            contradict_ids: IDs of facts contradicting the claim.

        Returns:
            Updated Claim with status and aggregated confidence.
        """
        claim = self._claims.get(claim_id)
        if claim is None:
            raise KeyError(f"Claim not found: {claim_id}")

        # Indexing rather than .get: the membership guard above makes the key
        # present, so each element is a Fact rather than a Fact | None.
        supporting = [self._facts[fid] for fid in fact_ids if fid in self._facts]
        contradicting = [
            self._facts[fid] for fid in contradict_ids if fid in self._facts
        ]

        if contradicting:
            claim.status = ClaimStatus.CONTRADICTED
            claim.confidence = _aggregate_confidence(contradicting)
        elif supporting:
            claim.status = ClaimStatus.SUPPORTED
            claim.confidence = _aggregate_confidence(supporting)
        else:
            claim.status = ClaimStatus.INSUFFICIENT_EVIDENCE

        claim.supporting_facts = fact_ids
        claim.contradicting_facts = contradict_ids
        return claim


def _aggregate_confidence(facts: list[Fact]) -> float:
    """Aggregate confidence from a list of facts using a simple mean."""
    if not facts:
        return 0.0
    return sum(f.confidence for f in facts) / len(facts)


__all__ = [
    "Claim",
    "ClaimStatus",
    "Fact",
    "KnowledgeEngine",
    "Rule",
    "_aggregate_confidence",
]
