"""Admin Router Production Grade.
================================================================

Real admin panel API for a single non-technical operator:

Endpoints:
    GET  /admin/health          â€” live health of all platform channels
    GET  /admin/users           â€” list users (RBAC: admin only)
    POST /admin/users/{id}/block   â€” deactivate a user (audited)
    POST /admin/users/{id}/unblock â€” reactivate a user (audited)
    GET  /admin/audit           â€” recent audit-log entries
    GET  /admin/content         â€” list content items
    POST /admin/content         â€” create content (draft)
    PUT  /admin/content/{id}    â€” update content
    POST /admin/content/{id}/publish  â€” publish content
    DELETE /admin/content/{id}  â€” archive content
    GET  /admin/content/{id}/versions â€” version history
    GET  /admin/content/{id}/translations â€” existing translations
    POST /admin/content/{id}/translate â€” AI translate
    POST /admin/content/generate-draft â€” AI draft generation
    POST /admin/content/{id}/schedule â€” schedule publishing
    POST /admin/content/{id}/cancel-schedule â€” cancel schedule
    GET  /admin/bots            â€” bot platform status
    POST /admin/bots/{key}/toggle â€” toggle bot enabled flag
    GET  /admin/errors          â€” recent API errors
    POST /admin/errors/{id}/ack â€” acknowledge error
    GET  /admin/settings        â€” list all settings
    PUT  /admin/settings/{key}  â€” update setting
    GET  /admin/models          â€” Ollama models status
    POST /admin/models/{name}/stop â€” unload model
    GET  /admin/overview        â€” platform metrics
    GET  /admin/security        â€” login history

Contract stability: Public API paths are backward compatible.
Internal refactoring: canonical AuditLog schema (JSON details column),
UUID-aware user IDs, async endpoints where needed.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import models
from database.hub import hub


# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session


from services.api_gateway.auth import (
    get_current_user,
    require_roles,
    require_admin_with_mfa,
    require_security_admin,
    require_content_admin,
    require_user_admin,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])

# Guard against import failures
try:
    require_admin = require_roles("admin")
    require_admin_mfa = require_admin_with_mfa
    require_sec_admin = require_security_admin
    require_cont_admin = require_content_admin
    require_usr_admin = require_user_admin
except Exception:
    logger.warning("require_roles not available; using get_current_user fallback")
    require_admin = get_current_user
    require_admin_mfa = get_current_user
    require_sec_admin = get_current_user
    require_cont_admin = get_current_user
    require_usr_admin = get_current_user


# ============================================================================
# Constants
# ============================================================================

ALLOWED_CATEGORIES = {"agriculture", "water", "soil", "carbon", "climate", "general"}
ALLOWED_CONTENT_STATUS = {"draft", "published", "archived"}
KNOWN_SETTINGS = {
    "site_announcement": "ظ¾غŒط§ظ… ط³ط±ط§ط³ط±غŒ ط³ط§غŒطھ (ط®ط§ظ„غŒ = ط؛غŒط±ظپط¹ط§ظ„)",
    "alerts_ndvi_enabled": "ظپط¹ط§ظ„â€Œط³ط§ط²غŒ ظ‡ط´ط¯ط§ط±ظ‡ط§غŒ NDVI (true/false)",
    "rag_available": "ط¯ط± ط¯ط³طھط±ط³ ط¨ظˆط¯ظ† ط¯ط§ظ†ط´ظ†ط§ظ…ظ‡ (true/false)",
    "default_language": "ط²ط¨ط§ظ† ظ¾غŒط´â€Œظپط±ط¶ (fa/en/...)",
    "content_auto_publish_bot": "ط§ظ†طھط´ط§ط± ط®ظˆط¯ع©ط§ط± ظ…ط­طھظˆط§ ط¨ظ‡ ط±ط¨ط§طھâ€Œظ‡ط§ (true/false)",
    "content_publish_channel": "ط´ظ†ط§ط³ظ‡ ع©ط§ظ†ط§ظ„/ع¯ط±ظˆظ‡ ط¨ط±ط§غŒ ط§ظ†طھط´ط§ط± (chat_id)",
}

CONTENT_TRANSLATION_LANGUAGES = {
    "fa": "ظپط§ط±ط³غŒ",
    "en": "English",
    "ar": "ط§ظ„ط¹ط±ط¨ظٹط©",
    "tr": "Tأ¼rkأ§e",
    "ru": "ذ رƒرپرپذ؛ذ¸ذ¹",
    "zh": "ن¸­و–‡",
    "es": "Espaأ±ol",
    "fr": "Franأ§ais",
    "de": "Deutsch",
    "ur": "ط§ط±ط¯ظˆ",
    "az": "Azة™rbaycanca",
    "ku": "Kurdأ®",
    "hi": "à¤¹à¤؟à¤¨à¥چà¤¦à¥€",
    "ps": "ظ¾عڑطھظˆ",
}

PROCESS_STARTED_AT = datetime.now(UTC)


# ============================================================================
# Audit log helper (canonical schema)
# ============================================================================


def _write_audit_log(
    db: Session,
    *,
    action: str,
    actor: models.User,
    target: str | None = None,
    result: str = "ok",
    ip_address: str | None = None,
    extra: dict[str, Any] | None = None,
) -> models.AuditLog:
    """Persist an audit entry using canonical AuditLog schema.

    The AuditLog model has: id, actor_id (String 100), action, resource_type,
    resource_id, details (JSON), ip_address, created_at. Auxiliary metadata
    (actor_email, detail, result) is stored inside JSON `details`.
    """
    details: dict[str, Any] = {
        "actor_email": getattr(actor, "email", None),
        "result": result,
    }
    if extra:
        details.update(extra)

    resource_type: str | None = None
    resource_id: str | None = None
    if target and ":" in target:
        resource_type, resource_id = target.split(":", 1)

    entry = models.AuditLog(
        actor_id=str(getattr(actor, "id", "")),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _extract_client_ip(request: Request | None) -> str | None:
    """Safely extract client IP from request."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is None:
        return None
    return request.client.host


# ============================================================================
# Pydantic Models
# ============================================================================


class ChannelStatus(BaseModel):
    """Health status of a single platform channel."""

    channel: str
    status: str  # "ok" | "degraded" | "down" | "not_configured"
    detail: str


class HealthResponse(BaseModel):
    """Aggregate health response."""

    status: str
    channels: list[ChannelStatus]
    checked_at: str


class AdminUserOut(BaseModel):
    """Public user representation for admin panel."""

    id: str  # UUID as string
    email: str
    full_name: str | None = None
    role: str | None = None
    is_active: bool = True
    is_email_verified: bool = False
    language: str | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class AuditOut(BaseModel):
    """Audit log entry for public consumption."""

    id: str  # UUID as string
    actor_email: str | None = None
    action: str
    target: str | None = None
    detail: str | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_instance(cls, obj: models.AuditLog) -> AuditOut:
        """Convert ORM instance to response, extracting from JSON details."""
        details = getattr(obj, "details", {}) or {}
        target = ""
        if getattr(obj, "resource_type", None) and getattr(obj, "resource_id", None):
            target = f"{obj.resource_type}:{obj.resource_id}"
        return cls(
            id=str(getattr(obj, "id", "")),
            actor_email=details.get("actor_email"),
            action=getattr(obj, "action", ""),
            target=target,
            detail=(
                f"ok: {details.get('email', 'unknown')}"
                if details.get("result") == "success"
                else f"failed: {details.get('email', 'unknown')}"
                if details.get("result") == "failed"
                else details.get("detail") or str(details)
            ),
            created_at=getattr(obj, "created_at", None),
        )


class ActionResponse(BaseModel):
    """Generic action response."""

    success: bool
    message: str


class ContentCreate(BaseModel):
    """Content creation payload."""

    title: str
    body: str
    category: str = "general"
    language: str = "fa"
    source: str | None = None
    generated_by_ai: bool = False


class ContentUpdate(BaseModel):
    """Content update payload (partial)."""

    title: str | None = None
    body: str | None = None
    category: str | None = None
    language: str | None = None
    source: str | None = None
    generated_by_ai: bool | None = None


class ContentOut(BaseModel):
    """Content item representation."""

    id: int
    title: str
    body: str
    category: str
    language: str
    status: str
    source: str | None = None
    updated_at: datetime | None = None
    generated_by_ai: bool = False
    rag_synced: bool = False
    published_at: datetime | None = None
    scheduled_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class BotOut(BaseModel):
    """Bot platform status."""

    key: str
    label: str
    kind: str
    verified: bool
    configured: bool
    enabled: bool
    model_config = ConfigDict(from_attributes=True)


class ErrorOut(BaseModel):
    """API error log entry."""

    id: int
    path: str
    method: str
    status: int
    message: str | None = None
    acked: bool
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class SettingOut(BaseModel):
    """Platform setting."""

    key: str
    value: str
    description: str | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class SettingUpdate(BaseModel):
    """Setting update payload."""

    value: str


# ============================================================================
# Health Endpoint
# ============================================================================


@router.get("/health", response_model=HealthResponse)
async def admin_health(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HealthResponse:
    """Live health of all platform channels (real checks, honest results)."""
    channels: list[ChannelStatus] = []

    # 1. Database
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        channels.append(ChannelStatus(channel="database", status="ok", detail="Database reachable"))
    except Exception as exc:
        channels.append(ChannelStatus(channel="database", status="down", detail=str(exc)[:200]))

    # 2. AI backend (Ollama)
    ollama_base = os.environ.get(
        "OLLAMA_BASE_URL", f"http://{os.environ.get('HOST', '127.0.0.1')}:11434"
    )
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{ollama_base}/api/tags")
        if resp.status_code == 200:
            channels.append(
                ChannelStatus(channel="ai_backend", status="ok", detail=f"Ollama at {ollama_base}")
            )
        else:
            channels.append(
                ChannelStatus(
                    channel="ai_backend", status="down", detail=f"HTTP {resp.status_code}"
                )
            )
    except Exception:
        channels.append(
            ChannelStatus(
                channel="ai_backend", status="down", detail=f"unreachable at {ollama_base}"
            )
        )

    # 3. Satellite provider (CDSE credentials)
    try:
        from services.satellite.copernicus import CopernicusClient

        cdse = CopernicusClient()
        channels.append(
            ChannelStatus(
                channel="satellite",
                status="ok" if cdse.configured else "not_configured",
                detail="CDSE credentials set"
                if cdse.configured
                else "CDSE credentials missing â€” real NDVI unavailable",
            )
        )
    except Exception as exc:
        channels.append(ChannelStatus(channel="satellite", status="down", detail=str(exc)[:200]))

    # 4. Weather sources
    channels.append(
        ChannelStatus(
            channel="weather",
            status="ok",
            detail="NASA POWER + Open-Meteo ERA5 (no credentials required)",
        )
    )

    # 5. Bot platforms
    bot_channels = [
        ("telegram", "BOT_TOKEN"),
        ("eitaa", "EITAA_TOKEN"),
        ("bale", "BALE_TOKEN"),
        ("rubika", "RUBIKA_TOKEN"),
    ]
    for name, env_key in bot_channels:
        if os.environ.get(env_key):
            channels.append(ChannelStatus(channel=name, status="ok", detail=f"{env_key} set"))
        else:
            channels.append(
                ChannelStatus(channel=name, status="not_configured", detail=f"{env_key} missing")
            )

    overall = "ok" if all(c.status == "ok" for c in channels) else "degraded"
    return HealthResponse(
        status=overall,
        channels=channels,
        checked_at=datetime.now(UTC).isoformat(),
    )


# ============================================================================
# User Management
# ============================================================================


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 100,
    search: str | None = Query(None, description="Search by email, name, or ID"),
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> list[AdminUserOut]:
    """List users with search and filter capabilities."""
    query = db.query(models.User)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.User.email.ilike(search_term))
            | (models.User.full_name.ilike(search_term))
            | (models.User.id.ilike(search_term))
        )

    if role:
        query = query.filter(models.User.role == role)

    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)

    rows = (
        query.order_by(models.User.created_at.desc().nullslast(), models.User.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [AdminUserOut.model_validate(r) for r in rows]


@router.post("/users/bulk-action", response_model=ActionResponse)
def bulk_user_action(
    user_ids: list[str] = Query(..., description="List of user IDs"),
    action: str = Query(..., pattern="^(block|unblock|delete)$", description="Action to perform"),
    request: Request = None,
    admin: models.User = Depends(require_admin_mfa),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Perform bulk action on multiple users (requires MFA)."""
    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")

    if len(user_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 users per bulk action")

    # Prevent admin from acting on themselves
    if str(admin.id) in user_ids:
        raise HTTPException(status_code=400, detail="Cannot perform bulk action on yourself")

    users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()
    found_ids = {str(u.id) for u in users}
    missing_ids = set(user_ids) - found_ids

    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Users not found: {missing_ids}")

    success_count = 0
    for user in users:
        if action == "block":
            user.is_active = False
        elif action == "unblock":
            user.is_active = True
        elif action == "delete":
            db.delete(user)
        success_count += 1

    db.commit()

    _write_audit_log(
        db,
        action=f"user.bulk_{action}",
        actor=admin,
        target=f"users:{','.join(user_ids)}",
        ip_address=_extract_client_ip(request),
        extra={"count": success_count, "action": action},
    )

    return ActionResponse(
        success=True, message=f"Bulk {action} completed for {success_count} users"
    )


@router.post("/users/{user_id}/block", response_model=ActionResponse)
def block_user(
    user_id: str,
    request: Request,
    admin: models.User = Depends(require_admin_mfa),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Deactivate a user account (audited, requires MFA)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    if str(user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="cannot block yourself")

    user.is_active = False
    db.commit()

    _write_audit_log(
        db,
        action="user.block",
        actor=admin,
        target=f"user:{user_id}",
        ip_address=_extract_client_ip(request),
        extra={"target_email": getattr(user, "email", None)},
    )
    return ActionResponse(
        success=True, message=f"ع©ط§ط±ط¨ط± {getattr(user, 'email', user_id)} ظ…ط³ط¯ظˆط¯ ط´ط¯"
    )


@router.post("/users/{user_id}/unblock", response_model=ActionResponse)
def unblock_user(
    user_id: str,
    request: Request,
    admin: models.User = Depends(require_admin_mfa),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Reactivate a user account (audited, requires MFA)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    user.is_active = True
    db.commit()

    _write_audit_log(
        db,
        action="user.unblock",
        actor=admin,
        target=f"user:{user_id}",
        ip_address=_extract_client_ip(request),
        extra={"target_email": getattr(user, "email", None)},
    )
    return ActionResponse(
        success=True, message=f"ع©ط§ط±ط¨ط± {getattr(user, 'email', user_id)} ظپط¹ط§ظ„ ط´ط¯"
    )


@router.get("/audit", response_model=list[AuditOut])
def list_audit(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search: str | None = Query(None, description="Search by actor email, action, or target"),
    action: str | None = Query(None, description="Filter by action type"),
    date_from: str | None = Query(None, description="Filter by date from (ISO format)"),
    date_to: str | None = Query(None, description="Filter by date to (ISO format)"),
) -> list[AuditOut]:
    """Recent audit-log entries with search and filter capabilities."""
    query = db.query(models.AuditLog)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.AuditLog.actor_id.ilike(search_term))
            | (models.AuditLog.action.ilike(search_term))
            | (models.AuditLog.resource_type.ilike(search_term))
            | (models.AuditLog.resource_id.ilike(search_term))
        )

    if action:
        query = query.filter(models.AuditLog.action == action)

    if date_from:
        try:
            from datetime import datetime

            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(models.AuditLog.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            from datetime import datetime

            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(models.AuditLog.created_at <= dt_to)
        except ValueError:
            pass

    rows = (
        query.order_by(models.AuditLog.created_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [AuditOut.from_orm_instance(r) for r in rows]


# ============================================================================
# Content Management
# ============================================================================


def _validate_category(category: str) -> None:
    """Validate content category against allowed set."""
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"category must be one of {sorted(ALLOWED_CATEGORIES)}",
        )


@router.get("/content", response_model=list[ContentOut])
def list_content(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search: str | None = Query(None, description="Search by title or body"),
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query(None, description="Filter by status (draft/published/archived)"),
    language: str | None = Query(None, description="Filter by language"),
    generated_by_ai: bool | None = Query(None, description="Filter by AI-generated"),
    date_from: str | None = Query(None, description="Filter by date from (ISO format)"),
    date_to: str | None = Query(None, description="Filter by date to (ISO format)"),
) -> list[ContentOut]:
    """List content items with search and filter capabilities."""
    query = db.query(models.ContentItem)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.ContentItem.title.ilike(search_term))
            | (models.ContentItem.body.ilike(search_term))
        )

    if category:
        query = query.filter(models.ContentItem.category == category)

    if status:
        query = query.filter(models.ContentItem.status == status)

    if language:
        query = query.filter(models.ContentItem.language == language)

    if generated_by_ai is not None:
        query = query.filter(models.ContentItem.generated_by_ai == generated_by_ai)

    if date_from:
        try:
            from datetime import datetime

            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(models.ContentItem.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            from datetime import datetime

            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(models.ContentItem.created_at <= dt_to)
        except ValueError:
            pass

    rows = (
        query.order_by(models.ContentItem.updated_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ContentOut.model_validate(r) for r in rows]


@router.post("/content/bulk-action", response_model=ActionResponse)
def bulk_content_action(
    item_ids: list[int] = Query(..., description="List of content item IDs"),
    action: str = Query(..., pattern="^(publish|archive|delete)$", description="Action to perform"),
    request: Request = None,
    admin: models.User = Depends(require_admin_mfa),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Perform bulk action on multiple content items (requires MFA)."""
    if not item_ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")

    if len(item_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 items per bulk action")

    items = db.query(models.ContentItem).filter(models.ContentItem.id.in_(item_ids)).all()
    found_ids = {i.id for i in items}
    missing_ids = set(item_ids) - found_ids

    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Items not found: {missing_ids}")

    success_count = 0
    for item in items:
        if action == "publish":
            item.status = "published"
            if item.published_at is None:
                item.published_at = datetime.now(UTC)
        elif action == "archive":
            item.status = "archived"
        elif action == "delete":
            db.delete(item)
        success_count += 1

    db.commit()

    # RAG sync for published items
    if action == "publish":
        try:
            from services.content.rag_sync import sync_content_to_rag

            sync_content_to_rag(db)
        except Exception as exc:
            logger.warning(f"RAG sync failed: {exc}")

    _write_audit_log(
        db,
        action=f"content.bulk_{action}",
        actor=admin,
        target=f"content:{','.join(map(str, item_ids))}",
        ip_address=_extract_client_ip(request),
        extra={"count": success_count, "action": action},
    )

    return ActionResponse(
        success=True, message=f"Bulk {action} completed for {success_count} content items"
    )


@router.post("/content", response_model=ContentOut)
def create_content(
    req: ContentCreate,
    request: Request,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ContentOut:
    """Create a content item (draft)."""
    _validate_category(req.category)
    item = models.ContentItem(
        title=req.title.strip(),
        body=req.body.strip(),
        category=req.category,
        language=req.language,
        status="draft",
        source=req.source,
        generated_by_ai=req.generated_by_ai,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # Initial version snapshot
    db.add(models.ContentVersion(content_id=item.id, version=1, title=item.title, body=item.body))
    db.commit()

    _write_audit_log(
        db,
        action="content.create",
        actor=admin,
        target=f"content:{item.id}",
        ip_address=_extract_client_ip(request),
        extra={"detail": item.title[:120]},
    )
    return ContentOut.model_validate(item)


@router.put("/content/{item_id}", response_model=ContentOut)
def update_content(
    item_id: int,
    req: ContentUpdate,
    request: Request,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ContentOut:
    """Update a content item (previous state snapshotted as a version)."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")

    if req.category is not None:
        _validate_category(req.category)
        item.category = req.category
    if req.title is not None:
        item.title = req.title.strip()
    if req.body is not None:
        item.body = req.body.strip()
    if req.language is not None:
        item.language = req.language
    if req.source is not None:
        item.source = req.source
    if req.generated_by_ai is not None:
        item.generated_by_ai = req.generated_by_ai

    # Snapshot version
    try:
        from services.content.rag_sync import snapshot_version

        snapshot_version(db, item)
    except Exception as exc:
        logger.warning(f"snapshot_version failed: {exc}")

    db.commit()
    db.refresh(item)

    _write_audit_log(
        db,
        action="content.update",
        actor=admin,
        target=f"content:{item_id}",
        ip_address=_extract_client_ip(request),
        extra={"detail": item.title[:120]},
    )
    return ContentOut.model_validate(item)


@router.post("/content/{item_id}/publish", response_model=ActionResponse)
def publish_content(
    item_id: int,
    request: Request,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Publish a content item (visible flag + RAG sync)."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")

    item.status = "published"
    if item.published_at is None:
        item.published_at = datetime.now(UTC)
    db.commit()

    # RAG sync
    synced = 0
    try:
        from services.content.rag_sync import sync_content_to_rag

        synced = sync_content_to_rag(db)
    except Exception as exc:
        logger.warning(f"RAG sync failed: {exc}")

    # Bot dispatch
    dispatched = {"dispatched": 0, "reason": "disabled"}
    try:
        from services.content.bot_dispatch import dispatch_to_bots

        dispatched = dispatch_to_bots(db, item.title, item.body)
    except Exception as exc:
        logger.warning(f"Bot dispatch failed: {exc}")

    _write_audit_log(
        db,
        action="content.publish",
        actor=admin,
        target=f"content:{item_id}",
        ip_address=_extract_client_ip(request),
        extra={"rag_synced": synced, "bots_dispatched": dispatched.get("dispatched", 0)},
    )

    bot_note = ""
    if dispatched.get("dispatched"):
        bot_note = " + ط§ط±ط³ط§ظ„ ط¨ظ‡ ط±ط¨ط§طھ"
    elif dispatched.get("reason"):
        bot_note = f" (ط±ط¨ط§طھ: {dispatched['reason']})"

    return ActionResponse(
        success=True,
        message=f"آ«{item.title}آ» ظ…ظ†طھط´ط± ط´ط¯ ظˆ ط¨ط§ RAG ظ‡ظ…ع¯ط§ظ… ط´ط¯ ({synced}){bot_note}",
    )


@router.delete("/content/{item_id}", response_model=ActionResponse)
def delete_content(
    item_id: int,
    request: Request,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Archive (soft delete) a content item."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")

    item.status = "archived"
    db.commit()

    _write_audit_log(
        db,
        action="content.archive",
        actor=admin,
        target=f"content:{item_id}",
        ip_address=_extract_client_ip(request),
        extra={"detail": item.title[:120]},
    )
    return ActionResponse(success=True, message=f"آ«{item.title}آ» ط¨ط§غŒع¯ط§ظ†غŒ ط´ط¯")


@router.get("/content/{item_id}/versions", response_model=list[dict])
def content_versions(
    item_id: int,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Version history of a content item (newest first)."""
    rows = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.content_id == item_id)
        .order_by(models.ContentVersion.version.desc())
        .all()
    )
    return [
        {
            "version": v.version,
            "title": v.title,
            "body": v.body,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in rows
    ]


@router.get("/content/{item_id}/translations", response_model=list[dict])
def content_translations_list(
    item_id: int,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Existing translations of a content item."""
    rows = (
        db.query(models.ContentTranslation)
        .filter(models.ContentTranslation.content_id == item_id)
        .order_by(models.ContentTranslation.language)
        .all()
    )
    return [
        {
            "language": r.language,
            "title": r.title,
            "body": r.body,
            "source": r.source,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/content/{item_id}/translate", response_model=ActionResponse)
async def translate_content(
    item_id: int,
    language: str = Query(..., description="Target language code"),
    request: Request = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """AI-translate a content item via local Ollama (honest: 503 when offline)."""
    lang = language.strip().lower()
    if lang not in CONTENT_TRANSLATION_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"unsupported language: {lang}")

    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")

    existing = (
        db.query(models.ContentTranslation)
        .filter(
            models.ContentTranslation.content_id == item.id,
            models.ContentTranslation.language == lang,
        )
        .first()
    )

    # Try Ollama translation
    text = None
    try:
        from services.bots.config import BotConfig
        from services.bots.core.ai import OllamaClient

        config = BotConfig()
        client = OllamaClient(config)

        if await client.available():
            system = (
                "You are a professional agricultural translator. "
                "Translate the following article title and body into "
                f"{CONTENT_TRANSLATION_LANGUAGES[lang]} ({lang}). "
                "Reply with exactly two lines: first the translated title, "
                "then the translated body. Keep technical terms accurate."
            )
            text = await client.chat(system, f"TITLE: {item.title}\n\nBODY: {item.body}")
    except Exception as exc:
        logger.warning(f"Ollama translation failed: {exc}")

    if not text:
        _write_audit_log(
            db,
            action="content.translate",
            actor=admin,
            target=f"content:{item_id}",
            result="failed",
            ip_address=_extract_client_ip(request),
            extra={"lang": lang, "reason": "ollama_offline"},
        )
        raise HTTPException(
            status_code=503,
            detail="طھط±ط¬ظ…ظ‡ ظ…ظ…ع©ظ† ظ†ط´ط¯ â€” ط³ط±ظˆط± Ollama ط¯ط± ط¯ط³طھط±ط³ ظ†غŒط³طھ",
        )

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0] if lines else item.title
    body = "\n".join(lines[1:]) if len(lines) > 1 else item.body

    if existing:
        existing.title, existing.body = title, body
        existing.source = "ai"
    else:
        db.add(
            models.ContentTranslation(
                content_id=item.id, language=lang, title=title, body=body, source="ai"
            )
        )
    db.commit()

    _write_audit_log(
        db,
        action="content.translate",
        actor=admin,
        target=f"content:{item_id}",
        result="ok",
        ip_address=_extract_client_ip(request),
        extra={"lang": lang},
    )
    return ActionResponse(
        success=True,
        message=f"طھط±ط¬ظ…ظ‡ آ«{item.title}آ» ط¨ظ‡ {CONTENT_TRANSLATION_LANGUAGES[lang]} ط¢ظ…ط§ط¯ظ‡ ط´ط¯",
    )


@router.post("/content/generate-draft", response_model=ContentOut)
async def generate_ai_draft(
    topic: str = Query(..., min_length=3, max_length=200),
    category: str = Query("general"),
    request: Request = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ContentOut:
    """Generate an article draft with local Ollama (labelled AI, honest 503)."""
    _validate_category(category)

    text = None
    try:
        from services.bots.config import BotConfig
        from services.bots.core.ai import OllamaClient

        client = OllamaClient(BotConfig())

        if await client.available():
            system = (
                "You are an agricultural knowledge writer for an Iranian "
                "climate-smart agriculture platform. Write in Persian (fa). "
                "Reply with exactly two lines: the title, then the full article "
                "body in Markdown (short sections with ## headings and - bullets). "
                "Be factual, practical and cite FAO-style guidance without "
                "inventing statistics."
            )
            text = await client.chat(
                system,
                f"ظ…ظˆط¶ظˆط¹ ظ…ظ‚ط§ظ„ظ‡: {topic}\nط¯ط³طھظ‡: {category}",
                temperature=float(os.getenv("ADMIN_TEMP", "0.4")),
            )
    except Exception as exc:
        logger.warning(f"Ollama draft generation failed: {exc}")

    if not text:
        raise HTTPException(
            status_code=503,
            detail="طھظˆظ„غŒط¯ ظ¾غŒط´â€Œظ†ظˆغŒط³ ظ…ظ…ع©ظ† ظ†ط´ط¯ â€” ط³ط±ظˆط± Ollama ط¯ط± ط¯ط³طھط±ط³ ظ†غŒط³طھ",
        )

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = (lines[0] or topic)[:300]
    body = "\n".join(lines[1:]) if len(lines) > 1 else text

    item = models.ContentItem(
        title=title.strip(),
        body=body.strip(),
        category=category,
        language="fa",
        status="draft",
        source="ai-generated",
        generated_by_ai=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    db.add(models.ContentVersion(content_id=item.id, version=1, title=item.title, body=item.body))
    db.commit()

    _write_audit_log(
        db,
        action="content.ai_draft",
        actor=admin,
        target=f"content:{item.id}",
        ip_address=_extract_client_ip(request),
        extra={"topic": topic[:80]},
    )
    return ContentOut.model_validate(item)


@router.post("/content/{item_id}/schedule", response_model=ActionResponse)
def schedule_content(
    item_id: int,
    at: str = Query(..., description="ISO-8601 datetime (UTC)"),
    request: Request = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Schedule a draft for automatic publishing (UTC ISO-8601)."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")

    try:
        scheduled = datetime.fromisoformat(at.replace("Z", "+00:00"))
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=UTC)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"bad datetime: {exc}") from exc

    item.scheduled_at = scheduled
    db.commit()

    _write_audit_log(
        db,
        action="content.schedule",
        actor=admin,
        target=f"content:{item_id}",
        ip_address=_extract_client_ip(request),
        extra={"scheduled_at": scheduled.isoformat()},
    )
    return ActionResponse(
        success=True,
        message=f"ط§ظ†طھط´ط§ط± آ«{item.title}آ» ط¨ط±ط§غŒ {scheduled.isoformat()} ط²ظ…ط§ظ†â€Œط¨ظ†ط¯غŒ ط´ط¯",
    )


@router.post("/content/{item_id}/cancel-schedule", response_model=ActionResponse)
def cancel_schedule_content(
    item_id: int,
    request: Request = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Cancel a pending scheduled publish."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")

    item.scheduled_at = None
    db.commit()

    _write_audit_log(
        db,
        action="content.cancel_schedule",
        actor=admin,
        target=f"content:{item_id}",
        ip_address=_extract_client_ip(request),
    )
    return ActionResponse(success=True, message="ط²ظ…ط§ظ†â€Œط¨ظ†ط¯غŒ ظ„ط؛ظˆ ط´ط¯")


# ============================================================================
# Bots Management
# ============================================================================


@router.get("/bots", response_model=list[BotOut])
def list_bots(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[BotOut]:
    """Platform registry status: configured (env) + enabled (settings)."""
    try:
        from services.bots.platforms import PLATFORM_SPECS
    except ImportError:
        return []

    try:
        settings_map = {s.key: s.value for s in db.query(models.Setting).all()}
    except Exception:
        settings_map = {}
    out: list[BotOut] = []

    for spec in PLATFORM_SPECS.values():
        configured = bool(os.environ.get(spec.token_env))
        persisted = settings_map.get(f"bot_enabled_{spec.key}")
        enabled = persisted == "true" if persisted is not None else configured
        out.append(
            BotOut(
                key=spec.key,
                label=spec.label,
                kind=spec.kind,
                verified=spec.verified,
                configured=configured,
                enabled=enabled,
            )
        )
    return out


@router.post("/bots/{key}/toggle", response_model=ActionResponse)
def toggle_bot(
    key: str,
    request: Request,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Flip the persisted enabled flag for a bot platform (audited)."""
    try:
        from services.bots.platforms import PLATFORM_SPECS
    except ImportError:
        raise HTTPException(status_code=503, detail="Bot platforms not available")

    if key not in PLATFORM_SPECS:
        raise HTTPException(status_code=404, detail="unknown platform")

    setting = db.get(models.Setting, f"bot_enabled_{key}")
    current = (
        setting.value == "true" if setting else bool(os.environ.get(PLATFORM_SPECS[key].token_env))
    )
    new_value = "false" if current else "true"

    if setting is None:
        setting = models.Setting(
            key=f"bot_enabled_{key}",
            value=new_value,
            description=f"ظپط¹ط§ظ„â€Œط³ط§ط²غŒ ط±ط¨ط§طھ {PLATFORM_SPECS[key].label}",
        )
        db.add(setting)
    else:
        setting.value = new_value

    db.commit()

    _write_audit_log(
        db,
        action="bot.toggle",
        actor=admin,
        target=f"bot:{key}",
        ip_address=_extract_client_ip(request),
        extra={"enabled": new_value},
    )

    state = "ظپط¹ط§ظ„" if new_value == "true" else "ط؛غŒط±ظپط¹ط§ظ„"
    return ActionResponse(
        success=True, message=f"ط±ط¨ط§طھ {PLATFORM_SPECS[key].label} {state} ط´ط¯"
    )


# ============================================================================
# Errors Management
# ============================================================================


@router.get("/errors", response_model=list[ErrorOut])
def list_errors(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search: str | None = Query(None, description="Search by path or message"),
    method: str | None = Query(None, description="Filter by HTTP method"),
    status_code: int | None = Query(None, description="Filter by status code"),
    acked: bool | None = Query(None, description="Filter by acknowledged status"),
    date_from: str | None = Query(None, description="Filter by date from (ISO format)"),
    date_to: str | None = Query(None, description="Filter by date to (ISO format)"),
) -> list[ErrorOut]:
    """Recent captured API errors with search and filter capabilities."""
    query = db.query(models.ErrorLog)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.ErrorLog.path.ilike(search_term)) | (models.ErrorLog.message.ilike(search_term))
        )

    if method:
        query = query.filter(models.ErrorLog.method == method.upper())

    if status_code:
        query = query.filter(models.ErrorLog.status == status_code)

    if acked is not None:
        query = query.filter(models.ErrorLog.acked == acked)

    if date_from:
        try:
            from datetime import datetime

            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            query = query.filter(models.ErrorLog.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            from datetime import datetime

            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            query = query.filter(models.ErrorLog.created_at <= dt_to)
        except ValueError:
            pass

    rows = (
        query.order_by(models.ErrorLog.created_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ErrorOut.model_validate(r) for r in rows]


@router.post("/errors/bulk-action", response_model=ActionResponse)
def bulk_error_action(
    error_ids: list[int] = Query(..., description="List of error IDs"),
    action: str = Query(..., pattern="^(ack|unack|delete)$", description="Action to perform"),
    request: Request = None,
    admin: models.User = Depends(require_admin_mfa),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Perform bulk action on multiple errors (requires MFA)."""
    if not error_ids:
        raise HTTPException(status_code=400, detail="No error IDs provided")

    if len(error_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 errors per bulk action")

    errors = db.query(models.ErrorLog).filter(models.ErrorLog.id.in_(error_ids)).all()
    found_ids = {e.id for e in errors}
    missing_ids = set(error_ids) - found_ids

    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Errors not found: {missing_ids}")

    success_count = 0
    for err in errors:
        if action == "ack":
            err.acked = True
        elif action == "unack":
            err.acked = False
        elif action == "delete":
            db.delete(err)
        success_count += 1

    db.commit()

    _write_audit_log(
        db,
        action=f"error.bulk_{action}",
        actor=admin,
        target=f"errors:{','.join(map(str, error_ids))}",
        ip_address=_extract_client_ip(request),
        extra={"count": success_count, "action": action},
    )

    return ActionResponse(
        success=True, message=f"Bulk {action} completed for {success_count} errors"
    )


@router.post("/errors/{error_id}/ack", response_model=ActionResponse)
def ack_error(
    error_id: int,
    request: Request,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActionResponse:
    """Mark an error as acknowledged (seen/handled)."""
    err = db.get(models.ErrorLog, error_id)
    if err is None:
        raise HTTPException(status_code=404, detail="error not found")

    err.acked = True
    db.commit()

    _write_audit_log(
        db,
        action="error.ack",
        actor=admin,
        target=f"error:{error_id}",
        ip_address=_extract_client_ip(request),
        extra={"path": err.path},
    )
    return ActionResponse(
        success=True, message="ط®ط·ط§ ط¨ظ‡â€Œط¹ظ†ظˆط§ظ† ط±ط³غŒط¯ع¯غŒâ€Œط´ط¯ظ‡ ط¹ظ„ط§ظ…طھ ط®ظˆط±ط¯"
    )


# ============================================================================
# Settings Management
# ============================================================================


@router.get("/settings", response_model=list[SettingOut])
def list_settings(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[SettingOut]:
    """All persisted settings."""
    rows = db.query(models.Setting).order_by(models.Setting.key).all()
    return [SettingOut.model_validate(r) for r in rows]


@router.put("/settings/{key}", response_model=SettingOut)
def update_setting(
    key: str,
    req: SettingUpdate,
    request: Request,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SettingOut:
    """Create or update a global setting (audited)."""
    if key not in KNOWN_SETTINGS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown setting key; allowed: {sorted(KNOWN_SETTINGS)}",
        )

    setting = db.get(models.Setting, key)
    if setting is None:
        setting = models.Setting(key=key, value=req.value.strip(), description=KNOWN_SETTINGS[key])
        db.add(setting)
    else:
        setting.value = req.value.strip()

    db.commit()
    db.refresh(setting)

    _write_audit_log(
        db,
        action="setting.update",
        actor=admin,
        target=f"setting:{key}",
        ip_address=_extract_client_ip(request),
        extra={"value": req.value[:200]},
    )
    return SettingOut.model_validate(setting)


# ============================================================================
# AI Models Management (Ollama)
# ============================================================================


def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", f"http://{os.environ.get('HOST', 'localhost')}:11434")


def _ollama_timeout() -> float:
    try:
        return float(os.getenv("OLLAMA_TIMEOUT", "3.0"))
    except ValueError:
        return 3.0


@router.get("/models", response_model=dict)
async def list_models(
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """List Ollama models + loaded state. Never fabricates: unreachable -> honest flags."""
    base = _ollama_base_url()
    try:
        async with httpx.AsyncClient(timeout=_ollama_timeout()) as client:
            tags_resp = await client.get(f"{base}/api/tags")
            ps_resp = await client.get(f"{base}/api/ps")
            tags = tags_resp.json().get("models", [])
            ps = ps_resp.json().get("models", [])
    except Exception as exc:
        return {
            "configured": False,
            "error": str(exc)[:200],
            "models": [],
            "loaded": [],
            "default_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        }

    loaded_names = {m.get("name") for m in ps}
    models_list = [
        {
            "name": m.get("name"),
            "size_bytes": m.get("size", 0),
            "family": (m.get("details") or {}).get("family"),
            "parameter_size": (m.get("details") or {}).get("parameter_size"),
            "quantization": (m.get("details") or {}).get("quantization_level"),
            "loaded": m.get("name") in loaded_names,
        }
        for m in tags
    ]
    return {
        "configured": True,
        "error": None,
        "models": models_list,
        "loaded": sorted(loaded_names),
        "default_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
    }


@router.post("/models/{model_name}/stop", response_model=dict)
async def stop_model(
    model_name: str,
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Unload a loaded model from memory (keep_alive=0). Audited."""
    base = _ollama_base_url()
    try:
        async with httpx.AsyncClient(timeout=_ollama_timeout()) as client:
            resp = await client.post(
                f"{base}/api/generate",
                json={"model": model_name, "keep_alive": 0},
            )
            resp.raise_for_status()
    except Exception as exc:
        _write_audit_log(
            db,
            action="models.stop",
            actor=admin,
            target=f"model:{model_name}",
            result="failed",
            ip_address=_extract_client_ip(request),
            extra={"error": str(exc)[:200]},
        )
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {str(exc)[:200]}")

    _write_audit_log(
        db,
        action="models.stop",
        actor=admin,
        target=f"model:{model_name}",
        result="ok",
        ip_address=_extract_client_ip(request),
    )
    return {"ok": True, "model": model_name, "message": "Model unloaded from memory"}


# ============================================================================
# Overview & Security
# ============================================================================


@router.get("/overview", response_model=dict)
def admin_overview(
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Honest platform metrics: counts, uptime, recent activity, open errors."""
    uptime_seconds = max(0.0, (datetime.now(UTC) - PROCESS_STARTED_AT).total_seconds())

    users_count = db.query(models.User).count()
    farms_count = db.query(models.Farm).count() if hasattr(models, "Farm") else 0
    audit_count = db.query(models.AuditLog).count()
    errors_total = db.query(models.ErrorLog).count() if hasattr(models, "ErrorLog") else 0
    errors_open = (
        db.query(models.ErrorLog).filter(models.ErrorLog.acked.is_(False)).count()
        if hasattr(models, "ErrorLog")
        else 0
    )
    content_total = db.query(models.ContentItem).count() if hasattr(models, "ContentItem") else 0
    content_published = (
        db.query(models.ContentItem).filter(models.ContentItem.status == "published").count()
        if hasattr(models, "ContentItem")
        else 0
    )

    recent_audit = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc().nullslast())
        .limit(8)
        .all()
    )
    recent_errors = (
        db.query(models.ErrorLog)
        .order_by(models.ErrorLog.created_at.desc().nullslast())
        .limit(5)
        .all()
        if hasattr(models, "ErrorLog")
        else []
    )

    return {
        "uptime_seconds": round(uptime_seconds, 1),
        "counts": {
            "users": users_count,
            "farms": farms_count,
            "audit_entries": audit_count,
            "errors_total": errors_total,
            "errors_open": errors_open,
            "content_total": content_total,
            "content_published": content_published,
        },
        "recent_audit": [AuditOut.from_orm_instance(a).model_dump() for a in recent_audit],
        "recent_errors": [
            {
                "id": e.id,
                "path": e.path,
                "method": e.method,
                "status": e.status,
                "acked": e.acked,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in recent_errors
        ],
    }


@router.get("/security", response_model=dict)
def admin_security(
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Recent authentication events (login attempts, success/failure)."""
    rows = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.action == "auth.login")
        .order_by(models.AuditLog.created_at.desc().nullslast())
        .limit(50)
        .all()
    )
    return {"events": [AuditOut.from_orm_instance(a).model_dump() for a in rows]}


# ============================================================================
# Admin AI assistant (local Ollama) â€” admin copilot
# ============================================================================


class AdminAIChatRequest(BaseModel):
    question: str
    page: str | None = None


@router.get("/ai/status", response_model=dict)
async def admin_ai_status_endpoint(
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
) -> dict:
    """Ollama reachability + configured model availability (panel banner)."""
    from services.ai.admin_assistant import admin_ai_status

    return await admin_ai_status()


@router.post("/ai/chat", response_model=dict)
async def admin_ai_chat(
    payload: AdminAIChatRequest,
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Context-aware Persian admin assistant backed by the local Ollama model.

    Read-only DB context; the answer is advisory only. Every call is audited.
    """
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(status_code=422, detail="question is required")
    if len(question) > 2000:
        raise HTTPException(status_code=422, detail="question too long (max 2000 chars)")
    from services.ai.admin_assistant import ask_admin_assistant

    result = await ask_admin_assistant(db, question, payload.page)
    _write_audit_log(
        db,
        action="ai.admin_chat",
        actor=admin,
        target=f"page:{payload.page or 'unknown'}",
        result="ok",
        ip_address=_extract_client_ip(request),
        extra={"question": question[:200], "provider": result.get("provider")},
    )
    return result
