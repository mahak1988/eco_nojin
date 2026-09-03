#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_phase3_memory_fixes.py
==================================

Tests for Phase 3 memory leak fixes.
"""

import sys
import gc
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestMemoryMonitor:
    """Tests for memory monitoring."""

    def test_memory_tracker_creation(self):
        """MemoryTracker should be created properly."""
        from engine.memory_monitor import MemoryTracker
        tracker = MemoryTracker("test")
        assert tracker.name == "test"
        assert tracker.warn_threshold_mb == 10.0

    def test_memory_tracker_context_manager(self):
        """track_memory context manager should work."""
        from engine.memory_monitor import track_memory
        with track_memory("test_op") as tracker:
            data = [i for i in range(1000)]
        assert tracker.delta_mb >= 0  # Memory increased or stable

    def test_memory_manager(self):
        """MemoryManager should track operations."""
        from engine.memory_monitor import MemoryManager
        manager = MemoryManager()
        manager.track("op1", 5.0)
        manager.track("op2", 15.0)  # Leak
        manager.track("op3", 3.0)

        stats = manager.get_stats()
        assert stats["operations"] == 3
        assert stats["leaks"] == 1  # Only op2 was a leak
        assert stats["leak_rate"] == pytest.approx(1/3)

    def test_memory_monitor_decorator(self):
        """@monitor_memory decorator should work."""
        from engine.memory_monitor import monitor_memory

        @monitor_memory(warn_threshold_mb=100.0)
        def small_operation():
            return sum(range(100))

        result = small_operation()
        assert result == sum(range(100))


class TestResourceManager:
    """Tests for resource management."""

    def test_managed_connection(self):
        """managed_connection should auto-close."""
        from engine.resource_manager import managed_connection
        pytest.importorskip("duckdb")

        with managed_connection("master") as conn:
            result = conn.execute("SELECT 1").fetchone()
            assert result[0] == 1
        # Connection should be back in pool or closed

    def test_managed_session(self):
        """managed_session should work with hub."""
        from engine.resource_manager import managed_session

        with managed_session() as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1"))
            assert result is not None

    def test_cleanup_resources(self):
        """cleanup_resources should force GC."""
        from engine.resource_manager import cleanup_resources

        # Create some garbage
        garbage = [[i for i in range(1000)] for _ in range(100)]
        del garbage

        stats = cleanup_resources()
        assert stats["gc_collected"] >= 0

    def test_get_memory_usage(self):
        """get_memory_usage_mb should return positive value."""
        from engine.resource_manager import get_memory_usage_mb
        pytest.importorskip("psutil")

        usage = get_memory_usage_mb()
        assert usage > 0  # Process should use some memory


class TestConnectionPooling:
    """Tests for DuckDB connection pooling."""

    def test_get_duckdb_pooled_exists(self):
        """Hub should have pooled connection methods."""
        from database.hub import hub

        assert hasattr(hub, "get_duckdb_pooled")
        assert hasattr(hub, "return_duckdb_pooled")

    def test_pooled_connection_reuse(self):
        """Pooled connections should be reused."""
        from database.hub import hub
        pytest.importorskip("duckdb")

        if not hasattr(hub, "get_duckdb_pooled"):
            pytest.skip("Pool not implemented")

        # Get and return connection
        conn1 = hub.get_duckdb_pooled("master")
        hub.return_duckdb_pooled(conn1, "master")

        # Get again - should be same connection
        conn2 = hub.get_duckdb_pooled("master")
        assert conn1 is conn2
        hub.return_duckdb_pooled(conn2, "master")

    def test_pool_cleanup(self):
        """Pool cleanup should close all connections."""
        from database.hub import hub
        pytest.importorskip("duckdb")

        if not hasattr(hub, "get_duckdb_pooled"):
            pytest.skip("Pool not implemented")

        # Create multiple connections
        conns = [hub.get_duckdb_pooled("master") for _ in range(3)]
        for conn in conns:
            hub.return_duckdb_pooled(conn, "master")

        # Cleanup should not raise
        hub.close_all()


class TestMemoryLeakFixes:
    """Tests to verify memory leaks are fixed."""

    def test_100_queries_no_leak(self):
        """100 queries should not leak significantly."""
        from engine.data_connector import connector
        from engine.memory_monitor import track_memory

        pytest.importorskip("duckdb")

        with track_memory("100_queries", warn_threshold_mb=5.0) as tracker:
            for i in range(100):
                connector.execute_analytics_query("SELECT 1")
                if i % 10 == 0:
                    gc.collect()

        # Should not leak significantly
        assert tracker.delta_mb < 5.0, f"Memory leak: {tracker.delta_mb:.1f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])