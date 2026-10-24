"""Pedotransfer functions for soil hydraulic properties (Phase 1).

Reference:
- Saxton, K.E. & Rawls, W.J. (2006). Soil Water Characteristic Estimates
  by Texture and Organic Matter for Hydrologic Solutions. SSSAJ 70:975-987.
  (units converted to cm/cm and cm/day)

Three of the four returned values are the published regressions, reproduced
faithfully. One is not, and is labelled where it is implemented.

``theta_s`` is not a saturated water content
--------------------------------------------
The third regression below is the published estimate of plant-available water,
theta(s-33) -- water content at 33 kPa *minus* water content at 1500 kPa. This
module stores it under the name ``theta_s`` and, in the second half of the
function, treats it as the saturated water content theta_s. Those are different
quantities by about a factor of three, and the substitution is not consistent
even within itself, because the clamp ``theta_s = max(theta_s, theta_33 + 0.02)``
fires for most textures and not for the coarsest ones:

* sand 100 / clay 0 / OM 1.0 -> ``theta_s`` = 0.356, the regression unclamped. It
  reads like a plausible theta_s by coincidence.
* sand 40 / clay 25 / OM 1.5 -> ``theta_s`` = 0.3126, which is
  ``theta_33 + 0.02`` = 0.29265 + 0.02. The regression value (0.13942) is
  discarded by the clamp, and 0.3126 is far below the ~0.43 that loam's
  saturated water content is. This module's own sibling table,
  ``engine/hydroma/soil/physics.py``, puts loam theta_s at 0.43.

A caller reading ``theta_s`` gets one of two unrelated numbers depending on the
texture, and the ``awc`` key alongside it is a *different* route to the same
quantity (``theta_33 - theta_1500`` = 0.1426 here against the regression's
0.1394, a 2 % disagreement between the two published forms).

Not fixed here: supplying a real theta_s needs a source that is not in the
repository, and renaming or removing the key changes the response of
``POST /api/v1/hydroma/soil/pedotransfer/run``. The value is left exactly as it
was and labelled.

``ks_cm_per_day`` is not a conductivity in any unit
--------------------------------------------------
The saturated-conductivity block below computes ``exp()`` of a linear
combination of sand and clay percentages and then multiplies by ``2.778``.
Neither the combination nor the prefactor can be attributed to the cited paper
from anything in this repository: the coefficients appear nowhere else in the
tree, and ``2.778`` appears nowhere else in the tree at all.

Substituting the variables as written into the printed expression, with
sand_pct = 40 and clay_pct = 20:

    ln_ks = 12.012 - 0.0755*40 + (-3.895 + 0.03671*40 - 0.110*20
              + 0.00876*400 + 0.000501*1600*20 - 0.000452*40*400)
          = 16.6694
    exp(16.6694) * 2.778 = 4.82e7   cm/h, i.e. 1.16e9 cm/day

1.16e9 cm/day is 11,500 km/day. It is off by roughly eight orders of magnitude
from the saturated conductivity of a sandy loam, and the sign of the
clay-dependence is wrong as well: the function returns *more* water for more
clay (clay 100 / sand 0 gives 4.1e38 cm/day), which no soil does. No caller and
no test in the repository read the value under the key it used to carry,
``ks_cm_per_day`` -- ``services/validation/formula_checks.py`` checks only
``awc`` from this function -- which is why it survived.

What would resolve it, and what was deliberately not done
---------------------------------------------------------
1. The paper, or a copy of its equation set, so the coefficient set and the
   prefactor can be checked against it rather than inferred. It is not in the
   repository and the same project rule that withdrew the Carsel & Parrish
   attribution on the sibling table (see engine/data/SOIL_TABLE_CONFLICTS.md)
   applies here.
2. A leading candidate worth checking against it, recalled here and NOT
   verified: the paper is usually cited for a direct saturated-conductivity
   regression rather than a log-linear one, of the form
   ``Ksat = 1930 * (theta_33 - theta_1500) ** (3 - theta_33)`` in cm/day.
   Applied to the same inputs that gives 9.9 cm/day, which is the right order of
   magnitude. It has **not** been substituted here, because it was recalled and
   not read: writing it in would replace a labelled defect with an unlabelled
   guess, which is the failure this repository's measurement rule exists to
   prevent.
3. Failing the source, a unit test asserting Ksat falls with clay content and
   lands inside a stated cm/day band. Such a test would have caught this at
   introduction. That test is not written here either, because without the
   source any band would be invented.

Containment (P0-5)
------------------
The arithmetic is unchanged, but the value is no longer emitted under the key
``ks_cm_per_day``. It is emitted as ``ks_cm_per_day_unconfirmed``, alongside
``ks_confirmed = False`` and the ``UNCONFIRMED_UNITHED_CONSTANTS`` marker, so a
consumer of ``POST /api/v1/hydroma/soil/pedotransfer/run`` cannot read it as an
attributed saturated conductivity. Nothing was deleted and no dependency broke:
no caller and no test in the repository read the old key -- the only in-tree
reader of this function's output, ``services/validation/formula_checks.py``,
checks ``awc`` alone. The rename is the containment, and this paragraph is its
record.
"""

import math
from typing import Any

#: Marker for a value whose provenance cannot be established from anything in
#: this repository. A response field carrying this string must not be read as a
#: measurement, and a test asserting a value carries it must also assert the
#: flag is unconfirmed.
UNCONFIRMED_UNITHED_CONSTANTS = "UNCONFIRMED_UNITHED_CONSTANTS"


def estimate_soil_parameters(
    sand_pct: float,
    clay_pct: float,
    om_pct: float = 1.0,
) -> dict[str, Any]:
    """Estimate hydraulic parameters from texture + organic matter.

    Implements the Saxton & Rawls (2006) regression-style estimates
    (sand/clay/organic-matter fractions are used as decimals in the
    original regressions; here we reproduce the standard published form).

    Args:
        sand_pct: sand percentage (0-100)
        clay_pct: clay percentage (0-100)
        om_pct: organic matter percentage (default 1.0)

    Returns:
        dict with theta_1500 (PWP), theta_33 (FC), theta_s, awc, and
            ``ks_cm_per_day_unconfirmed`` (gated: see the module docstring).

    ``theta_s`` and ``ks_cm_per_day_unconfirmed`` are not what their names say.
    See the module docstring; neither defect is repaired here, but the second
    is gated behind the ``ks_confirmed`` flag so no response payload can serve
    it as an attributed conductivity.
    """
    S = sand_pct / 100.0
    C = clay_pct / 100.0
    OM = om_pct / 100.0

    # Moisture at 1500 kPa (permanent wilting point)
    theta_1500 = (
        -0.024 * S
        + 0.487 * C
        + 0.006 * OM
        + 0.005 * (S * OM)
        - 0.013 * (C * OM)
        + 0.068 * (S * C)
        + 0.031
    )
    # Moisture at 33 kPa (field capacity)
    theta_33 = (
        -0.251 * S
        + 0.195 * C
        + 0.011 * OM
        + 0.006 * (S * OM)
        - 0.027 * (C * OM)
        + 0.452 * (S * C)
        + 0.299
    )
    # Published estimate of plant-available water, theta(s-33). NOT theta_s.
    # Stored under the name theta_s by this module since it was written; see the
    # module docstring. The clamp below is what turns it into theta_33 + 0.02 for
    # most textures while leaving it as the regression for the coarsest ones.
    theta_s = (
        0.278 * S
        + 0.034 * C
        + 0.022 * OM
        - 0.018 * (S * OM)
        - 0.027 * (C * OM)
        - 0.584 * (S * C)
        + 0.078
    )

    # Saturated hydraulic conductivity.
    #
    # UNATTRIBUTED. The coefficient set and the 2.778 prefactor are in no other
    # file in this repository, and the 2.778 appears in no other file in this
    # repository at all, so neither can be traced to Saxton & Rawls (2006) from
    # anything in-tree. The comment above this block used to say "Saturated
    # hydraulic conductivity [cm/h] then converted to cm/day (published
    # Saxton-Rawls log form)", which asserted a provenance nothing supports.
    #
    # With sand_pct = 40 and clay_pct = 20 the printed expression evaluates to
    # exp(16.6694) * 2.778 = 4.82e7 cm/h. See the module docstring for why that
    # is not a conductivity in any unit and for what would be needed to resolve
    # it. The arithmetic is unchanged.
    ln_ks_cmh = (
        12.012
        - 0.0755 * (sand_pct)
        + (
            -3.895
            + 0.03671 * (sand_pct)
            - 0.110 * (clay_pct)
            + 0.00876 * (clay_pct**2)
            + 0.000501 * (sand_pct**2) * (clay_pct)
            - 0.000452 * (sand_pct) * (clay_pct**2)
        )
    )
    ks_cmh = 2.778 * max(1e-6, float(math.exp(ln_ks_cmh)))
    ks_cm_day = ks_cmh * 24.0

    # Sanity clamps (prevent non-physical values). The first of these is what
    # silently replaces the AWC regression above with theta_33 + 0.02 -- see the
    # module docstring. Neither clamp touches ks_cm_day.
    theta_s = max(theta_s, theta_33 + 0.02)
    theta_33 = max(theta_33, theta_1500 + 0.01)
    theta_1500 = max(theta_1500, 0.01)
    theta_s = min(theta_s, 0.60)

    # The ks value is returned under a gated key, not ``ks_cm_per_day``. It is
    # the same arithmetic, unchanged and documented in the module docstring;
    # only the key and the accompanying flags changed, so no consumer can read
    # it as an attributed saturated conductivity. See "Containment (P0-5)".
    return {
        "theta_1500": round(theta_1500, 4),
        "theta_33": round(theta_33, 4),
        "theta_s": round(theta_s, 4),
        "awc": round(theta_33 - theta_1500, 4),
        "ks_cm_per_day_unconfirmed": round(ks_cm_day, 2),
        "ks_confirmed": False,
        "ks_unconfirmed_marker": UNCONFIRMED_UNITHED_CONSTANTS,
        "ks_note": (
            "Unattributed: the coefficient set and 2.778 prefactor appear "
            "nowhere else in this repository and cannot be traced to Saxton & "
            "Rawls (2006). Do not read as a saturated conductivity."
        ),
    }


def estimate_texture_from_particles(sand_pct: float, clay_pct: float) -> str:
    """Quick texture estimate from sand/clay (silt = remainder)."""
    from .texture import classify_texture

    silt = 100.0 - sand_pct - clay_pct
    return classify_texture(sand_pct, silt, clay_pct)
