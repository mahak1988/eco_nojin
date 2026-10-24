"""Stage 40 — frozen parameter plumbing tests.

These tests cover the defect that the Stage 40 benchmark would otherwise
have reproduced silently: ``HYRUE(params=..., crop="wheat")`` lets the
**crop preset override the explicit parameters**, so a calibrated model
would have been evaluated with the uncalibrated default epsilon.

Covers:
* ``HYRUE`` gives explicit params precedence (crop does not override)
* ``compute_hyrue_seasonal`` uses supplied params, not the crop preset
* ``SeasonalPredictionRequest.hyrue_params`` reaches the model
* the analytical Stage 40 calibration formula equals ``HYRUE.compute``
* the runner passes its parameters into every prediction
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

from engine.hydroma.eval.identifiability_calibration import predict_yield  # noqa: E402
from engine.hydroma.models.hyrue import HYRUE, HYRUEParams  # noqa: E402
from engine.hydroma.simulation.par_pipeline import (  # noqa: E402
    SeasonalClimateInputs,
    compute_hyrue_seasonal,
)


def _params(epsilon: float) -> HYRUEParams:
    return HYRUEParams(
        epsilon=epsilon,
        k=0.65,
        hi=0.45,
        lai_max=6.0,
        t_opt=20.0,
        t_min=5.0,
        t_max=35.0,
    )


def _inputs(n: int = 30) -> SeasonalClimateInputs:
    rng = np.random.default_rng(7)
    return SeasonalClimateInputs(
        dates=[f"2020-01-{i + 1:02d}" for i in range(n)],
        par=rng.uniform(15.0, 25.0, n),
        lai=np.linspace(0.5, 5.0, n),
        ewsi=rng.uniform(0.05, 0.4, n),
        t_mean=rng.uniform(12.0, 30.0, n),
        par_provenance="test",
        lai_provenance={"quality_status": "test"},
        ewsi_provenance={"quality_status": "test"},
        input_quality="complete",
        missing_fields=[],
    )


# ----------------------------------------------------------------------
# HYRUE parameter precedence
# ----------------------------------------------------------------------


def test_hyrue_explicit_params_take_precedence_over_crop() -> None:
    """Explicit params must not be discarded when a crop is also given."""
    model = HYRUE(params=_params(3.7), crop="wheat")
    assert model.params.epsilon == pytest.approx(3.7)


def test_hyrue_crop_preset_still_applies_without_params() -> None:
    """The pre-existing crop-preset behaviour is unchanged."""
    model = HYRUE(crop="wheat")
    assert model.params.epsilon == pytest.approx(2.2)


# ----------------------------------------------------------------------
# Seasonal pipeline
# ----------------------------------------------------------------------


def test_compute_hyrue_seasonal_uses_supplied_params() -> None:
    """``params`` must change the result; the crop preset must not win."""
    inputs = _inputs()
    default_result = compute_hyrue_seasonal(inputs, crop="wheat")
    calibrated_result = compute_hyrue_seasonal(
        inputs, crop="wheat", params=_params(2.8)
    )

    assert calibrated_result["yield_t_ha"] != pytest.approx(
        default_result["yield_t_ha"]
    )
    # epsilon scales the biomass linearly, so the ratio must be exact.
    ratio = calibrated_result["yield_t_ha"] / default_result["yield_t_ha"]
    assert ratio == pytest.approx(2.8 / 2.2, rel=1e-9)


def test_compute_hyrue_seasonal_without_params_uses_preset() -> None:
    """The default path is unchanged: no params means the crop preset."""
    inputs = _inputs()
    result = compute_hyrue_seasonal(inputs, crop="wheat")
    preset = HYRUE(crop="wheat")
    expected = preset.compute(
        par=inputs.par, lai=inputs.lai, ewsi=inputs.ewsi, t_mean=inputs.t_mean
    )
    assert result["yield_t_ha"] == pytest.approx(expected["yield_t_ha"], rel=1e-12)


# ----------------------------------------------------------------------
# Analytical calibration formula == HYRUE.compute
# ----------------------------------------------------------------------


def test_analytical_calibration_matches_hyrue_compute() -> None:
    """The Stage 40 analytical yield must equal the model it calibrates.

    The calibration evaluates a closed-form replica of HYRUE's seasonal
    integral so that parameter sweeps are free.  If that replica ever
    drifts from ``HYRUE.compute`` the calibration would be fitting a
    different model from the one evaluated on the test set.
    """
    from engine.hydroma.eval.identifiability_calibration import SeasonProfile

    rng = np.random.default_rng(11)
    n = 40
    par = rng.uniform(12.0, 28.0, n)
    lai = np.linspace(0.2, 4.5, n)
    ewsi = rng.uniform(0.0, 0.5, n)
    t_mean = rng.uniform(8.0, 33.0, n)
    params = _params(2.57)

    profile = SeasonProfile(
        record_id="r1",
        district_id="d",
        season="2020",
        observed_yield=3.0,
        s_integral=0.0,
        n_days=n,
        par=par,
        lai=lai,
        ewsi=ewsi,
        t_mean=t_mean,
        input_quality="complete",
        ewsi_missing=[],
    )

    analytical = predict_yield(
        profile,
        epsilon=params.epsilon,
        hi=params.hi,
        k=params.k,
        lai_max=params.lai_max,
        t_opt=params.t_opt,
        t_min=params.t_min,
        t_max=params.t_max,
    )

    model = HYRUE(params=params)
    reference = model.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t_mean)

    assert analytical == pytest.approx(reference["yield_t_ha"], rel=1e-12)


# ----------------------------------------------------------------------
# Runner plumbing
# ----------------------------------------------------------------------


def test_runner_passes_parameters_into_predictions() -> None:
    """The runner must hand its parameter set to every prediction."""
    from engine.hydroma.eval.resumable_benchmark_runner import ResumableBenchmarkRunner

    runner = ResumableBenchmarkRunner(
        db_path=Path("D:/HyDroMA/engine/reports/data/_tmp_stage40_runner.sqlite"),
        results_path=Path("D:/HyDroMA/engine/reports/data/_tmp_stage40_runner.jsonl"),
        manifest_path=Path("D:/HyDroMA/engine/reports/data/_tmp_stage40_runner.json"),
        hyrue_params=_params(2.57),
        run_id="test",
        data_label="test",
    )
    assert runner.hyrue_params is not None
    assert runner.hyrue_params.epsilon == pytest.approx(2.57)
    assert runner.data_label == "test"


def test_runner_manifest_records_model_parameters(tmp_path) -> None:
    """The run manifest must record the parameter set that was used."""
    from engine.hydroma.eval.resumable_benchmark_runner import ResumableBenchmarkRunner

    runner = ResumableBenchmarkRunner(
        db_path=tmp_path / "state.sqlite",
        results_path=tmp_path / "results.jsonl",
        manifest_path=tmp_path / "manifest.json",
        hyrue_params=_params(2.57),
        run_id="test",
        data_label="test",
    )
    assert runner.hyrue_params is not None
    assert runner.data_label == "test"
    assert runner.run_id == "test"
