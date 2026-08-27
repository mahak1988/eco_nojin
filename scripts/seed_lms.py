"""Seed LMS courses/lessons from data/lms/courses.json into Supabase (idempotent)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _auth() -> tuple[str, str]:
    import os

    token = os.getenv("SUPABASE_ACCESS_TOKEN", "").strip()
    url = os.getenv("SUPABASE_URL", "").strip()
    m = re.search(r"https://([a-z0-9]+)\.supabase\.co", url)
    if not token or not m:
        sys.exit("ERROR: SUPABASE_ACCESS_TOKEN / SUPABASE_URL required in .env")
    return m.group(1), token


def _q(s: str) -> str:
    return s.replace("'", "''")


def main() -> None:
    data_path = ROOT / "data" / "lms" / "courses.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    courses = raw.get("courses") if isinstance(raw, dict) else raw
    if not isinstance(courses, list):
        sys.exit("ERROR: courses.json must contain a list (or {\"courses\": [...]})")

    parts = ["do $$", "declare cid uuid;", "begin"]
    for c in courses:
        slug = c.get("slug") or c["title"].strip().lower().replace(" ", "-")
        lessons = c.get("lessons") or []
        parts.append(
            f"  insert into public.lms_courses (slug, title, level, duration_min, description, lesson_count) "
            f"values ('{_q(slug)}', '{_q(c['title'])}', '{_q(c.get('level', ''))}', "
            f"{int(c.get('duration_min', 0))}, '{_q(c.get('description', ''))}', {len(lessons)}) "
            f"on conflict (slug) do update set title = excluded.title, level = excluded.level, "
            f"duration_min = excluded.duration_min, description = excluded.description, lesson_count = excluded.lesson_count "
            f"returning id into cid;"
        )
        for i, l in enumerate(lessons, start=1):
            parts.append(
                f"  insert into public.lms_lessons (course_id, position, title, minutes, content) "
                f"values (cid, {i}, '{_q(l.get('title', ''))}', {int(l.get('minutes', 0))}, '{_q(l.get('content', ''))}') "
                f"on conflict do nothing;"
            )
    parts.append("end $$;")
    sql = "\n".join(parts)

    ref, token = _auth()
    r = httpx.post(
        f"https://api.supabase.com/v1/projects/{ref}/database/query",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": sql},
        timeout=120.0,
    )
    print(f"seed: HTTP {r.status_code} {r.text[:300]}")
    if r.status_code >= 400:
        sys.exit(1)


if __name__ == "__main__":
    main()
