"""Stage 36 — Calibration, split, and uncertainty tests.

Tests the Stage 36 modules without requiring imports from
engine/hydroma/models/ or engine/hydroma/simulation/ (which have a
filesystem visibility limitation in this environment).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

from engine.hydroma.eval.benchmark_split_manifest import (
    create_split_manifest,
    load_split_manifest,
    verify_split,
)
from engine.hydroma.eval.calibration_parameter_registry import (
    ParameterGroup,
    ParameterStatus,
    build_registry,
)
from engine.hydroma.eval.hyrue_uncertainty_analysis import (
    UncertaintyResult,
    cluster_bootstrap_uncertainty,
)
from engine.hydroma.eval.pilot_error_analysis import (
    analyze_pilot_error,
    compute_hyrue_component_breakdown,
)

# ---------------------------------------------------------------------------
# Split manifest tests
# ---------------------------------------------------------------------------

def test_split_manifest_creation():
    """Manifest is created with correct structure and counts."""
    manifest = create_split_manifest()
    assert manifest["dataset_id"] == "CIMMYT_EASTERN_INDIA_WHEAT"
    assert manifest["split_version"] == "stage36_v1"
    assert manifest["total_record_count"] == 5689
    assert manifest["development_record_count"] == 3967
    assert manifest["test_record_count"] == 1722
    assert len(manifest["development_districts"]) == 7
    assert len(manifest["test_districts"]) == 3
    assert "manifest_hash" in manifest


def test_split_no_district_overlap():
    """No district appears in both development and test sets."""
    manifest = load_split_manifest()
    dev = set(manifest["development_districts"])
    test = set(manifest["test_districts"])
    assert dev & test == set()


def test_split_no_record_overlap():
    """No record ID appears in both development and test sets."""
    manifest = load_split_manifest()
    dev_ids = set(manifest["development_record_ids"])
    test_ids = set(manifest["test_record_ids"])
    assert dev_ids & test_ids == set()


def test_split_manifest_hash_verification():
    """Manifest hash matches recomputed hash."""
    manifest = load_split_manifest()
    verification = verify_split(manifest)
    assert verification["verified"] is True
    assert verification["manifest_hash_matches"] is True
    assert verification["no_id_overlap"] is True
    assert verification["no_district_overlap"] is True


def test_split_all_districts_accounted():
    """All 10 districts are in either dev or test."""
    manifest = load_split_manifest()
    all_districts = set(manifest["development_districts"]) | set(
        manifest["test_districts"]
    )
    df = pd.read_excel(
        "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
    )
    data_districts = set(df["District"].unique())
    assert all_districts == data_districts


# ---------------------------------------------------------------------------
# Parameter registry tests
# ---------------------------------------------------------------------------

def test_registry_has_17_parameters():
    """Registry contains all 17 expected parameters."""
    registry = build_registry()
    assert registry.summary()["total_parameters"] == 17


def test_registry_status_counts():
    """Registry has correct status distribution."""
    registry = build_registry()
    summary = registry.summary()
    assert summary["status_counts"]["calibratable"] == 10
    assert summary["status_counts"]["uncalibrated"] == 6
    assert summary["status_counts"]["fixed"] == 1


def test_ewsi_weights_sum_to_one():
    """EWSI weights sum to 1.0."""
    registry = build_registry()
    ndmi = registry.get_value("ewsi_weight_ndmi")
    vpd = registry.get_value("ewsi_weight_vpd")
    soil = registry.get_value("ewsi_weight_soil")
    assert abs(ndmi + vpd + soil - 1.0) < 1e-6


def test_ewsi_weights_non_negative():
    """EWSI weights are non-negative."""
    registry = build_registry()
    for name in ("ewsi_weight_ndmi", "ewsi_weight_vpd", "ewsi_weight_soil"):
        val = registry.get_value(name)
        assert val >= 0.0


def test_parameter_bounds_respected():
    """All parameter values are within allowed bounds."""
    registry = build_registry()
    for name, entry in registry.get_all().items():
        val = entry.parameter_value
        if entry.allowed_min is not None:
            assert val >= entry.allowed_min, (
                f"{name}={val} below min={entry.allowed_min}"
            )
        if entry.allowed_max is not None:
            assert val <= entry.allowed_max, (
                f"{name}={val} above max={entry.allowed_max}"
            )


def test_parameter_update_with_traceability():
    """Parameter update records calibration metadata."""
    registry = build_registry()
    registry.get_value("epsilon")
    registry.update_value(
        parameter_name="epsilon",
        new_value=2.5,
        calibration_method="grid_search",
        calibration_dataset="CIMMYT_dev",
        calibration_version="stage36_v1",
        rationale="Optimized on development districts",
    )
    entry = registry.get("epsilon")
    assert entry.parameter_value == 2.5
    assert entry.parameter_status == ParameterStatus.CALIBRATED
    assert entry.calibration_method == "grid_search"
    assert entry.calibration_dataset == "CIMMYT_dev"
    assert entry.calibration_version == "stage36_v1"


def test_parameter_update_rejects_out_of_bounds():
    """Parameter update outside bounds raises ValueError."""
    registry = build_registry()
    with pytest.raises(ValueError):
        registry.update_value(
            parameter_name="epsilon",
            new_value=10.0,  # above allowed_max=5.0
        )


# ---------------------------------------------------------------------------
# Pilot error analysis tests
# ---------------------------------------------------------------------------

def test_pilot_error_computation():
    """Pilot error analysis computes correct error metrics."""
    diagnosis = analyze_pilot_error()
    assert diagnosis.observed_yield == 6.68
    assert abs(diagnosis.predicted_yield - 10.899) < 0.01
    assert abs(diagnosis.absolute_error - 4.219) < 0.01
    assert abs(diagnosis.relative_error_percent - 63.16) < 1.0


def test_pilot_error_has_component_issues():
    """Pilot error analysis identifies component issues."""
    diagnosis = analyze_pilot_error()
    assert len(diagnosis.component_issues) >= 3
    assert len(diagnosis.primary_drivers) >= 1
    assert len(diagnosis.recommendations) >= 1


def test_pilot_error_par_primary_driver():
    """PAR unit error is identified as primary driver."""
    diagnosis = analyze_pilot_error()
    drivers_text = " ".join(diagnosis.primary_drivers)
    assert "PAR" in drivers_text


def test_hyrue_component_breakdown():
    """Component breakdown returns expected structure."""
    breakdown = compute_hyrue_component_breakdown()
    assert "f_ipar" in breakdown
    assert "f_water" in breakdown
    assert "yield_with_shortwave_as_par_t_ha" in breakdown
    assert "observed_yield_t_ha" in breakdown
    assert abs(breakdown["observed_yield_t_ha"] - 6.68) < 0.01


# ---------------------------------------------------------------------------
# Uncertainty analysis tests
# ---------------------------------------------------------------------------

def test_uncertainty_with_sufficient_districts():
    """Cluster bootstrap works with >= 3 districts."""
    np.random.seed(42)
    records = []
    districts = ["Buxar", "Muzaffarpur", "Rohtas", "Begusarai", "Bhojpur"]
    for i in range(30):
        obs = np.random.uniform(3, 8)
        pred = obs + np.random.normal(0, 1.0)
        records.append({
            "district": districts[i % len(districts)],
            "observed_yield": obs,
            "predicted_yield": pred,
            "computation_status": "success",
        })

    result = cluster_bootstrap_uncertainty(records, n_bootstrap=100)
    assert isinstance(result, UncertaintyResult)
    assert result.method == "cluster_bootstrap"
    assert result.n_districts == 5
    assert result.n_bootstrap_samples == 100
    assert result.blocked_reason is None
    assert result.rmse_mean is not None
    assert result.mae_mean is not None
    assert result.bias_mean is not None


def test_uncertainty_blocked_insufficient_districts():
    """Bootstrap blocked with < 3 districts."""
    records = []
    for i in range(10):
        records.append({
            "district": "Buxar",
            "observed_yield": 5.0 + i * 0.1,
            "predicted_yield": 5.5 + i * 0.1,
            "computation_status": "success",
        })

    result = cluster_bootstrap_uncertainty(records)
    assert result.blocked_reason is not None
    assert result.rmse_mean is None
    assert "district" in result.blocked_reason.lower()


def test_uncertainty_blocked_no_successful_records():
    """Bootstrap blocked with no successful records."""
    records = []
    for _i in range(10):
        records.append({
            "district": "Buxar",
            "observed_yield": None,
            "predicted_yield": None,
            "computation_status": "failed",
        })

    result = cluster_bootstrap_uncertainty(records)
    assert result.blocked_reason is not None
    assert result.rmse_mean is None


# ---------------------------------------------------------------------------
# Registry serialization tests
# ---------------------------------------------------------------------------

def test_registry_to_dict():
    """Registry serializes to dict correctly."""
    registry = build_registry()
    d = registry.to_dict()
    assert len(d) == 17
    for _name, entry in d.items():
        assert "parameter_value" in entry
        assert "unit" in entry
        assert "parameter_status" in entry
        assert "parameter_source" in entry


def test_registry_get_by_group():
    """Registry can filter by parameter group."""
    registry = build_registry()
    ewsii_weights = registry.get_by_group(ParameterGroup.EWSI_WEIGHTS)
    assert len(ewsii_weights) == 3
    assert "ewsi_weight_ndmi" in ewsii_weights
    assert "ewsi_weight_vpd" in ewsii_weights
    assert "ewsi_weight_soil" in ewsii_weights
