"""Operational validation report for HY-RUE external validation.

This module aggregates results from the matching pipeline
(:mod:`engine.hydroma.eval.validation_matching`) and the metrics
(:mod:`engine.hydroma.eval.validation_metrics`) into a structured,
reproducible report.

The report distinguishes strictly between independent status dimensions:

- ``computation_status`` (whether HYRUE ran)
- ``scientific_support_status`` (equation grounding)
- ``data_availability_status`` (whether real observations exist)
- ``data_quality_status`` (whether records passed quality gates)
- ``evaluation_independence_status`` (whether the evaluation set is
  independent of the calibration set)
- ``sample_adequacy_status`` (whether the sample size supports the
  generalization claim being made)
- ``external_validation_status`` (the final verdict)

This separation is enforced at the API boundary: ``external_validation_status``
is ``BLOCKED`` whenever any critical prerequisite is unmet, regardless of
whether the computation itself succeeded.

**No single threshold (e.g. "5 pairs") determines ``VALIDATED_EXTERNAL``.**
That status requires demonstrably independent data with adequate sample
size for the claimed generalization scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

import numpy as np

from engine.hydroma.eval.field_validation import RealFieldRecord, run_quality_gates
from engine.hydroma.eval.prediction import PredictionResult
from engine.hydroma.eval.validation_matching import (
    ValidationPair,
    ValidationSplit,
)
from engine.hydroma.eval.validation_metrics import (
    ValidationMetrics,
    compute_validation_metrics,
)
from engine.hydroma.eval.validation_protocol import (
    EvaluationTarget,
    ValidationProtocol,
)


class DataAvailabilityStatus(StrEnum):
    """Whether real observation data is available for evaluation."""

    AVAILABLE = "available"
    INSUFFICIENT_DATA = "insufficient_data"
    NO_DATA = "no_data"


class DataQualityStatus(StrEnum):
    """Aggregate quality gate outcome for the evaluation dataset."""

    ACCEPTED = "accepted"
    REQUIRES_REVIEW = "requires_review"
    REJECTED = "rejected"


class EvaluationIndependenceStatus(StrEnum):
    """Whether the evaluation set is independent of the calibration set."""

    INDEPENDENT = "independent"
    NOT_INDEPENDENT = "not_independent"
    UNKNOWN = "unknown"


class SampleAdequacyStatus(StrEnum):
    """Whether the sample size supports the claimed generalization."""

    ADEQUATE = "adequate"
    INSUFFICIENT = "insufficient"
    NOT_ASSESSED = "not_assessed"


class ExternalValidationStatus(StrEnum):
    """Final verdict on external validation against real-world observations.

    This is a *composite* status — it should only be ``VALIDATED_EXTERNAL``
    when all independent dimensions support that conclusion.
    """

    BLOCKED = "blocked"
    NOT_ASSESSED = "not_assessed"
    PARTIALLY_EVALUATED = "partially_evaluated"
    VALIDATED_EXTERNAL = "validated_external"


class DataLeakageStatus(StrEnum):
    """Status of data leakage prevention in the validation design."""

    NOT_APPLICABLE = "not_applicable"
    CLEAN = "clean"
    POTENTIAL_LEAKAGE = "potential_leakage"


def determine_external_validation_status(
    n_pairs: int,
    *,
    data_availability: DataAvailabilityStatus = DataAvailabilityStatus.NO_DATA,
    data_quality: DataQualityStatus = DataQualityStatus.REJECTED,
    evaluation_independence: EvaluationIndependenceStatus = EvaluationIndependenceStatus.UNKNOWN,
    sample_adequacy: SampleAdequacyStatus = SampleAdequacyStatus.NOT_ASSESSED,
    data_leakage: DataLeakageStatus = DataLeakageStatus.NOT_APPLICABLE,
    has_protocol: bool = False,
) -> ExternalValidationStatus:
    """Determine external validation status from independent dimensions.

    Rules:
    - No data available → BLOCKED.
    - Data quality REJECTED or data not independent → BLOCKED.
    - Data leakage detected → BLOCKED (integrity failure).
    - No protocol defined → at most PARTIALLY_EVALUATED.
    - < adequate samples → PARTIALLY_EVALUATED.
    - All criteria met → VALIDATED_EXTERNAL.

    **No single pair-count threshold determines the verdict.** The decision
    is based on the conjunction of all independent dimensions.
    """
    if data_availability == DataAvailabilityStatus.NO_DATA:
        return ExternalValidationStatus.BLOCKED

    if data_availability == DataAvailabilityStatus.INSUFFICIENT_DATA:
        return ExternalValidationStatus.BLOCKED

    if data_quality == DataQualityStatus.REJECTED:
        return ExternalValidationStatus.BLOCKED

    if evaluation_independence == EvaluationIndependenceStatus.NOT_INDEPENDENT:
        return ExternalValidationStatus.BLOCKED

    if data_leakage == DataLeakageStatus.POTENTIAL_LEAKAGE:
        return ExternalValidationStatus.BLOCKED

    if not has_protocol:
        if n_pairs == 0:
            return ExternalValidationStatus.BLOCKED
        return ExternalValidationStatus.PARTIALLY_EVALUATED

    if n_pairs == 0:
        return ExternalValidationStatus.BLOCKED

    if sample_adequacy == SampleAdequacyStatus.INSUFFICIENT:
        return ExternalValidationStatus.PARTIALLY_EVALUATED

    if data_quality == DataQualityStatus.REQUIRES_REVIEW:
        return ExternalValidationStatus.PARTIALLY_EVALUATED

    if evaluation_independence == EvaluationIndependenceStatus.UNKNOWN:
        return ExternalValidationStatus.PARTIALLY_EVALUATED

    return ExternalValidationStatus.VALIDATED_EXTERNAL


def assess_sample_adequacy(
    n_pairs: int,
    n_sites: int,
    n_seasons: int,
    n_crops: int,
    evaluation_target: EvaluationTarget,
) -> tuple[SampleAdequacyStatus, list[str]]:
    """Assess whether the sample size is adequate for the claimed generalization.

    This function does **not** use a single universal threshold. Instead,
    it checks adequacy relative to the evaluation target:

    - ``SPATIAL`` generalization requires >= 3 independent sites.
    - ``TEMPORAL`` generalization requires >= 2 independent seasons.
    - ``SPATIAL_AND_TEMPORAL`` requires >= 3 sites and >= 2 seasons.
    - ``NONE`` (reproducibility test) requires at least 1 pair.

    Returns (status, limiting_factors).
    """
    limitations: list[str] = []

    if evaluation_target == EvaluationTarget.NONE:
        if n_pairs < 1:
            limitations.append("No matched pairs available for evaluation.")
            return SampleAdequacyStatus.INSUFFICIENT, limitations
        return SampleAdequacyStatus.ADEQUATE, []

    hard_limitations: list[str] = []
    soft_notes: list[str] = []

    if evaluation_target == EvaluationTarget.SPATIAL:
        if n_sites < 3:
            hard_limitations.append(
                f"Spatial generalization requires >= 3 independent sites, "
                f"got {n_sites}."
            )
        if n_pairs < 10:
            soft_notes.append(
                f"Spatial generalization ideally has >= 10 matched pairs, "
                f"got {n_pairs}."
            )

    if evaluation_target == EvaluationTarget.TEMPORAL:
        if n_seasons < 2:
            hard_limitations.append(
                f"Temporal generalization requires >= 2 independent seasons, "
                f"got {n_seasons}."
            )
        if n_pairs < 10:
            soft_notes.append(
                f"Temporal generalization ideally has >= 10 matched pairs, "
                f"got {n_pairs}."
            )

    if evaluation_target == EvaluationTarget.SPATIAL_AND_TEMPORAL:
        if n_sites < 3:
            hard_limitations.append(
                f"Spatial+temporal generalization requires >= 3 independent "
                f"sites, got {n_sites}."
            )
        if n_seasons < 2:
            hard_limitations.append(
                f"Spatial+temporal generalization requires >= 2 independent "
                f"seasons, got {n_seasons}."
            )
        if n_pairs < 15:
            soft_notes.append(
                f"Spatial+temporal generalization ideally has >= 15 matched "
                f"pairs, got {n_pairs}."
            )

    if hard_limitations:
        return SampleAdequacyStatus.INSUFFICIENT, hard_limitations + soft_notes
    return SampleAdequacyStatus.ADEQUATE, soft_notes


@dataclass
class CropEvaluation:
    """Per-crop evaluation results within a validation run.

    Attributes:
        crop: Crop name.
        pair_count: Number of matched pairs for this crop.
        site_count: Number of unique sites for this crop.
        season_count: Number of unique seasons for this crop.
        metrics: Computed metrics (or None if insufficient data).
        adequacy_status: Whether the sample is adequate for this crop.
        in_scope: Whether this crop was in the protocol's scope.
        limitation: Description of any limitation (or empty string).
    """

    crop: str
    pair_count: int
    site_count: int
    season_count: int
    metrics: ValidationMetrics | None
    adequacy_status: str
    in_scope: bool
    limitation: str = ""


@dataclass
class ValidationOutput:
    """Complete validation output with independent status dimensions.

    Attributes:
        validation_run_id: Unique identifier for this validation run.
        evaluation_timestamp: ISO timestamp of evaluation.
        model_name: Name of the scientific model.
        model_version: Version of the model.
        prediction_ids: List of prediction IDs that were evaluated.
        dataset_version: Version label of the observation dataset.
        evaluation_method: How predictions were produced.
        protocol: The validation protocol used (or None if missing).
        overall_metrics: Overall metrics across all pairs.
        crop_evaluations: Per-crop evaluation results.
        matched_pairs: All :class:`ValidationPair` objects.
        unmatched_predictions: Predictions with no matching observation.
        unmatched_observations: Observations with no matching prediction.
        data_records_total: Total observation records received.
        data_records_accepted: Records that passed quality gates.
        data_records_rejected: Records that failed quality gates.
        data_records_review: Records requiring manual review.
        total_unique_sites: Number of unique sites across all matched pairs.
        total_unique_seasons: Number of unique seasons across all matched pairs.
        total_unique_crops: Number of unique crops across all matched pairs.
        total_unique_fields: Number of unique fields across all matched pairs.
        data_availability_status: Whether data was available.
        data_quality_status: Aggregate quality gate outcome.
        evaluation_independence_status: Whether eval is independent of calibration.
        sample_adequacy_status: Whether sample size is adequate.
        external_validation_status: The final validation status verdict.
        data_leakage_status: Whether data leakage prevention is active.
        leakage_violations: List of specific leakage violations found.
        scientific_limitations: List of limitations affecting interpretation.
        notes: Free-form notes about the evaluation.
    """

    validation_run_id: str
    evaluation_timestamp: str
    model_name: str
    model_version: str
    prediction_ids: list[str]
    dataset_version: str
    evaluation_method: str
    protocol: ValidationProtocol | None
    overall_metrics: ValidationMetrics | None
    crop_evaluations: list[CropEvaluation]
    matched_pairs: list[ValidationPair]
    unmatched_predictions: list[PredictionResult]
    unmatched_observations: list[RealFieldRecord]
    data_records_total: int
    data_records_accepted: int
    data_records_rejected: int
    data_records_review: int
    total_unique_sites: int
    total_unique_seasons: int
    total_unique_crops: int
    total_unique_fields: int
    data_availability_status: str
    data_quality_status: str
    evaluation_independence_status: str
    sample_adequacy_status: str
    external_validation_status: str
    data_leakage_status: str
    leakage_violations: list[str]
    scientific_limitations: list[str]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        overall = None
        if self.overall_metrics:
            overall = {
                "mae": self.overall_metrics.mae_result.to_dict(),
                "rmse": self.overall_metrics.rmse_result.to_dict(),
                "bias": self.overall_metrics.bias_result.to_dict(),
                "r_squared": self.overall_metrics.r_squared_result.to_dict(),
                "mape": self.overall_metrics.mape_result.to_dict(),
                "n_samples": self.overall_metrics.n_samples,
                "mean_observed": self.overall_metrics.mean_observed,
                "mean_predicted": self.overall_metrics.mean_predicted,
                "common_unit": self.overall_metrics.common_unit,
            }

        crop_list = []
        for c in self.crop_evaluations:
            crop_dict: dict[str, Any] = {
                "crop": c.crop,
                "pair_count": c.pair_count,
                "site_count": c.site_count,
                "season_count": c.season_count,
                "adequacy_status": c.adequacy_status,
                "in_scope": c.in_scope,
                "limitation": c.limitation,
            }
            if c.metrics:
                crop_dict["metrics"] = {
                    "mae": c.metrics.mae_result.to_dict(),
                    "rmse": c.metrics.rmse_result.to_dict(),
                    "bias": c.metrics.bias_result.to_dict(),
                    "r_squared": c.metrics.r_squared_result.to_dict(),
                    "mape": c.metrics.mape_result.to_dict(),
                    "n_samples": c.metrics.n_samples,
                    "mean_observed": c.metrics.mean_observed,
                    "mean_predicted": c.metrics.mean_predicted,
                }
            else:
                crop_dict["metrics"] = None
            crop_list.append(crop_dict)

        return {
            "validation_run_id": self.validation_run_id,
            "evaluation_timestamp": self.evaluation_timestamp,
            "model": {"name": self.model_name, "version": self.model_version},
            "prediction_ids": self.prediction_ids,
            "dataset_version": self.dataset_version,
            "evaluation_method": self.evaluation_method,
            "protocol": self.protocol.to_dict() if self.protocol else None,
            "overall_metrics": overall,
            "crop_evaluations": crop_list,
            "data_coverage": {
                "total_unique_sites": self.total_unique_sites,
                "total_unique_seasons": self.total_unique_seasons,
                "total_unique_crops": self.total_unique_crops,
                "total_unique_fields": self.total_unique_fields,
            },
            "matched_pairs_count": len(self.matched_pairs),
            "unmatched_predictions_count": len(self.unmatched_predictions),
            "unmatched_observations_count": len(self.unmatched_observations),
            "data_quality": {
                "total": self.data_records_total,
                "accepted": self.data_records_accepted,
                "rejected": self.data_records_rejected,
                "requires_review": self.data_records_review,
            },
            "statuses": {
                "data_availability": self.data_availability_status,
                "data_quality": self.data_quality_status,
                "evaluation_independence": self.evaluation_independence_status,
                "sample_adequacy": self.sample_adequacy_status,
                "external_validation": self.external_validation_status,
                "data_leakage": self.data_leakage_status,
            },
            "leakage_violations": self.leakage_violations,
            "scientific_limitations": self.scientific_limitations,
            "notes": self.notes,
        }


def _compute_metrics_safe(
    pairs: list[ValidationPair],
    unit: str = "t/ha",
) -> ValidationMetrics | None:
    """Compute metrics for a list of pairs, or None if insufficient data."""
    if len(pairs) == 0:
        return None
    obs = np.array([p.observed_yield_t_ha for p in pairs])
    pred = np.array([p.predicted_yield_t_ha for p in pairs])
    return compute_validation_metrics(obs, pred, unit=unit)


def _group_by_key(
    pairs: list[ValidationPair], key_func
) -> dict[str, list[ValidationPair]]:
    """Group pairs by a key function."""
    groups: dict[str, list[ValidationPair]] = {}
    for p in pairs:
        k = key_func(p)
        groups.setdefault(k, []).append(p)
    return groups


def _compute_crop_evaluations(
    pairs: list[ValidationPair],
    protocol: ValidationProtocol | None,
    evaluation_target: EvaluationTarget,
) -> list[CropEvaluation]:
    """Compute per-crop evaluation with adequacy assessment."""
    crop_groups = _group_by_key(pairs, lambda p: p.crop)
    crops_in_scope = set(protocol.crops_in_scope) if protocol else set()

    results: list[CropEvaluation] = []
    for crop_name, crop_pairs in sorted(crop_groups.items()):
        sites = {p.site_id for p in crop_pairs}
        seasons = {p.season_id for p in crop_pairs}
        metrics = _compute_metrics_safe(crop_pairs)

        adequacy, limitations = assess_sample_adequacy(
            n_pairs=len(crop_pairs),
            n_sites=len(sites),
            n_seasons=len(seasons),
            n_crops=1,
            evaluation_target=evaluation_target,
        )

        in_scope = crop_name in crops_in_scope if protocol else True
        limitation = "; ".join(limitations) if limitations else ""

        results.append(
            CropEvaluation(
                crop=crop_name,
                pair_count=len(crop_pairs),
                site_count=len(sites),
                season_count=len(seasons),
                metrics=metrics,
                adequacy_status=adequacy.value,
                in_scope=in_scope,
                limitation=limitation,
            )
        )
    return results


def _assess_evaluation_independence(
    protocol: ValidationProtocol | None,
    split: ValidationSplit | None,
    pairs: list[ValidationPair],
) -> tuple[EvaluationIndependenceStatus, list[str]]:
    """Assess whether the evaluation is independent of calibration data.

    Independence is confirmed when:
    - A protocol defines separate calibration and validation datasets.
    - OR a split is provided where calibration and validation/test sets share
      no (site, season) keys.
    """
    if protocol is not None:
        if protocol.calibration_dataset_id == protocol.validation_dataset_id:
            return (
                EvaluationIndependenceStatus.NOT_INDEPENDENT,
                ["Calibration and validation datasets are identical."],
            )
        return EvaluationIndependenceStatus.INDEPENDENT, []

    if split is not None:
        violations = split.leakage_check()
        if violations:
            return EvaluationIndependenceStatus.NOT_INDEPENDENT, violations
        if not split.calibration and not split.validation:
            return (
                EvaluationIndependenceStatus.UNKNOWN,
                ["No calibration split defined; independence unclear."],
            )
        return EvaluationIndependenceStatus.INDEPENDENT, []

    # No protocol and no split — independence cannot be verified
    return (
        EvaluationIndependenceStatus.UNKNOWN,
        ["No validation protocol or split provided; independence cannot be verified."],
    )


def produce_validation_report(
    predictions: list[PredictionResult],
    observations: list[RealFieldRecord],
    *,
    dataset_version: str = "1.0.0",
    evaluation_method: str = "seasonal_pipeline",
    protocol: ValidationProtocol | None = None,
    split: ValidationSplit | None = None,
    evaluation_target: EvaluationTarget | None = None,
) -> ValidationOutput:
    """Produce a complete validation report from predictions and observations.

    Args:
        predictions: List of PredictionResult objects (from Stage 26).
        observations: List of RealFieldRecord objects (real field data).
        dataset_version: Version label for the observation dataset.
        evaluation_method: How predictions were produced.
        protocol: Optional validation protocol defining the evaluation design.
        split: Optional pre-computed split for leakage tracking.
        evaluation_target: What generalization type is tested. Inferred from
            protocol if available.

    Returns:
        A :class:`ValidationOutput` with all metrics, groupings, and status.
    """
    from engine.hydroma.eval.validation_matching import (
        match_predictions_to_observations,
    )

    validation_run_id = f"VAL-{uuid4().hex[:12].upper()}"
    timestamp = datetime.now(UTC).isoformat()

    # Run quality gates on observations first, then count
    observations = run_quality_gates(observations) if observations else observations

    total_obs = len(observations)
    accepted_obs = sum(
        1 for o in observations if o.quality_gate_decision == "ACCEPTED"
    )
    rejected_obs = sum(
        1 for o in observations if o.quality_gate_decision == "REJECTED"
    )
    review_obs = sum(
        1 for o in observations if o.quality_gate_decision == "REQUIRES_REVIEW"
    )

    # Data availability
    if total_obs == 0:
        data_availability = DataAvailabilityStatus.NO_DATA
    elif accepted_obs == 0:
        data_availability = DataAvailabilityStatus.INSUFFICIENT_DATA
    else:
        data_availability = DataAvailabilityStatus.AVAILABLE

    # Data quality
    if rejected_obs > 0 and accepted_obs == 0:
        data_quality = DataQualityStatus.REJECTED
    elif review_obs > 0:
        data_quality = DataQualityStatus.REQUIRES_REVIEW
    else:
        data_quality = DataQualityStatus.ACCEPTED

    # Match predictions to observations
    pairs = match_predictions_to_observations(predictions, observations, run_gates=False)

    # Track unmatched
    matched_pred_ids = {p.prediction.prediction_id for p in pairs}
    unmatched_preds = [p for p in predictions if p.prediction_id not in matched_pred_ids]

    matched_obs_keys = {(p.observation.site_id, p.observation.season_id) for p in pairs}
    unmatched_obs = [
        o for o in observations
        if (o.site_id, o.season_id) not in matched_obs_keys
    ]

    # Coverage metrics
    unique_sites = {p.site_id for p in pairs}
    unique_seasons = {p.season_id for p in pairs}
    unique_crops = {p.crop for p in pairs}
    unique_fields = {p.observation.field_id for p in pairs if p.observation.field_id}

    # Overall metrics
    overall = _compute_metrics_safe(pairs)

    # Per-crop evaluations
    target = evaluation_target
    if target is None:
        if protocol is not None:
            target = protocol.evaluation_target
        elif split is not None:
            target = EvaluationTarget.SPATIAL
        else:
            target = EvaluationTarget.NONE

    crop_evals = _compute_crop_evaluations(pairs, protocol, target)

    # Evaluation independence
    independence, independence_notes = _assess_evaluation_independence(
        protocol, split, pairs
    )

    # Data leakage check
    leakage_violations: list[str] = []
    leakage_status = DataLeakageStatus.NOT_APPLICABLE
    if split is not None:
        leakage_violations = split.leakage_check()
        if leakage_violations:
            leakage_status = DataLeakageStatus.POTENTIAL_LEAKAGE
        else:
            leakage_status = DataLeakageStatus.CLEAN

    # Sample adequacy
    sample_adequacy, adequacy_limitations = assess_sample_adequacy(
        n_pairs=len(pairs),
        n_sites=len(unique_sites),
        n_seasons=len(unique_seasons),
        n_crops=len(unique_crops),
        evaluation_target=target,
    )

    # Determine validation status
    has_protocol = protocol is not None
    val_status = determine_external_validation_status(
        n_pairs=len(pairs),
        data_availability=data_availability,
        data_quality=data_quality,
        evaluation_independence=independence,
        sample_adequacy=sample_adequacy,
        data_leakage=leakage_status,
        has_protocol=has_protocol,
    )

    # Scientific limitations
    limitations: list[str] = []
    if data_availability == DataAvailabilityStatus.NO_DATA:
        limitations.append("No real observation data available for validation.")
    if data_availability == DataAvailabilityStatus.INSUFFICIENT_DATA:
        limitations.append(
            f"Only {accepted_obs} of {total_obs} records passed quality gates; "
            "insufficient data for evaluation."
        )
    if independence == EvaluationIndependenceStatus.NOT_INDEPENDENT:
        limitations.append(
            "Evaluation set overlaps with calibration data; results are not "
            "independently validated."
        )
    if independence == EvaluationIndependenceStatus.UNKNOWN:
        limitations.append(
            "Evaluation independence cannot be verified without a validation "
            "protocol or data split."
        )
    if leakage_status == DataLeakageStatus.POTENTIAL_LEAKAGE:
        limitations.append(
            "Data leakage detected: some (site, season) pairs appear in "
            "multiple splits. Results may be over-optimistic."
        )
    limitations.extend(adequacy_limitations)

    for note in independence_notes:
        if note not in limitations:
            limitations.append(note)

    n_crops = len(unique_crops)
    limitations.append(
        f"Evaluation covers {n_crops} crop(s); extrapolation to untested "
        "crops is not supported."
    )

    # Check if all data is synthetic
    all_synthetic = all(
        p.observation.data_label.startswith("synthetic")
        for p in pairs
    )
    if all_synthetic and pairs:
        limitations.append(
            "All matched observations are synthetic test data; results "
            "do not constitute external validation."
        )

    # Protocol limitations
    if protocol is not None and not protocol.is_complete():
        limitations.append(
            "Validation protocol is incomplete; "
            "external validation claims are limited."
        )

    prediction_ids = [p.prediction_id for p in predictions]
    model_name = predictions[0].model_name if predictions else "HY-RUE"
    model_version = predictions[0].model_version if predictions else "2.0.0"

    return ValidationOutput(
        validation_run_id=validation_run_id,
        evaluation_timestamp=timestamp,
        model_name=model_name,
        model_version=model_version,
        prediction_ids=prediction_ids,
        dataset_version=dataset_version,
        evaluation_method=evaluation_method,
        protocol=protocol,
        overall_metrics=overall,
        crop_evaluations=crop_evals,
        matched_pairs=pairs,
        unmatched_predictions=unmatched_preds,
        unmatched_observations=unmatched_obs,
        data_records_total=total_obs,
        data_records_accepted=accepted_obs,
        data_records_rejected=rejected_obs,
        data_records_review=review_obs,
        total_unique_sites=len(unique_sites),
        total_unique_seasons=len(unique_seasons),
        total_unique_crops=len(unique_crops),
        total_unique_fields=len(unique_fields),
        data_availability_status=data_availability.value,
        data_quality_status=data_quality.value,
        evaluation_independence_status=independence.value,
        sample_adequacy_status=sample_adequacy.value,
        external_validation_status=val_status.value,
        data_leakage_status=leakage_status.value,
        leakage_violations=leakage_violations,
        scientific_limitations=limitations,
    )
