"""
Evapotranspiration computation dispatch module.

Routes CANON model IDs to their scientific implementations in
``engine.hydroma.climate.et_calculator``. The gateway's
``_dispatch_by_type`` calls this module's ``compute_et`` function for
CANON-001, CANON-002, CANON-003, and CANON-011_RAD.

Input keys arriving from the gateway use the *facade naming convention*
(``temp_max``, ``temp_min``, ``rh_min``, etc.) and are accompanied by
``_unit`` suffixed parallel entries (added by ``_normalize_inputs``).
This module strips those and maps the remaining scalar values to the
``ClimateData`` fields that the calculator expects (``tmax``, ``tmin`` …).
"""

from __future__ import annotations

from typing import Any

from engine.hydroma.climate.et_calculator import (
    ClimateData,
    calc_et0_hargreaves,
    calc_et0_penman_monteith,
    calc_extraterrestrial_radiation,
)


def _strip_units(inputs: dict[str, Any]) -> dict[str, Any]:
    """Remove ``_unit`` suffixed keys produced by the gateway normalizer."""
    return {k: v for k, v in inputs.items() if not k.endswith("_unit")}


def compute_et(
    model_id: str,
    inputs: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Dispatch an ET model to its calculator implementation.

    Parameters
    ----------
    model_id
        One of ``CANON-001`` (Penman-Monteith), ``CANON-002``
        (Hargreaves), ``CANON-003`` (Thornthwaite), ``CANON-011_RAD``
        (extraterrestrial radiation).
    inputs
        Normalized input dict from the gateway (facade naming, with
        ``_unit`` suffixed entries that are silently ignored).
    parameters
        Additional model parameters (currently unused).

    Returns
    -------
    dict with ``et0_mm_day`` (or ``ra_mj_m2_day``) and ``method`` keys.

    Raises
    ------
    NotImplementedError for CANON-003 (Thornthwaite) which has no
    Python implementation yet.
    ValueError for an unrecognized model_id.
    """
    clean = _strip_units(inputs)

    if model_id == "CANON-002":
        data = ClimateData(
            tmin=clean["temp_min"],
            tmax=clean["temp_max"],
            elevation=clean.get("elevation", 0.0),
            latitude=clean.get("latitude", 0.0),
            doy=int(clean.get("doy", 1)),
        )
        et0 = calc_et0_hargreaves(data=data)
        return {"et0_mm_day": et0, "method": "hargreaves"}

    if model_id == "CANON-001":
        data = ClimateData(
            tmin=clean["temp_min"],
            tmax=clean["temp_max"],
            rh_min=clean.get("rh_min"),
            rh_max=clean.get("rh_max"),
            wind_speed=clean.get("wind_speed"),
            solar_radiation=clean.get("solar_radiation"),
            elevation=clean.get("elevation", 0.0),
            latitude=clean.get("latitude", 0.0),
            doy=int(clean.get("doy", 1)),
        )
        et0 = calc_et0_penman_monteith(data)
        return {"et0_mm_day": et0, "method": "penman_monteith"}

    if model_id == "CANON-011_RAD":
        ra = calc_extraterrestrial_radiation(
            clean.get("latitude", 0.0),
            int(clean.get("doy", 1)),
        )
        return {"ra_mj_m2_day": ra, "method": "extraterrestrial_radiation"}

    if model_id == "CANON-003":
        raise NotImplementedError(
            "CANON-003 (Thornthwaite PET) is not yet implemented — see ECO-03.1"
        )

    raise ValueError(f"Unknown ET model: {model_id}")
