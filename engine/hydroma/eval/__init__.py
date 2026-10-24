"""Independent evaluation framework for HY-RUE model outputs.

Provides RMSE, MAE, Bias, R², and relative error metrics for comparing
model predictions against reference observations, plus field-data contracts,
data ingestion, dataset versioning with leakage-prevention splits, scenario
tracking, and HYRUE-to-observation matching.

Provenance: evaluation_utility (not a scientific model).

Note: submodules are resolved lazily via ``__getattr__``.  Eagerly importing
them here created a re-entrant import chain (``engine.hydroma.eval`` ->
``engine.hydroma.eval.seasonal_predictor`` -> ``engine.hydroma.simulation`` ->
``engine.hydroma``) that made ``import engine.hydroma.eval.<module>`` fail
depending on import order.
"""

from __future__ import annotations

import importlib
from typing import Any

#: Public name -> submodule that defines it.
_EXPORTS: dict[str, str] = {
    "EvaluationResult": "metrics",
    "compute_metrics": "metrics",
    "rmse": "metrics",
    "mae": "metrics",
    "bias": "metrics",
    "r_squared": "metrics",
    "relative_error": "metrics",
    "mean_absolute_percentage_error": "metrics",
    "ValidationSummary": "validation",
    "validate_against_reference": "validation",
    "CrossValidationResult": "validation",
    "cross_validate": "validation",
    "SensitivityResult": "sensitivity",
    "SensitivityAnalysisReport": "sensitivity",
    "oat_sensitivity": "sensitivity",
    "seasonal_sensitivity": "sensitivity",
    "ConsistencyCheck": "consistency",
    "ConsistencyReport": "consistency",
    "verify_seasonal_consistency": "consistency",
    "EvaluationDataset": "field_data",
    "FieldObservation": "field_data",
    "ObservationSource": "field_data",
    "SeasonInfo": "field_data",
    "SiteInfo": "field_data",
    "VariableType": "field_data",
    "CSVIngester": "data_ingestion",
    "JSONIngester": "data_ingestion",
    "IngestionResult": "data_ingestion",
    "QualityReport": "data_ingestion",
    "ingest_csv": "data_ingestion",
    "ingest_json": "data_ingestion",
    "DataSplit": "dataset",
    "DatasetVersion": "dataset",
    "EvaluationDatasetManager": "dataset",
    "SplitMethod": "dataset",
    "SplitRole": "dataset",
    "ComputationStatus": "prediction",
    "ExternalValidationStatus": "prediction",
    "InputQuality": "prediction",
    "ScientificSupportStatus": "prediction",
    "PredictionMatch": "prediction",
    "PredictionResult": "prediction",
    "match_hyra_to_observations": "prediction",
    "Scenario": "scenarios",
    "ScenarioResult": "scenarios",
    "UncertaintyMethod": "scenarios",
    "UncertaintyReport": "scenarios",
    "aggregate_uncertainty": "scenarios",
    "build_default_scenarios": "scenarios",
    "run_scenarios": "scenarios",
    "SeasonalPredictionRequest": "seasonal_predictor",
    "OperationalReport": "seasonal_predictor",
    "InputSourcePolicy": "seasonal_predictor",
    "EWSIInputs": "seasonal_predictor",
    "compute_seasonal_prediction": "seasonal_predictor",
    "generate_synthetic_weather": "seasonal_predictor",
    "RealFieldRecord": "field_validation",
    "QualityGateDecision": "field_validation",
    "run_quality_gates": "field_validation",
    "convert_yield_to_t_ha": "field_validation",
    "MetricResult": "validation_metrics",
    "ValidationMetrics": "validation_metrics",
    "compute_validation_metrics": "validation_metrics",
    "compute_r_squared_with_notes": "validation_metrics",
    "compute_mape_with_notes": "validation_metrics",
    "ValidationPair": "validation_matching",
    "ValidationSplit": "validation_matching",
    "match_prediction_to_observations": "validation_matching",
    "match_predictions_to_observations": "validation_matching",
    "split_for_validation": "validation_matching",
    "DataLeakageStatus": "validation_report",
    "produce_validation_report": "validation_report",
    "ValidationExternalStatus": "validation_report",
    "EvaluationTarget": "validation_protocol",
    "MetricAcceptanceCriterion": "validation_protocol",
    "MetricCriterion": "validation_protocol",
    "ValidationProtocol": "validation_protocol",
    "BootstrapResult": "validation_uncertainty",
    "UncertaintyAssessment": "validation_uncertainty",
    "UncertaintyStatus": "validation_uncertainty",
    "assess_uncertainty": "validation_uncertainty",
    "bootstrap_metric": "validation_uncertainty",
    "BenchmarkSpec": "benchmark",
    "BenchmarkStatus": "benchmark",
    "BenchmarkBlocker": "benchmark",
    "InputPolicy": "benchmark",
    "DatasetProvenance": "benchmark",
    "DatasetInventory": "benchmark",
    "BenchmarkReport": "benchmark_report",
    "BenchmarkMetrics": "benchmark_report",
    "DatasetInfo": "benchmark_report",
    "create_blocked_report": "benchmark_report",
    "produce_benchmark_report": "benchmark_report",
    "DatasetManifest": "dataset_manifest",
    "DataProvenance": "dataset_manifest",
    "DataFormat": "dataset_manifest",
    "FileHash": "dataset_manifest",
    "DataQualityCheckError": "dataset_manifest",
    "QualityCheckResult": "dataset_manifest",
    "DataQualityReport": "dataset_manifest",
    "check_data_independence": "dataset_manifest",
    "check_duplicate_records": "dataset_manifest",
    "check_no_synthetic_label": "dataset_manifest",
    "check_required_fields_present": "dataset_manifest",
    "check_yield_unit_consistency": "dataset_manifest",
    "compute_file_hash": "dataset_manifest",
    "compute_hashes": "dataset_manifest",
    "create_real_dataset_manifest": "dataset_manifest",
    "create_synthetic_manifest": "dataset_manifest",
    "run_data_quality_checks": "dataset_manifest",
    "verify_file_integrity": "dataset_manifest",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Resolve a public name by importing its defining submodule on demand."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))
