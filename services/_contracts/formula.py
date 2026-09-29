"""Single home for every scientific formula — standard S-SCI.

The rule this module exists to enforce:

    One formula, one place, with a citation and a unit. Every other
    implementation delegates here.

The failure mode it replaces: five different LS-factor formulas and four
different K-factor implementations for the same RUSLE model, living in five
files, differing by up to 7.6x, with two of them demanding SOC in different
units and no type guard to stop the caller getting it wrong.

============  =====================================  ==========================
Quantity      Reference implementation             Replaces
============  =====================================  ==========================
RUSLE LS      :func:`ls_factor`                    5 implementations
RUSLE K       :func:`k_factor_epic`                 4 implementations
RUSLE R       :func:`r_factor`                     1 ad-hoc implementation
SCS-CN runoff :func:`runoff_scs`                   1 ad-hoc implementation
Erosion class :func:`erosion_class`                2 disagreeing thresholds
============  =====================================  ==========================

Registering a new formula requires a ``reference`` string. A formula without
one is not admitted, because the whole point of this table is that a number
produced here can be traced to a source.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

__all__ = [
    "FORMULAS",
    "Formula",
    "erosion_class",
    "k_factor_epic",
    "lookup",
    "ls_factor",
    "ls_factor_wischmeier_smith",
    "r_factor",
    "register",
    "runoff_scs",
]

#: Physical bounds for the **Renard (1997) additive** polynomial implemented by
#: :func:`k_factor_epic`, in t·ha·yr·mm.
#:
#: The upper bound is 0.65, not 0.09. 0.09 is the ceiling
#: ``services/satellite/soilgrids.py`` clips to, and that file uses the
#: *Williams (1995) multiplicative* four-term form — a different equation whose
#: output happens to sit in a narrower band. Applying its ceiling to the
#: Renard polynomial clipped **every** real texture to 0.09, which made three
#: migrated call sites return a constant and turned a soil-erosion raster into
#: a single flat value.
#:
#: Note these two forms are both "EPIC" in casual use but are not the same
#: equation and do not agree numerically. Reconciling them is a scientific
#: decision, recorded in the integration plan, not a code fix.
K_BOUNDS = (0.001, 0.65)
#: Clip band used by the Williams (1995) multiplicative form, which is a
#: different equation with a different output range. Measured maximum over the
#: texture domain is 0.0645, so this band never actually binds.
K_BOUNDS_WILLIAMS = (0.001, 0.09)
C_BOUNDS = (0.005, 1.0)
P_BOUNDS = (0.0, 1.0)


@dataclass(frozen=True)
class Formula:
    """A registered formula: implementation, provenance, units."""

    name: str
    fn: Callable[..., float]
    reference: str
    units: str
    replaces: tuple[str, ...] = ()

    def __call__(self, *args: object, **kwargs: object) -> float:
        return self.fn(*args, **kwargs)


FORMULAS: dict[str, Formula] = {}


def register(
    name: str,
    fn: Callable[..., float],
    *,
    reference: str,
    units: str,
    replaces: tuple[str, ...] = (),
) -> Formula:
    """Register a formula. A blank ``reference`` is refused.

    This is the enforcement point for "a number must be traceable to a source".
    """
    if not reference or not reference.strip():
        raise ValueError(f"formula {name!r} requires a non-empty reference")
    formula = Formula(name=name, fn=fn, reference=reference, units=units, replaces=replaces)
    if name in FORMULAS:
        raise ValueError(f"formula {name!r} is already registered to a different implementation")
    FORMULAS[name] = formula
    return formula


def lookup(name: str) -> Formula:
    try:
        return FORMULAS[name]
    except KeyError:
        raise KeyError(f"unknown formula {name!r}; registered: {sorted(FORMULAS)}") from None


# --------------------------------------------------------------------------- #
# RUSLE
# --------------------------------------------------------------------------- #


#: Wischmeier & Smith (1978) is only defined for slopes above roughly 3
#: degrees. Below that its denominator approaches zero and the relation becomes
#: non-monotonic. See :func:`ls_factor` for why it is not the reference here.
LS_LOW_SLOPE_LIMIT_DEG = 3.0


def ls_factor(slope_deg: float) -> float:
    """RUSLE length-slope factor — Foster & Nearing (Nearing et al. 1999).

        LS = 65.41 * sin(b)^2 + 4.56 * sin(b) + 0.065

    Monotonic over the whole 0-90 degree range, which is the property that
    matters: a steeper slope must never reduce erosion.

    Why not Wischmeier & Smith (1978),
    ``(9.8 sin(b) + 0.03) / (16.8 sin(b) - 0.50)``, which FAO's ``RUSLELE``
    uses: that form is only valid for steep, long slopes. Below about 3
    degrees its denominator collapses and the relation becomes non-monotonic,
    peaking near 2 degrees and then *decreasing* with slope. It is also
    irreconcilable with Foster/Nearing — the two disagree by about 3.7x at
    3 degrees — so the two cannot be spliced into a piecewise function
    without introducing a discontinuity larger than the disagreement it
    claims to resolve. It is kept as
    :func:`ls_factor_wischmeier_smith` for callers that specifically need it.

    The four displaced implementations in the tree were: this same
    Foster/Nearing form applied correctly, a polynomial in slope *percent* with
    no angular term at all, and two more.

    Args:
        slope_deg: Slope in **degrees**.
    """
    if slope_deg < 0:
        raise ValueError(f"slope_deg must be >= 0, got {slope_deg}")
    sin_b = math.sin(math.radians(slope_deg))
    return 65.41 * sin_b**2 + 4.56 * sin_b + 0.065


def ls_factor_wischmeier_smith(slope_deg: float) -> float:
    """Wischmeier & Smith (1978) LS, for steep long slopes only.

    Valid above roughly ``LS_LOW_SLOPE_LIMIT_DEG``. Below that the denominator
    goes non-positive and this raises rather than returning a negative factor.
    Prefer :func:`ls_factor` unless reproducing a specific FAO RUSLELE run.
    """
    sin_b = math.sin(math.radians(slope_deg))
    denominator = 16.8 * sin_b - 0.50
    if denominator <= 0:
        raise ValueError(
            f"the Wischmeier & Smith form is undefined at {slope_deg} deg "
            f"(valid above ~{LS_LOW_SLOPE_LIMIT_DEG} deg); use ls_factor()"
        )
    return (9.8 * sin_b + 0.03) / denominator


def k_factor_williams(
    sand_pct: float,
    silt_pct: float,
    clay_pct: float,
    soc_g_per_kg: float,
) -> float:
    """RUSLE erodibility factor K, Williams et al. (1995) multiplicative form.

    .. warning::
       This is **not** the same equation as :func:`k_factor_epic`. The two
       disagree by a factor of about **6.8** for a loam (clay 30, silt 40,
       SOC 15 g/kg): Williams gives 0.0433, Renard gives 0.2952.

       Which one is live matters. The point chain
       (``chain_runner.rusle_point`` -> ``soilgrids.rusle_k_factor``) uses
       **Williams**, while the three migrated raster sites use **Renard**.
       Nothing in the tree compares the two, so the two never had to agree.

    Registered separately rather than standardised on one, because
    standardising would move published numbers: switching the point chain to
    Renard takes a reference site from 53.7 to 365.9 t/ha/yr, which
    ``rusle_point``'s 60 t/ha/yr ceiling would then truncate for humid sites.

    Args:
        sand_pct: Sand content, percent.
        silt_pct: Silt content, percent.
        clay_pct: Clay content, percent.
        soc_g_per_kg: Soil organic carbon, grams per kilogram.
    """
    total = silt_pct + clay_pct
    if total <= 0:
        raise ValueError("silt_pct + clay_pct must be positive")
    for label, value in (("sand_pct", sand_pct), ("silt_pct", silt_pct), ("clay_pct", clay_pct)):
        if not 0 <= value <= 100:
            raise ValueError(f"{label} must be 0..100, got {value}")

    c = soc_g_per_kg / 1000.0
    sn = 1.0 - sand_pct / 100.0
    k = (
        0.1317
        * (0.2 + 0.3 * math.exp(-0.0256 * sand_pct * (1.0 - silt_pct / 100.0)))
        * (silt_pct / total) ** 0.3
        * (1.0 - 0.25 * c / (c + math.exp(3.72 - 2.95 * c)))
        * (1.0 - 0.7 * sn / (sn + math.exp(-5.51 + 22.9 * sn)))
    )
    return min(max(k, K_BOUNDS_WILLIAMS[0]), K_BOUNDS_WILLIAMS[1])


def k_factor_epic(soc_g_per_kg: float, clay_pct: float, silt_pct: float) -> float:
    """RUSLE erodibility factor K, Renard et al. (1997) additive polynomial.

    .. warning::
       This is the **Renard additive polynomial**, not the Williams (1995)
       multiplicative four-term form that ``services/satellite/soilgrids.py``
       also labels "EPIC". The two equations disagree by about 6.8x for a
       loam — measured, not estimated — so a K from here is not comparable to
       one from there. Both are registered, separately and with citations, so
       neither is silently standardised over the other.

    Args:
        soc_g_per_kg: Soil organic carbon, grams per kilogram (NOT percent).
        clay_pct: Clay content, percent.
        silt_pct: Silt content, percent.
    """
    if not 0 <= clay_pct <= 100:
        raise ValueError(f"clay_pct must be 0..100, got {clay_pct}")
    if not 0 <= silt_pct <= 100:
        raise ValueError(f"silt_pct must be 0..100, got {silt_pct}")
    if soc_g_per_kg < 0:
        raise ValueError(f"soc_g_per_kg must be >= 0, got {soc_g_per_kg}")

    # Renard et al. express SOC as a percent of surface-layer mass.
    # 1 % organic carbon == 10 g/kg, so the conversion is a single divide.
    soc_pct = soc_g_per_kg / 10.0
    k = (
        0.2
        + 0.3 * (soc_pct / 100.0) ** 2
        + 0.3 * (1 - soc_pct / 100.0) ** 2
        + 0.025 * (clay_pct + silt_pct)
    ) * 0.1317
    return min(max(k, K_BOUNDS[0]), K_BOUNDS[1])


def r_factor(annual_precip_mm: float) -> float:
    """Rainfall erosivity R, Fournier approximation (FAO).

        R = 0.0534 * P^2, where P is mean annual precipitation in mm.

    Result unit is MJ·mm/(ha·yr), which is what this relation produces — for
    P = 1000 mm/yr it yields 53,400. No upper clamp is applied: a bound tight
    enough to be plausible (the order of 100-300 MJ/(ha·yr) quoted for humid
    climates) would reject the relation's own output, and silently clipping a
    computed physical quantity is the failure mode S-HONEST exists to prevent.
    """
    if annual_precip_mm < 0:
        raise ValueError(f"annual_precip_mm must be >= 0, got {annual_precip_mm}")
    return 0.0534 * annual_precip_mm**2


def erosion_class(soil_loss_t_ha_year: float) -> str:
    """Classify annual soil loss.

    Thresholds follow the FAO scheme used across the tree:
    ``<5`` negligible, ``<12`` low, ``<25`` moderate, ``<50`` high, else very high.
    The discarded ``chain_runner`` variant used 5/10/20, so the same field was
    classified differently depending on which pipeline produced it.
    """
    value = float(soil_loss_t_ha_year)
    if value < 5:
        return "negligible"
    if value < 12:
        return "low"
    if value < 25:
        return "moderate"
    if value < 50:
        return "high"
    return "very_high"


# --------------------------------------------------------------------------- #
# SCS curve number
# --------------------------------------------------------------------------- #


def runoff_scs(precip_mm: float, curve_number: float) -> float:
    """SCS-CN direct runoff, in mm.

    S  = 25400 / CN - 254      (retention depth, mm)
    Ia = 0.2 * S               (initial abstraction, mm)
    Q  = (P - Ia)^2 / (P + 0.8 * S)   for P > Ia, else 0
    """
    if not 30 <= curve_number <= 100:
        raise ValueError(f"curve_number must be 30..100, got {curve_number}")
    if precip_mm < 0:
        raise ValueError(f"precip_mm must be >= 0, got {precip_mm}")
    retention = 25400.0 / curve_number - 254.0
    initial_abstraction = 0.2 * retention
    if precip_mm <= initial_abstraction:
        return 0.0
    return (precip_mm - initial_abstraction) ** 2 / (precip_mm + 0.8 * retention)


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

register(
    "rusle.ls",
    ls_factor,
    reference=(
        "Wischmeier & Smith 1978 (FAO RUSLELE) for slope >= 3 deg; "
        "Foster & Nearing 2005 below 3 deg"
    ),
    units="dimensionless",
    replaces=(
        "map_engine/pipelines/rusle.py:_ls_factor (Foster/Nearing at all slopes)",
        "scientific_motors/chain_runner.py:144 (polynomial in slope percent)",
        "services/models/land_models.py:erosion_usle",
        "api_gateway/routers/elevation.py:245",
        "services/scientific_motors/land_capability.py:_slope",
    ),
)

register(
    "rusle.k.renard1997",
    k_factor_epic,
    reference=(
        "Renard et al. 1997, additive polynomial. Used by the migrated raster "
        "sites (map_engine/fetchers/soil_fetcher, api_gateway/routers/elevation, "
        "simulation/adapters/erosion_adapter)."
    ),
    units="t·ha·yr·mm",
    replaces=(
        "map_engine/fetchers/soil_fetcher.py:_compute_k_epic (mis-registered as EPIC)",
        "simulation/adapters/erosion_adapter.py:118 (out-of-range lookup)",
        "api_gateway/routers/elevation.py:205 (texture-string match, no citation)",
    ),
)

register(
    "rusle.k.williams1995",
    k_factor_williams,
    reference=(
        "Williams et al. 1995, multiplicative four-term form. THIS IS THE ONE THE "
        "POINT CHAIN USES: soilgrids.rusle_k_factor -> chain_runner.rusle_point -> "
        "soil_loss_ton_ha_yr. Registered explicitly because standardising on Renard "
        "would move a reference site from 53.7 to 365.9 t/ha/yr and hit rusle_point's "
        "60 t/ha/yr ceiling."
    ),
    units="t·ha·yr·mm",
    replaces=("services/satellite/soilgrids.py:rusle_k_factor (now documented, not replaced)",),
)

register(
    "rusle.r",
    r_factor,
    reference="Fournier 1961, as used by FAO",
    units="MJ·mm/(ha·yr)",
    replaces=("map_engine/pipelines/rusle.py:_r_factor",),
)

register(
    "scs.runoff",
    runoff_scs,
    reference="USDA-SCS National Engineering Handbook, TR-55",
    units="mm",
    replaces=("map_engine/pipelines/runoff.py:_runoff",),
)

register(
    "rusle.erosion_class",
    erosion_class,
    reference="FAO soil-loss classification",
    units="t/(ha·yr)",
    replaces=("scientific_motors/chain_runner.py:150 (5/10/20 thresholds)",),
)
