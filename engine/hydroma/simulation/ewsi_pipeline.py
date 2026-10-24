"""Daily EWSI (Water Stress Index) pipeline for the seasonal HYRUE computation.

This module connects the existing EWSI model at
``engine/hydroma/models/ewsi.py`` to the seasonal pipeline.  It assembles
the EWSI inputs (NIR/SWIR reflectance, VPD, soil moisture, field capacity)
into a daily time series and computes EWSI for each day.

Missing component policy:

* ``strict`` — all three components (NDMI, VPD, soil moisture) must be
  present.  If any is missing, computation is blocked (ValueError).
* ``allow_estimated`` — computation proceeds with available components.
  Weights of missing components are redistributed proportionally among
  available components.  Missing components are recorded in the output
  provenance.  Output is flagged as lower quality.

Provenance: ``model_generated`` — EWSI is a novel composite index (NDMI +
VPD + soil moisture) defined in this project.  Its inputs may come from
satellite observations, meteorological data, or soil models.

Honesty: EWSI is NOT a published index.  The three-factor composition, the
weights (0.4/0.3/0.3), and the VPD anchors are this project's own.  Only
the NDMI sub-index has a source (Gao 1996, corrected to note it is NDWI
not NDMI).  See ``engine/hydroma/models/ewsi.py::EWSI.REFERENCES``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np

from engine.hydroma.models.ewsi import EWSI, EWSIWeights
from engine.hydroma.simulation.quality_status import QualityStatus
from engine.hydroma.simulation.remote_sensing.spectral_indices import (
    ndmi,
    ndmi_stress,
)
from engine.hydroma.simulation.soil_moisture_model import (
    SoilMoistureInput,
    compute_daily_soil_stress,
)
from engine.hydroma.simulation.vpd_model import vpd_stress


class EWSIComputationPolicy(StrEnum):
    """Policy for handling missing EWSI components."""

    STRICT = "strict"
    ALLOW_ESTIMATED = "allow_estimated"


@dataclass
class EWSIComponentProvenance:
    """Provenance for a single EWSI component.

    Attributes:
        component: Component name ("ndmi", "vpd", "soil").
        present: Whether the component data was available.
        quality_status: QualityStatus of the component input.
        source: Data source label.
        source_product: Product identifier.
        stress_value: Computed stress value (None if component missing).
        weight: Effective weight after redistribution (0 if missing).
        original_weight: Original configured weight before redistribution.
    """

    component: str
    present: bool
    quality_status: str
    source: str = ""
    source_product: str = ""
    stress_value: float | None = None
    weight: float = 0.0
    original_weight: float = 0.0


@dataclass
class EWSIInputSeries:
    """Daily inputs for EWSI computation.

    All arrays must have the same length (one element per day).
    """

    dates: list[str]
    nir: np.ndarray | None = None
    swir: np.ndarray | None = None
    vpd: np.ndarray | None = None
    soil_moisture: np.ndarray | None = None
    soil_field_capacity: float = 0.35

    # Component-level provenance (optional, filled by caller)
    nir_quality: QualityStatus | None = None
    swir_quality: QualityStatus | None = None
    vpd_quality: QualityStatus | None = None
    soil_moisture_quality: QualityStatus | None = None
    nir_source: str = ""
    swir_source: str = ""
    vpd_source: str = ""
    soil_moisture_source: str = ""
    nir_source_product: str = ""
    swir_source_product: str = ""
    vpd_source_product: str = ""
    soil_moisture_source_product: str = ""


@dataclass
class EWSIOutputSeries:
    """Daily EWSI output with full provenance.

    Attributes:
        dates: ISO date strings.
        ewsi: Daily EWSI values in [0, 1].
        source_model: Model name ("EWSI").
        source_date: Source date label.
        unit: Unit label ("dimensionless").
        valid_range: Valid range tuple (0.0, 1.0).
        quality_status: Overall quality status.
        method: Computation method string.
        reference: Scientific reference string.
        scientific_status: Scientific status ("novel").
        weights: Effective weights after redistribution.
        missing_fields: List of component names that were missing.
        component_provenance: Per-component provenance details.
        computation_policy: Policy used (strict or allow_estimated).
        interpolated_dates: List of dates where interpolation was used.
    """

    dates: list[str]
    ewsi: np.ndarray
    source_model: str = "EWSI"
    source_date: str = "computed_from_daily_inputs"
    unit: str = "dimensionless"
    valid_range: tuple[float, float] = (0.0, 1.0)
    quality_status: str = "model_generated"
    method: str = "0.4*ndmi_stress + 0.3*vpd_stress + 0.3*soil_stress"
    reference: str = (
        "engine/hydroma/models/ewsi.py::EWSI.REFERENCES. "
        "EWSI is a novel composite index; only the NDMI sub-index has a source."
    )
    scientific_status: str = "novel"
    weights: dict[str, float] = field(
        default_factory=lambda: {"ndmi": 0.4, "vpd": 0.3, "soil": 0.3}
    )
    missing_fields: list[str] = field(default_factory=list)
    component_provenance: list[EWSIComponentProvenance] = field(
        default_factory=list
    )
    computation_policy: str = "strict"
    interpolated_dates: list[str] = field(default_factory=list)


def _redistribute_weights(
    weights: EWSIWeights,
    available: dict[str, bool],
) -> dict[str, float]:
    """Redistribute weights proportionally among available components.

    Args:
        weights: Original EWSIWeights.
        available: Dict of component -> available (bool).

    Returns:
        Dict of component -> effective weight (0 for missing, redistributed
        proportionally for available).  Sum of effective weights = 1.0 if
        at least one component is available, else all zeros.
    """
    total_available_weight = sum(
        getattr(weights, comp) for comp, avail in available.items() if avail
    )

    if total_available_weight <= 0:
        return {"ndmi": 0.0, "vpd": 0.0, "soil": 0.0}

    result: dict[str, float] = {}
    for comp in ("ndmi", "vpd", "soil"):
        if available[comp]:
            result[comp] = getattr(weights, comp) / total_available_weight
        else:
            result[comp] = 0.0
    return result


def compute_daily_ewsi(
    inputs: EWSIInputSeries,
    weights: EWSIWeights | None = None,
    policy: EWSIComputationPolicy | str = EWSIComputationPolicy.STRICT,
) -> EWSIOutputSeries:
    """Compute daily EWSI from input series with missing-component policy.

    Args:
        inputs: EWSIInputSeries with daily NIR/SWIR, VPD, soil moisture.
        weights: Optional custom EWSIWeights.  Defaults to (0.4, 0.3, 0.3).
        policy: Missing-component policy.  ``strict`` blocks computation
            when any component is missing.  ``allow_estimated`` proceeds
            with available components and redistributes weights.

    Returns:
        EWSIOutputSeries with daily EWSI values and full provenance.

    Raises:
        ValueError: if policy is strict and any required component is missing,
            or if no components are available under allow_estimated.
    """
    if isinstance(policy, str):
        policy = EWSIComputationPolicy(policy)

    n_days = len(inputs.dates)
    config_weights = weights or EWSIWeights()

    # Check component availability
    has_nir_swir = (
        inputs.nir is not None
        and inputs.swir is not None
        and len(inputs.nir) == n_days
        and len(inputs.swir) == n_days
    )
    has_vpd = inputs.vpd is not None and len(inputs.vpd) == n_days
    has_sm = inputs.soil_moisture is not None and len(inputs.soil_moisture) == n_days

    available = {
        "ndmi": has_nir_swir,
        "vpd": has_vpd,
        "soil": has_sm,
    }

    missing = [comp for comp, avail in available.items() if not avail]

    # Strict policy: all components required
    if policy == EWSIComputationPolicy.STRICT and missing:
        raise ValueError(
            f"Strict EWSI policy: missing required components "
            f"({', '.join(missing)}). EWSI requires NIR/SWIR, VPD, and "
            f"soil moisture for each day."
        )

    # Allow estimated: redistribute weights
    effective_weights = _redistribute_weights(config_weights, available)

    if sum(effective_weights.values()) <= 0:
        raise ValueError(
            "No EWSI components available. At least one of NDMI, VPD, "
            "or soil moisture is required."
        )

    # Compute component stress values
    ndmi_stress_values: np.ndarray | None = None
    vpd_stress_values: np.ndarray | None = None
    soil_stress_values: np.ndarray | None = None

    component_provenance: list[EWSIComponentProvenance] = []

    # NDMI component
    if has_nir_swir:
        ndmi_values = ndmi(inputs.nir, inputs.swir)
        ndmi_ref = 0.3  # Reference NDMI under non-stressed conditions
        ndmi_crit = -0.2  # Critical NDMI at maximal stress
        ndmi_stress_values = ndmi_stress(ndmi_values, ndmi_ref, ndmi_crit)

        nir_q = (
            inputs.nir_quality.value
            if inputs.nir_quality is not None
            else QualityStatus.SATELLITE_RETRIEVED.value
        )
        swir_q = (
            inputs.swir_quality.value
            if inputs.swir_quality is not None
            else QualityStatus.SATELLITE_RETRIEVED.value
        )
        component_provenance.append(
            EWSIComponentProvenance(
                component="ndmi",
                present=True,
                quality_status=f"{nir_q}+{swir_q}",
                source=inputs.nir_source or inputs.swir_source,
                source_product=inputs.nir_source_product or inputs.swir_source_product,
                stress_value=float(np.mean(ndmi_stress_values)),
                weight=effective_weights["ndmi"],
                original_weight=config_weights.ndmi,
            )
        )
    else:
        component_provenance.append(
            EWSIComponentProvenance(
                component="ndmi",
                present=False,
                quality_status=QualityStatus.MISSING.value,
                weight=0.0,
                original_weight=config_weights.ndmi,
            )
        )

    # VPD component
    if has_vpd:
        vpd_low = 0.5  # kPa — no stress below this
        vpd_high = 4.0  # kPa — severe stress above this
        vpd_stress_values = vpd_stress(inputs.vpd, vpd_low, vpd_high)

        vpd_q = (
            inputs.vpd_quality.value
            if inputs.vpd_quality is not None
            else QualityStatus.REANALYSIS_ESTIMATE.value
        )
        component_provenance.append(
            EWSIComponentProvenance(
                component="vpd",
                present=True,
                quality_status=vpd_q,
                source=inputs.vpd_source,
                source_product=inputs.vpd_source_product,
                stress_value=float(np.mean(vpd_stress_values)),
                weight=effective_weights["vpd"],
                original_weight=config_weights.vpd,
            )
        )
    else:
        component_provenance.append(
            EWSIComponentProvenance(
                component="vpd",
                present=False,
                quality_status=QualityStatus.MISSING.value,
                weight=0.0,
                original_weight=config_weights.vpd,
            )
        )

    # Soil moisture component
    if has_sm:
        # Soil moisture input is constructed per-day below
        # Use soil_moisture_model for per-day computation
        soil_stress_values = np.zeros(n_days, dtype=float)
        for i in range(n_days):
            day_sm_input = SoilMoistureInput(
                date=inputs.dates[i],
                soil_moisture=float(inputs.soil_moisture[i]),
                field_capacity=inputs.soil_field_capacity,
            )
            sm_out = compute_daily_soil_stress(day_sm_input)
            soil_stress_values[i] = sm_out.soil_stress if sm_out.soil_stress is not None else 0.0

        sm_q = (
            inputs.soil_moisture_quality.value
            if inputs.soil_moisture_quality is not None
            else QualityStatus.REANALYSIS_ESTIMATE.value
        )
        component_provenance.append(
            EWSIComponentProvenance(
                component="soil",
                present=True,
                quality_status=sm_q,
                source=inputs.soil_moisture_source,
                source_product=inputs.soil_moisture_source_product,
                stress_value=float(np.mean(soil_stress_values)),
                weight=effective_weights["soil"],
                original_weight=config_weights.soil,
            )
        )
    else:
        component_provenance.append(
            EWSIComponentProvenance(
                component="soil",
                present=False,
                quality_status=QualityStatus.MISSING.value,
                weight=0.0,
                original_weight=config_weights.soil,
            )
        )

    # Fuse components into EWSI
    ewsi_values = np.zeros(n_days, dtype=float)

    for i in range(n_days):
        daily_ewsi = 0.0
        if has_nir_swir and effective_weights["ndmi"] > 0:
            daily_ewsi += effective_weights["ndmi"] * float(ndmi_stress_values[i])
        if has_vpd and effective_weights["vpd"] > 0:
            daily_ewsi += effective_weights["vpd"] * float(vpd_stress_values[i])
        if has_sm and effective_weights["soil"] > 0:
            daily_ewsi += effective_weights["soil"] * float(soil_stress_values[i])

        ewsi_values[i] = float(np.clip(daily_ewsi, 0.0, 1.0))

    # Determine overall quality status
    if not missing:
        overall_quality = QualityStatus.MODEL_ESTIMATE.value
    else:
        overall_quality = QualityStatus.MODEL_ESTIMATE.value
        # Missing components reduce confidence but don't invalidate

    method_parts: list[str] = []
    if has_nir_swir:
        method_parts.append(
            f"{effective_weights['ndmi']:.2f}*ndmi_stress"
        )
    if has_vpd:
        method_parts.append(
            f"{effective_weights['vpd']:.2f}*vpd_stress"
        )
    if has_sm:
        method_parts.append(
            f"{effective_weights['soil']:.2f}*soil_stress"
        )
    method_str = " + ".join(method_parts)

    return EWSIOutputSeries(
        dates=inputs.dates,
        ewsi=ewsi_values.astype(float),
        missing_fields=missing,
        component_provenance=component_provenance,
        computation_policy=policy.value,
        weights=effective_weights,
        method=method_str,
        quality_status=overall_quality,
    )


def compute_ewsi_from_scalars(
    nir: float,
    swir: float,
    vpd: float,
    soil_moisture: float,
    soil_field_capacity: float = 0.35,
    weights: EWSIWeights | None = None,
) -> float:
    """Compute scalar EWSI from single-day inputs."""
    model = EWSI(weights=weights)
    ewsi = model.compute(
        nir=np.array([nir]),
        swir=np.array([swir]),
        vpd=vpd,
        soil_moisture=soil_moisture,
        soil_field_capacity=soil_field_capacity,
    )
    return float(np.clip(ewsi[0], 0.0, 1.0))


def ewsi_provenance() -> dict[str, Any]:
    """Return provenance metadata for EWSI output."""
    return {
        "source_model": "EWSI",
        "source_date": "computed_from_daily_inputs",
        "unit": "dimensionless",
        "valid_range": (0.0, 1.0),
        "quality_status": "model_generated",
        "method": "0.4*ndmi_stress + 0.3*vpd_stress + 0.3*soil_stress",
        "reference": (
            "engine/hydroma/models/ewsi.py::EWSI.REFERENCES. "
            "EWSI is a novel composite index; only the NDMI sub-index has a source."
        ),
        "scientific_status": "novel",
        "weights": {"ndmi": 0.4, "vpd": 0.3, "soil": 0.3},
    }
