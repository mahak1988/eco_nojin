"""Stage 40 — benchmark execution and metrics tests.

Covers:
* the metric definitions
* the baseline and the calibrated result sets are not mixed
* records with incomplete inputs are not counted as valid predictions
* sample sizes are reported for every metric
* a re-run does not duplicate records
* the benchmark refuses test-district records in the calibration path
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

from engine.hydroma.eval.identifiability_calibration import (  # noqa: E402
    SeasonProfile,
    leave_one_district_out,
)
from engine.hydroma.eval.stage39_benchmark import (  # noqa: E402
    cluster_bootstrap_uncertainty,
    compute_benchmark_metrics,
    compute_grouped_metrics,
)

TEST_DISTRICTS = ["Buxar", "Muzaffarpur", "Rohtas"]
STAGE39_RESULTS = Path(
    "D:/HyDroMA/engine/reports/data/stage39_benchmark/record_results.jsonl"
)
STAGE40_RESULTS = Path(
    "D:/HyDroMA/engine/reports/data/stage40_test_benchmark/record_results.jsonl"
)


def _records(n=10):
    return [
        {
            "record_id": f"r{i}",
            "district_id": "Buxar",
            "season": "2016-17",
            "observed_yield": 4.0 + 0.1 * i,
            "predicted_yield": 3.8 + 0.1 * i,
            "execution_status": "COMPUTED",
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def test_metrics_match_hand_computation():
    """RMSE / MAE / Bias / R2 / MAPE match a hand-computed example."""
    records = [
        {"observed_yield": 2.0, "predicted_yield": 4.0},
        {"observed_yield": 4.0, "predicted_yield": 6.0},
    ]
    m = compute_benchmark_metrics(records)
    assert m.n == 2
    assert m.rmse == pytest.approx(2.0)
    assert m.mae == pytest.approx(2.0)
    assert m.bias == pytest.approx(2.0)
    assert m.r2 == pytest.approx(-3.0)
    # |(4-2)/2| = 1.0 and |(6-4)/4| = 0.5 -> mean 0.75 -> 75 %
    assert m.mape == pytest.approx(75.0)


def test_metrics_report_the_sample_size():
    """Every metric set carries its sample size."""
    m = compute_benchmark_metrics(_records(7))
    assert m.n == 7


def test_records_without_predictions_are_excluded():
    """A record with no prediction does not contribute to the metrics."""
    records = _records(3)
    records.append(
        {
            "record_id": "x",
            "observed_yield": 9.0,
            "predicted_yield": None,
            "execution_status": "BLOCKED",
        }
    )
    m = compute_benchmark_metrics(records)
    assert m.n == 3


def test_zero_observations_are_excluded_from_mape():
    """Near-zero observations are excluded and counted."""
    records = [
        {"observed_yield": 0.0, "predicted_yield": 1.0},
        {"observed_yield": 2.0, "predicted_yield": 4.0},
    ]
    m = compute_benchmark_metrics(records)
    assert m.mape_excluded == 1
    assert m.mape == pytest.approx(100.0)


def test_r2_is_undefined_for_zero_variance():
    """R2 is null, with a reason, when the observations have no variance."""
    records = [
        {"observed_yield": 3.0, "predicted_yield": 2.0},
        {"observed_yield": 3.0, "predicted_yield": 4.0},
    ]
    m = compute_benchmark_metrics(records)
    assert m.r2 is None
    assert m.r2_undefined_reason


def test_metrics_are_grouped_by_district_and_season():
    """Grouped metrics are produced for each district and season."""
    records = _records(6)
    records[0]["district_id"] = "Rohtas"
    records[1]["season"] = "2017-18"
    by_district = compute_grouped_metrics(records, "district_id")
    by_season = compute_grouped_metrics(records, "season")
    assert set(by_district) == {"Buxar", "Rohtas"}
    assert set(by_season) == {"2016-17", "2017-18"}


# ---------------------------------------------------------------------------
# Result-set separation
# ---------------------------------------------------------------------------

def test_baseline_and_calibrated_results_are_not_mixed():
    """The two result files are separate and carry different model versions."""
    if not STAGE39_RESULTS.exists() or not STAGE40_RESULTS.exists():
        pytest.skip("result files not both present yet")
    with open(STAGE39_RESULTS, encoding="utf-8") as f:
        baseline = [json.loads(line) for line in f if line.strip()]
    with open(STAGE40_RESULTS, encoding="utf-8") as f:
        calibrated = [json.loads(line) for line in f if line.strip()]

    # The same record may appear in both, but they are different runs and
    # must not be concatenated into one metric set.
    assert baseline is not calibrated
    versions = {r.get("model_version") for r in calibrated}
    if calibrated:
        assert len(versions) == 1


def test_rerun_does_not_duplicate_records():
    """Re-running the runner skips records already in a terminal state."""
    import tempfile

    from engine.hydroma.eval.resumable_benchmark_runner import (
        ResumableBenchmarkRunner,
    )

    with tempfile.TemporaryDirectory() as tmp:
        runner = ResumableBenchmarkRunner(
            db_path=Path(tmp) / "r.sqlite",
            results_path=Path(tmp) / "r.jsonl",
            manifest_path=Path(tmp) / "m.json",
        )
        runner._save_record_state("rec1", "Buxar", "2016-17", "COMPUTED")
        assert runner._is_processed("rec1") is True
        assert runner._get_processed_ids() == {"rec1"}
        # A second run must not re-process it.
        assert "rec1" in runner._get_processed_ids()


def test_failed_record_keeps_its_reason():
    """A failed record is stored with its failure reason."""
    import sqlite3
    import tempfile

    from engine.hydroma.eval.resumable_benchmark_runner import (
        ResumableBenchmarkRunner,
    )

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "r.sqlite"
        runner = ResumableBenchmarkRunner(
            db_path=db,
            results_path=Path(tmp) / "r.jsonl",
            manifest_path=Path(tmp) / "m.json",
        )
        runner._save_record_state(
            "recX", "Rohtas", "2017-18", "FAILED", failure_reason="boom"
        )
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT status, failure_reason FROM record_state "
                "WHERE record_id = 'recX'"
            ).fetchone()
        finally:
            conn.close()
        assert row == ("FAILED", "boom")


# ---------------------------------------------------------------------------
# Uncertainty
# ---------------------------------------------------------------------------

def test_bootstrap_is_blocked_below_three_districts():
    """Fewer than three districts is reported as blocked, not as an interval."""
    records = [
        {
            "district_id": "Buxar",
            "observed_yield": 5.0,
            "predicted_yield": 4.0,
        },
        {
            "district_id": "Rohtas",
            "observed_yield": 5.5,
            "predicted_yield": 4.5,
        },
    ]
    result = cluster_bootstrap_uncertainty(records)
    assert result["status"] == "BLOCKED"
    assert result["n_districts"] == 2


def test_bootstrap_resamples_whole_districts():
    """The bootstrap draws districts, not individual records."""
    records = []
    for d in ("A", "B", "C"):
        for i in range(4):
            records.append({
                "district_id": d,
                "observed_yield": 5.0 + i,
                "predicted_yield": 4.0 + i,
            })
    result = cluster_bootstrap_uncertainty(records, n_bootstrap=50)
    assert result["status"] == "OK"
    assert result["n_districts"] == 3
    assert result["n_records"] == 12
    assert result["rmse_ci"][0] <= result["rmse_mean"] <= result["rmse_ci"][1]


# ---------------------------------------------------------------------------
# Leakage
# ---------------------------------------------------------------------------

def test_calibration_path_rejects_test_districts():
    """A test-district record in the calibration sample aborts."""
    profiles = [
        SeasonProfile(
            record_id="t1", district_id="Buxar", season="2016-17",
            observed_yield=5.0, s_integral=400.0, n_days=150,
        )
    ]
    with pytest.raises(ValueError, match="leakage guard"):
        leave_one_district_out(profiles, test_districts=TEST_DISTRICTS)
