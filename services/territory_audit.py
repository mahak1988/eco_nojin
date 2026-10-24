"""Audit trail logging middleware/handler for territory endpoints."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from database.hub import hub
from services.api_gateway.errors import safe_error_detail

Base = declarative_base()


class AuditTrail(Base):
    """Audit trail record for territory API operations."""

    __tablename__ = "audit_trails"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_body = Column(Text, nullable=True)
    response_status = Column(String(10), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    territory_id = Column(String(100), nullable=True, index=True)
    action = Column(String(50), nullable=True, index=True)  # CREATE, READ, UPDATE, DELETE, VERIFY
    success = Column(String(10), nullable=False)  # true, false
    error_message = Column(Text, nullable=True)


def _extract_territory_id(path: str) -> str | None:
    """Extract territory/village ID from path."""
    import re
    match = re.search(r'/territories/([^/]+)', path)
    if match:
        return match.group(1)
    match = re.search(r'/landscape/villages/([^/]+)', path)
    if match:
        return match.group(1)
    return None


def _determine_action(method: str, path: str) -> str:
    """Determine the action type from method and path."""
    if method == "POST" and "/territories" in path and path.endswith("/verify"):
        return "VERIFY"
    elif method == "POST" and "/landscape/villages" in path:
        return "CREATE"
    elif method == "GET" and ("/territories" in path or "/landscape/villages" in path):
        return "READ"
    elif method in ("PATCH", "PUT") and ("/territories" in path or "/landscape/villages" in path):
        return "UPDATE"
    elif method == "DELETE":
        return "DELETE"
    return "UNKNOWN"


class AuditTrailMiddleware(BaseHTTPMiddleware):
    """Middleware to log audit trails for territory API endpoints."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("audit_trail")

    async def dispatch(self, request: Request, call_next: Callable):
        # Only audit territory-related endpoints
        path = request.url.path
        if not ("/territories" in path or "/landscape/villages" in path):
            return await call_next(request)

        start_time = datetime.now(UTC)
        territory_id = _extract_territory_id(path)
        action = _determine_action(request.method, path)
        user_id = getattr(request.state, "user_id", None)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        # Read request body (for non-GET requests)
        request_body = None
        if request.method in ("POST", "PATCH", "PUT"):
            try:
                body = await request.body()
                if body:
                    request_body = body.decode("utf-8")[:5000]  # Limit size
            except Exception:
                request_body = "[unreadable]"

        # Process request
        try:
            response = await call_next(request)
            response_status = str(response.status_code)
            success = "true" if 200 <= response.status_code < 400 else "false"
            error_message = None
        except Exception as e:
            response_status = "500"
            success = "false"
            error_message = safe_error_detail(e)[:1000]
            raise
        finally:
            response_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Log to database
            try:
                async with hub.get_async_session() as session:
                    audit = AuditTrail(
                        timestamp=start_time,
                        method=request.method,
                        path=path,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent[:500] if user_agent else None,
                        request_body=request_body,
                        response_status=response_status,
                        response_time_ms=response_time_ms,
                        territory_id=territory_id,
                        action=action,
                        success=success,
                        error_message=error_message,
                    )
                    session.add(audit)
                    await session.commit()
            except Exception as log_error:
                # Don't fail the request if audit logging fails
                self.logger.error(f"Audit trail logging failed: {log_error}")

        return response


def setup_audit_trail(app):
    """Add audit trail middleware to the app."""
    app.add_middleware(AuditTrailMiddleware)