"""Main entry point for the Eco Nojin API Gateway."""
import os
import secrets as _secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from engine.hydroma.core.database import Base, engine
from .routers import (
    soil, materials, ai, satellite, scenarios,
    marketplace, carbon, watershed, benchmark, sync, ussd
)

# Create database tables on startup (Research mode)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Eco Nojin API Gateway",
    description="Scientific engine API for ecosystem restoration and smart agriculture.",
    version="1.2.0",
)

# --- CORS configuration (STD-008) --------------------------------------
# Wildcard origin + credentials is invalid per the CORS spec and rejected by
# browsers. Origins come from CORS_ALLOWED_ORIGINS (comma-separated env);
# credentials are enabled only when an explicit origin list is configured.
_cors_origins = [
    o.strip()
    for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=bool(_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Optional auth gate (opt-in) ----------------------------------------
# Set AUTH_ENABLED=1 and AUTH_TOKEN=<secret> to require a bearer token on all
# /api/v1 routes except /health. Disabled by default for research mode.
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "0") == "1"
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    if AUTH_ENABLED and request.url.path.startswith("/api/v1") and not request.url.path.endswith("/health"):
        auth = request.headers.get("Authorization", "")
        expected = "Bearer " + AUTH_TOKEN
        if not _secrets.compare_digest(auth, expected):
            raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)


# Include domain routers
app.include_router(soil.router)
app.include_router(materials.router)
app.include_router(ai.router)
app.include_router(satellite.router)
app.include_router(scenarios.router)
app.include_router(marketplace.router)
app.include_router(carbon.router)
app.include_router(watershed.router)
app.include_router(benchmark.router)
app.include_router(sync.router)
app.include_router(ussd.router)


@app.get("/api/v1/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "operational",
        "engine": "HyDroMa",
        "mode": "research",
        "version": "1.2.0",
        "modules": [
            "soil", "materials", "ai_assistant", "satellite",
            "scenarios", "marketplace", "carbon", "watershed",
            "benchmark", "sync", "ussd_sms"
        ],
        "inclusive_access": {
            "web_app": True,
            "pwa_offline": True,
            "ussd_feature_phone": True,
            "sms_commands": True,
            "languages": ["en", "fa", "ar"],
        },
    }