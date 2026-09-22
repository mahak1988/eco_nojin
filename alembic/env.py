"""Alembic environment — wired to the unified database.config (Phase 0)."""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

from alembic import context

from database.models import Base
from database import models  # noqa: F401  (populates Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_engine():
    """ساخت موتور از تنظیمات config (sqlalchemy.url)"""
    from sqlalchemy import engine_from_config
    from sqlalchemy.pool import NullPool
    import os

    # دریافت url از config یا متغیر محیطی
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = os.getenv("DATABASE_URL", "sqlite:///./data/econojin.db")
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = url
    return engine_from_config(cfg, prefix="sqlalchemy.", poolclass=NullPool)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = "sqlite:///./data/econojin.db"
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = _resolve_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
