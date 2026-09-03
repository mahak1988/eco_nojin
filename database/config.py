"""
database.config
===============

Compatibility layer for database configuration.

This module provides backward compatibility for code that imports
from database.config. Internally, it uses the centralized DataHub.

DEPRECATED: Use database.hub directly instead:
    from database.hub import hub
    with hub.get_session() as session:
        # ...

Author: Eco Nojin Architecture Team
"""

from database.hub import hub
from database.base import Base


# Compatibility: SessionLocal
SessionLocal = hub.get_session_factory()


def get_db():
    """
    Get a database session.
    
    DEPRECATED: Use hub.get_session() instead.
    
    Usage:
        with hub.get_session() as session:
            # ...
    """
    with hub.get_session() as session:
        yield session


def init_db():
    """
    Initialize database tables.
    
    Creates all tables defined in Base.metadata.
    """
    engine = hub.get_sqlalchemy_engine()
    Base.metadata.create_all(bind=engine)


# Compatibility: get_engine
def get_engine():
    """
    Get SQLAlchemy engine.
    
    DEPRECATED: Use hub.get_sqlalchemy_engine() instead.
    """
    return hub.get_sqlalchemy_engine()


__all__ = [
    "SessionLocal",
    "get_db",
    "init_db",
    "get_engine",
    "hub",
    "Base",
]
