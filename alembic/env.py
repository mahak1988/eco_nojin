"""Alembic environment — wired to the unified database.config (Phase 0)."""

import os
from importlib import import_module
from logging.config import fileConfig

from dotenv import load_dotenv

from alembic import context

load_dotenv()
models = import_module("database.models")
Base = models.Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    url = os.getenv("DATABASE_URL") or "sqlite:///./data/econojin.db"
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _resolve_engine():
    """ساخت موتور از تنظیمات config (sqlalchemy.url)"""
    from sqlalchemy import engine_from_config
    from sqlalchemy.pool import NullPool

    url = config.get_main_option("sqlalchemy.url") or _database_url()
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = url
    return engine_from_config(cfg, prefix="sqlalchemy.", poolclass=NullPool)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url") or _database_url()
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
