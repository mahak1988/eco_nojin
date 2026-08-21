"""
Bot dispatch for published content (Phase 6).

Honesty contract: without a bot token the dispatcher reports
``dispatched=0`` with an explicit reason — it never pretends a message
was sent. Telegram is the only wired channel today (Eitaa/Bale/Rubika
arrive with their tokens via the same settings keys).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from database import models

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _setting(db: Session, key: str, default: str = "") -> str:
    row = db.query(models.Setting).filter(models.Setting.key == key).first()
    return row.value if row else default


def dispatch_to_bots(
    db: Session, title: str, body: str, channel: Optional[str] = None
) -> Dict[str, Any]:
    """Best-effort dispatch of a published article to messenger channels.

    Returns a dict with ``dispatched`` and ``reason``; never raises.
    """
    import os

    enabled = _setting(db, "content_auto_publish_bot", "false").lower() == "true"
    if not enabled:
        return {"dispatched": 0, "reason": "publishing to bots is disabled (setting content_auto_publish_bot)"}
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        return {"dispatched": 0, "reason": "no BOT_TOKEN configured"}
    target = channel or _setting(db, "content_publish_channel", "")
    if not target:
        return {"dispatched": 0, "reason": "no channel configured (content_publish_channel)"}
    text = f"{title}\n\n{body[:1000]}"
    try:
        resp = httpx.post(
            TELEGRAM_API.format(token=token),
            json={"chat_id": target, "text": text},
            timeout=10.0,
        )
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 — best-effort dispatch
        logger.warning("bot dispatch failed: %s", exc)
        return {"dispatched": 0, "reason": f"telegram API error: {str(exc)[:120]}"}
    return {"dispatched": 1, "reason": "sent to telegram"}


def run_due_publishes(db: Session) -> List[int]:
    """Publish items whose scheduled_at is due (used by the periodic loop)."""
    from datetime import datetime, UTC

    now = datetime.now(UTC)
    due = (
        db.query(models.ContentItem)
        .filter(
            models.ContentItem.status == "draft",
            models.ContentItem.scheduled_at.isnot(None),
            models.ContentItem.scheduled_at <= now,
        )
        .all()
    )
    ids: List[int] = []
    for item in due:
        item.status = "published"
        if item.published_at is None:
            item.published_at = now
        item.rag_synced = True
        ids.append(item.id)
        logger.info("scheduled publish: content:%s «%s»", item.id, item.title[:60])
    db.commit()
    return ids
