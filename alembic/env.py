"""Alembic environment script.

Configured so that ``alembic upgrade --sql`` renders the SQL that Alembic
would execute, without requiring a running database server. The test suite
calls this in a subprocess to prove each migration is not merely well-formed
but executable.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

# Make the project root importable so ``import database.models`` resolves.
sys.path.insert(0, os.environ.get("PYTHONPATH", ""))

from sqlalchemy import MetaData, engine_from_config, pool

# ---------------------------------------------------------------------------
# target_metadata: import the ORM models so autogenerate sees all tables.
# We import defensively — if a model has a hard dependency that is not
# installable in the environment, the SQL-rendering path still works because
# we register tables from Base.metadata.
# ---------------------------------------------------------------------------
target_metadata = MetaData()
try:
    from database.models import Base as DefaultBase  # noqa: F401

    target_metadata = DefaultBase.metadata
except Exception:  # pragma: no cover - environment-specific
    pass

config = None  # populated below in run_migrations_online / offline

# this is alembic's config object; accessed as the global ``config`` symbol
# that alembic's env_template expects.
from alembic import context

config = context.config

if config.config_file_name is not None:
    # P1 (supervisor): the default ``disable_existing_loggers=True`` sets
    # ``logger.disabled = True`` on every pre-existing logger not named in
    # alembic.ini — including ``database.hub``, whose WAL-reset ERROR then never
    # reaches any test's caplog. That made
    # ``test_sqlite_concurrency.py::...test_affected_runtime_logs_the_upgrade_requirement``
    # fail whenever an alembic test ran earlier in the same process.
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def get_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./_alembic_sqlcheck.db")


def run_migrations_offline() -> None:
    """Render SQL without connecting to a database."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_name="sqlite",
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        url=get_url(),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
