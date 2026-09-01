"""Phase 7 live E2E test: admin issues credits + certificate; farmer is rejected.

Creates two temp users (p7_admin@econojin.test, p7_farmer@econojin.test),
bootstraps admin role via SQL, runs the full audit/credit flow against
os.environ.get('HOST', 'localhost'):8011, then cleans up all test rows. Requires: server on 8011,
SUPABASE_ACCESS_TOKEN in .env, PYTHONPATH=D:\\eco_nojin.
"""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

import io
import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BASE = "http://os.environ.get('HOST', '127.0.0.1'):8011"
PASSWORD = "P7TestPass123"  # >= 6 chars
ADMIN_EMAIL = "p7_admin@econojin.test"
FARMER_EMAIL = "p7_farmer@econojin.test"

admin_uid = farmer_uid = ""


def _token() -> tuple[str, str]:
    t = os.getenv("SUPABASE_ACCESS_TOKEN", "").strip()
    u = os.getenv("SUPABASE_URL", "").strip()
    m = re.search(r"https://([a-z0-9]+)\.supabase\.co", u)
    if not t or not m:
        sys.exit("SUPABASE_ACCESS_TOKEN/SUPABASE_URL required in .env")
    return m.group(1), t


def sql(query: str) -> str:
    ref, tok = _token()
    r = httpx.post(
        f"https://api.supabase.com/v1/projects/{ref}/database/query",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        json={"query": query},
        timeout=120.0,
    )
    return f"HTTP {r.status_code}: {r.text[:300]}"


def signup(email: str) -> dict:
    r = httpx.post(f"{BASE}/api/v1/auth/supabase/signup", json={"email": email, "password": PASSWORD}, timeout=30)
    return r.json()


def login(email: str) -> str:
    r = httpx.post(f"{BASE}/api/v1/auth/supabase/login", json={"email": email, "password": PASSWORD}, timeout=30)
    return r.json()["access_token"]


def main() -> int:
    global admin_uid, farmer_uid
    results = []
    try:
        # 1) users
        a = signup(ADMIN_EMAIL)
        f = signup(FARMER_EMAIL)
        admin_uid = a.get("user_id", "")
        farmer_uid = f.get("user_id", "")
        results.append(("signup admin/farmer", f"{bool(admin_uid)}/{bool(farmer_uid)}"))
        at, ft = login(ADMIN_EMAIL), login(FARMER_EMAIL)

        # 2) profiles
        for tok, name in ((at, "P7 Admin"), (ft, "P7 Farmer")):
            httpx.put(f"{BASE}/api/v1/supabase/profile", params={"token": tok, "display_name": name}, timeout=30)
        results.append(("profiles", "ok"))

        # 3) bootstrap admin role
        r = sql(f"update public.platform_profiles set role='admin' where id='{admin_uid}';")
        results.append(("bootstrap admin", r))

        # 4) create project (admin owns)
        rp = httpx.post(
            f"{BASE}/api/v1/supabase/carbon-projects",
            params={"token": at, "name": "پروژه فاز ۷", "project_type": "soil_carbon", "area_ha": 8.5, "duration_years": 15},
            timeout=30,
        ).json()
        pid = rp.get("project", {}).get("id", "")
        results.append(("create project", f"pid={pid[:8]}"))

        # 5) issue credits (admin)
        rc = httpx.post(f"{BASE}/api/v1/audit/credits", params={"token": at, "project_id": pid, "amount": 42.5}, timeout=30).json()
        results.append(("issue credits", json.dumps(rc, ensure_ascii=False)[:160]))

        # 6) credits list (admin)
        rl = httpx.get(f"{BASE}/api/v1/audit/credits", params={"token": at}, timeout=30).json()
        results.append(("credits list", f"count={rl.get('count')}"))

        # 7) certificate PDF (admin)
        rcert = httpx.get(f"{BASE}/api/v1/audit/certificate/{pid}", params={"token": at}, timeout=60)
        pdf_ok = rcert.status_code == 200 and rcert.content[:4] == b"%PDF" and len(rcert.content) > 3000
        results.append(("certificate pdf", f"status={rcert.status_code} bytes={len(rcert.content)} pdf={pdf_ok}"))

        # 8) farmer cannot issue credits
        rf = httpx.post(f"{BASE}/api/v1/audit/credits", params={"token": ft, "project_id": pid, "amount": 1}, timeout=30)
        results.append(("farmer issue blocked", f"status={rf.status_code} body={rf.text[:80]}"))

        # 9) farmer cannot call admin_set_role via proxy
        rr = httpx.post(
            f"{BASE}/api/v1/supabase/admin/role",
            params={"token": ft, "user_id": admin_uid, "role": "admin"},
            timeout=30,
        )
        results.append(("farmer role blocked", f"status={rr.status_code} body={rr.text[:80]}"))

        # 10) farmer vote rejected (auditor_vote not_authorized)
        rv = httpx.post(
            f"{BASE}/api/v1/audit/vote",
            params={"token": ft, "verification_id": "00000000-0000-4000-8000-000000000001", "vote_value": "approved"},
            timeout=30,
        )
        results.append(("farmer vote blocked", f"status={rv.status_code} body={rv.text[:80]}"))

    finally:
        # cleanup
        uids = ",".join(f"'{u}'" for u in (admin_uid, farmer_uid) if u)
        if uids:
            sql(
                "delete from public.platform_carbon_projects where owner_id in (" + uids + ");"
                "delete from public.platform_carbon_credits where owner_id in (" + uids + ");"
                "delete from public.token_transactions where user_id in (" + uids + ");"
                "delete from public.platform_profiles where id in (" + uids + ");"
                "delete from public.users where email in ('" + ADMIN_EMAIL + "','" + FARMER_EMAIL + "');"
                "delete from auth.users where email in ('" + ADMIN_EMAIL + "','" + FARMER_EMAIL + "');"
            )
        results.append(("cleanup", "done"))

    logger.info("\n".join(f"{k}: {v}" for k, v in results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
