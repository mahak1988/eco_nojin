"""Real field observation contracts for external validation of HY-RUE.

Defines the data contracts and quality gates for *real* (non-synthetic)
field observations: site metadata, growing-season metadata, and harvest
yield records.  All validation is structural and quality-flag based;
no synthetic data is ever accepted as a real observation.

Quality gates:
    - Reject records with non-finite yield values.
    - Reject records with invalid yield units.
    - Reject negative yields.
    - Detect and flag duplicate (site, season) records.
    - Flag records with missing critical metadata as REQUIRES_REVIEW.

Provenance vocabulary for observation sources:
    ``field_measured``     instrument deployed at the site.
    ``satellite_retrieved`` satellite product.
    ``analysis_product``   reanalysis / analysis gridded product.
    ``published_literature`` secondary data from a published study.

This module is import-safe: pydantic + numpy only — no service or network imports.
"""

from __future__ import annotations

import math
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

YIELD_UNIT_T_HA = "t/ha"
YIELD_UNIT_KG_HA = "kg/ha"
YIELD_UNIT_G_M2 = "g/m²"

VALID_YIELD_UNITS: frozenset[str] = frozenset(
    {YIELD_UNIT_T_HA, YIELD_UNIT_KG_HA, YIELD_UNIT_G_M2}
)

#: Conversion factors to t/ha (the internal canonical unit).
_YIELD_TO_T_HA: dict[str, float] = {
    YIELD_UNIT_T_HA: 1.0,
    YIELD_UNIT_KG_HA: 0.001,
    YIELD_UNIT_G_M2: 0.01,
}


def convert_yield_to_t_ha(value: float, unit: str) -> float:
    """Convert a yield value to t/ha.

    Args:
        value: The numeric yield value.
        unit: One of ``t/ha``, ``kg/ha``, ``g/m²``.

    Returns:
        The yield value in t/ha.

    Raises:
        ValueError: if the unit is not recognised.
    """
    unit_clean = unit.strip()
    if unit_clean not in _YIELD_TO_T_HA:
        raise ValueError(
            f"Unknown yield unit {unit!r}; expected one of {VALID_YIELD_UNITS}"
        )
    return value * _YIELD_TO_T_HA[unit_clean]


class QualityGateDecision(StrEnum):
    """Outcome of a quality gate check on a field record."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


VALID_QUALITY_GATE_DECISIONS = {
    QualityGateDecision.ACCEPTED,
    QualityGateDecision.REJECTED,
    QualityGateDecision.REQUIRES_REVIEW,
}


class ObservationSource(StrEnum):
    """Source provenance for real field observations (extended vocabulary)."""

    FIELD_MEASURED = "field_measured"
    SATELLITE_RETRIEVED = "satellite_retrieved"
    ANALYSIS_PRODUCT = "analysis_product"
    PUBLISHED_LITERATURE = "published_literature"


VALID_OBSERVATION_SOURCES = {
    ObservationSource.FIELD_MEASURED,
    ObservationSource.SATELLITE_RETRIEVED,
    ObservationSource.ANALYSIS_PRODUCT,
    ObservationSource.PUBLISHED_LITERATURE,
}


class RealFieldRecord(BaseModel):
    """A single real field observation record for external validation.

    Attributes:
        site_id: Stable, unique identifier for the site within a dataset.
        field_id: Identifier for the specific field parcel (``site_id`` may
            cover multiple fields).
        season_id: Season identifier (crop + year, e.g. ``"wheat_2024"``).
        crop: Crop name (``"wheat"``, ``"maize"``, etc.).
        cultivar: Optional cultivar or variety name.
        planting_date: ISO date string of planting.
        harvest_date: ISO date string of harvest.
        latitude: WGS84 decimal degrees (positive = north).
        longitude: WGS84 decimal degrees (positive = east).
        area_ha: Field area in hectares.
        observed_yield: Observed harvest yield value (in ``observed_yield_unit``).
        observed_yield_unit: One of ``t/ha``, ``kg/ha``, ``g/m²``.
        yield_measurement_method: Description of how yield was measured.
        harvest_sample_size: Number of sub-samples or quadrats used.
        observation_source: Origin of the observation.
        observation_source_id: Optional identifier of the source dataset/study.
        quality_gate_decision: ACCEPTED / REJECTED / REQUIRES_REVIEW.
        quality_gate_reasons: Human-readable reasons for the decision.
        data_label: Label identifying this record's data origin (real datasets
            must have a label that does not start with ``"synthetic"``).
    """

    model_config = {"extra": "forbid"}

    site_id: str = Field(min_length=1)
    field_id: str | None = None
    season_id: str = Field(min_length=1)
    crop: str = Field(min_length=1)
    cultivar: str | None = None
    planting_date: date
    harvest_date: date
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    area_ha: float | None = Field(default=None, ge=0.0)
    observed_yield: float
    observed_yield_unit: str = Field(min_length=1)
    yield_measurement_method: str | None = None
    harvest_sample_size: int | None = Field(default=None, ge=1)
    observation_source: str = Field(min_length=1)
    observation_source_id: str | None = None
    quality_gate_decision: str = QualityGateDecision.ACCEPTED.value
    quality_gate_reasons: list[str] = Field(default_factory=list)
    data_label: str = "real_field_data"

    @field_validator("observed_yield")
    @classmethod
    def reject_non_finite(cls, v: float) -> float:
        if not isinstance(v, (int, float)):
            raise ValueError(f"observed_yield must be numeric, got {type(v)}")
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"observed_yield must be finite, got {v}")
        return float(v)

    @field_validator("observed_yield")
    @classmethod
    def reject_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"observed_yield must be non-negative, got {v}")
        return v

    @field_validator("observed_yield_unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        unit_clean = v.strip()
        if unit_clean not in VALID_YIELD_UNITS:
            raise ValueError(
                f"observed_yield_unit {unit_clean!r} not in {VALID_YIELD_UNITS}"
            )
        return unit_clean

    @field_validator("harvest_date")
    @classmethod
    def harvest_after_planting(cls, v: date, info) -> date:
        planting = info.data.get("planting_date")
        if planting is not None and v < planting:
            raise ValueError(
                f"harvest_date ({v}) must not precede planting_date ({planting})"
            )
        return v

    @field_validator("data_label")
    @classmethod
    def reject_synthetic_label(cls, v: str) -> str:
        if v.startswith("synthetic"):
            raise ValueError(
                f"data_label {v!r} is marked synthetic; "
                "RealFieldRecord requires a real data source label"
            )
        return v

    @field_validator("observation_source")
    @classmethod
    def validate_observation_source(cls, v: str) -> str:
        if v not in VALID_OBSERVATION_SOURCES:
            raise ValueError(
                f"observation_source {v!r} not in "
                f"{VALID_OBSERVATION_SOURCES}"
            )
        return v

    @property
    def yield_t_ha(self) -> float:
        """Observed yield converted to the canonical t/ha unit."""
        return convert_yield_to_t_ha(self.observed_yield, self.observed_yield_unit)

    @property
    def record_key(self) -> tuple[str, str, str]:
        """Unique matching key: (site_id, season_id, crop)."""
        return (self.site_id, self.season_id, self.crop)


def run_quality_gates(
    records: list[RealFieldRecord],
) -> list[RealFieldRecord]:
    """Apply quality gate rules to a batch of records in-place.

    Rules:
    1.  Non-finite or negative yield → REJECTED.
    2.  Invalid yield unit → REJECTED.
    3.  Duplicate (site_id, season_id, crop) → second+ record flagged
        REQUIRES_REVIEW.
    4.  Missing critical metadata (area_ha, cultivar, sample_size) →
        REQUIRES_REVIEW (not rejected — metadata is optional but informative).
    5.  ``synthetic`` data_label → always REJECTED (defensive; the
        validator should already reject it, but this is a belt-and-suspenders check).

    Returns a new list with quality_gate fields updated. Records that
    fail pydantic validation are not included (they raise at construction).
    """
    seen_keys: dict[tuple[str, str, str], RealFieldRecord] = {}
    results: list[RealFieldRecord] = []

    for rec in records:
        if rec.data_label.startswith("synthetic"):
            rec.quality_gate_decision = QualityGateDecision.REJECTED.value
            rec.quality_gate_reasons = ["record is labeled synthetic"]
            results.append(rec)
            continue

        if rec.observed_yield < 0:
            rec.quality_gate_decision = QualityGateDecision.REJECTED.value
            rec.quality_gate_reasons = ["observed_yield is negative"]
            results.append(rec)
            continue

        key = rec.record_key
        if key in seen_keys:
            prev = seen_keys[key]
            rec.quality_gate_decision = QualityGateDecision.REQUIRES_REVIEW.value
            rec.quality_gate_reasons = [
                f"duplicate of record for site_id={prev.site_id}, "
                f"season_id={prev.season_id}, crop={prev.crop}"
            ]
        else:
            seen_keys[key] = rec

            if rec.area_ha is None:
                rec.quality_gate_reasons.append(
                    "area_ha is missing; field size unknown"
                )
            if rec.cultivar is None:
                rec.quality_gate_reasons.append("cultivar is not specified")
            if rec.harvest_sample_size is None:
                rec.quality_gate_reasons.append(
                    "harvest_sample_size is not specified"
                )
            if rec.quality_gate_reasons:
                rec.quality_gate_decision = QualityGateDecision.REQUIRES_REVIEW.value

        results.append(rec)

    return results
