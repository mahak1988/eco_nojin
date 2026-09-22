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

import yaml
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "distribution_constants.yaml"

with open(CONFIG_PATH) as f:
    _config = yaml.safe_load(f)

SHARES = _config["DISTRIBUTION_PCT"]
SHARES_BPS = _config["DISTRIBUTION_BPS"]
BURN_RATE_BPS = _config["BURN_RATE_BPS"]


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


def distribute_bps(total: int) -> dict[str, int]:
    """Split ``total`` ECO (in base units) by basis points (exact integer math)."""
    if total <= 0:
        raise ValueError("total must be positive")
    parts = {name: (total * bps) // 10000 for name, bps in SHARES_BPS.items()}
    # fix rounding drift
    drift = total - sum(parts.values())
    parts["governance"] += drift
    return parts


def apply_burn(total: int, burn_rate_bps: int = None) -> tuple[int, int]:
    """Apply burn rate and return (burned_amount, net_amount)."""
    if burn_rate_bps is None:
        burn_rate_bps = BURN_RATE_BPS
    burned = (total * burn_rate_bps) // 10000
    net = total - burned
    return burned, net
