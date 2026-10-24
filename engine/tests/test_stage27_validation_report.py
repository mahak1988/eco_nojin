"""Tests for Stage 27: End-to-end validation report.

Tests cover:
- ValidationOutput structure and fields
- determine_external_validation_status rules (no hardcoded 5-pair threshold)
- produce_validation_report: full pipeline from predictions+observations
- to_dict serialization
- Status separation (computation vs validation)
- Synthetic data detection
- Data leakage detection in report
- Independent status dimensions
"""

from __future__ import annotations

from datetime import date

from engine.hydroma.eval.field_validation import RealFieldRecord
from engine.hydroma.eval.prediction import PredictionResult
from engine.hydroma.eval.validation_matching import (
    split_for_validation,
)
from engine.hydroma.eval.validation_protocol import (
    EvaluationTarget,
    ValidationProtocol,
)
from engine.hydroma.eval.validation_report import (
    DataAvailabilityStatus,
    DataLeakageStatus,
    DataQualityStatus,
    EvaluationIndependenceStatus,
    ExternalValidationStatus,
    SampleAdequacyStatus,
    assess_sample_adequacy,
    determine_external_validation_status,
    produce_validation_report,
)


def _make_obs(
    site_id="SITE001",
    season_id="wheat_2024",
    crop="wheat",
    yield_t_ha=6.5,
    data_label="field_station_2024",
    quality_gate_decision="ACCEPTED",
    observation_source="field_measured",
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
        "yield_measurement_method": "combine_harvster",
        "harvest_sample_size": 20,
        "observation_source": observation_source,
        "observation_source_id": "study_2024",
        "data_label": data_label,
    }
    defaults.update(kw)
    rec = RealFieldRecord(**defaults)
    if quality_gate_decision:
        rec.quality_gate_decision = quality_gate_decision
    return rec


def _make_pred(
    site_id="SITE001",
    season_id="wheat_2024",
    crop="wheat",
    value=6.3,
    prediction_id="PRED-001",
    **kw,
) -> PredictionResult:
    defaults = {
        "prediction_id": prediction_id,
        "site_id": site_id,
        "season_id": season_id,
        "value": value,
        "unit": "t/ha",
        "model_name": "HY-RUE",
        "model_version": "2.0.0",
        "metadata": {"crop": crop},
    }
    defaults.update(kw)
    return PredictionResult(**defaults)


def _make_many_obs(n: int) -> list[RealFieldRecord]:
    obs = []
    for i in range(n):
        obs.append(
            _make_obs(
                site_id=f"SITE{i:03d}",
                season_id=f"s{i}",
                crop="wheat",
                yield_t_ha=5.0 + i * 0.1,
                field_id=f"FIELD_{i:03d}",
            )
        )
    return obs


def _make_many_pred(n: int) -> list[PredictionResult]:
    preds = []
    for i in range(n):
        preds.append(
            _make_pred(
                site_id=f"SITE{i:03d}",
                season_id=f"s{i}",
                crop="wheat",
                value=5.0 + i * 0.1 + 0.2,
                prediction_id=f"PRED-{i:03d}",
            )
        )
    return preds


def _make_protocol(
    cal_dataset="cal_data_v1",
    val_dataset="val_data_v1",
    target=EvaluationTarget.SPATIAL,
    sites=None,
    seasons=None,
    crops=None,
    **kw,
) -> ValidationProtocol:
    defaults = {
        "calibration_dataset_id": cal_dataset,
        "validation_dataset_id": val_dataset,
        "evaluation_target": target,
        "evaluation_scope": "test scope",
        "crops_in_scope": crops or ["wheat"],
        "sites_in_scope": sites or ["SITE000"],
        "seasons_in_scope": seasons or ["s0"],
        "minimum_sites": 3,
        "minimum_seasons": 2,
    }
    defaults.update(kw)
    return ValidationProtocol(**defaults)


class TestDataAvailabilityStatuses:
    def test_available(self):
        assert DataAvailabilityStatus.AVAILABLE == "available"

    def test_insufficient(self):
        assert DataAvailabilityStatus.INSUFFICIENT_DATA == "insufficient_data"

    def test_no_data(self):
        assert DataAvailabilityStatus.NO_DATA == "no_data"


class TestDataQualityStatuses:
    def test_accepted(self):
        assert DataQualityStatus.ACCEPTED == "accepted"

    def test_rejected(self):
        assert DataQualityStatus.REJECTED == "rejected"

    def test_requires_review(self):
        assert DataQualityStatus.REQUIRES_REVIEW == "requires_review"


class TestEvaluationIndependenceStatus:
    def test_independent(self):
        assert (
            EvaluationIndependenceStatus.INDEPENDENT == "independent"
        )

    def test_not_independent(self):
        assert (
            EvaluationIndependenceStatus.NOT_INDEPENDENT
            == "not_independent"
        )

    def test_unknown(self):
        assert EvaluationIndependenceStatus.UNKNOWN == "unknown"


class TestSampleAdequacyStatus:
    def test_adequate(self):
        assert SampleAdequacyStatus.ADEQUATE == "adequate"

    def test_insufficient(self):
        assert SampleAdequacyStatus.INSUFFICIENT == "insufficient"

    def test_not_assessed(self):
        assert SampleAdequacyStatus.NOT_ASSESSED == "not_assessed"


class TestExternalValidationStatus:
    def test_blocked(self):
        assert ExternalValidationStatus.BLOCKED == "blocked"

    def test_not_assessed(self):
        assert ExternalValidationStatus.NOT_ASSESSED == "not_assessed"

    def test_partially_evaluated(self):
        assert (
            ExternalValidationStatus.PARTIALLY_EVALUATED
            == "partially_evaluated"
        )

    def test_validated_external(self):
        assert (
            ExternalValidationStatus.VALIDATED_EXTERNAL == "validated_external"
        )


class TestDetermineExternalValidationStatus:
    """Tests for the redesigned status determination logic."""

    def test_no_data_blocked(self):
        """No data → BLOCKED."""
        assert determine_external_validation_status(
            n_pairs=0,
            data_availability=DataAvailabilityStatus.NO_DATA,
        ) == ExternalValidationStatus.BLOCKED

    def test_insufficient_data_blocked(self):
        """Insufficient data → BLOCKED."""
        assert determine_external_validation_status(
            n_pairs=0,
            data_availability=DataAvailabilityStatus.INSUFFICIENT_DATA,
        ) == ExternalValidationStatus.BLOCKED

    def test_rejected_data_blocked(self):
        """Rejected data → BLOCKED."""
        assert determine_external_validation_status(
            n_pairs=10,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.REJECTED,
        ) == ExternalValidationStatus.BLOCKED

    def test_not_independent_blocked(self):
        """Not independent → BLOCKED."""
        assert determine_external_validation_status(
            n_pairs=100,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.ACCEPTED,
            evaluation_independence=EvaluationIndependenceStatus.NOT_INDEPENDENT,
        ) == ExternalValidationStatus.BLOCKED

    def test_leakage_blocked(self):
        """Leakage detected → BLOCKED."""
        assert determine_external_validation_status(
            n_pairs=100,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.ACCEPTED,
            evaluation_independence=EvaluationIndependenceStatus.INDEPENDENT,
            data_leakage=DataLeakageStatus.POTENTIAL_LEAKAGE,
        ) == ExternalValidationStatus.BLOCKED

    def test_no_protocol_with_pairs_partially_evaluated(self):
        """No protocol but pairs exist → PARTIALLY_EVALUATED."""
        assert determine_external_validation_status(
            n_pairs=50,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.ACCEPTED,
            evaluation_independence=EvaluationIndependenceStatus.INDEPENDENT,
            has_protocol=False,
        ) == ExternalValidationStatus.PARTIALLY_EVALUATED

    def test_insufficient_samples_partially_evaluated(self):
        """Adequate independence but insufficient samples → PARTIALLY_EVALUATED."""
        assert determine_external_validation_status(
            n_pairs=3,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.ACCEPTED,
            evaluation_independence=EvaluationIndependenceStatus.INDEPENDENT,
            sample_adequacy=SampleAdequacyStatus.INSUFFICIENT,
            has_protocol=True,
        ) == ExternalValidationStatus.PARTIALLY_EVALUATED

    def test_review_data_partially_evaluated(self):
        """Data with REQUIRES_REVIEW → PARTIALLY_EVALUATED (not BLOCKED)."""
        assert determine_external_validation_status(
            n_pairs=50,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.REQUIRES_REVIEW,
            evaluation_independence=EvaluationIndependenceStatus.INDEPENDENT,
            sample_adequacy=SampleAdequacyStatus.ADEQUATE,
            has_protocol=True,
        ) == ExternalValidationStatus.PARTIALLY_EVALUATED

    def test_all_criteria_met_validated_external(self):
        """All criteria met → VALIDATED_EXTERNAL."""
        assert determine_external_validation_status(
            n_pairs=100,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.ACCEPTED,
            evaluation_independence=EvaluationIndependenceStatus.INDEPENDENT,
            sample_adequacy=SampleAdequacyStatus.ADEQUATE,
            data_leakage=DataLeakageStatus.CLEAN,
            has_protocol=True,
        ) == ExternalValidationStatus.VALIDATED_EXTERNAL

    def test_unknown_independence_blocked_or_partial(self):
        """Unknown independence → not VALIDATED_EXTERNAL."""
        result = determine_external_validation_status(
            n_pairs=100,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.ACCEPTED,
            evaluation_independence=EvaluationIndependenceStatus.UNKNOWN,
            has_protocol=True,
        )
        assert result != ExternalValidationStatus.VALIDATED_EXTERNAL

    def test_small_sample_not_auto_validated(self):
        """Small sample with full protocol does not auto-validate."""
        result = determine_external_validation_status(
            n_pairs=5,
            data_availability=DataAvailabilityStatus.AVAILABLE,
            data_quality=DataQualityStatus.ACCEPTED,
            evaluation_independence=EvaluationIndependenceStatus.INDEPENDENT,
            sample_adequacy=SampleAdequacyStatus.INSUFFICIENT,
            has_protocol=True,
        )
        assert result == ExternalValidationStatus.PARTIALLY_EVALUATED


class TestAssessSampleAdequacy:
    """Tests for sample adequacy assessment."""

    def test_spatial_needs_3_sites(self):
        """Spatial generalization needs >= 3 sites."""
        status, limitations = assess_sample_adequacy(
            n_pairs=20, n_sites=2, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT
        assert any("site" in lim.lower() for lim in limitations)

    def test_spatial_adequate(self):
        """Spatial generalization adequate with >= 3 sites."""
        status, _ = assess_sample_adequacy(
            n_pairs=20, n_sites=5, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL,
        )
        assert status == SampleAdequacyStatus.ADEQUATE

    def test_temporal_needs_2_seasons(self):
        """Temporal generalization needs >= 2 seasons."""
        status, limitations = assess_sample_adequacy(
            n_pairs=10, n_sites=1, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.TEMPORAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT
        assert any("season" in lim.lower() for lim in limitations)

    def test_temporal_adequate(self):
        """Temporal generalization adequate with >= 2 seasons."""
        status, _ = assess_sample_adequacy(
            n_pairs=10, n_sites=1, n_seasons=3, n_crops=1,
            evaluation_target=EvaluationTarget.TEMPORAL,
        )
        assert status == SampleAdequacyStatus.ADEQUATE

    def test_spatial_and_temporal_needs_both(self):
        """Spatial+temporal needs >= 3 sites AND >= 2 seasons."""
        status, limitations = assess_sample_adequacy(
            n_pairs=10, n_sites=2, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.SPATIAL_AND_TEMPORAL,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT
        assert len(limitations) >= 1

    def test_none_target_adequate_with_1_pair(self):
        """NONE target (reproducibility) needs only 1 pair."""
        status, _ = assess_sample_adequacy(
            n_pairs=1, n_sites=1, n_seasons=1, n_crops=1,
            evaluation_target=EvaluationTarget.NONE,
        )
        assert status == SampleAdequacyStatus.ADEQUATE

    def test_none_target_no_data(self):
        """NONE target with 0 pairs → insufficient."""
        status, _ = assess_sample_adequacy(
            n_pairs=0, n_sites=0, n_seasons=0, n_crops=0,
            evaluation_target=EvaluationTarget.NONE,
        )
        assert status == SampleAdequacyStatus.INSUFFICIENT


class TestProduceValidationReport:
    """Tests for produce_validation_report with new governance model."""

    def test_no_data_blocked(self):
        """No observations → BLOCKED."""
        preds = _make_many_pred(5)
        report = produce_validation_report(
            predictions=preds, observations=[]
        )
        assert report.external_validation_status == "blocked"
        assert report.data_availability_status == "no_data"
        assert len(report.matched_pairs) == 0

    def test_no_predictions_blocked(self):
        """No predictions → BLOCKED."""
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=[], observations=obs
        )
        assert report.external_validation_status == "blocked"

    def test_insufficient_samples_partially_evaluated(self):
        """< 3 sites for spatial → PARTIALLY_EVALUATED (insufficient)."""
        # Create 5 pairs but only 2 sites — insufficient for spatial generalization
        preds = []
        obs = []
        for i in range(5):
            site = "SITE000" if i < 3 else "SITE001"
            preds.append(_make_pred(
                site_id=site, season_id=f"s{i}", crop="wheat",
                value=5.2 + i * 0.01, prediction_id=f"P{i:03d}",
            ))
            obs.append(_make_obs(
                site_id=site, season_id=f"s{i}", crop="wheat",
                yield_t_ha=5.0,
            ))
        protocol = _make_protocol(
            sites=["SITE000", "SITE001"],
            seasons=[f"s{i}" for i in range(5)],
            target=EvaluationTarget.SPATIAL,
            minimum_sites=3,
            minimum_seasons=1,
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, protocol=protocol
        )
        assert report.sample_adequacy_status == "insufficient"
        assert report.external_validation_status == "partially_evaluated"

    def test_adequate_samples_with_protocol_validated(self):
        """>= 3 sites for spatial → VALIDATED_EXTERNAL with protocol."""
        # Create 6 sites, 6 predictions, 6 obs, spatial target
        preds = []
        obs = []
        for i in range(6):
            preds.append(_make_pred(
                site_id=f"SITE{i:03d}", season_id="s0", crop="wheat",
                value=5.2 + i * 0.01, prediction_id=f"P{i:03d}",
                metadata={"crop": "wheat"},
            ))
            obs.append(_make_obs(
                site_id=f"SITE{i:03d}", season_id="s0", crop="wheat",
                yield_t_ha=5.0,
            ))
        protocol = _make_protocol(
            sites=[f"SITE{i:03d}" for i in range(6)],
            seasons=["s0"],
            target=EvaluationTarget.SPATIAL,
            minimum_sites=3,
            minimum_seasons=1,
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, protocol=protocol
        )
        assert report.data_availability_status == "available"
        assert report.data_quality_status == "accepted"
        assert report.evaluation_independence_status == "independent"
        assert report.sample_adequacy_status == "adequate"
        assert report.external_validation_status == "validated_external"

    def test_all_synthetic_data_blocked(self):
        """All-synthetic observations → all rejected → BLOCKED."""
        obs = []
        for i in range(6):
            syn_rec = RealFieldRecord.model_construct(
                site_id=f"SITE{i:03d}",
                field_id="FIELD_A",
                season_id=f"s{i}",
                crop="wheat",
                cultivar="scepter",
                planting_date=date(2024, 4, 1),
                harvest_date=date(2024, 5, 30),
                latitude=40.0,
                longitude=-105.0,
                area_ha=2.5,
                observed_yield=6.5,
                observed_yield_unit="t/ha",
                observation_source="field_measured",
                observation_source_id="study_2024",
                data_label="synthetic_test_data",
            )
            obs.append(syn_rec)
        preds = _make_many_pred(6)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.external_validation_status == "blocked"
        assert report.data_availability_status == "insufficient_data"

    def test_data_quality_counts(self):
        """Data quality counts reflect accepted/rejected/review records."""
        obs = _make_many_obs(5)
        # Add a synthetic observation (bypass validator with model_construct)
        syn_rec = RealFieldRecord.model_construct(
            site_id="SITE005",
            field_id="FIELD_A",
            season_id="s5",
            crop="wheat",
            cultivar="scepter",
            planting_date=date(2024, 4, 1),
            harvest_date=date(2024, 5, 30),
            latitude=40.0,
            longitude=-105.0,
            area_ha=2.5,
            observed_yield=6.5,
            observed_yield_unit="t/ha",
            observation_source="field_measured",
            observation_source_id="study_2024",
            data_label="synthetic_test_data",
        )
        obs.append(syn_rec)
        # Add a duplicate of SITE000
        obs.append(_make_obs(site_id="SITE000", season_id="s0"))

        preds = _make_many_pred(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.data_records_total == 7
        assert report.data_records_accepted == 5
        assert report.data_records_rejected == 1
        assert report.data_records_review == 1

    def test_data_quality_status_rejected(self):
        """All records rejected → data_quality_status == rejected."""
        obs = []
        for i in range(5):
            syn = RealFieldRecord.model_construct(
                site_id=f"SITE{i:03d}",
                field_id="F1",
                season_id=f"s{i}",
                crop="wheat",
                cultivar="scepter",
                planting_date=date(2024, 4, 1),
                harvest_date=date(2024, 5, 30),
                latitude=40.0,
                longitude=-105.0,
                area_ha=2.5,
                observed_yield=6.5,
                observed_yield_unit="t/ha",
                observation_source="field_measured",
                observation_source_id="study_2024",
                data_label="synthetic_test_data",
            )
            obs.append(syn)
        preds = _make_many_pred(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.data_quality_status == "rejected"
        assert report.external_validation_status == "blocked"

    def test_no_protocol_partially_evaluated(self):
        """Without a protocol, even with many pairs → PARTIALLY_EVALUATED."""
        preds = _make_many_pred(20)
        obs = _make_many_obs(20)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.external_validation_status == "partially_evaluated"
        # Without protocol or split, independence cannot be verified
        assert report.evaluation_independence_status == "unknown"

    def test_unmatched_predictions_tracked(self):
        """Predictions with no matching observation are tracked."""
        preds = _make_many_pred(8)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert len(report.matched_pairs) == 5
        assert len(report.unmatched_predictions) == 3

    def test_unmatched_observations_tracked(self):
        """Observations with no matching prediction are tracked."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(8)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert len(report.matched_pairs) == 5
        assert len(report.unmatched_observations) == 3

    def test_split_clean_no_leakage(self):
        """A clean split → CLEAN leakage status."""
        obs = _make_many_obs(10)
        split = split_for_validation(obs, method="site", seed=42)
        preds = _make_many_pred(10)
        report = produce_validation_report(
            predictions=preds, observations=obs, split=split
        )
        assert report.data_leakage_status == "clean"

    def test_scientific_limitations_populated(self):
        """Limitations are populated based on conditions."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert len(report.scientific_limitations) > 0

    def test_model_name_from_predictions(self):
        """Model name and version come from predictions."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.model_name == "HY-RUE"
        assert report.model_version == "2.0.0"

    def test_prediction_ids_in_report(self):
        """Prediction IDs are preserved in the report."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.prediction_ids == [p.prediction_id for p in preds]

    def test_validation_run_id_format(self):
        """Validation run ID follows VAL-<hex> format."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.validation_run_id.startswith("VAL-")
        assert len(report.validation_run_id) > 4

    def test_evaluation_timestamp_iso_format(self):
        """Evaluation timestamp is ISO format."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        from datetime import datetime

        datetime.fromisoformat(report.evaluation_timestamp)

    def test_coverage_metrics(self):
        """Coverage metrics (sites, seasons, crops) are populated."""
        preds = _make_many_pred(6)
        obs = _make_many_obs(6)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert report.total_unique_sites == 6
        assert report.total_unique_seasons == 6
        assert report.total_unique_crops == 1
        assert report.total_unique_fields == 6

    def test_protocol_in_report(self):
        """Protocol is attached to the report when provided."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        protocol = _make_protocol(
            sites=[f"SITE{i:03d}" for i in range(5)],
            seasons=["s0"],
            crops=["wheat"],
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, protocol=protocol
        )
        assert report.protocol is not None
        assert report.protocol.calibration_dataset_id == "cal_data_v1"

    def test_crop_evaluations_populated(self):
        """Per-crop evaluations are computed."""
        preds = _make_many_pred(6)
        obs = _make_many_obs(6)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        assert len(report.crop_evaluations) >= 1
        assert all(c.crop == "wheat" for c in report.crop_evaluations)


class TestValidationOutputSerialization:
    """Tests for ValidationOutput.to_dict()."""

    def test_to_dict_keys(self):
        """to_dict returns expected top-level keys."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        d = report.to_dict()
        expected_keys = {
            "validation_run_id",
            "evaluation_timestamp",
            "model",
            "prediction_ids",
            "dataset_version",
            "evaluation_method",
            "protocol",
            "overall_metrics",
            "crop_evaluations",
            "data_coverage",
            "matched_pairs_count",
            "unmatched_predictions_count",
            "unmatched_observations_count",
            "data_quality",
            "statuses",
            "leakage_violations",
            "scientific_limitations",
            "notes",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_statuses(self):
        """to_dict includes all status dimensions."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        d = report.to_dict()
        assert "statuses" in d
        assert "data_availability" in d["statuses"]
        assert "data_quality" in d["statuses"]
        assert "evaluation_independence" in d["statuses"]
        assert "sample_adequacy" in d["statuses"]
        assert "external_validation" in d["statuses"]
        assert "data_leakage" in d["statuses"]

    def test_to_dict_data_coverage(self):
        """to_dict includes coverage metrics."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        report = produce_validation_report(
            predictions=preds, observations=obs
        )
        d = report.to_dict()
        assert d["data_coverage"]["total_unique_sites"] == 5
        assert d["data_coverage"]["total_unique_seasons"] == 5
        assert d["data_coverage"]["total_unique_crops"] == 1

    def test_to_dict_with_no_metrics(self):
        """to_dict handles empty metrics (BLOCKED case)."""
        report = produce_validation_report(predictions=[], observations=[])
        d = report.to_dict()
        assert d["overall_metrics"] is None
        assert d["matched_pairs_count"] == 0
        assert d["statuses"]["external_validation"] == "blocked"

    def test_to_dict_with_protocol(self):
        """to_dict includes protocol info when provided."""
        preds = _make_many_pred(5)
        obs = _make_many_obs(5)
        protocol = _make_protocol(
            sites=[f"SITE{i:03d}" for i in range(5)],
            seasons=["s0"],
            crops=["wheat"],
        )
        report = produce_validation_report(
            predictions=preds, observations=obs, protocol=protocol
        )
        d = report.to_dict()
        assert d["protocol"] is not None
        assert d["protocol"]["protocol_id"].startswith("PROTO-")
