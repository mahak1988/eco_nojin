from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request

from services.api_gateway.observability.structured_logger import (
    correlation_id_var,
    get_logger,
    set_correlation_id,
)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, logger: structlog.BoundLogger | None = None) -> None:
        super().__init__(app)
        self.logger = logger or get_logger("econojin.http")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = getattr(request.state, "request_id", None) or request.headers.get(
            "X-Request-ID"
        ) or str(uuid.uuid4())
        request.state.request_id = request_id
        correlation_token = set_correlation_id(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            self.logger.error(
                "http_error",
                method=request.method,
                path=request.url.path,
                request_id=request_id,
                status_code=500,
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=True,
            )
            raise
        else:
            self.logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
            )
            return response
        finally:
            correlation_id_var.reset(correlation_token)
