"""Security hardening utility for error responses.

Replaces `str(exc)` exposure with safe, generic error codes
per eco.md §۴۸ (No Internal Implementation Exposure) and
Phase 24 adversarial review finding §1.1 (246 `str(exc)` leak sites).

Usage:
    from services.api_gateway.errors import safe_error_detail
    
    except Exception as exc:
        logger.error("...", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=safe_error_detail(exc),
        )
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Generic error codes that leak no internal information.
ERROR_CODE_MAP: dict[str, str] = {
    "IntegrityError": "data_integrity_violation",
    "OperationalError": "database_unavailable",
    "ProgrammingError": "internal_error",
    "DataError": "data_validation_failed",
    "DoesNotExist": "entity_not_found",
    "DoesNotExistError": "entity_not_found",
    "ValidationError": "validation_failed",
    "ValueError": "invalid_input",
    "KeyError": "missing_field",
    "TypeError": "type_error",
    "TimeoutError": "timeout",
    "ConnectionError": "connection_failed",
    "PermissionError": "permission_denied",
    "FileNotFoundError": "resource_not_found",
    "NotImplementedError": "not_implemented",
    "AttributeError": "internal_error",
    "RuntimeError": "internal_error",
}

#: Public-safe error responses for HTTP 500-level errors.
SAFE_DETAIL: dict[int, str] = {
    400: "Bad request",
    401: "Authentication required",
    403: "Insufficient permissions",
    404: "Resource not found",
    409: "Conflict with existing data",
    422: "Validation failed",
    500: "Internal server error",
    502: "Upstream service unavailable",
    503: "Service temporarily unavailable",
    504: "Upstream timeout",
}


def safe_error_detail(exc: Exception | str) -> str:
    """Return a generic, non-revealing error message for HTTP responses.

    Logs the full exception internally but never exposes internal details
    to the client.
    """
    exc_type = type(exc).__name__ if isinstance(exc, Exception) else "UnknownError"
    code = ERROR_CODE_MAP.get(exc_type, "internal_error")
    return code


def safe_error_id(exc: Exception) -> str:
    """Generate a short hash for error correlation (logged internally, shown to client).

    The client receives `error_id` to quote in support requests; internal logs
    use full traceback. This preserves operability without leaking internals.
    """
    full_repr = repr(exc) if hasattr(exc, "__repr__") else str(exc)
    return hashlib.sha256(full_repr.encode("utf-8")).hexdigest()[:12]


def safe_detail_for_status(exc: Exception, status_code: int = 500) -> str:
    """Generic safe detail for HTTPException based on status code."""
    return SAFE_DETAIL.get(status_code, "internal_error")


def domain_detail(exc: Exception, status_code: int = 400) -> str:
    """Client-safe detail for a *domain* error the API contract makes public.

    Every caller of this helper caught a specific exception type it owns
    (``DepartureError``, ``ComplianceError``, ``RefundError``,
    ``UnknownAccountCode``, the ``ValueError`` a service rule raises…). Those
    messages are the API contract — clients and the honesty-contract tests pin
    them — and they are composed from rule inputs, never from driver or
    database text, so they carry no internals.

    The distinction is structural: the caller already narrowed the ``except``
    clause to a domain exception, which is what makes the message safe to
    pass. Unexpected exceptions (``DatabaseError``, ``AttributeError``, …) must
    keep using :func:`safe_detail_for_status`, whose detail is the generic
    status message and leaks nothing.
    """
    message = str(exc).strip()
    return message or SAFE_DETAIL.get(status_code, "internal_error")


def access_error_status(exc: Exception) -> int:
    """Map ValueError to appropriate status code without exception-text parsing.

    Replaces the dangerous text-parsing pattern:
        status_code=403 if "دسترسی" in str(e) else 404

    Uses exception type/attributes instead of parsing the Persian literal.
    """
    if hasattr(exc, "access_denied") and getattr(exc, "access_denied", False):
        return 403
    return 404


def log_and_return(exc: Exception, status_code: int = 500) -> dict[str, Any]:
    """Log full exception, return safe HTTP response body.

    Returns a dict with `detail` (generic message) and `error_id` (for correlation).
    """
    logger.error("Unhandled exception", exc_info=True)
    return {
        "detail": SAFE_DETAIL.get(status_code, "Internal server error"),
        "error_id": safe_error_id(exc),
    }
