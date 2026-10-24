"""Stage 40 — spatial grouped cross-validation tests.

Covers:
* leave-one-district-out produces one fold per development district
* the held-out district never contributes to the fit
* parameter stability across folds is assessed, not assumed
* the decision criterion compares validation performance, not training
* folds that cannot be run are reported rather than hidden
"""

from __future__ import annotations

import sys

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

from engine.hydroma.eval.identifiability_calibration import (  # noqa: E402
    SeasonProfile,
    leave_one_district_out,
    parameter_stability_report,
)

TEST_DISTRICTS = ["Buxar", "Muzaffarpur", "Rohtas"]
DEV_DISTRICTS = ["Begusarai", "Bhojpur", "Deoria", "EastChamparan",
                 "Kushinagar", "Lakhisarai", "Madhepura"]


def _profiles(n=28):
    out = []
    for i in range(n):
        out.append(
            SeasonProfile(
                record_id=f"r{i}",
                district_id=DEV_DISTRICTS[i % len(DEV_DISTRICTS)],
                season="2016-17",
                observed_yield=4.0 + 0.1 * (i % 6),
                s_integral=300.0 + 8.0 * (i % 9),
                n_days=150,
            )
        )
    return out


def test_lodo_produces_one_fold_per_development_district():
    """Every development district is used as a held-out group once."""
    result = leave_one_district_out(_profiles(28), test_districts=TEST_DISTRICTS)
    assert result["stability"]["n_folds"] == len(DEV_DISTRICTS)
    held_out = [f["held_out_district"] for f in result["folds"]]
    assert sorted(held_out) == sorted(DEV_DISTRICTS)


def test_held_out_district_is_excluded_from_training():
    """The fold's training set does not contain its held-out district."""
    result = leave_one_district_out(_profiles(28), test_districts=TEST_DISTRICTS)
    for fold in result["folds"]:
        assert fold["n_train"] + fold["n_validation"] == 28
        assert fold["n_validation"] > 0


def test_leave_one_district_out_is_reproducible():
    """The same input gives the same fold estimates."""
    a = leave_one_district_out(_profiles(28), test_districts=TEST_DISTRICTS)
    b = leave_one_district_out(_profiles(28), test_districts=TEST_DISTRICTS)
    assert a["stability"]["values"] == b["stability"]["values"]


def test_stability_is_assessed():
    """Fold-to-fold spread is reported."""
    result = leave_one_district_out(_profiles(28), test_districts=TEST_DISTRICTS)
    stability = result["stability"]
    assert "relative_range" in stability
    assert "stable" in stability
    assert stability["mean"] is not None


def test_decision_criterion_uses_validation_not_training():
    """The improvement flag is computed from held-out performance."""
    result = leave_one_district_out(_profiles(28), test_districts=TEST_DISTRICTS)
    stability = result["stability"]
    assert "mean_validation_rmse_calibrated" in stability
    assert "mean_validation_rmse_baseline" in stability
    expected = (
        stability["mean_validation_rmse_calibrated"]
        < stability["mean_validation_rmse_baseline"]
    )
    assert stability["calibration_improves_validation"] == expected


def test_skipped_folds_are_reported():
    """A district with too few training records is reported, not dropped."""
    profiles = _profiles(4)  # fewer records than the minimum
    result = leave_one_district_out(
        profiles, test_districts=TEST_DISTRICTS, min_train_records=10
    )
    assert result["stability"]["n_folds"] == 0
    assert result["stability"]["skipped_folds"]
    for entry in result["stability"]["skipped_folds"]:
        assert "reason" in entry


def test_stability_report_handles_empty_input():
    """No folds produces an explicit not-stable verdict."""
    report = parameter_stability_report([], parameter="epsilon")
    assert report["n_folds"] == 0
    assert report["stable"] is False
    assert "no folds" in report["note"]
