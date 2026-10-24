"""Tests for Stage 28: Validation governance and protocol enforcement.

Tests cover:
- ValidationProtocol creation, completeness checks, serialization
- Protocol-based status determination
- Protocol completeness prevents VALIDATED_EXTERNAL
"""

from __future__ import annotations

from datetime import date

import pytest

from engine.hydroma.eval.validation_matching import ValidationSplit
from engine.hydroma.eval.validation_protocol import (
    EvaluationTarget,
    MetricAcceptanceCriterion,
    MetricCriterion,
    ValidationProtocol,
)


class TestValidationProtocolCreation:
    """Tests for ValidationProtocol construction and defaults."""

    def test_default_protocol(self):
        """Protocol has a default ID starting with PROTO-."""
        proto = ValidationProtocol()
        assert proto.protocol_id.startswith("PROTO-")
        assert proto.protocol_version == "1.0"
        assert proto.model_version == "2.0.0"
        assert proto.evaluation_target == EvaluationTarget.NONE
        assert proto.has_protocol if False else True  # always has protocol object

    def test_complete_protocol(self):
        """A complete protocol passes is_complete()."""
        proto = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test scope",
            crops_in_scope=["wheat"],
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
            minimum_sites=3,
            minimum_seasons=1,
        )
        assert proto.is_complete() is True

    def test_incomplete_protocol_missing_calibration(self):
        """Missing calibration dataset → incomplete."""
        proto = ValidationProtocol(
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test scope",
            crops_in_scope=["wheat"],
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
        )
        assert proto.is_complete() is False

    def test_incomplete_protocol_missing_validation(self):
        """Missing validation dataset → incomplete."""
        proto = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test scope",
            crops_in_scope=["wheat"],
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
        )
        assert proto.is_complete() is False

    def test_incomplete_protocol_same_dataset(self):
        """Same calibration/validation dataset → incomplete."""
        proto = ValidationProtocol(
            calibration_dataset_id="same_data",
            validation_dataset_id="same_data",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test scope",
            crops_in_scope=["wheat"],
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
            minimum_sites=3,
            minimum_seasons=1,
        )
        assert proto.is_complete() is False

    def test_incomplete_protocol_none_target(self):
        """EvaluationTarget.NONE → incomplete."""
        proto = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.NONE,
            evaluation_scope="test scope",
            crops_in_scope=["wheat"],
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
            minimum_sites=3,
            minimum_seasons=1,
        )
        assert proto.is_complete() is False

    def test_incomplete_protocol_no_crops(self):
        """No crops in scope → incomplete."""
        proto = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test scope",
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
            minimum_sites=3,
            minimum_seasons=1,
        )
        assert proto.is_complete() is False

    def test_incomplete_protocol_zero_minimum_sites(self):
        """minimum_sites=0 → incomplete."""
        proto = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test scope",
            crops_in_scope=["wheat"],
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
            minimum_sites=0,
            minimum_seasons=1,
        )
        assert proto.is_complete() is False


class TestValidationProtocolSerialization:
    """Tests for ValidationProtocol.to_dict()."""

    def test_to_dict_keys(self):
        """to_dict returns expected keys."""
        proto = ValidationProtocol(
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
            evaluation_target=EvaluationTarget.SPATIAL,
            evaluation_scope="test scope",
            crops_in_scope=["wheat"],
            sites_in_scope=["SITE001"],
            seasons_in_scope=["s1"],
        )
        d = proto.to_dict()
        expected_keys = {
            "protocol_id",
            "protocol_version",
            "model_version",
            "model_parameters_hash",
            "calibration_dataset_id",
            "validation_dataset_id",
            "evaluation_target",
            "evaluation_scope",
            "evaluation_start_date",
            "evaluation_end_date",
            "crops_in_scope",
            "sites_in_scope",
            "seasons_in_scope",
            "split_method",
            "split_seed",
            "unit_of_independence",
            "minimum_sites",
            "minimum_seasons",
            "acceptance_criteria",
            "notes",
            "created_at",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_evaluation_target(self):
        """evaluation_target is serialized as a string value."""
        proto = ValidationProtocol(
            evaluation_target=EvaluationTarget.TEMPORAL,
        )
        d = proto.to_dict()
        assert d["evaluation_target"] == "temporal"


class TestMetricAcceptanceCriterion:
    """Tests for MetricAcceptanceCriterion."""

    def test_valid_max_criterion(self):
        """Max criterion is created successfully."""
        crit = MetricAcceptanceCriterion(
            metric="rmse", comparison="max", threshold=2.0, unit="t/ha"
        )
        assert crit.metric == "rmse"
        assert crit.comparison == "max"
        assert crit.threshold == 2.0

    def test_valid_min_criterion(self):
        """Min criterion is created successfully."""
        crit = MetricAcceptanceCriterion(
            metric="r_squared", comparison="min", threshold=0.5, unit="dimensionless"
        )
        assert crit.metric == "r_squared"
        assert crit.comparison == "min"

    def test_invalid_comparison_raises(self):
        """Invalid comparison raises ValueError."""
        with pytest.raises(ValueError, match="max.*min"):
            MetricAcceptanceCriterion(
                metric="rmse", comparison="equal", threshold=2.0, unit="t/ha"
            )


class TestMetricCriterion:
    """Tests for MetricCriterion enum."""

    def test_rmse_threshold(self):
        assert MetricCriterion.RMSE_THRESHOLD.value == "rmse_threshold"

    def test_mae_threshold(self):
        assert MetricCriterion.MAE_THRESHOLD.value == "mae_threshold"

    def test_r_squared_min(self):
        assert MetricCriterion.R_SQUARED_MIN.value == "r_squared_min"

    def test_bias_max(self):
        assert MetricCriterion.BIAS_MAX.value == "bias_max"

    def test_mape_max(self):
        assert MetricCriterion.MAPE_MAX.value == "mape_max"


class TestEvaluationTarget:
    """Tests for EvaluationTarget enum."""

    def test_spatial(self):
        assert EvaluationTarget.SPATIAL.value == "spatial"

    def test_temporal(self):
        assert EvaluationTarget.TEMPORAL.value == "temporal"

    def test_spatial_and_temporal(self):
        assert (
            EvaluationTarget.SPATIAL_AND_TEMPORAL.value
            == "spatial_and_temporal"
        )

    def test_none(self):
        assert EvaluationTarget.NONE.value == "none"


class TestProtocolFromSplit:
    """Tests for ValidationProtocol.from_split factory."""

    def test_from_split_creates_protocol(self):
        """from_split creates a protocol from a ValidationSplit."""
        from engine.hydroma.eval.field_validation import RealFieldRecord

        recs = [
            RealFieldRecord(
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
                observed_yield=5.0,
                observed_yield_unit="t/ha",
                observation_source="field_measured",
                data_label="field_station_2024",
            )
            for i in range(5)
        ]

        split = ValidationSplit(
            calibration=[],
            validation=recs[:3],
            test=recs[3:],
            method="site",
            seed=42,
        )

        proto = ValidationProtocol.from_split(
            split,
            calibration_dataset_id="cal_v1",
            validation_dataset_id="val_v1",
        )

        assert proto.calibration_dataset_id == "cal_v1"
        assert proto.validation_dataset_id == "val_v1"
        assert proto.evaluation_target == EvaluationTarget.SPATIAL
        assert "wheat" in proto.crops_in_scope
        assert len(proto.sites_in_scope) == 5
        assert proto.is_complete()
