"""Dynamic module registration for API Gateway.

Registers optional service modules (marketplace, tourism, landscape) that may
not be available in all deployments. Failures are silently logged and do not
prevent application startup.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Registry of optional modules: (module_path, router_attr, prefix, tags)
OPTIONAL_MODULES: list[tuple[str, str, str, list[str]]] = [
    ("services.marketplace.api", "router", "/api/v1/marketplace", ["marketplace"]),
    ("services.tourism.api", "router", "/api/v1/tourism", ["tourism"]),
    ("services.landscape.api", "router", "/api/v1/landscape", ["landscape"]),
]


def register_new_modules(app: FastAPI) -> dict[str, bool]:
    """Register all optional modules. Returns registration status map."""
    results: dict[str, bool] = {}

    for module_path, router_attr, prefix, tags in OPTIONAL_MODULES:
        try:
            module = __import__(module_path, fromlist=[router_attr])
            router = getattr(module, router_attr)
            app.include_router(router, prefix=prefix, tags=tags)
            results[module_path] = True
            logger.info(f"✅ Registered optional module: {module_path}")
        except (ImportError, AttributeError) as exc:
            results[module_path] = False
            logger.debug(f"⚠️ Skipped optional module {module_path}: {exc}")
        except Exception as exc:
            results[module_path] = False
            logger.error(f"❌ Failed to register {module_path}: {exc}")

    return results
