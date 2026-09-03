"""Support team personas — user-facing platform support (3 languages, named staff).

The personas present themselves as HyDroMa support staff (named, with roles).
On a DIRECT question about being AI/human, they answer honestly (legal safety).
Never expose internal architecture or other users' data.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

import os

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

PERSONAS: dict[str, dict[str, str]] = {
    "fa": {
        "name": "پریا صادقی",
        "role": "کارشناس ارشد پشتیبانی هیدروما",
        "model": "qwen3:4b",
        "intro": "سلام! پریا از تیم پشتیبانی هیدروما هستم 🌱",
        "signature": "— پریا، تیم پشتیبانی هیدروما",
        "honest": "من دستیار خودکار پشتیبانی هیدروما هستم — سریع‌ترین راه برای جواب دقیق! چطور می‌توانم کمکتان کنم؟",
        "prompt_file": "persona-fa.md",
    },
    "en": {
        "name": "Daniel Reyes",
        "role": "Senior Support Specialist, HyDroMa",
        "model": "gemma3:4b",
        "intro": "Hi! Daniel here from the HyDroMa support team 🌱",
        "signature": "— Daniel, HyDroMa Support Team",
        "honest": "I'm HyDroMa's automated support assistant — the fastest way to accurate answers! How can I help?",
        "prompt_file": "persona-en.md",
    },
    "ar": {
        "name": "ليلى المصري",
        "role": "خبيرة الدعم الفني في هيدروما",
        "model": "qwen3:4b",
        "intro": "مرحباً! ليلى من فريق دعم هيدروما 🌱",
        "signature": "— ليلى، فريق دعم هيدروما",
        "honest": "أنا مساعد الدعم الآلي في هيدروما — أسرع طريق لإجابات دقيقة! كيف أساعدك؟",
        "prompt_file": "persona-ar.md",
    },
}


def personas_list() -> list[dict[str, str]]:
    return [
        {"lang": k, "name": v["name"], "role": v["role"], "intro": v["intro"], "model": v["model"]}
        for k, v in PERSONAS.items()
    ]


def persona_for(lang: str) -> tuple[str, dict[str, str]]:
    lang = (lang or "fa").lower()
    if lang.startswith("ar"):
        return "ar", PERSONAS["ar"]
    if lang.startswith("fa"):
        return "fa", PERSONAS["fa"]
    return "en", PERSONAS["en"]


AI_IDENTITY_RE = re.compile(
    r"(انسانی|هوش\s*مصنوعی|ربات|چت\s*بات|باتی|human|are\s+you\s+(a\s+)?(human|bot|ai|robot)|robot|إنسان|ذكاء\s*اصطناعي|روبوت)",
    re.IGNORECASE,
)


def _is_identity_question(question: str) -> bool:
    return len(question.strip()) < 120 and bool(AI_IDENTITY_RE.search(question))


def _ollama_base() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://os.environ.get('HOST', '127.0.0.1'):11434").rstrip("/")


def _llm_timeout() -> float:
    try:
        return float(os.getenv("AI_LLM_TIMEOUT", "120"))
    except ValueError:
        return 120.0


def _strip_think(text: str) -> str:
    return _THINK_RE.sub("", text or "").strip()


def _prompts_dir() -> Path:
    return Path(__file__).parent / "prompts" / "support"


def _load_support_prompts(key: str) -> str:
    d = _prompts_dir()
    parts = []
    persona = d / f"persona-{key}.md"
    if persona.exists():
        parts.append(persona.read_text(encoding="utf-8-sig").strip())
    for name in ("faq-base.md", "escalation.md"):
        f = d / name
        if f.exists():
            parts.append(f"### {name}\n{f.read_text(encoding='utf-8-sig').strip()}")
    return "\n\n".join(parts) if parts else "You are HyDroMa support staff. Answer helpfully."


def _user_context(db: Session, user: Any) -> dict[str, Any]:
    from database import models  # noqa: F401
    from database.hub import hub

    ctx: dict[str, Any] = {"نام": getattr(user, "full_name", None) or getattr(user, "username", None) or getattr(user, "email", "")}
    try:
        ctx["مزارع"] = db.query(models.Farm).filter(models.Farm.user_id == user.id).count()
    except Exception:
        ctx["مزارع"] = "—"
    try:
        w = db.query(models.EcoWallet).filter(models.EcoWallet.user_id == user.id).first()
        ctx["موجودی_اکو_کوین"] = float(w.balance) if w and w.balance is not None else 0
    except Exception:
        ctx["موجودی_اکو_کوین"] = "—"
    return ctx


def _identity_answer(key: str) -> dict[str, Any]:
    persona = PERSONAS[key]
    return {
        "answer": persona["honest"] + "\n\n" + persona["signature"],
        "persona": persona["name"],
        "provider": "persona-rule",
        "model": persona["model"],
    }


async def _chat_ollama(model: str, system: str, user: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.4},
    }
    async with httpx.AsyncClient(timeout=_llm_timeout()) as client:
        resp = await client.post(f"{_ollama_base()}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
    return _strip_think((data.get("message") or {}).get("content", ""))


async def ask_support(
    db: Session,
    user: Any,
    lang: str,
    question: str,
    page: str | None = None,
) -> dict[str, Any]:
    """Answer a user's support question as a named platform staff persona."""
    key, persona = persona_for(lang)
    q = question.strip()

    # honest identity answer on direct AI/human questions (legal safety)
    if _is_identity_question(q):
        out = _identity_answer(key)
        out["context"] = {"user": getattr(user, "email", "") or getattr(user, "username", "")}
        return out

    user_ctx = _user_context(db, user)
    system = _load_support_prompts(key)
    ctx_json = json.dumps(user_ctx, ensure_ascii=False, default=str)
    user_msg = (
        f"اطلاعات کاربر (JSON):\n{ctx_json}\n\n"
        f"صفحه: {page or 'نامشخص'}\n\n"
        f"سوال کاربر: {q}"
    )
    model = persona["model"]
    provider = f"ollama:{model}"
    try:
        answer = await _chat_ollama(persona["model"], system, user_msg)
        if not answer.strip():
            raise RuntimeError("empty answer")
    except Exception as exc:
        answer = (
            "در حال حاضر امکان پاسخ‌دهی کامل نیست؛ لطفاً بعداً تلاش کنید یا از بخش راهنما استفاده کنید.\n"
            f"(کد خطا: {str(exc)[:120]})"
        )
        provider = "unavailable"
    return {
        "answer": answer + "\n\n" + persona["signature"],
        "persona": persona["name"],
        "provider": provider,
        "model": model,
        "context": user_ctx,
        "page": page,
    }
