"""Tests for Stage 28: Sample adequacy assessment.

Tests cover:
- Spatial generalization requires >= 3 sites
- Temporal generalization requires >= 2 seasons
- Spatial+temporal requires both
- None target requires at least 1 pair
- No single pair-count threshold determines validation status
- 5 pairs from a single site do not validate spatial generalization
"""

from __future__ import annotations

from datetime import date

from engine.hydroma.eval.field_validation import RealFieldRecord
from engine.hydroma.eval.prediction import PredictionResult
from engine.hydroma.eval.validation_protocol import (
    EvaluationTarget,
    ValidationProtocol,
)
from engine.hydroma.eval.validation_report import (
    SampleAdequacyStatus,
    assess_sample_adequacy,
    produce_validation_report,
)


def _make_obs(
    site_id="S1",
    season_id="s1",
    crop="wheat",
    yield_t_ha=6.5,
) -> RealFieldRecord:
    return RealFieldRecord(
        site_id=site_id,
        field_id="F1",
        season_id=season_id,
        crop=crop,
        cultivar="scepter",
        planting_date=date(2024, 4, 1),
        harvest_date=date(2024, 5, 30),
        latitude=40.0,
        longitude=-105.0,
        area_ha=2.5,
        observed_yield=yield_t_ha,
        observed_yield_unit="t/ha",
        yield_measurement_method="combine_harvester",
        harvest_sample_size=20,
        observation_source="field_measured",
        data_label="field_station_2024",
    )


def _make_pred(
    site_id="S1",
    season_id="s1",
    crop="wheat",
    value=6.3,
    prediction_id="P001",
) -> PredictionResult:
    return PredictionResult(
        prediction_id=prediction_id,
        site_id=site_id,
        season_id=season_id,
        value=value,
        unit="t/ha",
        metadata={"crop": crop},
    )


class TestSpatialAdequacy:
    """Spatial generalization requires >= 3 independent sites."""

    def test_two_sites_insufficient(self):
        """2 sites → INSUFFICIENT for SPATIAL."""
        status, limitations = assess_sample_adequacy(
            n_pairs=10, n_sites=2, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT
        assert any("site" in lim.lower() for lim in limitations)

    def test_three_sites_adequate(self):
        """3 sites → ADEQUATE for SPATIAL."""
        status, _ = assess_sample_adequacy(
            n_pairs=10, n_sites=3, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL,
        )
        assert status == SampleAdequacyStatus.ADEQUATE

    def test_five_sites_from_single_site_blocked(self):
        """5 pairs from 1 site → INSUFFICIENT for SPATIAL."""
        status, _ = assess_sample_adequacy(
            n_pairs=5, n_sites=1, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT

    def test_soft_note_n_pairs_does_not_affect_status(self):
        """< 10 pairs with >= 3 sites → still ADEQUATE for SPATIAL."""
        status, notes = assess_sample_adequacy(
            n_pairs=5, n_sites=3, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL,
        )
        assert status == SampleAdequacyStatus.ADEQUATE
        assert len(notes) > 0  # soft note about pair count


class TestTemporalAdequacy:
    """Temporal generalization requires >= 2 independent seasons."""

    def test_one_season_insufficient(self):
        """1 season → INSUFFICIENT for TEMPORAL."""
        status, _ = assess_sample_adequacy(
            n_pairs=10, n_sites=1, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.TEMPORAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT

    def test_two_seasons_adequate(self):
        """2 seasons → ADEQUATE for TEMPORAL."""
        status, _ = assess_sample_adequacy(
            n_pairs=10, n_sites=1, n_seasons=2, n_crops=1,
            evaluation_target=EvaluationTarget.TEMPORAL,
        )
        assert status == SampleAdequacyStatus.ADEQUATE


class TestSpatialAndTemporalAdequacy:
    """Spatial+temporal requires >= 3 sites AND >= 2 seasons."""

    def test_insufficient_sites(self):
        """2 sites, 2 seasons → INSUFFICIENT."""
        status, _ = assess_sample_adequacy(
            n_pairs=15, n_sites=2, n_seasons=2, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL_AND_TEMPORAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT

    def test_insufficient_seasons(self):
        """5 sites, 1 season → INSUFFICIENT."""
        status, _ = assess_sample_adequacy(
            n_pairs=15, n_sites=5, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL_AND_TEMPORAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT

    def test_adequate_both(self):
        """5 sites, 3 seasons → ADEQUATE."""
        status, _ = assess_sample_adequacy(
            n_pairs=20, n_sites=5, n_seasons=3, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL_AND_TEMPORAL,
        )
        assert status == SampleAdequacyStatus.ADEQUATE


class TestNoneTargetAdequacy:
    """NONE target (reproducibility) requires only 1 pair."""

    def test_one_pair_adequate(self):
        """1 pair with NONE target → ADEQUATE."""
        status, _ = assess_sample_adequacy(
            n_pairs=1, n_sites=1, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.NONE,
        )
        assert status == SampleAdequacyStatus.ADEQUATE

    def test_zero_pairs_insufficient(self):
        """0 pairs with NONE target → INSUFFICIENT."""
        status, _ = assess_sample_adequacy(
            n_pairs=0, n_sites=0, n_seasons=0, n_crops=0,
            evaluation_target=EvaluationTarget.NONE,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT


class TestNoUniversalThreshold:
    """Critical test: no single pair-count threshold determines validation."""

    def test_five_pairs_single_site_not_validated(self):
        """5 pairs from 1 site with SPATIAL protocol → NOT validated."""
        preds = [_make_pred(site_id="S1", season_id=f"s{i}", value=5.3, prediction_id=f"P{i}")
                 for i in range(5)]
        obs = [_make_obs(site_id="S1", season_id=f"s{i}") for i in range(5)]
        protocol = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="spatial test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S1"],
            seasons_in_scope=[f"s{i}" for i in range(5)],
            minimum_sites=3,
            minimum_seasons=1,
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, protocol=protocol
        )
        assert report.sample_adequacy_status == "insufficient"
        assert report.external_validation_status == "partially_evaluated"
        # CRITICAL: must NOT be validated_external
        assert (
            report.external_validation_status != "validated_external"
        )

    def test_100_pairs_single_site_not_validated_spatial(self):
        """100 pairs from 1 site → still NOT validated for SPATIAL generalization."""
        preds = [_make_pred(site_id="S1", season_id=f"s{i}", value=5.3, prediction_id=f"P{i}")
                 for i in range(100)]
        obs = [_make_obs(site_id="S1", season_id=f"s{i}") for i in range(100)]
        protocol = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="spatial test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S1"],
            seasons_in_scope=[f"s{i}" for i in range(100)],
            minimum_sites=3,
            minimum_seasons=1,
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, protocol=protocol
        )
        assert report.sample_adequacy_status == "insufficient"
        assert report.external_validation_status == "partially_evaluated"

    def test_few_pairs_many_sites_can_be_adequate(self):
        """5 pairs from 3 sites → ADEQUATE for SPATIAL (pair count is soft)."""
        preds = []
        obs = []
        for i in range(5):
            site = f"S{i}" if i < 3 else f"S{i % 3}"
            p = _make_pred(
                site_id=site, season_id=f"s{i}", value=5.3, prediction_id=f"P{i}"
            )
            preds.append(p)
            o = _make_obs(site_id=site, season_id=f"s{i}")
            obs.append(o)
        protocol = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="spatial test",
            crops_in_scope=["wheat"],
            sites_in_scope=["S0", "S1", "S2"],
            seasons_in_scope=[f"s{i}" for i in range(5)],
            minimum_sites=3,
            minimum_seasons=1,
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, protocol=protocol
        )
        assert report.sample_adequacy_status == "adequate"
        assert report.external_validation_status == "validated_external"
