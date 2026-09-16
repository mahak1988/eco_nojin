"""API gateway wiring for the dispute-resolution router (plan v2.0, phase 3).

`main.py` imports `from .routers import disputes`; the actual implementation
lives in ``services.dispute_resolution.routers.disputes`` and is re-exported
here so the gateway keeps a single source of truth for the API surface.
"""
from services.dispute_resolution.routers.disputes import router  # noqa: F401
