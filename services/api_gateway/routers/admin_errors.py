"""Admin Errors Router - Error management endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.api_gateway.auth import require_admin_with_mfa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/errors", tags=["admin-errors"])


class ErrorResponse(BaseModel):
    id: str
    path: str
    method: str
    status_code: int
    error_type: str
    message: str
    user_id: Optional[str] = None
    created_at: str
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None


class ErrorAckRequest(BaseModel):
    acknowledged_by: str


# In-memory error store (replace with actual database)
ERROR_STORE = []


def add_error(path: str, method: str, status_code: int, error_type: str, message: str, user_id: Optional[str] = None):
    """Add error to store."""
    ERROR_STORE.append({
        "id": f"err-{len(ERROR_STORE)+1}",
        "path": path,
        "method": method,
        "status_code": status_code,
        "error_type": error_type,
        "message": message,
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
        "acknowledged": False,
        "acknowledged_at": None,
        "acknowledged_by": None,
    })
    # Keep only last 1000 errors
    if len(ERROR_STORE) > 1000:
        ERROR_STORE.pop(0)


@router.get("", response_model=List[ErrorResponse])
async def list_errors(
    status_code: Optional[int] = Query(None),
    error_type: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_admin_with_mfa),
):
    """List recent API errors with filters."""
    errors = ERROR_STORE[::-1]  # Most recent first

    if status_code:
        errors = [e for e in errors if e["status_code"] == status_code]
    if error_type:
        errors = [e for e in errors if e["error_type"] == error_type]
    if acknowledged is not None:
        errors = [e for e in errors if e["acknowledged"] == acknowledged]

    return errors[offset:offset+limit]


@router.get("/{error_id}", response_model=ErrorResponse)
async def get_error(
    error_id: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Get error details."""
    error = next((e for e in ERROR_STORE if e["id"] == error_id), None)
    if not error:
        raise HTTPException(404, "Error not found")
    return error


@router.post("/{error_id}/ack", response_model=ErrorResponse)
async def acknowledge_error(
    error_id: str,
    payload: ErrorAckRequest,
    current_user=Depends(require_admin_with_mfa),
):
    """Acknowledge an error."""
    error = next((e for e in ERROR_STORE if e["id"] == error_id), None)
    if not error:
        raise HTTPException(404, "Error not found")

    error["acknowledged"] = True
    error["acknowledged_at"] = datetime.now(UTC).isoformat()
    error["acknowledged_by"] = payload.acknowledged_by
    return error


@router.post("/{error_id}/resolve", response_model=ErrorResponse)
async def resolve_error(
    error_id: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Mark error as resolved (acknowledged + removed from active)."""
    error = next((e for e in ERROR_STORE if e["id"] == error_id), None)
    if not error:
        raise HTTPException(404, "Error not found")

    error["acknowledged"] = True
    error["acknowledged_at"] = datetime.now(UTC).isoformat()
    error["acknowledged_by"] = "auto-resolved"
    return error


@router.post("/{error_id}/suppress")
async def suppress_error(
    error_id: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Suppress future occurrences of this error."""
    error = next((e for e in ERROR_STORE if e["id"] == error_id), None)
    if not error:
        raise HTTPException(404, "Error not found")

    error["suppressed"] = True
    return {"message": "Error suppressed"}


@router.get("/summary")
async def error_summary(
    current_user=Depends(require_admin_with_mfa),
):
    """Get error summary statistics."""
    from collections import Counter
    total = len(ERROR_STORE)
    by_type = Counter(e["error_type"] for e in ERROR_STORE)
    by_status = Counter(e["status_code"] for e in ERROR_STORE)
    unacknowledged = sum(1 for e in ERROR_STORE if not e["acknowledged"])

    return {
        "total": total,
        "unacknowledged": unacknowledged,
        "by_type": dict(by_type),
        "by_status": dict(by_status),
    }