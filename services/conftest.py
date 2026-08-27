import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.base import Base

# Import service modules to register their models
from services.landscape.service import LandscapeService
from services.marketplace.service import MarketplaceService
from services.tourism.service import TourismService


@pytest_asyncio.fixture
async def db_session():
    """ساخت دیتابیس SQLite درون‌حافظه‌ای برای تست‌های async."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session

    await engine.dispose()

@pytest.fixture
def landscape_service(db_session):
    return LandscapeService(db=db_session)

@pytest.fixture
def marketplace_service(db_session):
    return MarketplaceService(db=db_session)

@pytest.fixture
def tourism_service(db_session):
    return TourismService(db=db_session)
