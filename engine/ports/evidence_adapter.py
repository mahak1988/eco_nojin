"""Port for evidence / computation-record persistence.

This module defines the contract the engine uses to persist the immutable
records that make up the provenance chain. The engine depends ONLY on this
protocol (and the :class:`ComputationRecord` dataclass it defines) — never on
a specific database implementation. The production adapter is provided by the
services / application layer via dependency injection through the Engine
Gateway.

Per INV-002 (ECO-04 §11): the engine must not import ``database``. Every
call site that needs persistence goes through :class:`EvidenceAdapter`.

The :class:`ComputationRecord` is the canonical serialisable unit of a single
gateway execution: it binds a ``trace_id`` to the model, inputs, parameters,
outputs, and the Evidence id that summarises the run, so an external auditor
can re-derive the full chain ``data -> transforms -> model -> parameters ->
execution -> result -> interpretation -> decision``.

Architecture:
    Application
        -> EvidenceAdapter port (this module)
        -> Persistence adapter (services layer)
        -> Database
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "ComputationRecord",
    "EvidenceAdapter",
    "default_evidence_adapter",
]


@dataclass
class ComputationRecord:
    """Immutable record of a single scientific computation.

    A computation record is the persistence-side mirror of a gateway
    execution: it captures everything required to replay or re-audit the
    result, keyed by a ``trace_id`` that links back to the Evidence item
    generated for the run.

    Attributes:
        trace_id: Stable identifier shared with the generated Evidence item.
        model_id: Identifier of the executed model (e.g. ``CANON-001``).
        model_version: Version string of the model.
        model_name: Human-readable model name.
        inputs: Normalised (SI) input values.
        parameters: Model parameters used for the run.
        outputs: Raw computation result.
        evidence_id: ID of the Evidence item summarising this execution.
        execution_id: Per-execution identifier from ExecutionMetadata.
        started_at: When the computation started (ISO-8601).
        completed_at: When the computation finished (ISO-8601).
        duration_ms: Wall-clock duration of the computation.
        status: ``success`` or ``error``.
        error: Error message when ``status == "error"``.
        gateway_version: Version of the gateway that ran the computation.
        provenance: Upstream evidence / fact IDs that funded this run.
    """

    trace_id: str
    model_id: str
    model_version: str = ""
    model_name: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    evidence_id: str | None = None
    execution_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: float | None = None
    status: str = "success"
    error: str | None = None
    gateway_version: str = "1.0.0"
    provenance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict of this record."""
        data = asdict(self)
        if isinstance(data.get("started_at"), datetime):
            data["started_at"] = data["started_at"].isoformat()
        if isinstance(data.get("completed_at"), datetime):
            data["completed_at"] = data["completed_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComputationRecord:
        """Reconstruct a record from a dict (e.g. from persisted JSON)."""
        return cls(
            trace_id=data["trace_id"],
            model_id=data["model_id"],
            model_version=data.get("model_version", ""),
            model_name=data.get("model_name", ""),
            inputs=dict(data.get("inputs", {})),
            parameters=dict(data.get("parameters", {})),
            outputs=dict(data.get("outputs", {})),
            evidence_id=data.get("evidence_id"),
            execution_id=data.get("execution_id"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            duration_ms=data.get("duration_ms"),
            status=data.get("status", "success"),
            error=data.get("error"),
            gateway_version=data.get("gateway_version", "1.0.0"),
            provenance=list(data.get("provenance", [])),
        )


@runtime_checkable
class EvidenceAdapter(Protocol):
    """Interface for evidence / computation-record persistence.

    Implementations live in the services layer (e.g. a SQLAlchemy or
    DuckDB-backed store). The engine speaks only this protocol so that the
    storage backend can be swapped without touching engine code.
    """

    def store_computation_record(self, record: ComputationRecord) -> str:
        """Persist a computation record and return its trace_id.

        Implementations should treat records as immutable: a record with an
        existing trace_id is either rejected or version-stamped rather than
        overwritten, preserving the audit trail.
        """
        ...

    def retrieve_by_trace(self, trace_id: str) -> ComputationRecord:
        """Retrieve a single computation record by its trace_id.

        Raises:
            KeyError: if no record is stored for *trace_id*.
        """
        ...

    def list_records_by_model(self, model_id: str) -> list[str]:
        """Return the trace_ids of all records for *model_id*, newest last."""
        ...


class _MissingEvidenceAdapter:
    """Placeholder used when no evidence adapter has been configured.

    All methods raise a clear error explaining that persistence must be
    injected via the Engine Gateway.
    """

    _MSG = (
        "Evidence persistence not configured. The engine was initialised "
        "without an EvidenceAdapter. Inject a port via the Engine Gateway."
    )

    def store_computation_record(self, record: ComputationRecord) -> str:
        raise RuntimeError(self._MSG)

    def retrieve_by_trace(self, trace_id: str) -> ComputationRecord:
        raise RuntimeError(self._MSG)

    def list_records_by_model(self, model_id: str) -> list[str]:
        raise RuntimeError(self._MSG)


def default_evidence_adapter() -> EvidenceAdapter:
    """Return the default evidence adapter.

    Returns a stub that raises if used. The real implementation is injected by
    the application layer via the Engine Gateway. This function does NOT
    import from ``database`` — it returns a local stub.
    """
    return _MissingEvidenceAdapter()
