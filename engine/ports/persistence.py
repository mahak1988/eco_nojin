"""Persistence port for the engine.

This module defines the PersistencePort interface that the engine uses
to access database services through dependency injection, rather than
importing database implementation directly.

Per docs/specs/ECO-04.md §11:
  Engine should only know the contract/port, not the database implementation.

The PersistencePort is the single interface the engine needs for:
1. Database connection access (get_duckdb, get_sqlite)
2. Pooled connection management
3. Session factory provision
4. Domain-object persistence (save/load Evidence, Fact, Decision)

Architecture:
  Application
      ↓
  Repository / Port  (this module - PersistencePort)
      ↓
  Persistence Adapter (provided by services/application layer)
      ↓
  Database
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from engine.ports.persistence_impl import FileBackedPersistence, InMemoryPersistence

if TYPE_CHECKING:
    from engine.evidence import Evidence
    from engine.knowledge import Fact
    from engine.tasmimyar import Decision

__all__ = [
    "PersistencePort",
    "default_persistence_port",
    "InMemoryPersistence",
    "FileBackedPersistence",
]


@runtime_checkable
class PersistencePort(Protocol):
    """The persistence collaborator the engine needs.

    This protocol defines the interface that the persistence adapter
    must implement. The engine depends ONLY on this protocol, never
    on a specific database implementation.

    Attributes:
        get_duckdb: Return a DuckDB connection for the named database.
        get_sqlite: Return a SQLite connection for the named database.
        get_duckdb_pooled: Return a pooled DuckDB connection.
        return_duckdb_pooled: Return a connection to the pool.
    """

    def get_duckdb(self, name: str) -> Any:
        """Return a DuckDB connection for the named database."""
        ...

    def get_sqlite(self, name: str) -> Any:
        """Return a SQLite connection for the named database."""
        ...

    def get_duckdb_pooled(self, database: str) -> Any:
        """Return a pooled DuckDB connection."""
        ...

    def return_duckdb_pooled(self, conn: Any, database: str) -> None:
        """Return a pooled connection to the pool."""
        ...

    # ── Domain-object persistence ──────────────────────────────────
    # These methods persist the epistemic types used by the Evidence,
    # Knowledge, and Decision engines. A production adapter backed by a
    # database should implement them; the in-memory and file-backed
    # implementations in this module provide the domain contract for
    # testing and local operation.

    def save_evidence(self, evidence: Evidence) -> str:
        """Persist an Evidence item. Returns its evidence_id."""
        ...

    def load_evidence(self, evidence_id: str) -> Evidence | None:
        """Load a previously-saved Evidence item by ID."""
        ...

    def save_fact(self, fact: Fact) -> str:
        """Persist a Fact. Returns its fact_id."""
        ...

    def load_fact(self, fact_id: str) -> Fact | None:
        """Load a previously-saved Fact by ID."""
        ...

    def save_decision(self, decision: Decision) -> str:
        """Persist a Decision. Returns its decision_id."""
        ...

    def load_decision(self, decision_id: str) -> Decision | None:
        """Load a previously-saved Decision by ID."""
        ...

    def list_evidence(self, filters: dict) -> list[Evidence]:
        """List evidence items matching *filters* (key/value metadata match)."""
        ...


class _MissingPersistencePort:
    """Placeholder used when no persistence port has been configured.

    All methods raise a clear error explaining that persistence
    must be injected via the Engine Gateway.
    """

    _MSG = (
        "Persistence not configured. The engine was initialized without a "
        "PersistencePort. Inject a port via the Engine Gateway or "
        "DataConnector constructor."
    )

    def get_duckdb(self, name: str) -> Any:
        raise RuntimeError(self._MSG)

    def get_sqlite(self, name: str) -> Any:
        raise RuntimeError(self._MSG)

    def get_duckdb_pooled(self, database: str) -> Any:
        raise RuntimeError(self._MSG)

    def return_duckdb_pooled(self, conn: Any, database: str) -> None:
        raise RuntimeError(self._MSG)

    def save_evidence(self, evidence: Any) -> str:
        raise RuntimeError(self._MSG)

    def load_evidence(self, evidence_id: str) -> Any:
        raise RuntimeError(self._MSG)

    def save_fact(self, fact: Any) -> str:
        raise RuntimeError(self._MSG)

    def load_fact(self, fact_id: str) -> Any:
        raise RuntimeError(self._MSG)

    def save_decision(self, decision: Any) -> str:
        raise RuntimeError(self._MSG)

    def load_decision(self, decision_id: str) -> Any:
        raise RuntimeError(self._MSG)

    def list_evidence(self, filters: dict) -> list[Any]:
        raise RuntimeError(self._MSG)

    # ── Schema / Base access ─────────────────────────────────────────
    # ``engine.hydroma.core.models`` imports ``Base`` from the database shim
    # so ORM models can declare their tables without importing the database
    # package. The default port returns a process-local declarative base; a
    # production adapter returns the shared one.
    def get_base(self) -> Any:
        from sqlalchemy.orm import declarative_base

        return declarative_base()


# Module-level default port instance.
# This is NOT a database import — it's a local stub that raises if used
# without being properly configured. The production implementation is
# provided by services via dependency injection.
def default_persistence_port() -> PersistencePort:
    """Return the default persistence port.

    Returns a stub that raises if used. The real implementation is
    injected by the application layer via DataConnector.__init__(hub=...).

    This function does NOT import from 'database' — it returns a local
    stub. The import guard should not flag this.
    """
    return _MissingPersistencePort()
