"""Soil moisture model for EWSI computation.

Provides soil water stress computation from volumetric soil moisture and
field capacity / wilting point parameters.  Supports both absolute soil
moisture stress and relative soil moisture anomaly (when field capacity
and wilting point are unavailable).

No pedotransfer function parameters are hard-coded as facts.  If FC and WP
are unavailable, the model falls back to a relative anomaly index clearly
labeled as such.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from engine.hydroma.simulation.quality_status import QualityStatus


@dataclass
class SoilMoistureInput:
    """Daily soil moisture inputs.

    Attributes:
        date: ISO date string.
        soil_moisture: Volumetric soil moisture in m³/m³.
        soil_layer_top_cm: Top depth of the soil layer (cm).
        soil_layer_bottom_cm: Bottom depth of the soil layer (cm).
        field_capacity: Volumetric water content at field capacity (m³/m³).
        wilting_point: Volumetric water content at wilting point (m³/m³).
        source: Data source label (e.g. "ERA5-Land", "Copernicus SWI").
        source_product: Product identifier.
        quality_status: QualityStatus of the input data.
    """

    date: str
    soil_moisture: float
    soil_layer_top_cm: float = 0.0
    soil_layer_bottom_cm: float = 0.0
    field_capacity: float | None = None
    wilting_point: float | None = None
    source: str = ""
    source_product: str = ""
    quality_status: QualityStatus = QualityStatus.REANALYSIS_ESTIMATE


@dataclass
class SoilMoistureOutput:
    """Daily soil moisture stress output.

    Attributes:
        date: ISO date string.
        soil_moisture: Input volumetric soil moisture (m³/m³).
        soil_layer_top_cm: Top depth of layer (cm).
        soil_layer_bottom_cm: Bottom depth of layer (cm).
        field_capacity: Field capacity (m³/m³) or None.
        wilting_point: Wilting point (m³/m³) or None.
        soil_stress: Soil water stress in [0, 1] (None if computed via anomaly).
        relative_anomaly: Relative soil moisture anomaly (None if FC/WP available).
        method: "field_capacity" or "relative_anomaly".
        source: Data source label.
        source_product: Product identifier.
        quality_status: QualityStatus of the output.
    """

    date: str
    soil_moisture: float
    soil_layer_top_cm: float
    soil_layer_bottom_cm: float
    field_capacity: float | None
    wilting_point: float | None
    soil_stress: float | None
    relative_anomaly: float | None
    method: str
    source: str = ""
    source_product: str = ""
    quality_status: QualityStatus = QualityStatus.REANALYSIS_ESTIMATE


def validate_soil_moisture(
    soil_moisture: float,
    field_capacity: float | None = None,
    wilting_point: float | None = None,
) -> list[str]:
    """Validate soil moisture and optional soil parameters.

    Args:
        soil_moisture: Volumetric soil moisture in m³/m³.
        field_capacity: Optional field capacity in m³/m³.
        wilting_point: Optional wilting point in m³/m³.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []

    if not math.isfinite(soil_moisture):
        errors.append(f"Soil moisture {soil_moisture} is not finite")
    elif soil_moisture < 0.0 or soil_moisture > 0.6:
        errors.append(
            f"Soil moisture {soil_moisture} outside valid range [0, 0.6] m³/m³"
        )

    if field_capacity is not None:
        if not math.isfinite(field_capacity) or field_capacity <= 0:
            errors.append(
                f"Field capacity {field_capacity} must be > 0"
            )
        elif field_capacity > 0.6:
            errors.append(
                f"Field capacity {field_capacity} outside [0, 0.6] m³/m³"
            )

    if wilting_point is not None:
        if not math.isfinite(wilting_point) or wilting_point < 0:
            errors.append(
                f"Wilting point {wilting_point} must be >= 0"
            )
        elif wilting_point > 0.6:
            errors.append(
                f"Wilting point {wilting_point} outside [0, 0.6] m³/m³"
            )

    if field_capacity is not None and wilting_point is not None:
        if wilting_point >= field_capacity:
            errors.append(
                f"Wilting point ({wilting_point}) must be < field capacity ({field_capacity})"
            )

    return errors


def soil_stress_from_field_capacity(
    soil_moisture: float,
    field_capacity: float,
) -> float:
    """Compute soil water stress from field capacity ratio.

    S_soil = clip(1 - theta / FC, 0, 1)

    Interpretation:
    - S_soil = 0: soil moisture at or above field capacity (no stress)
    - S_soil = 1: soil moisture at or below zero (severe stress)

    Note: This uses FC as the denominator, not (FC - WP).  When wilting
    point is available, use :func:`soil_stress_from_fc_wp` instead.

    Args:
        soil_moisture: Volumetric soil moisture in m³/m³.
        field_capacity: Field capacity in m³/m³ (> 0).

    Returns:
        Soil stress in [0, 1].

    Raises:
        ValueError: if field_capacity <= 0.
    """
    if field_capacity <= 0:
        raise ValueError(
            f"Field capacity {field_capacity} must be > 0"
        )
    stress = 1.0 - (soil_moisture / field_capacity)
    return float(np.clip(stress, 0.0, 1.0))


def soil_stress_from_fc_wp(
    soil_moisture: float,
    field_capacity: float,
    wilting_point: float,
) -> float:
    """Compute soil water stress using field capacity and wilting point.

    S_soil = clip((FC - theta) / (FC - WP), 0, 1)

    Interpretation:
    - S_soil = 0: theta >= FC (at or above field capacity)
    - S_soil = 1: theta <= WP (at or below wilting point)

    Args:
        soil_moisture: Volumetric soil moisture in m³/m³.
        field_capacity: Field capacity in m³/m³.
        wilting_point: Wilting point in m³/m³.

    Returns:
        Soil stress in [0, 1].

    Raises:
        ValueError: if FC <= WP or FC <= 0.
    """
    errors = validate_soil_moisture(
        soil_moisture, field_capacity, wilting_point
    )
    if errors:
        raise ValueError("; ".join(errors))

    if field_capacity <= wilting_point:
        raise ValueError(
            f"Field capacity ({field_capacity}) must be > wilting point ({wilting_point})"
        )

    stress = (field_capacity - soil_moisture) / (field_capacity - wilting_point)
    return float(np.clip(stress, 0.0, 1.0))


def relative_soil_moisture_anomaly(
    soil_moisture: float,
    reference_median: float,
) -> float:
    """Compute relative soil moisture anomaly.

    SM_anomaly = theta_t - median(theta_reference)

    This is a RELATIVE index, NOT a direct measure of plant water stress.
    It must not be clipped to [0, 1] and presented as stress without
    a documented conversion function.

    Args:
        soil_moisture: Current volumetric soil moisture (m³/m³).
        reference_median: Median reference soil moisture (m³/m³).

    Returns:
        Anomaly value (positive = wetter than reference, negative = drier).
    """
    return float(soil_moisture - reference_median)


def anomaly_to_stress_index(
    anomaly: float,
    anomaly_scale: float,
) -> float:
    """Convert a relative soil moisture anomaly to a [0, 1] stress index.

    S_anomaly = clip(-anomaly / anomaly_scale, 0, 1)

    Negative anomaly (drier than reference) -> positive stress.
    Positive anomaly (wetter than reference) -> zero stress.

    Args:
        anomaly: Relative soil moisture anomaly (m³/m³).
        anomaly_scale: Scale parameter converting anomaly to stress (m³/m³).
            Must be > 0.

    Returns:
        Stress index in [0, 1].

    Raises:
        ValueError: if anomaly_scale <= 0.
    """
    if anomaly_scale <= 0:
        raise ValueError(
            f"anomaly_scale {anomaly_scale} must be > 0"
        )
    stress = -anomaly / anomaly_scale
    return float(np.clip(stress, 0.0, 1.0))


def compute_daily_soil_stress(
    inputs: SoilMoistureInput,
    reference_median: float | None = None,
    anomaly_scale: float | None = None,
) -> SoilMoistureOutput:
    """Compute daily soil moisture stress from inputs.

    Priority:
    1. If field_capacity is provided, use FC-based stress.
    2. Else if both field_capacity and wilting_point are provided, use FC-WP method.
    3. Else if reference_median and anomaly_scale are provided, use anomaly method.
    4. Else, raise ValueError (no valid method available).

    Args:
        inputs: :class:`SoilMoistureInput` with soil moisture data.
        reference_median: Optional reference median for anomaly method.
        anomaly_scale: Optional scale for anomaly-to-stress conversion.

    Returns:
        :class:`SoilMoistureOutput` with computed stress.

    Raises:
        ValueError: if no valid computation method is available, or if
            soil moisture validation fails.
    """
    errors = validate_soil_moisture(
        inputs.soil_moisture,
        inputs.field_capacity,
        inputs.wilting_point,
    )
    if errors:
        raise ValueError("; ".join(errors))

    date_str = inputs.date

    # Method 1: FC-WP (preferred when both available)
    if inputs.field_capacity is not None and inputs.wilting_point is not None:
        stress = soil_stress_from_fc_wp(
            inputs.soil_moisture,
            inputs.field_capacity,
            inputs.wilting_point,
        )
        return SoilMoistureOutput(
            date=date_str,
            soil_moisture=inputs.soil_moisture,
            soil_layer_top_cm=inputs.soil_layer_top_cm,
            soil_layer_bottom_cm=inputs.soil_layer_bottom_cm,
            field_capacity=inputs.field_capacity,
            wilting_point=inputs.wilting_point,
            soil_stress=stress,
            relative_anomaly=None,
            method="field_capacity_wilting_point",
            source=inputs.source,
            source_product=inputs.source_product,
            quality_status=inputs.quality_status,
        )

    # Method 2: FC only
    if inputs.field_capacity is not None:
        stress = soil_stress_from_field_capacity(
            inputs.soil_moisture,
            inputs.field_capacity,
        )
        return SoilMoistureOutput(
            date=date_str,
            soil_moisture=inputs.soil_moisture,
            soil_layer_top_cm=inputs.soil_layer_top_cm,
            soil_layer_bottom_cm=inputs.soil_layer_bottom_cm,
            field_capacity=inputs.field_capacity,
            wilting_point=inputs.wilting_point,
            soil_stress=stress,
            relative_anomaly=None,
            method="field_capacity",
            source=inputs.source,
            source_product=inputs.source_product,
            quality_status=inputs.quality_status,
        )

    # Method 3: relative anomaly
    if reference_median is not None and anomaly_scale is not None:
        anomaly = relative_soil_moisture_anomaly(
            inputs.soil_moisture, reference_median
        )
        stress = anomaly_to_stress_index(anomaly, anomaly_scale)
        return SoilMoistureOutput(
            date=date_str,
            soil_moisture=inputs.soil_moisture,
            soil_layer_top_cm=inputs.soil_layer_top_cm,
            soil_layer_bottom_cm=inputs.soil_layer_bottom_cm,
            field_capacity=None,
            wilting_point=None,
            soil_stress=stress,
            relative_anomaly=anomaly,
            method="relative_anomaly",
            source=inputs.source,
            source_product=inputs.source_product,
            quality_status=inputs.quality_status,
        )

    raise ValueError(
        "Cannot compute soil stress: no field_capacity, wilting_point, "
        "or anomaly reference/scale provided."
    )


def root_zone_weighted_moisture(
    layer_moistures: list[float],
    layer_top_cms: list[float],
    layer_bottom_cms: list[float],
    root_zone_top_cm: float = 0.0,
    root_zone_bottom_cm: float = 30.0,
) -> float:
    """Compute root-zone weighted average soil moisture.

    Weights each layer by its overlap with the root zone.  Layers entirely
    outside the root zone receive zero weight.

    Args:
        layer_moistures: Volumetric soil moisture for each layer (m³/m³).
        layer_top_cms: Top depth of each layer (cm).
        layer_bottom_cms: Bottom depth of each layer (cm).
        root_zone_top_cm: Top of root zone (cm).
        root_zone_bottom_cm: Bottom of root zone (cm).

    Returns:
        Root-zone weighted average soil moisture (m³/m³).

    Raises:
        ValueError: if input lists are mismatched or empty.
    """
    n = len(layer_moistures)
    if n == 0:
        raise ValueError("layer_moistures must not be empty")
    if len(layer_top_cms) != n or len(layer_bottom_cms) != n:
        raise ValueError(
            "layer_moistures, layer_top_cms, layer_bottom_cms must have same length"
        )

    total_weight = 0.0
    weighted_sum = 0.0

    for moisture, top, bottom in zip(layer_moistures, layer_top_cms, layer_bottom_cms, strict=True):
        # Compute overlap between [top, bottom] and [root_zone_top, root_zone_bottom]
        overlap_top = max(top, root_zone_top_cm)
        overlap_bottom = min(bottom, root_zone_bottom_cm)
        overlap = max(0.0, overlap_bottom - overlap_top)
        layer_thickness = max(0.0, bottom - top)

        if layer_thickness > 0 and overlap > 0:
            weight = overlap / layer_thickness
            weighted_sum += moisture * weight
            total_weight += weight

    if total_weight == 0:
        raise ValueError(
            "No layers overlap with the root zone "
            f"[{root_zone_top_cm}, {root_zone_bottom_cm}] cm"
        )

    return float(weighted_sum / total_weight)
