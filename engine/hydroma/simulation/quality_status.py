"""Unified quality status vocabulary for environmental data inputs.

Provides a single source of truth for quality status labels used across
the satellite reflectance, atmospheric VPD, soil moisture, and EWSI
pipelines.  Each status carries a provenance class that distinguishes
direct observations from model-generated estimates.

Statuses:

OBSERVED           Direct field or in-situ measurement.
SATELLITE_RETRIEVED Satellite-derived product (not a ground measurement).
REANALYSIS_ESTIMATE Reanalysis / gridded modelled product (e.g. ERA5-Land).
MODEL_ESTIMATE     Output of an internal model (e.g. GDD LAI, EWSI composite).
INTERPOLATED       Value filled between observations via interpolation.
MISSING            No data available for this variable/time.
INVALID            Data present but failed quality control (out of range,
                   failed mask, negative denominator, etc.).
"""

from __future__ import annotations

from enum import StrEnum


class QualityStatus(StrEnum):
    """Quality status for any environmental input variable."""

    OBSERVED = "observed"
    SATELLITE_RETRIEVED = "satellite_retrieved"
    REANALYSIS_ESTIMATE = "reanalysis_estimate"
    MODEL_ESTIMATE = "model_estimate"
    INTERPOLATED = "interpolated"
    MISSING = "missing"
    INVALID = "invalid"


#: Statuses that represent a directly observed or retrieved measurement
#: (highest confidence).
DIRECT_STATUSES: frozenset[QualityStatus] = frozenset(
    {
        QualityStatus.OBSERVED,
        QualityStatus.SATELLITE_RETRIEVED,
    }
)

#: Statuses that represent an estimate or model output (lower confidence).
ESTIMATED_STATUSES: frozenset[QualityStatus] = frozenset(
    {
        QualityStatus.REANALYSIS_ESTIMATE,
        QualityStatus.MODEL_ESTIMATE,
        QualityStatus.INTERPOLATED,
    }
)

#: Statuses that mean no usable value exists.
ABSENT_STATUSES: frozenset[QualityStatus] = frozenset(
    {QualityStatus.MISSING, QualityStatus.INVALID}
)


def is_direct(status: QualityStatus | str) -> bool:
    """Return True if ``status`` is a direct observation or retrieval."""
    return QualityStatus(status) in DIRECT_STATUSES


def is_estimated(status: QualityStatus | str) -> bool:
    """Return True if ``status`` is an estimate or model output."""
    return QualityStatus(status) in ESTIMATED_STATUSES


def is_absent(status: QualityStatus | str) -> bool:
    """Return True if ``status`` means no usable value exists."""
    return QualityStatus(status) in ABSENT_STATUSES


def quality_rank(status: QualityStatus | str) -> int:
    """Return a confidence rank (0 = highest, 6 = lowest)."""
    order = [
        QualityStatus.OBSERVED,
        QualityStatus.SATELLITE_RETRIEVED,
        QualityStatus.REANALYSIS_ESTIMATE,
        QualityStatus.MODEL_ESTIMATE,
        QualityStatus.INTERPOLATED,
        QualityStatus.MISSING,
        QualityStatus.INVALID,
    ]
    try:
        return order.index(QualityStatus(status))
    except ValueError:
        return len(order)
