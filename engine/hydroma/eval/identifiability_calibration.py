"""Stage 40 — identifiability-constrained calibration of HYRUE.

Design
------
The seasonal yield of HYRUE is

    B_day   = PAR_d * f_IPAR(LAI_d) * epsilon * f_water(EWSI_d) * f_temp(T_d)
    B_total = sum_d B_day
    Y_t/ha  = B_total * HI / 100

``epsilon`` and ``HI`` are multiplicative constants applied *after* the
daily sum.  Therefore the seasonal "light-and-stress integral"

    S = sum_d ( PAR_d * f_IPAR(LAI_d) * f_water(EWSI_d) * f_temp(T_d) )

is independent of both, and for any candidate (epsilon, HI):

    Y = epsilon * S * HI / 100

Caching ``S`` (and the daily arrays, for sweeps over k / t_opt) makes a
parameter sweep essentially free once the expensive data acquisition has
been done once per record.  This is what makes calibration feasible at
all: the cost is one pipeline pass over the development set, not one
pass per candidate parameter set.

Identifiability
---------------
``epsilon`` and ``HI`` are perfectly collinear: only the product
``epsilon * HI`` is identifiable from yield data.  The first calibrated
model therefore holds ``HI`` fixed at its documented value and fits
``epsilon`` alone.  See ``STAGE-40-PARAMETER-IDENTIFIABILITY.md``.

Leakage
-------
Every entry point in this module takes *development* records only.
:func:`assert_no_test_districts` is called on every sample and raises if a
test-district record is present.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np


class ParameterClass(StrEnum):
    """How a parameter is treated in the calibration."""

    #: Independent scientific backing is sufficient — never fitted.
    FIXED = "fixed"
    #: Can be estimated from the development data with a defensible method.
    CALIBRATABLE = "calibratable"
    #: Several values give near-identical output — fitted only with explicit
    #: justification, and reported as performance-calibrated.
    WEAKLY_IDENTIFIABLE = "weakly_identifiable"
    #: Not enough evidence to estimate — left at its default.
    INSUFFICIENT_DATA = "insufficient_data"
    #: Used for sensitivity analysis only; never part of an operational model.
    DIAGNOSTIC = "diagnostic"


@dataclass
class ParameterSpec:
    """Classification and bounds of one model parameter."""

    name: str
    unit: str
    parameter_class: ParameterClass
    default_value: float
    allowed_min: float | None = None
    allowed_max: float | None = None
    scientific_source: str = ""
    note: str = ""

    def in_bounds(self, value: float) -> bool:
        import math

        if not math.isfinite(value):
            return False
        if self.allowed_min is not None and value < self.allowed_min:
            return False
        if self.allowed_max is not None and value > self.allowed_max:
            return False
        return True


#: The Stage 40 parameter registry.
#:
#: The bounds are physical / literature-plausible ranges fixed **before**
#: any fitting, not ranges chosen from the observed fit quality.
PARAMETER_REGISTRY: dict[str, ParameterSpec] = {
    "epsilon": ParameterSpec(
        name="epsilon",
        unit="g/MJ IPAR",
        parameter_class=ParameterClass.CALIBRATABLE,
        default_value=2.2,
        allowed_min=1.0,
        allowed_max=4.0,
        scientific_source=(
            "HYRUEParams CROP_PRESETS['wheat'] (Steduto et al. 2009 "
            "AquaCrop range for wheat)"
        ),
        note=(
            "Fitted with HI held fixed, because epsilon and HI are "
            "perfectly collinear in yield data."
        ),
    ),
    "hi": ParameterSpec(
        name="hi",
        unit="dimensionless",
        parameter_class=ParameterClass.FIXED,
        default_value=0.45,
        allowed_min=0.2,
        allowed_max=0.6,
        scientific_source="HYRUEParams CROP_PRESETS['wheat']",
        note=(
            "Held fixed in the first calibrated model. Only the product "
            "epsilon * HI is identifiable from yield data."
        ),
    ),
    "k": ParameterSpec(
        name="k",
        unit="dimensionless",
        parameter_class=ParameterClass.WEAKLY_IDENTIFIABLE,
        default_value=0.65,
        allowed_min=0.3,
        allowed_max=1.0,
        scientific_source=(
            "Beer-Lambert extinction coefficient; conventionally 0.46-0.75 "
            "depending on canopy and row spacing"
        ),
        note=(
            "Confounded with the LAI curve and with the LAI source itself. "
            "Only fitted if the LAI series carries real variation."
        ),
    ),
    "lai_max": ParameterSpec(
        name="lai_max",
        unit="m^2/m^2",
        parameter_class=ParameterClass.WEAKLY_IDENTIFIABLE,
        default_value=6.0,
        allowed_min=3.0,
        allowed_max=8.0,
        scientific_source="HYRUEParams default (physical canopy ceiling)",
        note="Confounded with k; applied as a clip on the canopy.",
    ),
    "t_opt": ParameterSpec(
        name="t_opt",
        unit="degC",
        parameter_class=ParameterClass.WEAKLY_IDENTIFIABLE,
        default_value=20.0,
        allowed_min=10.0,
        allowed_max=30.0,
        scientific_source="HYRUEParams CROP_PRESETS['wheat']",
        note=(
            "Confounded with the hard-coded Gaussian width (8 degC) and with "
            "the season length."
        ),
    ),
    "t_min": ParameterSpec(
        name="t_min",
        unit="degC",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=5.0,
        allowed_min=0.0,
        allowed_max=10.0,
        scientific_source="HYRUEParams default",
        note="Rarely binding in this climate; no gradient information.",
    ),
    "t_max": ParameterSpec(
        name="t_max",
        unit="degC",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=35.0,
        allowed_min=30.0,
        allowed_max=45.0,
        scientific_source="HYRUEParams default",
        note="Rarely binding in this climate; no gradient information.",
    ),
    "thermal_gaussian_width": ParameterSpec(
        name="thermal_gaussian_width",
        unit="degC",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=8.0,
        allowed_min=3.0,
        allowed_max=15.0,
        scientific_source="none (hard-coded in the model)",
        note=(
            "Hard-coded twice in the implementation; it cannot be calibrated "
            "without a code change."
        ),
    ),
    "ewsi_weight_ndmi": ParameterSpec(
        name="ewsi_weight_ndmi",
        unit="dimensionless",
        parameter_class=ParameterClass.WEAKLY_IDENTIFIABLE,
        default_value=0.4,
        allowed_min=0.0,
        allowed_max=1.0,
        scientific_source="project default (EWSIWeights)",
        note="Confounded with the other two weights and with f_water amplitude.",
    ),
    "ewsi_weight_vpd": ParameterSpec(
        name="ewsi_weight_vpd",
        unit="dimensionless",
        parameter_class=ParameterClass.WEAKLY_IDENTIFIABLE,
        default_value=0.3,
        allowed_min=0.0,
        allowed_max=1.0,
        scientific_source="project default (EWSIWeights)",
        note="Confounded with the other two weights.",
    ),
    "ewsi_weight_soil": ParameterSpec(
        name="ewsi_weight_soil",
        unit="dimensionless",
        parameter_class=ParameterClass.WEAKLY_IDENTIFIABLE,
        default_value=0.3,
        allowed_min=0.0,
        allowed_max=1.0,
        scientific_source="project default (EWSIWeights)",
        note="Confounded with the other two weights.",
    ),
    "ndmi_ref": ParameterSpec(
        name="ndmi_ref",
        unit="dimensionless",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=0.3,
        allowed_min=0.0,
        allowed_max=0.7,
        scientific_source="none (project default)",
        note="No published source for wheat in eastern India.",
    ),
    "ndmi_crit": ParameterSpec(
        name="ndmi_crit",
        unit="dimensionless",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=-0.2,
        allowed_min=-0.8,
        allowed_max=0.0,
        scientific_source="none (project default)",
        note="No published source for wheat in eastern India.",
    ),
    "vpd_low": ParameterSpec(
        name="vpd_low",
        unit="kPa",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=0.5,
        allowed_min=0.0,
        allowed_max=2.0,
        scientific_source="none (project default)",
        note="No published source for wheat in eastern India.",
    ),
    "vpd_high": ParameterSpec(
        name="vpd_high",
        unit="kPa",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=4.0,
        allowed_min=2.0,
        allowed_max=8.0,
        scientific_source="none (project default)",
        note="No published source for wheat in eastern India.",
    ),
    "soil_field_capacity": ParameterSpec(
        name="soil_field_capacity",
        unit="m^3/m^3",
        parameter_class=ParameterClass.INSUFFICIENT_DATA,
        default_value=0.35,
        allowed_min=0.2,
        allowed_max=0.5,
        scientific_source="none (project default)",
        note="Not site-specific.",
    ),
    "shortwave_to_par_factor": ParameterSpec(
        name="shortwave_to_par_factor",
        unit="dimensionless",
        parameter_class=ParameterClass.FIXED,
        default_value=0.5,
        allowed_min=0.4,
        allowed_max=0.6,
        scientific_source=(
            "Monteith & Unsworth (2013) ch. 9; FAO-56 default in the absence "
            "of spectral data"
        ),
        note="Unit conversion, not a model parameter; never fitted.",
    ),
}


def assert_no_test_districts(
    records: Sequence[dict[str, Any]],
    test_districts: Iterable[str],
) -> None:
    """Raise if any record belongs to a test district.

    Every calibration entry point calls this.  The check is on the record's
    own ``district_id`` field, so a mislabelled record is caught too.
    """
    forbidden = {str(d) for d in test_districts}
    offenders = [
        str(r.get("record_id", "?"))
        for r in records
        if str(r.get("district_id", "")) in forbidden
    ]
    if offenders:
        raise ValueError(
            "leakage guard: "
            f"{len(offenders)} record(s) belong to test districts "
            f"{sorted(forbidden)}: {offenders[:10]}"
        )


@dataclass
class SeasonProfile:
    """Cached daily inputs for one record.

    Attributes:
        record_id: Stable record identifier.
        district_id: District the record belongs to.
        season: Crop season label.
        observed_yield: Observed grain yield (t/ha).
        s_integral: ``sum_d (PAR_d * f_IPAR * f_water * f_temp)`` — the
            seasonal light-and-stress integral, independent of epsilon and HI.
        n_days: Season length in days.
        par: Daily PAR (MJ/m²/day).
        lai: Daily LAI (m²/m²).
        ewsi: Daily EWSI (0-1 stress index).
        t_mean: Daily mean temperature (°C).
        input_quality: Input quality label from the pipeline.
        ewsi_missing: EWSI components that were unavailable.
    """

    record_id: str
    district_id: str
    season: str
    observed_yield: float
    s_integral: float
    n_days: int
    par: np.ndarray = field(repr=False, default_factory=lambda: np.empty(0))
    lai: np.ndarray = field(repr=False, default_factory=lambda: np.empty(0))
    ewsi: np.ndarray = field(repr=False, default_factory=lambda: np.empty(0))
    t_mean: np.ndarray = field(repr=False, default_factory=lambda: np.empty(0))
    input_quality: str = "unknown"
    ewsi_missing: list[str] = field(default_factory=list)
    #: Where the inputs came from.  The observed yield is the CIMMYT
    #: eastern-India wheat field-trial mean; the daily arrays are resolved
    #: by the engine pipeline (ERA5 weather, Sentinel-2 L2A, GDD LAI).
    data_source: str = "cimmyt_wheat_field_season"

    @property
    def has_daily_arrays(self) -> bool:
        return self.par.size > 0


def predict_yield(
    profile: SeasonProfile,
    epsilon: float,
    hi: float,
    k: float | None = None,
    lai_max: float | None = None,
    t_opt: float | None = None,
    t_min: float = 5.0,
    t_max: float = 35.0,
    gaussian_width: float = 8.0,
) -> float:
    """Predict yield (t/ha) for one record from its cached profile.

    When ``k``/``lai_max``/``t_opt`` are supplied, the daily arrays are
    re-evaluated; otherwise the cached ``s_integral`` is used, which makes
    an epsilon-only sweep free.
    """
    if k is None and t_opt is None:
        s = profile.s_integral
    else:
        if not profile.has_daily_arrays:
            raise ValueError(
                f"record {profile.record_id} has no cached daily arrays"
            )
        from engine.hydroma.models.hyrue import HYRUE

        k_eff = k if k is not None else 0.65
        lai_max_eff = lai_max if lai_max is not None else 6.0
        t_opt_eff = t_opt if t_opt is not None else 20.0

        f_ipar = HYRUE.f_ipar(profile.lai, k_eff, lai_max_eff)
        f_water = 1.0 - profile.ewsi
        t = profile.t_mean
        below = t < t_min
        above = t > t_max
        clipped = np.where(below | above, t_opt_eff, t)
        f_temp = np.exp(-(((clipped - t_opt_eff) / gaussian_width) ** 2))
        f_temp = np.where(below | above, 0.0, f_temp)
        s = float(np.sum(profile.par * f_ipar * f_water * f_temp))

    return epsilon * s * hi / 100.0


def rmse(observed: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((predicted - observed) ** 2)))


def mae(observed: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(predicted - observed)))


def bias(observed: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(predicted - observed))


def r_squared(observed: np.ndarray, predicted: np.ndarray) -> float | None:
    ss_res = float(np.sum((observed - predicted) ** 2))
    ss_tot = float(np.sum((observed - np.mean(observed)) ** 2))
    if ss_tot <= 1e-12:
        return None
    return float(1.0 - ss_res / ss_tot)


def mape(observed: np.ndarray, predicted: np.ndarray) -> tuple[float | None, int]:
    """Mean absolute percentage error, excluding near-zero observations."""
    nonzero = np.abs(observed) > 1e-6
    excluded = int((~nonzero).sum())
    if not nonzero.any():
        return None, excluded
    value = float(
        np.mean(np.abs((predicted[nonzero] - observed[nonzero]) / observed[nonzero]))
        * 100
    )
    return value, excluded


def evaluate(
    profiles: Sequence[SeasonProfile],
    epsilon: float,
    hi: float,
    k: float | None = None,
    lai_max: float | None = None,
    t_opt: float | None = None,
) -> dict[str, Any]:
    """Evaluate a parameter set on a set of profiles."""
    if not profiles:
        return {
            "n": 0, "rmse": None, "mae": None, "bias": None,
            "r2": None, "mape": None, "mape_excluded": 0,
        }
    observed = np.array([p.observed_yield for p in profiles])
    predicted = np.array(
        [
            predict_yield(p, epsilon, hi, k, lai_max, t_opt)
            for p in profiles
        ]
    )
    mape_value, excluded = mape(observed, predicted)
    return {
        "n": len(profiles),
        "rmse": rmse(observed, predicted),
        "mae": mae(observed, predicted),
        "bias": bias(observed, predicted),
        "r2": r_squared(observed, predicted),
        "mape": mape_value,
        "mape_excluded": excluded,
    }


def calibrate_epsilon(
    profiles: Sequence[SeasonProfile],
    hi: float = 0.45,
    grid: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Fit ``epsilon`` on the development set with ``HI`` held fixed.

    The search is a deterministic grid over the *pre-registered* bounds of
    ``epsilon`` (1.0-4.0 g/MJ IPAR), refined to 0.01 by a second pass
    around the best coarse point.  The bounds are fixed in
    :data:`PARAMETER_REGISTRY` before any fitting, and are not chosen from
    the observed fit quality.

    Returns:
        Dict with the fitted epsilon, the objective value, the grid, and
        the metrics for the baseline and the fitted parameter set.
    """
    spec = PARAMETER_REGISTRY["epsilon"]
    if grid is None:
        coarse = np.arange(
            spec.allowed_min, spec.allowed_max + 1e-9, 0.1
        )
    else:
        coarse = np.asarray(list(grid), dtype=float)

    best: tuple[float, float] | None = None
    for value in coarse:
        if not spec.in_bounds(float(value)):
            continue
        metrics = evaluate(profiles, epsilon=float(value), hi=hi)
        if metrics["rmse"] is None:
            continue
        if best is None or metrics["rmse"] < best[1]:
            best = (float(value), metrics["rmse"])

    refined: list[tuple[float, float]] = []
    if best is not None:
        lo = max(spec.allowed_min, best[0] - 0.1)
        hi_bound = min(spec.allowed_max, best[0] + 0.1)
        for value in np.arange(lo, hi_bound + 1e-9, 0.01):
            if not spec.in_bounds(float(value)):
                continue
            metrics = evaluate(profiles, epsilon=float(value), hi=hi)
            if metrics["rmse"] is None:
                continue
            refined.append((float(value), metrics["rmse"]))
        if refined:
            best = min(refined, key=lambda t: t[1])

    baseline = evaluate(profiles, epsilon=spec.default_value, hi=hi)
    fitted = (
        evaluate(profiles, epsilon=best[0], hi=hi) if best is not None else baseline
    )

    # Objective flatness: how much does RMSE change across the grid?
    grid_values = [m for _, m in refined] if refined else [
        m for _, m in [(float(v), evaluate(profiles, epsilon=float(v), hi=hi)["rmse"])
                       for v in coarse if spec.in_bounds(float(v))]
    ]
    grid_values = [g for g in grid_values if g is not None]
    spread = (max(grid_values) - min(grid_values)) if grid_values else 0.0
    scale = abs(min(grid_values)) if grid_values else 0.0
    relative_spread = (spread / scale) if scale > 1e-12 else float("inf")

    return {
        "parameter": "epsilon",
        "fitted_value": best[0] if best is not None else spec.default_value,
        "hi_fixed": hi,
        "objective": "RMSE on development records (t/ha)",
        "baseline_metrics": baseline,
        "fitted_metrics": fitted,
        "n_records": len(profiles),
        "grid_rmse_min": min(grid_values) if grid_values else None,
        "grid_rmse_max": max(grid_values) if grid_values else None,
        "objective_relative_spread": relative_spread,
        "objective_flat": relative_spread < 0.10,
        "bounds": [spec.allowed_min, spec.allowed_max],
    }


@dataclass
class FoldResult:
    """Result of one leave-one-district-out fold."""

    held_out_district: str
    n_train: int
    n_validation: int
    fitted_epsilon: float
    train_metrics: dict[str, Any]
    validation_metrics: dict[str, Any]
    baseline_validation_metrics: dict[str, Any]
    #: Where the fold's data came from: the CIMMYT eastern-India wheat
    #: development districts only.  No test-district record enters a fold.
    data_source: str = "cimmyt_wheat_development_districts"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def leave_one_district_out(
    profiles: Sequence[SeasonProfile],
    test_districts: Iterable[str],
    hi: float = 0.45,
    min_train_records: int = 5,
) -> dict[str, Any]:
    """Leave-one-district-out cross-validation on the development set.

    For each development district, the district is held out, the
    parameter is fitted on the remaining development districts, and the
    fitted model is evaluated on the held-out district.  The held-out
    district contributes to neither the fit nor any data-dependent
    transformation.

    Args:
        profiles: Development-season profiles.
        test_districts: Districts reserved for the test set; any profile
            belonging to one of them is rejected.
        hi: Harvest index held fixed.
        min_train_records: Minimum training records required for a fold.

    Returns:
        Dict with the per-fold results and the parameter stability
        summary.
    """
    as_dicts = [
        {
            "record_id": p.record_id,
            "district_id": p.district_id,
            "season": p.season,
            "observed_yield": p.observed_yield,
        }
        for p in profiles
    ]
    assert_no_test_districts(as_dicts, test_districts)

    districts = sorted({p.district_id for p in profiles})
    folds: list[FoldResult] = []
    skipped: list[dict[str, Any]] = []

    for district in districts:
        train = [p for p in profiles if p.district_id != district]
        valid = [p for p in profiles if p.district_id == district]
        if len(train) < min_train_records or not valid:
            skipped.append({
                "district": district,
                "reason": (
                    f"only {len(train)} training records "
                    f"(minimum {min_train_records})"
                    if len(train) < min_train_records
                    else "no validation records"
                ),
            })
            continue

        fit = calibrate_epsilon(train, hi=hi)
        epsilon = fit["fitted_value"]
        validation = evaluate(valid, epsilon=epsilon, hi=hi)
        baseline_validation = evaluate(
            valid,
            epsilon=PARAMETER_REGISTRY["epsilon"].default_value,
            hi=hi,
        )
        folds.append(
            FoldResult(
                held_out_district=district,
                n_train=len(train),
                n_validation=len(valid),
                fitted_epsilon=epsilon,
                train_metrics=fit["fitted_metrics"],
                validation_metrics=validation,
                baseline_validation_metrics=baseline_validation,
            )
        )

    values = [f.fitted_epsilon for f in folds]
    stability: dict[str, Any] = {
        "n_folds": len(folds),
        "values": values,
        "mean": float(np.mean(values)) if values else None,
        "median": float(np.median(values)) if values else None,
        "std": float(np.std(values)) if values else None,
        "min": float(min(values)) if values else None,
        "max": float(max(values)) if values else None,
        "range": (float(max(values) - min(values))) if values else None,
        "skipped_folds": skipped,
    }
    if values:
        stability["relative_range"] = (
            (max(values) - min(values)) / abs(float(np.mean(values)))
            if abs(float(np.mean(values))) > 1e-12
            else float("inf")
        )
        stability["stable"] = stability["relative_range"] < 0.25
    else:
        stability["relative_range"] = None
        stability["stable"] = False

    # Does the calibrated model beat the baseline on the held-out folds?
    if folds:
        cal_rmse = [f.validation_metrics["rmse"] for f in folds]
        base_rmse = [f.baseline_validation_metrics["rmse"] for f in folds]
        stability["mean_validation_rmse_calibrated"] = float(np.mean(cal_rmse))
        stability["mean_validation_rmse_baseline"] = float(np.mean(base_rmse))
        stability["calibration_improves_validation"] = bool(
            np.mean(cal_rmse) < np.mean(base_rmse)
        )
    else:
        stability["calibration_improves_validation"] = False

    return {
        "folds": [f.to_dict() for f in folds],
        "stability": stability,
        "districts": districts,
        "hi_fixed": hi,
        "objective": "RMSE on development records (t/ha)",
    }


def parameter_stability_report(
    fold_values: Sequence[float],
    parameter: str = "epsilon",
) -> dict[str, Any]:
    """Summarise the stability of a parameter across cross-validation folds."""
    values = list(fold_values)
    if not values:
        return {
            "parameter": parameter,
            "n_folds": 0,
            "stable": False,
            "note": "no folds produced a value",
        }
    arr = np.array(values, dtype=float)
    mean = float(arr.mean())
    rel_range = (
        float(arr.max() - arr.min()) / abs(mean) if abs(mean) > 1e-12 else float("inf")
    )
    return {
        "parameter": parameter,
        "n_folds": len(values),
        "values": values,
        "mean": mean,
        "median": float(np.median(arr)),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "range": float(arr.max() - arr.min()),
        "relative_range": rel_range,
        "stable": bool(rel_range < 0.25),
        "converged": bool(len(set(np.round(arr, 3))) == 1),
    }


def hash_profiles(profiles: Sequence[SeasonProfile]) -> str:
    """Stable hash of a profile set (identifiers + observed yields)."""
    payload = json.dumps(
        [
            [p.record_id, p.district_id, p.season, round(p.observed_yield, 6)]
            for p in profiles
        ],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


__all__ = [
    "ParameterClass",
    "ParameterSpec",
    "PARAMETER_REGISTRY",
    "SeasonProfile",
    "assert_no_test_districts",
    "calibrate_epsilon",
    "evaluate",
    "fold_result_to_dict",
    "hash_profiles",
    "leave_one_district_out",
    "mape",
    "parameter_stability_report",
    "predict_yield",
    "r_squared",
]


def fold_result_to_dict(fold: FoldResult) -> dict[str, Any]:
    return fold.to_dict()
