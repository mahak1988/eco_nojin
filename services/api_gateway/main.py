"""
Eco Nojin - API Gateway
========================
Main FastAPI application entry point.

Architecture:
  1. Load settings FIRST (before app creation)
  2. Create FastAPI app
  3. Add CORSMiddleware IMMEDIATELY (before any router)
  4. Include all routers
  5. Add health/root endpoints
  6. Add global exception handler

Author: Eco Nojin Team
Created: 2026-08-15
Version: 0.1.0 (Phase 0.A)
"""

import os

from dotenv import load_dotenv

load_dotenv()

import logging
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

from database.hub import hub
from services.api_gateway.eventbus import init_nats, shutdown_nats
from services.api_gateway.exceptions import EcoNojinException
from services.api_gateway.middleware import UploadSizeMiddleware
from services.api_gateway.middleware.tenant import TenantMiddleware


# Compatibility: init_db via hub
def init_db():
    from database.base import Base
    import database.models  # noqa: F401
    import engine.land.models  # noqa: F401
    import engine.hydroma.core.models  # noqa: F401
    import engine.hydroma.biofertilizer.models  # noqa: F401

    engine = hub.get_sqlalchemy_engine()
    Base.metadata.create_all(bind=engine)


from engine.hydroma.config.settings import get_settings
from services.api_gateway.routers import nojin
from services.commerce.routers import commerce as commerce_router
from services.finance.routers import finance as finance_router
from services.inventory.routers import inventory as inventory_router

# Import all routers
# Import individual routers that are used later with app.include_router
from .routers import (  # Import the new router
    admin,
    ai,
    ai_chat,
    analyses,
    analytics,
    auth,
    auth_supabase,
    automation,
    benchmark,
    blockchain,
    carbon,
    contact,
    dashboard,
    disputes,
    ecowallet,
    elevation,
    farms,
    hydroma_carbon,
    hydroma_climate,
    hydroma_dashboard,
    hydroma_economics,
    hydroma_hub,
    hydroma_indices,
    hydroma_mrv,
    hydroma_neuro,
    hydroma_ops,
    hydroma_simulation,
    hydroma_soil,
    hydroma_water,
    iot_devices,
    insurance,
    land,
    logistics,
    manual_data,
    marketplace,
    materials,
    models as models_router,
    motors,
    mrv,
    newsletter,
    nojin,
    organizations,
    pilot,
    platform,
    quality,
    realtime,
    satellite,
    scenarios,
    science,
    simulation,
    soil,
    support,
    sync,
    ussd,
    voice,
    village_hub,
    watershed,
)

# ============================================================================
# LOAD SETTINGS (BEFORE app creation - used in FastAPI init)
# ============================================================================
logger = logging.getLogger("econojin.api")
_settings = get_settings()
logger.info(f"Settings loaded: app={_settings.app_name}, env={_settings.app_env}")


app = FastAPI(title="Eco Nojin API Gateway")

# Include existing routers (prefixes are defined in each router)
app.include_router(platform.router)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(auth.router)
app.include_router(analyses.router)
app.include_router(auth_supabase.router)
app.include_router(organizations.router)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
import structlog

from services.api_gateway.observability.structured_logger import (
    set_correlation_id,
    setup_structured_logging,
)

_structured_logger = setup_structured_logging(
    log_level="INFO",
    json_output=True,
    service_name="econojin-api",
    environment=_settings.app_env,
)

logger = structlog.get_logger("econojin.api")

# Prometheus metrics instrumentation (after logger is defined)
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/favicon.ico", "/health/live", "/health/ready"],
    )
    
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    logger.info("✅ Prometheus metrics instrumentation enabled (with custom metrics)")
except ImportError:
    logger.info("ℹ️ prometheus-fastapi-instrumentator not installed, metrics endpoint disabled")
except Exception as e:
    logger.warning(f"⚠️ Prometheus metrics setup failed: {e}")


# ============================================================================
# LIFESPAN (modern FastAPI startup/shutdown)
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting Eco Nojin API...")
    logger.info("=" * 60)

    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        logger.error(traceback.format_exc())

    app.state.start_time = time.time()

    # Initialize NATS JetStream Event Bus
    try:
        if _settings.enable_event_bus:
            await init_nats()
            logger.info("✅ NATS JetStream Event Bus initialized")
        else:
            logger.info("ℹ️ NATS Event Bus disabled (ENABLE_EVENT_BUS=false)")
    except Exception as e:
        logger.warning(f"⚠️ NATS Event Bus not initialized: {e}")

    # Initialize marketplace repositories
    try:
        from services.marketplace.order_management import init_order_manager
        from services.marketplace.product_catalog import init_catalog
        from services.marketplace.repositories.marketplace_repository import (
            MarketplaceMemberRepository,
            MarketplaceRepository,
            MarketplaceShopRepository,
        )

        with hub.get_session() as session:
            marketplace_repo = MarketplaceRepository(session)
            member_repo = MarketplaceMemberRepository(session)
            shop_repo = MarketplaceShopRepository(session)

        # Initialize with actual repositories (placeholder for now - will be replaced with proper repositories)
        init_catalog(seller_repo=None, product_repo=None)
        init_order_manager(order_repo=None)
        logger.info("✅ Marketplace repositories initialized")
    except Exception as e:
        logger.warning(f"⚠️ Marketplace repositories not initialized: {e}")

    # Initialize carbon repository
    try:
        from engine.hydroma.carbon.calculator import set_repository as set_carbon_repository
        from services.carbon.repository import CarbonProjectRepository

        with hub.get_session() as session:
            carbon_repo = CarbonProjectRepository(session)
        set_carbon_repository(carbon_repo)
        logger.info("✅ Carbon repository initialized")
    except Exception as e:
        logger.warning(f"⚠️ Carbon repository not initialized: {e}")

    logger.info(f"🌍 CORS origins: {_settings.cors_origins}")
    logger.info(f"📚 API docs: http://{os.environ.get('HOST', '127.0.0.1')}:8000/docs")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("🛑 Shutting down Eco Nojin API...")
    try:
        await shutdown_nats()
        logger.info("✅ NATS JetStream Event Bus shut down")
    except Exception as e:
        logger.warning(f"⚠️ NATS shutdown error: {e}")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================


# ============================================================================
# CORS MIDDLEWARE - MUST BE FIRST (before any router)
# This intercepts OPTIONS preflight requests BEFORE they hit routes
# ============================================================================
_cors_origins = _settings.cors_origins

# Ensure it's a list
if isinstance(_cors_origins, str):
    try:
        import json

        _cors_origins = json.loads(_cors_origins)
    except Exception:
        _cors_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]

# Pentest fix H1: no wildcard fallback. If origins resolve to an empty
# list, CORSMiddleware sends no ACAO headers at all (fail-closed).

logger.info(f"CORS middleware configured with {len(_cors_origins)} origins")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)


# ============================================================================
# RATE LIMITING + REQUEST ID + SECURITY HEADERS MIDDLEWARES
# ============================================================================
# Rate limit + request ID + security headers middlewares
from services.api_gateway.security import (
    HTTPSRedirectMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from services.security.csrf import CSRFMiddleware
from services.api_gateway.middleware import IdempotencyMiddleware, LocaleMiddleware

app.add_middleware(UploadSizeMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)

# Initialize Redis client if available for rate limiting
_redis_client = None
try:
    import redis as _redis

    _redis_url = getattr(_settings, "redis_url", "")
    if _redis_url:
        _redis_client = _redis.from_url(_redis_url, decode_responses=False)
        _redis_client.ping()
        logger.info("✅ Redis connected for rate limiting")
except Exception:
    _redis_client = None
    logger.info("ℹ️ Redis not available, using in-memory rate limiting")

# P0 FIX: Rate limit middleware is now active (previously only registered in tests)
app.add_middleware(RateLimitMiddleware, redis_client=_redis_client)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(CSRFMiddleware)
# Idempotency middleware for financial operations (must be after auth)
app.add_middleware(IdempotencyMiddleware)
logger.info(
    "HTTPS redirect + rate limit + security headers + request ID + CSRF + Idempotency middleware applied"
)

# Locale detection middleware (must be after CORS, before auth)
app.add_middleware(LocaleMiddleware)
logger.info("✅ Locale detection middleware applied")

# OpenTelemetry tracing (optional)
try:
    from services.api_gateway.tracing import setup_tracing

    setup_tracing(app)
except Exception:
    pass


# Pentest fix H1: the manual OPTIONS bypass and the per-response wildcard
# ACAO header were removed. CORS is enforced exclusively by the
# CORSMiddleware configured below (explicit origin allowlist).


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler - log and return safe response."""
    if isinstance(exc, EcoNojinException):
        logger.error("Handled error: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "path": str(request.url.path),
            },
        )
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    error_detail = str(exc) if _settings.app_env == "development" else "Internal server error"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_detail,
            "error_type": type(exc).__name__,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,  # Use the imported status constant
        content={
            "detail": f"Endpoint not found: {request.url.path}",
            "hint": "Check /docs for available endpoints",
        },
    )


# ============================================================================
# INCLUDE ALL ROUTERS
# ============================================================================
# Auth & User Management

app.include_router(land.router)
# Scientific Modules
app.include_router(soil.router)
app.include_router(satellite.router)
app.include_router(carbon.router)
app.include_router(watershed.router)
app.include_router(scenarios.router)

# AI & Assistant
app.include_router(ai.router)
app.include_router(ai_chat.router)

# Economy & Marketplace
app.include_router(ecowallet.router)
app.include_router(marketplace.router)
# Village Development Hub — extends marketplace with village development features
app.include_router(village_hub.router)

# Farm Management
app.include_router(farms.router)

# Additional Services
app.include_router(analytics.router)
app.include_router(materials.router)
app.include_router(blockchain.router)
app.include_router(ussd.router)
app.include_router(voice.router)
app.include_router(sync.router)
app.include_router(benchmark.router)
app.include_router(realtime.router)

# ════════════════════════════════════════════════════════════════
# Nojin Biofertilizer Router - Scientific soil restoration
# ════════════════════════════════════════════════════════════════
app.include_router(nojin.router)
# Scientific simulation & motors (HyDroMa)
app.include_router(simulation.router, tags=["simulation"])
app.include_router(mrv.router, prefix="/api/v1", tags=["mrv"])
app.include_router(science.router, tags=["science"])
app.include_router(models_router.router, tags=["models"])
app.include_router(elevation.router, tags=["elevation"])
app.include_router(support.router, tags=["support"])
app.include_router(manual_data.router, tags=["manual-data"])
app.include_router(dashboard.router)
app.include_router(contact.router, tags=["contact"])
app.include_router(pilot.router, tags=["pilot"])
app.include_router(newsletter.router, tags=["newsletter"])
app.include_router(hydroma_hub.router, tags=["hydroma-hub"])
app.include_router(hydroma_dashboard.router, tags=["hydroma-dashboard"])
app.include_router(hydroma_indices.router, tags=["hydroma-indices"])
app.include_router(hydroma_soil.router, tags=["hydroma-soil"])
app.include_router(hydroma_simulation.router, tags=["hydroma-simulation"])
app.include_router(hydroma_water.router, tags=["hydroma-water"])
app.include_router(automation.router, tags=["automation"])
app.include_router(hydroma_ops.router, tags=["hydroma-ops"])
app.include_router(hydroma_mrv.router, tags=["hydroma-mrv"])
app.include_router(logistics.router, tags=["logistics"])
app.include_router(quality.router, tags=["quality"])
app.include_router(disputes.router, tags=["disputes"])
app.include_router(commerce_router.router, tags=["commerce"])
app.include_router(finance_router.router, tags=["finance"])
app.include_router(inventory_router.router, tags=["inventory"])
app.include_router(hydroma_economics.router, tags=["hydroma-economics"])
app.include_router(hydroma_carbon.router, tags=["hydroma-carbon"])
app.include_router(hydroma_climate.router, tags=["hydroma-climate"])
app.include_router(hydroma_neuro.router, tags=["plant-neuro"])
app.include_router(iot_devices.router, tags=["iot-devices"])
app.include_router(insurance.router, tags=["insurance"])


# ============================================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================================
@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API info and links."""
    return {
        "name": "Eco Nojin API",
        "version": getattr(_settings, "api_version", "0.1.0"),
        "status": "running",
        "environment": _settings.app_env,
        "links": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
        },
        "modules": {
            "soil": "/api/v1/soil/*",
            "satellite": "/api/v1/satellite/*",
            "carbon": "/api/v1/carbon/*",
            "watershed": "/api/v1/watershed/*",
            "auth": "/api/v1/auth/*",
        },
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint - used by load balancers and monitoring."""
    checks = {
        "database": "ok",
        "settings": "ok",
        "routers": "loaded",
    }

    # Check database connectivity (with timeout)
    try:
        async with hub.get_async_session() as session:
            from sqlalchemy import text

            result = await session.execute(text("SELECT 1"))
            result.scalar()
        checks["database"] = "ok"
    except Exception as exc:
        logger.warning("Health check database failed: %s", exc)
        checks["database"] = "error"

    # Check Redis connectivity (if configured) - async with timeout
    try:
        redis_url = getattr(_settings, "redis_url", None)
        if redis_url:
            import redis.asyncio as redis

            redis_client = redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
            await redis_client.ping()
            await redis_client.close()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not_configured"
    except Exception as exc:
        logger.warning("Health check redis failed: %s", exc)
        checks["redis"] = "error"

    # Check the numerical backend (compiled C++ core vs Python fallback).
    # NOTE: the previous implementation imported the non-existent module
    # ``engine.hydroma.cpp_bindings`` and therefore always reported "error".
    try:
        from engine.hydroma.cpp_bridge import backend_status

        _cpp = backend_status()
        checks["cpp_core"] = "ok" if _cpp["cpp_available"] else "fallback"
        checks["cpp_backend"] = _cpp["backend"]
        checks["cpp_fallback_calls"] = _cpp["telemetry"]["fallback_calls"]
    except Exception as exc:
        logger.warning("Health check cpp_core failed: %s", exc)
        checks["cpp_core"] = "error"
        checks["cpp_backend"] = "unknown"

    # Determine overall status (degradation must be explicit, never silent)
    degraded_reasons: list[str] = []
    if any(v == "error" for v in checks.values()):
        degraded_reasons.append("dependency_error")
    if checks.get("cpp_core") == "fallback":
        degraded_reasons.append("cpp_core_fallback")
    status = "degraded" if degraded_reasons else "healthy"

    return {
        "status": status,
        "service": "api-gateway",
        "version": getattr(_settings, "api_version", "0.1.0"),
        "environment": _settings.app_env,
        "modules": {
            "soil": "/api/v1/soil/*",
            "satellite": "/api/v1/satellite/*",
            "carbon": "/api/v1/carbon/*",
            "watershed": "/api/v1/watershed/*",
            "auth": "/api/v1/auth/*",
            "ussd": "/api/v1/ussd/*",
            "voice_ivr": "/api/v1/voice/*",
            "mrv": "/api/v1/mrv/*",
            "blockchain": "/api/v1/blockchain/*",
        },
        "blockchain": {
            "enabled": True,
        },
        "inclusive_access": {
            "ussd_feature_phone": True,
            "sms_commands": True,
            "voice_ivr": True,
        },
        "checks": checks,
        "degraded_reasons": degraded_reasons,
    }


@app.get("/health/live", tags=["health"])
async def health_live():
    """Liveness probe - minimal check for Kubernetes."""
    return {"status": "alive", "service": "api-gateway"}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    """Readiness probe - checks dependencies."""
    checks = {"database": "ok"}
    try:
        from sqlalchemy import text
        engine = hub.get_sqlalchemy_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Readiness check database failed: %s", exc)
        checks["database"] = "error"
    status = "ready" if checks["database"] == "ok" else "not_ready"
    return {"status": status, "service": "api-gateway", "checks": checks}


@app.get("/api/v1/health", tags=["health"])
async def health_v1():
    """Versioned health check endpoint."""
    return await health()


@app.get("/ready", tags=["health"])
async def readiness():
    """Readiness check - indicates if service can accept traffic."""
    return {
        "ready": True,
        "service": "api-gateway",
    }


# ============================================================================
# DEBUG ENDPOINT (explicit toggle, off by default in production)
# ============================================================================
if _settings.enable_debug_routes:

    @app.get("/debug/routes", tags=["debug"])
    async def debug_routes():
        """List all registered routes (debug mode only)."""
        routes = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                routes.append(
                    {
                        "path": route.path,
                        "methods": list(route.methods) if route.methods else [],
                        "name": route.name,
                    }
                )
        return {
            "total_routes": len(routes),
            "routes": sorted(routes, key=lambda x: x["path"]),
        }


# ============================================================================
# STARTUP MESSAGE (when run directly)
# ============================================================================


# ============================================================================
# Health Check Endpoint
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Eco Nojin API in standalone mode...")
    uvicorn.run(
        "services.api_gateway.main:app",
        host=_settings.app_host,
        port=_settings.app_port,
        reload=(_settings.app_env == "development"),
        log_level="info",
        timeout_keepalive=30,
        timeout_notify=10,
        limit_concurrency=100,
        limit_max_requests=1000,
    )
