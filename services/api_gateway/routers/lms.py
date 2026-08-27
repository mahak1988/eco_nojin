"""LMS router (Phase 6C) — free educational content served from repo JSON.
Progress tracking is client-side (localStorage) for now; DB-backed once
LMS tables are created on Supabase (requires migration with DB access).
"""

import json
import os
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/lms", tags=["lms"])

COURSES_PATH = os.path.join("data", "lms", "courses.json")


def _load_courses() -> Dict[str, Any]:
    with open(COURSES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@router.get("/courses")
async def courses() -> Dict[str, Any]:
    """Course catalog (titles + lesson lists, no full content)."""
    try:
        data = _load_courses()
        out = []
        for c in data.get("courses", []):
            out.append(
                {
                    "id": c["id"],
                    "title": c["title"],
                    "level": c.get("level"),
                    "duration_min": c.get("duration_min"),
                    "description": c.get("description"),
                    "lesson_count": len(c.get("lessons", [])),
                    "lessons": [{"id": l["id"], "title": l["title"], "minutes": l.get("minutes")} for l in c.get("lessons", [])],
                }
            )
        return {"status": "ok", "count": len(out), "courses": out}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/courses/{course_id}")
async def course(course_id: str) -> Dict[str, Any]:
    """Full course content (lessons with body text)."""
    try:
        data = _load_courses()
        for c in data.get("courses", []):
            if c["id"] == course_id:
                return {"status": "ok", "course": c}
        return {"status": "error", "error": "course not found"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
