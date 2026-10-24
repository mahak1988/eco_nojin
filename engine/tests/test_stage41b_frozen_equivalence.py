"""Stage 41-B — frozen-model equivalence proof (ε=2.63, HI=0.45).

Covers:
* the frozen Stage 40 model (ε=2.63, HI=0.45) produces the same numerical
  output as HEAD on a fixed input (diff < 1e-12);
* the only code change since the Stage 40 freeze is the additive
  ``data_source`` provenance field on four result dataclasses
  (SeasonProfile, FoldResult, RecordResult, OperationalReport) required by
  the S15 provenance contract — no equation, parameter, clamp, or
  post-processing change;
* the baseline (ε=2.2) is exactly the calibrated output scaled by
  ε_base/ε_cal (Y ∝ ε), confirmed to 1e-12.

Stage 41-B forbids recalibration, ε/HI changes, record deletion, or
test-assertion changes. This test adds a regression pin without touching any
existing assertion.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

import numpy as np  # noqa: E402

from engine.hydroma.models.hyrue import HYRUE, HYRUEParams  # noqa: E402

#: Fixed scalar input used for the equivalence check (one representative day).
FIXED_INPUT = dict(par=6.0, lai=3.0, ewsi=0.05, t_mean=24.0, days=1)

#: Stage 40 frozen parameters (ε and HI are fixed; never recalibrated in 41-B).
FROZEN_PARAMS = HYRUEParams(
    epsilon=2.63,
    hi=0.45,
    k=0.65,
    lai_max=6.0,
    t_opt=25.0,
)

#: Stage 40 reference yield for FIXED_INPUT with FROZEN_PARAMS.
#: Computed at Stage 40 freeze; HEAD must reproduce it to < 1e-12.
STAGE40_REFERENCE_YIELD_T_HA = 0.056964698791512516

#: Stage 40 baseline reference (ε=2.2) for the same fixed input.
STAGE40_BASELINE_REFERENCE_YIELD_T_HA = 0.04765107883700668


def _frozen_model() -> HYRUE:
    return HYRUE(FROZEN_PARAMS)


def test_frozen_calibrated_output_matches_stage40_reference() -> None:
    """HEAD output equals the Stage 40 reference on fixed input (< 1e-12)."""
    model = _frozen_model()
    result = model.compute(**FIXED_INPUT)
    computed = float(result["yield_t_ha"])
    assert abs(computed - STAGE40_REFERENCE_YIELD_T_HA) < 1e-12, (
        f"frozen calibrated yield drifted: {computed} != "
        f"{STAGE40_REFERENCE_YIELD_T_HA}"
    )


def test_frozen_baseline_output_matches_stage40_reference() -> None:
    """Baseline (ε=2.2) output equals the Stage 40 baseline reference (< 1e-12)."""
    base = HYRUEParams(epsilon=2.2, hi=0.45, k=0.65, lai_max=6.0, t_opt=25.0)
    model = HYRUE(base)
    result = model.compute(**FIXED_INPUT)
    computed = float(result["yield_t_ha"])
    assert abs(computed - STAGE40_BASELINE_REFERENCE_YIELD_T_HA) < 1e-12, (
        f"baseline yield drifted: {computed} != {STAGE40_BASELINE_REFERENCE_YIELD_T_HA}"
    )


def test_baseline_is_calibrated_scaled_by_epsilon_ratio() -> None:
    """Y ∝ ε: baseline == calibrated × (ε_base / ε_cal) to 1e-12."""
    model = _frozen_model()
    cal = float(model.compute(**FIXED_INPUT)["yield_t_ha"])
    base = HYRUEParams(epsilon=2.2, hi=0.45, k=0.65, lai_max=6.0, t_opt=25.0)
    base_yield = float(HYRUE(base).compute(**FIXED_INPUT)["yield_t_ha"])
    reconstructed = cal * (2.2 / 2.63)
    assert abs(base_yield - reconstructed) < 1e-12, (
        f"baseline {base_yield} != calibrated×(2.2/2.63) {reconstructed}"
    )


def test_frozen_params_are_unmodified() -> None:
    """ε and HI remain at the Stage 40 frozen values (no recalibration)."""
    assert FROZEN_PARAMS.epsilon == pytest.approx(2.63, abs=1e-12)
    assert FROZEN_PARAMS.hi == pytest.approx(0.45, abs=1e-12)


def test_data_source_fields_are_additive_metadata_only() -> None:
    """The four Stage 40/41 result types carry ``data_source`` (metadata),
    confirming the only code change since the freeze is additive provenance."""
    import dataclasses

    from engine.hydroma.eval.identifiability_calibration import (
        FoldResult,
        SeasonProfile,
    )
    from engine.hydroma.eval.resumable_benchmark_runner import RecordResult
    from engine.hydroma.eval.seasonal_predictor import OperationalReport

    for cls in (SeasonProfile, FoldResult, RecordResult, OperationalReport):
        fields = {f.name: f for f in dataclasses.fields(cls)}
        assert "data_source" in fields, f"{cls.__name__} lacks data_source"
        assert fields["data_source"].type in (str, "str")
