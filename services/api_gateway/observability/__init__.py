"""
Observability Package
=====================
"""

from services.api_gateway.observability.request_logging import StructuredLoggingMiddleware
from services.api_gateway.observability.structured_logger import (
    setup_structured_logging,
    get_logger,
    get_correlation_id,
    set_correlation_id,
    correlation_context,
    log_request,
    log_response,
    log_error,
    log_external_call,
    log_db_query,
    log_cache_operation,
    log_background_task,
    log_request_response,
)

__all__ = [
    "setup_structured_logging",
    "get_logger",
    "get_correlation_id",
    "set_correlation_id",
    "correlation_context",
    "log_request",
    "log_response",
    "log_error",
    "log_external_call",
    "log_db_query",
    "log_cache_operation",
    "log_background_task",
    "log_request_response",
    "StructuredLoggingMiddleware",
]
