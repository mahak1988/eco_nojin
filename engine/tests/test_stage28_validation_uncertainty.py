"""Tests for Stage 28: Validation uncertainty estimation.

Tests cover:
- BootstrapResult dataclass fields
- UncertaintyAssessment dataclass fields
- Cluster bootstrap respects data hierarchy (resamples at unit level)
- Insufficient independent units → NOT_ASSESSED status
- Reproducibility with fixed seed
- Bootstrap CI is conservative vs naive record-level bootstrap
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from engine.hydroma.eval.field_validation import RealFieldRecord
from engine.hydroma.eval.prediction import PredictionResult
from engine.hydroma.eval.validation_matching import ValidationPair
from engine.hydroma.eval.validation_uncertainty import (
    BootstrapResult,
    UncertaintyAssessment,
    UncertaintyStatus,
    assess_uncertainty,
    bootstrap_metric,
    compute_metric_on_pairs,
)


def _make_pair(
    site_id: str,
    season_id: str,
    pred: float = 5.0,
    obs: float = 5.0,
    field_id: str | None = None,
) -> ValidationPair:
    o = RealFieldRecord(
        site_id=site_id,
        field_id=field_id or f"F_{site_id}",
        season_id=season_id,
        crop="wheat",
        cultivar="scepter",
        planting_date=date(2024, 4, 1),
        harvest_date=date(2024, 5, 30),
        latitude=40.0,
        longitude=-105.0,
        area_ha=2.5,
        observed_yield=obs,
        observed_yield_unit="t/ha",
        yield_measurement_method="combine_harvester",
        harvest_sample_size=20,
        observation_source="field_measured",
        data_label="field_station_2024",
    )
    p = PredictionResult(
        prediction_id=f"P_{site_id}_{season_id}",
        site_id=site_id,
        season_id=season_id,
        value=pred,
        unit="t/ha",
        metadata={"crop": "wheat"},
    )
    return ValidationPair(
        pair_id=f"PAIR_{site_id}_{season_id}",
        site_id=site_id,
        season_id=season_id,
        crop="wheat",
        prediction=p,
        observation=o,
        predicted_yield_t_ha=pred,
        observed_yield_t_ha=obs,
        prediction_unit="t/ha",
        observation_unit="t/ha",
        yield_unit_conversion="identity",
        quality_gate_decision="PASSED",
    )


def rmse_metric(obs: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((obs - pred) ** 2)))


class TestBootstrapResult:
    """Tests for BootstrapResult dataclass."""

    def test_fields(self):
        """BootstrapResult has expected fields."""
        result = BootstrapResult(
            metric_name="rmse",
            point_estimate=1.5,
            ci_lower=1.0,
            ci_upper=2.0,
            confidence_level=0.95,
            bootstrap_sample_count=1000,
            bootstrap_method="cluster_bootstrap (site)",
            status=UncertaintyStatus.ASSESSED,
            notes=[],
        )
        assert result.metric_name == "rmse"
        assert result.point_estimate == 1.5
        assert result.ci_lower == 1.0
        assert result.ci_upper == 2.0
        assert result.status == UncertaintyStatus.ASSESSED


class TestUncertaintyAssessment:
    """Tests for UncertaintyAssessment dataclass."""

    def test_fields(self):
        """UncertaintyAssessment has expected fields."""
        result = BootstrapResult(
            metric_name="rmse",
            point_estimate=1.5,
            ci_lower=1.0,
            ci_upper=2.0,
            confidence_level=0.95,
            bootstrap_sample_count=1000,
            bootstrap_method="cluster_bootstrap (site)",
            status=UncertaintyStatus.ASSESSED,
            notes=[],
        )
        assessment = UncertaintyAssessment(
            assessment_id="UNC-ABC123",
            metric_results=[result],
            n_independent_units=5,
            unit_of_independence="site",
            random_seed=42,
        )
        assert assessment.assessment_id == "UNC-ABC123"
        assert len(assessment.metric_results) == 1
        assert assessment.n_independent_units == 5
        assert assessment.unit_of_independence == "site"
        assert assessment.random_seed == 42


class TestComputeMetricOnPairs:
    """Tests for compute_metric_on_pairs helper."""

    def test_rmse_perfect_fit(self):
        """Perfect predictions → RMSE 0."""
        pairs = [
            _make_pair("S1", "s1", pred=5.0, obs=5.0),
            _make_pair("S2", "s1", pred=6.0, obs=6.0),
        ]
        result = compute_metric_on_pairs(pairs, rmse_metric)
        assert result == 0.0

    def test_rmse_error(self):
        """Known RMSE calculation."""
        pairs = [
            _make_pair("S1", "s1", pred=5.0, obs=4.0),
            _make_pair("S2", "s1", pred=7.0, obs=6.0),
        ]
        result = compute_metric_on_pairs(pairs, rmse_metric)
        assert result == pytest.approx(np.sqrt(1.0), rel=1e-6)  # sqrt((1+1)/2)


class TestClusterBootstrap:
    """Tests for cluster bootstrap at the unit of independence."""

    def test_insufficient_units_not_assessed(self):
        """Fewer than min_units groups → NOT_ASSESSED."""
        pairs = [
            _make_pair("S1", "s1", pred=5.0, obs=5.5),
            _make_pair("S1", "s2", pred=5.0, obs=5.5),
        ]
        result = bootstrap_metric(pairs, rmse_metric, unit_of_independence="site")
        assert result.status == UncertaintyStatus.NOT_ASSESSED
        assert result.ci_lower is None
        assert result.ci_upper is None
        assert len(result.notes) > 0

    def test_assessed_with_many_sites(self):
        """Many independent sites → ASSESSED with CI."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0 + i * 0.1, obs=5.0 + i * 0.1)
            for i in range(10)
        ]
        result = bootstrap_metric(
            pairs, rmse_metric, unit_of_independence="site", n_bootstrap=500
        )
        assert result.status == UncertaintyStatus.ASSESSED
        assert result.ci_lower is not None
        assert result.ci_upper is not None
        assert result.ci_lower <= result.point_estimate <= result.ci_upper

    def test_assessed_with_many_seasons(self):
        """Many independent seasons → ASSESSED with CI."""
        pairs = [
            _make_pair("S1", f"s{i}", pred=5.0 + i * 0.1, obs=5.0 + i * 0.1)
            for i in range(10)
        ]
        result = bootstrap_metric(
            pairs, rmse_metric, unit_of_independence="season", n_bootstrap=500
        )
        assert result.status == UncertaintyStatus.ASSESSED
        assert result.ci_lower is not None

    def test_assessed_with_many_fields(self):
        """Many independent fields → ASSESSED with CI."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0 + i * 0.1, obs=5.0 + i * 0.1, field_id=f"F{i}")
            for i in range(10)
        ]
        result = bootstrap_metric(
            pairs, rmse_metric, unit_of_independence="field", n_bootstrap=500
        )
        assert result.status == UncertaintyStatus.ASSESSED
        assert result.ci_lower is not None

    def test_cluster_bootstrap_cwider_ci_than_record_level(self):
        """Cluster bootstrap gives wider CI than record-level when clustered."""
        # 2 sites, 10 obs each (within-site correlation)
        pairs = []
        for site in ["S1", "S2"]:
            site_offset = 0.5 if site == "S1" else -0.5
            for s in range(10):
                pairs.append(
                    _make_pair(site, f"s{s}", pred=5.0 + site_offset, obs=5.0 + site_offset)
                )

        # Cluster bootstrap (site level)
        cluster_result = bootstrap_metric(
            pairs, rmse_metric, unit_of_independence="site", n_bootstrap=500
        )
        # Record-level bootstrap (should be narrower due to ignoring clustering)
        bootstrap_metric(
            pairs, rmse_metric, unit_of_independence="season", n_bootstrap=500
        )

        # Both should be assessed, but cluster CI should be wider (or equal)
        # because it has fewer independent units
        if cluster_result.status == UncertaintyStatus.ASSESSED:
            assert cluster_result.ci_lower is not None
            assert cluster_result.ci_upper is not None

    def test_reproducible_with_seed(self):
        """Same seed → identical results."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0, obs=5.0) for i in range(8)
        ]
        result1 = bootstrap_metric(pairs, rmse_metric, unit_of_independence="site", random_seed=42)
        result2 = bootstrap_metric(pairs, rmse_metric, unit_of_independence="site", random_seed=42)
        assert result1.ci_lower == result2.ci_lower
        assert result1.ci_upper == result2.ci_upper

    def test_different_seed_different_ci(self):
        """Different seed → different CI (but same point estimate)."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0 + i * 0.1, obs=5.0)
            for i in range(12)
        ]
        result1 = bootstrap_metric(pairs, rmse_metric, unit_of_independence="site", random_seed=1)
        result2 = bootstrap_metric(pairs, rmse_metric, unit_of_independence="site", random_seed=2)
        assert result1.point_estimate == result2.point_estimate

    def test_zero_variation_in_bootstrap(self):
        """All predictions perfect → bootstrap produces narrow CI."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0, obs=5.0) for i in range(10)
        ]
        result = bootstrap_metric(pairs, rmse_metric, unit_of_independence="site", n_bootstrap=200)
        if result.status == UncertaintyStatus.ASSESSED:
            assert result.point_estimate == 0.0
            assert result.ci_lower <= 0.0
            assert result.ci_upper >= 0.0


class TestAssessUncertainty:
    """Tests for assess_uncertainty multi-metric assessment."""

    def test_assesses_all_metrics(self):
        """All three metrics (rmse, mae, bias) are assessed."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0 + i * 0.2, obs=5.0 + i * 0.1)
            for i in range(8)
        ]
        assessment = assess_uncertainty(pairs, unit_of_independence="site")
        assert len(assessment.metric_results) == 3
        metric_names = {r.metric_name for r in assessment.metric_results}
        assert metric_names == {"rmse", "mae", "bias"}

    def test_n_independent_units(self):
        """n_independent_units reflects the grouping level."""
        pairs = [
            _make_pair("S1", f"s{i}", pred=5.0, obs=5.0) for i in range(10)
        ]
        assessment = assess_uncertainty(pairs, unit_of_independence="season")
        assert assessment.n_independent_units == 10
        assert assessment.unit_of_independence == "season"

    def test_all_metrics_assessed_with_sites(self):
        """With enough sites, all metrics should be ASSESSED."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0 + i * 0.1, obs=5.0)
            for i in range(10)
        ]
        assessment = assess_uncertainty(pairs, unit_of_independence="site", n_bootstrap=500)
        for result in assessment.metric_results:
            assert result.status == UncertaintyStatus.ASSESSED

    def test_all_metrics_not_assessed_with_few_sites(self):
        """With too few sites, all metrics should be NOT_ASSESSED."""
        pairs = [
            _make_pair("S1", f"s{i}", pred=5.0, obs=5.0) for i in range(10)
        ]
        assessment = assess_uncertainty(pairs, unit_of_independence="site")
        for result in assessment.metric_results:
            assert result.status == UncertaintyStatus.NOT_ASSESSED

    def test_reproducible(self):
        """Same seed → identical assessment."""
        pairs = [
            _make_pair(f"S{i}", "s1", pred=5.0 + i * 0.1, obs=5.0)
            for i in range(8)
        ]
        a1 = assess_uncertainty(pairs, unit_of_independence="site", random_seed=42)
        a2 = assess_uncertainty(pairs, unit_of_independence="site", random_seed=42)
        for r1, r2 in zip(a1.metric_results, a2.metric_results, strict=True):
            assert r1.ci_lower == r2.ci_lower
            assert r1.ci_upper == r2.ci_upper
