"""Make a disputed conductivity row fail loudly instead of silently.

The publication could not be obtained: four routes were tried and all are
blocked (the search provider returns 403, DuckDuckGo and its lite front end
serve a bot challenge, Bing returns unrelated results, Mojeek returns 403). So
the four rows stay unresolved.

What this module does about it
------------------------------
Not nothing. The four values are still served - deleting them would break
callers - but a caller who asks for one is warned, with the texture, the value,
the interval its own physics permits, and where the conflict is written down. A
wrong number that announces itself is a smaller problem than one that does not.

The check is derived from the fineness ordering, which is a physical law and
needs no publication: saturated conductivity cannot rise with texture fineness,
so each row is bracketed by its coarser and finer neighbours. Three of the four
rows have an EMPTY interval, meaning the two neighbours already contradict each
other and no single-row repair is possible. That is recorded per row rather than
inferred at call time, so the value is stable and comparable.

Closing it
----------
``python -m engine.data.apply_published_table --from published.csv`` writes a
verified table in, re-derives the intervals, regenerates the C++ block, and
flips the status from ``design_assumption_disputed`` to ``verified``.
"""

from __future__ import annotations

import warnings
from typing import Any


class PhysicsWarning(UserWarning):
    """A parameter value that violates a physical constraint of its own table."""


def disputed_rows() -> dict[str, dict[str, Any]]:
    """Rows whose Ks does not sit inside the interval fineness permits."""
    from engine.data.soil_table import FINENESS_ORDER, SOIL_PARAMETERS

    out: dict[str, dict[str, Any]] = {}
    for texture in FINENESS_ORDER:
        entry = SOIL_PARAMETERS[texture]
        if entry["ks_interval_empty"] or entry["ks_outside_interval"]:
            out[texture] = {
                "value_cm_per_day": entry["Ks"],
                "admissible_min": entry["ks_admissible_min"],
                "admissible_max": entry["ks_admissible_max"],
                "empty_interval": entry["ks_interval_empty"],
            }
    return out


def warn_if_disputed(texture: str, stacklevel: int = 3) -> None:
    """Emit a :class:`PhysicsWarning` if this row is unresolved."""
    row = disputed_rows().get(texture)
    if row is None:
        return
    hi = row["admissible_max"]
    interval = f"its neighbours must bracket it between {row['admissible_min']:.2f} and " + (
        "unbounded above" if hi == float("inf") else f"{hi:.2f}"
    )
    kind = (
        "its two neighbours contradict each other, so no single-row repair exists"
        if row["empty_interval"]
        else interval
    )
    warnings.warn(
        f"soil texture {texture!r}: saturated conductivity "
        f"{row['value_cm_per_day']:.2f} cm/day is disputed - {kind}. "
        f"Conductivity cannot rise with texture fineness. The value is served "
        f"because callers depend on it, but it is a design assumption, not a "
        f"transcription. See engine/data/SOIL_TABLE_CONFLICTS.md, and close it "
        f"with: python -m engine.data.apply_published_table --from <published.csv>",
        PhysicsWarning,
        stacklevel=stacklevel,
    )
