"""Security status & anti-phishing endpoints (Phase 8-C)."""

import sys
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from services.security import pqcrypto, waf as waf_mod
from services.security.anti_phishing import check_email_auth, domain_squatting, page_clone_signature
from services.security.audit import recent_events
from services.security.honeypot import TRAP_PATHS, honeypot
from services.security.middleware import circuit_breaker
from services.security.waf import waf_engine

router = APIRouter(prefix="/api/v1/security", tags=["security"])


class PhishingCheck(BaseModel):
    domain: str | None = None
    url: str | None = None


#: The two header middlewares in this repo disagree about their name lookup:
#: the mounted one keeps its mapping on the class, the unmounted one keeps it
#: at module level. Reading both is what lets ``/status`` describe the layer
#: that is actually running.
_HEADER_MIDDLEWARE = "SecurityHeadersMiddleware"
_CSP_HEADER = "Content-Security-Policy"


def _mounted_middleware_entries(request: Request) -> list[tuple[str, type | None]]:
    """(class name, class) for each middleware actually stacked on this app.

    Reads the live stack rather than a hardcoded list, so a layer cannot be
    reported as active while sitting unregistered. Handles both the
    ``MiddlewareStack.middlewares`` shape and a plain nested ``.app`` chain.
    """
    entries: list[tuple[str, type | None]] = []
    stack = getattr(request.app, "middleware_stack", None)
    for mw in getattr(stack, "middlewares", ()) or ():
        cls = getattr(mw, "cls", None)
        entries.append((getattr(cls, "__name__", ""), cls))
    layer = stack
    guard = 0
    while layer is not None and guard < 64:
        entries.append((type(layer).__name__, type(layer)))
        layer = getattr(layer, "app", None)
        guard += 1
    return entries


def _mounted_middleware(request: Request) -> set[str]:
    """Class names of the middleware actually stacked on this app."""
    return {name for name, _ in _mounted_middleware_entries(request)}


def _declared_headers(cls: type) -> dict[str, str]:
    """The header map a middleware class would actually send on a response."""
    headers = getattr(cls, "HEADERS", None)
    if isinstance(headers, dict):
        return headers
    module = sys.modules.get(getattr(cls, "__module__", "") or "")
    module_headers = getattr(module, "_HEADERS", None)
    return module_headers if isinstance(module_headers, dict) else {}


def _csp_report(request: Request) -> dict[str, Any]:
    """Whether a Content-Security-Policy is really sent, and which one.

    This was a hardcoded string, ``"self + free data providers"``, describing
    the policy in ``services/security/headers.py`` -- a middleware that is *not*
    mounted. The mounted ``SecurityHeadersMiddleware`` comes from
    ``services.api_gateway.security`` and declares no CSP at all, so the
    endpoint asserted a header the gateway never sent. Deriving the value from
    the mounted class is the only version of this field that can stay true when
    the header layer changes.
    """
    for name, cls in _mounted_middleware_entries(request):
        if name != _HEADER_MIDDLEWARE or cls is None:
            continue
        value = _declared_headers(cls).get(_CSP_HEADER)
        source = f"{cls.__module__}.{name}"
        if value:
            return {"enforced": True, "policy": value, "source": source}
        return {
            "enforced": False,
            "policy": None,
            "source": source,
            "note": (
                "SecurityHeadersMiddleware is mounted but declares no "
                "Content-Security-Policy, so no CSP header is sent"
            ),
        }
    return {
        "enforced": False,
        "policy": None,
        "source": None,
        "note": f"no {_HEADER_MIDDLEWARE} in the stack",
    }


#: Layers that sit on the request path. `anti_phishing` is excluded on purpose:
#: it is invoked by endpoint, not by middleware, and listing it here would make
#: the posture look weaker than it is.
_REQUEST_PATH_LAYERS = (
    "waf",
    "honeypot",
    "anomaly",
    "circuit_breaker",
    "rate_limit",
    "headers",
    "csrf",
    "https_redirect",
    "request_id",
    "tenant",
    "idempotency",
    "upload_size",
)

#: Layers worth having but not part of a hard security floor.
_ADVISORY_LAYERS = ("locale", "cors", "rbac_audit")


@router.get("/status")
async def security_status(request: Request) -> dict[str, Any]:
    """Live status of every firewall layer, read from the real app stack.

    The top-level ``status`` is computed, not asserted. It used to be the
    literal ``"ok"``, so the endpoint kept reporting a healthy posture even if
    every layer had been unmounted -- which is precisely the situation this
    endpoint exists to detect.
    """
    mounted = _mounted_middleware(request)
    firewall = "SpiderFirewallMiddleware" in mounted

    layers = {
        "waf": {
            "active": firewall,
            "enforcement": "spider_firewall" if firewall else "not_mounted",
            "rules": len(waf_mod._RULES),
            "blocks": len(waf_engine.events),
        },
        "honeypot": {
            "active": firewall,
            "enforcement": "spider_firewall" if firewall else "not_mounted",
            "traps": len(TRAP_PATHS),
            "hits": len(honeypot.hits),
        },
        "anomaly": {
            "active": firewall,
            "enforcement": "spider_firewall" if firewall else "not_mounted",
            "mode": "behavior-scoring",
        },
        "circuit_breaker": {
            "active": firewall,
            "blocked_ips": len(circuit_breaker._blocked),
        },
        "rate_limit": {
            "active": "RateLimitMiddleware" in mounted,
            "enforcement": "gateway" if "RateLimitMiddleware" in mounted else "not_mounted",
            "mode": "per-ip sliding window",
        },
        "headers": {
            "active": _HEADER_MIDDLEWARE in mounted,
            "enforcement": "gateway" if _HEADER_MIDDLEWARE in mounted else "not_mounted",
            "csp": _csp_report(request),
        },
        "csrf": {
            "active": "CSRFMiddleware" in mounted,
            "enforcement": "gateway" if "CSRFMiddleware" in mounted else "not_mounted",
        },
        "https_redirect": {"active": "HTTPSRedirectMiddleware" in mounted},
        "request_id": {"active": "RequestIDMiddleware" in mounted},
        "tenant": {"active": "TenantMiddleware" in mounted},
        "idempotency": {
            # Two middlewares are involved and only one of them existed before
            # phase 4: IdentityMiddleware resolves the JWT subject onto
            # request.state.user_id, and IdempotencyMiddleware consumes it.
            # Reporting only the second hid the first.
            "active": "IdentityMiddleware" in mounted and "IdempotencyMiddleware" in mounted,
            "identity": "IdentityMiddleware" in mounted,
            "enforcement": (
                "gateway"
                if "IdentityMiddleware" in mounted and "IdempotencyMiddleware" in mounted
                else "not_mounted"
            ),
        },
        "locale": {"active": "LocaleMiddleware" in mounted},
        "upload_size": {"active": "UploadSizeMiddleware" in mounted},
        "cors": {"active": "CORSMiddleware" in mounted},
        "anti_phishing": {
            "active": True,
            "enforcement": "on_demand_endpoint",
            "note": "not request-path middleware; invoked via POST /anti-phishing",
            "trusted_domains": ["econojin.ir", "econojin.com"],
        },
        "post_quantum": pqcrypto.status(),
        "encryption": {
            "at_rest": "supabase-managed + field-level Fernet helper",
            "in_transit": "TLS (deploy)",
        },
        "rbac_audit": {
            "active": firewall,
            "enforcement": "spider_firewall" if firewall else "not_mounted",
            "store": "supabase + local-jsonl fallback",
        },
    }

    missing = [name for name in _REQUEST_PATH_LAYERS if not layers.get(name, {}).get("active")]
    if missing:
        status = "degraded"
        reason = (
            f"{len(missing)} request-path security layer(s) are not mounted: "
            + ", ".join(missing)
            + ". The gateway is running without them."
        )
    elif _csp_report(request)["enforced"] is not True:
        status = "degraded"
        reason = (
            "every request-path layer is mounted, but no Content-Security-Policy header "
            "is sent. See layers.headers.csp."
        )
    else:
        status = "ok"
        reason = None

    return {
        "status": status,
        "reason": reason,
        "missing_layers": missing,
        "advisory_layers": list(_ADVISORY_LAYERS),
        "layers": layers,
        "mount_point": "verified against app.middleware_stack",
        "note": (
            "وضعیت هر لایه از پشتهٔ واقعی middleware خوانده می‌شود؛ "
            "لایهٔ ثبت‌نشده با active=false و enforcement=not_mounted گزارش می‌شود."
        ),
    }


@router.post("/anti-phishing")
async def anti_phishing(payload: PhishingCheck, request: Request):
    """Domain squatting check (+ live SPF/DKIM/DMARC when a domain is given,
    + structural clone signature when a public URL is given)."""
    result = {"status": "ok"}
    if payload.domain:
        result["squatting"] = domain_squatting(payload.domain)
        result["email_auth"] = check_email_auth(payload.domain)
    if payload.url:
        result["clone"] = page_clone_signature(payload.url)
    if payload.domain is None and payload.url is None:
        result = {"status": "error", "error": "domain یا url را بفرستید"}
    return result


@router.get("/events")
async def security_events(limit: int = 20):
    """Recent security events (local store; cloud mirror via migration 0007)."""
    return {"status": "ok", "events": recent_events(limit=min(limit, 100))}
