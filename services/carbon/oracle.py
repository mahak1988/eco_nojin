"""
VerificationOracle (Phase 8) — certificate-style issuance report.

Wraps the VM0042-style methodology checks + credit issuance into a single
auditable "oracle report" (the migration target from econojin.com).
The report is generated ONLY from real stored state (project + checks) —
never fabricated; it can be rendered as a PDF certificate later.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from database import models


def build_oracle_report(project: "models.CarbonProject") -> Dict[str, Any]:
    """Assemble an oracle certificate from a stored carbon project."""
    import json

    detail: Optional[Dict[str, Any]] = None
    if project.verification_detail:
        try:
            detail = json.loads(project.verification_detail)
        except Exception:  # noqa: BLE001
            detail = None

    checks = (detail or {}).get("checks", []) if detail else []
    return {
        "certificate_id": f"ECO-ORACLE-{project.project_id}",
        "project_id": project.project_id,
        "name": project.name,
        "methodology": (detail or {}).get("methodology", "VM0042-aligned"),
        "verification_status": project.verification_status,
        "checks": [
            {"name": c.get("name"), "passed": c.get("passed"), "detail": c.get("detail")}
            for c in checks
        ],
        "credits_issued": project.credits_issued,
        "status": project.status,
        "registered_at": project.registered_at.isoformat() if project.registered_at else None,
        "issued_at": project.issued_at.isoformat() if project.issued_at else None,
        "issuer": "Eco Nojin VerificationOracle",
        "note": "گواهی دیجیتال؛ قابل ارایه به حسابرس مستقل — نه جایگزین مشاوره حقوقی",
    }
