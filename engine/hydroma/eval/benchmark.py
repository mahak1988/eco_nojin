"""Benchmark specification and execution contract for HY-RUE external validation.

A :class:`BenchmarkSpec` defines the design of a benchmark evaluation,
including the dataset, protocol, model version, and input policy. It is
the bridge between a real agricultural dataset and the HYRUE prediction
pipeline.

Crucially, a benchmark can only transition to ``READY`` or ``COMPLETED``
when a real field-yield dataset is available. Without real observational
data, the benchmark is ``BLOCKED`` with a specific blocker reason.

This module is import-safe: dataclasses + numpy only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from engine.hydroma.eval.validation_protocol import (
    EvaluationTarget,
    ValidationProtocol,
)


class BenchmarkStatus(StrEnum):
    """Lifecycle status of a benchmark execution."""

    NOT_READY = "not_ready"
    BLOCKED = "blocked"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InputPolicy(StrEnum):
    """Policy for model input sources in the benchmark.

    ``STRICT`` — only observed inputs (real weather stations, ground-truthed
    PAR/LAI) are permitted. No modeled or estimated inputs without explicit
    approval.

    ``ALLOW_ESTIMATED_INPUTS`` — weather reanalysis or modeled inputs are
    permitted, but their type and source must be recorded per-record.
    """

    STRICT = "strict"
    ALLOW_ESTIMATED_INPUTS = "allow_estimated_inputs"


class DatasetProvenance(StrEnum):
    """Provenance category of the evaluation dataset.

    ``REAL_FIELD_OBSERVATIONS`` — data collected through field campaigns,
    farm management records, or official statistical sources.

    ``SYNTHETIC_TEST_FIXTURES`` — data generated for unit/integration testing.
    """

    REAL_FIELD_OBSERVATIONS = "real_field_observations"
    SYNTHETIC_TEST_FIXTURES = "synthetic_test_fixtures"


class BenchmarkBlocker(StrEnum):
    """Reason codes for why a benchmark is blocked from execution."""

    NO_REAL_FIELD_YIELD_DATA = "no_real_field_yield_data"
    NO_VALIDATION_DATASET = "no_validation_dataset"
    NO_INDEPENDENT_EVALUATION_DATA = "no_independent_evaluation_data"
    NO_WEATHER_INPUTS = "no_weather_inputs"
    INCOMPLETE_PROTOCOL = "incomplete_protocol"
    DATASET_NOT_CONFIGURED = "dataset_not_configured"


@dataclass
class DatasetInventory:
    """Lightweight inventory of real data availability.

    This is populated from real dataset manifests or returns a BLOCKED
    status when no real data is found.
    """

    dataset_id: str
    dataset_version: str
    provenance: DatasetProvenance
    observation_source: str
    dataset_source: str = ""
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
class BenchmarkSpec:
    """Specification for a single benchmark execution.

    Attributes:
        benchmark_id: Unique identifier (e.g. BENCH-<hex>).
        benchmark_version: Version of this benchmark specification.
        dataset_id: Identifier of the evaluation dataset.
        dataset_version: Version of the dataset.
        dataset_source: Path or connection string to the dataset.
        dataset_provenance: Whether the dataset is real or synthetic.
        protocol: The :class:`ValidationProtocol` governing this benchmark.
            If None, the benchmark cannot achieve ``READY``.
        evaluation_target: What generalization type is tested.
        unit_of_independence: The level at which independence is enforced.
        model_name: Name of the model being benchmarked.
        model_version: Version string of the model.
        model_parameters_hash: Hash of model parameters (calibration transparency).
        input_policy: Whether strict or estimated inputs are allowed.
        benchmark_status: Current lifecycle status.
        blockers: List of :class:`BenchmarkBlocker` reasons if blocked.
        notes: Additional notes about the benchmark design.
        created_at: ISO timestamp of spec creation.
    """

    benchmark_id: str = field(default_factory=lambda: f"BENCH-{uuid4().hex[:12].upper()}")
    benchmark_version: str = "1.0"

    dataset_id: str = ""
    dataset_version: str = ""
    dataset_source: str = ""
    dataset_provenance: DatasetProvenance = DatasetProvenance.REAL_FIELD_OBSERVATIONS

    protocol: ValidationProtocol | None = None
    evaluation_target: EvaluationTarget = EvaluationTarget.NONE
    unit_of_independence: str = "site"

    model_name: str = "HY-RUE"
    model_version: str = "2.0.0"
    model_parameters_hash: str = ""

    input_policy: InputPolicy = InputPolicy.STRICT

    benchmark_status: BenchmarkStatus = BenchmarkStatus.NOT_READY
    blockers: list[BenchmarkBlocker] = field(default_factory=list)

    notes: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def check_prerequisites(
        self,
        dataset_inventory: DatasetInventory | None = None,
    ) -> list[BenchmarkBlocker]:
        """Check whether all prerequisites for benchmark execution are met.

        Returns a list of :class:`BenchmarkBlocker` reasons. An empty list
        means all hard prerequisites are satisfied and the benchmark is
        ``READY``.

        Prerequisites:
        - A real field-yield observation dataset is available.
        - The dataset has valid observation source metadata.
        - Yield observations are available in the dataset.
        - A complete validation protocol is provided.
        - The protocol defines an evaluation target (not NONE).
        - Calibration and validation datasets are distinct.
        """
        blockers: list[BenchmarkBlocker] = []

        if dataset_inventory is None:
            blockers.append(BenchmarkBlocker.NO_VALIDATION_DATASET)
            blockers.append(BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA)
            blockers.append(BenchmarkBlocker.INCOMPLETE_PROTOCOL)
            return blockers

        if dataset_inventory.provenance == DatasetProvenance.SYNTHETIC_TEST_FIXTURES:
            blockers.append(BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA)

        if not dataset_inventory.yield_observations_available:
            blockers.append(BenchmarkBlocker.NO_REAL_FIELD_YIELD_DATA)

        if not dataset_inventory.weather_observations_available:
            blockers.append(BenchmarkBlocker.NO_WEATHER_INPUTS)

        if not self.protocol:
            blockers.append(BenchmarkBlocker.INCOMPLETE_PROTOCOL)
        else:
            if not self.protocol.is_complete():
                blockers.append(BenchmarkBlocker.INCOMPLETE_PROTOCOL)
            if (
                self.protocol.calibration_dataset_id
                == self.protocol.validation_dataset_id
            ):
                blockers.append(BenchmarkBlocker.NO_INDEPENDENT_EVALUATION_DATA)

        return blockers

    def evaluate_status(
        self,
        dataset_inventory: DatasetInventory | None = None,
    ) -> BenchmarkStatus:
        """Evaluate and return the benchmark status based on prerequisites."""
        blockers = self.check_prerequisites(dataset_inventory)
        self.blockers = blockers

        if blockers:
            return BenchmarkStatus.BLOCKED
        return BenchmarkStatus.READY

    def to_dict(self) -> dict[str, Any]:
        """Serialize benchmark spec to a JSON-safe dictionary."""
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "dataset_source": self.dataset_source,
            "dataset_provenance": self.dataset_provenance.value,
            "evaluation_target": self.evaluation_target.value,
            "unit_of_independence": self.unit_of_independence,
            "model": {
                "name": self.model_name,
                "version": self.model_version,
                "parameters_hash": self.model_parameters_hash,
            },
            "input_policy": self.input_policy.value,
            "protocol": self.protocol.to_dict() if self.protocol else None,
            "benchmark_status": self.benchmark_status.value,
            "blockers": [b.value for b in self.blockers],
            "notes": list(self.notes),
            "created_at": self.created_at,
        }
