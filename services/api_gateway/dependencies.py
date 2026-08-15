"""Dependency injection for API services (Phase 0 unification).

Single ``get_db`` delegating to ``database.config`` so API, engine and
models all share one session factory.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from database.config import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session for API requests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
