"""
Runoff computation dispatch module.

Routes CANON-004 and CANON-008 to the SCS-CN and Rational-method
implementation in ``engine.hydroma.models.runoff_model``. The
gateway's ``_dispatch_by_type`` calls this module's
``compute_runoff`` function.

Input keys arriving from the gateway use the facade naming
convention (``precipitation``, ``curve_number``, ``ia_factor``)
and are accompanied by ``_unit`` suffixed parallel entries (added
by ``_normalize_inputs``). This module strips those and maps the
remaining scalar values to the ``RunoffInput`` fields that the
calculator expects.

The scientific relation is the NRCS curve-number method
(NRCS National Engineering Handbook, Part 630 / TR-55), SI form::

    S  = 25400 / CN - 254            [mm]
    Ia = 0.2 S                        [mm]
    Q  = (P - Ia)^2 / (P + 0.8 S)     [mm]   for P > Ia, else 0

The implementation lives in ``RunoffCalculator`` and is covered by
``engine/strict_tests/test_s03_hydrology_runoff.py`` against the
published NRCS worked example. This module is a thin adapter only;
it contains no scientific formula of its own.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from engine.hydroma.models.runoff_model import (
    MethodType,
    RunoffCalculator,
    RunoffInput,
)


def _strip_units(inputs: dict[str, Any]) -> dict[str, Any]:
    """Remove ``_unit`` suffixed keys produced by the gateway normalizer."""
    return {k: v for k, v in inputs.items() if not k.endswith("_unit")}


def _require(clean: dict[str, Any], *names: str) -> Any:
    """Return the first present, non-None value among *names*."""
    for name in names:
        if name in clean and clean[name] is not None:
            return clean[name]
    raise KeyError(f"runoff input missing: expected one of {names}")


def compute_runoff(
    inputs: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Dispatch a runoff model to its calculator implementation.

    Parameters
    ----------
    inputs
        Normalized input dict from the gateway (facade naming, with
        ``_unit`` suffixed entries that are silently ignored).
    parameters
        Additional model parameters (currently unused).

    Returns
    -------
    dict with ``runoff_volume_m3``, ``runoff_depth_mm`` and
    ``peak_flow_m3s`` keys. ``runoff_depth_mm`` is the depth over
    the contributing area, which is what the gateway's ``"mm"``
    unit label refers to.
    """
    clean = _strip_units(inputs)

    precipitation_mm = float(
        _require(
            clean,
            "precipitation_mm",
            "precipitation",
            "rainfall_mm",
            "rain_mm",
        )
    )
    curve_number = float(_require(clean, "curve_number", "cn"))
    area_ha = float(clean.get("area_ha", clean.get("area", 1.0)))
    method = str(clean.get("method", "SCS-CN"))
    storm_duration_h = clean.get("storm_duration_h")
    rational_coefficient = float(clean.get("rational_coefficient", 0.6))

    runoff_input = RunoffInput(
        precipitation_mm=precipitation_mm,
        curve_number=curve_number,
        area_ha=area_ha,
        # RunoffInput's Literal check is the runtime filter: an unknown method
        # string raises here, so the payload value is accepted as it arrives.
        method=cast("MethodType", method),
        storm_duration_h=storm_duration_h,
        rational_coefficient=rational_coefficient,
    )
    out = RunoffCalculator().execute(runoff_input)

    depth_mm = out.volume_m3 / (area_ha * 10.0) if area_ha else 0.0
    return {
        "runoff_volume_m3": out.volume_m3,
        "runoff_depth_mm": depth_mm,
        "peak_flow_m3s": out.peak_flow_m3s,
        "method": method,
    }


def scs_cn_raster_depth_mm(
    precipitation: Any,
    curve_number: Any,
    *,
    ia_factor: float = 0.2,
) -> np.ndarray:
    """The SCS-CN triplet for whole grids, in one call.

    The relation is ``RunoffCalculator._scs_cn_method``'s — S = 25400/CN - 254,
    Ia = ``ia_factor`` S, Q = (P - Ia)^2 / (P + 0.8 S) for P > Ia, else 0 —
    evaluated once over array inputs instead of once per scalar gateway call, so
    a raster of N cells costs one vector pass rather than N gateway round
    trips (the per-pair loop was quadratic in practice: measured 2128x slower
    than this on a 300x300 grid).

    Curve numbers follow the scalar contract: a finite CN must be in
    30..100 (the NRCS table is defined for 30 <= CN <= 100; above 100 the
    retention goes negative and below 30 it is physically meaningless — a
    CN of 5 would silently produce an 82-metre retention), and a non-finite
    or below-abstraction cell keeps depth 0. Parity with the scalar method is
    pinned in ``engine/strict_tests`` and by the services raster tests.
    """
    p = np.asarray(precipitation, dtype=np.float64)
    cn = np.asarray(curve_number, dtype=np.float64)
    finite_cn = cn[np.isfinite(cn)]
    if finite_cn.size and (
        float(finite_cn.min()) < 30.0 or float(finite_cn.max()) > 100.0
    ):
        raise ValueError(
            "Curve number must be in 30..100 for the SCS-CN method "
            f"(got [{float(finite_cn.min())}, {float(finite_cn.max())}]); "
            "the NRCS table is defined for 30 <= CN <= 100"
        )
    with np.errstate(divide="ignore", invalid="ignore"):
        s = 25400.0 / cn - 254.0
        ia = ia_factor * s
        q = np.where(p > ia, (p - ia) ** 2 / (p + 0.8 * s), 0.0)
    return np.asarray(np.nan_to_num(q, nan=0.0, posinf=0.0, neginf=0.0), dtype=np.float64)
