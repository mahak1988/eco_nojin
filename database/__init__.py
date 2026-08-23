"""
Database Package - EcoNojin
============================
Central exports for database access.

Primary exports:
    - get_db: FastAPI dependency for database sessions
    - SessionLocal: SQLAlchemy session factory
    - engine: SQLAlchemy engine
    - Base: Declarative base for models
    - settings: Application settings
    - init_db: Initialize database schema

Models are available via:
    - database.models (SQLAlchemy ORM models)
    - database.models.database_models (analysis result models)
"""

# Core database configuration
from .config import (
    get_db,
    init_db,
    settings,
    Base,
    engine,
    SessionLocal,
)

# Adapter for multiple database backends
try:
    from .adapter import DatabaseAdapter, DuckDBAdapter
except ImportError:
    DatabaseAdapter = None
    DuckDBAdapter = None

# Analytics engine
try:
    from .analytics import AnalyticsEngine, get_analytics
except ImportError:
    AnalyticsEngine = None
    get_analytics = None

__all__ = [
    # Core
    "get_db",
    "init_db",
    "settings",
    "Base",
    "engine",
    "SessionLocal",
    # Adapters
    "DatabaseAdapter",
    "DuckDBAdapter",
    # Analytics
    "AnalyticsEngine",
    "get_analytics",
]
