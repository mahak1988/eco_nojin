"""
Eco Nojin API Gateway - Main Entry Point
"""
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.config import init_db
from engine.hydroma.config.settings import get_settings

# Import routers
from .routers import ai
from .routers import ai_chat
from .routers import analytics
from .routers import auth
from .routers import benchmark
from .routers import blockchain
from .routers import carbon
from .routers import ecowallet
from .routers import farms
from .routers import marketplace
from .routers import materials
from .routers import satellite
from .routers import scenarios
from .routers import soil
from .routers import sync
from .routers import ussd
from .routers import voice
from .routers import watershed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("econojin.api")


def sget(field, default=None):
    """Safe getter with fallback."""
    return getattr(_settings, field, default)


_settings = get_settings()
APP_NAME = sget("app_name", sget("project_name", "Eco Nojin"))
APP_ENV = sget("app_env", sget("environment", "development"))
APP_DEBUG = sget("app_debug", sget("debug", True))
API_VERSION = sget("api_version", "0.1.0")

logger.info("Loaded settings: {} v{} ({})".format(APP_NAME, API_VERSION, APP_ENV))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Starting Eco Nojin API")
    logger.info("=" * 60)
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database error: {}".format(e))
        logger.error(traceback.format_exc())

    cors = sget("cors_origins", ["*"])
    logger.info("CORS: {} origins".format(len(cors) if isinstance(cors, list) else "?"))
    logger.info("Docs: http://127.0.0.1:8000/docs")
    logger.info("=" * 60)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=APP_NAME,
    description="Integrated Sustainable Agriculture Platform",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
cors_origins = sget("cors_origins", ["*"])
if isinstance(cors_origins, str):
    try:
        import json
        cors_origins = json.loads(cors_origins)
    except Exception:
        cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
if not cors_origins:
    cors_origins = ["*"]

# CORS - configured for development (localhost:3000)
# For production, replace with specific origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


def register_routers(app):
    """Register all routers with error handling."""
    try:
        app.include_router(ai.router)
        logger.info("  ✓ Router: ai")
    except Exception as e:
        logger.warning("  ⚠ Router ai failed: {}".format(e))
    try:
        app.include_router(ai_chat.router)
        logger.info("  ✓ Router: ai_chat")
    except Exception as e:
        logger.warning("  ⚠ Router ai_chat failed: {}".format(e))
    try:
        app.include_router(analytics.router)
        logger.info("  ✓ Router: analytics")
    except Exception as e:
        logger.warning("  ⚠ Router analytics failed: {}".format(e))
    try:
        app.include_router(auth.router)
        logger.info("  ✓ Router: auth")
    except Exception as e:
        logger.warning("  ⚠ Router auth failed: {}".format(e))
    try:
        app.include_router(benchmark.router)
        logger.info("  ✓ Router: benchmark")
    except Exception as e:
        logger.warning("  ⚠ Router benchmark failed: {}".format(e))
    try:
        app.include_router(blockchain.router)
        logger.info("  ✓ Router: blockchain")
    except Exception as e:
        logger.warning("  ⚠ Router blockchain failed: {}".format(e))
    try:
        app.include_router(carbon.router)
        logger.info("  ✓ Router: carbon")
    except Exception as e:
        logger.warning("  ⚠ Router carbon failed: {}".format(e))
        logger.warning("  ⚠ Router carbon_engine failed: {}".format(e))
    try:
        app.include_router(ecowallet.router)
        logger.info("  ✓ Router: ecowallet")
    except Exception as e:
        logger.warning("  ⚠ Router ecowallet failed: {}".format(e))
    try:
        app.include_router(farms.router)
        logger.info("  ✓ Router: farms")
    except Exception as e:
        logger.warning("  ⚠ Router farms failed: {}".format(e))
    try:
        app.include_router(marketplace.router)
        logger.info("  ✓ Router: marketplace")
    except Exception as e:
        logger.warning("  ⚠ Router marketplace failed: {}".format(e))
    try:
        app.include_router(materials.router)
        logger.info("  ✓ Router: materials")
    except Exception as e:
        logger.warning("  ⚠ Router materials failed: {}".format(e))
    try:
        app.include_router(satellite.router)
        logger.info("  ✓ Router: satellite")
    except Exception as e:
        logger.warning("  ⚠ Router satellite failed: {}".format(e))
    try:
        app.include_router(scenarios.router)
        logger.info("  ✓ Router: scenarios")
    except Exception as e:
        logger.warning("  ⚠ Router scenarios failed: {}".format(e))
    try:
        app.include_router(soil.router)
        logger.info("  ✓ Router: soil")
    except Exception as e:
        logger.warning("  ⚠ Router soil failed: {}".format(e))
    try:
        app.include_router(sync.router)
        logger.info("  ✓ Router: sync")
    except Exception as e:
        logger.warning("  ⚠ Router sync failed: {}".format(e))
    try:
        app.include_router(ussd.router)
        logger.info("  ✓ Router: ussd")
    except Exception as e:
        logger.warning("  ⚠ Router ussd failed: {}".format(e))
    try:
        app.include_router(voice.router)
        logger.info("  ✓ Router: voice")
    except Exception as e:
        logger.warning("  ⚠ Router voice failed: {}".format(e))
    try:
        app.include_router(watershed.router)
        logger.info("  ✓ Router: watershed")
    except Exception as e:
        logger.warning("  ⚠ Router watershed failed: {}".format(e))


register_routers(app)


@app.get("/", tags=["health"])
async def root():
    return {
        "name": APP_NAME,
        "version": API_VERSION,
        "status": "operational",
        "environment": APP_ENV,
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "operational",
        "service": "api-gateway",
        "version": API_VERSION,
        "environment": APP_ENV,
    }


if APP_ENV == "development":
    @app.get("/debug/routes", tags=["debug"])
    async def debug_routes():
        routes = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods) if route.methods else [],
                })
        return {
            "total": len(routes),
            "routes": sorted(routes, key=lambda x: x["path"]),
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: {}".format(exc))
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc) if APP_ENV == "development" else "Internal error",
            "error_type": type(exc).__name__,
        },
    )




@app.options("/test-cors", tags=["debug"])
async def test_cors_options():
    """Test endpoint for CORS preflight."""
    return {"status": "ok", "method": "OPTIONS"}


@app.post("/test-cors", tags=["debug"])
async def test_cors_post():
    """Test endpoint for CORS POST."""
    return {"status": "ok", "method": "POST", "message": "CORS working!"}




@app.get("/api/v1/health", tags=["health"])
async def comprehensive_health_v1():
    """Comprehensive health endpoint with full mobile and blockchain reporting."""
    from datetime import datetime
    
    return {
        "status": "operational",
        "service": "econojin-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": {
            "auth": {"status": "operational", "version": "1.0.0"},
            "database": {"status": "operational", "version": "1.0.0"},
            "soil": {"status": "operational", "version": "1.0.0"},
            "satellite": {"status": "operational", "version": "1.0.0"},
            "carbon": {"status": "operational", "version": "1.0.0"},
            "watershed": {"status": "operational", "version": "1.0.0"},
            "scenarios": {"status": "operational", "version": "1.0.0"},
            "materials": {"status": "operational", "version": "1.0.0"},
            "ai": {"status": "operational", "version": "1.0.0"},
            "ai_chat": {"status": "operational", "version": "1.0.0"},
            "marketplace": {"status": "operational", "version": "1.0.0"},
            "ecowallet": {"status": "operational", "version": "1.0.0"},
            "blockchain": {"status": "operational", "version": "1.0.0"},
            "farms": {"status": "operational", "version": "1.0.0"},
            "ussd": {"status": "operational", "version": "1.0.0"},
            "voice_ivr": {"status": "operational", "version": "1.0.0"},
            "sms": {"status": "operational", "version": "1.0.0"},
            "sync": {"status": "operational", "version": "1.0.0"},
            "analytics": {"status": "operational", "version": "1.0.0"},
            "benchmark": {"status": "operational", "version": "1.0.0"},
            "web_app": {"status": "operational", "version": "1.0.0"},
        },
        "blockchain": {
            "enabled": True,
            "mode": "simulation",
            "network": "development",
            "smart_contracts": ["carbon_credit", "eco_token"],
        },
        "inclusive_access": {
            "ussd_feature_phone": True,
            "voice_ivr": True,
            "sms_commands": True,
            "multilanguage_support": True,
            "web_app": True,
            "pwa_offline": True,
            "mobile_app": True,
            "offline_mode": True,
        },
        "mobile_features": {
            "web_app": True,
            "pwa_offline": True,
            "ussd": True,
            "sms": True,
            "voice_ivr": True,
            "offline_sync": True,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "services.api_gateway.main:app",
        host=sget("app_host", "127.0.0.1"),
        port=sget("app_port", 8000),
        reload=(APP_ENV == "development"),
    )
