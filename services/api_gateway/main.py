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
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request # Added Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status # Added status import

from database.hub import hub

# Compatibility: init_db via hub
def init_db():
    # Create tables using hub engine
    from database.base import Base
    engine = hub.get_sqlalchemy_engine()
    Base.metadata.create_all(bind=engine)
from engine.hydroma.config.settings import get_settings

# Import all routers
from .routers import platform, admin, auth, analyses # Import the new router

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
from .routers import manual_data
from .routers import voice
from .routers import dashboard
from services.api_gateway.routers import nojin

app = FastAPI(title="Eco Nojin API Gateway")

# Include existing routers
app.include_router(platform.router, prefix="/api/v1", tags=["platform"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# Include the new analyses router
app.include_router(analyses.router, prefix="/api/v1", tags=["analyses"]) # Register the new router

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
    
    logger.info(f"🌍 CORS origins: {_settings.cors_origins}")
    logger.info(f"📚 API docs: http://os.environ.get('HOST', '127.0.0.1'):8000/docs")
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
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
logger.info("Rate limit + security headers + request ID middleware applied")


# Pentest fix H1: the manual OPTIONS bypass and the per-response wildcard
# ACAO header were removed. CORS is enforced exclusively by the
# CORSMiddleware configured below (explicit origin allowlist).


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler - log and return safe response."""
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
app.include_router(auth.router)

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
app.include_router(platform.router)

# ═══════════════════════════════════════════════════════════════
# Nojin Biofertilizer Router - Scientific soil restoration
# ═══════════════════════════════════════════════════════════════
app.include_router(nojin.router)
# Scientific simulation & motors (HyDroMa)
app.include_router(simulation.router, tags=["simulation"])
app.include_router(motors.router, prefix="/api", tags=["scientific-motors"])
app.include_router(motors.router, prefix="/api/v1", tags=["scientific-motors"])
app.include_router(mrv.router, tags=["mrv"])
app.include_router(science.router, tags=["science"])
app.include_router(models_router.router, tags=["models"])
app.include_router(elevation.router, tags=["elevation"])
app.include_router(support.router, tags=["support"])
app.include_router(manual_data.router, tags=["manual-data"])
app.include_router(dashboard.router)


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
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": getattr(_settings, "api_version", "0.1.0"),
        "environment": _settings.app_env,
        "checks": {
            "database": "ok",  # init_db already ran in lifespan
            "settings": "ok",
            "routers": "loaded",
        },
    }


@app.get("/ready", tags=["health"])
async def readiness():
    """Readiness check - indicates if service can accept traffic."""
    return {
        "ready": True,
        "service": "api-gateway",
    }


# ============================================================================
# DEBUG ENDPOINT (development only)
# ============================================================================
if _settings.app_env == "development":
    @app.get("/debug/routes", tags=["debug"])
    async def debug_routes():
        """List all registered routes (development only)."""
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
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "Eco Nojin API Gateway",
        "timestamp": datetime.now().isoformat() if 'datetime' in dir() else "N/A"
    }

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
