"""دیتابیس تست مشترک با StaticPool"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# import همه مدل‌ها
import engine.hydroma.biofertilizer.models
import engine.hydroma.core.models
import engine.land.models
from database.base import Base  # از models import می‌کنیم

engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=engine, checkfirst=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
TEST_SESSION_FACTORY = SessionLocal
