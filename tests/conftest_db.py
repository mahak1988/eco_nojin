"""
tests/conftest_db.py
====================

Shared fixtures for rigorous database tests.
"""

import sys
import time
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Provide project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def datahub_instance():
    """Provide DataHub singleton instance."""
    from database.hub import DataHub
    instance = DataHub()
    yield instance
    instance.close_all()


@pytest.fixture(scope="session")
def connector_instance():
    """Provide DataConnector singleton instance."""
    from engine.data_connector import connector
    return connector


@pytest.fixture
def fresh_sqlite_session():
    """Provide fresh SQLAlchemy session with rollback."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.base import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    engine.dispose()


@pytest.fixture
def benchmark_timer():
    """Context manager for precise timing."""
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
