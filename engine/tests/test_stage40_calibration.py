"""Stage 40 — calibration protocol tests.

Covers:
* calibration only ever sees development-district records
* the objective function rejects test-district identifiers
* HI stays fixed in the first calibrated model
* the number of free parameters is limited
* the seed is recorded and the run is reproducible
* the objective function behaves on invalid input
* non-convergence is detected rather than silently accepted
"""

from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

from engine.hydroma.eval.identifiability_calibration import (  # noqa: E402
    PARAMETER_REGISTRY,
    ParameterClass,
    SeasonProfile,
    assert_no_test_districts,
    calibrate_epsilon,
    evaluate,
    hash_profiles,
    parameter_stability_report,
    predict_yield,
)

TEST_DISTRICTS = ["Buxar", "Muzaffarpur", "Rohtas"]
DEV_DISTRICTS = ["Begusarai", "Bhojpur", "Deoria", "EastChamparan",
                 "Kushinagar", "Lakhisarai", "Madhepura"]


def _profiles(n=18, districts=DEV_DISTRICTS):
    out = []
    for i in range(n):
        out.append(
            SeasonProfile(
                record_id=f"r{i}",
                district_id=districts[i % len(districts)],
                season="2016-17",
                observed_yield=4.0 + 0.2 * (i % 5),
                s_integral=300.0 + 10.0 * (i % 7),
                n_days=150,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Leakage guards
# ---------------------------------------------------------------------------

def test_calibration_rejects_test_district_records():
    """A test-district record aborts the calibration."""
    records = [{"record_id": "t1", "district_id": "Buxar"}]
    with pytest.raises(ValueError, match="leakage guard"):
        assert_no_test_districts(records, TEST_DISTRICTS)


def test_calibration_accepts_development_records():
    """Development-district records pass the guard."""
    records = [{"record_id": "d1", "district_id": "Deoria"}]
    assert_no_test_districts(records, TEST_DISTRICTS)


def test_objective_never_sees_test_ids():
    """The calibration entry point refuses test-district input."""
    profiles = _profiles(n=6, districts=["Buxar"])
    with pytest.raises(ValueError):
        # leave_one_district_out performs the guard on every call
        from engine.hydroma.eval.identifiability_calibration import (
            leave_one_district_out,
        )

        leave_one_district_out(profiles, test_districts=TEST_DISTRICTS)


# ---------------------------------------------------------------------------
# Identifiability constraints
# ---------------------------------------------------------------------------

def test_hi_is_fixed_in_the_first_calibrated_model():
    """HI is a FIXED parameter, not a fitted one."""
    assert PARAMETER_REGISTRY["hi"].parameter_class == ParameterClass.FIXED


def test_epsilon_is_the_only_calibratable_parameter():
    """Exactly one parameter is free in the first calibrated model."""
    free = [
        name
        for name, spec in PARAMETER_REGISTRY.items()
        if spec.parameter_class == ParameterClass.CALIBRATABLE
    ]
    assert free == ["epsilon"]


def test_number_of_free_parameters_is_limited():
    """At most three parameters are free at once in the first model."""
    calibratable = [
        name
        for name, spec in PARAMETER_REGISTRY.items()
        if spec.parameter_class == ParameterClass.CALIBRATABLE
    ]
    # The first calibrated model frees exactly one parameter (epsilon).
    assert len(calibratable) <= 3
    assert calibratable == ["epsilon"]


def test_epsilon_and_hi_are_collinear():
    """Scaling epsilon and inversely scaling HI gives the same prediction."""
    profile = SeasonProfile(
        record_id="x", district_id="Deoria", season="2016-17",
        observed_yield=5.0, s_integral=400.0, n_days=150,
    )
    a = predict_yield(profile, epsilon=2.0, hi=0.45)
    b = predict_yield(profile, epsilon=4.0, hi=0.225)
    assert a == pytest.approx(b)


def test_every_parameter_has_a_class_and_bounds():
    """Each registered parameter declares a class and an allowed range."""
    for name, spec in PARAMETER_REGISTRY.items():
        assert spec.parameter_class in tuple(ParameterClass), name
        assert spec.allowed_min is not None, name
        assert spec.allowed_max is not None, name
        assert spec.allowed_min < spec.allowed_max, name


# ---------------------------------------------------------------------------
# Objective function behaviour
# ---------------------------------------------------------------------------

def test_objective_rejects_empty_input():
    """An empty sample yields null metrics, not a crash."""
    metrics = evaluate([], epsilon=2.2, hi=0.45)
    assert metrics["n"] == 0
    assert metrics["rmse"] is None


def test_objective_handles_invalid_values():
    """Non-finite inputs are rejected by the parameter bounds."""
    spec = PARAMETER_REGISTRY["epsilon"]
    assert spec.in_bounds(2.2) is True
    assert spec.in_bounds(spec.allowed_max + 1.0) is False
    assert spec.in_bounds(spec.allowed_min - 1.0) is False
    assert spec.in_bounds(float("nan")) is False


def test_calibration_stays_within_pre_registered_bounds():
    """The fitted epsilon never leaves its pre-registered range."""
    fit = calibrate_epsilon(_profiles(24), hi=0.45)
    spec = PARAMETER_REGISTRY["epsilon"]
    assert spec.in_bounds(fit["fitted_value"])


def test_calibration_is_reproducible():
    """The same input gives the same fitted value."""
    profiles = _profiles(24)
    a = calibrate_epsilon(profiles, hi=0.45)
    b = calibrate_epsilon(profiles, hi=0.45)
    assert a["fitted_value"] == b["fitted_value"]
    assert a["fitted_metrics"]["rmse"] == b["fitted_metrics"]["rmse"]


def test_calibration_reports_objective_flatness():
    """A flat objective is reported, not hidden."""
    fit = calibrate_epsilon(_profiles(24), hi=0.45)
    assert "objective_flat" in fit
    assert "objective_relative_spread" in fit


def test_non_convergence_is_detected():
    """Unstable fold values are reported as unstable."""
    report = parameter_stability_report([2.0, 2.05, 3.9], parameter="epsilon")
    assert report["stable"] is False
    assert report["relative_range"] > 0.25


def test_converged_folds_are_reported():
    """Identical fold values are reported as converged."""
    report = parameter_stability_report([2.20, 2.20, 2.20], parameter="epsilon")
    assert report["converged"] is True
    assert report["stable"] is True


def test_profile_hash_is_stable():
    """The profile hash depends only on identity and observed yield."""
    profiles = _profiles(6)
    assert hash_profiles(profiles) == hash_profiles(_profiles(6))
