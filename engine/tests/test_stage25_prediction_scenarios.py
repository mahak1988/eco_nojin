"""Tests for Stage 25: Prediction results, matching, and scenario/uncertainty.

Tests cover:
- Prediction result with computation/quality/validation status fields
- HYRUE-to-observation matching with unit conversion
- Scenario tracking and uncertainty aggregation
- Integration: HYRUE seasonal computation with provenance
"""

from __future__ import annotations

import pytest

from engine.honesty.statuses import VOCABULARY
from engine.hydroma.eval import (
    ComputationStatus,
    ExternalValidationStatus,
    FieldObservation,
    InputQuality,
    ObservationSource,
    PredictionResult,
    Scenario,
    ScenarioResult,
    ScientificSupportStatus,
    UncertaintyMethod,
    VariableType,
    aggregate_uncertainty,
    build_default_scenarios,
    match_hyra_to_observations,
    run_scenarios,
)
from engine.hydroma.simulation.par_pipeline import (
    build_seasonal_climate_inputs,
    compute_hyrue_seasonal,
)

# ---------------------------------------------------------------------------
# Section 5: Prediction result and status fields
# ---------------------------------------------------------------------------


class TestComputationStatus:
    def test_all_enum_values(self):
        assert ComputationStatus.COMPUTED.value == "computed"
        assert ComputationStatus.FAIL_CLOSED.value == "fail_closed"
        assert ComputationStatus.PARTIAL.value == "partial"
        assert ComputationStatus.NOT_ATTEMPTED.value == "not_attempted"


class TestExternalValidationStatus:
    def test_all_enum_values(self):
        assert ExternalValidationStatus.VALIDATED_EXTERNAL.value == "VALIDATED_EXTERNAL"
        assert (
            ExternalValidationStatus.VALIDATED_METHOD_CONFORMANCE.value
            == "VALIDATED_METHOD_CONFORMANCE"
        )
        assert ExternalValidationStatus.REGRESSION_ANCHOR_STABLE.value == "REGRESSION_ANCHOR_STABLE"
        assert ExternalValidationStatus.PARTIAL.value == "PARTIAL"
        assert ExternalValidationStatus.UNVALIDATED.value == "UNVALIDATED"
        assert ExternalValidationStatus.BLOCKED.value == "BLOCKED"

    def test_from_vocabulary_accepted(self):
        for term in VOCABULARY:
            status = ExternalValidationStatus.from_vocabulary(term)
            assert status.value == term

    def test_from_vocabulary_legacy_alias(self):
        status = ExternalValidationStatus.from_vocabulary("validated")
        assert status.value == "VALIDATED_EXTERNAL"

    def test_from_vocabulary_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown validation status"):
            ExternalValidationStatus.from_vocabulary("bogus")


class TestScientificSupportStatus:
    def test_all_enum_values(self):
        assert ScientificSupportStatus.REFERENCED.value == "referenced"
        assert ScientificSupportStatus.DEFAULTED.value == "defaulted"
        assert ScientificSupportStatus.PARTIAL.value == "partial"
        assert ScientificSupportStatus.UNVALIDATED.value == "unvalidated"
        assert ScientificSupportStatus.BLOCKED.value == "blocked"


class TestInputQuality:
    def test_all_enum_values(self):
        assert InputQuality.COMPLETE.value == "complete"
        assert InputQuality.PARTIAL.value == "partial"
        assert InputQuality.UNAVAILABLE.value == "unavailable"


class TestPredictionResult:
    def test_minimal_prediction(self):
        pred = PredictionResult(
            prediction_id="pred_001",
            site_id="S1",
            season_id="wheat_2024",
        )
        assert pred.model_name == "HY-RUE"
        assert pred.computation_status == "computed"
        assert pred.external_validation_status == "UNVALIDATED"
        assert pred.input_quality == "complete"
        assert pred.computed is True

    def test_prediction_with_value(self):
        pred = PredictionResult(
            prediction_id="pred_001",
            site_id="S1",
            season_id="wheat_2024",
            value=5.5,
            unit="t/ha",
        )
        assert pred.value == 5.5
        assert pred.unit == "t/ha"

    def test_prediction_with_provenance(self):
        pred = PredictionResult(
            prediction_id="pred_001",
            site_id="S1",
            season_id="wheat_2024",
            par_provenance="satellite_retrieved",
            lai_provenance={"source_model": "ndvi_empirical"},
            ewsi_provenance={"source_model": "composite"},
            shortwave_source="NASA POWER",
        )
        assert pred.par_provenance == "satellite_retrieved"
        assert pred.lai_provenance["source_model"] == "ndvi_empirical"

    def test_prediction_with_uncertainty_interval(self):
        pred = PredictionResult(
            prediction_id="pred_001",
            site_id="S1",
            season_id="wheat_2024",
            value=5.5,
            prediction_interval_lower=4.5,
            prediction_interval_upper=6.5,
            uncertainty_std=0.5,
        )
        assert pred.prediction_interval_lower == 4.5
        assert pred.prediction_interval_upper == 6.5
        assert pred.uncertainty_std == 0.5

    def test_prediction_to_dict(self):
        pred = PredictionResult(
            prediction_id="pred_001",
            site_id="S1",
            season_id="wheat_2024",
            value=5.5,
        )
        d = pred.to_dict()
        assert d["prediction_id"] == "pred_001"
        assert d["value"] == 5.5
        assert d["computation_status"] == "computed"


# ---------------------------------------------------------------------------
# Section 6: HYRUE-to-observation matching
# ---------------------------------------------------------------------------


class TestMatching:
    def test_match_exact(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="yield", value=5.0, unit="t/ha",
        )
        obs = FieldObservation(
            site="S1", season="wheat_2024", observation_id="o1",
            variable=VariableType.YIELD, value=5.5, unit="t/ha",
            observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
        )
        matches = match_hyra_to_observations([pred], [obs])
        assert len(matches) == 1
        m = matches[0]
        assert m.prediction_value == 5.0
        assert m.observed_value == 5.5
        assert m.residual == pytest.approx(0.5)  # observed - prediction
        assert m.relative_error == pytest.approx(0.5 / 5.5)
        assert m.absolute_residual == pytest.approx(0.5)

    def test_match_no_site_match(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="yield", value=5.0, unit="t/ha",
        )
        obs = FieldObservation(
            site="S2", season="wheat_2024", observation_id="o1",
            variable=VariableType.YIELD, value=5.5, unit="t/ha",
            observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
        )
        matches = match_hyra_to_observations([pred], [obs])
        assert len(matches) == 0

    def test_match_no_variable_match(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="yield", value=5.0, unit="t/ha",
        )
        obs = FieldObservation(
            site="S1", season="wheat_2024", observation_id="o1",
            variable=VariableType.LAI, value=3.5, unit="index",
            observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
        )
        matches = match_hyra_to_observations([pred], [obs])
        assert len(matches) == 0

    def test_match_unit_conversion_kg_ha_to_t_ha(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="yield", value=5.0, unit="t/ha",
        )
        obs = FieldObservation(
            site="S1", season="wheat_2024", observation_id="o1",
            variable=VariableType.YIELD, value=5500, unit="kg/ha",
            observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
        )
        matches = match_hyra_to_observations([pred], [obs])
        assert len(matches) == 1
        m = matches[0]
        assert m.observed_value_normalized == pytest.approx(5.5)  # 5500 kg/ha = 5.5 t/ha
        assert m.prediction_value_normalized == pytest.approx(5.0)
        assert m.residual == pytest.approx(0.5)

    def test_match_unit_conversion_g_m2_to_t_ha(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="yield", value=5.0, unit="t/ha",
        )
        obs = FieldObservation(
            site="S1", season="wheat_2024", observation_id="o1",
            variable=VariableType.YIELD, value=500, unit="g/m2",
            observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
        )
        matches = match_hyra_to_observations([pred], [obs])
        assert len(matches) == 1
        m = matches[0]
        assert m.observed_value_normalized == pytest.approx(5.0)  # 500 g/m² = 5.0 t/ha

    def test_match_par_unit_conversion(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="par", value=5.0, unit="MJ/m2/day",
        )
        obs = FieldObservation(
            site="S1", season="wheat_2024", observation_id="o1",
            variable=VariableType.PAR, value=10.0, unit="mol/m2/day",
            observation_date="2024-07-15", source=ObservationSource.SATELLITE_RETRIEVED,
        )
        matches = match_hyra_to_observations([pred], [obs])
        assert len(matches) == 1

    def test_match_multiple_predictions_to_one_observation(self):
        pred1 = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="yield", value=4.5, unit="t/ha",
        )
        pred2 = PredictionResult(
            prediction_id="p2", site_id="S1", season_id="wheat_2024",
            variable="yield", value=5.5, unit="t/ha",
        )
        obs = FieldObservation(
            site="S1", season="wheat_2024", observation_id="o1",
            variable=VariableType.YIELD, value=5.0, unit="t/ha",
            observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
        )
        matches = match_hyra_to_observations([pred1, pred2], [obs])
        assert len(matches) == 2

    def test_match_empty_inputs(self):
        matches = match_hyra_to_observations([], [])
        assert len(matches) == 0

    def test_match_prediction_none_value(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="wheat_2024",
            variable="yield", value=None, unit="t/ha",
        )
        obs = FieldObservation(
            site="S1", season="wheat_2024", observation_id="o1",
            variable=VariableType.YIELD, value=5.5, unit="t/ha",
            observation_date="2024-07-15", source=ObservationSource.FIELD_MEASURED,
        )
        matches = match_hyra_to_observations([pred], [obs])
        assert len(matches) == 1
        assert matches[0].prediction_value == 0.0


# ---------------------------------------------------------------------------
# Section 7: Scenario tracking and uncertainty
# ---------------------------------------------------------------------------


class TestScenario:
    def test_scenario_creation(self):
        scenario = Scenario(
            scenario_id="S001",
            name="par_satellite",
            description="Use satellite PAR",
            input_source_config={"par_source": "satellite_retrieved"},
            par_source="satellite_retrieved",
        )
        assert scenario.scenario_id == "S001"
        assert scenario.par_source == "satellite_retrieved"

    def test_scenario_default_values(self):
        scenario = Scenario(scenario_id="S001", name="default")
        assert scenario.description == ""
        assert scenario.input_source_config == {}
        assert scenario.par_source is None

    def test_scenario_with_climate_priors(self):
        scenario = Scenario(
            scenario_id="S002",
            name="warm_scenario",
            description="2C warming",
            climate_priors={"temp_offset": 2.0},
        )
        assert scenario.climate_priors["temp_offset"] == 2.0


class TestScenarioResult:
    def test_scenario_result_creation(self):
        scenario = Scenario(scenario_id="S001", name="test")
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="s1", value=5.0,
        )
        result = ScenarioResult(
            scenario=scenario,
            prediction=pred,
            input_source_used={"par_source": "satellite_retrieved"},
            uncertainty_method="scenario_spread",
        )
        assert result.scenario.scenario_id == "S001"
        assert result.prediction.value == 5.0
        assert result.uncertainty_method == "scenario_spread"


class TestRunScenarios:
    def test_run_scenarios_basic(self):
        scenarios = [
            Scenario(scenario_id="S1", name="a", input_source_config={"offset": 1}),
            Scenario(scenario_id="S2", name="b", input_source_config={"offset": 2}),
        ]

        def prediction_fn(offset: int = 0, **kwargs) -> PredictionResult:
            return PredictionResult(
                prediction_id=f"pred_{offset}",
                site_id="S1",
                season_id="s1",
                value=5.0 + offset,
            )

        results = run_scenarios(scenarios, prediction_fn)
        assert len(results) == 2
        assert results[0].prediction.value == 6.0
        assert results[1].prediction.value == 7.0

    def test_run_scenarios_empty(self):
        results = run_scenarios([], lambda **kw: PredictionResult(
            prediction_id="p", site_id="S", season_id="s", value=1.0
        ))
        assert len(results) == 0

    def test_run_scenarios_preserves_input_source(self):
        scenario = Scenario(
            scenario_id="S1", name="test",
            input_source_config={"par_source": "satellite_retrieved"},
            par_source="satellite_retrieved",
        )

        def prediction_fn(**kw) -> PredictionResult:
            return PredictionResult(
                prediction_id="p1", site_id="S", season_id="s", value=5.0,
            )

        results = run_scenarios([scenario], prediction_fn)
        assert results[0].input_source_used["par_source"] == "satellite_retrieved"


class TestUncertaintyAggregation:
    def _make_results(self, values: list[float]) -> list[ScenarioResult]:
        return [
            ScenarioResult(
                scenario=Scenario(scenario_id=f"S{i}", name=f"scenario_{i}"),
                prediction=PredictionResult(
                    prediction_id=f"p{i}", site_id="S1", season_id="s1",
                    value=v,
                ),
                input_source_used={},
            )
            for i, v in enumerate(values)
        ]

    def test_aggregate_basic(self):
        results = self._make_results([5.0, 6.0, 4.0, 5.5])
        report = aggregate_uncertainty(results)
        assert report.n_scenarios == 4
        assert report.central_value == pytest.approx(5.125)
        assert report.std_dev > 0
        assert report.spread_range == pytest.approx(2.0)

    def test_aggregate_single_scenario(self):
        results = self._make_results([5.0])
        report = aggregate_uncertainty(results)
        assert report.n_scenarios == 1
        assert report.central_value == 5.0
        assert report.std_dev == 0.0

    def test_aggregate_empty(self):
        report = aggregate_uncertainty([])
        assert report.n_scenarios == 0
        assert report.central_value is None

    def test_aggregate_percentile_method(self):
        results = self._make_results([4.0, 5.0, 6.0, 7.0, 5.0, 5.0, 5.0, 5.0])
        report = aggregate_uncertainty(results, method="percentile", ci_percentile=90)
        assert report.prediction_interval_lower is not None
        assert report.prediction_interval_upper is not None
        assert report.prediction_interval_lower < report.prediction_interval_upper

    def test_aggregate_summary(self):
        results = self._make_results([5.0, 6.0, 4.0])
        report = aggregate_uncertainty(results)
        summary = report.summary()
        assert summary["n_scenarios"] == 3
        assert summary["central_value"] == pytest.approx(5.0)
        assert summary["uncertainty_method"] == "scenario_spread"


class TestBuildDefaultScenarios:
    def test_build_default_scenarios_count(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="s1",
            value=5.0, par_provenance="satellite_retrieved",
        )
        scenarios = build_default_scenarios(pred)
        assert len(scenarios) > 0
        assert all(isinstance(s, Scenario) for s in scenarios)

    def test_build_default_scenarios_unique_ids(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="s1",
            value=5.0, par_provenance="satellite_retrieved",
        )
        scenarios = build_default_scenarios(pred)
        ids = [s.scenario_id for s in scenarios]
        assert len(ids) == len(set(ids))

    def test_build_default_scenarios_has_satellite(self):
        pred = PredictionResult(
            prediction_id="p1", site_id="S1", season_id="s1",
            value=5.0, par_provenance="satellite_retrieved",
        )
        scenarios = build_default_scenarios(pred)
        all_satellite = [s for s in scenarios if s.name == "all_satellite"]
        assert len(all_satellite) == 1


class TestUncertaintyMethod:
    def test_all_enum_values(self):
        assert UncertaintyMethod.ENSEMBLE_RANGE.value == "ensemble_range"
        assert UncertaintyMethod.BOOTSTRAP.value == "bootstrap"
        assert UncertaintyMethod.MONTE_CARLO.value == "monte_carlo"
        assert UncertaintyMethod.PARAMETRIC.value == "parametric"
        assert UncertaintyMethod.SCENARIO_SPREAD.value == "scenario_spread"
        assert UncertaintyMethod.NONE.value == "none"


# ---------------------------------------------------------------------------
# Section 8: Integration — HYRUE computation with provenance
# ---------------------------------------------------------------------------


class TestHyraIntegration:
    def test_compute_seasonal_attaches_provenance(self):
        import pandas as pd

        n_days = 365
        dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
        weather = pd.DataFrame({
            "MinTemp": [5.0] * n_days,
            "MaxTemp": [15.0] * n_days,
            "Precipitation": [0.0] * n_days,
            "ReferenceET": [2.5] * n_days,
            "ShortwaveRadiation": [15.0] * n_days,
            "PAR": [5.0] * n_days,
            "Date": dates,
        })
        weather["Date"] = pd.to_datetime(weather["Date"])
        weather.attrs["shortwave_unit"] = "MJ/m^2/day"
        weather.attrs["shortwave_source"] = "test_source"
        weather.attrs["shortwave_source_parameter"] = "test_param"
        weather.attrs["par_unit"] = "MJ/m^2/day"
        weather.attrs["par_source"] = "NASA POWER"
        weather.attrs["par_source_parameter"] = "ALLSKY_SFC_PAR_TOT"
        weather.attrs["par_source_reference"] = "Su et al. (2007), CERES SYN1deg Ed. 4.2"

        climate_inputs = build_seasonal_climate_inputs(
            weather,
            lai_array=[3.0] * n_days,
            ewsi_array=[0.1] * n_days,
        )
        result = compute_hyrue_seasonal(climate_inputs, crop="wheat")

        assert "par_provenance" in result
        assert "par_conversion_spec" in result
        assert "input_quality" in result
        assert "missing_fields" in result
        assert "data_source" in result
        assert "lai_provenance" in result
        assert "ewsi_provenance" in result
        assert result["par_provenance"] == "satellite_retrieved"
        assert result["par_conversion_spec"]["status"] == "satellite_retrieved"
        assert result["input_quality"] == "complete"
        assert result["data_source"] == "weather_source"
