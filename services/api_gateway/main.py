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

from services.api_gateway.exceptions import EcoNojinException
from services.api_gateway.middleware import UploadSizeMiddleware
from services.api_gateway.middleware.tenant import TenantMiddleware

from database.hub import hub

# Compatibility: init_db via hub
def init_db():
    # Create tables using hub engine
    from database.base import Base
    engine = hub.get_sqlalchemy_engine()
    Base.metadata.create_all(bind=engine)
from engine.hydroma.config.settings import get_settings

# Import all routers
from .routers import platform, admin, auth, analyses, auth_supabase, organizations  # Import the new router

# Import individual routers that are used later with app.include_router
from .routers import land, soil, satellite, carbon, watershed, scenarios, ai, ai_chat, ecowallet, marketplace, farms, analytics, materials, blockchain
from .routers import benchmark
from .routers import nojin
from .routers import sync
from .routers import ussd
from .routers import simulation, motors, mrv, science
from .routers import models as models_router
from .routers import elevation
from .routers import support
from .routers import contact
from .routers import pilot
from .routers import newsletter
from .routers import hydroma_hub
from .routers import hydroma_indices
from .routers import hydroma_soil
from .routers import hydroma_simulation
from .routers import hydroma_water
from .routers import automation
from .routers import hydroma_ops
from .routers import hydroma_mrv
from .routers import hydroma_economics
from .routers import hydroma_carbon
from .routers import hydroma_climate
from .routers import manual_data
from .routers import voice
from .routers import iot_devices
from .routers import organizations
from .routers import carbon as carbon_router
from .routers import marketplace as marketplace_router
from .routers import dashboard
from .routers import iot_devices
from services.api_gateway.routers import nojin

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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("econojin.api")


# ============================================================================
# LOAD SETTINGS (BEFORE app creation - used in FastAPI init)
# ============================================================================
_settings = get_settings()
logger.info(f"Settings loaded: app={_settings.app_name}, env={_settings.app_env}")


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

    # Initialize marketplace repositories
    try:
        from services.marketplace.repositories.marketplace_repository import (
            OrderRepository,
            ProductRepository,
            SellerRepository,
        )
        from services.marketplace.product_catalog import init_catalog
        from services.marketplace.order_management import init_order_manager

        with hub.get_session() as session:
            seller_repo = SellerRepository(session)
            product_repo = ProductRepository(session)
            order_repo = OrderRepository(session)

        init_catalog(seller_repo=seller_repo, product_repo=product_repo)
        init_order_manager(order_repo=order_repo)
        logger.info("✅ Marketplace repositories initialized")
    except Exception as e:
        logger.warning(f"⚠️ Marketplace repositories not initialized: {e}")

    # Initialize carbon repository
    try:
        from services.carbon.repository import CarbonProjectRepository
        from engine.hydroma.carbon.calculator import set_repository as set_carbon_repository

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
from services.api_gateway.security import (
    HTTPSRedirectMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
)
from services.security.csrf import CSRFMiddleware

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

app.add_middleware(RateLimitMiddleware, redis_client=_redis_client)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(CSRFMiddleware)
logger.info("HTTPS redirect + rate limit + security headers + request ID + CSRF middleware applied")

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
    error_detail = (
        str(exc)
        if _settings.app_env == "development"
        else "Internal server error"
    )
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
        status_code=404, # Use the imported status constant
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

# ═══════════════════════════════════════════════════════════════
# Nojin Biofertilizer Router - Scientific soil restoration
# ═══════════════════════════════════════════════════════════════
app.include_router(nojin.router)
# Scientific simulation & motors (HyDroMa)
app.include_router(simulation.router, tags=["simulation"])
app.include_router(motors.router, prefix="/api", tags=["scientific-motors"])
app.include_router(motors.router, prefix="/api/v1", tags=["scientific-motors"])
app.include_router(mrv.router, prefix="/api", tags=["mrv"])
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
app.include_router(hydroma_indices.router, tags=["hydroma-indices"])
app.include_router(hydroma_soil.router, tags=["hydroma-soil"])
app.include_router(hydroma_simulation.router, tags=["hydroma-simulation"])
app.include_router(hydroma_water.router, tags=["hydroma-water"])
app.include_router(automation.router, tags=["automation"])
app.include_router(hydroma_ops.router, tags=["hydroma-ops"])
app.include_router(hydroma_mrv.router, tags=["hydroma-mrv"])
app.include_router(hydroma_economics.router, tags=["hydroma-economics"])
app.include_router(hydroma_carbon.router, tags=["hydroma-carbon"])
app.include_router(hydroma_climate.router, tags=["hydroma-climate"])
app.include_router(iot_devices.router, tags=["iot-devices"])


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

    # Check database connectivity
    try:
        from sqlalchemy import text
        engine = hub.get_sqlalchemy_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.warning("Health check database failed: %s", exc)
        checks["database"] = "error"

    # Check Redis connectivity (if configured)
    try:
        redis_url = getattr(_settings, "redis_url", None)
        if redis_url:
            redis_client = hub.get_redis()
            if redis_client is not None:
                redis_client.ping()
                checks["redis"] = "ok"
            else:
                checks["redis"] = "unavailable"
        else:
            checks["redis"] = "not_configured"
    except Exception as exc:
        logger.warning("Health check redis failed: %s", exc)
        checks["redis"] = "error"

    # Check C++ core availability
    try:
        from engine.hydroma.cpp_bindings import is_available
        checks["cpp_core"] = "ok" if is_available() else "fallback"
    except Exception as exc:
        logger.warning("Health check cpp_core failed: %s", exc)
        checks["cpp_core"] = "error"

    # Determine overall status
    status = "healthy"
    if any(v == "error" for v in checks.values()):
        status = "degraded"

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
    }


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


@app.get("/metrics", tags=["observability"])
async def metrics():
    """Prometheus-style metrics endpoint."""
    try:
        from engine.hydroma.cpp_bindings import get_telemetry, is_available
        cpp_telemetry = get_telemetry()
        cpp_available = is_available()
    except Exception:
        cpp_telemetry = {}
        cpp_available = False

    return {
        "service": "api-gateway",
        "cpp_core_available": cpp_available,
        "cpp_calls": cpp_telemetry.get("cpp_calls", 0),
        "cpp_fallback_calls": cpp_telemetry.get("fallback_calls", 0),
        "cpp_total_time_ms": cpp_telemetry.get("total_cpp_time_ms", 0.0),
        "uptime_seconds": int(time.time() - app.state.start_time) if hasattr(app.state, "start_time") else 0,
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
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods) if route.methods else [],
                    "name": route.name,
                })
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
    )
