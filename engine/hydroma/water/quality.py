"""Water quality assessment."""

from __future__ import annotations

from typing import Any


def assess_water_quality(ph: float, ec: float, tds: float) -> str:
    """Classify irrigation water quality from basic parameters.

    Parameters
    ----------
    ph:
        Water pH.
    ec:
        Electrical conductivity in dS/m.
    tds:
        Total dissolved solids in ppm.

    Returns
    -------
    str
        Quality class: ``"good"``, ``"moderate"`` or ``"poor"``.
    """
    if ph is None or ec is None or tds is None:
        return "unknown"

    ph_ok = 6.5 <= ph <= 8.5
    ec_ok = ec <= 1.5
    tds_ok = tds <= 1000

    if ph_ok and ec_ok and tds_ok:
        return "good"
    if not ph_ok or ec > 3.0 or tds > 2000:
        return "poor"
    return "moderate"


def classify_salinity(ec: float) -> str:
    """Classify salinity from EC."""
    if ec < 2:
        return "non_saline"
    if ec < 4:
        return "slightly_saline"
    if ec < 8:
        return "moderately_saline"
    if ec < 16:
        return "strongly_saline"
    return "very_strongly_saline"
