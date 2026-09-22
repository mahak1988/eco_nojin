"""
Structured JSON Logger with Correlation IDs
============================================

Provides structured logging with automatic correlation ID propagation,
context enrichment, and multiple output formats.
"""

import contextvars
import json
import logging
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import wraps
from typing import Any, Dict, Optional

import structlog
from structlog.stdlib import ProcessorFormatter

# Context variable for correlation ID
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)

# Context variable for extra context
extra_context_var: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "extra_context", default={}
)

service_name_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "service_name", default="eco-nojin-api"
)
environment_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "environment", default="development"
)


def get_correlation_id() -> str:
    """Get current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> contextvars.Token[str]:
    """Set correlation ID in context and return its reset token."""
    return correlation_id_var.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from context."""
    correlation_id_var.set("")


def get_extra_context() -> Dict[str, Any]:
    """Get extra context from context variable."""
    return extra_context_var.get().copy()


def set_extra_context(context: Dict[str, Any]) -> None:
    """Set extra context in context variable."""
    extra_context_var.set(context)


def update_extra_context(key: str, value: Any) -> None:
    """Update a single key in extra context."""
    ctx = extra_context_var.get().copy()
    ctx[key] = value
    extra_context_var.set(ctx)


def clear_extra_context() -> None:
    """Clear extra context."""
    extra_context_var.set({})


@contextmanager
def correlation_context(correlation_id: Optional[str] = None, **extra_context):
    """Context manager for correlation ID and extra context."""
    cid_token = correlation_id_var.set(correlation_id) if correlation_id is not None else None
    context_token = extra_context_var.set(extra_context) if extra_context else None

    try:
        yield
    finally:
        if context_token is not None:
            extra_context_var.reset(context_token)
        if cid_token is not None:
            correlation_id_var.reset(cid_token)


def add_correlation_id(logger, method_name, event_dict):
    """Structlog processor to add correlation ID to all log entries."""
    cid = correlation_id_var.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def add_extra_context(logger, method_name, event_dict):
    """Structlog processor to add extra context to all log entries."""
    ctx = extra_context_var.get()
    if ctx:
        event_dict.update(ctx)
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """Structlog processor to add ISO timestamp."""
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def add_service_info(logger, method_name, event_dict):
    """Structlog processor to add service info."""
    event_dict["service"] = service_name_var.get()
    event_dict["environment"] = environment_var.get()
    return event_dict


def setup_structured_logging(
    log_level: str = "INFO",
    json_output: bool = True,
    service_name: str = "eco-nojin-api",
    environment: str = "development",
) -> structlog.BoundLogger:
    """
    Configure structured logging with structlog.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: Whether to output JSON (True) or console format (False)
        service_name: Service name for log entries
        environment: Environment name (development, staging, production)

    Returns:
        Configured structlog logger
    """
    service_name_var.set(service_name)
    environment_var.set(environment)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        add_extra_context,
        add_timestamp,
        add_service_info,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        # JSON output for production/log aggregation
        formatter = ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        # Human-readable console output for development
        formatter = ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )

    # Configure root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Return configured logger
    return structlog.get_logger(service_name)


def get_logger(name: str = "eco-nojin") -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Convenience functions for common log patterns
def log_request(logger: structlog.BoundLogger, method: str, path: str, **extra):
    """Log an incoming HTTP request."""
    logger.info("http_request", method=method, path=path, **extra)


def log_response(
    logger: structlog.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **extra,
):
    """Log an HTTP response."""
    logger.info(
        "http_response",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra,
    )


def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    context: str = "",
    **extra,
):
    """Log an error with full context."""
    logger.error(
        "error",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context,
        exc_info=True,
        **extra,
    )


def log_external_call(
    logger: structlog.BoundLogger,
    service: str,
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    **extra,
):
    """Log an external API call."""
    logger.info(
        "external_call",
        service=service,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra,
    )


def log_db_query(
    logger: structlog.BoundLogger,
    query: str,
    duration_ms: float,
    rows_affected: Optional[int] = None,
    **extra,
):
    """Log a database query."""
    logger.debug(
        "db_query",
        query=query[:200],  # Truncate long queries
        duration_ms=duration_ms,
        rows_affected=rows_affected,
        **extra,
    )


def log_cache_operation(
    logger: structlog.BoundLogger,
    operation: str,
    key: str,
    hit: Optional[bool] = None,
    duration_ms: Optional[float] = None,
    **extra,
):
    """Log a cache operation."""
    logger.debug(
        "cache_operation",
        operation=operation,
        key=key,
        hit=hit,
        duration_ms=duration_ms,
        **extra,
    )


def log_background_task(
    logger: structlog.BoundLogger,
    task_name: str,
    status: str,  # started, completed, failed
    duration_ms: Optional[float] = None,
    **extra,
):
    """Log a background task."""
    logger.info(
        "background_task",
        task_name=task_name,
        status=status,
        duration_ms=duration_ms,
        **extra,
    )


# Decorator for automatic request/response logging
def log_request_response(logger: structlog.BoundLogger):
    """Decorator to automatically log request/response."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now(UTC)
            try:
                result = await func(*args, **kwargs)
                duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
                logger.debug(
                    "function_call",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    status="success",
                )
                return result
            except Exception as e:
                duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
                log_error(logger, e, context=f"function {func.__name__}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now(UTC)
            try:
                result = func(*args, **kwargs)
                duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
                logger.debug(
                    "function_call",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    status="success",
                )
                return result
            except Exception as e:
                duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
                log_error(logger, e, context=f"function {func.__name__}")
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
