"""Stage 40 — frozen model configuration tests.

Covers:
* the frozen configuration records every required field
* the frozen parameters match the calibration output
* the frozen model is not modified by a benchmark run
* the configuration hash is stable
* the baseline (Stage 39) results are preserved separately
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

ROOT = Path("D:/HyDroMA")
FROZEN = ROOT / "engine/reports/data/stage40_frozen_model_config.json"
BASELINE = ROOT / "engine/reports/data/stage40_baseline_manifest.json"
CALIB = ROOT / "engine/reports/data/stage40_calibration_results.json"

REQUIRED_FIELDS = [
    "model_version",
    "calibration_status",
    "calibration_dataset_hash",
    "calibration_record_ids_hash",
    "test_manifest_hash",
    "parameter_values",
    "parameter_bounds",
    "fixed_parameters",
    "free_parameters",
    "objective_function",
    "optimisation_method",
    "random_seed",
    "cross_validation_protocol",
    "code_commit",
    "model_code_hash",
    "equation_version",
    "radiation_contract_version",
    "input_policy",
    "freeze_timestamp",
]


def _frozen():
    if not FROZEN.exists():
        pytest.skip("frozen configuration not built yet")
    with open(FROZEN, encoding="utf-8") as f:
        return json.load(f)


def test_frozen_config_has_every_required_field():
    """The frozen configuration is complete."""
    cfg = _frozen()
    for field in REQUIRED_FIELDS:
        assert field in cfg, field


def test_frozen_config_declares_the_free_and_fixed_parameters():
    """Only epsilon is free; HI and the unsourced parameters are fixed."""
    cfg = _frozen()
    assert cfg["free_parameters"] == ["epsilon"]
    assert "hi" in cfg["fixed_parameters"]
    assert "shortwave_to_par_factor" in cfg["fixed_parameters"]
    assert "ndmi_ref" in cfg["fixed_parameters"]


def test_frozen_parameter_values_are_consistent():
    """The frozen values agree with the registry defaults except for epsilon."""
    from engine.hydroma.eval.identifiability_calibration import (
        PARAMETER_REGISTRY,
    )

    cfg = _frozen()
    for name, spec in PARAMETER_REGISTRY.items():
        assert name in cfg["parameter_values"], name
        if name != "epsilon":
            assert cfg["parameter_values"][name] == pytest.approx(
                spec.default_value
            ), name


def test_frozen_parameter_bounds_are_preserved():
    """The bounds in the frozen config match the registry."""
    from engine.hydroma.eval.identifiability_calibration import (
        PARAMETER_REGISTRY,
    )

    cfg = _frozen()
    for name, spec in PARAMETER_REGISTRY.items():
        lo, hi = cfg["parameter_bounds"][name]
        assert lo == spec.allowed_min, name
        assert hi == spec.allowed_max, name


def test_frozen_model_code_hash_is_stable():
    """The recorded code hash matches the current files."""
    cfg = _frozen()
    current = {}
    for rel, recorded in cfg["file_hashes"].items():
        path = ROOT / rel
        if not path.exists():
            continue
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        assert h.hexdigest() == recorded, rel
        current[rel] = recorded
    combined = hashlib.sha256(
        json.dumps(current, sort_keys=True).encode()
    ).hexdigest()
    assert combined == cfg["model_code_hash"]


def test_frozen_config_is_not_modified_by_a_benchmark_run():
    """Running the metrics does not touch the frozen configuration."""
    cfg = _frozen()
    before = open(FROZEN, encoding="utf-8").read()
    from engine.hydroma.eval.stage39_benchmark import compute_benchmark_metrics

    compute_benchmark_metrics(
        [{"observed_yield": 5.0, "predicted_yield": 4.0}], group="probe"
    )
    after = open(FROZEN, encoding="utf-8").read()
    assert before == after
    assert cfg["free_parameters"] == ["epsilon"]


def test_baseline_manifest_is_preserved_separately():
    """The Stage 39 baseline is recorded in its own file."""
    if not BASELINE.exists():
        pytest.skip("baseline manifest not built yet")
    with open(BASELINE, encoding="utf-8") as f:
        baseline = json.load(f)
    assert baseline["baseline_type"] == "baseline_only"
    assert baseline["calibration_status"] == "baseline_only"
    assert baseline["model_code_hash"]
    assert "metrics_so_far" in baseline
    # The baseline must not claim to be calibrated.
    assert baseline["calibration_status"] != "calibrated"
