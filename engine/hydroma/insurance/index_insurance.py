"""Index-based insurance prototype (Phase 10, step 1).

Computes an NDVI-based index from real (or validated synthetic) seasonal
NDVI series and evaluates a simple payout trigger against a reference level.

Honest rules:
- The module only computes the index and trigger; it does NOT price premiums
  (that requires actuarial calibration and regulatory review).
- Missing/NaN values are rejected (fail-fast), never silently imputed.
- Reference NDVI must be provided or computed from an explicit baseline
  series; the module never invents a baseline.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class IndexInsuranceResult:
    """Outcome of an index evaluation."""

    farm_id: str
    season_mean_ndvi: float
    reference_ndvi: float
    deficit: float  # reference - season mean (positive = shortfall)
    trigger_active: bool
    payout_rate: float  # 0..1 of insured sum (linear ramp beyond trigger)
    note: str = field(default="")


class IndexInputError(ValueError):
    """Invalid index input (rejected, not imputed)."""


def season_mean_ndvi(ndvi_values: List[float]) -> float:
    """Robust seasonal mean: rejects NaN/negative/out-of-range values."""
    clean: List[float] = []
    for v in ndvi_values:
        if v is None or v != v:  # NaN check
            raise IndexInputError("missing/NaN NDVI value in series")
        if v < 0.0 or v > 1.0:
            raise IndexInputError(f"NDVI out of range [0,1]: {v}")
        clean.append(v)
    if len(clean) < 3:
        raise IndexInputError("season NDVI series needs at least 3 observations")
    return statistics.fmean(clean)


def evaluate_index_insurance(
    farm_id: str,
    ndvi_values: List[float],
    reference_ndvi: Optional[float] = None,
    trigger_deficit: float = 0.15,
    full_payout_deficit: float = 0.45,
) -> IndexInsuranceResult:
    """Evaluate the NDVI index trigger.

    payout_rate ramps linearly from 0 at ``trigger_deficit`` to 1 at
    ``full_payout_deficit`` (both expressed as fractions of reference NDVI).
    """
    mean = season_mean_ndvi(ndvi_values)
    if reference_ndvi is None:
        raise IndexInputError("reference_ndvi is required (no invented baseline)")
    if not (0.0 < reference_ndvi <= 1.0):
        raise IndexInputError(f"reference NDVI out of range: {reference_ndvi}")
    if trigger_deficit <= 0 or full_payout_deficit <= trigger_deficit:
        raise IndexInputError("invalid trigger/full-payout deficit thresholds")

    deficit = reference_ndvi - mean
    if deficit <= trigger_deficit * reference_ndvi:
        rate = 0.0
    elif deficit >= full_payout_deficit * reference_ndvi:
        rate = 1.0
    else:
        span = (full_payout_deficit - trigger_deficit) * reference_ndvi
        rate = (deficit - trigger_deficit * reference_ndvi) / span

    return IndexInsuranceResult(
        farm_id=farm_id,
        season_mean_ndvi=round(mean, 4),
        reference_ndvi=round(reference_ndvi, 4),
        deficit=round(deficit, 4),
        trigger_active=rate > 0.0,
        payout_rate=round(max(0.0, min(1.0, rate)), 4),
        note="شاخص NDVI فصلی — پرداخت نیازمند بازبینی اکچوئری و مقررات بیمه است",
    )
