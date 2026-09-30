"""Database reset helper shared by the integration test modules.

``Base.metadata.drop_all()`` only drops objects the model metadata knows about, so
a table or index left behind by an earlier module -- or created by an Alembic
migration whose objects the models do not declare -- survives and makes the next
``create_all()`` fail with "index ... already exists". The integration modules
shared one file-backed SQLite database, so the failure depended on execution
order.

``reset_database()`` reflects the live schema first and drops everything in it,
including objects the metadata does not model, then recreates from the metadata.
The result is order-independent.
"""

from __future__ import annotations

import contextlib
import importlib

from sqlalchemy import inspect, text

from database.base import Base

#: Imported for their side effect of registering their tables on ``Base``.
#: services.provenance.models is deliberately absent: its three tables declare
#: PostgreSQL UUID columns, so Base.metadata.create_all raises
#: UnsupportedCompilationError on SQLite. Those tables therefore have no
#: migration either and cannot exist on the SQLite dev/test lane at all.
_MODEL_MODULES = (
    "database.models",
    "services.marketplace.models",
)


def reset_database(bind=None) -> None:
    """Drop the entire schema, then recreate it from the model metadata."""
    for name in _MODEL_MODULES:
        with contextlib.suppress(Exception):  # pragma: no cover - optional model packages
            importlib.import_module(name)

    if bind is None:
        from database.hub import hub

        bind = hub.get_sqlalchemy_engine()

    insp = inspect(bind)
    # Dispose the async engine first. It keeps its own pooled connections, and a
    # connection opened before the drop would still be mid-transaction, which
    # surfaces as "no such table: users" in whichever test runs next.
    try:
        from database.hub import hub

        async_engine = getattr(hub, "_async_engine", None)
        if async_engine is not None:
            hub._async_engine = None
            hub._async_session_factory = None
            async_engine.sync_engine.dispose()
    except Exception:  # pragma: no cover - disposal is best effort
        pass

    # SQLAlchemy 2.0 removed Engine.execute(); go through a connection.
    # Foreign keys are suspended for the drop: SQLite has no CASCADE DROP TABLE,
    # so dropping a parent before its children fails with "no such table".
    with bind.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
        for table in sorted(insp.get_table_names(), reverse=True):
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(bind=bind)
