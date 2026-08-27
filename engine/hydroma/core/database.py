"""Database access for the HyDroMa engine (Phase 0 unification).

Delegates to ``database.config`` so the whole project shares one
engine / Base / session. Backward compatible: existing imports
(``from engine.hydroma.core.database import Base, engine``) keep working.
"""

from database.config import SessionLocal, engine, get_db, init_db
from database.models import Base

__all__ = ["Base", "SessionLocal", "engine", "get_db", "init_db"]
