"""Admin Router - Main entry point including all sub-routers.

This file serves as the main admin router that includes all sub-routers
for different admin functionalities. Each sub-router is in its own file
for better maintainability and separation of concerns.

Sub-routers:
- admin_users: User management (list, block, unblock, bulk actions)
- admin_content: Content management (CRUD, versions, translations, AI draft)
- admin_bots: Bot platform management (list, toggle, restart)
- admin_errors: Error tracking (list, acknowledge, bulk actions)
- admin_settings: Platform settings (list, update, bulk update)
- admin_models: Local LLM models (list, pull, load, stop, delete)
- admin_overview: Platform metrics and health
- admin_security: Login history and security audit
"""

from __future__ import annotations

from fastapi import APIRouter

# Import sub-routers
from . import (
    admin_users,
    admin_content,
    admin_bots,
    admin_errors,
    admin_settings,
    admin_models,
    admin_overview,
    admin_security,
)

router = APIRouter(tags=["admin"])

# Include all sub-routers
router.include_router(admin_users.router)
router.include_router(admin_content.router)
router.include_router(admin_bots.router)
router.include_router(admin_errors.router)
router.include_router(admin_settings.router)
router.include_router(admin_models.router)
router.include_router(admin_overview.router)
router.include_router(admin_security.router)

# Legacy health endpoint (backward compatibility)
@router.get("/health")
async def admin_health():
    """Legacy health endpoint - redirects to overview health."""
    return {
        "status": "ok",
        "message": "Admin router active. Use /admin/overview/health for detailed health.",
        "sub_routers": [
            "users", "content", "bots", "errors",
            "settings", "models", "overview", "security"
        ],
    }