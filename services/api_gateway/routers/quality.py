"""API gateway wiring for the quality-assurance router (plan v2.0, phase 3).

`main.py` imports `from .routers import quality`; the actual implementation
lives in ``services.quality_assurance.routers.quality`` and is re-exported
here so the gateway keeps a single source of truth for the API surface.

The re-export is load-bearing. `main.py:604` does
`app.include_router(quality.router, ...)`, and the unit tests reach for the
same attribute, so removing the import left this module empty and broke
collection of eight test modules.
"""

from services.quality_assurance.routers.quality import router

__all__ = ["router"]
