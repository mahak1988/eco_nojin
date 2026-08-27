"""Layer 11 — zero-trust audit logging.

Every security/authz decision is recorded. Writes go to the Supabase
`security_events` / `audit_log` tables when credentials are available
(Management API, free tier), otherwise to a local JSONL file under
`data/security/` — the honest fallback is explicit in the record.
"""
import json
import os
import time
from pathlib import Path
from typing import Any

_AUDIT_DIR = Path("data/security")
_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
_LOCAL_FILE = _AUDIT_DIR / "audit.jsonl"


def _local_write(kind: str, record: dict[str, Any]) -> None:
    with open(_LOCAL_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": kind, **record}, ensure_ascii=False) + "\n")


def _supabase_write(table: str, row: dict[str, Any]) -> bool:
    """Best-effort insert via Supabase Management API (parameterized, no DB password)."""
    try:
        import httpx

        token = os.getenv("SUPABASE_ACCESS_TOKEN", "")
        ref = os.getenv("SUPABASE_PROJECT_REF", "cpncggavcfplewlhvvnw")
        if not token:
            return False
        sql = (
            f"insert into {table} (id, ts, ip, actor, action, decision, detail, severity) "
            "values (gen_random_uuid(), now(), $1, $2, $3, $4, $5::jsonb, $6)"
        )
        payload = {
            "query": sql,
            "params": [
                row.get("ip"), row.get("actor"), row.get("action"),
                row.get("decision"), json.dumps(row.get("detail", {}), ensure_ascii=False),
                row.get("severity", "info"),
            ],
        }
        resp = httpx.post(
            f"https://api.supabase.com/v1/projects/{ref}/database/query",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def log_event(
    kind: str,
    ip: str,
    action: str,
    decision: str,
    detail: dict[str, Any],
    actor: str | None = None,
    severity: str = "info",
) -> None:
    """Record a security event. `kind` in {waf, rate, anomaly, honeypot, authz, phishing}."""
    record = {
        "ts": time.time(),
        "ip": ip,
        "actor": actor or "anonymous",
        "action": action,
        "decision": decision,
        "severity": severity,
        "detail": detail,
    }
    # Try cloud, fall back to local — the record says which store was used.
    if not _supabase_write("security_events", record):
        record["store"] = "local-jsonl"
        _local_write(kind, record)


def recent_events(limit: int = 20) -> list:
    """Read recent events from the local store (works offline, deterministic)."""
    events = []
    if _LOCAL_FILE.exists():
        with open(_LOCAL_FILE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return events[-limit:]
