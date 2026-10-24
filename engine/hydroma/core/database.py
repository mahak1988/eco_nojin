"""Database access for the HyDroMa engine (lazy compatibility shim).

Backwards-compatible surface for ``from engine.hydroma.core.database import
Base, SessionLocal, engine, get_db, init_db``.

Resolution is lazy (PEP 562 ``__getattr__``) so that merely importing this
module does **not** pull in the application-layer ``database`` package.
Names are resolved on first access through :class:`engine.ports.PersistencePort`,
which is the contract the engine is allowed to depend on (ECO-04 §11). The
production adapter is injected by the application layer; in the meantime a
default in-memory adapter is returned.

This module is a **compatibility shim**, not a port implementation. New
engine code should depend on ``engine.ports.PersistencePort`` and inject a
session; see ``engine/ports/session.py``.
"""

from __future__ import annotations

from typing import Any

__all__ = ["Base", "SessionLocal", "engine", "get_db", "init_db"]  # noqa: F822


def _resolve(name: str) -> Any:
    """Resolve a shimmed database name via PersistencePort, never via direct import."""
    from engine.ports.persistence import default_persistence_port

    port = default_persistence_port()

    if name == "Base":
        # The production port exposes get_base(); the abstraction deliberately
        # declares only what every persistence backend provides.
        return port.get_base()  # type: ignore[attr-defined]
    if name == "SessionLocal":
        factory = getattr(port, "get_session_factory", None)
        if factory is not None:
            return factory()
        return None
    if name == "engine":
        eng = getattr(port, "get_engine", lambda: None)()
        if eng is None:
            raise AttributeError(
                f"engine.hydroma.core.database cannot provide '{name}'. "
                "The database layer is not available in this engine context; "
                "inject a real PersistencePort via the Engine Gateway."
            )
        return eng
    if name in ("get_db", "init_db"):
        raise AttributeError(
            f"engine.hydroma.core.database cannot provide '{name}'. "
            "The database layer is not available in this engine context; "
            "inject a real PersistencePort via the Engine Gateway."
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str) -> Any:
    """Resolve a shimmed database name on first access via PersistencePort."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return _resolve(name)


def __dir__() -> list[str]:
    return sorted(__all__)
