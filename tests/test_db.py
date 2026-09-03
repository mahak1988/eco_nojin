"""دیتابیس تست مشترک با StaticPool"""
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from database.base import Base # از models import می‌کنیم

# import همه مدل‌ها
import database.models
import services.auth.models
import engine.land.models
import engine.hydroma.core.models
import engine.hydroma.biofertilizer.models

engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
TEST_SESSION_FACTORY = SessionLocal