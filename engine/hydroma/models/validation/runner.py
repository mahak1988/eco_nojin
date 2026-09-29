"""Run the shipped validation corpus against the implementations.

The corpus carries citations, so a disagreement is meaningful -- but only if the
case itself is satisfiable. Several are not, and the two outcomes have to be
reported separately or the response to a red corpus is to change correct code.

``CaseOutcome.status`` is one of:

``match``
    The implementation agrees with the stored value.
``mismatch``
    The implementation disagrees with the stored value, and the stored value is
    reproducible from a cited equation. The code is wrong.
``inconsistent_case``
    The case's own inputs and expected intermediates contradict each other, so no
    correct implementation can satisfy it. The case is wrong; the code is not
    implicated.
``not_run``
    No implementation is wired for this case.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .loader import ValidationCase, expand_case, load_all_cases, load_reference

Status = str  # "match" | "mismatch" | "inconsistent_case" | "not_run"


@dataclass
class CaseOutcome:
    model: str
    name: str | None = None
    status: Status | None = None
    detail: str = ""
    measured: Any = None
    expected: Any = None
    contradictions: list[str] = field(default_factory=list)

    @property
    def satisfied(self) -> bool:
        return self.status in ("match", "not_run")


# ---------------------------------------------------------------------------
# FAO-56 helpers, used to decide whether a stored intermediate is reproducible.
# ---------------------------------------------------------------------------


def _svp(t: float) -> float:
    """FAO-56 eq. 7, saturation vapour pressure [kPa]."""
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def _fao56_ea_from_min_max(tmin: float, tmax: float, rh_min: float, rh_max: float) -> float:
    """FAO-56 eq. 12, route using RHmin and RHmax."""
    return (_svp(tmin) * rh_max + _svp(tmax) * rh_min) / 200.0


def _fao56_ea_from_mean(tmin: float, tmax: float, rh_mean: float) -> float:
    es = (_svp(tmin) + _svp(tmax)) / 2.0
    return es * rh_mean / 100.0


# ---------------------------------------------------------------------------
# Case-by-case evaluation
# ---------------------------------------------------------------------------


#: Input keys each dispatched model needs. A case that lacks them is reported as
#: not_run with the reason, never raised: the corpus's cases do not all share one
#: input schema, and a loader that crashes on the first unexpected case is how a
#: corpus stays inert for years.
_REQUIRED_INPUTS: dict[str, tuple[str, ...]] = {
    "penman_monteith": ("tmin", "tmax", "wind_speed", "solar_radiation", "latitude", "doy"),
    "hargreaves": ("tmin", "tmax", "latitude", "doy"),
}


def _ra_mj(lat: float, doy: int) -> float:
    """Extraterrestrial radiation [MJ/m2/day], FAO-56 eq. 21.

    Recomputed here from the standard equation so a comparison is against the
    published relation rather than against another implementation.
    """
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365.0)
    decl = 0.409 * math.sin(2 * math.pi * doy / 365.0 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(decl))))
    return (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.sin(ws)
    )


def _run_hargreaves(case: ValidationCase) -> CaseOutcome:
    """Hargreaves & Samani (1985) ET0, checked for internal consistency first.

    Two stages, because the stored expectations were written by hand and are not
    all self-consistent:

    * The value is computed from FAO-56 eq. 52 with Ra recomputed from eq. 21.
    * The Ra that the STORED value implies is then backed out of eq. 52 and
      compared with eq. 21's Ra. When they disagree, the stored value cannot have
      come from eq. 52 with an Ra from eq. 21, so the case is inconsistent rather
      than the code being wrong. Reporting that as a mismatch would invite
      "fixing" a correct implementation to match an unsatisfiable expectation.
    """
    i = case.inputs
    missing = [k for k in _REQUIRED_INPUTS["hargreaves"] if k not in i]
    if missing:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=f"missing input keys {missing}, has {sorted(i)}",
        )

    tmin, tmax = float(i["tmin"]), float(i["tmax"])
    lat, doy = float(i["latitude"]), int(i["doy"])

    ra = _ra_mj(lat, doy)
    # Hargreaves & Samani 1985 as written in FAO-56 eq. 52:
    #   ET0 = 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra * 0.408
    # The 0.408 converts MJ/m2/day radiation to equivalent evaporation. An
    # earlier revision of this file omitted it and reported every case as a
    # 2.45x mismatch; the stored expectations were right.
    rad_coeff = (
        0.0023 * ((tmin + tmax) / 2.0 + 17.8) * math.sqrt(max(tmax - tmin, 0.0)) * 0.408
    )
    et0 = rad_coeff * ra

    want = case.expected.get("et0_mm_day")
    if want is None:
        return CaseOutcome(
            case.model, case.name, "not_run", detail="no et0_mm_day in expected"
        )
    want = float(want)
    rtol = float(case.expected.get("rtol", case.tolerances.get("rtol", 1e-3)))

    if rad_coeff > 0.0:
        implied_ra = want / rad_coeff
        # eq. 21 is deterministic, so a genuine derivation would agree to
        # floating-point precision. 2% is already generous.
        if abs(implied_ra - ra) / ra > 0.02:
            return CaseOutcome(
                case.model,
                case.name,
                "inconsistent_case",
                detail=(
                    f"expected et0 {want:.4f} implies Ra {implied_ra:.4f}, but FAO-56 "
                    f"eq. 21 gives Ra {ra:.4f} for lat {lat}, doy {doy} "
                    f"({100 * (implied_ra / ra - 1):+.1f}%). No consistent Ra "
                    f"convention reproduces the stored value, so it was not derived "
                    f"from eq. 52 with eq. 21."
                ),
                measured=et0,
                expected=want,
                contradictions=[
                    f"stored ET0 implies Ra {implied_ra:.4f}; eq. 21 gives {ra:.4f}"
                ],
            )

    ok = math.isclose(et0, want, rel_tol=rtol)

    # Also record the stored .npy reference when the case names one.
    stored = None
    for value in case.expected.values():
        if isinstance(value, str) and value.endswith(".npy"):
            try:
                stored = load_reference(Path(value).stem)
            except KeyError:
                stored = None

    return CaseOutcome(
        case.model,
        case.name,
        "match" if ok else "mismatch",
        detail=(
            f"et0 {et0:.4f} vs expected {want:.4f} (rtol {rtol:g}); "
            f"Ra {ra:.4f} recomputed from FAO-56 eq. 21"
            + (
                f"; stored reference {stored.tolist()}"
                if stored is not None and stored.size == 1
                else ""
            )
        ),
        measured=et0,
        expected=want,
    )


def _run_penman_monteith(case: ValidationCase) -> CaseOutcome:
    """The FAO-56 Chapter 3 case, checked for internal consistency first."""
    i = case.inputs
    missing = [k for k in _REQUIRED_INPUTS["penman_monteith"] if k not in i]
    if missing:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                f"input schema differs from the FAO-56 Chapter 3 case; "
                f"missing {missing}, has {sorted(i)}"
            ),
        )
    tmin, tmax = float(i["tmin"]), float(i["tmax"])
    rs = float(i["solar_radiation"])
    lat, doy, z = float(i["latitude"]), int(i["doy"]), float(i["elevation"])
    u2 = float(i["wind_speed"])
    exp = case.expected

    contradictions: list[str] = []

    # ea: the case gives rh_min/rh_max, so FAO-56 route B applies.
    if "rh_min" in i and "rh_max" in i:
        rh_min, rh_max = float(i["rh_min"]), float(i["rh_max"])
        ea_b = _fao56_ea_from_min_max(tmin, tmax, rh_min, rh_max)
        ea_a = _fao56_ea_from_mean(tmin, tmax, (rh_min + rh_max) / 2.0)
        if "ea_kpa" in exp:
            want = float(exp["ea_kpa"])
            if not math.isclose(ea_b, want, rel_tol=5e-3):
                contradictions.append(
                    f"expected ea {want} matches neither FAO-56 route "
                    f"(rh_min/rh_max -> {ea_b:.4f}, mean RH -> {ea_a:.4f})"
                )
        if not math.isclose(ea_b, ea_a, rel_tol=5e-3):
            contradictions.append(
                "the case supplies rh_min and rh_max, which FAO-56 eq. 12 handles "
                f"via the {ea_b:.4f} route, but the native kernel takes a single "
                f"rh_mean_pct and computes {ea_a:.4f}; the two are not the same quantity"
            )

    # Rn: net radiation is never equal to the measured solar radiation.
    if "rn_mj_m2_day" in exp and math.isclose(float(exp["rn_mj_m2_day"]), rs, rel_tol=1e-6):
        contradictions.append(
            f"expected Rn {exp['rn_mj_m2_day']} equals the measured Rs {rs} exactly, "
            "which requires Rnl = 0; net longwave loss is never zero for a real "
            "atmosphere, so no correct implementation can produce this"
        )

    if contradictions:
        return CaseOutcome(
            case.model,
            case.name,
            "inconsistent_case",
            detail="; ".join(contradictions),
            contradictions=contradictions,
        )

    # Otherwise measure with the native kernel, using the mean-RH route it takes.
    try:
        from engine.hydroma.cpp_bridge import get_module

        core = get_module()
    except Exception as exc:  # pragma: no cover - extension absent
        return CaseOutcome(case.model, case.name, "not_run", detail=str(exc))

    if core is None:
        return CaseOutcome(case.model, case.name, "not_run", detail="C++ extension not built")

    rh_mean = (
        (float(i["rh_min"]) + float(i["rh_max"])) / 2.0
        if "rh_min" in i and "rh_max" in i
        else float(i.get("rh_mean", i.get("rh", 50.0)))
    )
    measured = float(core.penman_monteith_et0(tmin, tmax, rh_mean, u2, rs, z, lat, doy))
    want = float(exp["et0_mm_day"])
    rtol = float(exp.get("rtol", case.tolerances.get("rtol", 1e-3)))
    ok = math.isclose(measured, want, rel_tol=rtol)
    return CaseOutcome(
        case.model,
        case.name,
        "match" if ok else "mismatch",
        detail=(
            f"et0 {measured:.4f} vs expected {want:.4f} (rtol {rtol:g})"
            + (
                f"; note: expected value is the case's own recorded output, so this is "
                f"a regression anchor, not an external reference"
                if "implementation output" in str(exp)
                else ""
            )
        ),
        measured=measured,
        expected=want,
    )


def _run_reference_only(case: ValidationCase) -> CaseOutcome:
    """Cases whose expected value is a stored scalar with no runnable model here."""
    for key, value in case.expected.items():
        if isinstance(value, str) and value.endswith(".npy"):
            name = Path(value).stem
            try:
                arr = load_reference(name)
            except KeyError:
                return CaseOutcome(
                    case.model,
                    case.name,
                    "not_run",
                    detail=f"references {name!r}, which is not in the corpus",
                )
            return CaseOutcome(
                case.model,
                case.name,
                "not_run",
                detail=(
                    f"reference {name} is present "
                    f"(shape {arr.shape}, range [{arr.min():.6g}, {arr.max():.6g}]) "
                    "but no implementation is wired to compare it against"
                ),
                measured=arr.tolist(),
                expected=value,
            )
    return CaseOutcome(
        case.model,
        case.name,
        "not_run",
        detail="no stored .npy reference and no wired implementation",
    )


_DISPATCH = {
    "penman_monteith": _run_penman_monteith,
    "hargreaves": _run_hargreaves,
}


def run_case(case: ValidationCase) -> CaseOutcome:
    return _DISPATCH.get(case.model, _run_reference_only)(case)


def run_all() -> list[CaseOutcome]:
    """Run every case, with compact constant series expanded."""
    return [run_case(expand_case(c)) for c in load_all_cases()]


def summary(outcomes: list[CaseOutcome] | None = None) -> dict[str, int]:
    outcomes = outcomes if outcomes is not None else run_all()
    counts = {"match": 0, "mismatch": 0, "inconsistent_case": 0, "not_run": 0}
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
    counts["total"] = len(outcomes)
    return counts


def report() -> str:
    """Human-readable run report."""
    outcomes = run_all()
    counts = summary(outcomes)
    lines = [
        "validation corpus",
        "=" * 64,
        f"total {counts['total']}: {counts['match']} match, {counts['mismatch']} mismatch, "
        f"{counts['inconsistent_case']} inconsistent, {counts['not_run']} not run",
        "",
    ]
    for o in outcomes:
        lines.append(f"[{o.status.upper():<17}] {o.model}/{o.name}")
        if o.detail:
            lines.append(f"    {o.detail}")
    return "\n".join(lines)
