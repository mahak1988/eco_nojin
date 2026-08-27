"""Audit router (Phase 7) — carbon audit queue, auditor votes, credit issuance,
and Persian RTL credit certificates. All writes go through SECURITY DEFINER
RPCs (auditor_vote / admin_issue_credits) that check roles server-side;
reads are RLS-filtered by the user's JWT. Honest errors, real rows only."""

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


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


async def _user_from_token(token: str) -> dict[str, Any]:
    cfg = _cfg()
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            f"{cfg['url']}/auth/v1/user",
            headers={"apikey": cfg["anon"], "Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="token_invalid")
        return r.json()


async def _get(table: str, select: str, extra: str = "", token: str | None = None) -> Any:
    cfg = _cfg()
    bearer = token or cfg["anon"]
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(
            f"{cfg['url']}/rest/v1/{table}?select={select}{extra}",
            headers={"apikey": cfg["anon"], "Authorization": f"Bearer {bearer}", "Accept": "application/json"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Supabase {table}: HTTP {r.status_code} {r.text[:150]}")
        return r.json()


async def _rpc(fn: str, body: dict[str, Any], token: str) -> Any:
    cfg = _cfg()
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.post(
            f"{cfg['url']}/rest/v1/rpc/{fn}",
            json=body,
            headers={"apikey": cfg["anon"], "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail=f"{fn}: HTTP {r.status_code} {r.text[:200]}")
        return r.json()


@router.get("/queue")
async def queue(token: str, limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    """Verification queue — RLS decides (auditor/admin see rows via base tables)."""
    try:
        await _user_from_token(token)
        rows = await _get("verification_queue", "*", f"&limit={limit}", token=token)
        return {"status": "ok", "count": len(rows), "queue": rows}
    except HTTPException:
        raise
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/vote")
async def vote(token: str, verification_id: str, vote_value: str, confidence: int = 70, comment: str | None = None) -> dict[str, Any]:
    """Auditor vote (validator_id = auth.uid via auditor_vote RPC)."""
    try:
        await _user_from_token(token)
        res = await _rpc("auditor_vote", {"verification_id": verification_id, "vote": vote_value, "confidence": confidence, "comment": comment}, token)
        return {"status": "ok", "recorded": bool(res)}
    except HTTPException:
        raise
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/credits")
async def issue_credits(token: str, project_id: str, amount: float) -> dict[str, Any]:
    """Admin issues carbon credits (admin_issue_credits RPC -> credit + tx)."""
    try:
        await _user_from_token(token)
        res = await _rpc("admin_issue_credits", {"p_project_id": project_id, "p_amount": amount}, token)
        return {"status": "ok", "credit": res}
    except HTTPException:
        raise
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/credits")
async def credits(token: str) -> dict[str, Any]:
    """Own credits (admin sees all via RLS)."""
    try:
        u = await _user_from_token(token)
        rows = await _get("platform_carbon_credits", "id,project_id,owner_id,amount,issued_at,retired,tx_hash", f"&owner_id=eq.{u['id']}&order=issued_at.desc", token=token)
        return {"status": "ok", "count": len(rows), "credits": rows}
    except HTTPException:
        raise
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/certificate/{project_id}")
async def certificate(project_id: str, token: str) -> Response:
    """Persian RTL credit certificate PDF for a verified project."""
    from services.audit.certificate_pdf import build_certificate_pdf

    try:
        u = await _user_from_token(token)
        projs = await _get("platform_carbon_projects", "*", f"&id=eq.{project_id}&limit=1", token=token)
        if not projs:
            raise HTTPException(status_code=404, detail="project not found")
        proj = projs[0]
        creds = await _get("platform_carbon_credits", "*", f"&project_id=eq.{project_id}&order=issued_at.desc&limit=1", token=token)
        if not creds:
            raise HTTPException(status_code=404, detail="no credits issued for this project")
        credit = creds[0]
        owners = await _get("platform_profiles", "display_name", f"&id=eq.{proj.get('owner_id')}&limit=1", token=token)
        owner = owners[0] if owners else {"display_name": u.get("email")}
        owner["email"] = u.get("email")
        data = {
            "project": proj,
            "credit": credit,
            "owner": owner,
            "meta": {"standard": "IPCC 2019 Refinement", "standard_link": "https://www.ipcc-nggip.iges.or.jp/2019Refinement/"},
        }
        pdf = build_certificate_pdf(data)
        return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="cert-{str(credit["id"])[:8]}.pdf"'})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
