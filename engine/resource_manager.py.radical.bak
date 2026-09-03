#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.resource_manager
=======================

Resource management with automatic cleanup for Eco Nojin.

Usage:
    from engine.resource_manager import managed_connection

    # Auto-closed connection
    with managed_connection("master") as conn:
        result = conn.execute("SELECT 1")

Author: Eco Nojin Architecture Team
Version: 3.0.0
"""

import gc
from contextlib import contextmanager
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


@contextmanager
def managed_connection(database: str = "master", pooled: bool = True):
    """
    Context manager for DuckDB connections.

    Automatically returns connection to pool (or closes it) on exit.

    Args:
        database: "master" or "analytics"
        pooled: Whether to use connection pooling

    Usage:
        with managed_connection("master") as conn:
            result = conn.execute("SELECT * FROM weather_daily")
        # Connection automatically returned to pool here
    """
    from database.hub import hub

    conn = None
    try:
        if pooled and hasattr(hub, "get_duckdb_pooled"):
            conn = hub.get_duckdb_pooled(database)
            try:
                yield conn
            finally:
                hub.return_duckdb_pooled(conn, database)
        else:
            conn = hub.get_duckdb(database)
            try:
                yield conn
            finally:
                conn.close()
    except Exception as e:
        logger.error(f"Error in managed connection: {e}")
        raise


@contextmanager
def managed_session():
    """Context manager for SQLAlchemy sessions."""
    from database.hub import hub

    with hub.get_session() as session:
        yield session


def cleanup_resources() -> Dict:
    """
    Force cleanup of all resources.

    Returns:
        Dictionary with cleanup statistics
    """
    from database.hub import hub

    stats = {
        "gc_collected": 0,
        "connections_closed": 0,
        "sessions_closed": 0,
    }

    # Force garbage collection
    for _ in range(3):
        stats["gc_collected"] += gc.collect()

    # Close all connections
    try:
        hub.close_all()
        stats["connections_closed"] = 1
    except Exception as e:
        logger.warning(f"Error closing hub connections: {e}")

    logger.info(f"Resource cleanup: {stats}")
    return stats


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


__all__ = [
    "managed_connection",
    "managed_session",
    "cleanup_resources",
    "get_memory_usage_mb",
]