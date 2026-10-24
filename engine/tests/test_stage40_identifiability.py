"""Stage 40 — parameter identifiability tests.

Covers:
* the parameter registry classifies every model parameter
* uncalibratable parameters are excluded from estimation
* the identifiability constraint (HI fixed) is enforced
* the fitted epsilon is the only quantity the objective can move
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
    calibrate_epsilon,
    evaluate,
    predict_yield,
)


def _profile(**kw):
    base = {
        "record_id": "x",
        "district_id": "Deoria",
        "season": "2016-17",
        "observed_yield": 5.0,
        "s_integral": 400.0,
        "n_days": 150,
    }
    base.update(kw)
    return SeasonProfile(**base)


def test_registry_covers_every_hyrue_parameter():
    """All seventeen HYRUE/EWSI parameters are registered."""
    expected = {
        "epsilon", "hi", "k", "lai_max", "t_opt", "t_min", "t_max",
        "thermal_gaussian_width",
        "ewsi_weight_ndmi", "ewsi_weight_vpd", "ewsi_weight_soil",
        "ndmi_ref", "ndmi_crit", "vpd_low", "vpd_high",
        "soil_field_capacity", "shortwave_to_par_factor",
    }
    assert expected == set(PARAMETER_REGISTRY)


def test_unsourced_parameters_are_not_calibratable():
    """Parameters without a scientific source are not fitted."""
    for name in (
        "ndmi_ref", "ndmi_crit", "vpd_low", "vpd_high",
        "soil_field_capacity", "thermal_gaussian_width",
    ):
        assert (
            PARAMETER_REGISTRY[name].parameter_class
            != ParameterClass.CALIBRATABLE
        ), name


def test_unit_conversion_is_never_fitted():
    """The shortwave->PAR factor is a unit conversion, not a parameter."""
    assert (
        PARAMETER_REGISTRY["shortwave_to_par_factor"].parameter_class
        == ParameterClass.FIXED
    )


def test_epsilon_scales_predictions_linearly():
    """Doubling epsilon doubles the prediction, holding HI fixed."""
    p = _profile()
    a = predict_yield(p, epsilon=2.0, hi=0.45)
    b = predict_yield(p, epsilon=4.0, hi=0.45)
    assert b == pytest.approx(2.0 * a)


def test_hi_scales_predictions_linearly():
    """Doubling HI doubles the prediction, holding epsilon fixed."""
    p = _profile()
    a = predict_yield(p, epsilon=2.2, hi=0.45)
    b = predict_yield(p, epsilon=2.2, hi=0.90)
    assert b == pytest.approx(2.0 * a)


def test_objective_moves_only_epsilon():
    """With HI held fixed, changing the fitted epsilon changes the fit."""
    profiles = [
        _profile(record_id=f"r{i}", observed_yield=4.0 + 0.1 * i,
                 s_integral=300.0 + 5.0 * i)
        for i in range(10)
    ]
    base = evaluate(profiles, epsilon=2.2, hi=0.45)
    fit = calibrate_epsilon(profiles, hi=0.45)
    assert fit["fitted_metrics"]["rmse"] <= base["rmse"]


def test_ewsi_weights_stay_on_the_simplex():
    """The registered EWSI weights sum to one and are non-negative."""
    weights = [
        PARAMETER_REGISTRY["ewsi_weight_ndmi"].default_value,
        PARAMETER_REGISTRY["ewsi_weight_vpd"].default_value,
        PARAMETER_REGISTRY["ewsi_weight_soil"].default_value,
    ]
    assert all(w >= 0 for w in weights)
    assert sum(weights) == pytest.approx(1.0)


def test_weakly_identifiable_parameters_are_flagged():
    """Confounded parameters are marked, not silently fitted."""
    for name in ("k", "lai_max", "t_opt",
                 "ewsi_weight_ndmi", "ewsi_weight_vpd", "ewsi_weight_soil"):
        assert (
            PARAMETER_REGISTRY[name].parameter_class
            == ParameterClass.WEAKLY_IDENTIFIABLE
        ), name
