"""
Theis drawdown computation dispatch module.

Routes CANON-005 to the Theis (1935) implementation in
``engine.hydroma.groundwater.models``. The gateway's
``_dispatch_by_type`` calls this module's ``compute_theis`` function.

Input keys arriving from the gateway are accompanied by ``_unit``
suffixed parallel entries (added by ``_normalize_inputs``). This
module strips those and maps the remaining scalar values to the
``calculate_theis_drawdown`` parameters.

The scientific relation is the Theis (1935) solution for drawdown
in a confined aquifer::

    s = Q / (4 pi T) * W(u),      u = r^2 S / (4 T t),      W(u) = E1(u)

The implementation lives in ``calculate_theis_drawdown`` and is
covered by ``engine/strict_tests/test_s04_groundwater.py`` against
the published Theis reference. This module is a thin adapter only;
it contains no scientific formula of its own.
"""

from __future__ import annotations

from typing import Any

from engine.hydroma.groundwater.models import calculate_theis_drawdown


def _strip_units(inputs: dict[str, Any]) -> dict[str, Any]:
    """Remove ``_unit`` suffixed keys produced by the gateway normalizer."""
    return {k: v for k, v in inputs.items() if not k.endswith("_unit")}


def _require(clean: dict[str, Any], *names: str) -> Any:
    """Return the first present, non-None value among *names*."""
    for name in names:
        if name in clean and clean[name] is not None:
            return clean[name]
    raise KeyError(f"theis input missing: expected one of {names}")


def compute_theis(
    inputs: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Dispatch a Theis drawdown request to its implementation.

    Parameters
    ----------
    inputs
        Normalized input dict from the gateway (with ``_unit``
        suffixed entries that are silently ignored). Accepts the
        canonical day-based parameter names and their short forms.
    parameters
        Additional model parameters (currently unused).

    Returns
    -------
    dict with a ``drawdown_m`` key. ``drawdown_m`` is ``None``
    when the implementation rejects the parameters (non-positive
    storativity or transmissivity); the singularities at the well
    face (``r <= 0``) and at time zero (``t <= 0``) raise
    ``ValueError``, which the gateway surfaces as an execution error.
    """
    clean = _strip_units(inputs)

    transmissivity = float(
        _require(clean, "transmissivity_m2day", "transmissivity", "T")
    )
    storativity = float(_require(clean, "storativity", "S"))
    pumping_rate = float(
        _require(clean, "pumping_rate_m3day", "pumping_rate", "Q")
    )
    distance = float(
        _require(clean, "distance_from_well_m", "distance_from_well", "distance", "r")
    )
    time_days = float(
        _require(
            clean,
            "time_since_pumping_start_days",
            "time_since_pumping_start",
            "time",
            "t",
        )
    )

    drawdown = calculate_theis_drawdown(
        transmissivity_m2day=transmissivity,
        storativity=storativity,
        pumping_rate_m3day=pumping_rate,
        distance_from_well_m=distance,
        time_since_pumping_start_days=time_days,
    )

    return {
        "drawdown_m": drawdown,
        "method": "theis",
    }
