"""
Pytest Configuration for Eco Nojin
═══════════════════════════════════════════════════════════════════════
Root conftest providing fixtures for all integration tests.
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

# Import Base from canonical location
from database.models import Base


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async SQLite in-memory database session for tests.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Import all models so they register with Base.metadata
    try:
        from services.marketplace.models import (
            MarketplaceSeller, MarketplaceProduct,
            MarketplaceOrder, MarketplaceCommissionRule,
        )
    except ImportError as e:
        print(f"[conftest] Warning marketplace: {e}")
    
    try:
        from services.tourism.models import (
            TourismGuide, TourismTour, TourismBooking
        )
    except ImportError as e:
        print(f"[conftest] Warning tourism: {e}")
    
    try:
        from services.landscape.models import (
            LandscapeVillage, LandscapeGovernanceMember,
            LandscapeFund, LandscapeFundDistribution
        )
    except ImportError as e:
        print(f"[conftest] Warning landscape: {e}")
    
    try:
        from services.analytics.models import AnalyticsSnapshot
        from services.auth.models import AuthUser, RefreshToken
        from services.admin.models import AuditLog as AdminAuditLog
        from services.reporting.models import Report
    except ImportError as e:
        print(f"[conftest] Warning phase3 models: {e}")
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def marketplace_service(db_session: AsyncSession):
    """MarketplaceService instance for tests"""
    from services.marketplace.service import MarketplaceService
    return MarketplaceService(db_session)


@pytest_asyncio.fixture
async def tourism_service(db_session: AsyncSession):
    """TourismService instance for tests"""
    from services.tourism.service import TourismService
    return TourismService(db_session)


@pytest_asyncio.fixture
async def landscape_service(db_session: AsyncSession):
    """LandscapeService instance for tests"""
    from services.landscape.service import LandscapeService
    return LandscapeService(db_session)


# ═══════════════════════════════════════════════════════════════
# Phase 3 - Wave 1 Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def analytics_service(db_session: AsyncSession):
    from services.analytics.service import AnalyticsService
    return AnalyticsService(db_session)


@pytest_asyncio.fixture
async def auth_service(db_session: AsyncSession):
    from services.auth.service import AuthService
    return AuthService(db_session)


@pytest_asyncio.fixture
async def admin_service(db_session: AsyncSession):
    from services.admin.service import AdminService
    return AdminService(db_session)


@pytest_asyncio.fixture
async def reporting_service(db_session: AsyncSession):
    from services.reporting.service import ReportingService
    return ReportingService(db_session)


# ═══════════════════════════════════════════════════════════════
# Phase 3 - Wave 2 Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def unified_bot_service(db_session: AsyncSession):
    from services.bots.unified_service import UnifiedBotService
    return UnifiedBotService(db_session)


@pytest_asyncio.fixture
async def satellite_service(db_session: AsyncSession):
    from services.satellite.monitoring_service import SatelliteMonitoringService
    return SatelliteMonitoringService(db_session)


@pytest_asyncio.fixture
async def smart_map_service(db_session: AsyncSession):
    from services.map_engine.smart_service import SmartMapService
    return SmartMapService(db_session)


@pytest_asyncio.fixture
async def telegram_service(db_session: AsyncSession):
    from services.telegram_bot.integration_service import TelegramIntegrationService
    return TelegramIntegrationService(db_session)
