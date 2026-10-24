"""Evidence Engine: evidence collection, validation, and provenance tracking.

The Evidence Engine collects evidence from various sources (measurements,
models, literature, expert judgment) and provides validation capabilities.
It produces Evidence objects that feed the Knowledge Engine.

Architecture (ECO-04 §4):
    - EvidenceEngine: orchestrates evidence collection and validation
    - Evidence: a single piece of evidence with provenance
    - EvidenceSource: where evidence comes from (measurement, model, etc.)
    - EvidenceType: how evidence is represented (quantitative, qualitative)

Design principle: The Evidence Engine never imports `database`. Storage
and retrieval of evidence records goes through PersistencePort.

This module integrates with the Engine Gateway (ECO-04.2) so evidence
can be registered through the Gateway API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import uuid4

__all__ = [
    "EvidenceSource",
    "EvidenceType",
    "Evidence",
    "ValidationResult",
    "EvidenceEngine",
]


class EvidenceSource(StrEnum):
    """Origin of an evidence item."""

    MEASUREMENT = "measurement"
    MODEL = "model"
    LITERATURE = "literature"
    EXPERT = "expert"
    SIMULATION = "simulation"
    FIELD_OBSERVATION = "field_observation"


class EvidenceType(StrEnum):
    """Representation type of evidence."""

    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    CITATION = "citation"


@dataclass
class Evidence:
    """A single piece of evidence with full provenance.

    Attributes:
        id: Unique identifier for the evidence item.
        source: Where the evidence came from.
        evidence_type: How the evidence is represented.
        value: The evidence content (number, string, or dict).
        confidence: Trustworthiness of the evidence in [0, 1].
        timestamp: When the evidence was collected or asserted.
        provenance: Chain of custody / origin metadata.
        metadata: Additional context.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    source: EvidenceSource = EvidenceSource.MEASUREMENT
    evidence_type: EvidenceType = EvidenceType.QUANTITATIVE
    value: float | str | int | dict[str, Any] = 0.0
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    provenance: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of this evidence item."""
        return {
            "id": self.id,
            "source": self.source.value,
            "evidence_type": self.evidence_type.value,
            "value": _jsonable(self.value),
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "provenance": list(self.provenance),
            "metadata": _jsonable(self.metadata),
        }


@dataclass
class ValidationResult:
    """Result of validating an Evidence item.

    Attributes:
        evidence_id: ID of the validated evidence.
        is_valid: Whether the evidence passed validation.
        issues: List of validation issue descriptions.
        validated_at: When validation was performed.
    """

    evidence_id: str
    is_valid: bool
    issues: list[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


class EvidenceEngine:
    """Evidence collection, validation, and provenance engine.

    The engine is purely computational — it holds Evidence items in memory
    and provides validation capabilities. Persistence is delegated to
    PersistencePort via Gateway injection.

    Integration with the KnowledgeEngine is optional: when a
    ``knowledge_engine`` is available (via constructor or per-call argument)
    :meth:`to_fact` asserts the generated Fact directly via
    ``KnowledgeEngine.assert_fact()``.
    """

    def __init__(self, knowledge_engine: Any = None) -> None:
        self._evidence: dict[str, Evidence] = {}
        self._validations: dict[str, ValidationResult] = {}
        # evidence_id -> [fact_id]  (evidence -> derived knowledge)
        self._fact_links: dict[str, list[str]] = {}
        # evidence_id -> [decision_id]  (evidence -> downstream decision)
        self._decision_links: dict[str, list[str]] = {}
        # Self-contained caches so export_chain needs no external engine
        self._facts: dict[str, Any] = {}
        self._decisions: dict[str, dict[str, Any]] = {}
        self._knowledge_engine = knowledge_engine

    def collect(self, evidence: Evidence) -> Evidence:
        """Collect an Evidence item into the evidence store.

        Args:
            evidence: The Evidence item to collect.

        Returns:
            The same Evidence item (with generated ID if needed).
        """
        self._evidence[evidence.id] = evidence
        return evidence

    def get(self, evidence_id: str) -> Evidence | None:
        """Retrieve an Evidence item by ID."""
        return self._evidence.get(evidence_id)

    def all(self) -> list[Evidence]:
        """Return all collected Evidence items."""
        return list(self._evidence.values())

    def validate(self, evidence_id: str) -> ValidationResult:
        """Validate an Evidence item against basic quality rules.

        This skeleton implementation checks:
        1. Confidence is in [0, 1]
        2. Value is present (not None for quantitative evidence)
        3. Provenance chain is non-empty for expert evidence

        Args:
            evidence_id: ID of the evidence to validate.

        Returns:
            ValidationResult with validity and any issues found.
        """
        evidence = self._evidence.get(evidence_id)
        if evidence is None:
            result = ValidationResult(
                evidence_id=evidence_id,
                is_valid=False,
                issues=["Evidence not found"],
            )
            self._validations[evidence_id] = result
            return result

        issues: list[str] = []

        if not 0.0 <= evidence.confidence <= 1.0:
            issues.append(
                f"Confidence {evidence.confidence} out of [0, 1] range"
            )

        if (
            evidence.evidence_type == EvidenceType.QUANTITATIVE
            and evidence.value is None
        ):
            issues.append("Quantitative evidence has no value")

        if (
            evidence.source == EvidenceSource.EXPERT
            and not evidence.provenance
        ):
            issues.append("Expert evidence requires provenance chain")

        result = ValidationResult(
            evidence_id=evidence_id,
            is_valid=len(issues) == 0,
            issues=issues,
        )
        self._validations[evidence_id] = result
        return result

    def get_validation(self, evidence_id: str) -> ValidationResult | None:
        """Retrieve the ValidationResult for an evidence item."""
        return self._validations.get(evidence_id)

    def to_fact(
        self,
        evidence_id: str,
        statement: str,
        source_id: str | None = None,
        knowledge_engine: Any = None,
    ) -> Any:
        """Convert an Evidence item to a Knowledge Engine Fact.

        Uses dynamic import to avoid circular dependency between
        evidence and knowledge engines.

        Args:
            evidence_id: ID of the evidence to convert.
            statement: The fact statement to create.
            source_id: Optional override for the fact's source_id.
            knowledge_engine: Optional KnowledgeEngine. When provided
                (or when the EvidenceEngine was constructed with one)
                the Fact is asserted via ``KnowledgeEngine.assert_fact()``
                so that provenance is recorded in the knowledge base.

        Returns:
            A Fact object from engine.knowledge.
        """
        from engine.knowledge import Fact

        evidence = self._evidence.get(evidence_id)
        if evidence is None:
            raise KeyError(f"Evidence not found: {evidence_id}")

        fact = Fact(
            id=f"fact_{evidence_id}",
            statement=statement,
            source_id=source_id or evidence.source.value,
            confidence=evidence.confidence,
            provenance_chain=list(evidence.provenance),
            metadata={
                **evidence.metadata,
                "evidence_id": evidence_id,
                "evidence_type": evidence.evidence_type.value,
                "provenance": evidence.provenance,
            },
        )

        engine = knowledge_engine or self._knowledge_engine
        if engine is not None:
            engine.assert_fact(fact)

        # Record the Evidence -> Fact derivation link so the provenance chain
        # is traceable in both directions.
        self._facts[fact.id] = fact
        self._fact_links.setdefault(evidence.id, []).append(fact.id)

        return fact

    # ------------------------------------------------------------------
    # Provenance chain
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_evidence_id(ref: str) -> str:
        """Resolve a provenance/fact reference to a bare Evidence id.

        Handles fact IDs (``fact_<evidence_id>``) and plain evidence IDs.
        Any other reference is returned unchanged and treated as an external
        (non-evidence) marker that need not resolve.
        """
        if ref.startswith("fact_"):
            return ref[len("fact_"):]
        return ref

    def trace(self, fact_id: str) -> list[Evidence]:
        """Retrieve the provenance chain ending at the evidence for *fact_id*.

        Resolves *fact_id* to its originating Evidence item (stripping a
        ``fact_`` prefix when present), then walks every entry in each item's
        ``provenance`` list — which may itself hold evidence IDs or fact IDs —
        collecting the full ancestry of Evidence objects.

        Args:
            fact_id: A Fact id (``fact_<evidence_id>``) or an Evidence id.

        Returns:
            Ordered list of Evidence objects, root (the evidence that the
            fact was derived from) first, followed by each ancestor. Returns
            an empty list if the starting id is unknown.
        """
        start = self._resolve_evidence_id(fact_id)
        root = self._evidence.get(start) if start in self._evidence else self._evidence.get(fact_id)
        if root is None:
            return []

        chain: list[Evidence] = []
        seen: set[str] = set()

        def _walk(eid: str) -> None:
            evidence = self._evidence.get(eid)
            if evidence is None:
                return
            if evidence.id in seen:
                return
            seen.add(evidence.id)
            chain.append(evidence)
            for ref in evidence.provenance:
                _walk(self._resolve_evidence_id(ref))

        _walk(root.id)
        return chain

    def export_chain(self, evidence_id: str) -> dict[str, Any]:
        """Produce a full traceability export for the chain of *evidence_id*.

        The export is JSON-serializable and self-contained: it resolves the
        Evidence -> Fact -> Decision derivation graph in both directions so an
        external system can verify end-to-end provenance without querying the
        Knowledge or Decision engines directly.

        Args:
            evidence_id: ID of the Evidence item to export.

        Returns:
            A dict with keys ``evidence_id``, ``trace_id``, ``chain``
            (each ancestor Evidence with its validation result),
            ``derived_facts``, ``derived_decisions`` and ``integrity``.

        Raises:
            KeyError: if *evidence_id* cannot be resolved.
        """
        evidence = self._evidence.get(evidence_id)
        if evidence is None:
            evidence = self._evidence.get(self._resolve_evidence_id(evidence_id))
        if evidence is None:
            raise KeyError(f"Evidence not found: {evidence_id}")

        chain = self.trace(evidence.id)
        serialized_chain: list[dict[str, Any]] = []
        for item in chain:
            validation = self._validations.get(item.id)
            serialized_chain.append({
                "id": item.id,
                "source": item.source.value,
                "evidence_type": item.evidence_type.value,
                "value": _jsonable(item.value),
                "confidence": item.confidence,
                "timestamp": item.timestamp.isoformat(),
                "provenance": list(item.provenance),
                "metadata": _jsonable(item.metadata),
                "validation": _validation_to_dict(validation),
            })

        derived_facts = [
            {
                "fact_id": f.id,
                "statement": f.statement,
                "source_id": f.source_id,
                "confidence": f.confidence,
                "timestamp": f.timestamp.isoformat() if hasattr(f, "timestamp") else None,
                "provenance_chain": list(
                    getattr(f, "provenance_chain", []) or f.metadata.get("provenance", [])
                ),
                "metadata": _jsonable(f.metadata),
            }
            for f in (self._facts.get(fid) for fid in self._fact_links.get(evidence.id, []))
            if f is not None
        ]

        derived_decisions = [
            self._decisions[did] for did in self._decision_links.get(evidence.id, [])
            if did in self._decisions
        ]

        return {
            "evidence_id": evidence.id,
            "trace_id": evidence.metadata.get("trace_id"),
            "chain": serialized_chain,
            "derived_facts": derived_facts,
            "derived_decisions": derived_decisions,
            "integrity": self.validate_chain_integrity(),
        }

    def validate_chain_integrity(self) -> bool:
        """Verify that every provenance link resolves to a known Evidence item.

        A link is valid when, after resolving ``fact_<id>`` prefixes, it
        matches an Evidence id that has been collected. Links that do not
        resolve are dangling references and cause this to return ``False``.
        """
        for evidence in self._evidence.values():
            for ref in evidence.provenance:
                resolved = self._resolve_evidence_id(ref)
                if resolved not in self._evidence:
                    return False
        return True

    def register_decision(self, decision: Any, fact_id: str) -> None:
        """Record that a Decision was derived from the Evidence behind *fact_id*.

        Resolves *fact_id* to its originating Evidence id and stores the
        decision snapshot so :meth:`export_chain` can include downstream
        decisions in the provenance graph.
        """
        evidence_id = self._resolve_evidence_id(fact_id)
        if evidence_id not in self._evidence:
            return
        decision_id = getattr(decision, "decision_id", None) or getattr(decision, "id", None)
        if not decision_id:
            return
        trace = getattr(decision, "trace", None)
        snapshot: dict[str, Any] = {
            "decision_id": decision_id,
            "claim_id": getattr(decision, "claim_id", None),
            "outcome": str(getattr(decision, "outcome", "")),
            "confidence": float(getattr(decision, "confidence", 0.0)),
            "trace_id": getattr(trace, "trace_id", None) if trace is not None else None,
            "fact_ids": list(getattr(trace, "fact_ids", [])) if trace is not None else [],
        }
        self._decisions[decision_id] = snapshot
        self._decision_links.setdefault(evidence_id, []).append(decision_id)


# ---------------------------------------------------------------------------
# Module-level serialization helpers
# ---------------------------------------------------------------------------


def _jsonable(value: Any) -> Any:
    """Return a JSON-serializable form of *value*.

    ``datetime`` objects are converted to ISO-8601 strings; dataclasses and
    objects with ``__dict__`` are mapped recursively; everything else is
    returned unchanged (numbers, strings, lists, dicts of the above).
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    # dataclass instances
    if hasattr(value, "__dataclass_fields__"):
        return {k: _jsonable(getattr(value, k)) for k in value.__dataclass_fields__}
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    return value


def _validation_to_dict(validation: ValidationResult | None) -> dict[str, Any] | None:
    if validation is None:
        return None
    return {
        "evidence_id": validation.evidence_id,
        "is_valid": validation.is_valid,
        "issues": list(validation.issues),
        "validated_at": validation.validated_at.isoformat()
        if isinstance(validation.validated_at, datetime)
        else validation.validated_at,
    }
