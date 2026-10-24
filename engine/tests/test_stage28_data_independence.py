"""Tests for Stage 28: Data independence and leakage controls.

Tests cover:
- leakage_check detects calibration/validation/test overlaps
- Site-level independence (spatial generalization)
- Season-level independence (temporal generalization)
- Duplicate records detection
- Cross-dataset independence verification
"""

from __future__ import annotations

from datetime import date

from engine.hydroma.eval.field_validation import RealFieldRecord
from engine.hydroma.eval.prediction import PredictionResult
from engine.hydroma.eval.validation_matching import (
    ValidationSplit,
    split_for_validation,
)
from engine.hydroma.eval.validation_report import produce_validation_report


def _make_obs(
    site_id="SITE001",
    season_id="wheat_2024",
    crop="wheat",
    yield_t_ha=6.5,
    **kw,
) -> RealFieldRecord:
    defaults = {
        "site_id": site_id,
        "field_id": "FIELD_A",
        "season_id": season_id,
        "crop": crop,
        "cultivar": "scepter",
        "planting_date": date(2024, 4, 1),
        "harvest_date": date(2024, 5, 30),
        "latitude": 35.0,
        "longitude": 50.0,
        "area_ha": 2.5,
        "observed_yield": yield_t_ha,
        "observed_yield_unit": "t/ha",
        "yield_measurement_method": "combine_harvester",
        "harvest_sample_size": 20,
        "observation_source": "field_measured",
        "observation_source_id": "study_2024",
        "data_label": "field_station_2024",
    }
    defaults.update(kw)
    return RealFieldRecord(**defaults)


class TestLeakageCheck:
    """Tests for ValidationSplit.leakage_check()."""

    def test_clean_split_no_violations(self):
        """A split with no overlapping sites has zero violations."""
        split = ValidationSplit(
            calibration=[_make_obs(site_id="S1", season_id="s1")],
            validation=[_make_obs(site_id="S2", season_id="s1")],
            test=[_make_obs(site_id="S3", season_id="s1")],
        )
        assert split.leakage_check() == []

    def test_cal_val_overlap_detected(self):
        """Overlap between calibration and validation is detected."""
        split = ValidationSplit(
            calibration=[_make_obs(site_id="S1", season_id="s1")],
            validation=[_make_obs(site_id="S1", season_id="s1")],
            test=[_make_obs(site_id="S3", season_id="s1")],
        )
        violations = split.leakage_check()
        assert len(violations) > 0
        assert any("calibration and validation" in v for v in violations)

    def test_cal_test_overlap_detected(self):
        """Overlap between calibration and test is detected."""
        split = ValidationSplit(
            calibration=[_make_obs(site_id="S1", season_id="s1")],
            validation=[_make_obs(site_id="S2", season_id="s1")],
            test=[_make_obs(site_id="S1", season_id="s1")],
        )
        violations = split.leakage_check()
        assert any("calibration and test" in v for v in violations)

    def test_val_test_overlap_detected(self):
        """Overlap between validation and test is detected."""
        split = ValidationSplit(
            calibration=[_make_obs(site_id="S1", season_id="s1")],
            validation=[_make_obs(site_id="S2", season_id="s1")],
            test=[_make_obs(site_id="S2", season_id="s1")],
        )
        violations = split.leakage_check()
        assert any("validation and test" in v for v in violations)

    def test_three_way_overlap_detected(self):
        """Three-way overlap is detected."""
        rec = _make_obs(site_id="S1", season_id="s1")
        split = ValidationSplit(
            calibration=[rec.model_copy()],
            validation=[rec.model_copy()],
            test=[rec.model_copy()],
        )
        violations = split.leakage_check()
        assert any("all three" in v for v in violations)

    def test_no_overlap_different_sites(self):
        """Different sites → no leakage."""
        split = ValidationSplit(
            calibration=[_make_obs(site_id="S1", season_id="s1")],
            validation=[_make_obs(site_id="S2", season_id="s2")],
            test=[_make_obs(site_id="S3", season_id="s3")],
        )
        assert split.leakage_check() == []

    def test_same_site_different_season_no_leakage(self):
        """Same site, different season → still leakage (site_id,season_id)."""
        split = ValidationSplit(
            calibration=[_make_obs(site_id="S1", season_id="s1")],
            validation=[_make_obs(site_id="S1", season_id="s2")],
            test=[_make_obs(site_id="S3", season_id="s3")],
        )
        # (S1,s1) only in calibration, (S1,s2) only in validation — no overlap
        assert split.leakage_check() == []

    def test_empty_split_no_violations(self):
        """Empty split has no violations."""
        split = ValidationSplit()
        assert split.leakage_check() == []


class TestSiteLevelIndependence:
    """Tests for spatial generalization: site-level independence."""

    def test_split_by_site_separates_sites(self):
        """Site-based split ensures sites don't appear in multiple splits."""
        recs = [_make_obs(site_id=f"S{i}", season_id="s1") for i in range(12)]
        split = split_for_validation(recs, method="site", site_frac=0.3, seed=42)

        cal_sites = {r.site_id for r in split.calibration}
        val_sites = {r.site_id for r in split.validation}
        test_sites = {r.site_id for r in split.test}

        assert len(cal_sites & val_sites) == 0
        assert len(cal_sites & test_sites) == 0
        assert len(val_sites & test_sites) == 0

    def test_split_preserves_all_records(self):
        """All accepted records appear in exactly one split."""
        recs = [_make_obs(site_id=f"S{i}", season_id="s1") for i in range(10)]
        split = split_for_validation(recs, method="site", seed=42)

        total = len(split.calibration) + len(split.validation) + len(split.test)
        assert total == 10

    def test_too_few_sites_for_spatial(self):
        """Fewer than 3 independent sites → cannot claim spatial generalization."""
        recs = [_make_obs(site_id="S1", season_id=f"s{i}") for i in range(5)]
        split = split_for_validation(recs, method="site", seed=42, site_frac=0.0)
        # All go to validation/test, no calibration
        assert len(split.calibration) == 0
        # But only 1 site — spatial generalization impossible
        assert len({r.site_id for r in split.validation + split.test}) == 1


class TestSeasonLevelIndependence:
    """Tests for temporal generalization: season-level independence."""

    def test_split_by_season_separates_seasons(self):
        """Season-based split ensures seasons don't overlap."""
        recs = [_make_obs(site_id="S1", season_id=f"s{i}") for i in range(12)]
        split = split_for_validation(recs, method="season", site_frac=0.3, seed=42)

        cal_seasons = {r.season_id for r in split.calibration}
        val_seasons = {r.season_id for r in split.validation}
        test_seasons = {r.season_id for r in split.test}

        assert len(cal_seasons & val_seasons) == 0
        assert len(cal_seasons & test_seasons) == 0
        assert len(val_seasons & test_seasons) == 0

    def test_too_few_seasons_for_temporal(self):
        """Fewer than 2 seasons → cannot claim temporal generalization."""
        recs = [_make_obs(site_id="S1", season_id="s1") for i in range(5)]
        split = split_for_validation(recs, method="season", seed=42, site_frac=0.0)
        assert len({r.season_id for r in split.validation + split.test}) == 1


class TestDataIndependenceInReport:
    """Tests that produce_validation_report correctly flags independence."""

    def test_no_protocol_unknown_independence(self):
        """Without protocol or split → independence is UNKNOWN."""
        preds = [
            PredictionResult(
                prediction_id=f"P{i}", site_id=f"S{i}", season_id="s1",
                value=5.0, unit="t/ha", metadata={"crop": "wheat"},
            )
            for i in range(5)
        ]
        obs = [_make_obs(site_id=f"S{i}", season_id="s1") for i in range(5)]
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.evaluation_independence_status == "unknown"

    def test_leakage_makes_not_independent(self):
        """Leakage in split → independence is NOT_INDEPENDENT."""
        preds = [
            PredictionResult(
                prediction_id=f"P{i}", site_id=f"S{i}", season_id="s1",
                value=5.0, unit="t/ha", metadata={"crop": "wheat"},
            )
            for i in range(5)
        ]
        obs = [_make_obs(site_id=f"S{i}", season_id="s1") for i in range(5)]

        # Create a leaky split manually
        split = ValidationSplit(
            calibration=[obs[0]],
            validation=[obs[0]],
            test=[obs[1]],
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, split=split
        )
        assert report.evaluation_independence_status == "not_independent"
        assert report.data_leakage_status == "potential_leakage"
        assert len(report.leakage_violations) > 0

    def test_clean_split_independent(self):
        """Clean split → independence is INDEPENDENT + CLEAN leakage."""
        preds = [
            PredictionResult(
                prediction_id=f"P{i}", site_id=f"S{i}", season_id="s1",
                value=5.0, unit="t/ha", metadata={"crop": "wheat"},
            )
            for i in range(6)
        ]
        obs = [_make_obs(site_id=f"S{i}", season_id="s1") for i in range(6)]
        split = split_for_validation(obs, method="site", seed=42)
        report = produce_validation_report(
            predictions=preds, observations=obs, split=split
        )
        assert report.evaluation_independence_status == "independent"
        assert report.data_leakage_status == "clean"
