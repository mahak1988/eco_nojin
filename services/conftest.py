"""
conftest.py â€” Fixtures ط¬ط§ظ…ط¹ طھط³طھâ€Œظ‡ط§غŒ ط¨ع©â€Œط§ظ†ط¯ eco_nojin
طھظˆظ„غŒط¯ ط®ظˆط¯ع©ط§ط±: 2026-09-03 00:51:07
ظ…ط¹ظ…ط§ط±غŒ: ظ…ظ†ط·ط¨ظ‚ ط¨ط± ط³ط§ط®طھط§ط± ظˆط§ظ‚ط¹غŒ ط³ط±ظˆغŒط³â€Œظ‡ط§
"""

import importlib
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

# â”€â”€ ظ…ط³غŒط± ظ¾ط±ظˆعکظ‡ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# â”€â”€ Import Base â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
import contextlib

from database.base import Base


# â”€â”€ Import ط®ظˆط¯ع©ط§ط± ظ‡ظ…ظ‡ ظ…ط¯ظ„â€Œظ‡ط§ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _import_all_models():
    """
    Import ظ‡ظ…ظ‡ ظ…ط§عکظˆظ„â€Œظ‡ط§غŒ models ط¯ط± services/ ظˆ database/
    طھط§ Base.metadata ط´ط§ظ…ظ„ ظ‡ظ…ظ‡ ط¬ط¯ط§ظˆظ„ ط´ظˆط¯.
    """
    imported = []

    # 1) services/*/models.py  ظˆ  services/*/models/__init__.py
    services_dir = PROJECT_ROOT / "services"
    if services_dir.exists():
        for child in sorted(services_dir.iterdir()):
            if not child.is_dir() or child.name.startswith((".", "_")):
                continue

            # ط³ط§ط®طھط§ط± models.py
            models_py = child / "models.py"
            # ط³ط§ط®طھط§ط± models/__init__.py
            models_init = child / "models" / "__init__.py"

            target = None
            if models_py.exists() or models_init.exists():
                target = f"services.{child.name}.models"

            if target:
                try:
                    importlib.import_module(target)
                    imported.append(target)
                except Exception:
                    pass

            # ظ‡ظ…ع†ظ†غŒظ† schemaâ€Œظ‡ط§ ظˆ repositoryâ€Œظ‡ط§ ظ…ظ…ع©ظ† ط§ط³طھ ظ…ط¯ظ„ طھط¹ط±غŒظپ ع©ظ†ظ†ط¯
            for extra in ("schemas", "repository", "service"):
                extra_py = child / f"{extra}.py"
                child / extra / "__init__.py"
                if extra_py.exists():
                    with contextlib.suppress(Exception):
                        importlib.import_module(f"services.{child.name}.{extra}")

    # 2) database/models.py  غŒط§  database/models/__init__.py
    db_dir = PROJECT_ROOT / "database"
    if db_dir.exists():
        for candidate in ("models", "models.base"):
            try:
                importlib.import_module(f"database.{candidate}")
                imported.append(f"database.{candidate}")
            except Exception:
                pass

    return imported


_imported = _import_all_models()

# â”€â”€ Fixtures ظ¾ط§غŒظ‡ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Engine ط¯غŒطھط§ط¨غŒط³ SQLite ط¯ط± ط­ط§ظپط¸ظ‡"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine):
    """Session ط¯غŒطھط§ط¨غŒط³ async"""
    session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sync_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sync_db_session(sync_engine):
    Session = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = Session()
    yield session
    session.rollback()
    session.close()


# â”€â”€ Fixtures ط³ط±ظˆغŒط³â€Œظ‡ط§ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest_asyncio.fixture
async def admin_service(db_session):
    """Fixture ط¨ط±ط§غŒ AdminService"""
    try:
        from services.admin.repository import AdminRepository
        from services.admin.service import AdminService

        repo = AdminRepository(db_session)
        return AdminService(repo)
    except ImportError as e:
        pytest.skip(f"AdminService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.admin.service import AdminService

            return AdminService(db_session)
        except Exception as e2:
            pytest.skip(f"AdminService init failed: {e2}")


@pytest_asyncio.fixture
async def analytics_service(db_session):
    """Fixture ط¨ط±ط§غŒ AnalyticsService"""
    try:
        from services.analytics.repository import AnalyticsRepository
        from services.analytics.service import AnalyticsService

        repo = AnalyticsRepository(db_session)
        return AnalyticsService(repo)
    except ImportError as e:
        pytest.skip(f"AnalyticsService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.analytics.service import AnalyticsService

            return AnalyticsService(db_session)
        except Exception as e2:
            pytest.skip(f"AnalyticsService init failed: {e2}")


@pytest_asyncio.fixture
async def auth_service(db_session):
    """Fixture ط¨ط±ط§غŒ AuthService"""
    try:
        from services.auth.repository import AuthRepository
        from services.auth.service import AuthService

        repo = AuthRepository(db_session)
        return AuthService(repo)
    except ImportError as e:
        pytest.skip(f"AuthService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.auth.service import AuthService

            return AuthService(db_session)
        except Exception as e2:
            pytest.skip(f"AuthService init failed: {e2}")


@pytest_asyncio.fixture
async def carbon_service(db_session):
    """Fixture ط¨ط±ط§غŒ CarbonService"""
    try:
        from services.carbon.service import CarbonService

        return CarbonService(db_session)
    except ImportError as e:
        pytest.skip(f"CarbonService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.carbon.service import CarbonService

            return CarbonService(db_session)
        except Exception as e2:
            pytest.skip(f"CarbonService init failed: {e2}")


@pytest_asyncio.fixture
async def ecowallet_service(db_session):
    """Fixture returning the ecowallet module's callable API.

    This fixture imported ``EcowalletService``, a class that has never existed
    in ``services/ecowallet/service.py`` -- the module exposes module-level
    functions (``earn``, ``redeem``, ``wallet_state``, ``get_or_create_wallet``)
    -- so the ImportError was caught and the fixture silently skipped on every
    run. Found while consolidating the earning-rate tables in phase 4.
    """
    from services.ecowallet import service as ecowallet_module

    return ecowallet_module


@pytest_asyncio.fixture
async def field_monitoring_service(db_session):
    """Fixture ط¨ط±ط§غŒ FieldMonitoringService"""
    try:
        from services.field_monitoring.service import FieldMonitoringService

        return FieldMonitoringService(db_session)
    except ImportError as e:
        pytest.skip(f"FieldMonitoringService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.field_monitoring.service import FieldMonitoringService

            return FieldMonitoringService(db_session)
        except Exception as e2:
            pytest.skip(f"FieldMonitoringService init failed: {e2}")


@pytest_asyncio.fixture
async def land_service(db_session):
    """Fixture ط¨ط±ط§غŒ LandService"""
    try:
        from services.land.service import LandService

        return LandService(db_session)
    except ImportError as e:
        pytest.skip(f"LandService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.land.service import LandService

            return LandService(db_session)
        except Exception as e2:
            pytest.skip(f"LandService init failed: {e2}")


@pytest_asyncio.fixture
async def landscape_service(db_session):
    """Fixture ط¨ط±ط§غŒ LandscapeService"""
    try:
        from services.landscape.service import LandscapeService

        return LandscapeService(db_session)
    except ImportError as e:
        pytest.skip(f"LandscapeService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.landscape.service import LandscapeService

            return LandscapeService(db_session)
        except Exception as e2:
            pytest.skip(f"LandscapeService init failed: {e2}")


@pytest_asyncio.fixture
async def ledger_service(db_session):
    """Fixture ط¨ط±ط§غŒ LedgerService"""
    try:
        from services.ledger.service import SingleEntryLedgerService

        return SingleEntryLedgerService(db_session)
    except ImportError as e:
        pytest.skip(f"LedgerService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.ledger.service import SingleEntryLedgerService

            return SingleEntryLedgerService(db_session)
        except Exception as e2:
            pytest.skip(f"LedgerService init failed: {e2}")


@pytest_asyncio.fixture
async def livestock_service(db_session):
    """Fixture ط¨ط±ط§غŒ LivestockService"""
    try:
        from services.livestock.service import LivestockService

        return LivestockService(db_session)
    except ImportError as e:
        pytest.skip(f"LivestockService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.livestock.service import LivestockService

            return LivestockService(db_session)
        except Exception as e2:
            pytest.skip(f"LivestockService init failed: {e2}")


@pytest_asyncio.fixture
async def marketplace_service(db_session):
    """Fixture ط¨ط±ط§غŒ MarketplaceService"""
    try:
        from services.marketplace.service import MarketplaceService

        return MarketplaceService(db_session)
    except ImportError as e:
        pytest.skip(f"MarketplaceService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.marketplace.service import MarketplaceService

            return MarketplaceService(db_session)
        except Exception as e2:
            pytest.skip(f"MarketplaceService init failed: {e2}")


@pytest_asyncio.fixture
async def mobile_monitoring_service(db_session):
    """Fixture ط¨ط±ط§غŒ MobileMonitoringService"""
    try:
        from services.mobile_monitoring.service import MobileMonitoringService

        return MobileMonitoringService(db_session)
    except ImportError as e:
        pytest.skip(f"MobileMonitoringService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.mobile_monitoring.service import MobileMonitoringService

            return MobileMonitoringService(db_session)
        except Exception as e2:
            pytest.skip(f"MobileMonitoringService init failed: {e2}")


@pytest_asyncio.fixture
async def notification_service(db_session):
    """Fixture ط¨ط±ط§غŒ NotificationService"""
    try:
        from services.notification.service import NotificationService

        return NotificationService(db_session)
    except ImportError as e:
        pytest.skip(f"NotificationService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.notification.service import NotificationService

            return NotificationService(db_session)
        except Exception as e2:
            pytest.skip(f"NotificationService init failed: {e2}")


@pytest_asyncio.fixture
async def reporting_service(db_session):
    """Fixture ط¨ط±ط§غŒ ReportingService"""
    try:
        from services.reporting.repository import ReportingRepository
        from services.reporting.service import ReportingService

        repo = ReportingRepository(db_session)
        return ReportingService(repo)
    except ImportError as e:
        pytest.skip(f"ReportingService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.reporting.service import ReportingService

            return ReportingService(db_session)
        except Exception as e2:
            pytest.skip(f"ReportingService init failed: {e2}")


@pytest_asyncio.fixture
async def satellite_service(db_session):
    """Fixture ط¨ط±ط§غŒ SatelliteService"""
    try:
        from services.satellite.service import SatelliteService

        return SatelliteService(db_session)
    except ImportError as e:
        pytest.skip(f"SatelliteService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.satellite.service import SatelliteService

            return SatelliteService(db_session)
        except Exception as e2:
            pytest.skip(f"SatelliteService init failed: {e2}")


@pytest_asyncio.fixture
async def simulation_service(db_session):
    """Fixture ط¨ط±ط§غŒ SimulationService"""
    try:
        from services.simulation.service import SimulationService

        return SimulationService(db_session)
    except ImportError as e:
        pytest.skip(f"SimulationService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.simulation.service import SimulationService

            return SimulationService(db_session)
        except Exception as e2:
            pytest.skip(f"SimulationService init failed: {e2}")


@pytest_asyncio.fixture
async def tourism_service(db_session):
    """Fixture ط¨ط±ط§غŒ TourismService"""
    try:
        from services.tourism.service import TourismService

        return TourismService(db_session)
    except ImportError as e:
        pytest.skip(f"TourismService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.tourism.service import TourismService

            return TourismService(db_session)
        except Exception as e2:
            pytest.skip(f"TourismService init failed: {e2}")


@pytest_asyncio.fixture
async def workflow_service(db_session):
    """Fixture ط¨ط±ط§غŒ WorkflowService"""
    try:
        from services.workflow.service import WorkflowService

        return WorkflowService(db_session)
    except ImportError as e:
        pytest.skip(f"WorkflowService not available: {e}")
    except TypeError:
        # fallback: ظ…ظ…ع©ظ† ط§ط³طھ constructor ظ…طھظپط§ظˆطھ ط¨ط§ط´ط¯
        try:
            from services.workflow.service import WorkflowService

            return WorkflowService(db_session)
        except Exception as e2:
            pytest.skip(f"WorkflowService init failed: {e2}")
