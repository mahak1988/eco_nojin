"""Honesty contracts: a claim-status vocabulary that cannot round-trip to "validated".

The point of this module is that a *recorded* result is not a *validated* one.
``refine_claim`` maps the legacy alias ``"validated"`` onto the precise term that
matches the evidence actually produced, so no caller can silently promote a
regression anchor (a test that merely still passes) into an external validation.

Stdlib only: no engine imports, no third-party imports.
"""

from engine.honesty.statuses import (
    AR_COUNT,
    AR_RULES,
    BRAKE_COUNT,
    BRAKES,
    VOCABULARY,
    refine_claim,
)

__all__ = [
    "AR_COUNT",
    "AR_RULES",
    "BRAKE_COUNT",
    "BRAKES",
    "VOCABULARY",
    "refine_claim",
]
