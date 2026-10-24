"""Tests for Stage 27: Field validation contracts and quality gates.

Tests cover:
- RealFieldRecord validation (units, coordinates, dates, synthetic rejection)
- Yield unit conversions (t/ha, kg/ha, g/m²)
- Quality gate rules (non-finite, negative, duplicates, missing metadata)
- Observation source validation
"""

from __future__ import annotations

from datetime import date

import pytest

from engine.hydroma.eval.field_validation import (
    VALID_YIELD_UNITS,
    QualityGateDecision,
    RealFieldRecord,
    convert_yield_to_t_ha,
    run_quality_gates,
)


def _make_valid_record(**overrides) -> RealFieldRecord:
    """Create a valid RealFieldRecord with optional overrides."""
    defaults = {
        "site_id": "SITE001",
        "field_id": "FIELD_A",
        "season_id": "wheat_2024",
        "crop": "wheat",
        "cultivar": "scepter",
        "planting_date": date(2024, 3, 15),
        "harvest_date": date(2024, 6, 15),
        "latitude": 35.0,
        "longitude": 50.0,
        "area_ha": 2.5,
        "observed_yield": 6.5,
        "observed_yield_unit": "t/ha",
        "yield_measurement_method": "combine_harvester",
        "harvest_sample_size": 20,
        "observation_source": "field_measured",
        "observation_source_id": "study_2024",
        "data_label": "field_station_2024",
    }
    defaults.update(overrides)
    return RealFieldRecord(**defaults)


class TestYieldUnitConversion:
    """Tests for yield unit conversion to t/ha."""

    def test_t_ha_passthrough(self):
        """t/ha converts to itself."""
        assert convert_yield_to_t_ha(5.0, "t/ha") == 5.0

    def test_kg_ha_to_t_ha(self):
        """1000 kg/ha = 1 t/ha."""
        assert convert_yield_to_t_ha(1000.0, "kg/ha") == pytest.approx(1.0)

    def test_g_m2_to_t_ha(self):
        """100 g/m² = 1 t/ha."""
        assert convert_yield_to_t_ha(100.0, "g/m²") == pytest.approx(1.0)

    def test_invalid_unit_raises(self):
        """Unknown unit raises ValueError."""
        with pytest.raises(ValueError, match="Unknown yield unit"):
            convert_yield_to_t_ha(5.0, "bushels/acre")

    def test_valid_units_set(self):
        """VALID_YIELD_UNITS contains the three accepted units."""
        assert VALID_YIELD_UNITS == frozenset({"t/ha", "kg/ha", "g/m²"})


class TestRealFieldRecordValidation:
    """Tests for RealFieldRecord pydantic validation."""

    def test_valid_record_accepted(self):
        """A well-formed record passes validation."""
        rec = _make_valid_record()
        assert rec.site_id == "SITE001"
        assert rec.observed_yield == 6.5
        assert rec.observed_yield_unit == "t/ha"

    def test_negative_yield_rejected(self):
        """Negative yield raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            _make_valid_record(observed_yield=-1.0)

    def test_nan_yield_rejected(self):
        """NaN yield raises ValueError."""
        with pytest.raises(ValueError, match="finite"):
            _make_valid_record(observed_yield=float("nan"))

    def test_inf_yield_rejected(self):
        """Inf yield raises ValueError."""
        with pytest.raises(ValueError, match="finite"):
            _make_valid_record(observed_yield=float("inf"))

    def test_invalid_yield_unit_rejected(self):
        """Unknown yield unit raises ValueError."""
        with pytest.raises(ValueError, match="not in"):
            _make_valid_record(observed_yield_unit="bushels/acre")

    def test_invalid_latitude_rejected(self):
        """Latitude > 90 raises ValueError."""
        with pytest.raises(ValueError, match="less_than_equal|less than or equal"):
            _make_valid_record(latitude=95.0)

    def test_invalid_longitude_rejected(self):
        """Longitude > 180 raises ValueError."""
        with pytest.raises(ValueError, match=">= -180|<= 180|greater_than_equal"):
            _make_valid_record(longitude=-200.0)

    def test_harvest_before_planting_rejected(self):
        """Harvest date before planting date raises ValueError."""
        with pytest.raises(ValueError, match="must not precede"):
            _make_valid_record(
                planting_date=date(2024, 6, 1),
                harvest_date=date(2024, 5, 1),
            )

    def test_synthetic_data_label_rejected(self):
        """Records with 'synthetic' data_label are rejected by the validator."""
        with pytest.raises(ValueError, match="synthetic"):
            _make_valid_record(data_label="synthetic_test_data")

    def test_synthetic_prefix_rejected(self):
        """Records with 'synthetic_' prefix are rejected."""
        with pytest.raises(ValueError, match="synthetic"):
            _make_valid_record(data_label="synthetic_field_data")

    def test_invalid_observation_source_rejected(self):
        """Unknown observation source is rejected."""
        with pytest.raises(ValueError, match="not in"):
            _make_valid_record(observation_source="unknown_source")

    def test_yield_t_ha_property(self):
        """yield_t_ha property converts from various units."""
        rec_kg = _make_valid_record(observed_yield=6500.0, observed_yield_unit="kg/ha")
        assert rec_kg.yield_t_ha == pytest.approx(6.5)

        rec_g = _make_valid_record(observed_yield=650.0, observed_yield_unit="g/m²")
        assert rec_g.yield_t_ha == pytest.approx(6.5)

    def test_record_key(self):
        """record_key returns (site_id, season_id, crop)."""
        rec = _make_valid_record()
        assert rec.record_key == ("SITE001", "wheat_2024", "wheat")

    def test_extra_field_rejected(self):
        """Unknown fields are rejected (extra='forbid')."""
        with pytest.raises(ValueError, match="extra_forbidden|Extra inputs"):
            RealFieldRecord(
                site_id="S1",
                field_id="F1",
                season_id="wheat_2024",
                crop="wheat",
                planting_date=date(2024, 4, 1),
                harvest_date=date(2024, 6, 1),
                latitude=40.0,
                longitude=-105.0,
                area_ha=2.0,
                observed_yield=5.0,
                observed_yield_unit="t/ha",
                observation_source="field_measured",
                data_label="real_data",
                bogus_field="should_fail",
            )


class TestQualityGates:
    """Tests for the quality gate rules."""

    def test_accept_single_record(self):
        """A single valid record is ACCEPTED."""
        rec = _make_valid_record()
        gated = run_quality_gates([rec])
        assert gated[0].quality_gate_decision == QualityGateDecision.ACCEPTED.value

    def test_reject_synthetic_record(self):
        """Records with synthetic label are REJECTED by quality gates.

        The pydantic validator rejects synthetic labels at construction, so
        we use model_construct to bypass validation and test the quality
        gate's belt-and-suspenders check.
        """
        rec = RealFieldRecord.model_construct(
            site_id="S1",
            season_id="s1",
            crop="wheat",
            planting_date=date(2024, 4, 1),
            harvest_date=date(2024, 6, 1),
            latitude=40.0,
            longitude=-105.0,
            observed_yield=5.0,
            observed_yield_unit="t/ha",
            observation_source="field_measured",
            data_label="synthetic_test_data",
        )
        gated = run_quality_gates([rec])
        assert gated[0].quality_gate_decision == QualityGateDecision.REJECTED.value
        assert "synthetic" in gated[0].quality_gate_reasons[0].lower()

    def test_duplicate_detected(self):
        """Duplicate (site_id, season_id, crop) records are flagged."""
        rec1 = _make_valid_record()
        rec2 = _make_valid_record(observation_source="satellite_retrieved")
        gated = run_quality_gates([rec1, rec2])
        assert gated[0].quality_gate_decision == QualityGateDecision.ACCEPTED.value
        assert gated[1].quality_gate_decision == QualityGateDecision.REQUIRES_REVIEW.value
        assert "duplicate" in gated[1].quality_gate_reasons[0].lower()

    def test_no_duplicate_for_different_site(self):
        """Records from different sites are not flagged as duplicates."""
        rec1 = _make_valid_record(site_id="SITE001")
        rec2 = _make_valid_record(site_id="SITE002")
        gated = run_quality_gates([rec1, rec2])
        assert all(
            g.quality_gate_decision == QualityGateDecision.ACCEPTED.value for g in gated
        )

    def test_missing_area_flags_review(self):
        """Missing area_ha flags REQUIRES_REVIEW."""
        rec = _make_valid_record(area_ha=None)
        gated = run_quality_gates([rec])
        assert gated[0].quality_gate_decision == QualityGateDecision.REQUIRES_REVIEW.value
        assert any("area_ha" in r for r in gated[0].quality_gate_reasons)

    def test_missing_cultivar_flags_review(self):
        """Missing cultivar flags REQUIRES_REVIEW."""
        rec = _make_valid_record(cultivar=None)
        gated = run_quality_gates([rec])
        assert gated[0].quality_gate_decision == QualityGateDecision.REQUIRES_REVIEW.value
        assert any("cultivar" in r for r in gated[0].quality_gate_reasons)

    def test_missing_sample_size_flags_review(self):
        """Missing harvest_sample_size flags REQUIRES_REVIEW."""
        rec = _make_valid_record(harvest_sample_size=None)
        gated = run_quality_gates([rec])
        assert gated[0].quality_gate_decision == QualityGateDecision.REQUIRES_REVIEW.value
        assert any("harvest_sample_size" in r for r in gated[0].quality_gate_reasons)

    def test_negative_yield_rejected_at_construction(self):
        """Negative yield is rejected at construction (pydantic validator)."""
        with pytest.raises(ValueError, match="non-negative"):
            _make_valid_record(observed_yield=-0.001)
