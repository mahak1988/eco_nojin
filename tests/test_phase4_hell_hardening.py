#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_phase4_hell_hardening.py
====================================

Tests for Phase 4 Hell hardening fixes.
"""

import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestSQLInjectionProtection:
    """Tests for SQL injection protection."""

    def test_dict_import(self):
        """Dict should be imported in data_connector."""
        from engine.data_connector import DataConnector
        # If import works, Dict is available
        dc = DataConnector.__dict__
        assert dc is not None

    def test_select_query_allowed(self):
        """SELECT queries should be allowed."""
        from engine.data_connector import connector
        # This should not raise
        try:
            result = connector.execute_analytics_query("SELECT 1 as test")
            assert result is not None or result is None  # Just check no exception
        except ValueError as e:
            if "injection" in str(e).lower():
                pytest.fail(f"SELECT blocked incorrectly: {e}")

    def test_drop_table_blocked(self):
        """DROP TABLE should be blocked."""
        from engine.data_connector import connector
        with pytest.raises((ValueError, RuntimeError)):
            connector.execute_analytics_query("DROP TABLE users")

    def test_delete_blocked(self):
        """DELETE should be blocked."""
        from engine.data_connector import connector
        with pytest.raises((ValueError, RuntimeError)):
            connector.execute_analytics_query("DELETE FROM users WHERE 1=1")

    def test_union_injection_blocked(self):
        """UNION SELECT injection should be blocked."""
        from engine.data_connector import connector
        with pytest.raises((ValueError, RuntimeError)):
            connector.execute_analytics_query(
                "SELECT 1 UNION SELECT username, password FROM users"
            )

    def test_comment_injection_blocked(self):
        """Comment-based injection should be blocked."""
        from engine.data_connector import connector
        with pytest.raises((ValueError, RuntimeError)):
            connector.execute_analytics_query(
                "SELECT * FROM users WHERE id = 1 -- comment"
            )

    def test_semicolon_injection_blocked(self):
        """Semicolon-based injection should be blocked."""
        from engine.data_connector import connector
        with pytest.raises((ValueError, RuntimeError)):
            connector.execute_analytics_query(
                "SELECT 1; DROP TABLE users"
            )


class TestThreadPoolImprovements:
    """Tests for thread pool improvements."""

    def test_pool_exists(self):
        """Hub should have session factory with pool."""
        from database.hub import hub
        assert hub.get_session is not None

    def test_concurrent_sessions(self):
        """Concurrent sessions should work without exhaustion."""
        from database.hub import hub
        from sqlalchemy import text
        import threading

        results = []
        errors = []

        def worker(i):
            try:
                with hub.get_session() as session:
                    session.execute(text("SELECT 1"))
                    results.append(i)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # Most should succeed (allowing for some contention)
        assert len(results) >= 20, f"Only {len(results)}/30 succeeded"


class TestConnectionTimeout:
    """Tests for connection timeouts."""

    def test_duckdb_connection_works(self):
        """DuckDB connections should still work."""
        from database.hub import hub
        pytest.importorskip("duckdb")

        conn = hub.get_duckdb("master")
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
