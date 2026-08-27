"""Read-only Supabase proxy (Phase 6B) — real data from the hosted project.

Allowlist-only: landscapes / standards / marketplace catalog. Uses the
PUBLISHABLE anon key (safe server-side); the service role key is never used here.
Honest contract: returns real rows; missing keys -> clear error.
"""

import os
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/supabase", tags=["supabase"])


def _cfg() -> Dict[str, str]:
    url = ""
    anon = ""
    for line in open(".env", encoding="utf-8-sig"):
        k, _, v = line.partition("=")
        if k.strip() == "SUPABASE_URL":
            url = v.strip()
        elif k.strip() == "SUPABASE_ANON_KEY":
            anon = v.strip()
    if not url or not anon:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY missing in .env")
    return {"url": url.rstrip("/"), "anon": anon}


async def _select(table: str, select: str = "*", extra: str = "") -> List[Dict[str, Any]]:
    cfg = _cfg()
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            f"{cfg['url']}/rest/v1/{table}?select={select}{extra}",
            headers={"apikey": cfg["anon"], "Authorization": f"Bearer {cfg['anon']}", "Accept": "application/json"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Supabase {table}: HTTP {r.status_code} {r.text[:150]}")
        return r.json()


@router.get("/landscapes")
async def landscapes() -> Dict[str, Any]:
    """Real platform_landscapes rows (21) with GeoJSON geo_boundary."""
    try:
        rows = await _select("platform_landscapes", "id,name,slug,country,province,geo_boundary,created_at")
        return {"status": "ok", "count": len(rows), "rows": rows}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/standards")
async def standards() -> Dict[str, Any]:
    """Real standards catalog (IPCC, ISO 17025, NASA EOSDIS, ...)."""
    try:
        rows = await _select("standards", "id,name,organization,description,link,category,is_active", "&is_active=eq.true")
        return {"status": "ok", "count": len(rows), "rows": rows}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/marketplace")
async def marketplace() -> Dict[str, Any]:
    """Marketplace catalog on the same DB: standards + project counters."""
    try:
        standards_rows = await _select("standards", "id,name,organization,description,link,category,is_active", "&is_active=eq.true")
        projects = await _select("projects", "*", "&limit=50")
        stats = await _select("dashboard_stats", "*", "&limit=5")
        return {
            "status": "ok",
            "standards": standards_rows,
            "projects": projects,
            "projects_count": len(projects),
            "stats": stats,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
