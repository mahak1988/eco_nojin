"""Alembic environment (Phase 0).

Uses the unified ``database.config`` engine and metadata so migrations
cover both ``database.models`` and ``engine.hydroma.core.models``.
SQLite uses batch mode (copy-and-move) for ALTER support.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

# Make repo root importable regardless of CWD
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import database.models  # noqa: E402,F401  (register ORM models)
import engine.hydroma.core.models  # noqa: E402,F401
from database.config import Base  # noqa: E402
from database.config import engine as target_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# SQLite requires batch mode for ALTER/CONSTRAINT operations
RENDER_AS_BATCH = target_engine.url.get_backend_name() == "sqlite"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to stdout)."""
    url = target_engine.url.render_as_string(hide_password=False)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=RENDER_AS_BATCH,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the engine)."""
    connectable = target_engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=RENDER_AS_BATCH,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
