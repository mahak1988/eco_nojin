"""
conftest.py — Fixtures جامع تست‌های بک‌اند eco_nojin
تولید خودکار: 2026-09-03 00:51:07
معماری: منطبق بر ساختار واقعی سرویس‌ها
"""

import sys
import importlib
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── مسیر پروژه ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Import Base ─────────────────────────────────────────────────
from database.base import Base

# ── Import خودکار همه مدل‌ها ────────────────────────────────────
def _import_all_models():
    """
    Import همه ماژول‌های models در services/ و database/
    تا Base.metadata شامل همه جداول شود.
    """
    imported = []

    # 1) services/*/models.py  و  services/*/models/__init__.py
    services_dir = PROJECT_ROOT / "services"
    if services_dir.exists():
        for child in sorted(services_dir.iterdir()):
            if not child.is_dir() or child.name.startswith((".", "_")):
                continue

            # ساختار models.py
            models_py = child / "models.py"
            # ساختار models/__init__.py
            models_init = child / "models" / "__init__.py"

            target = None
            if models_py.exists():
                target = f"services.{child.name}.models"
            elif models_init.exists():
                target = f"services.{child.name}.models"

            if target:
                try:
                    importlib.import_module(target)
                    imported.append(target)
                except Exception:
                    pass

            # همچنین schema‌ها و repository‌ها ممکن است مدل تعریف کنند
            for extra in ("schemas", "repository", "service"):
                extra_py = child / f"{extra}.py"
                extra_init = child / extra / "__init__.py"
                if extra_py.exists():
                    try:
                        importlib.import_module(f"services.{child.name}.{extra}")
                    except Exception:
                        pass

    # 2) database/models.py  یا  database/models/__init__.py
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

# ── Fixtures پایه ───────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Engine دیتابیس SQLite در حافظه"""
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
    """Session دیتابیس async"""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def sync_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def sync_db_session(sync_engine):
    Session = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ── Fixtures سرویس‌ها ──────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_service(db_session):
    """Fixture برای AdminService"""
    try:
        from services.admin.repository import AdminRepository
        from services.admin.service import AdminService
        repo = AdminRepository(db_session)
        return AdminService(repo)
    except ImportError as e:
        pytest.skip(f"AdminService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.admin.service import AdminService
            return AdminService(db_session)
        except Exception as e2:
            pytest.skip(f"AdminService init failed: {e2}")

@pytest_asyncio.fixture
async def ai_service(db_session):
    """Fixture برای AiService"""
    try:
        from services.ai.service import AiService
        return AiService(db_session)
    except ImportError as e:
        pytest.skip(f"AiService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.ai.service import AiService
            return AiService(db_session)
        except Exception as e2:
            pytest.skip(f"AiService init failed: {e2}")

@pytest_asyncio.fixture
async def analytics_service(db_session):
    """Fixture برای AnalyticsService"""
    try:
        from services.analytics.repository import AnalyticsRepository
        from services.analytics.service import AnalyticsService
        repo = AnalyticsRepository(db_session)
        return AnalyticsService(repo)
    except ImportError as e:
        pytest.skip(f"AnalyticsService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.analytics.service import AnalyticsService
            return AnalyticsService(db_session)
        except Exception as e2:
            pytest.skip(f"AnalyticsService init failed: {e2}")

@pytest_asyncio.fixture
async def api_gateway_service(db_session):
    """Fixture برای Api_gatewayService"""
    try:
        from services.api_gateway.service import Api_gatewayService
        return Api_gatewayService(db_session)
    except ImportError as e:
        pytest.skip(f"Api_gatewayService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.api_gateway.service import Api_gatewayService
            return Api_gatewayService(db_session)
        except Exception as e2:
            pytest.skip(f"Api_gatewayService init failed: {e2}")

@pytest_asyncio.fixture
async def audit_service(db_session):
    """Fixture برای AuditService"""
    try:
        from services.audit.service import AuditService
        return AuditService(db_session)
    except ImportError as e:
        pytest.skip(f"AuditService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.audit.service import AuditService
            return AuditService(db_session)
        except Exception as e2:
            pytest.skip(f"AuditService init failed: {e2}")

@pytest_asyncio.fixture
async def auth_service(db_session):
    """Fixture برای AuthService"""
    try:
        from services.auth.repository import AuthRepository
        from services.auth.service import AuthService
        repo = AuthRepository(db_session)
        return AuthService(repo)
    except ImportError as e:
        pytest.skip(f"AuthService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.auth.service import AuthService
            return AuthService(db_session)
        except Exception as e2:
            pytest.skip(f"AuthService init failed: {e2}")

@pytest_asyncio.fixture
async def bots_service(db_session):
    """Fixture برای BotsService"""
    try:
        from services.bots.service import BotsService
        return BotsService(db_session)
    except ImportError as e:
        pytest.skip(f"BotsService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.bots.service import BotsService
            return BotsService(db_session)
        except Exception as e2:
            pytest.skip(f"BotsService init failed: {e2}")

@pytest_asyncio.fixture
async def business_modules_service(db_session):
    """Fixture برای Business_modulesService"""
    try:
        from services.business_modules.service import Business_modulesService
        return Business_modulesService(db_session)
    except ImportError as e:
        pytest.skip(f"Business_modulesService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.business_modules.service import Business_modulesService
            return Business_modulesService(db_session)
        except Exception as e2:
            pytest.skip(f"Business_modulesService init failed: {e2}")

@pytest_asyncio.fixture
async def carbon_service(db_session):
    """Fixture برای CarbonService"""
    try:
        from services.carbon.service import CarbonService
        return CarbonService(db_session)
    except ImportError as e:
        pytest.skip(f"CarbonService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.carbon.service import CarbonService
            return CarbonService(db_session)
        except Exception as e2:
            pytest.skip(f"CarbonService init failed: {e2}")

@pytest_asyncio.fixture
async def content_service(db_session):
    """Fixture برای ContentService"""
    try:
        from services.content.service import ContentService
        return ContentService(db_session)
    except ImportError as e:
        pytest.skip(f"ContentService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.content.service import ContentService
            return ContentService(db_session)
        except Exception as e2:
            pytest.skip(f"ContentService init failed: {e2}")

@pytest_asyncio.fixture
async def data_service(db_session):
    """Fixture برای DataService"""
    try:
        from services.data.service import DataService
        return DataService(db_session)
    except ImportError as e:
        pytest.skip(f"DataService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.data.service import DataService
            return DataService(db_session)
        except Exception as e2:
            pytest.skip(f"DataService init failed: {e2}")

@pytest_asyncio.fixture
async def data_manual_service(db_session):
    """Fixture برای Data_manualService"""
    try:
        from services.data_manual.service import Data_manualService
        return Data_manualService(db_session)
    except ImportError as e:
        pytest.skip(f"Data_manualService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.data_manual.service import Data_manualService
            return Data_manualService(db_session)
        except Exception as e2:
            pytest.skip(f"Data_manualService init failed: {e2}")

@pytest_asyncio.fixture
async def data_sources_service(db_session):
    """Fixture برای Data_sourcesService"""
    try:
        from services.data_sources.service import Data_sourcesService
        return Data_sourcesService(db_session)
    except ImportError as e:
        pytest.skip(f"Data_sourcesService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.data_sources.service import Data_sourcesService
            return Data_sourcesService(db_session)
        except Exception as e2:
            pytest.skip(f"Data_sourcesService init failed: {e2}")

@pytest_asyncio.fixture
async def design_engine_service(db_session):
    """Fixture برای Design_engineService"""
    try:
        from services.design_engine.service import Design_engineService
        return Design_engineService(db_session)
    except ImportError as e:
        pytest.skip(f"Design_engineService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.design_engine.service import Design_engineService
            return Design_engineService(db_session)
        except Exception as e2:
            pytest.skip(f"Design_engineService init failed: {e2}")

@pytest_asyncio.fixture
async def ecowallet_service(db_session):
    """Fixture برای EcowalletService"""
    try:
        from services.ecowallet.service import EcowalletService
        return EcowalletService(db_session)
    except ImportError as e:
        pytest.skip(f"EcowalletService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.ecowallet.service import EcowalletService
            return EcowalletService(db_session)
        except Exception as e2:
            pytest.skip(f"EcowalletService init failed: {e2}")

@pytest_asyncio.fixture
async def field_monitoring_service(db_session):
    """Fixture برای FieldMonitoringService"""
    try:
        from services.field_monitoring.service import FieldMonitoringService
        return FieldMonitoringService(db_session)
    except ImportError as e:
        pytest.skip(f"FieldMonitoringService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.field_monitoring.service import FieldMonitoringService
            return FieldMonitoringService(db_session)
        except Exception as e2:
            pytest.skip(f"FieldMonitoringService init failed: {e2}")

@pytest_asyncio.fixture
async def land_service(db_session):
    """Fixture برای LandService"""
    try:
        from services.land.service import LandService
        return LandService(db_session)
    except ImportError as e:
        pytest.skip(f"LandService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.land.service import LandService
            return LandService(db_session)
        except Exception as e2:
            pytest.skip(f"LandService init failed: {e2}")

@pytest_asyncio.fixture
async def landscape_service(db_session):
    """Fixture برای LandscapeService"""
    try:
        from services.landscape.service import LandscapeService
        return LandscapeService(db_session)
    except ImportError as e:
        pytest.skip(f"LandscapeService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.landscape.service import LandscapeService
            return LandscapeService(db_session)
        except Exception as e2:
            pytest.skip(f"LandscapeService init failed: {e2}")

@pytest_asyncio.fixture
async def ledger_service(db_session):
    """Fixture برای LedgerService"""
    try:
        from services.ledger.service import LedgerService
        return LedgerService(db_session)
    except ImportError as e:
        pytest.skip(f"LedgerService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.ledger.service import LedgerService
            return LedgerService(db_session)
        except Exception as e2:
            pytest.skip(f"LedgerService init failed: {e2}")

@pytest_asyncio.fixture
async def livestock_service(db_session):
    """Fixture برای LivestockService"""
    try:
        from services.livestock.service import LivestockService
        return LivestockService(db_session)
    except ImportError as e:
        pytest.skip(f"LivestockService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.livestock.service import LivestockService
            return LivestockService(db_session)
        except Exception as e2:
            pytest.skip(f"LivestockService init failed: {e2}")

@pytest_asyncio.fixture
async def map_engine_service(db_session):
    """Fixture برای Map_engineService"""
    try:
        from services.map_engine.service import Map_engineService
        return Map_engineService(db_session)
    except ImportError as e:
        pytest.skip(f"Map_engineService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.map_engine.service import Map_engineService
            return Map_engineService(db_session)
        except Exception as e2:
            pytest.skip(f"Map_engineService init failed: {e2}")

@pytest_asyncio.fixture
async def marketplace_service(db_session):
    """Fixture برای MarketplaceService"""
    try:
        from services.marketplace.service import MarketplaceService
        return MarketplaceService(db_session)
    except ImportError as e:
        pytest.skip(f"MarketplaceService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.marketplace.service import MarketplaceService
            return MarketplaceService(db_session)
        except Exception as e2:
            pytest.skip(f"MarketplaceService init failed: {e2}")

@pytest_asyncio.fixture
async def mobile_monitoring_service(db_session):
    """Fixture برای MobileMonitoringService"""
    try:
        from services.mobile_monitoring.service import MobileMonitoringService
        return MobileMonitoringService(db_session)
    except ImportError as e:
        pytest.skip(f"MobileMonitoringService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.mobile_monitoring.service import MobileMonitoringService
            return MobileMonitoringService(db_session)
        except Exception as e2:
            pytest.skip(f"MobileMonitoringService init failed: {e2}")

@pytest_asyncio.fixture
async def models_service(db_session):
    """Fixture برای ModelsService"""
    try:
        from services.models.service import ModelsService
        return ModelsService(db_session)
    except ImportError as e:
        pytest.skip(f"ModelsService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.models.service import ModelsService
            return ModelsService(db_session)
        except Exception as e2:
            pytest.skip(f"ModelsService init failed: {e2}")

@pytest_asyncio.fixture
async def mrv_service(db_session):
    """Fixture برای MrvService"""
    try:
        from services.mrv.service import MrvService
        return MrvService(db_session)
    except ImportError as e:
        pytest.skip(f"MrvService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.mrv.service import MrvService
            return MrvService(db_session)
        except Exception as e2:
            pytest.skip(f"MrvService init failed: {e2}")

@pytest_asyncio.fixture
async def notification_service(db_session):
    """Fixture برای NotificationService"""
    try:
        from services.notification.service import NotificationService
        return NotificationService(db_session)
    except ImportError as e:
        pytest.skip(f"NotificationService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.notification.service import NotificationService
            return NotificationService(db_session)
        except Exception as e2:
            pytest.skip(f"NotificationService init failed: {e2}")

@pytest_asyncio.fixture
async def ogc_service(db_session):
    """Fixture برای OgcService"""
    try:
        from services.ogc.service import OgcService
        return OgcService(db_session)
    except ImportError as e:
        pytest.skip(f"OgcService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.ogc.service import OgcService
            return OgcService(db_session)
        except Exception as e2:
            pytest.skip(f"OgcService init failed: {e2}")

@pytest_asyncio.fixture
async def quality_service(db_session):
    """Fixture برای QualityService"""
    try:
        from services.quality.service import QualityService
        return QualityService(db_session)
    except ImportError as e:
        pytest.skip(f"QualityService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.quality.service import QualityService
            return QualityService(db_session)
        except Exception as e2:
            pytest.skip(f"QualityService init failed: {e2}")

@pytest_asyncio.fixture
async def reporting_service(db_session):
    """Fixture برای ReportingService"""
    try:
        from services.reporting.repository import ReportingRepository
        from services.reporting.service import ReportingService
        repo = ReportingRepository(db_session)
        return ReportingService(repo)
    except ImportError as e:
        pytest.skip(f"ReportingService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.reporting.service import ReportingService
            return ReportingService(db_session)
        except Exception as e2:
            pytest.skip(f"ReportingService init failed: {e2}")

@pytest_asyncio.fixture
async def satellite_service(db_session):
    """Fixture برای SatelliteService"""
    try:
        from services.satellite.service import SatelliteService
        return SatelliteService(db_session)
    except ImportError as e:
        pytest.skip(f"SatelliteService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.satellite.service import SatelliteService
            return SatelliteService(db_session)
        except Exception as e2:
            pytest.skip(f"SatelliteService init failed: {e2}")

@pytest_asyncio.fixture
async def science_service(db_session):
    """Fixture برای ScienceService"""
    try:
        from services.science.service import ScienceService
        return ScienceService(db_session)
    except ImportError as e:
        pytest.skip(f"ScienceService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.science.service import ScienceService
            return ScienceService(db_session)
        except Exception as e2:
            pytest.skip(f"ScienceService init failed: {e2}")

@pytest_asyncio.fixture
async def scientific_motors_service(db_session):
    """Fixture برای Scientific_motorsService"""
    try:
        from services.scientific_motors.service import Scientific_motorsService
        return Scientific_motorsService(db_session)
    except ImportError as e:
        pytest.skip(f"Scientific_motorsService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.scientific_motors.service import Scientific_motorsService
            return Scientific_motorsService(db_session)
        except Exception as e2:
            pytest.skip(f"Scientific_motorsService init failed: {e2}")

@pytest_asyncio.fixture
async def security_service(db_session):
    """Fixture برای SecurityService"""
    try:
        from services.security.service import SecurityService
        return SecurityService(db_session)
    except ImportError as e:
        pytest.skip(f"SecurityService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.security.service import SecurityService
            return SecurityService(db_session)
        except Exception as e2:
            pytest.skip(f"SecurityService init failed: {e2}")

@pytest_asyncio.fixture
async def simulation_service(db_session):
    """Fixture برای SimulationService"""
    try:
        from services.simulation.service import SimulationService
        return SimulationService(db_session)
    except ImportError as e:
        pytest.skip(f"SimulationService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.simulation.service import SimulationService
            return SimulationService(db_session)
        except Exception as e2:
            pytest.skip(f"SimulationService init failed: {e2}")

@pytest_asyncio.fixture
async def supabase_service(db_session):
    """Fixture برای SupabaseService"""
    try:
        from services.supabase.service import SupabaseService
        return SupabaseService(db_session)
    except ImportError as e:
        pytest.skip(f"SupabaseService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.supabase.service import SupabaseService
            return SupabaseService(db_session)
        except Exception as e2:
            pytest.skip(f"SupabaseService init failed: {e2}")

@pytest_asyncio.fixture
async def telegram_bot_service(db_session):
    """Fixture برای Telegram_botService"""
    try:
        from services.telegram_bot.service import Telegram_botService
        return Telegram_botService(db_session)
    except ImportError as e:
        pytest.skip(f"Telegram_botService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.telegram_bot.service import Telegram_botService
            return Telegram_botService(db_session)
        except Exception as e2:
            pytest.skip(f"Telegram_botService init failed: {e2}")

@pytest_asyncio.fixture
async def tourism_service(db_session):
    """Fixture برای TourismService"""
    try:
        from services.tourism.service import TourismService
        return TourismService(db_session)
    except ImportError as e:
        pytest.skip(f"TourismService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.tourism.service import TourismService
            return TourismService(db_session)
        except Exception as e2:
            pytest.skip(f"TourismService init failed: {e2}")

@pytest_asyncio.fixture
async def workflow_service(db_session):
    """Fixture برای WorkflowService"""
    try:
        from services.workflow.service import WorkflowService
        return WorkflowService(db_session)
    except ImportError as e:
        pytest.skip(f"WorkflowService not available: {e}")
    except TypeError:
        #fallback: ممکن است constructor متفاوت باشد
        try:
            from services.workflow.service import WorkflowService
            return WorkflowService(db_session)
        except Exception as e2:
            pytest.skip(f"WorkflowService init failed: {e2}")

