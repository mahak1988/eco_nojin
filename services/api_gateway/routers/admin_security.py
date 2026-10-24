"""Admin Security Router - Login history and security audit."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select

from database.hub import hub
from services.api_gateway.auth import require_security_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["admin-security"])


class LoginHistoryResponse(BaseModel):
    id: str
    user_id: str
    email: str
    ip_address: str
    user_agent: str | None = None
    success: bool
    failure_reason: str | None = None
    location: str | None = None
    created_at: str


class SecurityAuditResponse(BaseModel):
    total_logins_24h: int
    successful_logins: int
    failed_logins: int
    unique_users: int
    unique_ips: int
    top_countries: list[dict]
    suspicious_activities: list[dict]


def get_db():
    """Session dependency (generator form, so the session is closed).

    ``Depends(get_db)`` works too â€” FastAPI uses the return value
    of a plain callable directly â€” but it never closes the session, and a
    ``StaticPool`` engine owns exactly one connection, so the unclosed
    sessions accumulate. Same pattern as ``admin_users.get_db``.
    """
    with hub.get_session() as session:
        yield session


@router.get("/logins", response_model=list[LoginHistoryResponse])
async def get_login_history(
    user_id: Annotated[str | None, Query()] = None,
    success: Annotated[bool | None, Query()] = None,
    hours: Annotated[int, Query(ge=1, le=720)] = 24,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: Annotated[Any, Depends(require_security_admin)] = None,
    db: Annotated[Any, Depends(get_db)] = None,
):
    """Get login history with filters."""
    from database.models import LoginHistory

    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    stmt = select(LoginHistory).where(LoginHistory.created_at >= cutoff.isoformat())

    if user_id:
        stmt = stmt.where(LoginHistory.user_id == user_id)
    if success is not None:
        stmt = stmt.where(LoginHistory.success == success)

    stmt = stmt.order_by(desc(LoginHistory.created_at)).limit(limit).offset(offset)
    result = db.execute(stmt)
    items = result.scalars().all()

    return [
        LoginHistoryResponse(
            id=str(item.id),
            user_id=str(item.user_id),
            email=item.email,
            ip_address=item.ip_address,
            user_agent=item.user_agent,
            success=item.success,
            failure_reason=item.failure_reason,
            location=item.location,
            # ``LoginHistory.created_at`` is a DateTime column; pydantic v2
            # does not coerce datetime -> str, so passing the raw value
            # failed response validation (HTTP 500) on the first row.
            created_at=item.created_at.isoformat() if item.created_at else "",
        )
        for item in items
    ]


@router.get("/audit", response_model=SecurityAuditResponse)
async def get_security_audit(
    hours: Annotated[int, Query(ge=1, le=720)] = 24,
    current_user: Annotated[Any, Depends(require_security_admin)] = None,
    db: Annotated[Any, Depends(get_db)] = None,
):
    """Get security audit summary."""

    from database.models import LoginHistory

    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    stmt = select(LoginHistory).where(LoginHistory.created_at >= cutoff.isoformat())
    result = db.execute(stmt)
    logins = result.scalars().all()

    total = len(logins)
    successful = sum(1 for l in logins if l.success)
    failed = total - successful
    unique_users = len({l.user_id for l in logins})
    unique_ips = len({l.ip_address for l in logins})

    # Top countries (mock)
    top_countries = [
        {"country": "Iran", "count": int(total * 0.7)},
        {"country": "Germany", "count": int(total * 0.15)},
        {"country": "USA", "count": int(total * 0.1)},
        {"country": "Other", "count": int(total * 0.05)},
    ]

    # Suspicious activities (mock)
    suspicious = [
        {
            "type": "brute_force",
            "ip": "192.168.1.100",
            "attempts": 15,
            "time": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        },
        {
            "type": "credential_stuffing",
            "ip": "10.0.0.50",
            "attempts": 8,
            "time": (datetime.now(UTC) - timedelta(hours=5)).isoformat(),
        },
    ]

    return SecurityAuditResponse(
        total_logins_24h=total,
        successful_logins=successful,
        failed_logins=failed,
        unique_users=unique_users,
        unique_ips=unique_ips,
        top_countries=top_countries,
        suspicious_activities=suspicious,
    )
