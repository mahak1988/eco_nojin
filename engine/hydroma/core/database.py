"""Database configuration and session management for HyDroMa engine."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Research mode uses SQLite. Production will swap to PostGIS connection string.
DATABASE_URL = "sqlite:///./hydroma_research.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
