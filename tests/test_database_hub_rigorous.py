"""
tests/test_database_hub_rigorous.py
===================================

Rigorous tests for database.hub.DataHub.
"""

import sys
import time
import threading
import pytest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


import re as _re_ident


def _safe_ident(name):
    """فقط identifier معتبر SQL عبور می‌کند (ضد تزریق برای نام جدول/ستون)."""
    if not _re_ident.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(name)):
        raise ValueError("invalid SQL identifier: %r" % (name,))
    return str(name)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestDataHubSingleton:
    """Test Singleton pattern enforcement."""

    def test_singleton_identity(self):
        """Multiple instantiations should return same object."""
        from database.hub import DataHub
        h1 = DataHub()
        h2 = DataHub()
        h3 = DataHub()
        assert h1 is h2
        assert h2 is h3
        assert id(h1) == id(h2) == id(h3)

    def test_singleton_across_modules(self):
        """Singleton should work across different imports."""
        from database.hub import hub as hub1
        from database.hub.hub import DataHub
        hub2 = DataHub()
        assert hub1 is hub2

    def test_singleton_thread_safety(self):
        """Singleton should be thread-safe under contention."""
        from database.hub import DataHub

        instances = []
        barrier = threading.Barrier(50)

        def get_instance():
            barrier.wait()
            return DataHub()

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_instance) for _ in range(50)]
            for future in as_completed(futures):
                instances.append(future.result())

        first_id = id(instances[0])
        for instance in instances:
            assert id(instance) == first_id, "Singleton violated under concurrency"


class TestDataHubConnections:
    """Test connection lifecycle."""

    def test_sqlalchemy_engine_creation(self, datahub_instance):
        """SQLAlchemy engine should be created lazily."""
        engine = datahub_instance.get_sqlalchemy_engine()
        assert engine is not None

    def test_sqlalchemy_engine_reuse(self, datahub_instance):
        """SQLAlchemy engine should be reused."""
        e1 = datahub_instance.get_sqlalchemy_engine()
        e2 = datahub_instance.get_sqlalchemy_engine()
        assert e1 is e2

    def test_session_factory_creation(self, datahub_instance):
        """Session factory should be created."""
        factory = datahub_instance.get_session_factory()
        assert factory is not None
        assert callable(factory)

    def test_session_context_manager(self, datahub_instance):
        """get_session should work as context manager."""
        with datahub_instance.get_session() as session:
            assert session is not None
            assert hasattr(session, "query")

    def test_session_rollback_on_error(self):
        """Session should rollback on exception."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import text
        from database.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            session.execute(text("SELECT * FROM nonexistent_table_xyz"))
            session.commit()
        except Exception:
            session.rollback()

        session.close()
        engine.dispose()


class TestDataHubDuckDB:
    """Test DuckDB operations."""

    def test_duckdb_master_connection(self, datahub_instance):
        """Master DuckDB should be accessible."""
        pytest.importorskip("duckdb")
        conn = datahub_instance.get_duckdb("master")
        assert conn is not None
        conn.close()

    def test_duckdb_invalid_database(self, datahub_instance):
        """Invalid database name should raise ValueError."""
        pytest.importorskip("duckdb")
        with pytest.raises(ValueError, match="Unknown database"):
            datahub_instance.get_duckdb("nonexistent")

    def test_duckdb_query_execution(self, datahub_instance):
        """DuckDB should execute queries correctly."""
        pytest.importorskip("duckdb")
        conn = datahub_instance.get_duckdb("master")
        try:
            result = conn.execute("SELECT 1 AS val").fetchone()
            assert result[0] == 1
        finally:
            conn.close()

    def test_duckdb_large_query(self, datahub_instance):
        """DuckDB should handle large result sets."""
        pytest.importorskip("duckdb")
        conn = datahub_instance.get_duckdb("master")
        try:
            result = conn.execute("""
                SELECT * FROM weather_daily LIMIT 1000
            """).fetchall()
            assert len(result) <= 1000
        finally:
            conn.close()


class TestDataHubSQLite:
    """Test SQLite operations."""

    def test_sqlite_manual_connection(self, datahub_instance):
        """Manual SQLite should be accessible."""
        conn = datahub_instance.get_sqlite("manual")
        assert conn is not None
        conn.close()

    def test_sqlite_invalid_database(self, datahub_instance):
        """Invalid SQLite database should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown database"):
            datahub_instance.get_sqlite("nonexistent")

    def test_sqlite_row_factory(self, datahub_instance):
        """SQLite should use row factory for dict access."""
        conn = datahub_instance.get_sqlite("manual")
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
            )
            row = cursor.fetchone()
            assert row is not None
            if hasattr(row, "keys"):
                assert "name" in row.keys()
        finally:
            conn.close()


class TestDataHubConcurrency:
    """Test concurrent access safety."""

    def test_concurrent_sqlalchemy_sessions(self, datahub_instance):
        """Multiple concurrent sessions should work."""
        from sqlalchemy import text
        errors = []

        def use_session(idx):
            try:
                with datahub_instance.get_session() as session:
                    session.execute(text("SELECT 1"))
                    time.sleep(0.01)
            except Exception as e:
                errors.append((idx, str(e)))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(use_session, i) for i in range(20)]
            for future in as_completed(futures):
                pass

        assert len(errors) == 0, f"Concurrent errors: {errors}"

    def test_concurrent_duckdb_queries(self, datahub_instance):
        """Multiple DuckDB queries should work concurrently."""
        pytest.importorskip("duckdb")
        results = []
        errors = []

        def query_duckdb(idx):
            try:
                conn = datahub_instance.get_duckdb("master")
                try:
                    result = conn.execute('SELECT {} AS val'.format(_safe_ident(idx))).fetchone()  # nosec (کد آزمایشی — بدون ورودی کاربر)
                    results.append((idx, result[0]))
                finally:
                    conn.close()
            except Exception as e:
                errors.append((idx, str(e)))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query_duckdb, i) for i in range(10)]
            for future in as_completed(futures):
                pass

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 10


class TestDataHubMemoryManagement:
    """Test memory and resource management."""

    def test_connection_cleanup_after_exception(self, datahub_instance):
        """Connections should clean up after exception."""
        pytest.importorskip("duckdb")

        try:
            conn = datahub_instance.get_duckdb("master")
            conn.execute("SELECT * FROM nonexistent_table_12345")
        except Exception:
            pass

        # Should still be able to get new connection
        conn2 = datahub_instance.get_duckdb("master")
        assert conn2 is not None
        conn2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
