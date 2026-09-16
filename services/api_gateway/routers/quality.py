"""API gateway wiring for the quality-assurance router (plan v2.0, phase 3).

`main.py` imports `from .routers import quality`; the actual implementation
lives in ``services.quality_assurance.routers.quality`` and is re-exported
here so the gateway keeps a single source of truth for the API surface.
"""
from services.quality_assurance.routers.quality import router  # noqa: F401
