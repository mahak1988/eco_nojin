"""Matching pipeline: HYRUE predictions to real field observations.

This module closes the loop between Stage 26 (prediction) and Stage 27
(validation):

    SeasonalPredictionRequest
        -> compute_seasonal_prediction() -> PredictionResult
        -> match_prediction_to_observation() -> ValidationPair
        -> compute_validation_metrics() -> ValidationMetrics

The matching is strict: a prediction and an observation are paired
**only** when they share ``site_id``, ``season_id``, and ``crop``.
No fuzzy matching of crop names, years, or seasons is performed.

This module is import-safe: dataclasses + numpy only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from engine.hydroma.eval.field_validation import (
    QualityGateDecision,
    RealFieldRecord,
    convert_yield_to_t_ha,
    run_quality_gates,
)
from engine.hydroma.eval.prediction import PredictionResult


@dataclass
class ValidationPair:
    """A prediction paired with a real field observation.

    Attributes:
        pair_id: Unique identifier for this validation pair.
        site_id: Shared site identifier.
        season_id: Shared season identifier.
        crop: Shared crop name.
        prediction: The :class:`PredictionResult`.
        observation: The :class:`RealFieldRecord`.
        predicted_yield_t_ha: Prediction value in t/ha.
        observed_yield_t_ha: Observation value in t/ha.
        prediction_unit: Unit of the prediction.
        observation_unit: Unit of the observation.
        yield_unit_conversion: How the observation was converted.
        quality_gate_decision: The observation's quality gate status.
    """

    pair_id: str
    site_id: str
    season_id: str
    crop: str
    prediction: PredictionResult
    observation: RealFieldRecord
    predicted_yield_t_ha: float
    observed_yield_t_ha: float
    prediction_unit: str
    observation_unit: str
    yield_unit_conversion: str
    quality_gate_decision: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def residual(self) -> float:
        """observed - predicted in t/ha."""
        return self.observed_yield_t_ha - self.predicted_yield_t_ha

    @property
    def relative_error(self) -> float:
        """|residual| / |observed| (dimensionless). 0 if observed is 0."""
        if self.observed_yield_t_ha == 0:
            return 0.0
        return abs(self.residual) / abs(self.observed_yield_t_ha)


def match_prediction_to_observations(
    prediction: PredictionResult,
    observations: list[RealFieldRecord],
) -> list[ValidationPair]:
    """Match a single prediction to real observations.

    Matching key: ``(site_id, season_id, crop)``.

    Only observations with ``quality_gate_decision == ACCEPTED`` are matched.
    Observations that are REJECTED or REQUIRES_REVIEW are skipped.
    """
    pairs: list[ValidationPair] = []
    pred_key = (prediction.site_id, prediction.season_id, _crop_from_metadata(prediction))

    for obs in observations:
        if obs.quality_gate_decision != QualityGateDecision.ACCEPTED.value:
            continue

        obs_key = (obs.site_id, obs.season_id, obs.crop)
        if obs_key != pred_key:
            continue

        pred_val = prediction.value if prediction.value is not None else 0.0
        if prediction.unit == "t/ha":
            pred_t_ha = pred_val
            pred_unit = "t/ha"
        else:
            pred_t_ha = convert_yield_to_t_ha(pred_val, prediction.unit)
            pred_unit = "t/ha"

        obs_t_ha = obs.yield_t_ha

        conversion_note = "observed already in t/ha"
        if obs.observed_yield_unit != "t/ha":
            conversion_note = (
                f"converted {obs.observed_yield_unit} -> t/ha "
                f"(factor={_conversion_factor(obs.observed_yield_unit)})"
            )

        pairs.append(
            ValidationPair(
                pair_id=f"VP-{uuid4().hex[:12].upper()}",
                site_id=prediction.site_id,
                season_id=prediction.season_id,
                crop=pred_key[2],
                prediction=prediction,
                observation=obs,
                predicted_yield_t_ha=float(pred_t_ha),
                observed_yield_t_ha=float(obs_t_ha),
                prediction_unit=pred_unit,
                observation_unit=obs.observed_yield_unit,
                yield_unit_conversion=conversion_note,
                quality_gate_decision=obs.quality_gate_decision,
                metadata={
                    "prediction_computation_mode": prediction.metadata.get(
                        "computation_mode"
                    ),
                    "observation_source": obs.observation_source,
                },
            )
        )

    return pairs


def _crop_from_metadata(prediction: PredictionResult) -> str:
    """Extract crop name from prediction metadata."""
    return prediction.metadata.get("crop", "wheat")


def _conversion_factor(unit: str) -> float:
    """Return the conversion factor for a yield unit to t/ha."""
    factors = {"t/ha": 1.0, "kg/ha": 0.001, "g/m²": 0.01}
    return factors.get(unit.strip(), 1.0)


def match_predictions_to_observations(
    predictions: list[PredictionResult],
    observations: list[RealFieldRecord],
    *,
    run_gates: bool = True,
) -> list[ValidationPair]:
    """Match multiple predictions to observations.

    Args:
        predictions: List of :class:`PredictionResult` objects.
        observations: List of :class:`RealFieldRecord` objects.
        run_gates: If True, run quality gates on observations before matching.

    Returns:
        List of :class:`ValidationPair` objects, one per matched pair.
    """
    if run_gates and observations:
        observations = run_quality_gates(observations)

    pairs: list[ValidationPair] = []
    for pred in predictions:
        pairs.extend(
            match_prediction_to_observations(pred, observations)
        )
    return pairs


@dataclass
class ValidationSplit:
    """A train/validation/test split of real observation records.

    Ensures no leakage: the same (site_id, season_id) pair does not
    appear in more than one split. Splitting is by **site** (preferred)
    or by **season** to prevent within-site or within-season leakage.

    Attributes:
        calibration: Records used for parameter calibration (if any).
        validation: Records used for validation.
        test: Records held out for independent testing.
        method: ``"site"`` or ``"season"``.
        seed: Randomness seed (for reproducibility of random allocation).
        generalization_type: ``"spatial"``, ``"temporal"``, or
            ``"spatial_and_temporal"`` — describes what generalization
            the split is designed to test.
        unit_of_independence: ``"site"``, ``"field"``, or ``"season"`` —
            the granularity at which independence is enforced.
    """

    calibration: list[RealFieldRecord] = field(default_factory=list)
    validation: list[RealFieldRecord] = field(default_factory=list)
    test: list[RealFieldRecord] = field(default_factory=list)
    method: str = "site"
    seed: int = 42
    generalization_type: str = "spatial"
    unit_of_independence: str = "site"

    def _keys(self, records: list[RealFieldRecord]) -> set[tuple[str, str]]:
        """Extract (site_id, season_id) keys from records."""
        return {(r.site_id, r.season_id) for r in records}

    def leakage_check(self) -> list[str]:
        """Return list of leakage violations (empty if clean).

        Checks for both pairwise and three-way overlap of (site, season) pairs
        across calibration, validation, and test splits.
        """
        violations: list[str] = []

        cal_keys = self._keys(self.calibration)
        val_keys = self._keys(self.validation)
        test_keys = self._keys(self.test)

        # Pairwise overlaps
        cal_val_overlap = cal_keys & val_keys
        if cal_val_overlap:
            violations.append(
                f"leakage: {len(cal_val_overlap)} (site,season) pairs appear "
                f"in both calibration and validation"
            )
        cal_test_overlap = cal_keys & test_keys
        if cal_test_overlap:
            violations.append(
                f"leakage: {len(cal_test_overlap)} (site,season) pairs appear "
                f"in both calibration and test"
            )
        val_test_overlap = val_keys & test_keys
        if val_test_overlap:
            violations.append(
                f"leakage: {len(val_test_overlap)} (site,season) pairs appear "
                f"in both validation and test"
            )

        # Three-way overlaps
        three_way = cal_keys & val_keys & test_keys
        if three_way:
            violations.append(
                f"leakage: {len(three_way)} (site,season) pairs appear in all "
                "three splits"
            )

        return violations

    def has_site_overlap(
        self, other_split_name: str, other_keys: set[tuple[str, str]]
    ) -> int:
        """Count site-level overlap with another split's keys.

        Returns the number of (site_id, season_id) pairs that overlap.
        """
        my_keys = self._keys(self.validation + self.test)
        return len(my_keys & other_keys)


def split_for_validation(
    records: list[RealFieldRecord],
    *,
    method: str = "site",
    site_frac: float = 0.7,
    seed: int = 42,
    generalization_type: str = "spatial",
    unit_of_independence: str = "site",
) -> ValidationSplit:
    """Split real observation records for validation.

    ``method="site"`` puts distinct sites into calibration/validation/test
    (preferred — prevents within-site leakage).
    ``method="season"`` puts distinct seasons into calibration/validation/test.

    The calibration split may be empty (calibration may happen externally via
    the Stage 26 pipeline). In that case, all records go into
    validation or test only.

    Args:
        records: Real observation records (will be quality-gated).
        method: ``"site"`` or ``"season"``.
        site_frac: Fraction of groups for calibration.
        seed: Reproducibility seed.
        generalization_type: What generalization is being tested
            (``"spatial"``, ``"temporal"``, ``"spatial_and_temporal"``).
        unit_of_independence: Granularity of independence
            (``"site"``, ``"field"``, ``"season"``).
    """
    import random

    records = run_quality_gates(records) if records else records
    accepted = [
        r for r in records
        if r.quality_gate_decision == QualityGateDecision.ACCEPTED.value
    ]

    rng = random.Random(seed)

    if method == "site":
        groups: dict[str, list[RealFieldRecord]] = {}
        for r in accepted:
            groups.setdefault(r.site_id, []).append(r)
    elif method == "season":
        groups: dict[str, list[RealFieldRecord]] = {}
        for r in accepted:
            groups.setdefault(r.season_id, []).append(r)
    else:
        raise ValueError(f"unknown split method {method!r}; use 'site' or 'season'")

    keys = list(groups.keys())
    rng.shuffle(keys)
    n_cal = int(len(keys) * site_frac)
    cal_keys = set(keys[:n_cal]) if n_cal > 0 else set()
    remaining_keys = keys[n_cal:] if n_cal > 0 else keys
    rng.shuffle(remaining_keys)
    n_val = int(len(remaining_keys) * 0.5)
    val_keys = set(remaining_keys[:n_val]) if n_val > 0 else set()
    test_keys = set(remaining_keys[n_val:])

    result = ValidationSplit(
        method=method,
        seed=seed,
        generalization_type=generalization_type,
        unit_of_independence=unit_of_independence,
    )
    for r in accepted:
        if method == "site":
            key = r.site_id
        else:
            key = r.season_id
        if key in cal_keys:
            result.calibration.append(r)
        elif key in val_keys:
            result.validation.append(r)
        elif key in test_keys:
            result.test.append(r)
        else:
            result.test.append(r)

    return result
