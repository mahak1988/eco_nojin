"""API gateway wiring for the dispute-resolution router (plan v2.0, phase 3).

`main.py` imports `from .routers import disputes`; the actual implementation
lives in ``services.dispute_resolution.routers.disputes`` and is re-exported
here so the gateway keeps a single source of truth for the API surface.

The re-export is load-bearing. `main.py:605` does
`app.include_router(disputes.router, ...)`, so removing the import left this
module empty and broke collection of eight test modules.
"""

from services.dispute_resolution.routers.disputes import router

__all__ = ["router"]
