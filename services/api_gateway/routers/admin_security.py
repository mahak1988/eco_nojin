"""Admin Security Router - Login history and security audit."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from database.hub import hub
from database import models
from services.api_gateway.auth import require_security_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["admin-security"])


class LoginHistoryResponse(BaseModel):
    id: str
    user_id: str
    email: str
    ip_address: str
    user_agent: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None
    location: Optional[str] = None
    created_at: str


class SecurityAuditResponse(BaseModel):
    total_logins_24h: int
    successful_logins: int
    failed_logins: int
    unique_users: int
    unique_ips: int
    top_countries: List[dict]
    suspicious_activities: List[dict]


@router.get("/logins", response_model=List[LoginHistoryResponse])
async def get_login_history(
    user_id: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_security_admin),
    db=Depends(hub.get_session),
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
            created_at=item.created_at,
        )
        for item in items
    ]


@router.get("/audit", response_model=SecurityAuditResponse)
async def get_security_audit(
    hours: int = Query(24, ge=1, le=720),
    current_user=Depends(require_security_admin),
    db=Depends(hub.get_session),
):
    """Get security audit summary."""
    from database.models import LoginHistory
    from collections import Counter

    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    stmt = select(LoginHistory).where(LoginHistory.created_at >= cutoff.isoformat())
    result = db.execute(stmt)
    logins = result.scalars().all()

    total = len(logins)
    successful = sum(1 for l in logins if l.success)
    failed = total - successful
    unique_users = len(set(l.user_id for l in logins))
    unique_ips = len(set(l.ip_address for l in logins))

    # Top countries (mock)
    top_countries = [
        {"country": "Iran", "count": int(total * 0.7)},
        {"country": "Germany", "count": int(total * 0.15)},
        {"country": "USA", "count": int(total * 0.1)},
        {"country": "Other", "count": int(total * 0.05)},
    ]

    # Suspicious activities (mock)
    suspicious = [
        {"type": "brute_force", "ip": "192.168.1.100", "attempts": 15, "time": (datetime.now(UTC) - timedelta(hours=2)).isoformat()},
        {"type": "credential_stuffing", "ip": "10.0.0.50", "attempts": 8, "time": (datetime.now(UTC) - timedelta(hours=5)).isoformat()},
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