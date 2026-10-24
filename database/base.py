"""Base module for ORM models.

Provides the single SQLAlchemy declarative base that every ORM model
in the application layer inherits from. One shared ``Base`` means one
``metadata`` registry, which is what lets ``create_all`` and migrations
see every model in one place.

This is the application-layer persistence foundation. The engine
(scientific core) does not import this module directly; it reaches
persistence through ``engine.ports``. See ECO-04 §11.
"""

from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase


@compiles(JSONB, "sqlite")
def _compile_jsonb_on_sqlite(type_: JSONB, compiler: Any, **kw: Any) -> str:
    """Render PostgreSQL's ``JSONB`` as SQLite's ``JSON``.

    Service models declare PostgreSQL-dialect columns (``services/models/
    land_models.py``), while tests and local development run on SQLite.
    Without this shim, importing any such model registers a table whose
    columns SQLite cannot compile, and every later ``create_all`` in the
    same process fails -- which is how running the engine and services
    suites in one pytest session broke 167 tests (S17, D-26). The dialect
    map only affects SQLite; PostgreSQL keeps native ``JSONB``.
    """
    return "JSON"


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Works with both the legacy ``Column(...)`` style and the modern
    ``Mapped[...]`` / ``mapped_column(...)`` style, so engine-internal
    and service-layer models can share one metadata registry.
    """


__all__ = ["Base"]
