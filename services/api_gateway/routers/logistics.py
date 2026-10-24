"""API gateway wiring for the logistics router (plan v2.0, phase 3).

`main.py` imports `from .routers import logistics`; the actual implementation
lives in ``services.logistics.routers.logistics`` and is re-exported here so
the gateway keeps a single source of truth for the API surface.

Both names are re-exported. ``router`` is what the gateway mounts and what the
unit tests reach for; dropping it emptied this module, and eight test modules
that do ``from services.api_gateway.routers import logistics; logistics.router``
failed at collection.
"""

from services.logistics.routers.logistics import router

__all__ = ["router"]
