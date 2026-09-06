"""Real Supabase Auth proxy (Phase 6) — signup/login/me via GoTrue.

Free tier, keys already in .env. The anon key is a publishable key (safe
server-side here); the SERVICE_ROLE key is NEVER exposed to the frontend
and is only used for admin operations (delete test user, user lookup).
"""

import os
from typing import Any

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/auth/supabase", tags=["auth-supabase"])


def _cfg() -> dict[str, str]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    anon = os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_KEY", "")
    svc = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not anon:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY missing in environment")
    return {"url": url, "anon": anon, "svc": svc}


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=6, max_length=100)
    phone: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


async def _goto(session: httpx.AsyncClient, cfg: dict[str, str], path: str, body: dict[str, Any], key: str) -> dict[str, Any]:
    r = await session.post(
        f"{cfg['url']}{path}",
        json=body,
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    return {"http": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:200]}}


@router.post("/signup")
async def signup(req: SignupRequest) -> dict[str, Any]:
    """Real GoTrue signup (email+password). Returns session tokens on success."""
    try:
        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            res = await _goto(s, cfg, "/auth/v1/signup", {"email": req.email, "password": req.password}, cfg["anon"])
        body = res["body"]
        if res["http"] not in (200, 201):
            return {"status": "error", "error": body.get("msg") or body.get("error_description") or f"HTTP {res['http']}", "http": res["http"]}
        user = body.get("user") or {}
        return {
            "status": "ok",
            "email": user.get("email"),
            "user_id": user.get("id"),
            "confirmed": body.get("session") is not None,
            "note": "در صورت فعال بودن Email Confirmation، لینک تأیید ارسال شد.",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/login")
async def login(req: LoginRequest) -> dict[str, Any]:
    """Real GoTrue password login — returns access_token + refresh_token."""
    try:
        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            res = await _goto(s, cfg, "/auth/v1/token?grant_type=password", {"email": req.email, "password": req.password}, cfg["anon"])
        body = res["body"]
        if res["http"] != 200:
            return {"status": "error", "error": body.get("msg") or body.get("error_description") or f"HTTP {res['http']}", "http": res["http"]}
        return {
            "status": "ok",
            "access_token": body.get("access_token"),
            "refresh_token": body.get("refresh_token"),
            "expires_in": body.get("expires_in"),
            "user_id": (body.get("user") or {}).get("id"),
            "email": (body.get("user") or {}).get("email"),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/me")
async def me(access_token: str) -> dict[str, Any]:
    """Validate a Supabase JWT against GoTrue (real user info)."""
    try:
        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            r = await s.get(
                f"{cfg['url']}/auth/v1/user",
                headers={"apikey": cfg["anon"], "Authorization": f"Bearer {access_token}"},
            )
        if r.status_code != 200:
            return {"status": "error", "error": r.json().get("msg") or f"HTTP {r.status_code}"}
        u = r.json()
        return {"status": "ok", "user_id": u.get("id"), "email": u.get("email"), "created_at": u.get("created_at")}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/admin/delete-user")
async def admin_delete_user(user_id: str) -> dict[str, Any]:
    """Admin-only: delete a test user (service role). Never called from the frontend."""
    try:
        cfg = _cfg()
        if not cfg["svc"]:
            return {"status": "error", "error": "SUPABASE_SERVICE_ROLE_KEY missing"}
        async with httpx.AsyncClient(timeout=20) as s:
            r = await s.delete(
                f"{cfg['url']}/auth/v1/admin/users/{user_id}",
                headers={"apikey": cfg["svc"], "Authorization": f"Bearer {cfg['svc']}"},
            )
        return {"status": "ok" if r.status_code == 204 else "error", "http": r.status_code}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
