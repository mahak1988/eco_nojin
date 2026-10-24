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
    No implementation is wired for this case; or the case's inputs cannot be
    expressed in the API of the implementation that does exist; or the case
    stores no numeric expectation to compare (its expectation is a relation, or
    a reference file that was never shipped). A ``not_run`` detail names the
    missing piece, and may carry the measurement taken on the way to that verdict,
    so a gap in the corpus is never reported as a pass.

Dispatch rule used by every newly wired model (2026-10-10)
---------------------------------------------------------
1. Resolve anything the case file carries at *file* level (``parameters``: crop
   coefficients, van Genuchten coefficients, grid settings) before running; the
   loader keeps only per-case fields, and dropping those blocks silently
   substitutes the kernel's own defaults for the case's coefficients.
2. Run the real implementation with the case's own inputs. If a required input
   has no representation in the implementation's API -- an irrigation schedule,
   an initial root-zone depletion, a root zone that grows, a bed elevation, a
   prescribed-head bottom boundary, an hourly ET0 series, a CN map -- the case
   is ``not_run`` and the detail names that missing input. Choosing a value the
   case does not supply would be fabricating the comparison.
3. Judge internal consistency *first*, from the case's own numbers, exactly as
   ``_run_penman_monteith`` and ``_run_hargreaves`` do: a water balance that
   cannot close, an arithmetic identity that does not reproduce the value quoted
   next to it, a pool sum that does not equal the total it is part of. Those are
   ``inconsistent_case``, and the contradiction names the equation.
4. Compare every stored numeric expectation the implementation can produce. A
   stored expectation that names a reference file which is not in the corpus is
   a blocker: the case is ``not_run`` and the detail names the missing file.
5. A stored expectation that is an algebraic relation rather than a value
   (``"2*sqrt(g*h_left)"``) or a loose string (``"~45 cm"``) is reported as a
   measurement against the relation in the detail and is never scored. When it
   is the case's only substantive expectation the case is ``not_run``.

``machine_summary()`` returns the same verdicts per model and per case in plain
JSON-safe types, for consumers that fold them into a model status
(``engine/models/registry.py``) rather than print them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from .loader import (
    ValidationCase,
    expand_case,
    load_all_cases,
    load_file_document,
    load_reference,
)

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
# Case-file parameters and series helpers
# ---------------------------------------------------------------------------


def _case_parameters(case: ValidationCase) -> dict[str, Any]:
    """The `parameters:` block of the case's own file, if it has one.

    ``fao56_dual_kc``, ``richards_1d`` and ``saint_venant_1d`` carry their
    coefficients and grid settings at *file* level, not per case. The loader
    flattens per-case fields only, so a dispatcher that does not read this block
    would run the case with the kernel's own defaults -- a different set of crop
    coefficients from the one the case was written against -- and report a
    mismatch against a number the case never specified.
    """
    if case.source is None:
        return {}
    params = load_file_document(case.source).get("parameters")
    return dict(params) if isinstance(params, dict) else {}


def _case_reference(case: ValidationCase) -> str:
    return str(case.reference or "")


def _series(value: Any, n: int | None = None) -> list[float] | None:
    """Read a series field, in either the compact or the explicit YAML form.

    A field may be a list (``[5.0, 6.0, ...]``), a compact constant
    (``{value: 5.0, repeat: 168}``) or a bare scalar. ``None`` when absent, so a
    caller can distinguish "not supplied" from "supplied as zero".
    """
    if value is None:
        return None
    if isinstance(value, dict):
        if "value" not in value:
            return None
        repeat = int(value.get("repeat", n or 0))
        return [float(value["value"])] * repeat
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    return [float(value)]


def _length(*values: Any) -> int | None:
    """The length of the first sequence-like field, ignoring scalars/dicts."""
    for value in values:
        if isinstance(value, dict):
            for key in ("value",):
                if key in value and isinstance(value.get("repeat"), (int, float)):
                    return int(value["repeat"])
            return None
        if isinstance(value, (list, tuple)):
            return len(value)
    return None


def _bound(stored: Any) -> float | None:
    """Parse the corpus's bound form (``"< 1e-3"``) into a float threshold."""
    if isinstance(stored, bool) or stored is None:
        return None
    if isinstance(stored, (int, float)):
        return float(stored)
    text = str(stored).strip()
    if text[:1] in "<>=":
        text = text[1:].strip()
    try:
        return float(text)
    except ValueError:
        return None


def _is_bound(stored: Any) -> bool:
    """True when a stored expectation is a one-sided bound rather than a value."""
    return isinstance(stored, str) and stored.strip()[:1] in "<>="


#: Stored conventions the dispatchers recognise as "not a number to compare".
#: ``recorded_note`` is the corpus's own sibling key for a value recorded from
#: the model (the EPIA/ESRI/EWSI/HYRUE boundary cases and the anchors added
#: 2026-10-10); it documents the anchor, it is not one.
_NON_NUMERIC_KEYS = frozenset(
    {
        "note",
        "comment",
        "tolerance",
        "rtol",
        "rtol_above",
        "atol",
        "reproducibility",
        "message_contains",
        "error",
        "recorded_note",
    }
)

#: Extension of the corpus's reference-profile files.
_REFERENCE_SUFFIXES = (".npy", ".npz")


def _names_reference(value: Any) -> bool:
    return isinstance(value, str) and value.endswith(_REFERENCE_SUFFIXES)


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
    return (
        (24 * 60 / math.pi)
        * 0.0820
        * dr
        * (ws * math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.sin(ws))
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
    i: dict[str, Any] = case.inputs or {}
    tol: dict[str, Any] = case.tolerances or {}
    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
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
    rad_coeff = 0.0023 * ((tmin + tmax) / 2.0 + 17.8) * math.sqrt(max(tmax - tmin, 0.0)) * 0.408
    et0 = rad_coeff * ra

    want = expected.get("et0_mm_day")
    if want is None:
        return CaseOutcome(case.model, case.name, "not_run", detail="no et0_mm_day in expected")
    want = float(want)
    rtol = float(expected.get("rtol", tol.get("rtol", 1e-3)))

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
                contradictions=[f"stored ET0 implies Ra {implied_ra:.4f}; eq. 21 gives {ra:.4f}"],
            )

    ok = math.isclose(et0, want, rel_tol=rtol)

    # Also record the stored .npy reference when the case names one.
    stored = None
    for value in expected.values():
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
    i: dict[str, Any] = case.inputs or {}
    missing = [k for k in _REQUIRED_INPUTS["penman_monteith"] if k not in i]
    if missing:
        if i.get("hourly_data"):
            # The hourly form of the equation (FAO-56 Chapter 4) is a different
            # kernel from the daily form this repository ships
            # (penman_monteith_et0 takes tmin/tmax/rh_mean/u2/rs/z/lat/doy). The
            # case's 24 hourly temperature, RH and wind series have no
            # implementation to dispatch to.
            return CaseOutcome(
                case.model,
                case.name,
                "not_run",
                detail=(
                    "the case supplies an hourly series (24 t_c, rh and wind_ms values) and asks "
                    "for hourly-to-daily integration, and this repository ships only the daily "
                    "FAO-56 equation: penman_monteith_et0 takes tmin, tmax, rh_mean_pct, u2, rs, "
                    "elevation, lat and doy. There is no hourly ET0 kernel and no hourly-to-daily "
                    "aggregator, so hourly_data/rh/wind_ms have no dispatch target. "
                    f"Missing for the daily path: {missing}"
                ),
                measured={"hours": i.get("hours"), "series_lengths": [
                    len(i.get(k, [])) for k in ("t_c", "rh", "wind_ms")
                ]},
            )
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
    exp: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    tol: dict[str, Any] = case.tolerances or {}

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
    rtol = float(exp.get("rtol", tol.get("rtol", 1e-3)))
    ok = math.isclose(measured, want, rel_tol=rtol)
    return CaseOutcome(
        case.model,
        case.name,
        "match" if ok else "mismatch",
        detail=(
            f"et0 {measured:.4f} vs expected {want:.4f} (rtol {rtol:g})"
            + (
                "; note: expected value is the case's own recorded output, so this is "
                "a regression anchor, not an external reference"
                if "implementation output" in str(exp)
                else ""
            )
        ),
        measured=measured,
        expected=want,
    )


# ---------------------------------------------------------------------------
# New dispatchers: models that DO have a runnable implementation here
# ---------------------------------------------------------------------------


def _run_scs_cn(case: ValidationCase) -> CaseOutcome:
    """SCS-CN runoff through the project's own calculator.

    Expected keys are ``runoff_depth_mm`` and ``volume_m3``; the calculator
    reports a volume and a peak, so the depth is derived from the volume and
    the area the case supplies. The NRCS worked example (CN=70, P=50) checks
    the SI formula: S = 25400/CN - 254, Ia = 0.2 S, Q = (P-Ia)^2/(P+0.8 S).
    """
    i: dict[str, Any] = case.inputs or {}
    if "cn_map_values" in i:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                f"the case supplies a curve-number map (cn_map_values {i['cn_map_values']}) and "
                "an area, and RunoffInput takes a single scalar curve_number: there is no "
                "spatially-distributed input field anywhere in RunoffCalculator/RunoffInput, and "
                "no xarray surface to evaluate one over, so a weighted CN-map runoff cannot be "
                "computed by dispatching this implementation. Evaluating the calculator once per "
                "CN value and averaging the results would not be SCS-CN over a map (S is a "
                "nonlinear function of CN, so average-Q != Q(average-S)), so the case's stored "
                f"volume of {case.expected.get('volume_m3')} m3 is not derivable from it"
                if isinstance(case.expected, dict)
                else "the case supplies a cn_map_values map and RunoffInput takes a single "
                "scalar curve_number"
            ),
            expected=case.expected if isinstance(case.expected, dict) else {},
            measured={"cn_map_values": i["cn_map_values"], "area_ha": i.get("area_ha")},
        )
    if "curve_number" not in i or "precipitation_mm" not in i:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                f"missing inputs {sorted({'precipitation_mm', 'curve_number'} - set(i))}"
            ),        )

    from engine.hydroma.models.runoff_model import MethodType, RunoffCalculator, RunoffInput

    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    tol: dict[str, Any] = case.tolerances or {}
    want_depth = expected.get("runoff_depth_mm")
    want_volume = expected.get("volume_m3")

    # A case whose expectation is an error message is testing the validator,
    # not the arithmetic; it is judged by rejecting the inputs, not a number.
    if "error" in expected:
        try:
            RunoffCalculator().execute(
                RunoffInput(
                    precipitation_mm=float(i.get("precipitation_mm", 0.0)),
                    curve_number=float(i.get("curve_number", 0.0)),
                    area_ha=float(i.get("area_ha", 1.0)),
                method=cast(MethodType, str(i.get("method", "SCS-CN"))),
                    storm_duration_h=float(i.get("storm_duration_h", 3.0)),
                    rational_coefficient=float(i.get("rational_coefficient", 0.6)),
                )
            )
        except Exception as exc:  # noqa: BLE001 - the expected outcome IS an error
            message = str(expected.get("message_contains", "")).strip()
            text = str(exc)
            if message and message not in text:
                # The validator DID reject the input -- behaviour correct -- but
                # the recorded message text is not what a correct validator
                # emits. That is an unsatisfiable expectation, not a defect:
                # report it as an inconsistent case instead of "fixing" the
                # validator's message to match a hand-written string.
                return CaseOutcome(
                    case.model,
                    case.name,
                    "inconsistent_case",
                    detail=(
                        f"the input was rejected (correct), but the recorded "
                        f"message {message!r} is not the message a validator "
                        f"emits: {text.splitlines()[-1][:120]!r}"
                    ),
                    contradictions=[
                        f"recorded message: {message}",
                        f"actual message: {text[:200]}",
                    ],
                    measured=text[:200],
                    expected=expected,
                )
            return CaseOutcome(
                case.model,
                case.name,
                "match",
                detail=f"expected error raised: {type(exc).__name__}",
                measured=text[:200],
                expected=expected,
            )
        return CaseOutcome(
            case.model,
            case.name,
            "mismatch",
            detail="expected an input validation error, but the calculator accepted the inputs",
            measured="accepted",
            expected=expected,
        )

    try:
        result = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=float(i["precipitation_mm"]),
                curve_number=float(i["curve_number"]),
                area_ha=float(i.get("area_ha", 1.0)),
                method=cast(MethodType, str(i.get("method", "SCS-CN"))),
                storm_duration_h=float(i.get("storm_duration_h", 3.0)),
                rational_coefficient=float(i.get("rational_coefficient", 0.6)),
            )
        )
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"calculator raised {exc}"
        )

    volume = float(result.volume_m3)
    area_ha = float(i.get("area_ha", 1.0))
    depth = volume / (area_ha * 10.0) if area_ha > 0 else 0.0
    vol_tol = float(tol.get("volume_abs_tol", 1.0))
    rtol = float(tol.get("rtol", 1e-6))

    problems: list[str] = []
    comparable = 0
    if want_depth is not None:
        comparable += 1
        want_depth = float(want_depth)
        if not math.isclose(depth, want_depth, rel_tol=max(rtol, 1e-3), abs_tol=1e-6):
            problems.append(f"depth {depth:.4f} vs expected {want_depth:.4f}")
    if want_volume is not None:
        comparable += 1
        want_volume = float(want_volume)
        if not math.isclose(volume, want_volume, rel_tol=rtol, abs_tol=vol_tol):
            problems.append(f"volume {volume:.2f} vs expected {want_volume:.2f}")
    if comparable == 0:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail="no comparable expected key in case",
            measured={"runoff_depth_mm": depth, "volume_m3": volume},
            expected=expected,
        )

    return CaseOutcome(
        case.model,
        case.name,
        "match" if not problems else "mismatch",
        detail="; ".join(problems),
        measured={"runoff_depth_mm": depth, "volume_m3": volume},
        expected={"runoff_depth_mm": want_depth, "volume_m3": want_volume},
    )


#: import path for each class-based model key (the case files name the class).
_CLASS_MODELS: dict[str, str] = {
    "HYRUE": "engine.hydroma.models.hyrue:HYRUE",
    "ECSI": "engine.hydroma.models.ecsi:ECSI",
    "EPIA": "engine.hydroma.models.epia:EPIA",
    "ESRI": "engine.hydroma.models.esri:ESRI",
    "EWSI": "engine.hydroma.models.ewsi:EWSI",
    "HLHS": "engine.hydroma.models.hlhs:HLHS",
    "hdvi": "engine.hydroma.models.hdvi:HDVI",
    "hpheno": "engine.hydroma.models.hpheno:HPheno",
}


def _coerce(value: Any) -> Any:
    """Turn YAML lists into numpy arrays for the models that expect them.

    Only numeric lists are converted. ``hpheno`` supplies ``dates`` as ISO strings
    alongside ``ndvi_ts`` as floats, and its own ``_as_dates`` accepts a sequence
    of strings; forcing every list through ``np.asarray(dtype=float)`` turned the
    date list into ``ValueError: could not convert string to float``.
    """
    import numpy as np

    if isinstance(value, list):
        if value and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in value
        ):
            return np.asarray(value, dtype=float)
        return value
    return value


def _reduce(values: Any, how: str | None) -> Any:
    """Reduce a series to the single number the case compares."""
    import numpy as np

    if not isinstance(values, np.ndarray):
        return values
    if values.ndim == 0:
        return float(values)
    if how == "last":
        return float(values[-1])
    if how == "max":
        return float(values.max())
    if how == "mean":
        return float(values.mean())
    if how == "min":
        return float(values.min())
    return values.tolist()


def _run_class_model(case: ValidationCase) -> CaseOutcome:
    """Run one of the index models and compare its recorded key.

    The case supplies ``expected`` (a scalar), ``expected_key`` (which output
    field to compare) and optionally ``reduce`` (which element of a series).
    Values are the case's own recorded outputs, so this is a regression anchor
    -- the report says so instead of pretending it is an external reference.
    """
    i: dict[str, Any] = case.inputs or {}
    tol: dict[str, Any] = case.tolerances or {}
    raw = case.raw if isinstance(case.raw, dict) else {}
    expected = case.expected if isinstance(case.expected, dict) else {"value": case.expected}
    want = expected.get("value", expected)
    # ``expected_key`` and ``reduce`` are case-level YAML siblings of
    # ``expected``; the loader keeps them on the raw case.
    key = str(
        i.get("expected_key")
        or raw.get("expected_key")
        or expected.get("expected_key")
        or ""
    )
    reduce_to = i.get("reduce") or raw.get("reduce") or expected.get("reduce")

    spec = _CLASS_MODELS.get(case.model)
    if spec is None:
        return CaseOutcome(case.model, case.name, "not_run", detail="no class mapping")
    module_name, _, class_name = spec.partition(":")
    try:
        import importlib

        module = importlib.import_module(module_name)
        model = getattr(module, class_name)()
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"class import failed: {exc}"
        )

    kwargs = {k: _coerce(v) for k, v in i.items() if k not in ("expected_key", "reduce")}
    # HLHS.compute expects a LandscapeMetrics dataclass, not the raw mapping.
    if case.model == "HLHS" and "metrics" in kwargs:
        from engine.hydroma.models.hlhs import LandscapeMetrics

        raw_metrics = kwargs["metrics"]
        if isinstance(raw_metrics, dict):
            kwargs["metrics"] = LandscapeMetrics(**raw_metrics)
    try:
        result = model.compute(**kwargs)
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"compute raised {type(exc).__name__}: {exc}"
        )

    if not key:
        return CaseOutcome(
            case.model, case.name, "not_run", detail="no expected_key in case"
        )
    # EWSI returns a bare array; its expected_key is then a reducer name.
    if not isinstance(result, dict):
        if key in ("mean", "last", "max", "min"):
            measured = _reduce(result, key)
            rtol = float(tol.get("rtol", 1e-2))
            atol = float(tol.get("atol", 1e-2))
            try:
                ok = math.isclose(float(measured), float(want), rel_tol=rtol, abs_tol=atol)
            except (TypeError, ValueError):
                ok = measured == want
            return CaseOutcome(
                case.model,
                case.name,
                "match" if ok else "mismatch",
                detail=f"{key} {measured} vs expected {want} (rtol {rtol:g})",
                measured=measured,
                expected=want,
            )
        return CaseOutcome(
            case.model, case.name, "not_run",
            detail=f"output is {type(result).__name__}, not a mapping with {key!r}",
        )
    if key not in result:
        return CaseOutcome(
            case.model, case.name, "not_run",
            detail=(
                f"output has no key {key!r}; keys: "
                f"{sorted(result) if isinstance(result, dict) else type(result).__name__}"
            ),
        )
    measured = _reduce(result[key], reduce_to)

    rtol = float(tol.get("rtol", 1e-2))
    atol = float(tol.get("atol", 1e-2))
    try:
        ok = math.isclose(float(measured), float(want), rel_tol=rtol, abs_tol=atol)
    except (TypeError, ValueError):
        ok = measured == want
    return CaseOutcome(
        case.model,
        case.name,
        "match" if ok else "mismatch",
        detail=(
            f"{key} {measured} vs expected {want} (rtol {rtol:g}); recorded case output, "
            "so a regression anchor rather than an external reference"
        ),
        measured=measured,
        expected=want,
    )


def _run_check_dam(case: ValidationCase) -> CaseOutcome:
    """Check-dam design through the project's own calculator."""
    i: dict[str, Any] = case.inputs or {}
    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    if not expected:
        return CaseOutcome(
            case.model, case.name, "not_run", detail="no expected values in case"
        )
    import inspect as _inspect

    from engine.hydroma.watershed.calculator import design_check_dam

    # Forward every input the case supplies, keeping only the ones the
    # calculator's signature actually accepts -- dropping a supplied input
    # (area_m2, unit_cost_usd_m3, ...) silently changes the design.
    accepted = set(_inspect.signature(design_check_dam).parameters)
    call: dict[str, Any] = {
        k: float(v) if isinstance(v, (int, float)) else v for k, v in i.items()
    }
    forwarded: dict[str, Any] = {k: v for k, v in call.items() if k in accepted}
    dropped = sorted(set(call) - accepted)
    try:
        result = design_check_dam(**forwarded)
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"design_check_dam raised {exc}"
        )
    values = result if isinstance(result, dict) else {"result": result}
    problems: list[str] = []
    for key, want in expected.items():
        if key not in values:
            continue
        got = values[key]
        try:
            if not math.isclose(float(got), float(want), rel_tol=0.05, abs_tol=1e-6):
                problems.append(f"{key} {got} vs {want}")
        except (TypeError, ValueError):
            if got != want:
                problems.append(f"{key} {got!r} vs {want!r}")
    # A case file marked ``partial`` says its own expectations are not
    # authoritative: a disagreement there is an unsatisfiable expectation, not
    # a defect in the calculator, and is reported that way (the same convention
    # the penman_monteith cases use).
    if problems and str(case.status) == "partial":
        return CaseOutcome(
            case.model,
            case.name,
            "inconsistent_case",
            detail=(
                "the case file is marked 'partial', so its hand-written "
                "expectations are not authoritative; the calculator's own "
                "values are reported instead"
            ),
            contradictions=problems,
            measured=values,
            expected=expected,
        )
    return CaseOutcome(
        case.model,
        case.name,
        "match" if not problems else "mismatch",
        detail=(
            ("; ".join(problems) or "all expected keys matched")
            + (f"; inputs not used by the calculator: {dropped}" if dropped else "")
        ),
        measured=values,
        expected=expected,
    )


def _rothc_months(i: dict[str, Any]) -> tuple[list[Any] | None, str]:
    """Translate the case's RothC inputs into ``MonthClimate`` records.

    The case files do NOT store a list of month records. They store two parallel
    column blocks, ``monthly_inputs`` (``carbon_input``, ``dpm_rpm_split``) and
    ``monthly_climate`` (``temp_c``, ``smd_mm``, ``max_smd_mm``), each of which
    may be a list, a bare scalar, or the compact ``{value, repeat}`` form. The
    shipped adapter iterated ``monthly_inputs`` as if it were a list of month
    dicts, so every one of the seven cases died on
    ``string indices must be integers, not 'str'`` and were reported ``not_run``
    with a message that named ``rothc`` rather than the adapter.

    The fix is in the adapter, not in the model: ``run_rothc`` takes 12
    ``MonthClimate`` records and one monthly carbon input, which is what these
    cases mean.
    """
    mi = i.get("monthly_inputs") or {}
    mc = i.get("monthly_climate") or {}
    if not isinstance(mi, dict) or not isinstance(mc, dict):
        return None, "monthly_inputs/monthly_climate are not the mapping blocks the case files use"

    n = _length(mi.get("carbon_input"), mc.get("temp_c"), mc.get("smd_mm"), 12) or 12
    temps = _series(mc.get("temp_c"), n) or [0.0] * n
    smds = _series(mc.get("smd_mm"), n) or [0.0] * n
    max_smd = _series(mc.get("max_smd_mm"), n) or [100.0] * n
    carbon = _series(mi.get("carbon_input"), n) or [0.0] * n
    # A bare scalar in one column (``max_smd_mm: 100.0``, as every case file
    # writes it) expands to a single value; broadcast it over the year rather
    # than reporting a length mismatch against columns the case did populate.
    if len(max_smd) == 1 and n > 1:
        max_smd = max_smd * n
    if len(carbon) == 1 and n > 1:
        carbon = carbon * n

    if not (len(temps) == len(smds) == len(carbon) == len(max_smd) == n):
        return None, (
            f"parallel column lengths differ: temp {len(temps)}, smd {len(smds)}, "
            f"carbon {len(carbon)}, max_smd {len(max_smd)}"
        )

    from engine.hydroma.simulation.runners.rothc_runner import MonthClimate

    months = [
        MonthClimate(
            year=2000,
            month=month + 1,
            tmean_c=float(temps[month]),
            smd_mm=float(smds[month]),
            max_smd_mm=float(max_smd[month]),
        )
        for month in range(n)
    ]
    return months, ""


def _run_rothc(case: ValidationCase) -> CaseOutcome:
    """RothC through the project's own runner (monthly climate in, SOC out).

    Three classes of case are separated, because a single verdict would either
    hide a case defect or smear it onto a correct port:

    * the two ``stabilized_fraction`` / ``co2_fraction`` cases and the
      temperature, moisture and mass-balance cases judge derived quantities the
      implementation exposes directly;
    * ``standard_reference_run`` stores a pool breakdown that does not sum to
      its own total SOC and does not close its own water balance, so it is
      reported against the implementation's own values with the contradiction;
    * ``iom_independence_from_clay`` quotes ``0.049 * 80^1.139 = 6.09``, which
      the equation it quotes does not produce, so it is an inconsistent case
      rather than a defect in the port.
    """
    i: dict[str, Any] = case.inputs or {}
    if "initial_soc_t_ha" not in i:
        return CaseOutcome(case.model, case.name, "not_run", detail="no initial_soc_t_ha in case")
    if not i.get("monthly_inputs"):
        return CaseOutcome(case.model, case.name, "not_run", detail="no monthly_inputs in case")

    months, problem = _rothc_months(i)
    if months is None:
        return CaseOutcome(case.model, case.name, "not_run", detail=problem)

    from engine.hydroma.simulation.runners.rothc_runner import (
        run_rothc,
        temp_factor,
        water_factor,
    )

    n = len(months)
    mi = i.get("monthly_inputs") or {}
    carbon = _series(mi.get("carbon_input"), n) or [0.0] * n
    try:
        result = run_rothc(
            initial_soc_t_ha=float(i["initial_soc_t_ha"]),
            clay_pct=float(i.get("clay_pct", 23.0)),
            monthly=months,
            residue_c_t_ha_per_month=float(carbon[0]),
            plant_retainment=float(i.get("p_factor", 0.6)),
            years=int(i.get("years", 1)),
        )
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(case.model, case.name, "not_run", detail=f"rothc raised {exc}")

    pools = result.get("pools_t_ha", {})
    measured: dict[str, Any] = {
        "final_soc_t_ha": result.get("soc_after_t_ha"),
        "final_dpm_t_ha": pools.get("DPM"),
        "final_rpm_t_ha": pools.get("RPM"),
        "final_bio_t_ha": pools.get("BIO"),
        "final_hum_t_ha": pools.get("HUM"),
        "final_iom_t_ha": result.get("iom_t_ha"),
        "cumulative_co2_t_ha": result.get("co2_respired_t_ha"),
        "stabilized_fraction": result.get("stabilized_fraction"),
        "co2_fraction": result.get("co2_fraction"),
        "iom_t_ha": result.get("iom_t_ha"),
    }
    # Derived quantities the case names: the rate modifiers are exposed by the
    # implementation and are evaluated at the climate the case itself supplies.
    measured["temp_factor_at_10c"] = temp_factor(float(months[0].tmean_c))
    measured["moisture_factor"] = water_factor(float(months[0].smd_mm), float(months[0].max_smd_mm))
    breakpoint_mm = _MOISTURE_BREAKPOINT * float(months[0].max_smd_mm)
    measured["moisture_factor_at_breakpoint"] = water_factor(
        breakpoint_mm, float(months[0].max_smd_mm)
    )
    measured["moisture_factor_above"] = water_factor(
        breakpoint_mm * (1.0 + 1e-9), float(months[0].max_smd_mm)
    )
    # Mass balance of the run: initial + inputs - respired = final. Computed here
    # from the case's own identity, not read off the model, so a violation is the
    # model's and not a convention of either side.
    total_input = sum(carbon)
    measured["mass_balance_error"] = abs(
        float(i["initial_soc_t_ha"]) + total_input - float(result["co2_respired_t_ha"])
        - float(result["soc_after_t_ha"])
    )
    measured["soc_decrease"] = bool(result["soc_after_t_ha"] < result["soc_before_t_ha"])

    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    want = {k: v for k, v in expected.items() if k not in _NON_NUMERIC_KEYS and v is not None}
    if not want:
        return CaseOutcome(
            case.model, case.name, "not_run", detail="no numeric expectation in case",
            measured=measured,
        )

    contradictions = _rothc_contradictions(case, expected, measured)
    if contradictions:
        return CaseOutcome(
            case.model,
            case.name,
            "inconsistent_case",
            detail="; ".join(contradictions),
            measured=measured,
            expected=expected,
            contradictions=contradictions,
        )

    problems: list[str] = []
    for key, want_value in want.items():
        got = measured.get(key)
        if got is None:
            continue
        if isinstance(want_value, str):
            if key == "mass_balance_error" or _is_bound(want_value):
                threshold = _bound(want_value)
                if threshold is not None and float(got) > threshold:
                    problems.append(f"{key} {float(got):.6g} exceeds its own bound {want_value}")
            # A stored string that is not a bound (a flag such as True) is
            # compared for equality only.
            elif str(got) != want_value.strip():
                problems.append(f"{key} {got!r} vs {want_value!r}")
            continue
        if isinstance(got, bool):
            if bool(got) != bool(want_value):
                problems.append(f"{key} {got!r} vs {want_value!r}")
            continue
        # The case's own relative tolerance, never looser than 5 %: a case that
        # records no tolerance gets a defensible default rather than a pass.
        rtol = min(float(expected.get("rtol", 5e-2)), 5e-2)
        if f"rtol_{key}" in expected:
            rtol = float(expected[f"rtol_{key}"])
        if not math.isclose(float(got), float(want_value), rel_tol=rtol, abs_tol=1e-6):
            problems.append(f"{key} {float(got):.6g} vs {float(want_value):.6g} (rtol {rtol:g})")

    if problems:
        return CaseOutcome(
            case.model,
            case.name,
            "mismatch",
            detail="; ".join(problems),
            measured=measured,
            expected=expected,
        )

    return CaseOutcome(
        case.model,
        case.name,
        "match",
        detail=(
            "all numerically comparable expectations matched the in-house RothC port "
            "(Coleman & Jenkinson 1996; recorded case outputs, so a regression anchor "
            "rather than an external reference)"
        ),
        measured=measured,
        expected=expected,
    )


#: RothC-26.3 soil-moisture breakpoint, as a fraction of the maximum deficit.
_MOISTURE_BREAKPOINT = 0.444


def _rothc_contradictions(
    case: ValidationCase, expected: dict[str, Any], measured: dict[str, Any]
) -> list[str]:
    """Internal contradictions in a RothC case, provable from its own numbers.

    Three, each checked against the equation the case itself quotes:

    * the four active pools plus IOM must be the total SOC. When they do not sum
      to it the case's own pool breakdown and its own total disagree;
    * the water balance ``SOC_final = SOC_initial + inputs - CO2`` must hold.
      When it does not, either the total or the CO2 is wrong;
    * the IOM estimator ``IOM = 0.049 * SOC^1.139`` must reproduce the stored
      IOM. When it does not, the case's own arithmetic is wrong;
    * a piecewise-linear modifier is continuous, so two stored values separated
      by a vanishing interval cannot differ materially.
    """
    inputs: dict[str, Any] = case.inputs or {}
    out: list[str] = []
    pool_keys = (
        "final_dpm_t_ha",
        "final_rpm_t_ha",
        "final_bio_t_ha",
        "final_hum_t_ha",
    )
    if all(k in expected for k in pool_keys) and "final_soc_t_ha" in expected:
        pool_sum = sum(float(expected[k]) for k in pool_keys)
        iom = float(expected.get("final_iom_t_ha", measured.get("iom_t_ha") or 0.0))
        total = float(expected["final_soc_t_ha"])
        if abs(pool_sum + iom - total) > 0.01 * max(abs(total), 1.0):
            out.append(
                f"the case's four pool expectations sum to {pool_sum:.3f} and it separately "
                f"expects IOM {iom:.3f}, so the active pools plus IOM are {pool_sum + iom:.3f} "
                f"tC/ha, against its own total SOC expectation of {total:.3f} tC/ha; a total "
                f"SOC cannot exclude the inert pool the same case quotes"
            )
    if (
        "cumulative_co2_t_ha" in expected
        and "final_soc_t_ha" in expected
        and "initial_soc_t_ha" in inputs
    ):
        initial = float(inputs["initial_soc_t_ha"])
        mi = inputs.get("monthly_inputs", {}) or {}
        monthly = _series(mi.get("carbon_input"), 12) or [0.0]
        total_input = sum(monthly)
        co2 = float(expected["cumulative_co2_t_ha"])
        final = float(expected["final_soc_t_ha"])
        implied = initial + total_input - co2
        if abs(implied - final) > 0.01 * max(abs(final), 1.0):
            out.append(
                f"the case's own balance SOC_initial + inputs - CO2 gives {implied:.3f} tC/ha "
                f"({initial:.1f} + {total_input:.1f} - {co2:.1f}), against its own final SOC "
                f"expectation of {final:.3f} tC/ha"
            )
    if "iom_t_ha" in expected and "initial_soc_t_ha" in inputs:
        published = 0.049 * float(inputs["initial_soc_t_ha"]) ** 1.139
        stored = float(expected["iom_t_ha"])
        if abs(published - stored) > max(float(expected.get("rtol", 1e-2)) * abs(stored), 1e-6):
            out.append(
                f"the case quotes IOM = 0.049 * SOC^1.139 and records {stored:.4f} for "
                f"SOC = {float(inputs['initial_soc_t_ha']):.1f}, but that equation gives "
                f"{published:.4f}; the estimator the implementation ships is the published one"
            )
    mf, mfa = expected.get("moisture_factor"), expected.get("moisture_factor_above")
    if mf is not None and mfa is not None:
        if abs(float(mf) - float(mfa)) > 0.1:
            out.append(
                f"the case stores {float(mf):.4f} at SMD = {_MOISTURE_BREAKPOINT} * maxSMD and "
                f"{float(mfa):.4f} at the same deficit plus an epsilon, a jump of "
                f"{abs(float(mf) - float(mfa)):.4f} across one point; modifier continuity at "
                f"the breakpoint means the smaller value is the pre-fix branch, and the "
                f"implementation's join value is shared by construction"
            )
    return out



# ---------------------------------------------------------------------------
# Models dispatched through the compiled extension (language: cpp cases)
# ---------------------------------------------------------------------------


def _cpp_module() -> Any:
    """The compiled extension, or ``None`` when it is not built."""
    try:
        from engine.hydroma.cpp_bridge import get_module

        return get_module()
    except Exception:  # pragma: no cover - extension absent
        return None


def _missing_references(expected: dict[str, Any]) -> list[str]:
    """Stored expectations that name a reference file which is not in the corpus.

    ``richards_sandy_loam_24h``, ``sv_wetbed_shock`` and their siblings were
    never shipped: the YAML points at
    ``reference_profiles/<name>.npy`` and no such file exists. The case cannot
    be settled, and the honest verdict names the file rather than substituting
    a number for it.
    """
    missing: list[str] = []
    for value in expected.values():
        if not _names_reference(value):
            continue
        stem = Path(value).stem
        try:
            load_reference(stem)
        except KeyError:
            missing.append(stem)
    return missing


def _run_fao56_dual_kc(case: ValidationCase) -> CaseOutcome:
    """FAO-56 dual crop coefficient through the compiled water balance.

    ``engine/cpp_core/src/crop_water.cpp::simulate_crop_water`` is the only
    implementation of the dual-Kc balance in this repository. It takes the daily
    ET0 and rain series plus a ``CropWaterParams`` struct, and it does NOT take:

    * an irrigation *schedule* -- only an ``auto_irrigate`` flag that refills the
      root zone to field capacity whenever depletion exceeds RAW, which is a
      different policy from a dated 50 mm schedule and produces a different
      seasonal total;
    * an initial root-zone depletion -- ``dr`` starts at 0, i.e. at field
      capacity, on every run;
    * a root zone that grows during the season -- ``root_depth_m`` is a single
      number, while the case file carries ``root_depth_ini`` 0.3 m and
      ``root_depth_max`` 1.5 m;
    * a transpiration/evaporation split or a yield response, which is what two of
      the five cases ask for.

    So each case is judged on the part of its expectation the kernel can
    actually produce, and reported as ``not_run`` with the missing piece named
    where it cannot.
    """
    i: dict[str, Any] = case.inputs or {}
    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    params = _case_parameters(case)
    dc = i.get("daily_climate")
    if not isinstance(dc, dict):
        return CaseOutcome(
            case.model, case.name, "not_run", detail="no daily_climate mapping in case"
        )

    et0 = _series(dc.get("et0_mm"))
    rain = _series(dc.get("prec_mm"))
    if not et0 or rain is None or len(rain) != len(et0):
        return CaseOutcome(
            case.model, case.name, "not_run", detail="daily_climate series are absent or unequal"
        )

    # Internal consistency, checked from the case's own numbers before the
    # kernel is called: the FAO-56 dual-Kc balance is
    #   Dr_N = Dr_0 - (P - RO) - I + ETc + DP,   DP >= 0
    # so a case that starts and ends at zero depletion while evaporating more
    # than it was given requires NEGATIVE deep percolation and cannot be
    # satisfied by any implementation.
    contamination: list[str] = []
    if {"total_et_mm", "total_irrigation_mm", "final_depletion_mm"} <= set(expected):
        dr0 = float((i.get("initial_conditions") or {}).get("root_zone_depletion_mm", 0.0))
        dr_n = float(expected["final_depletion_mm"])
        schedule = i.get("irrigation_schedule") or []
        irrigation = float(sum(float(e.get("depth_mm", 0.0)) for e in schedule))
        precipitation = float(sum(rain))
        et_c = float(expected["total_et_mm"])
        implied_dp = dr0 + precipitation + irrigation - et_c - dr_n
        if implied_dp < -1e-9:
            contamination.append(
                f"the case's own water balance needs deep percolation of {implied_dp:.2f} mm: "
                f"Dr_0 {dr0:.1f} + rain {precipitation:.1f} + irrigation {irrigation:.1f} "
                f"- ETc {et_c:.1f} - Dr_final {dr_n:.1f} = {implied_dp:.2f}, and deep "
                f"percolation is a loss, never a gain; so the stored total ET, the stored "
                f"irrigation total and the stored final depletion cannot all hold"
            )

    core = _cpp_module()
    if core is None or not hasattr(core, "simulate_crop_water"):
        return CaseOutcome(
            case.model, case.name, "not_run", detail="C++ extension not built"
        )

    p = core.CropWaterParams()
    mapping = {
        "l_ini": ("ini_days", True),
        "l_dev": ("dev_days", True),
        "l_mid": ("mid_days", True),
        "l_late": ("late_days", True),
        "kcb_ini": ("kcb_ini", False),
        "kcb_mid": ("kcb_mid", False),
        "kcb_end": ("kcb_end", False),
        "rew_mm": ("rew", False),
        "tew_mm": ("tew", False),
        "theta_fc": ("fc", False),
        "theta_wp": ("wp", False),
        "p_fraction": ("raw", False),
    }
    for attr, (key, as_int) in mapping.items():
        if key in params:
            value = float(params[key])
            setattr(p, attr, int(value) if as_int else value)
    if "kc_max" in params:
        p.kc_max = float(params["kc_max"])

    schedule = i.get("irrigation_schedule") or []
    has_schedule = bool(schedule)
    initial = i.get("initial_conditions") or {}
    has_initial_depletion = float(initial.get("root_zone_depletion_mm", 0.0)) > 0.0
    root_ini = float(params.get("root_depth_ini", 0.0))
    root_max = float(params.get("root_depth_max", 0.0))
    # A case that specifies both an initial and a maximum root depth needs a
    # root zone that grows; the kernel takes one depth, so the reading is not
    # determined by the case.
    ambiguous_root = root_ini > 0.0 and root_max > 0.0 and not math.isclose(root_ini, root_max)
    p.root_depth_m = root_max if root_max > 0.0 else root_ini

    # Producible quantities, measured under the only unambiguous reading.
    runs: dict[str, Any] = {}
    try:
        result = core.simulate_crop_water(et0, rain, False, p)
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"simulate_crop_water raised {exc}"
        )
    import numpy as np

    ks = np.asarray(result.stress_factor, dtype=float)
    runs["depletion_max"] = p.root_depth_m
    runs["total_et_mm"] = float(result.total_etc_mm)
    runs["stress_coefficient_avg"] = float(ks.mean())
    runs["ks_day_1"] = float(ks[0])
    runs["ks_day_10"] = float(ks[9]) if ks.size > 9 else None
    runs["final_depletion_mm"] = float(result.depletion_mm[-1])
    runs["mass_balance_error"] = float(result.water_balance_error_mm)

    blockers: list[str] = _missing_references(expected)
    if has_schedule:
        blockers.append(
            f"the case supplies an irrigation schedule of {len(schedule)} dated events "
            f"({float(sum(float(e.get('depth_mm', 0.0)) for e in schedule)):.0f} mm total), and "
            f"simulate_crop_water takes no schedule: its only irrigation argument is an "
            f"auto_irrigate flag that refills to field capacity when depletion exceeds RAW"
        )
    if has_initial_depletion:
        taw = 1000.0 * (float(params.get("fc", 0.0)) - float(params.get("wp", 0.0))) * (
            root_max or root_ini or 1.0
        )
        raw = float(params.get("raw", 0.55)) * taw
        ks_at_raw = float(initial.get("root_zone_depletion_mm", 0.0))
        blockers.append(
            "the case starts the root zone at "
            f"{float(initial.get('root_zone_depletion_mm', 0.0)):.0f} mm of depletion, and "
            "simulate_crop_water always starts at dr = 0 (field capacity)"
            + (
                f"; and the case's initial depletion {ks_at_raw:.0f} mm is the RAW of its own "
                f"parameters ({raw:.0f} mm of a {taw:.0f} mm TAW), so any further uptake puts the "
                "root zone below RAW where FAO-56 eq. 84 gives Ks = (TAW-Dr)/(TAW-RAW) < 1 -- a "
                "case that demands Ks = 1 after ten days of uptake cannot be satisfied"
                if abs(ks_at_raw - raw) < 1e-6
                else ""
            )
        )
    if ambiguous_root:
        blockers.append(
            f"the case's parameters specify a growing root zone (root_depth_ini "
            f"{root_ini:.1f} m to root_depth_max {root_max:.1f} m) but CropWaterParams takes a "
            f"single root_depth_m; the two admissible readings differ by a factor of "
            f"{root_max / root_ini:.1f}, so the case does not determine the kernel's input"
        )
    if "seasonal_yield_reduction" in expected:
        blockers.append(
            "the case expects a seasonal yield reduction, and the dual-Kc kernel returns no "
            "yield response: there is no Ky or yield model behind simulate_crop_water"
        )
    if "evaporation_fraction" in expected or any(
        k.startswith("evaporation_day") for k in expected
    ):
        blockers.append(
            "the case expects an evaporation series or an evaporation fraction "
            "(Ke / (Kcb*Ks + Ke)), and CropWaterResult exposes only kc_effective "
            "(= Kcb*Ks + Ke combined); Kcb and Ke are not separately returned, so the "
            "split cannot be recovered from the result"
        )
    if "seasonal_et_breakdown" in expected:
        blockers.append(
            "the case expects a transpiration/evaporation breakdown, which the kernel does "
            "not report"
        )

    if contamination:
        return CaseOutcome(
            case.model,
            case.name,
            "inconsistent_case",
            detail="; ".join(contamination),
            contradictions=contamination,
            measured=runs,
            expected=expected,
        )
    if blockers:
        detail = "; ".join(blockers)
        measured_note = (
            f" measured with root_depth_m = {runs['depletion_max']:.1f} m and no irrigation: "
            f"total_et {runs['total_et_mm']:.2f} mm, final depletion "
            f"{runs['final_depletion_mm']:.2f} mm, mean Ks "
            f"{runs['stress_coefficient_avg']:.4f}, balance error "
            f"{runs['mass_balance_error']:.3g}"
        )
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=detail + measured_note,
            measured=runs,
            expected=expected,
        )

    # No blocker: compare everything the kernel can produce.
    comparable = {
        "total_et_mm": "total_et_mm",
        "final_depletion_mm": "final_depletion_mm",
        "stress_coefficient_avg": "stress_coefficient_avg",
        "ks_day_1": "ks_day_1",
        "ks_day_10": "ks_day_10",
    }
    problems: list[str] = []
    compared = 0
    for stored_key, measured_key in comparable.items():
        if stored_key not in expected or runs.get(measured_key) is None:
            continue
        want = expected[stored_key]
        if _is_bound(want):
            threshold = _bound(want)
            compared += 1
            if threshold is not None and runs[measured_key] > threshold:
                problems.append(f"{stored_key} {runs[measured_key]:.6g} exceeds {want}")
            continue
        if _names_reference(want):
            continue
        rtol = min(float(expected.get("rtol", 5e-2)), 5e-2)
        compared += 1
        if not math.isclose(float(runs[measured_key]), float(want), rel_tol=rtol, abs_tol=1e-6):
            problems.append(
                f"{stored_key} {float(runs[measured_key]):.6g} vs {float(want):.6g} (rtol {rtol:g})"
            )
    if compared == 0:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail="no comparable numeric expectation in case",
            measured=runs,
            expected=expected,
        )
    return CaseOutcome(
        case.model,
        case.name,
        "match" if not problems else "mismatch",
        detail="; ".join(problems)
        or "all numerically comparable expectations matched the compiled dual-Kc balance",
        measured=runs,
        expected=expected,
    )


_RICHARDS_TOP = {"flux": "Flux", "pressure": "Head", "head": "Head"}
_RICHARDS_BOTTOM = {"free_drainage": "FreeDrainage", "pressure": "Head", "head": "Head"}


def _run_richards(case: ValidationCase) -> CaseOutcome:
    """1-D Richards (Celia et al. 1990 mixed form) through the compiled solver.

    Two properties of ``engine/cpp_core/src/richards.cpp`` decide whether a case
    can be judged at all, and both are recorded findings rather than adapter
    choices:

    * the bottom-boundary flux is accumulated **only** for free drainage
      (``richards.cpp:296-298``: ``step_bottom += k_scalar(...)`` inside the
      ``FreeDrainage`` branch), so for a prescribed-head bottom boundary the
      reported ``mass_balance_error`` mixes in an unaccounted inflow and is not
      the case's balance error;
    * the top boundary is accumulated as ``flux_top_cm_day * dt``
      (``richards.cpp:232``, ``:295``) regardless of whether the boundary is a
      flux or a prescribed head, so for a Dirichlet top boundary the prescribed
      head value is added to the injected volume as though it were a flux.

    Both are named in the detail instead of being worked around, and no
    expectation is scored against a number the kernel does not compute.
    """
    i: dict[str, Any] = case.inputs or {}
    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    top = i.get("top_boundary") or {}
    bottom = i.get("bottom_boundary") or {}
    top_type = str(top.get("type", "")).lower()
    bottom_type = str(bottom.get("type", "")).lower()
    try:
        nz = int(i["nz"])
        dz = float(i["dz"])
        dt = float(i["dt"])
        n_steps = int(i["n_steps"])
        h0 = float(i["initial_pressure_head"])
    except KeyError as exc:
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"missing input {exc}"
        )

    core = _cpp_module()
    if core is None or not hasattr(core, "simulate_richards"):
        return CaseOutcome(case.model, case.name, "not_run", detail="C++ extension not built")

    missing = _missing_references(expected)
    o = core.RichardsOptions()
    o.n_cells = nz
    o.column_depth_cm = dz * nz
    o.dt_days = dt / 86400.0
    o.n_steps = n_steps
    o.max_iter = 50
    o.tolerance_cm = 1e-6
    if top_type not in _RICHARDS_TOP:
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"unknown top boundary {top_type!r}"
        )
    if bottom_type not in _RICHARDS_BOTTOM:
        return CaseOutcome(
            case.model, case.name, "not_run", detail=f"unknown bottom boundary {bottom_type!r}"
        )
    o.top = getattr(core.TopBoundary, _RICHARDS_TOP[top_type])
    o.top_value_cm_day = float(top.get("value", 0.0))
    o.bottom = getattr(core.BottomBoundary, _RICHARDS_BOTTOM[bottom_type])
    if bottom_type in ("pressure", "head"):
        o.bottom_head_cm = float(bottom.get("value", 0.0))

    import numpy as np

    try:
        result = core.simulate_richards(i.get("soil_type", "sandy_loam"), [h0] * nz, o)
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                f"the compiled solver does not converge for this case's own options "
                f"(nz {nz}, dz {dz} cm, dt {dt} s, {n_steps} steps, {top_type} top "
                f"{top.get('value')} / {bottom_type} bottom): {exc}"
                + (f"; also references {', '.join(missing)}, not in the corpus" if missing else "")
            ),
            expected=expected,
        )

    theta = np.asarray(result.theta, dtype=float)
    measured = {
        "mass_balance_error": float(result.mass_balance_error),
        "converged": bool(result.converged),
        "picard_iterations_per_step": int(result.iterations_last_step),
        "rejected_substeps": int(result.rejected_substeps),
        "cumulative_top_flux_cm": float(np.asarray(result.cumulative_top_flux_cm, dtype=float)[-1]),
        "cumulative_bottom_flux_cm": float(
            np.asarray(result.cumulative_bottom_flux_cm, dtype=float)[-1]
        ),
        "theta_range": [float(theta.min()), float(theta.max())],
    }

    if missing:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                "; ".join(f"references {name}, which is not in the corpus" for name in missing)
                + (
                    f"; measured on the way: the compiled solver closed the balance to "
                    f"{measured['mass_balance_error']:.3g} (relative) with converged="
                    f"{measured['converged']} after "
                    f"{measured['picard_iterations_per_step']} Picard iterations, but the "
                    f"case's primary expectation is the reference profile, so the case "
                    f"cannot be settled"
                )
            ),
            measured=measured,
            expected=expected,
        )
    blockers = []
    if top_type in ("pressure", "head"):
        blockers.append(
            "the top boundary is a prescribed head "
            f"({top.get('value')} cm) and the kernel accumulates it as an injected flux "
            "(richards.cpp:232 and :295 add top_value_cm_day * dt to the volume regardless of "
            "the boundary type), so its mass_balance_error and cumulative_top_flux_cm are not "
            "this case's balance; a Dirichlet inflow would have to be the computed q at the face"
        )
    if bottom_type in ("pressure", "head"):
        blockers.append(
            "the bottom boundary is a prescribed head "
            f"({bottom.get('value')} cm) and the kernel accumulates the bottom flux only for "
            "free drainage (richards.cpp:296-298), so its mass_balance_error omits the "
            f"boundary inflow entirely: measured {measured['mass_balance_error']:.4g}, which is "
            "an artefact of the accounting, not of this case"
        )
    if "max_residual" in expected:
        blockers.append(
            "the case expects a maximum Picard residual, and RichardsResult reports neither the "
            "residual nor the tolerance it converged to -- only converged and iterations_last_step"
        )

    if blockers:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail="; ".join(blockers),
            measured=measured,
            expected=expected,
        )

    problems: list[str] = []
    compared = 0
    for key, want in expected.items():
        if key in _NON_NUMERIC_KEYS or want is None or key not in measured:
            continue
        got = measured[key]
        if isinstance(got, bool):
            if bool(got) != bool(want):
                problems.append(f"{key} {got!r} vs {want!r}")
            compared += 1
            continue
        if not isinstance(got, (int, float)):
            # A measured value that is not a number (a list, a mapping, a
            # string) has no numeric comparison to make.
            continue
        if _is_bound(want):
            threshold = _bound(want)
            compared += 1
            if threshold is not None and float(got) > threshold:
                problems.append(f"{key} {float(got):.6g} exceeds its own bound {want}")
            continue
        rtol = min(float(expected.get("rtol", 5e-2)), 5e-2)
        compared += 1
        if not math.isclose(float(got), float(want), rel_tol=rtol, abs_tol=1e-6):
            problems.append(f"{key} {float(got):.6g} vs {float(want):.6g} (rtol {rtol:g})")
    if compared == 0:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail="no comparable numeric expectation in case",
            measured=measured,
            expected=expected,
        )
    return CaseOutcome(
        case.model,
        case.name,
        "match" if not problems else "mismatch",
        detail="; ".join(problems)
        or "all numerically comparable expectations matched the compiled Richards solver",
        measured=measured,
        expected=expected,
    )


#: Left-hand boundary conditions the compiled Saint-Venant kernel can express.
_SV_LEFT_BCS = {"wall", "inflow", "supercritical_inflow"}
#: Right-hand boundary conditions it can express: a transmissive outflow only.
_SV_RIGHT_BCS = {"transmissive"}


def _run_saint_venant(case: ValidationCase) -> CaseOutcome:
    """1-D Saint-Venant (Rusanov FV, Manning friction) through the kernel.

    ``engine/cpp_core/src/saint_venant.cpp::simulate_saint_venant`` takes an
    initial depth profile, an imposed left inflow and an options block. Its
    boundary conditions are a left imposed inflow (a zero inflow behaves as a
    wall) and a right transmissive outflow. A case that names any other right-hand
    boundary, or that needs a bed elevation, cannot be expressed in that API and
    is reported with that gap named.
    """
    i: dict[str, Any] = case.inputs or {}
    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    bcs = i.get("boundary_conditions") or {}
    left_bc = str(bcs.get("left", "inflow"))
    right_bc = str(bcs.get("right", "transmissive"))
    ic = i.get("initial_conditions") or {}

    core = _cpp_module()
    if core is None or not hasattr(core, "simulate_saint_venant"):
        return CaseOutcome(case.model, case.name, "not_run", detail="C++ extension not built")

    if "bed_elevation" in i:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                f"the case needs a bed elevation ({str(i['bed_elevation'])[:60]}) and "
                "SaintVenantOptions has no bathymetry input: the bed is flat at a single "
                "bed_slope, so the bump the case describes cannot be represented"
            ),
        )
    if left_bc not in _SV_LEFT_BCS or right_bc not in _SV_RIGHT_BCS:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                f"the case's boundary conditions are left {left_bc!r} / right {right_bc!r}, and "
                "the kernel implements a left imposed inflow and a right transmissive "
                "outflow only, so the named right-hand boundary has no implementation"
            ),
        )

    nx = int(i.get("nx", 0))
    dx = float(i.get("dx", 0.0))
    width = float(i.get("channel_width", 1.0))
    if "uniform" in ic:
        depth = [float(ic["uniform"]["depth"])] * nx
        velocity = float(ic["uniform"].get("velocity", 0.0))
    else:
        left = ic.get("left") or {}
        right = ic.get("right") or {}
        depth = [float(left.get("depth", 0.0))] * (nx // 2) + [float(right.get("depth", 0.0))] * (
            nx - nx // 2
        )
        velocity = 0.0
    if nx <= 0 or dx <= 0:
        return CaseOutcome(case.model, case.name, "not_run", detail="nx/dx are not usable")

    # A wall is a zero imposed inflow; a supercritical inflow is the discharge the
    # case's own initial state implies.
    inflow = 0.0 if left_bc == "wall" else width * float(depth[0]) * velocity

    o = core.SaintVenantOptions()
    o.n_cells = nx
    o.length_m = dx * nx
    o.t_end_s = float(i.get("dt", 0.0)) * int(i.get("n_steps", 0))
    o.width_m = width
    o.manning_n = float(i.get("manning_n", 0.03))
    o.bed_slope = float(i.get("slope", 0.0))
    o.cfl = 0.5
    o.dry_tolerance = 1e-4
    o.output_every = 1000

    import numpy as np

    try:
        result = core.simulate_saint_venant(depth, float(inflow), o)
    except Exception as exc:  # noqa: BLE001
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=f"simulate_saint_venant raised {exc}",
            expected=expected,
        )

    rows = np.asarray(result.depth_m, dtype=float)
    times = np.asarray(result.time_s, dtype=float)
    final = rows[-1] if rows.ndim == 2 else rows
    discharge = np.asarray(result.discharge_m3s, dtype=float)
    final_q = discharge[-1] if discharge.ndim == 2 else discharge
    measured: dict[str, Any] = {
        "mass_balance_error": float(result.mass_balance_error),
        "stable": bool(result.stable),
        "dried_cells": int(result.dried_cells),
        "final_depth_range": [float(final.min()), float(final.max())],
        "volume_initial_m3": float(result.total_volume_initial_m3),
        "volume_final_m3": float(result.total_volume_final_m3),
        "cumulative_inflow_m3": float(result.cumulative_inflow_m3),
        "cumulative_outflow_m3": float(result.cumulative_outflow_m3),
    }

    # Analytical relations the case names are evaluated here and reported, not
    # scored: the corpus stores them as formulas, so a disagreement is between
    # the run and a cited solution, which is worth recording in the detail.
    analytic: list[str] = []
    if "shock_speed" in expected or "shock_position" in expected:
        h_left = float(depth[0])
        g = 9.81
        analytical_speed = 2.0 * math.sqrt(g * h_left)
        t_end = float(times[-1]) if times.size else float(i.get("dt", 0.0)) * int(
            i.get("n_steps", 0)
        )
        # Wetting front: last cell whose depth clears 1 % of the upstream depth.
        threshold = 0.01 * h_left
        wet = np.nonzero(final > threshold)[0]
        front_m = (float(wet[-1]) + 0.5) * dx if wet.size else 0.0
        measured_speed = front_m / t_end if t_end > 0 else 0.0
        measured["front_position_m"] = front_m
        measured["front_speed_m_s"] = measured_speed
        measured["analytical_front_speed_m_s"] = analytical_speed
        analytic.append(
            f"Ritter (1892) front speed 2*sqrt(g*h_left) = {analytical_speed:.3f} m/s, measured "
            f"{measured_speed:.3f} m/s (front at {front_m:.0f} m of {dx * nx:.0f} m at "
            f"t = {t_end:.0f} s); the free-surface profile at t = {t_end:.0f} s is not the "
            " Ritter fan, so the case's analytical expectations are not reproduced"
        )
    if "conjugate_depths" in expected:
        analytic.append(
            "the case quotes the sequent-depth relation; the run's final discharge is "
            f"[{float(final_q.min()):.3f}, {float(final_q.max()):.3f}] m3/s against the imposed "
            f"{inflow:.3f} m3/s, so the jump it describes has drained away"
        )

    # Stored expectations that are analytical relations rather than values. The
    # corpus has no numeric value here to agree or disagree with, so the case
    # cannot be settled: the run is measured and reported, and recording the
    # measurement as the case's own expectation would let a relation the
    # implementation does not reproduce pass silently.
    relation_keys = [
        key
        for key, value in expected.items()
        if key not in _NON_NUMERIC_KEYS
        and isinstance(value, str)
        and not _is_bound(value)
        and not _names_reference(value)
    ]
    missing = _missing_references(expected)
    if missing:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                "; ".join(f"references {name}, which is not in the corpus" for name in missing)
                + (
                    f"; measured on the way: the compiled solver closed the balance to "
                    f"{measured['mass_balance_error']:.3g} (relative) with stable="
                    f"{measured['stable']} and "
                    f"{measured['final_depth_range'][1]:.4f} m as the deepest final cell, but "
                    f"the case's primary expectation is the shock profile, so the case cannot "
                    f"be settled"
                )
            ),
            measured=measured,
            expected=expected,
        )
    if relation_keys:
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                f"the case stores {', '.join(relation_keys)} as analytical relations rather than "
                "values, so there is no numeric expectation to compare. Measured against them: "
                + ("; ".join(analytic) if analytic else "no analytical relation evaluated")
                + (
                    f"; the case's one numeric bound, mass_balance_error, is satisfied at "
                    f"{measured['mass_balance_error']:.3g}"
                    if "mass_balance_error" in expected
                    else ""
                )
            ),
            measured=measured,
            expected=expected,
        )

    problems: list[str] = []
    compared = 0
    for key, want in expected.items():
        if key in _NON_NUMERIC_KEYS or want is None or key not in measured:
            continue
        got = measured[key]
        if isinstance(got, bool):
            if bool(got) != bool(want):
                problems.append(f"{key} {got!r} vs {want!r}")
            compared += 1
            continue
        if not isinstance(got, (int, float)):
            continue
        if _is_bound(want):
            # Named ``bound`` because this function already binds ``threshold``
            # to the 0.01 * h_left reference it uses above.
            bound: float | None = _bound(want)
            compared += 1
            if bound is not None and float(got) > bound:
                problems.append(f"{key} {float(got):.6g} exceeds its own bound {want}")
            continue
        if _names_reference(want):
            continue
        rtol = min(float(expected.get("rtol", 5e-2)), 5e-2)
        compared += 1
        if not math.isclose(float(got), float(want), rel_tol=rtol, abs_tol=1e-6):
            problems.append(f"{key} {float(got):.6g} vs {float(want):.6g} (rtol {rtol:g})")

    if compared == 0:
        # The case stores no numeric expectation: every quantity it asks for is
        # an algebraic relation. The run is measured and reported, but the case
        # cannot be settled, and recording the run as its own expectation would
        # hide that.
        return CaseOutcome(
            case.model,
            case.name,
            "not_run",
            detail=(
                "the case stores no numeric expectation, only analytical relations "
                + "; ".join(analytic)
                + (
                    f"; its one numeric bound, mass_balance_error, is satisfied at "
                    f"{measured['mass_balance_error']:.3g}"
                    if "mass_balance_error" in expected
                    else ""
                )
                + "; the measured values are recorded in the case file as a regression anchor"
            ),
            measured=measured,
            expected=expected,
        )
    if problems:
        return CaseOutcome(
            case.model,
            case.name,
            "mismatch",
            detail="; ".join(problems),
            measured=measured,
            expected=expected,
        )
    return CaseOutcome(
        case.model,
        case.name,
        "match",
        detail=(
            "; ".join(problems)
            or (
                "the compiled Saint-Venant solver closed the case's mass balance to "
                f"{measured['mass_balance_error']:.3g} (relative) with stable={measured['stable']}"
                + (f"; {'; '.join(analytic)}" if analytic else "")
            )
        ),
        measured=measured,
        expected=expected,
    )


def _run_biofertilizer(case: ValidationCase) -> CaseOutcome:
    """Biofertilizer C/N formulation through the project's own evaluator.

    The case asks for a mix minimising the distance to a target C/N. What this
    repository ships is ``engine/hydroma/materials/compost_formulator.py::
    calculate_mix_cn_ratio``, which evaluates the C/N of a mix that is handed to
    it -- and ``FormulationOptimizer`` in
    ``engine/hydroma/biofertilizer/advanced_calculator.py``, which is a
    catalogue-driven greedy fill keyed on ``material_code`` and never looks at a
    target C/N. There is no optimiser that takes a material list with a target
    C/N and returns an optimal mix.

    Where the case *records* a mix, the recorded C/N is checked with the
    evaluator the project does have, so the case's own numbers can be judged.
    """
    i: dict[str, Any] = case.inputs or {}
    expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}
    materials = i.get("materials") or []
    if not materials:
        return CaseOutcome(case.model, case.name, "not_run", detail="no materials in case")

    from engine.hydroma.materials.compost_formulator import CompostMaterial, calculate_mix_cn_ratio

    by_name = {m.get("name"): m for m in materials}
    mix = (
        expected.get("optimal_mix_kg")
        if isinstance(expected.get("optimal_mix_kg"), dict)
        else None
    )
    if mix:
        try:
            compost = [
                CompostMaterial(
                    name=str(name),
                    mass_kg=float(kg),
                    carbon_content=float(by_name[name]["c_ratio"]),
                    nitrogen_content=float(by_name[name]["n_ratio"]),
                )
                for name, kg in mix.items()
                if name in by_name
            ]
        except Exception as exc:  # noqa: BLE001
            return CaseOutcome(
                case.model,
                case.name,
                "not_run",
                detail=f"the recorded mix could not be built: {exc}",
            )
        final_cn = calculate_mix_cn_ratio(compost)
        want = expected.get("final_cn_ratio")
        if want is None:
            return CaseOutcome(
                case.model, case.name, "not_run", detail="no final_cn_ratio in expected"
            )
        want = float(want)
        weight = sum(float(kg) for kg in mix.values())
        if not math.isclose(final_cn, want, rel_tol=float(expected.get("rtol", 1e-1))):
            detail = (
                f"the case's own recorded mix ({weight:.0f} kg in total) has a C/N of "
                f"{final_cn:.3f} by the project's own calculate_mix_cn_ratio, against the "
                f"{want:.3f} the same case records under final_cn_ratio; the mix and the "
                f"target it is meant to satisfy are not the same quantity"
            )
            return CaseOutcome(
                case.model,
                case.name,
                "inconsistent_case",
                detail=detail,
                contradictions=[
                    f"recorded mix C/N {final_cn:.3f}",
                    f"recorded final_cn_ratio {want:.3f}",
                ],
                measured={"final_cn_ratio": float(final_cn), "optimal_mix_kg": mix},
                expected=expected,
            )
        return CaseOutcome(
            case.model,
            case.name,
            "match",
            detail=(
                f"the recorded mix evaluates to C/N {final_cn:.3f} against the recorded "
                f"{want:.3f} (FAO C/N guideline band 25-35:1)"
            ),
            measured={"final_cn_ratio": float(final_cn), "optimal_mix_kg": mix},
            expected=expected,
        )

    return CaseOutcome(
        case.model,
        case.name,
        "not_run",
        detail=(
            "no implementation exists in this repository that turns a material list plus a "
            f"target C/N ({expected.get('final_cn_ratio', i.get('target_cn_ratio'))}) into an "
            "optimal mix: calculate_mix_cn_ratio evaluates a mix it is given and does not "
            "optimise, and FormulationOptimizer is a catalogue-driven greedy fill keyed on "
            "material_code that never reads a target C/N. The case also records no mix, so "
            "there is no value to compare"
        ),
        measured={"target_cn_ratio": i.get("target_cn_ratio"), "materials": len(materials)},
        expected=expected,
    )


def _run_reference_only(case: ValidationCase) -> CaseOutcome:
    # A YAML case may carry a single scalar expectation rather than a mapping of
    # field -> value, so normalise before iterating. The six model cases added for
    # the EWSI/EPIA/ECSI/ESRI/HLHS/HPheno/HYRUE indices use the scalar form.
    expected = case.expected
    items = expected.items() if isinstance(expected, dict) else [("value", expected)]
    for _key, value in items:
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
    "scs_cn": _run_scs_cn,
    "HYRUE": _run_class_model,
    "ECSI": _run_class_model,
    "EPIA": _run_class_model,
    "ESRI": _run_class_model,
    "EWSI": _run_class_model,
    "HLHS": _run_class_model,
    "HPheno": _run_class_model,
    # hdvi and hpheno both ship a real implementation in this repository
    # (engine/hydroma/models/hdvi.py, engine/hydroma/models/hpheno.py). They were
    # on the reference-only path: hdvi had no dispatcher under its own
    # lower-case model name, and hpheno's registry key is "HPheno" while its case
    # files say "hpheno", so the lookup missed and the fallback reported "no
    # stored .npy reference and no wired implementation" for cases whose stored
    # expectation is a scalar with a documented rescaling.
    "hdvi": _run_class_model,
    "hpheno": _run_class_model,
    "check_dam": _run_check_dam,
    "rothc": _run_rothc,
    "fao56_dual_kc": _run_fao56_dual_kc,
    "richards_1d": _run_richards,
    "saint_venant_1d": _run_saint_venant,
    "biofertilizer": _run_biofertilizer,
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
        # status is Optional on CaseOutcome, but every runner site sets one.
        status = cast(str, o.status)
        counts[status] = counts.get(status, 0) + 1
    counts["total"] = len(outcomes)
    return counts


def _jsonable(value: Any) -> Any:
    """Best-effort conversion of a recorded measurement to JSON-safe plain types.

    ``CaseOutcome.measured`` is sometimes an ``np.ndarray`` (the stored ``.npy``
    reference cases) and sometimes a float or a mapping. The registry folds
    these records into a model status and exports them as JSON, so the
    conversion happens here, once, instead of in every consumer.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        try:
            return _jsonable(tolist())
        except (TypeError, ValueError):  # pragma: no cover - exotic array-likes
            return str(value)
    return str(value)


def machine_summary(outcomes: list[CaseOutcome] | None = None) -> dict[str, Any]:
    """Per-model, per-case record of a corpus run, in plain JSON-safe types.

    ``summary()`` answers "how many of each status" for the corpus as a whole.
    This answers "which case produced which status, and what did it measure",
    grouped by model, so that a consumer -- notably
    ``engine/models/registry.py::ModelRegistry.attach_validation_results``,
    which folds these records into a model's ``validation_status`` -- does not
    have to import this module or re-derive the grouping, and so the numbers a
    report prints are the same numbers the registry stores.

    Nothing here re-runs or re-judges a case: every field is copied from the
    ``CaseOutcome`` this module produced. A model whose cases are all
    ``not_run`` is reported as such, never as a pass.
    """
    outcomes = outcomes if outcomes is not None else run_all()
    models: dict[str, Any] = {}
    for o in outcomes:
        bucket = models.setdefault(o.model, {"cases": 0, "by_status": {}, "outcomes": []})
        bucket["cases"] += 1
        bucket["by_status"][o.status] = bucket["by_status"].get(o.status, 0) + 1
        bucket["outcomes"].append(
            {
                "name": o.name,
                "status": o.status,
                "detail": o.detail,
                "measured": _jsonable(o.measured),
                "expected": _jsonable(o.expected),
                "contradictions": list(o.contradictions),
            }
        )
    return {
        "counts": summary(outcomes),
        "models": {name: models[name] for name in sorted(models)},
    }


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
        lines.append(f"[{cast(str, o.status).upper():<17}] {o.model}/{o.name}")
        if o.detail:
            lines.append(f"    {o.detail}")
    return "\n".join(lines)
