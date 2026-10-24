"""Tests for Stage 25: Field data contracts, ingestion, evaluation datasets,
and PAR provenance fix.

Tests cover:
- Field data contract validation (SiteInfo, SeasonInfo, FieldObservation)
- Data ingestion from CSV and JSON with quality controls
- Dataset versioning and data-leakage-prevention splits
- PAR provenance fix: satellite_retrieved vs observed (backward compatible)

Matching, prediction status, scenario tracking and integration tests live in
``test_stage25_prediction_scenarios.py`` (split to stay under the 800-line
module ceiling).
"""

from __future__ import annotations

import json

import pytest

from engine.hydroma.eval import (
    CSVIngester,
    DatasetVersion,
    EvaluationDataset,
    EvaluationDatasetManager,
    FieldObservation,
    IngestionResult,
    ObservationSource,
    QualityReport,
    SeasonInfo,
    SiteInfo,
    VariableType,
    ingest_csv,
    ingest_json,
)
from engine.hydroma.simulation.par_pipeline import (
    build_seasonal_climate_inputs,
)
from engine.hydroma.simulation.weather_source import (
    PAR_SOURCE_NOT_CONVERTED,
    normalize_par_provenance,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_weather_df(
    n_days: int = 10,
    with_shortwave: bool = True,
    with_direct_par: bool = False,
) -> object:
    """Build a minimal weather DataFrame for testing."""
    import pandas as pd

    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    data: dict[str, object] = {
        "MinTemp": [5.0 + 0.5 * i for i in range(n_days)],
        "MaxTemp": [15.0 + 0.5 * i for i in range(n_days)],
        "Precipitation": [0.0] * n_days,
        "ReferenceET": [2.5] * n_days,
        "Date": dates,
    }
    if with_shortwave:
        data["ShortwaveRadiation"] = [10.5] * n_days
    if with_direct_par:
        data["PAR"] = [5.0] * n_days
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df.attrs["shortwave_unit"] = "MJ/m^2/day"
    df.attrs["shortwave_source"] = "test_source"
    df.attrs["shortwave_source_parameter"] = "shortwave_radiation_sum"
    if with_direct_par:
        df.attrs["par_unit"] = "MJ/m^2/day"
        df.attrs["par_source"] = "NASA POWER"
        df.attrs["par_source_parameter"] = "ALLSKY_SFC_PAR_TOT"
        df.attrs["par_source_reference"] = "NASA POWER CERES SYN1deg Ed. 4.2"
    return df


def _make_site_info(site_id: str = "SITE001") -> dict[str, object]:
    return {
        "site_id": site_id,
        "name": "Test Farm",
        "latitude": 40.0,
        "longitude": -105.0,
        "elevation_m": 1600.0,
        "country": "US",
        "admin_region": "CO",
        "dataset": "test_dataset",
    }


def _make_season_info(season_id: str = "wheat_2024") -> dict[str, object]:
    return {
        "crop": "wheat",
        "planting_date": "2024-03-15",
        "harvest_date": "2024-07-15",
        "season_length_days": 122,
        "growing_degree_days": 1200.0,
    }


def _make_observation_row(
    site_id: str, season_id: str, variable: str, value: float
) -> dict[str, object]:
    return {
        "site_id": site_id,
        "season_id": season_id,
        "date": "2024-06-15",
        "variable": variable,
        "value": value,
        "unit": "t/ha",
        "source": "field_measured",
        "quality_flag": "good",
    }


# ---------------------------------------------------------------------------
# Section 1: Field data contracts
# ---------------------------------------------------------------------------


class TestSiteInfo:
    def test_valid_site_info(self):
        site = SiteInfo(**_make_site_info())
        assert site.site_id == "SITE001"
        assert site.latitude == 40.0
        assert site.longitude == -105.0
        assert site.elevation_m == 1600.0

    def test_site_info_rejects_lat_out_of_range(self):
        data = _make_site_info()
        data["latitude"] = 95.0
        with pytest.raises(ValueError):
            SiteInfo(**data)

    def test_site_info_rejects_lon_out_of_range(self):
        data = _make_site_info()
        data["longitude"] = -200.0
        with pytest.raises(ValueError):
            SiteInfo(**data)

    def test_site_info_rejects_empty_site_id(self):
        data = _make_site_info()
        data["site_id"] = ""
        with pytest.raises(ValueError):
            SiteInfo(**data)

    def test_site_info_rejects_extra_field(self):
        data = _make_site_info()
        data["extra_field"] = "should_fail"
        with pytest.raises(ValueError):
            SiteInfo(**data)

    def test_site_info_country_2char(self):
        site = SiteInfo(**_make_site_info())
        assert len(site.country) == 2

    def test_site_info_country_too_short(self):
        data = _make_site_info()
        data["country"] = "U"
        with pytest.raises(ValueError):
            SiteInfo(**data)


class TestSeasonInfo:
    def test_valid_season_info(self):
        season = SeasonInfo(**_make_season_info())
        assert season.crop == "wheat"
        assert season.season_length_days == 122

    def test_season_info_rejects_harvest_before_planting(self):
        data = _make_season_info()
        data["planting_date"] = "2024-07-15"
        data["harvest_date"] = "2024-03-15"
        with pytest.raises(ValueError, match="must not precede"):
            SeasonInfo(**data)

    def test_season_info_rejects_mismatched_length(self):
        data = _make_season_info()
        data["season_length_days"] = 10  # doesn't match July 15 - March 15
        with pytest.raises(ValueError, match="does not match"):
            SeasonInfo(**data)

    def test_season_info_rejects_negative_season_length(self):
        data = _make_season_info()
        data["season_length_days"] = -5
        with pytest.raises(ValueError):
            SeasonInfo(**data)

    def test_season_info_rejects_too_long_season(self):
        data = _make_season_info()
        data["season_length_days"] = 400
        with pytest.raises(ValueError):
            SeasonInfo(**data)

    def test_season_info_rejects_extra_field(self):
        data = _make_season_info()
        data["extra"] = "fail"
        with pytest.raises(ValueError):
            SeasonInfo(**data)


class TestFieldObservation:
    def test_valid_observation(self):
        obs = FieldObservation(
            site="SITE001",
            season="wheat_2024",
            observation_id="obs_001",
            variable=VariableType.YIELD,
            value=5.2,
            unit="t/ha",
            observation_date="2024-07-15",
            source=ObservationSource.FIELD_MEASURED,
            quality_flag="good",
        )
        assert obs.value == 5.2
        assert obs.variable == VariableType.YIELD
        assert obs.source == ObservationSource.FIELD_MEASURED

    def test_observation_rejects_nan_value(self):
        with pytest.raises(ValueError, match="value must be finite"):
            FieldObservation(
                site="SITE001",
                season="wheat_2024",
                observation_id="obs_001",
                variable=VariableType.YIELD,
                value=float("nan"),
                unit="t/ha",
                observation_date="2024-07-15",
                source=ObservationSource.FIELD_MEASURED,
            )

    def test_observation_rejects_inf_value(self):
        with pytest.raises(ValueError, match="value must be finite"):
            FieldObservation(
                site="SITE001",
                season="wheat_2024",
                observation_id="obs_001",
                variable=VariableType.YIELD,
                value=float("inf"),
                unit="t/ha",
                observation_date="2024-07-15",
                source=ObservationSource.FIELD_MEASURED,
            )

    def test_observation_rejects_unknown_variable(self):
        with pytest.raises(ValueError):
            FieldObservation(
                site="SITE001",
                season="wheat_2024",
                observation_id="obs_001",
                variable="unknown_variable",
                value=5.2,
                unit="t/ha",
                observation_date="2024-07-15",
                source=ObservationSource.FIELD_MEASURED,
            )

    def test_observation_rejects_bad_quality_flag(self):
        with pytest.raises(ValueError, match="not in"):
            FieldObservation(
                site="SITE001",
                season="wheat_2024",
                observation_id="obs_001",
                variable=VariableType.YIELD,
                value=5.2,
                unit="t/ha",
                observation_date="2024-07-15",
                source=ObservationSource.FIELD_MEASURED,
                quality_flag="invalid_flag",
            )

    def test_observation_accepts_all_quality_flags(self):
        for flag in ["good", "suspect", "bad", "missing", "estimated"]:
            obs = FieldObservation(
                site="SITE001",
                season="wheat_2024",
                observation_id="obs_001",
                variable=VariableType.YIELD,
                value=5.2,
                unit="t/ha",
                observation_date="2024-07-15",
                source=ObservationSource.FIELD_MEASURED,
                quality_flag=flag,
            )
            assert obs.quality_flag == flag

    def test_observation_rejects_extra_field(self):
        with pytest.raises(ValueError):
            FieldObservation(
                site="SITE001",
                season="wheat_2024",
                observation_id="obs_001",
                variable=VariableType.YIELD,
                value=5.2,
                unit="t/ha",
                observation_date="2024-07-15",
                source=ObservationSource.FIELD_MEASURED,
                extra_field="not_allowed",
            )

    def test_observation_source_enum_from_label(self):
        assert (
            ObservationSource.from_label("field_measured")
            == ObservationSource.FIELD_MEASURED
        )
        assert (
            ObservationSource.from_label("satellite_retrieved")
            == ObservationSource.SATELLITE_RETRIEVED
        )
        assert (
            ObservationSource.from_label("analysis_product")
            == ObservationSource.ANALYSIS_PRODUCT
        )
        assert (
            ObservationSource.from_label("model_generated")
            == ObservationSource.MODEL_GENERATED
        )

    def test_observation_source_enum_unknown_label(self):
        with pytest.raises(ValueError, match="Unknown observation source"):
            ObservationSource.from_label("bogus")


class TestEvaluationDataset:
    def test_empty_dataset(self):
        ds = EvaluationDataset(name="test", version="1.0.0")
        assert ds.observations == []
        assert ds.sites == {}
        assert ds.seasons == {}

    def test_get_observations_by_variable(self):
        ds = EvaluationDataset(name="test", version="1.0.0")
        ds.observations = [
            FieldObservation(
                site="S1", season="season1", observation_id="0",
                variable=VariableType.YIELD, value=5.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
            ),
            FieldObservation(
                site="S1", season="season1", observation_id="1",
                variable=VariableType.LAI, value=3.0, unit="index",
                observation_date="2024-06-15", source=ObservationSource.SATELLITE_RETRIEVED,
            ),
        ]
        yield_obs = ds.get_observations(variable=VariableType.YIELD)
        assert len(yield_obs) == 1
        assert yield_obs[0].variable == VariableType.YIELD

    def test_get_observations_by_site(self):
        ds = EvaluationDataset(name="test", version="1.0.0")
        ds.observations = [
            FieldObservation(
                site="S1", season="season1", observation_id="0",
                variable=VariableType.YIELD, value=5.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
            ),
            FieldObservation(
                site="S2", season="season1", observation_id="1",
                variable=VariableType.YIELD, value=4.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
            ),
        ]
        s1_obs = ds.get_observations(site_id="S1")
        assert len(s1_obs) == 1
        assert s1_obs[0].site == "S1"

    def test_get_observations_by_min_quality(self):
        ds = EvaluationDataset(name="test", version="1.0.0")
        ds.observations = [
            FieldObservation(
                site="S1", season="s1", observation_id="0",
                variable=VariableType.YIELD, value=5.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
                quality_flag="good",
            ),
            FieldObservation(
                site="S1", season="s1", observation_id="1",
                variable=VariableType.YIELD, value=4.0, unit="t/ha",
                observation_date="2024-07-16", source=ObservationSource.FIELD_MEASURED,
                quality_flag="bad",
            ),
            FieldObservation(
                site="S1", season="s1", observation_id="2",
                variable=VariableType.YIELD, value=3.0, unit="t/ha",
                observation_date="2024-07-17", source=ObservationSource.FIELD_MEASURED,
                quality_flag="suspect",
            ),
        ]
        good_only = ds.get_observations(min_quality="good")
        assert len(good_only) == 1
        good_and_suspect = ds.get_observations(min_quality="suspect")
        assert len(good_and_suspect) == 2
        all_obs = ds.get_observations(min_quality="bad")
        assert len(all_obs) == 3


# ---------------------------------------------------------------------------
# Section 2: PAR provenance fix
# ---------------------------------------------------------------------------


class TestParProvenanceFix:
    def test_normalize_observed_maps_to_satellite_retrieved(self):
        assert normalize_par_provenance("observed") == "satellite_retrieved"

    def test_normalize_satellite_retrieved_unchanged(self):
        assert normalize_par_provenance("satellite_retrieved") == "satellite_retrieved"

    def test_normalize_field_measured_unchanged(self):
        assert normalize_par_provenance("field_measured") == "field_measured"

    def test_normalize_none_returns_not_converted(self):
        assert normalize_par_provenance(None) == PAR_SOURCE_NOT_CONVERTED

    def test_normalize_unknown_passthrough(self):
        assert normalize_par_provenance("bogus") == "bogus"

    def test_build_seasonal_with_direct_par_uses_satellite_retrieved(self):
        df = _make_weather_df(with_direct_par=True, with_shortwave=True)
        inputs = build_seasonal_climate_inputs(df)
        assert inputs.par_provenance == "satellite_retrieved"

    def test_build_seasonal_with_direct_par_spec_status_satellite_retrieved(self):
        df = _make_weather_df(with_direct_par=True, with_shortwave=True)
        inputs = build_seasonal_climate_inputs(df)
        assert inputs.par_conversion_spec.status == "satellite_retrieved"

    def test_build_seasonal_shortwave_only_still_estimated(self):
        df = _make_weather_df(with_direct_par=False, with_shortwave=True)
        inputs = build_seasonal_climate_inputs(df)
        assert inputs.par_provenance == "converted_documented"


# ---------------------------------------------------------------------------
# Section 3: Data ingestion
# ---------------------------------------------------------------------------


class TestCSVIngestion:
    def test_ingest_valid_csv(self, tmp_path):
        csv_content = (
            "site_id,season_id,date,variable,value,unit,source,quality_flag\n"
            "S1,wheat_2024,2024-07-15,yield,5.2,t/ha,field_measured,good\n"
            "S1,wheat_2024,2024-06-15,lai,3.5,index,satellite_retrieved,good\n"
        )
        csv_file = tmp_path / "observations.csv"
        csv_file.write_text(csv_content)

        result = ingest_csv(csv_file, dataset_name="test_ds", dataset_version="1.0.0")
        assert isinstance(result, IngestionResult)
        assert result.quality_report.total_rows == 2
        assert result.quality_report.rows_accepted == 2
        assert result.quality_report.rows_rejected == 0
        assert len(result.dataset.observations) == 2
        assert len(result.raw_rows) == 2

    def test_ingest_csv_missing_columns(self, tmp_path):
        csv_content = (
            "site_id,variable,value\n"
            "S1,yield,5.2\n"
        )
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(csv_content)

        result = ingest_csv(csv_file, dataset_name="test_ds", dataset_version="1.0.0")
        assert result.quality_report.rows_rejected == 0
        assert result.quality_report.errors
        assert "Missing required columns" in result.quality_report.errors[0]

    def test_ingest_csv_duplicate_detection(self, tmp_path):
        csv_content = (
            "site_id,season_id,date,variable,value,unit,source,quality_flag\n"
            "S1,wheat_2024,2024-07-15,yield,5.2,t/ha,field_measured,good\n"
            "S1,wheat_2024,2024-07-15,yield,5.3,t/ha,field_measured,good\n"
        )
        csv_file = tmp_path / "dups.csv"
        csv_file.write_text(csv_content)

        result = ingest_csv(csv_file, dataset_name="test_ds", dataset_version="1.0.0")
        assert result.quality_report.duplicates == 1
        assert len(result.dataset.observations) == 1
        assert len(result.quality_report.duplicates_detail) == 1

    def test_ingest_csv_rejects_bad_value(self, tmp_path):
        csv_content = (
            "site_id,season_id,date,variable,value,unit,source,quality_flag\n"
            "S1,wheat_2024,2024-07-15,yield,not_a_number,t/ha,field_measured,good\n"
        )
        csv_file = tmp_path / "bad_val.csv"
        csv_file.write_text(csv_content)

        result = ingest_csv(csv_file, dataset_name="test_ds", dataset_version="1.0.0")
        assert result.quality_report.rows_rejected == 1
        assert result.quality_report.errors

    def test_ingest_csv_invalid_variable(self, tmp_path):
        csv_content = (
            "site_id,season_id,date,variable,value,unit,source,quality_flag\n"
            "S1,wheat_2024,2024-07-15,unknown_var,5.2,t/ha,field_measured,good\n"
        )
        csv_file = tmp_path / "bad_var.csv"
        csv_file.write_text(csv_content)

        result = ingest_csv(csv_file, dataset_name="test_ds", dataset_version="1.0.0")
        assert result.quality_report.rows_rejected == 1

    def test_ingest_csv_raw_data_preserved(self, tmp_path):
        csv_content = (
            "site_id,season_id,date,variable,value,unit,source,quality_flag,notes\n"
            "S1,wheat_2024,2024-07-15,yield,5.2,t/ha,field_measured,good,plot_A\n"
        )
        csv_file = tmp_path / "raw.csv"
        csv_file.write_text(csv_content)

        result = ingest_csv(csv_file, dataset_name="test_ds", dataset_version="1.0.0")
        assert len(result.raw_rows) == 1
        assert result.raw_rows[0]["site_id"] == "S1"
        assert result.raw_rows[0]["notes"] == "plot_A"

    def test_ingest_csv_with_site_metadata(self, tmp_path):
        csv_content = (
            "site_id,season_id,date,variable,value,unit,source,quality_flag\n"
            "S1,wheat_2024,2024-07-15,yield,5.2,t/ha,field_measured,good\n"
        )
        csv_file = tmp_path / "obs.csv"
        csv_file.write_text(csv_content)

        site_meta = {"S1": _make_site_info()}
        season_meta = {"wheat_2024": _make_season_info()}
        result = ingest_csv(
            csv_file, dataset_name="test_ds", dataset_version="1.0.0",
            site_metadata=site_meta, season_metadata=season_meta,
        )
        assert "S1" in result.dataset.sites
        assert "wheat_2024" in result.dataset.seasons

    def test_csv_ingester_class_directly(self, tmp_path):
        csv_content = (
            "site_id,season_id,date,variable,value,unit,source,quality_flag\n"
            "S1,s1,2024-07-15,yield,5.2,t/ha,field_measured,good\n"
        )
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        ingester = CSVIngester(dataset_name="ds", dataset_version="2.0.0")
        result = ingester.ingest(csv_file)
        assert result.dataset.name == "ds"
        assert result.dataset.version == "2.0.0"


class TestJSONIngestion:
    def test_ingest_valid_json(self, tmp_path):
        records = [
            {
                "site_id": "S1", "season_id": "wheat_2024", "date": "2024-07-15",
                "variable": "yield", "value": 5.2, "unit": "t/ha",
                "source": "field_measured", "quality_flag": "good",
            },
            {
                "site_id": "S1", "season_id": "wheat_2024", "date": "2024-06-15",
                "variable": "lai", "value": 3.5, "unit": "index",
                "source": "satellite_retrieved", "quality_flag": "good",
            },
        ]
        json_file = tmp_path / "observations.json"
        json_file.write_text(json.dumps(records))

        result = ingest_json(json_file, dataset_name="json_ds", dataset_version="1.0.0")
        assert result.quality_report.total_rows == 2
        assert result.quality_report.rows_accepted == 2
        assert len(result.dataset.observations) == 2

    def test_ingest_json_not_array_raises(self, tmp_path):
        json_file = tmp_path / "bad.json"
        json_file.write_text(json.dumps({"key": "value"}))

        with pytest.raises(ValueError, match="top-level array"):
            ingest_json(json_file, dataset_name="ds", dataset_version="1.0.0")

    def test_ingest_json_missing_keys(self, tmp_path):
        records = [
            {"site_id": "S1", "date": "2024-07-15", "variable": "yield"},
        ]
        json_file = tmp_path / "missing_keys.json"
        json_file.write_text(json.dumps(records))

        result = ingest_json(json_file, dataset_name="ds", dataset_version="1.0.0")
        assert result.quality_report.rows_rejected == 1
        assert "missing keys" in result.quality_report.errors[0].lower()


class TestQualityReport:
    def test_quality_report_acceptance_rate(self):
        report = QualityReport(total_rows=10, rows_accepted=8, rows_rejected=2)
        assert report.acceptance_rate == pytest.approx(0.8)

    def test_quality_report_zero_rows(self):
        report = QualityReport()
        assert report.acceptance_rate == 0.0


# ---------------------------------------------------------------------------
# Section 4: Dataset versioning and splits
# ---------------------------------------------------------------------------


class TestDatasetVersion:
    def test_version_from_dataset(self):
        ds = EvaluationDataset(name="test", version="1.0.0")
        ds.observations = [
            FieldObservation(
                site="S1", season="s1", observation_id="0",
                variable=VariableType.YIELD, value=5.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
            ),
        ]
        version = DatasetVersion.from_dataset(ds)
        assert version.name == "test"
        assert version.version == "1.0.0"
        assert len(version.checksum) == 64  # SHA-256 hex
        assert version.created_at

    def test_version_deterministic(self):
        ds1 = EvaluationDataset(name="test", version="1.0.0")
        ds1.observations = [
            FieldObservation(
                site="S1", season="s1", observation_id="0",
                variable=VariableType.YIELD, value=5.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
            ),
        ]
        ds2 = EvaluationDataset(name="test", version="1.0.0")
        ds2.observations = list(ds1.observations)
        v1 = DatasetVersion.from_dataset(ds1)
        v2 = DatasetVersion.from_dataset(ds2)
        assert v1.checksum == v2.checksum

    def test_version_different_if_observations_differ(self):
        ds1 = EvaluationDataset(name="test", version="1.0.0")
        ds1.observations = [
            FieldObservation(
                site="S1", season="s1", observation_id="0",
                variable=VariableType.YIELD, value=5.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
            ),
        ]
        ds2 = EvaluationDataset(name="test", version="1.0.0")
        ds2.observations = [
            FieldObservation(
                site="S1", season="s1", observation_id="0",
                variable=VariableType.YIELD, value=6.0, unit="t/ha",
                observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
            ),
        ]
        v1 = DatasetVersion.from_dataset(ds1)
        v2 = DatasetVersion.from_dataset(ds2)
        assert v1.checksum != v2.checksum


class TestDataSplits:
    def _make_dataset(
        self, n_sites: int = 4, n_seasons: int = 2, obs_per: int = 2
    ) -> EvaluationDataset:
        ds = EvaluationDataset(name="test", version="1.0.0")
        obs_list = []
        for i in range(n_sites):
            for j in range(n_seasons):
                for k in range(obs_per):
                    obs_list.append(
                        FieldObservation(
                            site=f"S{i}", season=f"s{j}", observation_id=f"o{k}",
                            variable=VariableType.YIELD, value=float(k + 1),
                            unit="t/ha", observation_date="2024-07-15",
                            source=ObservationSource.FIELD_MEASURED,
                        )
                    )
        ds.observations = obs_list
        return ds

    def test_combined_split_no_leakage(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split = manager.get_split("test", method="combined", seed=42)
        assert split.is_leak_free
        assert split.train_size > 0
        assert split.validation_size > 0 or split.test_size > 0

    def test_combined_split_pair_no_overlap(self):
        """Combined split guarantees no (site, season) pair appears in two splits."""
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split = manager.get_split("test", method="combined", seed=42)
        assert len(split.train_pairs & split.validation_pairs) == 0
        assert len(split.train_pairs & split.test_pairs) == 0
        assert len(split.validation_pairs & split.test_pairs) == 0

    def test_combined_split_site_no_pair_overlap(self):
        """Combined split prevents pair-level site/season overlap (the guarantee)."""
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split = manager.get_split("test", method="combined", seed=42)
        assert len(split.train_pairs & split.test_pairs) == 0
        assert len(split.train_pairs & split.validation_pairs) == 0
        assert len(split.validation_pairs & split.test_pairs) == 0

    def test_season_split_prevents_season_overlap(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split = manager.get_split("test", method="season", seed=42)
        assert len(split.train_season_ids & split.validation_season_ids) == 0
        assert len(split.train_season_ids & split.test_season_ids) == 0
        assert len(split.validation_season_ids & split.test_season_ids) == 0

    def test_site_split_prevents_site_overlap(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split = manager.get_split("test", method="site", seed=42)
        assert len(split.train_site_ids & split.validation_site_ids) == 0
        assert len(split.train_site_ids & split.test_site_ids) == 0
        assert len(split.validation_site_ids & split.test_site_ids) == 0

    def test_split_reproducible_with_seed(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split1 = manager.get_split("test", method="combined", seed=42)
        split2 = manager.get_split("test", method="combined", seed=42)
        assert split1.train_size == split2.train_size
        assert split1.train_season_ids == split2.train_season_ids

    def test_split_different_seed_different_result(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split1 = manager.get_split("test", method="combined", seed=42)
        split2 = manager.get_split("test", method="combined", seed=99)
        assert split1.train_pairs != split2.train_pairs

    def test_split_summary(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split = manager.get_split("test", method="combined", seed=42)
        summary = split.summary()
        assert summary["method"] == "combined"
        assert summary["seed"] == 42
        assert summary["train"] == split.train_size
        assert summary["leak_free"] is True

    def test_random_split_may_have_leakage(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        split = manager.get_split("test", method="random", seed=42)
        assert split.method == "random"

    def test_unknown_dataset_raises(self):
        manager = EvaluationDatasetManager()
        with pytest.raises(KeyError, match="not registered"):
            manager.get_split("nonexistent", method="combined", seed=42)

    def test_unknown_method_raises(self):
        ds = self._make_dataset()
        manager = EvaluationDatasetManager()
        manager.add_dataset("test", ds)
        with pytest.raises(ValueError, match="Unknown split method"):
            manager.get_split("test", method="invalid_method", seed=42)

    def test_manager_list_datasets(self):
        manager = EvaluationDatasetManager()
        ds = EvaluationDataset(name="ds1", version="1.0.0")
        manager.add_dataset("ds1", ds)
        assert manager.list_datasets() == ["ds1"]

    def test_manager_get_version(self):
        manager = EvaluationDatasetManager()
        ds = EvaluationDataset(name="ds1", version="1.0.0")
        manager.add_dataset("ds1", ds)
        version = manager.get_version("ds1")
        assert version.name == "ds1"
        assert version.checksum
