"""Economic engine bindings for the gateway facade.

Owns the facade's engine import from ``engine.hydroma.economics.employment``
(``estimate_direct_employment``) and the thin public wrapper of the same name
the facade has always published.

The engine function is imported under its ``engine_`` name so the public
facade name stays bound to the wrapper, which is the only public entry point
the facade exposes for this capability.
"""

from __future__ import annotations

from typing import Any

from engine.hydroma.economics.employment import (
    estimate_direct_employment as engine_estimate_direct_employment,
)

__all__ = ["engine_estimate_direct_employment", "estimate_direct_employment"]


def estimate_direct_employment(
    activity_type: str,
    scale_of_activity: float,
    employment_intensity_per_unit: float,
    job_type: str = "full_time_equivalent",
    duration_months: float = 12.0,
) -> dict[str, Any]:
    """Estimate direct employment for an activity."""
    return engine_estimate_direct_employment(
        activity_type=activity_type,
        scale_of_activity=scale_of_activity,
        employment_intensity_per_unit=employment_intensity_per_unit,
        job_type=job_type,
        duration_months=duration_months,
    )
