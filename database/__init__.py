"""
Database Module - Facade Pattern

This file provides a unified interface for backward compatibility.

Allowed usage:
    from database.base import Base              # direct
    from database.config import engine, get_db     # direct
    from database.base import Base, engine, get_db     # facade (recommended)
"""

from database.base import Base  # noqa: F401

try:
    from database.config import (  # noqa: F401
        engine,
        SessionLocal,
        get_db,
    )
except ImportError:
    pass

try:
    from database.config import init_db  # noqa: F401
except ImportError:
    pass

__all__ = ['Base', 'engine', 'SessionLocal', 'get_db', 'init_db']
