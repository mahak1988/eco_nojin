"""Benchmark report generation for HY-RUE external validation.

A :class:`BenchmarkReport` aggregates the output of a benchmark run (or
explains why one was blocked). It re-uses the :class:`ValidationOutput`
from Stage 28 and preserves all independent status dimensions.

When the benchmark is BLOCKED (no real data), no metrics are computed
and all evaluation fields are ``None`` or "not_assessed".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from engine.hydroma.eval.benchmark import (
    BenchmarkBlocker,
    BenchmarkSpec,
    BenchmarkStatus,
    DatasetInventory,
    DatasetProvenance,
)
from engine.hydroma.eval.validation_protocol import EvaluationTarget
from engine.hydroma.eval.validation_report import (
    ExternalValidationStatus,
    ValidationOutput,
)


@dataclass
class DatasetInfo:
    """Public-facing dataset description in the report."""

    dataset_id: str
    dataset_version: str
    dataset_source: str
    provenance: DatasetProvenance
    crop_count: int = 0
    site_count: int = 0
    field_count: int = 0
    season_count: int = 0
    observation_count: int = 0
    yield_observations_available: bool = False
    weather_observations_available: bool = False
    par_available: bool = False
    lai_available: bool = False
    ews_inputs_available: bool = False
    calibration_overlap: str = "unknown"


@dataclass
class BenchmarkMetrics:
    """Evaluation metrics for a completed benchmark.

    All fields are ``None`` when the benchmark is blocked or has not run.
    """

    mae: float | None = None
    rmse: float | None = None
    bias: float | None = None
    r_squared: float | None = None
    mape: float | None = None
    n_valid_pairs: int = 0


@dataclass
class BenchmarkReport:
    """Final report combining spec, dataset inventory, and results.

    This report is the single source of truth for benchmark
    reproducibility and scientific scope.
    """

    dataset: DatasetInfo
    model_name: str
    model_version: str
    model_parameters_hash: str
    evaluation_target: EvaluationTarget
    unit_of_independence: str
    input_policy: str
    benchmark_status: BenchmarkStatus

    report_id: str = field(default_factory=lambda: f"BENCHRPT-{uuid4().hex[:12].upper()}")
    benchmark_id: str = ""
    blockers: list[BenchmarkBlocker] = field(default_factory=list)
    metrics: BenchmarkMetrics | None = None
    validation_output: ValidationOutput | None = None
    external_validation_status: str = "not_assessed"
    scientific_limitations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to a JSON-safe dictionary."""
        dataset_dict = {
            "dataset_id": self.dataset.dataset_id,
            "dataset_version": self.dataset.dataset_version,
            "dataset_source": self.dataset.dataset_source,
            "provenance": self.dataset.provenance.value,
            "coverage": {
                "crop_count": self.dataset.crop_count,
                "site_count": self.dataset.site_count,
                "field_count": self.dataset.field_count,
                "season_count": self.dataset.season_count,
                "observation_count": self.dataset.observation_count,
            },
            "inputs_available": {
                "yield_observations": self.dataset.yield_observations_available,
                "weather_observations": self.dataset.weather_observations_available,
                "par": self.dataset.par_available,
                "lai": self.dataset.lai_available,
                "ewsi": self.dataset.ews_inputs_available,
            },
            "calibration_overlap": self.dataset.calibration_overlap,
        }

        model_dict = {
            "name": self.model_name,
            "version": self.model_version,
            "parameters_hash": self.model_parameters_hash,
        }

        metrics_dict = None
        if self.metrics:
            metrics_dict = {
                "mae": self.metrics.mae,
                "rmse": self.metrics.rmse,
                "bias": self.metrics.bias,
                "r_squared": self.metrics.r_squared,
                "mape": self.metrics.mape,
                "n_valid_pairs": self.metrics.n_valid_pairs,
            }

        validation_dict = None
        if self.validation_output:
            validation_dict = self.validation_output.to_dict()

        return {
            "report_id": self.report_id,
            "benchmark_id": self.benchmark_id,
            "dataset": dataset_dict,
            "model": model_dict,
            "evaluation": {
                "evaluation_target": self.evaluation_target.value,
                "unit_of_independence": self.unit_of_independence,
                "input_policy": self.input_policy,
            },
            "benchmark_status": self.benchmark_status.value,
            "blockers": [b.value for b in self.blockers],
            "metrics": metrics_dict,
            "validation_output": validation_dict,
            "external_validation_status": self.external_validation_status,
            "scientific_limitations": self.scientific_limitations,
            "notes": list(self.notes),
            "generated_at": self.generated_at,
        }


def create_blocked_report(
    spec: BenchmarkSpec,
    dataset_inventory: DatasetInventory | None = None,
    reason: str = "No real field-yield dataset found.",
    scientific_limitations: list[str] | None = None,
) -> BenchmarkReport:
    """Create a BLOCKED benchmark report with no evaluation results.

    This function produces a complete report without executing HYRUE or
    computing any metrics.
    """
    blockers = list(spec.blockers) if spec.blockers else [
        BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA
    ]

    if dataset_inventory is not None:
        dataset_info = DatasetInfo(
            dataset_id=dataset_inventory.dataset_id,
            dataset_version=dataset_inventory.dataset_version,
            dataset_source=dataset_inventory.dataset_source,
            provenance=dataset_inventory.provenance,
            crop_count=dataset_inventory.crop_count,
            site_count=dataset_inventory.site_count,
            field_count=dataset_inventory.field_count,
            season_count=dataset_inventory.season_count,
            observation_count=dataset_inventory.observation_count,
            yield_observations_available=dataset_inventory.yield_observations_available,
            weather_observations_available=dataset_inventory.weather_observations_available,
            par_available=dataset_inventory.par_available,
            lai_available=dataset_inventory.lai_available,
            ews_inputs_available=dataset_inventory.ews_inputs_available,
            calibration_overlap=dataset_inventory.calibration_overlap,
        )
    else:
        dataset_info = DatasetInfo(
            dataset_id="",
            dataset_version="",
            dataset_source="",
            provenance=DatasetProvenance.SYNTHETIC_TEST_FIXTURES,
        )

    limitations = scientific_limitations or [
        "No real field-yield dataset found in the repository.",
        "Synthetic test fixtures are not valid for external validation.",
        "Benchmark execution blocked until real independent data is available.",
    ]

    return BenchmarkReport(
        benchmark_id=spec.benchmark_id,
        dataset=dataset_info,
        model_name=spec.model_name,
        model_version=spec.model_version,
        model_parameters_hash=spec.model_parameters_hash,
        evaluation_target=spec.evaluation_target,
        unit_of_independence=spec.unit_of_independence,
        input_policy=spec.input_policy.value,
        benchmark_status=BenchmarkStatus.BLOCKED,
        blockers=blockers,
        metrics=None,
        validation_output=None,
        external_validation_status=ExternalValidationStatus.BLOCKED.value,
        scientific_limitations=limitations,
        notes=[reason],
    )


def produce_benchmark_report(
    spec: BenchmarkSpec,
    dataset_inventory: DatasetInventory | None = None,
) -> BenchmarkReport:
    """Produce a benchmark report based on the spec and dataset availability.

    If the dataset is missing or synthetic, returns a BLOCKED report.
    If real data is available and prerequisites are met, returns a READY
    report with no metrics computed (execution would happen separately).
    """
    status = spec.evaluate_status(dataset_inventory)
    spec.benchmark_status = status

    if status == BenchmarkStatus.BLOCKED:
        return create_blocked_report(
            spec=spec,
            dataset_inventory=dataset_inventory,
            reason="Benchmark blocked: prerequisites not met.",
        )

    dataset_info = DatasetInfo(
        dataset_id=dataset_inventory.dataset_id,
        dataset_version=dataset_inventory.dataset_version,
        dataset_source=dataset_inventory.dataset_source,
        provenance=dataset_inventory.provenance,
        crop_count=dataset_inventory.crop_count,
        site_count=dataset_inventory.site_count,
        field_count=dataset_inventory.field_count,
        season_count=dataset_inventory.season_count,
        observation_count=dataset_inventory.observation_count,
        yield_observations_available=dataset_inventory.yield_observations_available,
        weather_observations_available=dataset_inventory.weather_observations_available,
        par_available=dataset_inventory.par_available,
        lai_available=dataset_inventory.lai_available,
        ews_inputs_available=dataset_inventory.ews_inputs_available,
        calibration_overlap=dataset_inventory.calibration_overlap,
    )

    return BenchmarkReport(
        benchmark_id=spec.benchmark_id,
        dataset=dataset_info,
        model_name=spec.model_name,
        model_version=spec.model_version,
        model_parameters_hash=spec.model_parameters_hash,
        evaluation_target=spec.evaluation_target,
        unit_of_independence=spec.unit_of_independence,
        input_policy=spec.input_policy.value,
        benchmark_status=BenchmarkStatus.READY,
        blockers=[],
        metrics=None,
        validation_output=None,
        external_validation_status="not_assessed",
        scientific_limitations=[
            "Benchmark is READY but has not yet been executed. "
            "READY does not imply validated_external."
        ],
        notes=["Prerequisites met. Ready for execution with real data."],
    )
