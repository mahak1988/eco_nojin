"""Water balance (indicator ENO_WB_001) — mass-conserving storage bucket.

Implements the water-balance equation per period, with every term in mm
per period::

    P = ET + Q + dS

where ``P`` is precipitation, ``ET`` is evapotranspiration, ``Q`` is
runoff and ``dS`` is the change in storage over the period. The bucket
state is integrated recursively::

    storage[t] = storage[t - 1] + P[t] - ET[t] - Q[t]

Storage is a physical quantity and may never become negative, so the
state is clamped at zero (``storage[t] = max(0, bucket[t])``). Clamping
removes demand from the balance: the part of ``ET[t] + Q[t]`` that the
available water ``P[t] + storage[t - 1]`` could not supply is reported
per period in ``excess_mm`` instead of being silently dropped, which is
the mass-conservation honesty requirement. The clamped balance is::

    P[t] + storage[t - 1] = (ET[t] + Q[t] - excess_mm[t]) + storage[t]

The reported closure residual follows from the returned (clamped) arrays::

    closure_mm[t] = P[t] - ET[t] - Q[t]
                    - (storage[t] - storage[t - 1]) + excess_mm[t]

Without the clamping term the residual of a clamped period would equal
``-excess_mm[t]``; adding it back closes the balance at zero and
accounts the removed water.

Reference: water-balance equation (Thornthwaite / FAO-56 style mass
balance), https://www.fao.org/3/X0490E/x0490e00.htm

Indicator: ``indicators/ENO_WB_001.yaml``.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def water_balance(
    precip: Any,
    et: Any,
    runoff: Any,
    storage0: float = 0.0,
) -> dict[str, Any]:
    """Integrate the water balance ``P = ET + Q + dS`` over equal periods.

    Parameters
    ----------
    precip, et, runoff
        One-dimensional sequences of equal length holding the
        per-period fluxes in mm per period.
    storage0
        Storage at the start of the first period, in mm (default 0.0).

    Returns
    -------
    dict
        ``storage`` (ndarray): end-of-period storage in mm, clamped at
        ``>= 0`` so water is never negative. ``excess_mm`` (ndarray):
        per-period demand removed by the clamp, i.e.
        ``max(0, ET + Q - P - storage_prev)``, reported so no water is
        silently dropped. ``closure_mm`` (ndarray): per-period mass
        closure residual, ``P - ET - Q - dS + excess_mm``.
        ``max_abs_closure`` (float): largest absolute residual.

    Raises
    ------
    ValueError
        If the inputs are not one-dimensional, do not share a length,
        or cannot be converted to float arrays.

    Notes
    -----
    These are not independent scientific validation: no published
    benchmark series is involved, only the mass-balance identity and
    the governing recurrence of this bucket.
    """
    precip_arr = np.asarray(precip, dtype=float)
    et_arr = np.asarray(et, dtype=float)
    runoff_arr = np.asarray(runoff, dtype=float)

    if precip_arr.ndim != 1 or et_arr.ndim != 1 or runoff_arr.ndim != 1:
        raise ValueError("precip, et and runoff must be one-dimensional sequences")
    if not (precip_arr.size == et_arr.size == runoff_arr.size):
        raise ValueError("precip, et and runoff must have the same length")

    n_periods = int(precip_arr.size)
    storage = np.zeros(n_periods, dtype=float)
    excess_mm = np.zeros(n_periods, dtype=float)
    closure_mm = np.zeros(n_periods, dtype=float)

    prev_storage = float(storage0)
    for period in range(n_periods):
        precip_mm = float(precip_arr[period])
        et_mm = float(et_arr[period])
        runoff_mm = float(runoff_arr[period])

        available = prev_storage + precip_mm
        demand = et_mm + runoff_mm

        if demand > available:
            end_storage = 0.0
            excess_mm[period] = demand - available
        else:
            end_storage = available - demand

        storage[period] = end_storage
        closure_mm[period] = precip_mm - et_mm - runoff_mm - (end_storage - prev_storage)
        closure_mm[period] += float(excess_mm[period])
        prev_storage = end_storage

    if n_periods:
        max_abs_closure = float(np.max(np.abs(closure_mm)))
    else:
        max_abs_closure = 0.0

    return {
        "storage": storage,
        "excess_mm": excess_mm,
        "closure_mm": closure_mm,
        "max_abs_closure": max_abs_closure,
    }
