"""Water quality assessment utilities."""
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

    if not (6.5 <= ph <= 8.5):
        ph_status = False
    else:
        ph_status = True

    if ec <= 1.5:
        ec_status = True
    elif ec <= 3.0:
        ec_status = "moderate"
    else:
        ec_status = False

    if tds <= 1000:
        tds_status = True
    elif tds <= 2000:
        tds_status = "moderate"
    else:
        tds_status = False

    if ph_status is True and ec_status is True and tds_status is True:
        return "good"
    if ph_status is False or ec_status is False or tds_status is False:
        return "poor"
    return "moderate"


def classify_salinity(ec: float) -> str:
    """Classify soil/water salinity from EC."""
    if ec < 2:
        return "non_saline"
    if ec < 4:
        return "slightly_saline"
    if ec < 8:
        return "moderately_saline"
    if ec < 16:
        return "strongly_saline"
    return "very_strongly_saline"
