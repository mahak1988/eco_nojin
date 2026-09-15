"""Upload size limiting middleware."""
from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from engine.hydroma.config.settings import get_settings

logger = logging.getLogger(__name__)


class UploadSizeMiddleware(BaseHTTPMiddleware):
    """Limit request body size for upload endpoints."""

    def __init__(self, app, max_bytes: int | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self._max_bytes = max_bytes or (getattr(settings, "max_upload_size_mb", 10) * 1024 * 1024)

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self._max_bytes:
                        logger.warning(
                            "Upload too large: %d bytes (max %d)",
                            size,
                            self._max_bytes,
                        )
                        return JSONResponse(
                            status_code=413,
                            content={
                                "detail": f"Request body too large. Max size: {self._max_bytes} bytes",
                                "max_bytes": self._max_bytes,
                            },
                        )
                except ValueError:
                    pass

        response = await call_next(request)
        return response
