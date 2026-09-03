"""
database.hub.hub
================

Central data access hub for Eco Nojin project.

This module provides a unified interface to all data sources:
- SQLAlchemy sessions (transactional data)
- DuckDB connections (analytics)
- SQLite connections (manual data)
- Redis connections (cache)

Usage:
    from database.hub import hub

    # Transactional queries with auto-commit
    with hub.get_session() as session:
        users = session.query(User).all()

    # Analytics queries
    conn = hub.get_duckdb("master")
    df = conn.execute("SELECT * FROM table").fetchdf()

    # Manual data
    sqlite_conn = hub.get_sqlite("manual")

Author: Eco Nojin Architecture Team
"""

from typing import Optional, Any, Generator
from pathlib import Path
from contextlib import contextmanager
import os
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DataHub:
    """
    Central data access hub (Singleton pattern).
    
    Provides unified access to all data sources with:
    - Automatic connection management
    - Transaction handling
    - Connection pooling
    - Integrated logging

    # Consolidated Architecture (Phase 3):
    # - Master DuckDB: data/eco_nojin_master.duckdb (132 tables, 466K+ rows)
    # - Transactional: data/econojin.db (62 tables via SQLAlchemy)
    # - Reference: data/manual/eco_manual_v1.sqlite (18 tables, 175K rows)
    #
    # Source databases (eco_nojin.duckdb, eco_nojin_analytics.duckdb) have been
    # migrated to master and can be archived after verification.

    """

    _instance: Optional["DataHub"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._duckdb_connection = None
        self._sqlalchemy_engine = None
        self._session_factory = None
        self._redis_client = None

        # Data paths
        self.data_dir = PROJECT_ROOT / "data"
        self.master_duckdb = self.data_dir / "eco_nojin_master.duckdb"
        self.analytics_duckdb = self.data_dir / "eco_nojin_analytics.duckdb"
        self.manual_sqlite = self.data_dir / "manual" / "eco_manual_v1.sqlite"
        self.main_sqlite = self.data_dir / "econojin.db"

        logger.info("DataHub initialized")

    def get_sqlalchemy_engine(self) -> Any:
        """Get SQLAlchemy engine with optimized pooling."""
        if self._sqlalchemy_engine is None:
            from sqlalchemy import create_engine
            from sqlalchemy.pool import QueuePool

            database_url = os.environ.get(
                "DATABASE_URL",
                f"sqlite:///{self.main_sqlite}"
            )

            self._sqlalchemy_engine = create_engine(
                database_url,
                echo=False,
                poolclass=QueuePool,
                pool_size=30,
                max_overflow=60,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            logger.info(f"SQLAlchemy engine created: {database_url}")

        return self._sqlalchemy_engine

    def get_session_factory(self) -> Any:
        """Get SQLAlchemy session factory."""
        if self._session_factory is None:
            from sqlalchemy.orm import sessionmaker

            engine = self.get_sqlalchemy_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

            logger.info("Session factory created")

        return self._session_factory

    @contextmanager
    def get_session(self) -> Generator:
        """
        Get a session with automatic transaction management.
        
        Usage:
            with hub.get_session() as session:
                users = session.query(User).all()
        
        Yields:
            SQLAlchemy Session instance
        """
        session_factory = self.get_session_factory()
        session = session_factory()

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            session.close()

    def get_duckdb(self, database: str = "master") -> Any:
        """
        Get DuckDB connection.
        
        Args:
            database: "master" or "analytics"
        
        Returns:
            DuckDB connection
        """
        try:
            import duckdb
        except ImportError:
            raise ImportError("duckdb is not installed. Run: pip install duckdb")

        if database == "master":
            db_path = self.master_duckdb
        elif database == "analytics":
            db_path = self.analytics_duckdb
        else:
            raise ValueError(f"Unknown database: {database}")

        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = duckdb.connect(str(db_path))
        logger.info(f"DuckDB connection created: {db_path}")

        return conn

    def get_sqlite(self, database: str = "manual") -> Any:
        """
        Get SQLite connection.
        
        Args:
            database: "manual" for manual data
        
        Returns:
            SQLite connection with row factory
        """
        import sqlite3

        if database == "manual":
            db_path = self.manual_sqlite
        else:
            raise ValueError(f"Unknown database: {database}")

        if not db_path.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        logger.info(f"SQLite connection created: {db_path}")

        return conn

    def get_redis(self) -> Any:
        """
        Get Redis client.
        
        Returns:
            Redis client instance
        """
        if self._redis_client is None:
            try:
                import redis
            except ImportError:
                raise ImportError("redis is not installed. Run: pip install redis")

            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info(f"Redis connection created: {redis_url}")

        return self._redis_client

    def close_all(self):
        """Close all active connections."""
        if self._duckdb_connection:
            self._duckdb_connection.close()
            self._duckdb_connection = None
            logger.info("DuckDB connection closed")

        if self._sqlalchemy_engine:
            self._sqlalchemy_engine.dispose()
            self._sqlalchemy_engine = None
            self._session_factory = None
            logger.info("SQLAlchemy engine disposed")

        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None
            logger.info("Redis connection closed")


# Global instance
hub = DataHub()

__all__ = ["DataHub", "hub"]
