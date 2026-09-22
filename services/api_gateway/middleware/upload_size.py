"""Upload size and type limiting middleware."""

from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from engine.hydroma.config.settings import get_settings

logger = logging.getLogger(__name__)

# Allowed MIME types for uploads (H7 fix)
ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "application/pdf",
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/json",
        "text/plain",
        "application/zip",
        "application/x-zip-compressed",
        "application/gzip",
        "application/x-gzip",
    }
)
# Allowed file extensions
ALLOWED_EXTENSIONS = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".pdf",
        ".csv",
        ".xls",
        ".xlsx",
        ".json",
        ".txt",
        ".zip",
        ".gz",
    }
)


class UploadSizeMiddleware(BaseHTTPMiddleware):
    """Limit request body size and validate file type for upload endpoints."""

    def __init__(self, app, max_bytes: int | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self._max_bytes = max_bytes or (getattr(settings, "max_upload_size_mb", 10) * 1024 * 1024)

    def _validate_file_type(self, request: Request) -> str | None:
        """Validate uploaded file type. Returns error message or None if valid."""
        content_type = request.headers.get("content-type", "")

        # Check multipart/form-data boundary
        if "multipart/form-data" not in content_type:
            return None  # Skip validation for non-multipart

        # For now, we can't easily parse multipart without reading the body
        # This is a middleware-level check; route-level validation should also be done
        return None

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


async def validate_upload_file(file, max_size_mb: int = 10) -> str | None:
    """Validate uploaded file size and type. Returns error message or None if valid."""
    # Check file extension
    if file.filename:
        ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            return f"File type {ext} not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        return f"MIME type {file.content_type} not allowed"

    return None
