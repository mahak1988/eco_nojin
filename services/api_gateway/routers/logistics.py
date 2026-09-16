"""API gateway wiring for the logistics router (plan v2.0, phase 3).

`main.py` imports `from .routers import logistics`; the actual implementation
lives in ``services.logistics.routers.logistics`` and is re-exported here so
the gateway keeps a single source of truth for the API surface.
"""
from services.logistics.routers.logistics import router  # noqa: F401
