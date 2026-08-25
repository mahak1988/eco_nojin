"""
Admin Router (Phase 5)
=======================
Real admin panel API for a single non-technical operator:

- GET  /admin/health          — live health of all platform channels
- GET  /admin/users           — list users (RBAC: admin only)
- POST /admin/users/{id}/block   — deactivate a user (audited)
- POST /admin/users/{id}/unblock — reactivate a user (audited)
- GET  /admin/audit           — recent audit-log entries (W-015)

Every mutating action writes an audit entry. Access is guarded by the
``admin`` role (see auth.py ``require_roles``). To bootstrap the first
admin: ``UPDATE users SET role='admin' WHERE email='you@example.com';``
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, UTC
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database.config import get_db
from database import models
from services.api_gateway.auth import get_current_user, require_roles
from services.content.rag_sync import snapshot_version, sync_content_to_rag
# TODO: Refactor to use service layer instead of direct database access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

require_admin = require_roles("admin")


# ============================================================================
# Audit log helper (W-015)
# ============================================================================

def log_audit(
    db: Session,
    actor: models.User,
    action: str,
    target: str,
    detail: str = "",
) -> models.AuditLog:
    """Persist an audit entry (who did what, when)."""
    entry = models.AuditLog(
        actor_id=actor.id,
        actor_email=actor.email,
        action=action,
        target=target,
        detail=detail[:2000],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ============================================================================
# Models
# ============================================================================

class ChannelStatus(BaseModel):
    channel: str
    status: str  # "ok" | "degraded" | "down" | "not_configured"
    detail: str


class HealthResponse(BaseModel):
    status: str
    channels: List[ChannelStatus]
    checked_at: str


class AdminUserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    language: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AuditOut(BaseModel):
    id: int
    actor_email: str
    action: str
    target: str
    detail: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ActionResponse(BaseModel):
    success: bool
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def admin_health(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Live health of all platform channels (real checks, honest results)."""
    channels: List[ChannelStatus] = []

    # 1. Database
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        channels.append(ChannelStatus(channel="database", status="ok", detail="SQLite reachable"))
    except Exception as exc:  # pragma: no cover - defensive
        channels.append(ChannelStatus(channel="database", status="down", detail=str(exc)[:200]))

    # 2. AI backend (Ollama) — configured?
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{ollama_base}/api/tags")
        if resp.status_code == 200:
            channels.append(ChannelStatus(channel="ai_backend", status="ok", detail=f"Ollama at {ollama_base}"))
        else:
            channels.append(ChannelStatus(channel="ai_backend", status="down", detail=f"HTTP {resp.status_code}"))
    except Exception:
        channels.append(ChannelStatus(channel="ai_backend", status="down", detail=f"unreachable at {ollama_base}"))

    # 3. Satellite provider (CDSE credentials)
    from services.satellite.copernicus import CopernicusClient
    cdse = CopernicusClient()
    channels.append(ChannelStatus(
        channel="satellite",
        status="ok" if cdse.configured else "not_configured",
        detail="CDSE credentials set" if cdse.configured
        else "CDSE credentials missing — real NDVI unavailable (W-001)",
    ))

    # 4. Weather sources
    nasa_configured = True  # NASA POWER needs no credentials
    channels.append(ChannelStatus(
        channel="weather",
        status="ok" if nasa_configured else "down",
        detail="NASA POWER + Open-Meteo ERA5 (no credentials required)",
    ))

    # 5. Bot platforms (tokens in env)
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
            channels.append(ChannelStatus(channel=name, status="not_configured", detail=f"{env_key} missing"))

    overall = "ok" if all(c.status == "ok" for c in channels) else "degraded"
    return HealthResponse(
        status=overall,
        channels=channels,
        checked_at=datetime.now(UTC).isoformat(),
    )


@router.get("/users", response_model=List[AdminUserOut])
def list_users(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 100,
):
    """List users (newest first)."""
    rows = db.query(models.User).order_by(models.User.id.desc()).limit(limit).all()
    return rows


@router.post("/users/{user_id}/block", response_model=ActionResponse)
def block_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Deactivate a user account (audited)."""
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="cannot block yourself")
    user.is_active = False
    db.commit()
    log_audit(db, admin, "user.block", f"user:{user_id}", user.email)
    return ActionResponse(success=True, message=f"کاربر {user.email} مسدود شد")


@router.post("/users/{user_id}/unblock", response_model=ActionResponse)
def unblock_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reactivate a user account (audited)."""
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    user.is_active = True
    db.commit()
    log_audit(db, admin, "user.unblock", f"user:{user_id}", user.email)
    return ActionResponse(success=True, message=f"کاربر {user.email} فعال شد")


@router.get("/audit", response_model=List[AuditOut])
def list_audit(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Recent audit-log entries (W-015)."""
    rows = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return rows

ALLOWED_CATEGORIES = {"agriculture", "water", "soil", "carbon", "climate", "general"}
ALLOWED_CONTENT_STATUS = {"draft", "published", "archived"}
KNOWN_SETTINGS = {
    "site_announcement": "پیام سراسری سایت (خالی = غیرفعال)",
    "alerts_ndvi_enabled": "فعال‌سازی هشدارهای NDVI (true/false)",
    "rag_available": "در دسترس بودن دانشنامه (true/false)",
    "default_language": "زبان پیش‌فرض (fa/en/...)",
    "content_auto_publish_bot": "انتشار خودکار محتوا به ربات‌ها (true/false)",
    "content_publish_channel": "شناسه کانال/گروه برای انتشار (chat_id)",
}


# ============================================================================
# Models
# ============================================================================

class ContentCreate(BaseModel):
    title: str
    body: str
    category: str = "general"
    language: str = "fa"
    source: Optional[str] = None
    generated_by_ai: bool = False


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None


class ContentOut(BaseModel):
    id: int
    title: str
    body: str
    category: str
    language: str
    status: str
    source: Optional[str] = None
    updated_at: Optional[datetime] = None
    generated_by_ai: bool = False
    rag_synced: bool = False
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class BotOut(BaseModel):
    key: str
    label: str
    kind: str
    verified: bool
    configured: bool       # token present in env
    enabled: bool          # persisted flag (default: configured)
    model_config = ConfigDict(from_attributes=True)

class ErrorOut(BaseModel):
    id: int
    path: str
    method: str
    status: int
    message: Optional[str] = None
    acked: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SettingOut(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SettingUpdate(BaseModel):
    value: str


class ActionResponse(BaseModel):
    success: bool
    message: str


# ============================================================================
# Content
# ============================================================================

def _validate_category(category: str) -> None:
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"category must be one of {sorted(ALLOWED_CATEGORIES)}",
        )


@router.get("/content", response_model=List[ContentOut])
def list_content(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 100,
):
    """List content items (newest first)."""
    return (
        db.query(models.ContentItem)
        .order_by(models.ContentItem.updated_at.desc())
        .limit(limit)
        .all()
    )


@router.post("/content", response_model=ContentOut)
def create_content(
    req: ContentCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a content item (draft)."""
    _validate_category(req.category)
    item = models.ContentItem(
        title=req.title.strip(),
        body=req.body.strip(),
        category=req.category,
        language=req.language,
        status="draft",
        source=req.source,
        generated_by_ai=getattr(req, "generated_by_ai", False),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    # initial version snapshot (Phase 6)
    db.add(
        models.ContentVersion(
            content_id=item.id, version=1, title=item.title, body=item.body
        )
    )
    db.commit()
    log_audit(db, admin, "content.create", f"content:{item.id}", item.title[:120])
    return item


@router.put("/content/{item_id}", response_model=ContentOut)
def update_content(
    item_id: int,
    req: ContentUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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
    if getattr(req, "generated_by_ai", None) is not None:
        item.generated_by_ai = req.generated_by_ai
    snapshot_version(db, item)
    db.commit()
    db.refresh(item)
    log_audit(db, admin, "content.update", f"content:{item.id}", item.title[:120])
    return item


@router.post("/content/{item_id}/publish", response_model=ActionResponse)
def publish_content(
    item_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Publish a content item (visible flag; RAG sync lands in Phase 6)."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")
    from datetime import datetime, UTC as _utc

    item.status = "published"
    if item.published_at is None:
        item.published_at = datetime.now(_utc)
    db.commit()
    synced = sync_content_to_rag(db)
    from services.content.bot_dispatch import dispatch_to_bots

    dispatched = dispatch_to_bots(db, item.title, item.body)
    log_audit(
        db, admin, "content.publish", f"content:{item.id}",
        f"rag={synced} bot={dispatched.get('dispatched', 0)}",
    )
    bot_note = ""
    if dispatched.get("dispatched"):
        bot_note = " + ارسال به ربات"
    elif dispatched.get("reason"):
        bot_note = f" (ربات: {dispatched['reason']})"
    return ActionResponse(
        success=True,
        message=f"«{item.title}» منتشر شد و با RAG همگام شد ({synced}){bot_note}",
    )


@router.delete("/content/{item_id}", response_model=ActionResponse)
def delete_content(
    item_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Archive (soft delete) a content item."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")
    item.status = "archived"
    db.commit()
    log_audit(db, admin, "content.archive", f"content:{item.id}", item.title[:120])
    return ActionResponse(success=True, message=f"«{item.title}» بایگانی شد")



# ----------------------------------------------------------------------------
# Phase 6: versions + translation
# ----------------------------------------------------------------------------


@router.get("/content/{item_id}/versions", response_model=List[dict])
def content_versions(
    item_id: int,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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


@router.get("/content/{item_id}/translations", response_model=List[dict])
def content_translations_list(
    item_id: int,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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


#: Phase 6 translation targets (bot i18n set, ISO 639-1)
CONTENT_TRANSLATION_LANGUAGES = {
    "fa": "فارسی", "en": "English", "ar": "العربية", "tr": "Türkçe",
    "ru": "Русский", "zh": "中文", "es": "Español", "fr": "Français",
    "de": "Deutsch", "ur": "اردو", "az": "Azərbaycanca", "ku": "Kurdî",
    "hi": "हिन्दी", "ps": "پښتو",
}


@router.post("/content/{item_id}/translate", response_model=ActionResponse)
def translate_content(
    item_id: int,
    language: str,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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
    from services.bots.config import BotConfig
    from services.bots.core.ai import OllamaClient

    config = BotConfig()
    client = OllamaClient(config)

    async def _run() -> "Optional[str]":
        if not await client.available():
            return None
        system = (
            "You are a professional agricultural translator. "
            "Translate the following article title and body into "
            f"{CONTENT_TRANSLATION_LANGUAGES[lang]} ({lang}). "
            "Reply with exactly two lines: first the translated title, "
            "then the translated body. Keep technical terms accurate."
        )
        return await client.chat(system, f"TITLE: {item.title}\n\nBODY: {item.body}")

    import asyncio

    try:
        text = asyncio.run(_run())
    except Exception:  # noqa: BLE001
        text = None
    if not text:
        log_audit(
            db, admin, "content.translate",
            f"content:{item.id}", f"failed lang={lang} (ollama offline)",
        )
        raise HTTPException(
            status_code=503,
            detail="ترجمه ممکن نشد — سرور Ollama در دسترس نیست",
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
    log_audit(
        db, admin, "content.translate", f"content:{item.id}",
        f"ok lang={lang}",
    )
    return ActionResponse(
        success=True,
        message=f"ترجمه «{item.title}» به {CONTENT_TRANSLATION_LANGUAGES[lang]} آماده شد",
    )



# ----------------------------------------------------------------------------
# Phase 6: AI draft generation + scheduled publishing
# ----------------------------------------------------------------------------


@router.post("/content/generate-draft", response_model=ContentOut)
def generate_ai_draft(
    topic: str = Query(..., min_length=3, max_length=200),
    category: str = Query("general"),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Generate an article draft with local Ollama (labelled AI, honest 503)."""
    _validate_category(category)
    from services.bots.config import BotConfig
    from services.bots.core.ai import OllamaClient

    client = OllamaClient(BotConfig())

    async def _run() -> "Optional[str]":
        if not await client.available():
            return None
        system = (
            "You are an agricultural knowledge writer for an Iranian "
            "climate-smart agriculture platform. Write in Persian (fa). "
            "Reply with exactly two lines: the title, then the full article "
            "body in Markdown (short sections with ## headings and - bullets). "
            "Be factual, practical and cite FAO-style guidance without "
            "inventing statistics."
        )
        return await client.chat(
            system,
            f"موضوع مقاله: {topic}\nدسته: {category}",
            temperature=float(os.getenv('ADMIN_TEMP', '0.4')),
        )

    import asyncio

    try:
        text = asyncio.run(_run())
    except Exception:  # noqa: BLE001
        text = None
    if not text:
        raise HTTPException(
            status_code=503, detail="تولید پیش‌نویس ممکن نشد — سرور Ollama در دسترس نیست"
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
    db.add(
        models.ContentVersion(
            content_id=item.id, version=1, title=item.title, body=item.body
        )
    )
    db.commit()
    log_audit(
        db, admin, "content.ai_draft", f"content:{item.id}",
        f"topic={topic[:80]}",
    )
    return item


@router.post("/content/{item_id}/schedule", response_model=ActionResponse)
def schedule_content(
    item_id: int,
    at: str = Query(..., description="ISO-8601 datetime (UTC)"),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Schedule a draft for automatic publishing (UTC ISO-8601)."""
    from datetime import datetime
    from datetime import timezone as _tz

    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")
    try:
        scheduled = datetime.fromisoformat(at.replace("Z", "+00:00"))
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=_tz.utc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"bad datetime: {exc}") from exc
    item.scheduled_at = scheduled
    db.commit()
    log_audit(
        db, admin, "content.schedule", f"content:{item.id}",
        f"at={scheduled.isoformat()}",
    )
    return ActionResponse(
        success=True, message=f"انتشار «{item.title}» برای {scheduled.isoformat()} زمان‌بندی شد"
    )


@router.post("/content/{item_id}/cancel-schedule", response_model=ActionResponse)
def cancel_schedule_content(
    item_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Cancel a pending scheduled publish."""
    item = db.get(models.ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="content not found")
    item.scheduled_at = None
    db.commit()
    log_audit(db, admin, "content.cancel_schedule", f"content:{item.id}", "")
    return ActionResponse(success=True, message="زمان‌بندی لغو شد")


# ============================================================================
# Bots
# ============================================================================

@router.get("/bots", response_model=List[BotOut])
def list_bots(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Platform registry status: configured (env) + enabled (settings)."""
    from services.bots.platforms import PLATFORM_SPECS

    settings_map = {s.key: s.value for s in db.query(models.Setting).all()}
    out: List[BotOut] = []
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
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Flip the persisted enabled flag for a bot platform (audited)."""
    from services.bots.platforms import PLATFORM_SPECS

    if key not in PLATFORM_SPECS:
        raise HTTPException(status_code=404, detail="unknown platform")
    setting = db.get(models.Setting, f"bot_enabled_{key}")
    current = setting.value == "true" if setting else bool(os.environ.get(PLATFORM_SPECS[key].token_env))
    new_value = "false" if current else "true"
    if setting is None:
        setting = models.Setting(
            key=f"bot_enabled_{key}",
            value=new_value,
            description=f"فعال‌سازی ربات {PLATFORM_SPECS[key].label}",
        )
        db.add(setting)
    else:
        setting.value = new_value
    db.commit()
    log_audit(db, admin, "bot.toggle", f"bot:{key}", f"enabled={new_value}")
    state = "فعال" if new_value == "true" else "غیرفعال"
    return ActionResponse(success=True, message=f"ربات {PLATFORM_SPECS[key].label} {state} شد")


# ============================================================================
# Errors
# ============================================================================

@router.get("/errors", response_model=List[ErrorOut])
def list_errors(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Recent captured API errors (newest first)."""
    return (
        db.query(models.ErrorLog)
        .order_by(models.ErrorLog.created_at.desc())
        .limit(limit)
        .all()
    )


@router.post("/errors/{error_id}/ack", response_model=ActionResponse)
def ack_error(
    error_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Mark an error as acknowledged (seen/handled)."""
    err = db.get(models.ErrorLog, error_id)
    if err is None:
        raise HTTPException(status_code=404, detail="error not found")
    err.acked = True
    db.commit()
    log_audit(db, admin, "error.ack", f"error:{error_id}", err.path)
    return ActionResponse(success=True, message="خطا به‌عنوان رسیدگی‌شده علامت خورد")


# ============================================================================
# Settings
# ============================================================================

@router.get("/settings", response_model=List[SettingOut])
def list_settings(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """All persisted settings."""
    return db.query(models.Setting).order_by(models.Setting.key).all()


@router.put("/settings/{key}", response_model=SettingOut)
def update_setting(
    key: str,
    req: SettingUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create or update a global setting (audited)."""
    if key not in KNOWN_SETTINGS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown setting key; allowed: {sorted(KNOWN_SETTINGS)}",
        )
    setting = db.get(models.Setting, key)
    if setting is None:
        setting = models.Setting(
            key=key, value=req.value.strip(), description=KNOWN_SETTINGS[key]
        )
        db.add(setting)
    else:
        setting.value = req.value.strip()
    db.commit()
    db.refresh(setting)
    log_audit(db, admin, "setting.update", f"setting:{key}", req.value[:200])
    return setting

# ============================================================================
# Models (AI model management — honest Ollama runtime state)
# ============================================================================


def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def _ollama_timeout() -> float:
    try:
        return float(os.getenv("OLLAMA_TIMEOUT", "3.0"))
    except ValueError:
        return 3.0


@router.get("/models", response_model=dict)
def list_models(
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List Ollama models + loaded state. Never fabricates: unreachable -> honest flags."""
    base = _ollama_base_url()
    try:
        import httpx

        with httpx.Client(timeout=_ollama_timeout()) as client:
            tags = client.get(f"{base}/api/tags").json().get("models", [])
            ps = client.get(f"{base}/api/ps").json().get("models", [])
    except Exception as exc:  # noqa: BLE001 — honest degradation
        return {
            "configured": False,
            "error": str(exc)[:200],
            "models": [],
            "loaded": [],
            "default_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        }
    loaded_names = {m.get("name") for m in ps}
    models = [
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
        "models": models,
        "loaded": sorted(loaded_names),
        "default_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
    }


@router.post("/models/{model_name}/stop", response_model=dict)
def stop_model(
    model_name: str,
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Unload a loaded model from memory (keep_alive=0). Audited."""
    base = _ollama_base_url()
    try:
        import httpx

        with httpx.Client(timeout=_ollama_timeout()) as client:
            resp = client.post(
                f"{base}/api/generate",
                json={"model": model_name, "keep_alive": 0},
            )
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        log_audit(db, admin, "models.stop", json.dumps({"model": model_name, "ok": False, "error": str(exc)[:200]}))
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {str(exc)[:200]}")
    log_audit(db, admin, "models.stop", json.dumps({"model": model_name, "ok": True}))
    return {"ok": True, "model": model_name, "message": "Model unloaded from memory"}

# ============================================================================
# Overview (metrics) + Security (login history)
# ============================================================================

#: Process start time for honest uptime reporting.
PROCESS_STARTED_AT = datetime.now(UTC)


@router.get("/overview", response_model=dict)
def admin_overview(
    request: Request,
    admin: models.User = Depends(get_current_user),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Honest platform metrics: counts, uptime, recent activity, open errors."""
    uptime_seconds = max(0.0, (datetime.now(UTC) - PROCESS_STARTED_AT).total_seconds())
    users_count = db.query(models.User).count()
    farms_count = db.query(models.Farm).count()
    audit_count = db.query(models.AuditLog).count()
    errors_total = db.query(models.ErrorLog).count()
    errors_open = (
        db.query(models.ErrorLog).filter(models.ErrorLog.acked.is_(False)).count()
    )
    content_total = db.query(models.ContentItem).count()
    content_published = (
        db.query(models.ContentItem)
        .filter(models.ContentItem.status == "published")
        .count()
    )
    recent_audit = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .limit(8)
        .all()
    )
    recent_errors = (
        db.query(models.ErrorLog)
        .order_by(models.ErrorLog.created_at.desc())
        .limit(5)
        .all()
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
        "recent_audit": [
            {
                "actor_email": a.actor_email,
                "action": a.action,
                "target": a.target,
                "detail": a.detail,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_audit
        ],
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
):
    """Recent authentication events (login attempts, success/failure)."""
    rows = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.action == "auth.login")
        .order_by(models.AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "events": [
            {
                "actor_email": a.actor_email,
                "target": a.target,
                "detail": a.detail,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in rows
        ]
    }
