"""Database package.

Provides the shared declarative ``Base``, the session factory
(``SessionLocal``) and the engine they are bound to. Importing
this package makes all three available as ``database.Base``,
``database.SessionLocal`` and ``database.engine``.
"""

from typing import Any

from database.base import Base

__all__ = ["Base", "SessionLocal", "engine"]


def __getattr__(name: str) -> Any:
    """Resolve ``SessionLocal``/``engine`` lazily (PEP 562).

    They used to be imported eagerly, which meant importing *any* part of
    this package (for example the sanctioned ``database.base`` bridge the
    engine may use) also executed ``database/config.py`` and its engine
    construction. The engine is only allowed to reach
    ``database.base`` (``tools/import_guard_policy.json`` marks
    ``database.config`` ``pending-removal``), and an eager import made
    that impossible to observe: ``sys.modules`` showed ``database.config``
    no matter which submodule was imported. Callers keep the same API
    (``database.SessionLocal`` / ``database.engine``); the import happens
    on first attribute access instead of at package import.
    """
    if name in ("SessionLocal", "engine"):
        from database import config

        return getattr(config, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
