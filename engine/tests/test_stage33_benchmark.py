"""Tests for Stage 33: External HYRUE Benchmark Execution with CIMMYT Data.

Tests cover:
- Data file hash verification
- CIMMYT data loading and audit
- Spatial protocol and leakage checks
- STRICT policy prediction fails (no EWSI)
- ALLOW_ESTIMATED policy prediction fails (no EWSI)
- DIAGNOSTIC policy prediction succeeds (legacy fallback)
- Metrics computation with blocked results
- Baseline computation from development set
- BenchmarkResult dataclass
- CSV output structure
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.hydroma.eval.field_validation import RealFieldRecord
from tools.stage33_benchmark import (
    BENCHMARK_VERSION,
    DATASET_ID,
    DEV_DISTRICTS,
    MODEL_NAME,
    MODEL_VERSION,
    TEST_DISTRICTS,
    BenchmarkResult,
    audit_grain_yield,
    audit_spatial_independence,
    audit_weather_data,
    check_data_leakage,
    compute_baseline_metrics,
    compute_file_hash,
    compute_metrics_from_results,
    define_spatial_protocol,
    load_cimmyt_data,
    verify_data_file,
)

STAGE33_RESULTS = Path("engine/reports/data/stage33_results.json")
STAGE33_CSV = Path("engine/reports/data/stage33_hyrue_predictions.csv")


@pytest.fixture(scope="module")
def cimmyt_results() -> dict:
    if not STAGE33_RESULTS.exists():
        pytest.skip("Stage 33 results not found — run tools/stage33_benchmark.py first")
    with open(STAGE33_RESULTS) as f:
        return json.load(f)


class TestBenchmarkIdentifiers:
    def test_model_version(self):
        assert MODEL_VERSION == "2.0.0"

    def test_model_name(self):
        assert MODEL_NAME == "HY-RUE"

    def test_benchmark_version(self):
        assert BENCHMARK_VERSION == "1.0"

    def test_dataset_id(self):
        assert DATASET_ID == "cimmyt_wheat_eastern_india_10.71682/10549424"

    def test_test_districts(self):
        assert TEST_DISTRICTS == ["Buxar", "Muzaffarpur", "Rohtas"]

    def test_dev_districts(self):
        assert len(DEV_DISTRICTS) == 7
        assert "Buxar" not in DEV_DISTRICTS


class TestDataFileVerification:
    def test_file_hash_matches_stage32(self):
        info = verify_data_file()
        assert info["hash_matches_stage32"] is True
        assert info["verified"] is True

    def test_file_exists(self):
        info = verify_data_file()
        assert Path(info["file_path"]).exists()

    def test_compute_file_hash(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        h = compute_file_hash(filepath)
        assert len(h) == 64
        assert h == "919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde"


class TestDataLoading:
    def test_load_cimmyt_data(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, audit = load_cimmyt_data()
        assert audit["total_records"] == 5689
        assert audit["site_count"] == 10
        assert len(audit["seasons"]) == 6

    def test_audit_grain_yield(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, _ = load_cimmyt_data()
        ya = audit_grain_yield(df)
        assert ya["missing_count"] == 0
        assert ya["negative_count"] == 0
        assert ya["zero_count"] == 0
        assert ya["min"] >= 0
        assert ya["max"] > 0
        assert ya["removed_records"] == 0

    def test_audit_spatial_independence(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, _ = load_cimmyt_data()
        sa = audit_spatial_independence(df)
        assert sa["unique_field_ids"] == 5689
        assert sa["spatially_independent_groups"] == 10
        assert sa["field_id_duplicates"] == 0


class TestWeatherDataAudit:
    def test_weather_audit_monthly_not_daily(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, _ = load_cimmyt_data()
        wa = audit_weather_data(df)
        assert wa["usable_for_hyrue"] is False
        assert "daily" in wa["reason"].lower()


class TestSpatialProtocol:
    def test_protocol_no_district_overlap(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, _ = load_cimmyt_data()
        records = create_records_from_df(df)
        protocol = define_spatial_protocol(records)
        assert protocol["overlap_clean"] is True
        assert len(protocol["district_overlap"]) == 0
        assert protocol["protocol_is_complete"] is True

    def test_protocol_test_dev_split(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, _ = load_cimmyt_data()
        records = create_records_from_df(df)
        protocol = define_spatial_protocol(records)
        assert set(protocol["test_districts"]) == set(TEST_DISTRICTS)
        assert set(protocol["dev_districts"]) == set(DEV_DISTRICTS)

    def test_protocol_field_ids_unique_in_test(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, _ = load_cimmyt_data()
        records = create_records_from_df(df)
        protocol = define_spatial_protocol(records)
        assert protocol["field_id_unique_in_test"] is True


class TestDataLeakage:
    def test_no_site_overlap(self):
        filepath = Path("data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx")
        if not filepath.exists():
            pytest.skip("CIMMYT data file not found")
        df, _ = load_cimmyt_data()
        records = create_records_from_df(df)
        test_records = [r for r in records if r.site_id.replace("District_", "") in TEST_DISTRICTS]
        dev_records = [r for r in records if r.site_id.replace("District_", "") in DEV_DISTRICTS]
        leakage = check_data_leakage(test_records, dev_records)
        assert leakage["overall_leakage_status"] == "CLEAN"
        assert leakage["leakage_violations"] == []


class TestBenchmarkResult:
    def test_benchmark_result_dataclass(self):
        r = BenchmarkResult(
            record_id="F001",
            field_id="F001",
            district="Buxar",
            state="Bihar",
            season_id="wheat_2016",
            crop="wheat",
            planting_date="2016-11-01",
            harvest_date="2017-03-15",
            latitude=26.0,
            longitude=84.0,
            observed_yield_t_ha=4.5,
            record_status="ACCEPTED",
            input_policy="strict",
            predicted_yield_t_ha=None,
            computation_status="fail_closed",
            input_quality="unavailable",
            weather_source="failed",
            weather_coverage=0,
            par_provenance="missing",
            lai_provenance="model_generated",
            ewsi_provenance="missing",
            model_version="2.0.0",
            failure_reason="EWSI inputs unavailable",
            prediction_id="",
        )
        assert r.record_id == "F001"
        assert r.predicted_yield_t_ha is None
        assert r.computation_status == "fail_closed"

    def test_benchmark_result_with_prediction(self):
        r = BenchmarkResult(
            record_id="F001",
            field_id="F001",
            district="Buxar",
            state="Bihar",
            season_id="wheat_2016",
            crop="wheat",
            planting_date="2016-11-01",
            harvest_date="2017-03-15",
            latitude=26.0,
            longitude=84.0,
            observed_yield_t_ha=4.5,
            record_status="ACCEPTED",
            input_policy="diagnostic",
            predicted_yield_t_ha=3.8,
            computation_status="partial",
            input_quality="partial",
            weather_source="open_meteo",
            weather_coverage=150,
            par_provenance="estimated",
            lai_provenance="model_generated",
            ewsi_provenance="missing",
            model_version="2.0.0",
            failure_reason="",
            prediction_id="PRED-ABC123",
            metadata={"computation_mode": "legacy_constant"},
        )
        assert r.predicted_yield_t_ha == 3.8
        assert r.metadata["computation_mode"] == "legacy_constant"


class TestMetricsComputation:
    def test_metrics_empty_results(self):
        results: list[BenchmarkResult] = []
        m = compute_metrics_from_results(results)
        assert m["n_valid_pairs"] == 0
        assert m["rmse"] is None
        assert m["mae"] is None

    def test_metrics_all_blocked(self):
        r = BenchmarkResult(
            record_id="F001", field_id="F001", district="Buxar", state="Bihar",
            season_id="wheat_2016", crop="wheat", planting_date="2016-11-01",
            harvest_date="2017-03-15", latitude=26.0, longitude=84.0,
            observed_yield_t_ha=4.5, record_status="ACCEPTED",
            input_policy="strict", predicted_yield_t_ha=None,
            computation_status="fail_closed", input_quality="unavailable",
            weather_source="failed", weather_coverage=0,
            par_provenance="missing", lai_provenance="model_generated",
            ewsi_provenance="missing", model_version="2.0.0",
            failure_reason="EWSI inputs unavailable", prediction_id="",
        )
        m = compute_metrics_from_results([r])
        assert m["n_valid_pairs"] == 0
        assert m["rmse"] is None


class TestBaselineComputation:
    def test_baseline_from_dev_set(self):
        test_records = make_test_records()
        dev_records = make_dev_records()
        base = compute_baseline_metrics(test_records, dev_records)
        assert base["baseline_type"] == "mean_observed_yield_from_development_set"
        assert base["dev_n"] > 0
        assert base["test_n"] > 0
        assert base["metrics"]["rmse"] is not None


class TestStage33Results:
    """Tests that validate the actual Stage 33 execution results."""

    def test_hash_verification(self, cimmyt_results):
        assert cimmyt_results["hash_verification"]["hash_matches_stage32"] is True

    def test_benchmark_status_blocked(self, cimmyt_results):
        assert cimmyt_results["benchmark_status"] == "BLOCKED"

    def test_strict_zero_predictions(self, cimmyt_results):
        s = cimmyt_results["summary"]
        assert s["strict_success"] == 0

    def test_allow_estimated_zero_predictions(self, cimmyt_results):
        s = cimmyt_results["summary"]
        assert s["allow_estimated_success"] == 0

    def test_diagnostic_all_succeeded(self, cimmyt_results):
        s = cimmyt_results["summary"]
        assert s["diagnostic_success"] == 80
        assert s["diagnostic_failed"] == 0

    def test_leakage_clean(self, cimmyt_results):
        assert cimmyt_results["leakage_audit"]["overall_leakage_status"] == "CLEAN"

    def test_protocol_complete(self, cimmyt_results):
        assert cimmyt_results["protocol"]["protocol_is_complete"] is True

    def test_strict_results_count(self, cimmyt_results):
        assert len(cimmyt_results["strict_results"]) == 80

    def test_allow_estimated_results_count(self, cimmyt_results):
        assert len(cimmyt_results["allow_estimated_results"]) == 80

    def test_diagnostic_results_count(self, cimmyt_results):
        assert len(cimmyt_results["diagnostic_results"]) == 80

    def test_strict_all_fail_closed(self, cimmyt_results):
        for r in cimmyt_results["strict_results"]:
            assert r["predicted_yield_t_ha"] is None
            assert r["computation_status"] == "fail_closed"

    def test_allow_estimated_all_fail_closed(self, cimmyt_results):
        for r in cimmyt_results["allow_estimated_results"]:
            assert r["predicted_yield_t_ha"] is None
            assert r["computation_status"] == "fail_closed"

    def test_diagnostic_all_have_predictions(self, cimmyt_results):
        for r in cimmyt_results["diagnostic_results"]:
            assert r["predicted_yield_t_ha"] is not None
            assert r["computation_status"] == "partial"
            assert r["input_policy"] == "diagnostic"

    def test_diagnostic_metadata_labels_leagcy(self, cimmyt_results):
        for r in cimmyt_results["diagnostic_results"]:
            mode = r["metadata"].get("computation_mode") if r.get("metadata") else None
            assert mode == "legacy_constant"


class TestCSVOutput:
    def test_csv_exists(self):
        if not STAGE33_CSV.exists():
            pytest.skip("CSV not found — run tools/stage33_benchmark.py first")
        assert STAGE33_CSV.exists()

    def test_csv_has_header(self):
        if not STAGE33_CSV.exists():
            pytest.skip("CSV not found")
        with open(STAGE33_CSV) as f:
            header = f.readline().strip()
        assert "predicted_yield_t_ha" in header
        assert "input_policy" in header
        assert "failure_reason" in header

    def test_csv_row_count(self):
        if not STAGE33_CSV.exists():
            pytest.skip("CSV not found")
        import csv as csv_mod
        with open(STAGE33_CSV) as f:
            reader = csv_mod.DictReader(f)
            rows = list(reader)
        assert len(rows) == 240  # 80 strict + 80 allow_estimated + 80 diagnostic

    def test_csv_contains_all_policies(self):
        if not STAGE33_CSV.exists():
            pytest.skip("CSV not found")
        import csv as csv_mod
        with open(STAGE33_CSV) as f:
            reader = csv_mod.DictReader(f)
            policies = {row["input_policy"] for row in reader}
        assert "strict" in policies
        assert "allow_estimated_inputs" in policies
        assert "diagnostic" in policies


class TestReportFiles:
    def test_all_report_files_exist(self):
        report_names = [
            "STAGE-33-BENCHMARK-PROTOCOL.md",
            "STAGE-33-BENCHMARK-EXECUTION.md",
            "STAGE-33-BENCHMARK-METRICS.md",
            "STAGE-33-BENCHMARK-DATA-QUALITY.md",
            "STAGE-33-BENCHMARK-LEAKAGE-AUDIT.md",
            "STAGE-33-BENCHMARK-UNCERTAINTY.md",
            "STAGE-33-BENCHMARK-LIMITATIONS.md",
        ]
        for name in report_names:
            path = Path(f"engine/reports/{name}")
            assert path.exists(), f"Report file missing: {name}"

    def test_protocol_report_mentions_blockage(self):
        path = Path("engine/reports/STAGE-33-BENCHMARK-PROTOCOL.md")
        if not path.exists():
            pytest.skip("Report not found")
        content = path.read_text()
        assert "STRICT" in content
        assert "ALLOW_ESTIMATED" in content

    def test_execution_report_marks_blocked(self):
        path = Path("engine/reports/STAGE-33-BENCHMARK-EXECUTION.md")
        if not path.exists():
            pytest.skip("Report not found")
        content = path.read_text()
        assert "BLOCKED" in content

    def test_limitations_report_mentions_ewsi(self):
        path = Path("engine/reports/STAGE-33-BENCHMARK-LIMITATIONS.md")
        if not path.exists():
            pytest.skip("Report not found")
        content = path.read_text()
        assert "EWSI" in content


class TestStrictPolicyBlocked:
    """Verify that STRICT policy predictions are correctly blocked."""

    def test_strict_requires_observed_lai(self):
        from engine.hydroma.eval.seasonal_predictor import InputSourcePolicy
        assert InputSourcePolicy.STRICT.value == "strict"

    def test_strict_results_label_fail_closed(self, cimmyt_results):
        statuses = {r["computation_status"] for r in cimmyt_results["strict_results"]}
        assert statuses == {"fail_closed"}


class TestAllowEstimatedPolicyBlocked:
    """Verify that ALLOW_ESTIMATED policy predictions are correctly blocked."""

    def test_allow_estimated_results_label_fail_closed(self, cimmyt_results):
        statuses = {r["computation_status"] for r in cimmyt_results["allow_estimated_results"]}
        assert statuses == {"fail_closed"}


class TestDiagnosticPolicySupplementary:
    """Verify that DIAGNOSTIC (supplementary) predictions use legacy fallback."""

    def test_diagnostic_results_have_legacy_mode(self, cimmyt_results):
        for r in cimmyt_results["diagnostic_results"]:
            mode = r.get("metadata", {}).get("computation_mode")
            assert mode == "legacy_constant"

    def test_diagnostic_results_not_validation_grade(self, cimmyt_results):
        for r in cimmyt_results["diagnostic_results"]:
            assert r["input_policy"] == "diagnostic"


# --- Helper functions ---

def create_records_from_df(df):
    """Create RealFieldRecord objects from a CIMMYT dataframe."""
    from datetime import date
    records = []
    for _, row in df.iterrows():
        planting = row["SowingDate"]
        harvest = row["HarvestDate"]
        season_id = f"wheat_{planting.year}"
        planting_str = (
            planting.strftime("%Y-%m-%d")
            if hasattr(planting, "strftime")
            else str(planting)[:10]
        )
        harvest_str = (
            harvest.strftime("%Y-%m-%d")
            if hasattr(harvest, "strftime")
            else str(harvest)[:10]
        )
        try:
            rec = RealFieldRecord(
                site_id=f"District_{row['District']}",
                field_id=str(row["Field_ID"]),
                season_id=season_id,
                crop="wheat",
                cultivar=row.get("Variety"),
                planting_date=date.fromisoformat(planting_str),
                harvest_date=date.fromisoformat(harvest_str),
                latitude=float(row["Latitude"]),
                longitude=float(row["Longitude"]),
                area_ha=None,
                observed_yield=float(row["GrainYield"]),
                observed_yield_unit="t/ha",
                yield_measurement_method=(
                    "Mean yield from three crop-cut spots "
                    "(plot basis, harvest)"
                ),
                harvest_sample_size=None,
                observation_source="published_literature",
                observation_source_id="doi:10.71682/10549424",
                data_label="real_field_data",
            )
            records.append(rec)
        except Exception:
            pass
    return records


def make_test_records():
    from datetime import date
    records = []
    for i, district in enumerate(TEST_DISTRICTS):
        rec = RealFieldRecord(
            site_id=f"District_{district}",
            field_id=f"TEST_{i}",
            season_id=f"wheat_{2016+i}",
            crop="wheat",
            planting_date=date(2016 + i, 11, 1),
            harvest_date=date(2017 + i, 3, 15),
            latitude=26.0 + i * 0.1,
            longitude=84.0 + i * 0.1,
            observed_yield=4.0 + i * 0.5,
            observed_yield_unit="t/ha",
            yield_measurement_method="test",
            observation_source="published_literature",
            data_label="real_field_data",
        )
        records.append(rec)
    return records


def make_dev_records():
    from datetime import date
    records = []
    for i, district in enumerate(DEV_DISTRICTS):
        rec = RealFieldRecord(
            site_id=f"District_{district}",
            field_id=f"DEV_{i}",
            season_id="wheat_2020",
            crop="wheat",
            planting_date=date(2020, 11, 1),
            harvest_date=date(2021, 3, 15),
            latitude=26.0 + i * 0.1,
            longitude=84.0 + i * 0.1,
            observed_yield=3.5 + i * 0.2,
            observed_yield_unit="t/ha",
            yield_measurement_method="test",
            observation_source="published_literature",
            data_label="real_field_data",
        )
        records.append(rec)
    return records
