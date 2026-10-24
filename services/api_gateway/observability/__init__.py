"""
Observability Package
=====================
"""

from services.api_gateway.observability.request_logging import StructuredLoggingMiddleware
from services.api_gateway.observability.structured_logger import (
    correlation_context,
    get_correlation_id,
    get_logger,
    log_background_task,
    log_cache_operation,
    log_db_query,
    log_error,
    log_external_call,
    log_request,
    log_request_response,
    log_response,
    set_correlation_id,
    setup_structured_logging,
)

__all__ = [
    "StructuredLoggingMiddleware",
    "correlation_context",
    "get_correlation_id",
    "get_logger",
    "log_background_task",
    "log_cache_operation",
    "log_db_query",
    "log_error",
    "log_external_call",
    "log_request",
    "log_request_response",
    "log_response",
    "set_correlation_id",
    "setup_structured_logging",
]
