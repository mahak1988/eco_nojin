"""Concrete PersistencePort implementations for domain objects.

Provides two in-process adapters that fulfil the PersistencePort contract
for Evidence, Fact, and Decision objects:

* :class:`InMemoryPersistence` — dict-based, transient, for testing.
* :class:`FileBackedPersistence` — JSON-file backed, durable.

Both implement the *domain* persistence methods (save/load/list). The
database-connection methods (``get_duckdb``, ``get_sqlite``, …) are not
meaningful for these adapters and raise ``NotImplementedError``.

Type hints use lazy imports inside functions to avoid circular
dependencies between ``engine.ports`` and the domain modules
(``engine.evidence``, ``engine.knowledge``, ``engine.tasmimyar``).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

__all__ = [
    "InMemoryPersistence",
    "FileBackedPersistence",
]


# ── In-memory adapter ──────────────────────────────────────────────────────


class InMemoryPersistence:
    """In-memory PersistencePort implementation for domain objects.

    Stores Evidence, Fact, and Decision items in dicts keyed by their
    primary ID. Suitable for testing and local/ephemeral operation.
    """

    _DB_MSG = (
        "InMemoryPersistence does not provide database connections. "
        "Use a database-backed PersistencePort for SQL/DuckDB access."
    )

    def __init__(self) -> None:
        self._evidence: dict[str, Any] = {}
        self._facts: dict[str, Any] = {}
        self._decisions: dict[str, Any] = {}

    # ── Evidence ──────────────────────────────

    def save_evidence(self, evidence: Any) -> str:
        """Persist an Evidence item in memory. Returns its ``id``."""
        self._evidence[evidence.id] = evidence
        evidence_id: str = evidence.id
        return evidence_id

    def load_evidence(self, evidence_id: str) -> Any | None:
        """Retrieve an Evidence item by ID, or ``None`` if not stored."""
        return self._evidence.get(evidence_id)

    # ── Fact ──────────────────────────────

    def save_fact(self, fact: Any) -> str:
        """Persist a Fact in memory. Returns its ``id``."""
        self._facts[fact.id] = fact
        fact_id: str = fact.id
        return fact_id

    def load_fact(self, fact_id: str) -> Any | None:
        """Retrieve a Fact by ID, or ``None`` if not stored."""
        return self._facts.get(fact_id)

    # ── Decision ──────────────────────────────

    def save_decision(self, decision: Any) -> str:
        """Persist a Decision in memory. Returns its ``decision_id``."""
        self._decisions[decision.decision_id] = decision
        decision_id: str = decision.decision_id
        return decision_id

    def load_decision(self, decision_id: str) -> Any | None:
        """Retrieve a Decision by ID, or ``None`` if not stored."""
        return self._decisions.get(decision_id)

    # ── Evidence listing ──────────────────────────────

    def list_evidence(self, filters: dict) -> list[Any]:
        """List Evidence items whose metadata matches all *filters*.

        Each ``key, value`` pair in *filters* is matched against
        ``evidence.metadata[key]`` using equality.
        """
        results: list[Any] = []
        for evidence in self._evidence.values():
            if _matches_filters(evidence.metadata, filters):
                results.append(evidence)
        return results

    # ── Database connection methods (not supported) ─────────────────────────

    def get_duckdb(self, name: str) -> Any:
        raise NotImplementedError(self._DB_MSG)

    def get_sqlite(self, name: str) -> Any:
        raise NotImplementedError(self._DB_MSG)

    def get_duckdb_pooled(self, database: str) -> Any:
        raise NotImplementedError(self._DB_MSG)

    def return_duckdb_pooled(self, conn: Any, database: str) -> None:
        raise NotImplementedError(self._DB_MSG)


# ── File-backed adapter ────────────────────────────────────────────────────


class FileBackedPersistence:
    """JSON-file-backed PersistencePort implementation for domain objects.

    All domain objects are stored in a single JSON document (default
    ``persistence.json``) organised by type. Each save rewrites the file;
    each load deserialises the relevant entry back into the original
    domain object type.

    Args:
        path: Path to the JSON store file. Created on first save if it
            does not exist.
    """

    _DB_MSG = (
        "FileBackedPersistence does not provide database connections. "
        "Use a database-backed PersistencePort for SQL/DuckDB access."
    )

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else Path("persistence.json")

    # ── Internal storage helpers ──────────────────────

    def _load_store(self) -> dict[str, list[dict]]:
        """Read the JSON store, returning the three collection lists."""
        if not self._path.exists():
            return {"evidence": [], "facts": [], "decisions": []}
        try:
            with open(self._path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, ValueError):
            return {"evidence": [], "facts": [], "decisions": []}
        return {
            "evidence": data.get("evidence", []),
            "facts": data.get("facts", []),
            "decisions": data.get("decisions", []),
        }

    def _save_store(self, store: dict[str, list[dict]]) -> None:
        """Atomically write the store to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(store, fh, indent=2, default=_json_default)
        tmp.replace(self._path)

    # ── Evidence ──────────────────────────────

    def save_evidence(self, evidence: Any) -> str:
        """Persist an Evidence item to JSON. Returns its ``id``."""
        store = self._load_store()
        serialized = _serialize_evidence(evidence)
        store["evidence"] = [
            e for e in store["evidence"] if e.get("id") != evidence.id
        ]
        store["evidence"].append(serialized)
        self._save_store(store)
        evidence_id: str = evidence.id
        return evidence_id

    def load_evidence(self, evidence_id: str) -> Any | None:
        """Load and deserialise an Evidence item by ID."""
        store = self._load_store()
        for raw in store["evidence"]:
            if raw.get("id") == evidence_id:
                return _deserialize_evidence(raw)
        return None

    # ── Fact ──────────────────────────────

    def save_fact(self, fact: Any) -> str:
        """Persist a Fact to JSON. Returns its ``id``."""
        store = self._load_store()
        serialized = _serialize_fact(fact)
        store["facts"] = [f for f in store["facts"] if f.get("id") != fact.id]
        store["facts"].append(serialized)
        self._save_store(store)
        fact_id: str = fact.id
        return fact_id

    def load_fact(self, fact_id: str) -> Any | None:
        """Load and deserialise a Fact by ID."""
        store = self._load_store()
        for raw in store["facts"]:
            if raw.get("id") == fact_id:
                return _deserialize_fact(raw)
        return None

    # ── Decision ──────────────────────────────

    def save_decision(self, decision: Any) -> str:
        """Persist a Decision to JSON. Returns its ``decision_id``."""
        store = self._load_store()
        serialized = _serialize_decision(decision)
        store["decisions"] = [
            d for d in store["decisions"] if d.get("decision_id") != decision.decision_id
        ]
        store["decisions"].append(serialized)
        self._save_store(store)
        decision_id: str = decision.decision_id
        return decision_id

    def load_decision(self, decision_id: str) -> Any | None:
        """Load and deserialise a Decision by ID."""
        store = self._load_store()
        for raw in store["decisions"]:
            if raw.get("decision_id") == decision_id:
                return _deserialize_decision(raw)
        return None

    # ── Evidence listing ──────────────────────────────

    def list_evidence(self, filters: dict) -> list[Any]:
        """List Evidence items whose metadata matches all *filters*."""
        store = self._load_store()
        results: list[Any] = []
        for raw in store["evidence"]:
            if _matches_filters(raw.get("metadata", {}), filters):
                results.append(_deserialize_evidence(raw))
        return results

    # ── Database connection methods (not supported) ─────────────────────────

    def get_duckdb(self, name: str) -> Any:
        raise NotImplementedError(self._DB_MSG)

    def get_sqlite(self, name: str) -> Any:
        raise NotImplementedError(self._DB_MSG)

    def get_duckdb_pooled(self, database: str) -> Any:
        raise NotImplementedError(self._DB_MSG)

    def return_duckdb_pooled(self, conn: Any, database: str) -> None:
        raise NotImplementedError(self._DB_MSG)


# ── Shared helper functions ──────────────────────────────────────────────────


def _matches_filters(metadata: dict, filters: dict) -> bool:
    """Return True when every *filters* key/value appears in *metadata*."""
    if not filters:
        return True
    for key, value in filters.items():
        if key not in metadata:
            return False
        if metadata[key] != value:
            return False
    return True


def _json_default(obj: Any) -> Any:
    """JSON encoder hook: serialise datetime and dataclass objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _serialize_fact(fact: Any) -> dict[str, Any]:
    """Serialise a Fact into a JSON-compatible dict."""
    from dataclasses import asdict

    data = asdict(fact)
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data


def _deserialize_fact(data: dict[str, Any]) -> Any:
    """Reconstruct a :class:`~engine.knowledge.Fact` from a dict."""
    from engine.knowledge import Fact

    timestamp = data.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)

    # The store's own writer always emits an ISO timestamp; the cast states the
    # dataclass contract and keeps a hand-edited store's absent timestamp
    # passing through exactly as before.
    return Fact(
        id=data["id"],
        statement=data["statement"],
        source_id=data["source_id"],
        confidence=data["confidence"],
        timestamp=cast("datetime", timestamp),
        provenance_chain=list(data.get("provenance_chain", [])),
        metadata=dict(data.get("metadata", {})),
    )


def _serialize_evidence(evidence: Any) -> dict[str, Any]:
    """Serialise an Evidence item into a JSON-compatible dict."""
    from dataclasses import asdict

    data = asdict(evidence)
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data


def _deserialize_evidence(data: dict[str, Any]) -> Any:
    """Reconstruct an :class:`~engine.evidence.Evidence` from a dict."""
    from engine.evidence import Evidence, EvidenceSource, EvidenceType

    timestamp = data.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)

    return Evidence(
        id=data["id"],
        source=EvidenceSource(data["source"]),
        evidence_type=EvidenceType(data["evidence_type"]),
        value=data["value"],
        confidence=data["confidence"],
        # Cast for the same reason as Fact: the writer always emits the
        # timestamp, and an absent one still passes through unchanged.
        timestamp=cast("datetime", timestamp),
        provenance=list(data.get("provenance", [])),
        metadata=dict(data.get("metadata", {})),
    )


def _serialize_decision(decision: Any) -> dict[str, Any]:
    """Serialise a Decision into a JSON-compatible dict."""
    from dataclasses import asdict

    data = asdict(decision)
    if isinstance(data.get("status"), str):
        pass
    return data


def _deserialize_decision(data: dict[str, Any]) -> Any:
    """Reconstruct a :class:`~engine.tasmimyar.Decision` from a dict."""
    from engine.tasmimyar import (
        Decision,
        DecisionCriterion,
        DecisionStatus,
        DecisionTrace,
    )

    criteria = [DecisionCriterion(**c) for c in data.get("criteria", [])]
    trace_data = data.get("trace", {})
    trace = DecisionTrace(**trace_data) if trace_data else None

    status_raw = data.get("status", "evaluated")
    try:
        status = DecisionStatus(status_raw)
    except ValueError:
        status = DecisionStatus.EVALUATED

    return Decision(
        decision_id=data["decision_id"],
        claim_id=data["claim_id"],
        outcome=data["outcome"],
        confidence=data["confidence"],
        criteria=criteria,
        # A stored decision always carries its trace; an absent one would pass
        # None exactly as before, so the cast states the contract without
        # changing the failure mode of a hand-edited store.
        trace=cast("DecisionTrace", trace),
        rationale=data.get("rationale", ""),
        recommendations=list(data.get("recommendations", [])),
        caveats=list(data.get("caveats", [])),
        status=status,
        timestamp=data.get("timestamp", ""),
    )
