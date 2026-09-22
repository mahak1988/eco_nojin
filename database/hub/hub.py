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

import logging
import os
import queue
import threading
import time
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, Optional

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
        self._async_engine = None
        self._async_session_factory = None
        self._redis_client = None
        self._active_duckdb_connections: dict = {}
        self._active_sqlite_connections: dict = {}

        # Thread safety lock for singleton initialization and connection access
        self._lock = threading.RLock()

        # Session pool tracking for cleanup
        self._active_sessions = set()
        self._sessions_lock = threading.Lock()

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

            database_url = os.environ.get("DATABASE_URL", f"sqlite:///{self.main_sqlite}")

            self._sqlalchemy_engine = create_engine(
                database_url,
                echo=False,
                poolclass=QueuePool,
                pool_size=50,
                max_overflow=100,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=30,
                connect_args={"timeout": 30.0} if database_url.startswith("sqlite") else {},
            )

            # --- SQLite hardening (WAL + FK + busy timeout) ---
            if database_url.startswith("sqlite"):
                from sqlalchemy import event as _sa_event

                @_sa_event.listens_for(self._sqlalchemy_engine, "connect")
                def _set_sqlite_pragmas(dbapi_connection, _record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA busy_timeout=5000")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.close()

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
    def get_session(self, timeout: float = 30.0) -> Generator:
        """
        Get a session with automatic transaction management and timeout.

        Usage:
            with hub.get_session() as session:
                users = session.query(User).all()

        Args:
            timeout: Maximum time to wait for a connection (seconds)

        Yields:
            SQLAlchemy Session instance
        """
        session_factory = self.get_session_factory()
        session = None

        # Acquire session with timeout
        acquired = False
        start_time = time.time()

        with self._sessions_lock:
            while not acquired:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(
                        f"Could not acquire database session within {timeout}s timeout. "
                        f"Check connection pool settings or wait for active operations to complete."
                    )
                # Check if we can create a new session
                try:
                    session = session_factory()
                    self._active_sessions.add(id(session))
                    acquired = True
                except Exception:
                    # Pool might be exhausted, wait a moment
                    time.sleep(0.01)

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            with self._sessions_lock:
                self._active_sessions.discard(id(session))
            session.close()

    def get_async_engine(self) -> Any:
        """Get async SQLAlchemy engine (additive — sync paths untouched)."""
        if getattr(self, "_async_engine", None) is None:
            from sqlalchemy.ext.asyncio import create_async_engine

            database_url = os.environ.get(
                "DATABASE_URL",
                f"sqlite:///{self.main_sqlite}",
            )

            # translate sync driver scheme -> async driver
            if database_url.startswith("sqlite:///"):
                async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            elif database_url.startswith("postgresql://"):
                async_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif database_url.startswith("postgres://"):
                async_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
            else:
                async_url = database_url  # assume async-capable already

            # PostgreSQL async pool configuration
            pool_kwargs = {}
            if async_url.startswith("postgresql+psycopg://"):
                pool_kwargs = {
                    "pool_size": 20,
                    "max_overflow": 10,
                    "pool_pre_ping": True,
                    "pool_recycle": 3600,
                }

            self._async_engine = create_async_engine(
                async_url,
                echo=False,
                **pool_kwargs,
            )
            logger.info(f"Async SQLAlchemy engine created: {async_url}")

        return self._async_engine

    def get_async_session_factory(self) -> Any:
        """Get async session factory."""
        if getattr(self, "_async_session_factory", None) is None:
            from sqlalchemy.ext.asyncio import async_sessionmaker

            engine = self.get_async_engine()
            self._async_session_factory = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                autoflush=False,
            )
            logger.info("Async session factory created")

        return self._async_session_factory

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[Any, None]:
        """
        Get an async session with automatic transaction management.

        Usage:
            async with hub.get_async_session() as session:
                result = await session.execute(select(User))
        """
        factory = self.get_async_session_factory()
        session = factory()

        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async transaction failed: {e}")
            raise
        finally:
            await session.close()

    def get_duckdb(self, database: str = "master", timeout: float = 30.0) -> Any:
        """
        Get DuckDB connection with resource limits and tracking.

        Args:
            database: "master" or "analytics"
            timeout: Optional timeout for connection operations

        Returns:
            DuckDB connection with resource limits
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

        conn = duckdb.connect(str(db_path), read_only=False)
        conn.execute("PRAGMA memory_limit='512MB';")
        conn.execute("PRAGMA enable_external_access=false;")
        conn.execute("PRAGMA threads=4;")

        # Track connection for cleanup
        conn_id = f"{database}_{id(conn)}"
        self._active_duckdb_connections[conn_id] = conn

        logger.debug(f"DuckDB connection created: {db_path}")

        return conn

    def release_duckdb(self, conn) -> None:
        """Release and close a DuckDB connection."""
        conn_id = f"master_{id(conn)}" if conn in self._active_duckdb_connections.values() else None
        for key, c in list(self._active_duckdb_connections.items()):
            if c is conn:
                conn_id = key
                break
        if conn_id:
            try:
                conn.close()
                del self._active_duckdb_connections[conn_id]
                logger.debug(f"DuckDB connection released: {conn_id}")
            except Exception as e:
                logger.warning(f"Error releasing DuckDB connection: {e}")

    def get_sqlite(self, database: str = "manual", timeout: float = 30.0) -> Any:
        """
        Get SQLite connection with tracking and timeout.

        Args:
            database: "manual" for manual data
            timeout: Connection timeout in seconds

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

        conn = sqlite3.connect(str(db_path), timeout=timeout)
        conn.row_factory = sqlite3.Row

        # Track connection
        conn_id = f"sqlite_manual_{id(conn)}"
        self._active_sqlite_connections[conn_id] = conn

        logger.debug(f"SQLite connection created: {db_path}")

        return conn

    def release_sqlite(self, conn) -> None:
        """Release a SQLite connection."""
        for key, c in list(self._active_sqlite_connections.items()):
            if c is conn:
                try:
                    conn.close()
                    del self._active_sqlite_connections[key]
                    logger.debug(f"SQLite connection released: {key}")
                except Exception as e:
                    logger.warning(f"Error releasing SQLite connection: {e}")
                break

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
        # Close DuckDB connections
        if self._active_duckdb_connections:
            for name, conn in list(self._active_duckdb_connections.items()):
                try:
                    conn.close()
                    logger.debug(f"DuckDB connection ({name}) closed")
                except Exception as e:
                    logger.warning(f"Error closing DuckDB connection {name}: {e}")
            self._active_duckdb_connections.clear()

        # Close SQLite connections
        if self._active_sqlite_connections:
            for name, conn in list(self._active_sqlite_connections.items()):
                try:
                    conn.close()
                    logger.debug(f"SQLite connection ({name}) closed")
                except Exception as e:
                    logger.warning(f"Error closing SQLite connection {name}: {e}")
            self._active_sqlite_connections.clear()

        # Close SQLAlchemy engine
        if self._sqlalchemy_engine:
            # Close any remaining sessions
            with self._sessions_lock:
                for sid in list(self._active_sessions):
                    logger.warning(f"Session {sid} not properly closed during cleanup")
                self._active_sessions.clear()

            self._sqlalchemy_engine.dispose()
            self._sqlalchemy_engine = None
            self._session_factory = None
            logger.info("SQLAlchemy engine disposed")

        # Close Redis
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None
            logger.info("Redis connection closed")

    def close_duckdb(self, db_name: str):
        """Close a specific DuckDB connection by name."""
        if db_name in self._active_duckdb_connections:
            conn = self._active_duckdb_connections[db_name]
            try:
                conn.close()
                logger.debug(f"DuckDB connection ({db_name}) closed")
            except Exception as e:
                logger.warning(f"Error closing DuckDB connection {db_name}: {e}")
            del self._active_duckdb_connections[db_name]

    def get_session_count(self) -> int:
        """Get count of active sessions (for monitoring)."""
        with self._sessions_lock:
            return len(self._active_sessions)


# Global instance
hub = DataHub()

__all__ = ["DataHub", "hub"]
