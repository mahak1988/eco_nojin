"""Database configuration — single source of truth (Phase 0).

Unified SQLAlchemy setup driven by ``engine.hydroma.config.settings``.
Fixes Phase-0 finding: two parallel SQLite databases
(``database/config.py`` vs ``engine/hydroma/core/database.py``) are
merged into one engine, one Base, one session factory.

Production swaps DATABASE_URL to PostGIS via .env (docker-compose).
"""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from engine.hydroma.config.settings import get_settings

settings = get_settings()

# Resolve SQLite relative paths against the repository root
_DB_URL = settings.database_url
if _DB_URL.startswith("sqlite:///") and not _DB_URL.startswith("sqlite:////"):
    _db_path = _DB_URL.replace("sqlite:///", "", 1)
    _abs = (Path(__file__).parent.parent / _db_path).resolve()
    _abs.parent.mkdir(parents=True, exist_ok=True)
    _DB_URL = f"sqlite:///{_abs.as_posix()}"

Base = declarative_base()

engine = create_engine(
    _DB_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _DB_URL.startswith("sqlite") else {},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _record):
    """SQLite performance/safety pragmas (WAL, FK enforcement)."""
    if _DB_URL.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: transactional session, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> list:
    """Create all tables (research bootstrap; use alembic for migrations)."""
    from database import models  # noqa: F401  (register ORM models)
    from engine.hydroma.core import models as engine_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    return sorted(Base.metadata.tables.keys())
