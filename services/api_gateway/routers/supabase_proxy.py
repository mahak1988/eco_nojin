"""Read/write Supabase proxy (Phase 6B/C) — real data from the hosted project.

Allowlist-only endpoints. Publishable anon key for reads; authenticated writes
pass the USER's JWT through (so RLS ownership policies apply once migration
0001 is applied). The service role key is only used for admin ops (never in
the frontend). Honest contract: real rows, real errors, no fabrication.
"""

from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1/supabase", tags=["supabase"])


def _env(key: str) -> str:
    for line in open(".env", encoding="utf-8-sig"):
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip()
    return ""


def _cfg() -> Dict[str, str]:
    url = _env("SUPABASE_URL")
    anon = _env("SUPABASE_ANON_KEY")
    svc = _env("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not anon:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY missing in .env")
    return {"url": url.rstrip("/"), "anon": anon, "svc": svc}


async def _select(
    table: str, select: str = "*", extra: str = "", key: Optional[str] = None, auth: Optional[str] = None
) -> List[Dict[str, Any]]:
    cfg = _cfg()
    apikey = key or cfg["anon"]
    bearer = auth or apikey
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            f"{cfg['url']}/rest/v1/{table}?select={select}{extra}",
            headers={"apikey": apikey, "Authorization": f"Bearer {bearer}", "Accept": "application/json"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Supabase {table}: HTTP {r.status_code} {r.text[:150]}")
        return r.json()


async def _write(method: str, table: str, body: Dict[str, Any], key: str, extra: str = "") -> Dict[str, Any]:
    """Write with apikey=anon (project identification) and Bearer=user JWT
    (RLS ownership). Service role is never used here."""
    cfg = _cfg()
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.request(
            method,
            f"{cfg['url']}/rest/v1/{table}{extra}",
            json=body,
            headers={
                "apikey": cfg["anon"],
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )
        return {"http": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:200]}}


async def _user_from_token(token: str) -> Dict[str, Any]:
    """Verify a user JWT against GoTrue (real user id + email)."""
    cfg = _cfg()
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            f"{cfg['url']}/auth/v1/user",
            headers={"apikey": cfg["anon"], "Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            raise RuntimeError("token_invalid")
        return r.json()


# ---------------------------------------------------------------- reads


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
    try:
        rows = await _select("standards", "id,name,organization,description,link,category,is_active", "&is_active=eq.true")
        return {"status": "ok", "count": len(rows), "rows": rows}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/marketplace")
async def marketplace() -> Dict[str, Any]:
    try:
        standards_rows = await _select("standards", "id,name,organization,description,link,category,is_active", "&is_active=eq.true")
        projects = await _select("platform_carbon_projects", "*", "&limit=50")
        return {
            "status": "ok",
            "standards": standards_rows,
            "projects": projects,
            "projects_count": len(projects),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/geo/nearest")
async def geo_nearest(lat: float, lon: float, limit: int = Query(default=5, ge=1, le=20)) -> Dict[str, Any]:
    """Nearest landscapes to a point — REAL PostGIS (RPC nearest_landscapes,
    ST_DWithin/<-> on geography), falls back to Haversine if the RPC is missing."""
    try:
        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            r = await s.post(
                f"{cfg['url']}/rest/v1/rpc/nearest_landscapes",
                json={"lat": lat, "lon": lon, "lim": limit},
                headers={"apikey": cfg["anon"], "Authorization": f"Bearer {cfg['anon']}", "Content-Type": "application/json"},
            )
        if r.status_code == 200:
            hits = r.json()
            return {"status": "ok", "count": len(hits), "nearest": hits, "engine": "postgis"}
        rows = await _select("platform_landscapes", "id,name,province,geo_boundary")
        import math

        def hav(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
            r = 6371.0
            p1, p2 = math.radians(a_lat), math.radians(b_lat)
            dp = math.radians(b_lat - a_lat)
            dl = math.radians(b_lon - a_lon)
            h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            return 2 * r * math.asin(math.sqrt(h))

        hits = []
        for row in rows:
            gb = row.get("geo_boundary") or {}
            if gb.get("type") == "Point" and gb.get("coordinates"):
                c = gb["coordinates"]
                hits.append(
                    {
                        "id": row.get("id"),
                        "name": row.get("name"),
                        "province": row.get("province"),
                        "lat": c[1],
                        "lon": c[0],
                        "distance_km": round(hav(lat, lon, c[1], c[0]), 2),
                    }
                )
        hits.sort(key=lambda h: h["distance_km"])
        return {"status": "ok", "count": len(hits), "nearest": hits[:limit], "engine": "haversine (fallback)"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------- authenticated


@router.get("/profile")
async def profile(token: str) -> Dict[str, Any]:
    """Own profile from platform_profiles (real schema: id = auth.users.id)
    plus wallet/eco balances from the users row (RLS: own row only)."""
    try:
        u = await _user_from_token(token)
        rows = await _select("platform_profiles", "*", f"&id=eq.{u['id']}&limit=1", auth=token)
        wallet = {}
        try:
            urows = await _select("users", "eco_balance,cct_balance,level,rank", f"&id=eq.{u['id']}&limit=1", auth=token)
            if urows:
                wallet = urows[0]
        except Exception:
            wallet = {}
        return {
            "status": "ok",
            "user": {"id": u["id"], "email": u.get("email")},
            "profile": rows[0] if rows else None,
            "wallet": wallet,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.put("/profile")
async def put_profile(token: str, display_name: Optional[str] = None, phone: Optional[str] = None, bio: Optional[str] = None) -> Dict[str, Any]:
    """Upsert own profile (writes carry the USER JWT -> RLS ownership applies)."""
    try:
        u = await _user_from_token(token)
        patch = {"display_name": display_name, "phone": phone, "bio": bio}
        patch = {k: v for k, v in patch.items() if v is not None}
        upd = await _write("PATCH", "platform_profiles", patch, token, f"?id=eq.{u['id']}")
        if upd["http"] == 200 and upd["body"]:
            return {"status": "ok", "profile": upd["body"][0], "mode": "updated"}
        ins = await _write("POST", "platform_profiles", {**patch, "id": u["id"]}, token)
        if ins["http"] in (200, 201):
            return {"status": "ok", "profile": (ins["body"] or [{}])[0], "mode": "created"}
        return {"status": "error", "error": f"upsert failed: {upd['http']} / {ins['http']}"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/carbon-projects")
async def create_carbon_project(
    token: str,
    name: str,
    project_type: str = "soil_carbon",
    area_ha: float = 100.0,
    duration_years: int = 20,
    landscape_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a real carbon project with owner_id = auth.uid() (RLS-ready)."""
    try:
        u = await _user_from_token(token)
        row = {
            "owner_id": u["id"],
            "name": name,
            "project_type": project_type,
            "area_ha": area_ha,
            "duration_years": duration_years,
            "status": "draft",
            **({"landscape_id": landscape_id} if landscape_id else {}),
        }
        res = await _write("POST", "platform_carbon_projects", row, token)
        if res["http"] in (200, 201):
            return {"status": "ok", "project": (res["body"] or [{}])[0]}
        return {"status": "error", "error": f"HTTP {res['http']} {res['body']}"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/carbon-projects")
async def list_carbon_projects(token: str) -> Dict[str, Any]:
    """Own carbon projects (RLS: owner_id = auth.uid())."""
    try:
        u = await _user_from_token(token)
        rows = await _select("platform_carbon_projects", "*", f"&owner_id=eq.{u['id']}&order=created_at.desc", auth=token)
        return {"status": "ok", "count": len(rows), "projects": rows}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------- admin / roles


@router.get("/admin/users")
async def admin_users(token: str) -> Dict[str, Any]:
    """All users — RLS decides: only admins see more than their own row."""
    try:
        await _user_from_token(token)
        rows = await _select("users", "id,email,username,level,eco_balance,cct_balance", "&order=created_at.desc", auth=token)
        return {"status": "ok", "count": len(rows), "users": rows}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/admin/role")
async def admin_role(token: str, user_id: str, role: str) -> Dict[str, Any]:
    """Set a user's role — calls admin_set_role RPC (function checks the caller
    is admin before writing; non-admins get not_admin)."""
    try:
        await _user_from_token(token)
        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            r = await s.post(
                f"{cfg['url']}/rest/v1/rpc/admin_set_role",
                json={"target": user_id, "new_role": role},
                headers={"apikey": cfg["anon"], "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
        if r.status_code == 200:
            return {"status": "ok", "changed": r.json(), "target": user_id, "role": role}
        return {"status": "error", "error": f"HTTP {r.status_code} {r.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
