"""LMS router (Phase 6C) — cloud-first on Supabase (lms_courses/lms_lessons/
lms_progress, RLS ownership), falls back to repo JSON when the cloud is
unreachable. Progress endpoints require a valid user JWT (token query param)."""

import json
import os
from typing import Any

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/lms", tags=["lms"])

COURSES_PATH = os.path.join("data", "lms", "courses.json")


def _env(key: str) -> str:
    for line in open(".env", encoding="utf-8-sig"):
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip()
    return ""


def _cfg() -> dict[str, str]:
    url = _env("SUPABASE_URL")
    anon = _env("SUPABASE_ANON_KEY")
    if not url or not anon:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY missing in .env")
    return {"url": url.rstrip("/"), "anon": anon}


def _load_local() -> dict[str, Any]:
    with open(COURSES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


async def _get(table: str, select: str, extra: str = "", auth: str | None = None) -> list[dict[str, Any]]:
    cfg = _cfg()
    bearer = auth or cfg["anon"]
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            f"{cfg['url']}/rest/v1/{table}?select={select}{extra}",
            headers={"apikey": cfg["anon"], "Authorization": f"Bearer {bearer}", "Accept": "application/json"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Supabase {table}: HTTP {r.status_code} {r.text[:150]}")
        return r.json()


async def _write(method: str, table: str, body: dict[str, Any], token: str, extra: str = "") -> dict[str, Any]:
    cfg = _cfg()
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.request(
            method,
            f"{cfg['url']}/rest/v1/{table}{extra}",
            json=body,
            headers={
                "apikey": cfg["anon"],
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )
        return {"http": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:200]}}


async def _user_from_token(token: str) -> dict[str, Any]:
    cfg = _cfg()
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            f"{cfg['url']}/auth/v1/user",
            headers={"apikey": cfg["anon"], "Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            raise RuntimeError("token_invalid")
        return r.json()


def _shape(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": c["id"],
        "slug": c.get("slug"),
        "title": c["title"],
        "level": c.get("level"),
        "duration_min": c.get("duration_min"),
        "description": c.get("description"),
        "lesson_count": c.get("lesson_count", 0),
    }


@router.get("/courses")
async def courses() -> dict[str, Any]:
    """Course catalog — cloud first, local JSON fallback."""
    try:
        rows = await _get("lms_courses", "id,slug,title,level,duration_min,description,lesson_count", "&order=created_at")
        out = [_shape(r) for r in rows]
        return {"status": "ok", "count": len(out), "courses": out, "source": "supabase"}
    except Exception as exc:
        try:
            data = _load_local()
            out = []
            for c in data.get("courses", []):
                out.append(
                    {
                        "id": c["id"],
                        "slug": c.get("slug"),
                        "title": c["title"],
                        "level": c.get("level"),
                        "duration_min": c.get("duration_min"),
                        "description": c.get("description"),
                        "lesson_count": len(c.get("lessons", [])),
                    }
                )
            return {"status": "ok", "count": len(out), "courses": out, "source": "local"}
        except Exception as exc2:
            return {"status": "error", "error": f"supabase: {exc}; local: {exc2}"}


@router.get("/courses/{course_id}")
async def course(course_id: str) -> dict[str, Any]:
    """Full course content (lessons with body text) — cloud first."""
    try:
        rows = await _get("lms_courses", "id,slug,title,level,duration_min,description", f"&id=eq.{course_id}&limit=1")
        if not rows:
            return {"status": "error", "error": "course not found"}
        c = rows[0]
        lessons = await _get(
            "lms_lessons", "id,title,minutes,content,position", f"&course_id=eq.{course_id}&order=position"
        )
        return {"status": "ok", "course": {**_shape(c), "lessons": lessons}, "source": "supabase"}
    except Exception as exc:
        try:
            data = _load_local()
            for c in data.get("courses", []):
                if c["id"] == course_id:
                    return {"status": "ok", "course": c, "source": "local"}
            return {"status": "error", "error": "course not found"}
        except Exception as exc2:
            return {"status": "error", "error": f"supabase: {exc}; local: {exc2}"}


@router.get("/progress")
async def progress(token: str) -> dict[str, Any]:
    """Own lesson progress (completed lesson ids) — RLS: auth.uid() = user_id."""
    try:
        u = await _user_from_token(token)
        rows = await _get("lms_progress", "lesson_id", f"&user_id=eq.{u['id']}", auth=token)
        return {"status": "ok", "user_id": u["id"], "completed": [r["lesson_id"] for r in rows]}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/progress")
async def mark_progress(token: str, lesson_id: str) -> dict[str, Any]:
    """Mark a lesson complete (owner-only insert, RLS WITH CHECK)."""
    try:
        u = await _user_from_token(token)
        res = await _write("POST", "lms_progress", {"user_id": u["id"], "lesson_id": lesson_id}, token)
        if res["http"] in (200, 201):
            return {"status": "ok", "lesson_id": lesson_id}
        return {"status": "error", "error": f"HTTP {res['http']} {res['body']}"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.delete("/progress")
async def unmark_progress(token: str, lesson_id: str) -> dict[str, Any]:
    """Unmark a lesson (owner-only delete)."""
    try:
        u = await _user_from_token(token)
        res = await _write("DELETE", "lms_progress", {}, token, f"?user_id=eq.{u['id']}&lesson_id=eq.{lesson_id}")
        if res["http"] in (200, 204):
            return {"status": "ok", "lesson_id": lesson_id, "removed": True}
        return {"status": "error", "error": f"HTTP {res['http']} {res['body']}"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
