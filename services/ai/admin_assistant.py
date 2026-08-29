"""Admin AI assistant v2 — context-aware helper for the admin panel (local-first).

What changed vs v1 (based on real admin-chat feedback):
    - context is Persian-labeled and much richer: security/login events,
      AI model list (from Ollama), manual dataset inventory, motor readiness
    - the system prompt defines the assistant's identity and duties honestly
      and forces it to use the provided numbers instead of claiming
      "data not available"
    - every call is audited by the calling router

Honest degradation: if the model is unreachable, the structured context itself
is returned as the answer with provider = local-context-only.
"""
from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _ollama_base() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def _ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "qwen3:4b")


def _llm_timeout() -> float:
    try:
        return float(os.getenv("AI_LLM_TIMEOUT", "120"))
    except ValueError:
        return 120.0


def _db_context(db: Session) -> dict[str, Any]:
    """Read-only snapshot from the app database. Persian labels, soft-fail."""
    from database import models

    day_ago = datetime.now(UTC) - timedelta(hours=24)
    ctx: dict[str, Any] = {}

    try:
        total = db.query(models.User).count()
        active = db.query(models.User).filter(models.User.is_active == True).count()  # noqa: E712
        ctx["کاربران"] = {"کل": total, "فعال": active, "مسدود": total - active}
    except Exception as exc:
        ctx["کاربران"] = {"خطا": str(exc)[:120]}

    try:
        logins_24h = (
            db.query(models.AuditLog)
            .filter(models.AuditLog.action == "auth.login")
            .filter(models.AuditLog.created_at >= day_ago)
            .count()
        )
        failed_24h = -1
        try:
            failed_24h = (
                db.query(models.AuditLog)
                .filter(models.AuditLog.action == "auth.login")
                .filter(models.AuditLog.result == "failed")
                .filter(models.AuditLog.created_at >= day_ago)
                .count()
            )
        except Exception:
            failed_24h = -1  # result column not queryable — skip silently
        audit_24h = (
            db.query(models.AuditLog)
            .filter(models.AuditLog.created_at >= day_ago)
            .count()
        )
        ctx["امنیت_۲۴ساعت_گذشته"] = {
            "رویدادهای_ورود": logins_24h,
            "ورود_ناموفق": failed_24h if failed_24h >= 0 else "نامشخص",
            "کل_رویدادهای_حسابرسی": audit_24h,
        }
    except Exception as exc:
        ctx["امنیت_۲۴ساعت_گذشته"] = {"خطا": str(exc)[:120]}

    try:
        errors_24h = (
            db.query(models.ErrorLog)
            .filter(models.ErrorLog.created_at >= day_ago)
            .count()
        )
        last_err = (
            db.query(models.ErrorLog)
            .order_by(models.ErrorLog.created_at.desc().nullslast())
            .first()
        )
        ctx["خطاها_۲۴ساعت_گذشته"] = {
            "تعداد": errors_24h,
            "آخرین_خطا": (last_err.message or "")[:160] if last_err else "هیچ",
        }
    except Exception as exc:
        ctx["خطاها_۲۴ساعت_گذشته"] = {"خطا": str(exc)[:120]}

    try:
        ctx["مزارع_و_تحلیل‌ها"] = {
            "مزارع": db.query(models.Farm).count(),
            "تحلیل‌های_ماهواره‌ای": db.query(models.SatelliteAnalysis).count(),
        }
    except Exception as exc:
        ctx["مزارع_و_تحلیل‌ها"] = {"خطا": str(exc)[:120]}

    return ctx


def _manual_dataset_context() -> dict[str, Any]:
    try:
        from services.data_manual import manual

        st = manual.status()
        if not st.get("exists"):
            return {"موجود": False}
        return {
            "موجود": True,
            "حجم_مگابایت": st.get("size_mb"),
            "جدول‌ها": st.get("tables", {}),
        }
    except Exception as exc:
        return {"خطا": str(exc)[:120]}


async def _ollama_context() -> dict[str, Any]:
    base = _ollama_base()
    model = _ollama_model()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tags = (await client.get(f"{base}/api/tags")).json().get("models", [])
        names = [m.get("name") for m in tags]
        ps = (await client.get(f"{base}/api/ps")).json().get("models", [])
        return {
            "در_دسترس": True,
            "مدل_پیش‌فرض": model,
            "فهرست_مدل‌ها": names,
            "مدل‌های_لودشده": [m.get("name") for m in ps],
        }
    except Exception as exc:
        return {"در_دسترس": False, "خطا": str(exc)[:120]}


MOTORS_INFO = {
    "aquacrop": "آماده — عملکرد محصول با هواشناسی واقعی",
    "irrigation": "آماده — برنامه‌ریز آبیاری با ET0 و خاک واقعی",
    "planting": "آماده — تقویم کاشت بر اساس اقلیم سایت",
    "crop_advisor": "آماده — مشاور انتخاب محصول",
    "rusle": "نیازمند لایه DEM (ماهواره‌ای) — بقیه‌ی داده‌ها آماده",
    "صفحه_اجرا": "/admin/motor-runner",
}


async def collect_admin_context(db: Session) -> dict[str, Any]:
    context: dict[str, Any] = {}
    context.update(_db_context(db))
    context["هوش_مصنوعی_محلی"] = await _ollama_context()
    context["دیتابیس_دستی_اکسل"] = _manual_dataset_context()
    context["موتورهای_علمی"] = MOTORS_INFO
    return context


def _strip_think(text: str) -> str:
    return _THINK_RE.sub("", text or "").strip()


SYSTEM_PROMPT = (
    "تو «دستیار هوشمند ادمین» پلتفرم اکو نُژین هستی — یک ابزار نرم‌افزاری داخل پنل ادمین، "
    "نه انسانی و نه مدل آموزش‌دیده‌ی اختصاصی؛ قدرت تو دسترسی زنده به داده‌های پلتفرم است.\n"
    "وظایف تو: پایش وضعیت پلتفرم، گزارش‌دهی (کاربران، خطاها، امنیت، مزارع)، "
    "راهنمای اجرای موتورهای علمی، و پاسخ به سوالات ادمین فقط بر اساس «زمینه» زنده‌ای که دریافت می‌کنی.\n"
    "قوانین پاسخ:\n"
    "1) هر عددی که در زمینه هست را مستقیم استفاده کن و بگو از کدام بخش داده آمده.\n"
    "2) اگر سوال امنیتی بود، از بخش «امنیت_۲۴ساعت_گذشته» و ورودهای ناموفق جواب بده.\n"
    "3) اگر سوال درباره مدل‌ها یا دیتاها بود، از بخش‌های «هوش_مصنوعی_محلی» و «دیتابیس_دستی_اکسل» لیست بده.\n"
    "4) اگر سوال درباره اجرای موتورها بود، راهنمایی کن از صفحه /admin/motor-runner استفاده کند.\n"
    "5) فقط وقتی بگو «داده در دسترس نیست» که واقعاً هیچ بخش مرتبطی در زمینه وجود نداشته باشد "
    "و دقیقاً بگو چه داده‌ای کم است.\n"
    "6) کوتاه، فارسی، عملی. هرگز عدد از خودت نساز و آموزش‌دیدگی غیرواقعی ادعا نکن."
)


async def _chat_ollama(system: str, user: str) -> str:
    payload = {
        "model": _ollama_model(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=_llm_timeout()) as client:
        resp = await client.post(f"{_ollama_base()}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
    return _strip_think((data.get("message") or {}).get("content", ""))


async def ask_admin_assistant(
    db: Session, question: str, page: str | None = None
) -> dict[str, Any]:
    """Answer the admin's question using the live context snapshot + local LLM."""
    context = await collect_admin_context(db)
    context_json = json.dumps(context, ensure_ascii=False, default=str, indent=1)
    user_msg = (
        f"زمینه‌ی زنده‌ی پلتفرم (JSON):\n{context_json}\n\n"
        f"صفحه‌ی فعلی ادمین: {page or 'نامشخص'}\n\n"
        f"سوال ادمین: {question}"
    )
    provider = f"ollama:{_ollama_model()}"
    try:
        answer = await _chat_ollama(SYSTEM_PROMPT, user_msg)
        if not answer.strip():
            raise RuntimeError("empty answer from model")
    except Exception as exc:
        answer = (
            "اتصال به مدل محلی برقرار نشد؛ خلاصه‌ی وضعیت پلتفرم مستقیم از پایگاه‌داده:\n"
            + "\n".join(f"- {k}: {v}" for k, v in context.items())
            + f"\n\n(خطا: {str(exc)[:160]})"
        )
        provider = "local-context-only"
    return {
        "answer": answer,
        "provider": provider,
        "model": _ollama_model(),
        "context": context,
        "page": page,
        "generated_at": datetime.now(UTC).isoformat(),
    }


async def admin_ai_status() -> dict[str, Any]:
    """Reachability + model availability for the panel banner. Never fabricates."""
    base = _ollama_base()
    model = _ollama_model()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tags = (await client.get(f"{base}/api/tags")).json().get("models", [])
        names = [m.get("name") for m in tags]
        return {
            "reachable": True,
            "base_url": base,
            "model": model,
            "model_available": model in names,
            "models_count": len(names),
        }
    except Exception as exc:
        return {
            "reachable": False,
            "base_url": base,
            "model": model,
            "model_available": False,
            "error": str(exc)[:160],
        }
