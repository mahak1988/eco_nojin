"""
EcoCoin distribution engine (Phase 8) — 70/15/10/5 split.

Every carbon/eco payout is split transparently:
- 70%  producer (farmer / project owner)
- 15%  platform & operations (community fund)
- 10%  ecosystem restoration fund
-  5%  governance / reserve

``distribute`` returns the exact split — the caller decides where each
share is credited (wallet earn calls), so no fake accounting here.
"""
from __future__ import annotations

from typing import Any

SHARES = {
    "producer": 0.70,
    "platform": 0.15,
    "ecosystem": 0.10,
    "governance": 0.05,
}


def distribute(total: float) -> dict[str, Any]:
    """Split ``total`` ECO by the 70/15/10/5 rule (sum == total, exact)."""
    if total <= 0:
        raise ValueError("total must be positive")
    parts = {name: round(total * share, 6) for name, share in SHARES.items()}
    # fix rounding drift so the parts sum EXACTLY to total
    drift = round(total - sum(parts.values()), 6)
    parts["governance"] = round(parts["governance"] + drift, 6)
    return {
        "total": round(total, 6),
        "shares": SHARES,
        "parts": parts,
        "sum": round(sum(parts.values()), 6),
        "rule": "70/15/10/5",
    }
