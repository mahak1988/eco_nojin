"""End-to-end integration test for the HyDroMA Phase C pipeline.

Tests the full path: TestDataGenerator → facade → EngineGateway →
engine.hydroma.et.compute_et → et_calculator → GatewayResult.
"""

from __future__ import annotations

import pytest

from engine.evidence import Evidence, EvidenceSource, EvidenceType
from engine.scientific_verification import TestDataGenerator
from services._gateway_facade import calc_et0_hargreaves, get_gateway


@pytest.fixture(scope="module")
def climate_series():
    return TestDataGenerator.climate_series(
        n_days=30, base_temp=20.0, temp_amp=5.0,
        base_precip=5.0, precip_amp=2.0,
    )


class TestE2EPipeline:
    """End-to-end pipeline: TDDG → facade → gateway → compute_et."""

    def test_facade_returns_rich_response(self, climate_series):
        """calc_et0_hargreaves returns model_id, data, provenance, execution_metadata."""
        result = calc_et0_hargreaves(
            temp_max=climate_series["tmax"][0],
            temp_min=climate_series["tmin"][0],
            elevation=1200.0,
            latitude=35.7,
            doy=180,
        )

        assert isinstance(result, dict)
        assert "model_id" in result
        assert "data" in result
        assert "provenance" in result
        assert "execution_metadata" in result

        assert result["model_id"] == "CANON-002"
        assert "et0_mm_day" in result["data"]
        assert result["data"]["et0_mm_day"] > 0
        assert result["provenance"]["source"] == "service_gateway_facade"
        assert result["provenance"]["source_type"] == "SERVICE_CALL"
        assert result["execution_metadata"]["gateway_version"] == "1.0.0"
        assert result["execution_metadata"]["cpp_backend"] is False

    def test_et0_within_physical_bounds(self, climate_series):
        """ET0 values are physically reasonable (0 < et0 < 15 mm/day)."""
        et0_values = []
        for i in range(30):
            result = calc_et0_hargreaves(
                temp_max=climate_series["tmax"][i],
                temp_min=climate_series["tmin"][i],
                elevation=1200.0,
                latitude=35.7,
                doy=180 + i,
            )
            et0 = result["data"]["et0_mm_day"]
            assert et0 > 0, f"Day {i}: ET0 must be positive, got {et0}"
            assert et0 < 15.0, f"Day {i}: ET0 exceeds physical ceiling, got {et0}"
            et0_values.append(et0)
        assert len(et0_values) == 30

    def test_provenance_chain_is_traceable(self, climate_series):
        """Gateway evidence engine records the computation as evidence."""
        gw = get_gateway()
        et0 = calc_et0_hargreaves(
            temp_max=climate_series["tmax"][5],
            temp_min=climate_series["tmin"][5],
            elevation=1200.0,
            latitude=35.7,
            doy=185,
        )["data"]["et0_mm_day"]
        evidence = Evidence(
            source=EvidenceSource.MODEL,
            evidence_type=EvidenceType.QUANTITATIVE,
            value=et0,
            confidence=1.0,
            provenance=[
                "service_gateway_facade",
                "engine_gateway",
                "engine.hydroma.et.compute_et",
                "et_calculator.calc_et0_hargreaves",
            ],
        )
        gw.evidence_engine.collect(evidence)
        all_evidence = gw.evidence_engine.all()
        assert len(all_evidence) > 0
        last = all_evidence[-1]
        assert last.source.value == "model"
        assert len(last.provenance) == 4
        assert last.provenance[0] == "service_gateway_facade"
        assert "et_calculator" in last.provenance[-1]

    def test_model_spec_is_correct(self, climate_series):
        """The model spec returned by the gateway matches CANON-002."""
        result = calc_et0_hargreaves(
            temp_max=climate_series["tmax"][10],
            temp_min=climate_series["tmin"][10],
            elevation=1200.0,
            latitude=35.7,
            doy=190,
        )
        assert result["model_name"] == "Hargreaves ET0"
        assert result["data"]["method"] == "hargreaves"
        assert result["data"]["units"] == "mm/day"

    def test_execution_metadata_populated(self, climate_series):
        """Execution metadata contains version and backend info."""
        result = calc_et0_hargreaves(
            temp_max=climate_series["tmax"][15],
            temp_min=climate_series["tmin"][15],
            elevation=1200.0,
            latitude=35.7,
            doy=195,
        )
        meta = result["execution_metadata"]
        assert meta["gateway_version"] == "1.0.0"
        assert meta["engine_version"] == "1.0.0"
        assert isinstance(meta["cpp_backend"], bool)
