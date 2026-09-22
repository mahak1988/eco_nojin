"""
Database Module - Facade Pattern

This file provides a unified interface for backward compatibility.

Allowed usage:
    from database.base import Base              # direct
    from database.config import engine, get_db     # direct
    from database.base import Base, engine, get_db     # facade (recommended)
"""

from database.base import Base

try:
    from database.config import (
        SessionLocal,
        engine,
        get_db,
    )
except ImportError:
    pass

try:
    from database.config import init_db
except ImportError:
    pass

__all__ = ["Base", "SessionLocal", "engine", "get_db", "init_db"]
