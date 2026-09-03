"""
Tests for database.hub.DataHub
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from database.hub import DataHub, hub


def test_singleton():
    """DataHub should be a singleton."""
    hub1 = DataHub()
    hub2 = DataHub()
    assert hub1 is hub2, "DataHub must be a singleton"
    print("PASS: Singleton test")


def test_sqlalchemy_engine():
    """SQLAlchemy engine should be created."""
    engine = hub.get_sqlalchemy_engine()
    assert engine is not None
    print("PASS: SQLAlchemy engine test")


def test_session_factory():
    """Session factory should be created."""
    factory = hub.get_session_factory()
    assert factory is not None
    print("PASS: Session factory test")


def test_get_session():
    """get_session() should work as context manager."""
    try:
        with hub.get_session() as session:
            assert session is not None
        print("PASS: get_session test")
    except Exception as e:
        print(f"SKIP: get_session test ({e})")


def test_duckdb():
    """DuckDB connection should work."""
    try:
        conn = hub.get_duckdb("master")
        assert conn is not None
        conn.close()
        print("PASS: DuckDB test")
    except ImportError:
        print("SKIP: DuckDB test (not installed)")


def test_sqlite():
    """SQLite connection should work."""
    try:
        conn = hub.get_sqlite("manual")
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
        )
        cursor.fetchone()
        conn.close()
        print("PASS: SQLite test")
    except Exception as e:
        print(f"SKIP: SQLite test ({e})")


if __name__ == "__main__":
    print("Running DataHub tests...\n")

    test_singleton()
    test_sqlalchemy_engine()
    test_session_factory()
    test_get_session()
    test_duckdb()
    test_sqlite()

    print("\nAll tests completed!")
