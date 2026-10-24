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

import asyncio
import hmac
import os

from dotenv import load_dotenv

from services.api_gateway.errors import safe_error_detail

load_dotenv()

import logging
import time
import traceback
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

from database.hub import hub
from services.api_gateway.eventbus import init_nats, shutdown_nats
from services.api_gateway.exceptions import EcoNojinException
from services.api_gateway.middleware import UploadSizeMiddleware
from services.api_gateway.middleware.tenant import TenantMiddleware


# Compatibility: init_db via hub - uses lazy imports to avoid INV-003 violation
# These are ORM model registrations, not scientific computation access
def init_db() -> "asyncio.Future | None":
    """Create the schema on both engines; return the async DDL future, if any.

    The returned future **must be awaited by the caller** (the lifespan does).
    The previous fire-and-forget ``loop.create_task(...)`` discarded it, so a
    failed async ``create_all`` died un-retrieved while startup logged success
    and the health probes kept passing — the async plane then answered
    ``no such table`` on every route (2026-10-12 review finding 9).
    """
    from database.base import Base  # noqa: E402, I001

    engine_obj = hub.get_sqlalchemy_engine()
    Base.metadata.create_all(bind=engine_obj)
    # P12 breadth delta: the sync plane above and the async plane
    # (``hub.get_async_session``) are two different in-memory engines, so a
    # schema created only on the sync one leaves every async route answering
    # ``no such table`` (measured: the marketplace marketplace/vendor/items
    # routes 500'd after their sessions moved to the async engine). Create the
    # schema on both engines.
    from database import hub as _hub

    async_engine = _hub._get_async_engine()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_hub._ensure_async_tables(async_engine))
        return None
    return loop.create_task(_hub._ensure_async_tables(async_engine))


from engine.hydroma.config.settings import get_settings
from services.api_gateway.routers import finance_consolidation as finance_consolidation_router
from services.api_gateway.routers import nojin
from services.commerce.routers import commerce as commerce_router
from services.finance.routers import finance as finance_router
from services.inventory.routers import inventory as inventory_router
from services.landscape.api import governance as landscape_governance_router
from services.landscape.api import territories as landscape_territories_router
from services.livestock import api as livestock_router
from services.simulation import api as simulation_legacy_router
from services.tourism.api.router import router as tourism_api_router
from services.validation import router as validation_router

# Import all routers
# Import individual routers that are used later with app.include_router
from .routers import (  # Import the new router
    admin_bots,
    admin_content,
    admin_errors,
    admin_models,
    admin_overview,
    admin_security,
    admin_settings,
    admin_users,
    ai,
    ai_advice_router,
    ai_analysis,
    ai_chat,
    analyses,
    analytics,
    audit,
    auth,
    auth_supabase,
    automation,
    benchmark,
    blockchain,
    carbon,
    climate,
    community,
    compliance,
    contact,
    content_public,
    culture,
    dashboard,
    disputes,
    economy,
    ecosystem,
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
    insurance,
    iot_devices,
    lab,
    land,
    legal_texts,
    lms,
    logistics,
    manual_data,
    marketplace,
    marketplace_reviews,
    materials,
    motors,
    mrv,
    nature,
    newsletter,
    ogc_router,
    organizations,
    passkey_router,
    pilot,
    platform,
    quality,
    rangeland,
    realtime,
    satellite,
    scenarios,
    science,
    security_router,
    simulation,
    soil,
    supabase_proxy,
    support,
    sync,
    tool_registry,
    tourism_router,
    ussd,
    village_hub,
    voice,
    water,
    watershed,
)
from .routers import (
    models as models_router,
)

# ============================================================================
# LOAD SETTINGS (BEFORE app creation - used in FastAPI init)
# ============================================================================
logger = logging.getLogger("econojin.api")
_settings = get_settings()
logger.info(f"Settings loaded: app={_settings.app_name}, env={_settings.app_env}")


# ============================================================================
# LIFESPAN (modern FastAPI startup/shutdown)
#
# Defined before the app is constructed because ``FastAPI(lifespan=...)``
# binds the reference at construction time. Registering it after
# ``app = FastAPI(...)`` left the whole startup/shutdown path unreachable:
# the DB was never initialised, NATS was never connected and the carbon
# repository was never bound.
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting Eco Nojin API...")
    logger.info("=" * 60)

    try:
        # SEC-09: await the async DDL future so a failure aborts startup
        # instead of logging success over a schema-less async plane.
        ddl_future = init_db()
        if ddl_future is not None:
            await ddl_future
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        logger.error(traceback.format_exc())

    # Idempotent by design: seed the canonical chart of accounts the settlement
    # and wallet batches journal against. A DB hiccup here must never block
    # boot, so it is isolated with its own warning like the NATS / carbon
    # / marketplace initialisations below.
    try:
        from services.finance.chart_of_accounts import seed_chart_of_accounts

        async with hub.get_async_session() as session:
            await seed_chart_of_accounts(session)
            await session.commit()
        logger.info("✅ Chart of accounts seeded")
    except Exception as e:
        logger.warning(f"⚠️ Chart of accounts not seeded: {e}")

    app.state.start_time = time.time()

    # Initialize NATS JetStream Event Bus
    try:
        if _settings.enable_event_bus:
            await init_nats()
            logger.info("✅ NATS JetStream Event Bus initialized")

            # Subscribe to commerce domain events (best-effort; failures are
            # logged and swallowed so a broker outage never breaks boot).
            try:
                from services.api_gateway.eventbus import get_nats_manager

                async def _commerce_event_handler(payload: dict, headers: dict) -> None:
                    """Dispatch commerce events to notification/workflow handlers."""
                    event_type = payload.get("event_type", "")
                    evt = payload.get("payload", {}) or {}
                    aggregate_type = evt.get("aggregate_type", "")
                    aggregate_id = evt.get("aggregate_id", "")
                    logger.info(
                        "commerce event: %s aggregate=%s id=%s",
                        event_type, aggregate_type, aggregate_id,
                    )

                    # --- Notification / workflow routing ---------------------
                    try:
                        if event_type == "order_created":
                            logger.info(
                                "workflow: notify seller of new order %s", aggregate_id
                            )
                        elif event_type == "order_paid":
                            logger.info(
                                "workflow: trigger settlement for order %s", aggregate_id
                            )
                        elif event_type == "order_shipped":
                            logger.info(
                                "workflow: notify buyer order %s shipped", aggregate_id
                            )
                        elif event_type == "order_delivered":
                            logger.info(
                                "workflow: start settlement window for order %s",
                                aggregate_id,
                            )
                        elif event_type == "order_settled":
                            logger.info(
                                "workflow: credit seller + landscape fund for %s",
                                aggregate_id,
                            )
                        elif event_type == "order_cancelled":
                            logger.info(
                                "workflow: release inventory for cancelled order %s",
                                aggregate_id,
                            )
                    except Exception as dispatch_exc:
                        logger.warning(
                            "commerce event dispatch failed for %s: %s",
                            event_type, dispatch_exc,
                        )

                nats_mgr = get_nats_manager()
                await nats_mgr.subscribe(
                    "commerce.>",
                    _commerce_event_handler,
                    durable_name="commerce-event-consumer",
                )
                logger.info("✅ Commerce event consumer subscribed")
            except Exception as exc:
                logger.warning(f"⚠️ Commerce event consumer not subscribed: {exc}")
        else:
            logger.info("ℹ️ NATS Event Bus disabled (ENABLE_EVENT_BUS=false)")
    except Exception as e:
        logger.warning(f"⚠️ NATS Event Bus not initialized: {e}")

    # Marketplace singletons. These are still wired to the in-memory demo
    # catalog: the DB repositories from services/marketplace/db_repos.py are
    # NOT connected yet (see INTEGRATION plan, group 4). The log line states
    # the real state instead of claiming a fully initialised marketplace.
    try:
        from services.marketplace.db_repos import DbOrderRepo, DbProductRepo, DbSellerRepo
        from services.marketplace.order_management import init_order_manager
        from services.marketplace.product_catalog import init_catalog

        init_catalog(
            seller_repo=DbSellerRepo(),
            product_repo=DbProductRepo(),
        )
        init_order_manager(order_repo=DbOrderRepo())
        logger.info("✅ Marketplace catalog + order manager wired to database repositories")
    except Exception as e:
        logger.warning(f"⚠️ Marketplace DB wiring failed, falling back to demo: {e}")
        try:
            from services.marketplace.order_management import init_order_manager
            from services.marketplace.product_catalog import init_catalog

            init_catalog(seller_repo=None, product_repo=None)
            init_order_manager(order_repo=None)
        except Exception:
            pass

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

    # Observability (OTel + Prometheus). Config-gated: the endpoint is only
    # enabled when OTEL_ENABLED=true, so a deployment that does not want the
    # collector traffic pays nothing and emits nothing.
    if os.getenv("OTEL_ENABLED", "false").lower() == "true":
        try:
            from services.observability.setup import instrument_app, setup_observability

            setup_observability(app, service_name="econojin-api")
            instrument_app(app)
            logger.info("OTel tracing + Prometheus metrics enabled")
        except Exception as e:
            logger.warning(f"Observability setup failed: {e}")
    else:
        logger.info("OTel tracing disabled (OTEL_ENABLED != true)")

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


app = FastAPI(title="Eco Nojin API Gateway", lifespan=lifespan)

# Include existing routers (prefixes are defined in each router)
app.include_router(platform.router)
app.include_router(admin_users.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_content.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_bots.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_errors.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_settings.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_models.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_overview.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_security.router, prefix="/api/v1/admin", tags=["admin"])
# P1: passkey registration/authentication + step-up proofs for sensitive acts
app.include_router(passkey_router.router)
app.include_router(auth.router)
app.include_router(analyses.router)
app.include_router(auth_supabase.router)
app.include_router(organizations.router)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
import structlog

from services.api_gateway.observability.structured_logger import (
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
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest  # noqa: E402
    from prometheus_fastapi_instrumentator import Instrumentator  # noqa: E402

    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/favicon.ico", "/health/live", "/health/ready"],
    )

    instrumentator.instrument(app)

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint(x_api_key: str | None = Header(None)):
        """Prometheus scrape endpoint.

        SEC-14: the previous ``instrumentator.expose(app, endpoint="/metrics")``
        published request volumes, business KPI counts and dependency health to
        anonymous callers. The scrape key is read from
        ``HYDROMA_METRICS_API_KEY``; when it is unset the endpoint stays closed
        (fail-closed: no key configured => no anonymous metrics). The
        comparison is on bytes: FastAPI decodes headers as latin-1, so a
        non-ASCII ``X-API-Key`` would raise ``TypeError`` inside
        ``compare_digest`` and turn an unauthenticated call into a 500.
        """
        expected = os.getenv("HYDROMA_METRICS_API_KEY", "")
        if (
            not expected
            or not x_api_key
            or not hmac.compare_digest(x_api_key.encode("utf-8"), expected.encode("utf-8"))
        ):
            raise HTTPException(status_code=401, detail="Invalid or missing metrics key")
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Import the custom metric definitions so they are registered in the
    # default registry. Without this, /metrics exposed only the instrumentator's
    # own HTTP series, and the log below announced custom metrics that were in
    # fact never imported: services/api_gateway/metrics.py — 616 lines covering
    # Redis, PostgreSQL, sync events, C++ calls and business KPIs — had no
    # importer anywhere in the repository.
    try:
        from services.api_gateway import metrics as _custom_metrics

        _custom_count = len([n for n in dir(_custom_metrics) if not n.startswith("_")])
        logger.info(
            f"✅ Prometheus metrics enabled: HTTP series + {_custom_count} custom metric "
            "objects registered (redis, postgres, sync, cpp, realtime, business kpi)"
        )
    except Exception as custom_error:
        # S-HONEST: say plainly that the custom metrics are missing rather than
        # letting the line above imply they are present.
        logger.warning(
            f"⚠️ Prometheus HTTP metrics enabled but custom metrics are NOT registered: {custom_error}"
        )
except ImportError:
    logger.info("ℹ️ prometheus-fastapi-instrumentator not installed, metrics endpoint disabled")
except Exception as e:
    logger.warning(f"⚠️ Prometheus metrics setup failed: {e}")


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
        # SEC-15: the header list used to omit the headers this codebase
        # actually reads (step-up TOTP, the CSRF double-submit token, the
        # idempotency key, the API keys), so a credentialed browser client
        # could not send them and those controls were unreachable from the
        # SPA. Additive: nothing previously allowed is removed.
        # X-Tenant-Id / X-Platform-Id are deliberately absent: SEC-03 removed
        # their trust (the tenant comes from the token), so no client needs
        # to send them.
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-CSRF-Token",
            "x-csrf-token",
            "X-TOTP-Code",
            "X-Step-Up-Token",
            "X-API-Key",
            "X-Webhook-Key",
            "Idempotency-Key",
            "X-Client-Secret",
        ],
    expose_headers=["X-Request-ID"],
    max_age=600,
)


# ============================================================================
# RATE LIMITING + REQUEST ID + SECURITY HEADERS MIDDLEWARES
# ============================================================================
# Rate limit + request ID + security headers middlewares
from services.api_gateway.middleware import (
    IdempotencyMiddleware,
    IdentityMiddleware,
    LocaleMiddleware,
)
from services.api_gateway.middleware.rate_limit import AuthRateLimitMiddleware  # noqa: E402
from services.api_gateway.middleware.security_headers import (  # noqa: E402
    SecurityHeadersMiddleware as GatewaySecurityHeadersMiddleware,
)
from services.api_gateway.security import (
    HTTPSRedirectMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
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

# P0 FIX: Rate limit middleware is now active (previously only registered in tests)
app.add_middleware(RateLimitMiddleware, redis_client=_redis_client)
app.add_middleware(SecurityHeadersMiddleware)
# ASVS-lite hardening: brute-force ceiling on the credential endpoints
# (outer, so 429s still carry the headers below) and the hardened header set
# with a CSP + HSTS-on-HTTPS (outer to the layer above, which sends none).
app.add_middleware(AuthRateLimitMiddleware)
app.add_middleware(GatewaySecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(CSRFMiddleware)
# Idempotency middleware for financial operations (must be after auth)
app.add_middleware(IdempotencyMiddleware)
logger.info(
    "HTTPS redirect + rate limit + security headers + request ID + CSRF + Idempotency middleware applied"
)

# Identity must be OUTSIDE Idempotency: middleware is registered last-outside,
# so this has to be added after IdempotencyMiddleware in order to resolve
# request.state.user_id before the idempotency scope is computed.
app.add_middleware(IdentityMiddleware)

# Locale detection middleware (must be after CORS, before auth)
app.add_middleware(LocaleMiddleware)
logger.info("✅ Locale detection middleware applied")

# P0: the spider firewall (honeypot -> circuit breaker -> WAF -> anomaly scoring)
# was implemented in services.security.middleware but never mounted, so those
# layers inspected no production traffic. Mounted last => outermost => it sees
# the request first. Rate limiting is delegated to the RateLimitMiddleware
# mounted above, which already enforces a per-IP budget correctly.
from services.security.middleware import SpiderFirewallMiddleware

_trusted_proxies = getattr(_settings, "trusted_proxies", "") or ""
app.add_middleware(
    SpiderFirewallMiddleware,
    redis_client=_redis_client,
    enable_rate_limit=False,
    trusted_proxies=_trusted_proxies,
)
logger.info(
    "✅ Spider firewall mounted (honeypot + circuit breaker + WAF + anomaly); trusted_proxies=%s",
    _trusted_proxies or "(none: X-Forwarded-For ignored)",
)

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

    # Gate the diagnostic detail on the explicit debug flag, not on an environment
    # string. The previous gate keyed off ``app_env == "development"``, which a
    # misconfigured ENVIRONMENT silently satisfied, so every unhandled 500 in
    # production returned the raw exception text, the exception class name and the
    # request path. A stable error id is returned instead so support can correlate
    # the client-side report with the server-side traceback via the request id.
    request_id = getattr(request.state, "request_id", None)
    error_id = request_id or uuid.uuid4().hex

    content = {
        "detail": "Internal server error",
        "error_id": error_id,
        "path": str(request.url.path),
    }
    if _settings.debug:
        content["detail"] = safe_error_detail(exc)
        content["error_type"] = type(exc).__name__

    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
    )
    if request_id:
        response.headers["X-Request-ID"] = str(request_id)
    return response


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Reference dataset (data/manual/*.sqlite) is not provisioned.

    Mirrors the honesty contract used by the reference-store 503s: log the full
    driver message server-side (it names the local file path) but return a
    generic, non-revealing 503 to the client, with an error_id for correlation.
    FastApi/Starlette dispatches FileNotFoundError here in preference to the
    catch-all Exception handler below, so this covers every loader-backed route
    (manual_data + elevation_grid._site_latlon) in one place.
    """
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    request_id = getattr(request.state, "request_id", None)
    error_id = request_id or uuid.uuid4().hex
    response = JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Reference dataset not provisioned; run scripts/import_manual_data.py",
            "error_id": error_id,
            "path": str(request.url.path),
        },
    )
    if request_id:
        response.headers["X-Request-ID"] = str(request_id)
    return response


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors.

    Starlette raises one 404 for two very different situations: "no route
    matched this path" (detail ``"Not Found"``) and an endpoint or
    dependency that deliberately raised ``HTTPException(404, ...)`` with a
    real reason ("Product not found", "Order not found"). Both landed in
    this handler, so a missing product reported itself as "Endpoint not
    found" — a routing message for a data problem, which sends a client
    looking for a typo in the URL instead of a stale id. Routing misses
    keep the descriptive body; endpoint 404s pass their own detail
    through.
    """
    detail = getattr(exc, "detail", None)
    if detail and detail != "Not Found":
        return JSONResponse(status_code=404, content={"detail": detail})
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
# Landscape / Territory (BG-001, BG-016, BG-025, BG-026)
app.include_router(landscape_territories_router.router)
app.include_router(landscape_governance_router.router)
# Scientific Modules
app.include_router(soil.router)
app.include_router(satellite.router)
app.include_router(carbon.router)
app.include_router(watershed.router)
app.include_router(scenarios.router)

# AI & Assistant
#
# Note: `ai.py`'s chat endpoint was at `POST /chat` (same path as `ai_chat.py`),
# creating a route conflict at `/api/v1/ai/chat`. Resolved by renaming `ai.py`'s
# RAG endpoint to `POST /rag` — no shadowing, no order-dependent matching.
app.include_router(ai_chat.router)
app.include_router(ai.router)
app.include_router(ai_analysis.router)

# Economy & Marketplace
app.include_router(ecowallet.router)
app.include_router(marketplace.router)
# Buyer ratings & reviews — the e-commerce trust half of the marketplace
app.include_router(marketplace_reviews.router)
# Village Development Hub — extends marketplace with village development features
app.include_router(village_hub.router)
# Rangeland (مرتع) endpoints — BG-014 (closed)
app.include_router(rangeland.router)
# EcoCoin/LMS/ecotourism module status endpoints: written, tested and previously
# unreachable because nothing in this file ever included them.
app.include_router(tourism_router.router, tags=["tourism"])
# Rural/tribal tourism lifecycle (P2-17): guides, tours and bookings over the
# services.tourism service layer, mounted beside the honest status stub above.
app.include_router(tourism_api_router, tags=["tourism"])

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
app.include_router(content_public.router)
app.include_router(models_router.router, tags=["models"])
app.include_router(elevation.router, tags=["elevation"])
app.include_router(support.router, tags=["support"])
app.include_router(manual_data.router, tags=["manual-data"])
app.include_router(dashboard.router)
app.include_router(contact.router, tags=["contact"])
app.include_router(pilot.router, tags=["pilot"])
app.include_router(newsletter.router, tags=["newsletter"])

# ── Routers that existed as tested, importable modules with a declared read
#    contract but no include_router() anywhere in this file. A page bound to
#    any of these paths rendered a permanent error state until now.
#    Each one is mounted at its own declared prefix with no extra prefix, so
#    scripts/check-mounted-routes.mjs can verify the result against the
#    running app rather than trusting the wiring by eye.

# Compliance: KYC/AML, greenwashing, credit bridge. require_user for reads,
# require_admin for any verdict or issuance (see the router's own docstring).
app.include_router(compliance.router, tags=["compliance"])
# Scientific motors: /motors/*. require_admin / get_current_user.
app.include_router(motors.router, tags=["motors"])
# OGC API - Features / WaterML. Public standard surface, read-only by design.
app.include_router(ogc_router.router, tags=["ogc"])
# LMS: public course catalogue; progress routes are scoped by a Supabase JWT
# and RLS, never by a caller-supplied user id.
app.include_router(lms.router, tags=["lms"])
# Supabase pass-through. Every user-scoped route resolves the token to a user
# id first; the two /admin/* routes delegate the role check to the
# admin_set_role RPC, so authorisation is enforced in the database, not here.
app.include_router(supabase_proxy.router, tags=["supabase"])
# HyDroMa scientific validation: read-only run/checks/reference-data contract.
app.include_router(validation_router.router, tags=["validation"])
# Livestock: /livestock/animal-types is a static capability catalogue. The
# simulate/forage POSTs are stateless in-process computation, the same posture
# as the already-mounted /api/v1/analyses and /api/v1/simulation compute routes.
app.include_router(livestock_router.router, tags=["livestock"])
# Unversioned legacy simulation surface (/simulation/simulators). The versioned
# /api/v1/simulation router is mounted above; this one is kept because the
# capability catalogue it serves is not a duplicate of anything.
app.include_router(simulation_legacy_router.router, tags=["simulation"])

# Legal & Registry (Phase 2)
app.include_router(legal_texts.router)
app.include_router(tool_registry.router)
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
app.include_router(finance_consolidation_router.router, tags=["finance"])
app.include_router(inventory_router.router, tags=["inventory"])
app.include_router(hydroma_economics.router, tags=["hydroma-economics"])
app.include_router(hydroma_carbon.router, tags=["hydroma-carbon"])
app.include_router(hydroma_climate.router, tags=["hydroma-climate"])
app.include_router(hydroma_neuro.router, tags=["plant-neuro"])
app.include_router(iot_devices.router, tags=["iot-devices"])
app.include_router(insurance.router, tags=["insurance"])

# ============================================================================
# SECURITY POSTURE & CARBON AUDIT
# ============================================================================
# Both of these existed as importable modules that no request could reach:
# nothing in this file ever included them, so a defined router is not a served
# one. The security router reads the live ``app.middleware_stack`` and is the
# only endpoint that reports which firewall layers are actually mounted. The
# audit router drives the SECURITY DEFINER RPCs from
# supabase/migrations/0006_audit_credits.sql.
app.include_router(security_router.router)
app.include_router(audit.router)

# Sponsorship: labelled funder recognition, not advertising. The public
# router takes no user, visitor or referrer parameter, so contextual placement
# is structural rather than a promise. See services/sponsors/policy.py.
from services.sponsors.routers import (
    admin as sponsors_admin,
)
from services.sponsors.routers import (
    sponsors as sponsors_public,
)

app.include_router(sponsors_public.router, tags=["sponsors"])
app.include_router(sponsors_admin.router, prefix="", tags=["admin-sponsors"])

# ---------------------------------------------------------------------------
# Daneshyar (knowledge) + Tasmimyar (decision) bridge. These routers existed as
# importable modules but had no include_router() anywhere, so every path they
# declared was unreachable. Mounted here at each router's own declared prefix.
from services.knowledge.router import router as knowledge_router
from services.tasmimyar import decision_service

# Daneshyar — knowledge entries / collections + RAG provenance.
app.include_router(knowledge_router, tags=["knowledge"])
# Tasmimyar — traceable decisions via EngineGateway.make_decision (guarded so a
# missing FastAPI bound degrades to "not mounted" instead of crashing import).
if decision_service.HAS_ROUTER:
    app.include_router(decision_service.router, tags=["tasmimyar"])

# P7 governance over HTTP. services/village/api.py declared a scoped router
# (cross-village isolation enforced server-side) that was never included, so
# the P7 workflow was unreachable. Mounted at its own declared prefix; the
# route-count pin grew by this mount — a deliberate delta, recorded here.
from services.village.api import router as village_governance_router

app.include_router(village_governance_router, tags=["village-governance"])

# Compute jobs (P13): authenticated and owner-scoped (a job carries another
# user's input/output/error data). The boundary policy declared this mount,
# but the include was missing, so the router lived only in its own tests.
from services.jobs.router import router as jobs_router

app.include_router(jobs_router, tags=["jobs"])

# P9 compliance registry over HTTP. It shares the /api/v1/compliance prefix
# with the carbon/KYC router (disjoint leaves), and every endpoint scopes the
# caller to their own subject unless they hold an approver role.
from services.compliance.api import router as compliance_registry_router

app.include_router(compliance_registry_router, tags=["compliance"])

# P8 tourism safety/refunds/incidents. Declared the same /api/v1/tourism
# prefix as the tours router (disjoint leaves); collections are scoped to the
# caller unless they hold an approver role.
from services.tourism.api.safety import router as tourism_safety_router

app.include_router(tourism_safety_router, tags=["tourism"])

# Nine gateway routers that were defined but never included (26 routes
# unreachable until now). Their modules are imported with the other gateway
# routers above; each is mounted at the prefix it declares.
app.include_router(ecosystem.router, tags=["ecosystem"])
app.include_router(climate.router, tags=["climate"])
app.include_router(lab.router, tags=["lab"])
app.include_router(community.router, tags=["community"])
app.include_router(culture.router, tags=["culture"])
app.include_router(economy.router, tags=["economy"])
app.include_router(nature.router, tags=["nature"])
app.include_router(water.router, tags=["water-signature"])
app.include_router(ai_advice_router.router, tags=["ai"])


# ============================================================================
# API VERSIONING
# ============================================================================

API_VERSION = "1.0.0"


@app.middleware("http")
async def add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = API_VERSION
    return response


@app.get("/api/version", tags=["health"])
async def api_version():
    """API version information."""
    return {
        "version": API_VERSION,
        "api_version": API_VERSION,
        "service": "api-gateway",
        "environment": _settings.app_env,
    }


# ============================================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================================
@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API info and links."""
    return {
        "name": "Eco Nojin API",
        "version": getattr(_settings, "api_version", "0.1.0"),
        "api_version": API_VERSION,
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


# ---------------------------------------------------------------------------
# Stable API-v1 surface (GET /api/v1/motors, /api/v1/rules, /api/v1/units).
#
# Included AFTER the health endpoints above on purpose: ``api/v1/router.py``
# also declares GET /api/v1/health (a terse {status, version}). Starlette
# matches the first registered route, so including this router here keeps the
# rich health payload defined above authoritative while still exposing the real
# motor inventory at /api/v1/motors (backed by scientific_motors/registry).
from services.api_gateway.api.v1 import router as api_v1_router

app.include_router(api_v1_router)


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
