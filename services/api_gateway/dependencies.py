"""Dependency injection for API services."""
from typing import Generator
from sqlalchemy.orm import Session
from engine.hydroma.core.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session for API requests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
