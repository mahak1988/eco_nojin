"""Validation protocol contracts for HY-RUE external validation.

A :class:`ValidationProtocol` records the design of a validation evaluation
*before* any metrics are computed.  This separates the experimental design
(the protocol) from the execution results, preventing post-hoc changes to
the validation plan that could introduce bias.

The protocol answers:
- Which dataset was used to calibrate model parameters?
- Which dataset is used for independent evaluation?
- What is the evaluation target (spatial generalization, temporal
  generalization, or both)?
- What is the unit of independence (site, field, season)?
- What metrics and acceptance criteria are used?
- What crops, sites, and seasons are in scope?

If the protocol is missing or incomplete, the validation report must be
limited — it cannot claim ``VALIDATED_EXTERNAL`` status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any
from uuid import uuid4

from engine.hydroma.eval.validation_matching import ValidationSplit


class EvaluationTarget(StrEnum):
    """What generalization the evaluation targets.

    ``SPATIAL`` — model parameters were calibrated on site A and evaluated
    on site B (site not seen during calibration).

    ``TEMPORAL`` — model parameters were calibrated on season T1 and
    evaluated on season T2 (later season not seen during calibration).

    ``SPATIAL_AND_TEMPORAL`` — both site-level and temporal independence.

    ``NONE`` — no explicit generalization target (e.g. same-site, same-season
    evaluation that only tests reproducibility).
    """

    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    SPATIAL_AND_TEMPORAL = "spatial_and_temporal"
    NONE = "none"


class MetricCriterion(StrEnum):
    """Acceptance criteria for validation metrics."""

    RMSE_THRESHOLD = "rmse_threshold"
    MAE_THRESHOLD = "mae_threshold"
    R_SQUARED_MIN = "r_squared_min"
    BIAS_MAX = "bias_max"
    MAPE_MAX = "mape_max"


@dataclass
class MetricAcceptanceCriterion:
    """A single acceptance criterion for a metric.

    Attributes:
        metric: Which metric this criterion applies to.
        comparison: ``"max"`` or ``"min"``.
        threshold: The critical value. Metric must satisfy
            ``metric_value <= threshold`` (max) or
            ``metric_value >= threshold`` (min).
        unit: Unit of the threshold (must match the metric's unit).
    """

    metric: str
    comparison: str
    threshold: float
    unit: str

    def __post_init__(self) -> None:
        if self.comparison not in ("max", "min"):
            raise ValueError(
                f"comparison must be 'max' or 'min', got {self.comparison!r}"
            )


@dataclass
class ValidationProtocol:
    """A formal validation evaluation protocol.

    The protocol must be defined **before** running the evaluation.  It
    records the independence structure, scope, and acceptance criteria so
    that results cannot be cherry-picked post hoc.

    Attributes:
        protocol_id: Unique identifier for this protocol definition.
        protocol_version: Version of the protocol (for audit trail).
        model_version: Version of the HY-RUE model being evaluated.
        model_parameters_hash: Hash of the exact model parameters used
            (calibration transparency).
        calibration_dataset_id: Identifier of the dataset used to calibrate
            model parameters.
        validation_dataset_id: Identifier of the dataset used for evaluation.
        evaluation_target: What generalization type is being tested.
        evaluation_scope: Human-readable description of the evaluation scope
            (e.g. "winter wheat across Mediterranean climates, 2020-2025").
        evaluation_start_date: Start date of the evaluation period.
        evaluation_end_date: End date of the evaluation period.
        crops_in_scope: List of crops evaluated.
        sites_in_scope: List of site IDs in the evaluation.
        seasons_in_scope: List of season IDs in the evaluation.
        split_method: How data was split for calibration vs evaluation.
        split_seed: Reproducibility seed for the split.
        unit_of_independence: The level at which independence is enforced
            (e.g. ``"site"``, ``"field"``, ``"season"``).
        minimum_sites: Minimum number of independent sites required.
        minimum_seasons: Minimum number of independent seasons required.
        acceptance_criteria: List of metric acceptance criteria.
        notes: Additional notes about the protocol.
        created_at: ISO timestamp of protocol creation.
    """

    protocol_id: str = field(default_factory=lambda: f"PROTO-{uuid4().hex[:12].upper()}")
    protocol_version: str = "1.0"
    model_version: str = "2.0.0"
    model_parameters_hash: str = ""
    calibration_dataset_id: str = ""
    validation_dataset_id: str = ""
    evaluation_target: EvaluationTarget = EvaluationTarget.NONE
    evaluation_scope: str = ""
    evaluation_start_date: str = ""
    evaluation_end_date: str = ""
    crops_in_scope: list[str] = field(default_factory=list)
    sites_in_scope: list[str] = field(default_factory=list)
    seasons_in_scope: list[str] = field(default_factory=list)
    split_method: str = "site"
    split_seed: int = 42
    unit_of_independence: str = "site"
    minimum_sites: int = 1
    minimum_seasons: int = 1
    acceptance_criteria: list[MetricAcceptanceCriterion] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: date.today().isoformat()
    )

    def is_complete(self) -> bool:
        """Check if the protocol has all required fields populated.

        A protocol is incomplete if:
        - calibration or validation dataset is unspecified.
        - evaluation target is NONE.
        - evaluation scope is empty.
        - no crops, sites, or seasons are in scope.
        - minimum_sites or minimum_seasons is 0.
        """
        if not self.calibration_dataset_id:
            return False
        if not self.validation_dataset_id:
            return False
        if self.evaluation_target == EvaluationTarget.NONE:
            return False
        if not self.evaluation_scope:
            return False
        if not self.crops_in_scope:
            return False
        if not self.sites_in_scope:
            return False
        if not self.seasons_in_scope:
            return False
        if self.minimum_sites <= 0:
            return False
        if self.minimum_seasons <= 0:
            return False
        if self.calibration_dataset_id == self.validation_dataset_id:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize protocol to a JSON-safe dictionary."""
        return {
            "protocol_id": self.protocol_id,
            "protocol_version": self.protocol_version,
            "model_version": self.model_version,
            "model_parameters_hash": self.model_parameters_hash,
            "calibration_dataset_id": self.calibration_dataset_id,
            "validation_dataset_id": self.validation_dataset_id,
            "evaluation_target": self.evaluation_target.value,
            "evaluation_scope": self.evaluation_scope,
            "evaluation_start_date": self.evaluation_start_date,
            "evaluation_end_date": self.evaluation_end_date,
            "crops_in_scope": list(self.crops_in_scope),
            "sites_in_scope": list(self.sites_in_scope),
            "seasons_in_scope": list(self.seasons_in_scope),
            "split_method": self.split_method,
            "split_seed": self.split_seed,
            "unit_of_independence": self.unit_of_independence,
            "minimum_sites": self.minimum_sites,
            "minimum_seasons": self.minimum_seasons,
            "acceptance_criteria": [
                {
                    "metric": c.metric,
                    "comparison": c.comparison,
                    "threshold": c.threshold,
                    "unit": c.unit,
                }
                for c in self.acceptance_criteria
            ],
            "notes": list(self.notes),
            "created_at": self.created_at,
        }

    @classmethod
    def from_split(
        cls,
        split: ValidationSplit,
        *,
        calibration_dataset_id: str,
        validation_dataset_id: str,
        model_version: str = "2.0.0",
        evaluation_target: EvaluationTarget = EvaluationTarget.SPATIAL,
        unit_of_independence: str = "site",
        evaluation_scope: str = "",
        **kwargs: Any,
    ) -> ValidationProtocol:
        """Build a protocol from a :class:`ValidationSplit`.

        Derives crops, sites, and seasons in scope from the split's
        validation and test records.
        """
        val_records = split.validation + split.test

        crops = sorted({r.crop for r in val_records})
        sites = sorted({r.site_id for r in val_records})
        seasons = sorted({r.season_id for r in val_records})

        start_dates: list[str] = []
        end_dates: list[str] = []
        for r in val_records:
            if r.planting_date:
                start_dates.append(r.planting_date.isoformat())
            if r.harvest_date:
                end_dates.append(r.harvest_date.isoformat())

        start_date = min(start_dates) if start_dates else ""
        end_date = max(end_dates) if end_dates else ""

        return cls(
            calibration_dataset_id=calibration_dataset_id,
            validation_dataset_id=validation_dataset_id,
            evaluation_target=evaluation_target,
            evaluation_scope=evaluation_scope or (
                f"Evaluation on {len(sites)} site(s), "
                f"{len(seasons)} season(s), crop(s): {', '.join(crops)}"
            ),
            evaluation_start_date=start_date,
            evaluation_end_date=end_date,
            crops_in_scope=crops,
            sites_in_scope=sites,
            seasons_in_scope=seasons,
            split_method=split.method,
            split_seed=split.seed,
            unit_of_independence=unit_of_independence,
            model_version=model_version,
            **kwargs,
        )
