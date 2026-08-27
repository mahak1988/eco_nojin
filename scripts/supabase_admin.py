"""
supabase_admin.py — run SQL on the hosted Supabase project via the Management API.

No DB password needed: uses a Personal Access Token (PAT) from
Supabase Dashboard → Account → Access Tokens → Generate new token.
Put it in .env as:  SUPABASE_ACCESS_TOKEN=sbp_xxxx

Usage:
    .venv\\Scripts\\python.exe scripts\\supabase_admin.py diagnose
    .venv\\Scripts\\python.exe scripts\\supabase_admin.py migrate
    .venv\\Scripts\\python.exe scripts\\supabase_admin.py verify
    .venv\\Scripts\\python.exe scripts\\supabase_admin.py query "<sql>"

Commands:
    diagnose  — list non-internal triggers on auth.users + RLS status + PostGIS
    migrate   — execute supabase/migrations/0001_phase6_harden.sql (idempotent)
    verify    — PostGIS version, platform_badges count, RLS flags per table
    query     — run an arbitrary SQL string
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_BASE = "https://api.supabase.com/v1"


def _auth() -> tuple[str, str]:
    token = os.getenv("SUPABASE_ACCESS_TOKEN", "").strip()
    url = os.getenv("SUPABASE_URL", "").strip()
    m = re.search(r"https://([a-z0-9]+)\.supabase\.co", url)
    if not token or not m:
        sys.exit(
            "ERROR: SUPABASE_ACCESS_TOKEN (sbp_...) and SUPABASE_URL are required in .env\n"
            "Get a token: Supabase Dashboard -> Account -> Access Tokens -> Generate new token"
        )
    return m.group(1), token


def _run_sql(ref: str, token: str, query: str) -> dict:
    r = httpx.post(
        f"{API_BASE}/projects/{ref}/database/query",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": query},
        timeout=120.0,
    )
    if r.status_code >= 400:
        return {"ok": False, "status": r.status_code, "body": r.text[:2000]}
    try:
        return {"ok": True, "status": r.status_code, "data": r.json()}
    except Exception:
        return {"ok": True, "status": r.status_code, "data": r.text[:2000]}


def _print(label: str, res: dict) -> None:
    print(f"\n=== {label} ===")
    if not res["ok"]:
        print(f"ERROR {res['status']}: {res['body']}")
        return
    data = res["data"]
    if isinstance(data, list):
        for row in data[:50]:
            print(row)
        print(f"(rows: {len(data)})")
    else:
        print(data)


def diagnose(ref: str, token: str) -> None:
    _print(
        "Non-internal triggers on auth.users",
        _run_sql(
            ref, token,
            "select tgname, pg_get_triggerdef(t.oid) as def "
            "from pg_trigger t where tgrelid = 'auth.users'::regclass and not tgisinternal;",
        ),
    )
    _print(
        "RLS status (true = RLS on)",
        _run_sql(
            ref, token,
            "select relname, relrowsecurity from pg_class "
            "where relkind='r' and relnamespace='public'::regnamespace "
            "order by relname;",
        ),
    )
    _print(
        "PostGIS installed?",
        _run_sql(ref, token, "select extname, extversion from pg_extension where extname='postgis';"),
    )


def migrate(ref: str, token: str) -> None:
    sql_path = ROOT / "supabase" / "migrations" / "0001_phase6_harden.sql"
    if not sql_path.exists():
        sys.exit(f"ERROR: migration file not found: {sql_path}")
    sql = sql_path.read_text(encoding="utf-8")
    res = _run_sql(ref, token, sql)
    if res["ok"]:
        print(f"MIGRATION OK ({res['status']}) — {sql_path.name} executed.")
    else:
        print(f"MIGRATION FAILED ({res['status']}): {res['body']}")


def verify(ref: str, token: str) -> None:
    _print("PostGIS", _run_sql(ref, token, "select extversion from pg_extension where extname='postgis';"))
    _print("platform_badges count", _run_sql(ref, token, "select count(*) as n from public.platform_badges;"))
    _print(
        "RLS per main table",
        _run_sql(
            ref, token,
            "select relname, relrowsecurity from pg_class "
            "where relname in ('platform_landscapes','platform_profiles','platform_carbon_projects',"
            "'platform_badges','users','standards','projects') and relkind='r' order by relname;",
        ),
    )
    _print(
        "Trigger functions that touch public tables (signup blocker probe)",
        _run_sql(
            ref, token,
            "select p.proname, p.prosrc from pg_proc p "
            "join pg_trigger t on t.tgfoid = p.oid "
            "where t.tgrelid = 'auth.users'::regclass and not t.tgisinternal;",
        ),
    )


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    ref, token = _auth()
    if cmd == "diagnose":
        diagnose(ref, token)
    elif cmd == "migrate":
        migrate(ref, token)
    elif cmd == "verify":
        verify(ref, token)
    elif cmd == "query":
        if len(sys.argv) < 3:
            sys.exit("Usage: supabase_admin.py query \"<sql>\"")
        _print("query", _run_sql(ref, token, sys.argv[2]))
    else:
        sys.exit(f"Unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
