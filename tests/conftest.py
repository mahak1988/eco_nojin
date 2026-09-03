"""
tests/conftest.py
=================

Shared fixtures for all tests.
Uses centralized DataHub for database access.
"""

import sys
import os
import pytest
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import DataHub
from database.hub import hub
from database.base import Base


# ── Compatibility aliases ────────────────────────────────────────
# For tests that still use old-style SessionLocal
SessionLocal = hub.get_session_factory()
engine = hub.get_sqlalchemy_engine()
TEST_SESSION_FACTORY = hub.get_session_factory()


# ── Project-level fixtures ───────────────────────────────────────

@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def datahub():
    """DataHub singleton instance."""
    return hub


@pytest.fixture(scope="function")
def db_session():
    """
    Provide a database session for tests.
    
    Automatically rolls back after each test.
    """
    with hub.get_session() as session:
        yield session


@pytest.fixture(scope="session")
def duckdb_master():
    """Provide DuckDB master connection."""
    try:
        conn = hub.get_duckdb("master")
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"DuckDB not available: {e}")


@pytest.fixture(scope="session")
def sqlite_manual():
    """Provide SQLite manual connection."""
    conn = hub.get_sqlite("manual")
    yield conn
    conn.close()


@pytest.fixture
def fresh_session():
    """
    Provide a fresh in-memory session for isolated tests.
    
    Creates all tables in memory, runs test, then discards.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Import all models to register them with Base
    import database.models  # noqa: F401

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    engine.dispose()


@pytest.fixture
def mock_request():
    """Mock FastAPI request for API tests."""
    class MockRequest:
        def __init__(self):
            self.state = type("State", (), {})()
    return MockRequest()


# ── Aliases for backward compatibility ─────────────────────────────
@pytest.fixture(scope="session")
def datahub_instance():
    """Alias for datahub fixture (for backward compatibility)."""
    return hub


@pytest.fixture(scope="session")
def connector_instance():
    """Provide DataConnector singleton instance."""
    from engine.data_connector import connector
    return connector


# ── Benchmark timer fixture ────────────────────────────────────────
@pytest.fixture
def benchmark_timer():
    """Context manager for precise timing in benchmarks."""
    import time
    
    class Timer:
        def __init__(self):
            self.start = None
            self.elapsed = None
        
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        
        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start
    
    return Timer()
