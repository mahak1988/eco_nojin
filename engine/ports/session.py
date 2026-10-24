"""Persistence ports for the engine.

The engine is the scientific core. It computes; something else stores. This
module declares the *shape* of the persistence collaborator the engine needs,
without naming SQLAlchemy, a session factory, or a database package.

Why this exists
---------------
Thirteen engine call sites used to do ``from database.config import
SessionLocal`` at module import time, which meant importing any of those
modules pulled in the entire database layer. ``engine/README.md`` claims the
engine is independent of the rest of the application; until this module
existed that claim was false and mechanically so.

Scope of the port
-----------------
The protocol below is deliberately **not** "everything SQLAlchemy's Session
can do". It is exactly the surface the engine call sites touch:

===========================  ==================================================
Call site                     Methods required
===========================  ==================================================
calibration/calibrator.py    add, commit, rollback, close
calibration/validator.py     query(...).filter(...).first(), commit, rollback, close
calibration/version_manager  query/filter/first/order_by/limit, update, add,
                              commit, rollback, close
optimization/optimizer.py    add, commit, rollback, close
decision_support/dss.py      add, flush, commit, rollback, close
scenarios/scenario_manager   query/filter/first, add, commit, rollback, close
biofertilizer/*              query/get/filter/order_by/limit/join/count,
                              add, delete, refresh, commit, close
analyses/topography_analysis add, commit
mrv/iot_ingest.py            query/filter/order_by/limit/all, add, refresh, commit
===========================  ==================================================

A SQLAlchemy ``Session`` structurally satisfies both protocols, so no adapter
is required to adopt it. Tests can pass an in-memory double instead, which is
how the persistence-dependent engine code becomes testable without a database.

Importing this module must stay cheap: it imports nothing outside the standard
library, and the default implementation is built lazily inside
:func:`default_session_factory` rather than at module scope.

Database boundary
-----------------
Per ECO-04 §11, the engine must not depend on the ``database`` package.
All database access goes through :class:`engine.ports.persistence.PersistencePort`.
The functions in this module use the port abstraction, NOT direct database imports.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, Self, runtime_checkable

__all__ = [
    "QueryPort",
    "SessionFactory",
    "SessionPort",
    "UnitOfWork",
]


@runtime_checkable
class QueryPort(Protocol):
    """The query builder surface the engine uses.

    Every terminal method returns a plain Python value and every intermediate
    method returns ``Self``, which is what lets call sites chain
    ``session.query(M).filter(...).order_by(...).limit(n).all()``.
    """

    def filter(self, *criteria: Any) -> Self:
        """Narrow the result set. Returns a new query."""

    def order_by(self, *criteria: Any) -> Self:
        """Order the result set. Returns a new query."""

    def limit(self, count: int) -> Self:
        """Cap the number of rows. Returns a new query."""

    def join(self, target: Any, *onclause: Any) -> Self:
        """SQL JOIN. Returns a new query."""

    def first(self) -> Any:
        """First row, or None."""

    def all(self) -> list[Any]:
        """Every row as a list."""

    def count(self) -> int:
        """Number of matching rows."""

    def update(self, values: dict[str, Any]) -> int:
        """Bulk UPDATE. Returns the number of rows changed."""


@runtime_checkable
class SessionPort(Protocol):
    """Unit-of-work over a set of mapped objects.

    Naming note: this is a *session*, not a repository. The engine still names
    ORM row classes when it persists, so it is coupled to an ORM's vocabulary
    even after the import is gone. Hiding that behind a repository protocol
    would be a larger refactor than removing the import, and would move the
    coupling rather than remove it.
    """

    def add(self, instance: Any) -> None:
        """Stage an object for insertion."""

    def delete(self, instance: Any) -> None:
        """Stage an object for deletion."""

    def commit(self) -> None:
        """Persist everything staged so far."""

    def flush(self) -> None:
        """Push pending state without ending the transaction.

        Needed to read a server-generated primary key back before commit.
        """

    def rollback(self) -> None:
        """Discard everything staged in this transaction."""

    def refresh(self, instance: Any) -> None:
        """Reload an instance's column values from the database."""

    def close(self) -> None:
        """Release the underlying connection."""

    def get(self, entity: type, ident: Any) -> Any:
        """Primary-key lookup, or None."""

    def query(self, *entities: type) -> QueryPort:
        """Start a query against one or more mapped classes."""


#: Anything that builds a fresh :class:`SessionPort`. A SQLAlchemy
#: ``sessionmaker`` is the production implementation.
SessionFactory = Callable[[], SessionPort]


@runtime_checkable
class UnitOfWork(Protocol):
    """Context-managed session scope.

    ``mrv/iot_ingest.get_latest_readings`` needs this shape: it borrows a
    session for the duration of a ``with`` block and must not own its
    lifecycle.
    """

    def __enter__(self) -> SessionPort:
        """Acquire a session."""

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Release the session, rolling back if the block raised."""


def default_session_factory() -> SessionFactory:
    """Return the production session factory, building it on first call.

    Uses PersistencePort abstraction instead of importing database directly.
    The production implementation is injected via the PersistencePort.
    """
    from engine.ports.persistence import default_persistence_port

    port = default_persistence_port()
    # The production port provides a get_session method
    if hasattr(port, "get_session_factory"):
        factory: SessionFactory = port.get_session_factory()
        return factory
    raise RuntimeError(
        "Persistence not configured. Inject a PersistencePort with "
        "get_session_factory() or provide SessionLocal via DI."
    )


def resolve_database_attr(module: str, name: str) -> Any:
    """Resolve database model attributes via PersistencePort, not direct import.

    The engine still names ORM row classes when it persists, so those names
    have to come from somewhere. They come from here, on demand, via the
    PersistencePort, turning a direct database dependency into a port call
    that a test can pre-empt by injecting its own.

    Args:
        module: Submodule name, e.g. ``"models"``.
        name: Attribute within it, e.g. ``"CalibrationRecordDB"``.

    Raises:
        AttributeError: if PersistencePort does not provide the attribute.
    """
    from engine.ports.persistence import default_persistence_port

    port = default_persistence_port()

    # The production port provides a get_model_attr method
    if hasattr(port, "get_model_attr"):
        return port.get_model_attr(module, name)

    raise AttributeError(
        f"PersistencePort does not provide '{name}' from '{module}'. "
        "Ensure a production PersistencePort adapter is configured."
    )


def default_unit_of_work() -> Callable[[], UnitOfWork]:
    """Return the production context-managed session scope, on first call.

    Uses PersistencePort abstraction instead of importing database.hub.
    """
    from engine.ports.persistence import default_persistence_port

    port = default_persistence_port()

    scoped: Callable[[], UnitOfWork] = port.get_session  # type: ignore[attr-defined]
    return scoped
