"""Prediction result types and HYRUE-to-observation matching.

Defines:
    - :class:`ComputationStatus` — whether the model actually ran.
    - :class:`ScientificSupportStatus` — what level of external evidence backs the result.
    - :class:`ExternalValidationStatus` — whether the result has been compared to observations.
    - :class:`InputQuality` — completeness of the input data.
    - :class:`PredictionResult` — a model prediction coupled to its provenance and status.
    - :class:`PredictionMatch` — a prediction paired with a field observation.
    - :func:`match_hyra_to_observations` — pairs HYRUE outputs with observations.

This module is import-safe (numpy + pydantic only — no service or network imports).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from engine.honesty.statuses import refine_claim
from engine.hydroma.eval.field_data import FieldObservation, VariableType


class ComputationStatus(StrEnum):
    """Whether the model actually ran to produce this prediction."""

    COMPUTED = "computed"
    FAIL_CLOSED = "fail_closed"
    PARTIAL = "partial"
    NOT_ATTEMPTED = "not_attempted"


class ExternalValidationStatus(StrEnum):
    """Whether the prediction has been compared against external observations."""

    VALIDATED_EXTERNAL = "VALIDATED_EXTERNAL"
    VALIDATED_METHOD_CONFORMANCE = "VALIDATED_METHOD_CONFORMANCE"
    REGRESSION_ANCHOR_STABLE = "REGRESSION_ANCHOR_STABLE"
    PARTIAL = "PARTIAL"
    UNVALIDATED = "UNVALIDATED"
    BLOCKED = "BLOCKED"

    @classmethod
    def from_vocabulary(cls, term: str) -> ExternalValidationStatus:
        """Accept the honesty vocabulary strings (including legacy alias)."""
        from engine.honesty.statuses import VOCABULARY

        if term not in VOCABULARY and term != "validated":
            raise ValueError(f"Unknown validation status {term!r}")
        if term == "validated":
            refined = refine_claim("validated", "VALIDATED_EXTERNAL")
            return cls(refined)
        return cls(term)


class ScientificSupportStatus(StrEnum):
    """Scientific grounding of the prediction's equations and parameters."""

    REFERENCED = "referenced"
    DEFAULTED = "defaulted"
    PARTIAL = "partial"
    UNVALIDATED = "unvalidated"
    BLOCKED = "blocked"


class InputQuality(StrEnum):
    """Completeness quality of the climate / model inputs."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


@dataclass
class PredictionResult:
    """A model prediction accompanied by provenance and quality metadata.

    Attributes:
        prediction_id: Unique identifier for this prediction.
        site_id: Site the prediction applies to.
        season_id: Season identifier.
        variable: Which variable was predicted (default: yield).
        value: The predicted numeric value.
        unit: Unit of the predicted value.
        computation_status: Whether the model ran.
        scientific_support_status: Scientific grounding level.
        external_validation_status: Validation status against observations.
        input_quality: Completeness of inputs.
        model_name: Name of the model that produced the prediction.
        model_version: Version of the model.
        data_source: Provenance of input data (measured/modelled/simulated etc.).
        computed: Whether the engine actually ran.
        par_provenance: Provenance label for PAR data.
        par_conversion_spec: Dict or None describing the PAR conversion.
        lai_provenance: Provenance metadata for LAI.
        ewsi_provenance: Provenance metadata for EWSI.
        shortwave_source: Source of shortwave radiation.
        missing_fields: Fields that were missing from inputs.
        prediction_interval_lower: Lower bound of prediction interval (optional).
        prediction_interval_upper: Upper bound of prediction interval (optional).
        uncertainty_std: Standard deviation of the prediction (optional).
        metadata: Additional free-form metadata.
    """

    prediction_id: str
    site_id: str
    season_id: str
    variable: str = "yield"
    value: float | None = None
    unit: str = "t/ha"
    computation_status: str = ComputationStatus.COMPUTED.value
    scientific_support_status: str = ScientificSupportStatus.REFERENCED.value
    external_validation_status: str = ExternalValidationStatus.UNVALIDATED.value
    input_quality: str = InputQuality.COMPLETE.value
    model_name: str = "HY-RUE"
    model_version: str = "2.0.0"
    data_source: str = "simulated"
    computed: bool = True
    par_provenance: str | None = None
    par_conversion_spec: dict[str, Any] | None = None
    lai_provenance: dict[str, Any] | None = None
    ewsi_provenance: dict[str, Any] | None = None
    shortwave_source: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    prediction_interval_lower: float | None = None
    prediction_interval_upper: float | None = None
    uncertainty_std: float | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "site_id": self.site_id,
            "season_id": self.season_id,
            "variable": self.variable,
            "value": self.value,
            "unit": self.unit,
            "computation_status": self.computation_status,
            "scientific_support_status": self.scientific_support_status,
            "external_validation_status": self.external_validation_status,
            "input_quality": self.input_quality,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "data_source": self.data_source,
            "computed": self.computed,
            "par_provenance": self.par_provenance,
            "par_conversion_spec": self.par_conversion_spec,
            "lai_provenance": self.lai_provenance,
            "ewsi_provenance": self.ewsi_provenance,
            "shortwave_source": self.shortwave_source,
            "missing_fields": self.missing_fields,
            "prediction_interval_lower": self.prediction_interval_lower,
            "prediction_interval_upper": self.prediction_interval_upper,
            "uncertainty_std": self.uncertainty_std,
            "metadata": self.metadata,
        }


@dataclass
class PredictionMatch:
    """A model prediction paired with a field observation.

    Attributes:
        prediction: The :class:`PredictionResult`.
        observation: The :class:`FieldObservation` it is compared against.
        prediction_value: The numeric prediction value.
        observed_value: The numeric observed value.
        prediction_unit: Unit of the prediction.
        observed_unit: Unit of the observation.
        prediction_value_normalized: Prediction value in the observation's unit.
        observed_value_normalized: Observed value in the observation's unit.
        residual: ``observed - prediction`` in common units.
        relative_error: ``residual / observed`` (dimensionless).
        absolute_residual: ``|observed - prediction|`` in common units.
    """

    prediction: PredictionResult
    observation: FieldObservation
    prediction_value: float
    observed_value: float
    prediction_unit: str
    observed_unit: str
    prediction_value_normalized: float
    observed_value_normalized: float
    residual: float
    relative_error: float
    absolute_residual: float


def _convert_yield_to_t_ha(value: float, unit: str) -> float:
    """Convert yield/biomass values to t/ha."""
    unit_normalized = unit.strip().lower().replace(" ", "").replace("^", "")
    conversion_factors = {
        "t/ha": 1.0,
        "tha": 1.0,
        "kg/ha": 0.001,
        "kgha": 0.001,
        "g/m2": 0.01,
        "gm2": 0.01,
    }
    factor = conversion_factors.get(unit_normalized, 1.0)
    return value * factor


def _convert_lai(value: float, unit: str) -> float:
    """LAI is dimensionless, but accept m2/m2 as equivalent to index."""
    return value


def _convert_par(value: float, unit: str) -> float:
    """Convert PAR to MJ/m²/day."""
    unit_normalized = unit.strip().lower().replace(" ", "").replace("^", "").replace("²", "2")
    if unit_normalized in ("mj/m2/day", "mj/m^2/day", "mj·m-2·day-1", "mjm2day"):
        return value
    if unit_normalized in ("mol/m2/day", "mol·m-2·day-1", "molm2day"):
        return value * 4.57  # ~4.57 MJ/mol for 400-700 nm
    if unit_normalized in ("w/m2", "wm2"):
        return value * 0.0864  # W/m² → MJ/m²/day (× 86400 s/day × 1e-6)
    return value


def match_hyra_to_observations(
    predictions: Sequence[PredictionResult],
    observations: Sequence[FieldObservation],
    *,
    match_fields: list[str] | None = None,
) -> list[PredictionMatch]:
    """Pair HYRUE predictions with field observations.

    Matching is performed on ``(site_id, season_id, variable)``.  When a
    prediction and an observation share all three, they are paired and unit
    conversion is applied so both values are in the observation's unit.

    Parameters
    ----------
    predictions:
        Model predictions to match.
    observations:
        Field observations to match against.
    match_fields:
        Optional override for the fields to match on. Default:
        ``["site_id", "season_id", "variable"]``.

    Returns:
        List of :class:`PredictionMatch` objects, one per matched pair.
    """
    if match_fields is None:
        match_fields = ["site_id", "season_id", "variable"]

    obs_by_key: dict[tuple[str, str, str], FieldObservation] = {}
    for obs in observations:
        key = (obs.site, obs.season, obs.variable.value)
        obs_by_key[key] = obs

    matches: list[PredictionMatch] = []

    for pred in predictions:
        key = (pred.site_id, pred.season_id, pred.variable)
        if key in obs_by_key:
            obs = obs_by_key[key]
            pred_val = pred.value if pred.value is not None else 0.0
            obs_val = obs.value

            pred_norm = _convert_to_common_unit(pred_val, pred.unit, obs.variable)
            obs_norm = _convert_to_common_unit(obs_val, obs.unit, obs.variable)

            residual = obs_norm - pred_norm
            rel_error = residual / obs_norm if obs_norm != 0 else float("inf")
            abs_residual = abs(residual)

            matches.append(
                PredictionMatch(
                    prediction=pred,
                    observation=obs,
                    prediction_value=pred_val,
                    observed_value=obs_val,
                    prediction_unit=pred.unit,
                    observed_unit=obs.unit,
                    prediction_value_normalized=pred_norm,
                    observed_value_normalized=obs_norm,
                    residual=residual,
                    relative_error=rel_error,
                    absolute_residual=abs_residual,
                )
            )

    return matches


def _convert_to_common_unit(value: float, unit: str, variable: VariableType | str) -> float:
    """Convert a value to a normalised unit based on its variable type."""
    var_str = variable.value if isinstance(variable, VariableType) else variable

    if var_str in ("yield", "biomass"):
        return _convert_yield_to_t_ha(value, unit)
    elif var_str == "lai":
        return _convert_lai(value, unit)
    elif var_str == "par":
        return _convert_par(value, unit)
    else:
        return value
