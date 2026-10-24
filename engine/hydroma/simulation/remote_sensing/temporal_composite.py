"""Temporal compositing and interpolation for satellite reflectance.

Handles the mismatch between satellite observation frequency (Sentinel-2:
5-day revisit at equator, less with clouds) and the daily time step required
by HYRUE.  All interpolated values are explicitly flagged as INTERPOLATED
and never labeled as SATELLITE_RETRIEVED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np


@dataclass
class CompositeResult:
    """Result of temporal compositing or interpolation.

    Attributes:
        dates: ISO date strings for each composite date.
        values: Composite values (one per date).
        source_dates: For each composite date, the nearest source observation date(s).
        method: Compositing method used ("nearest", "linear_interpolation", "none").
        interpolated_mask: Boolean array — True where value was interpolated.
        quality_status: QualityStatus for each composite date.
        max_gap_days: Maximum gap between consecutive source observations (days).
    """

    dates: list[str]
    values: np.ndarray
    source_dates: list[str | None] = field(default_factory=list)
    method: str = "none"
    interpolated_mask: list[bool] = field(default_factory=list)
    quality_status: list[str] = field(default_factory=list)
    max_gap_days: int = 0


def nearest_composite(
    source_dates: list[str],
    source_values: list[float | None],
    target_dates: list[str],
    max_gap_days: int | None = None,
) -> CompositeResult:
    """Assign each target date the value of the nearest source observation.

    Args:
        source_dates: ISO date strings of source observations.
        source_values: Values for each source date (None = missing).
        target_dates: ISO date strings of target dates (daily time step).
        max_gap_days: Maximum allowed gap between target and nearest source
            observation.  If None, no gap limit is applied.

    Returns:
        :class:`CompositeResult` with nearest-neighbor values.
    """
    source_parsed: list[tuple[date, float | None]] = []
    for d, v in zip(source_dates, source_values, strict=True):
        try:
            source_parsed.append((date.fromisoformat(d), v))
        except ValueError:
            continue

    if not source_parsed:
        return CompositeResult(
            dates=target_dates,
            values=np.full(len(target_dates), np.nan),
            source_dates=[None] * len(target_dates),
            method="nearest",
            interpolated_mask=[True] * len(target_dates),
            quality_status=["missing"] * len(target_dates),
            max_gap_days=0,
        )

    source_parsed.sort(key=lambda x: x[0])

    values: list[float] = []
    src_dates: list[str | None] = []
    interpolated: list[bool] = []
    quality: list[str] = []
    max_gap = 0

    prev_source_date: date | None = None
    for src_d, src_v in source_parsed:
        if prev_source_date is not None and src_v is not None:
            gap = (src_d - prev_source_date).days
            max_gap = max(max_gap, gap)
        if src_v is not None:
            prev_source_date = src_d

    for target_date_str in target_dates:
        target_date = date.fromisoformat(target_date_str)

        # Find nearest source observation
        best_idx = -1
        best_gap = float("inf")
        best_value = None

        for i, (src_d, src_v) in enumerate(source_parsed):
            if src_v is None:
                continue
            gap = abs((src_d - target_date).days)
            if gap < best_gap:
                best_gap = gap
                best_idx = i
                best_value = src_v

        if best_value is None:
            values.append(np.nan)
            src_dates.append(None)
            interpolated.append(True)
            quality.append("missing")
        else:
            is_interp = best_gap > 0
            values.append(best_value)
            src_dates.append(source_parsed[best_idx][0].isoformat())
            interpolated.append(is_interp)

            if max_gap_days is not None and best_gap > max_gap_days:
                quality.append("missing")
            elif is_interp:
                quality.append("interpolated")
            else:
                quality.append("satellite_retrieved")

    return CompositeResult(
        dates=target_dates,
        values=np.asarray(values, dtype=float),
        source_dates=src_dates,
        method="nearest",
        interpolated_mask=interpolated,
        quality_status=quality,
        max_gap_days=max_gap,
    )


def linear_interpolate(
    source_dates: list[str],
    source_values: list[float | None],
    target_dates: list[str],
    max_gap_days: int = 7,
) -> CompositeResult:
    """Linearly interpolate between source observations for each target date.

    Only interpolates within the range of source observations.  Target dates
    outside the observation range return NaN.  Gaps larger than max_gap_days
    between consecutive source observations result in missing values for the
    entire gap.

    Args:
        source_dates: ISO date strings of source observations.
        source_values: Values for each source date (None = missing).
        target_dates: ISO date strings of target dates (daily time step).
        max_gap_days: Maximum gap between consecutive source observations
            within which interpolation is allowed.

    Returns:
        :class:`CompositeResult` with interpolated values.
    """
    # Filter to valid (date, value) pairs
    valid: list[tuple[date, float]] = []
    for d, v in zip(source_dates, source_values, strict=True):
        if v is None:
            continue
        try:
            valid.append((date.fromisoformat(d), float(v)))
        except ValueError:
            continue

    valid.sort(key=lambda x: x[0])

    if len(valid) < 2:
        return CompositeResult(
            dates=target_dates,
            values=np.full(len(target_dates), np.nan),
            source_dates=[None] * len(target_dates),
            method="linear_interpolation",
            interpolated_mask=[True] * len(target_dates),
            quality_status=["missing"] * len(target_dates),
            max_gap_days=0,
        )

    # Check gaps between consecutive valid observations
    max_gap = 0
    gap_violations: list[tuple[date, date]] = []
    for i in range(1, len(valid)):
        gap = (valid[i][0] - valid[i - 1][0]).days
        max_gap = max(max_gap, gap)
        if gap > max_gap_days:
            gap_violations.append((valid[i - 1][0], valid[i][0]))

    dates_arr = [v[0] for v in valid]
    values_arr = np.asarray([v[1] for v in valid], dtype=float)

    values: list[float] = []
    src_dates: list[str | None] = []
    interpolated: list[bool] = []
    quality: list[str] = []

    obs_start = dates_arr[0]
    obs_end = dates_arr[-1]

    for target_date_str in target_dates:
        target_date = date.fromisoformat(target_date_str)

        # Outside observation range
        if target_date < obs_start or target_date > obs_end:
            values.append(np.nan)
            src_dates.append(None)
            interpolated.append(True)
            quality.append("missing")
            continue

        # Check if target falls in a gap that exceeds max_gap_days
        in_large_gap = False
        for gap_start, gap_end in gap_violations:
            if gap_start < target_date < gap_end:
                in_large_gap = True
                break

        if in_large_gap:
            values.append(np.nan)
            src_dates.append(None)
            interpolated.append(True)
            quality.append("missing")
            continue

        # Find surrounding observations for interpolation
        # np.interp requires ascending x
        interp_value = float(np.interp(
            target_date.toordinal(),
            [d.toordinal() for d in dates_arr],
            values_arr,
        ))

        # Find nearest source date for attribution
        nearest_idx = min(
            range(len(dates_arr)),
            key=lambda i: abs((dates_arr[i] - target_date).days),
        )
        nearest_gap = abs((dates_arr[nearest_idx] - target_date).days)

        values.append(interp_value)
        src_dates.append(dates_arr[nearest_idx].isoformat())
        interpolated.append(nearest_gap > 0)

        if nearest_gap == 0:
            quality.append("satellite_retrieved")
        else:
            quality.append("interpolated")

    return CompositeResult(
        dates=target_dates,
        values=np.asarray(values, dtype=float),
        source_dates=src_dates,
        method="linear_interpolation",
        interpolated_mask=interpolated,
        quality_status=quality,
        max_gap_days=max_gap,
    )


def daily_ewsi_from_composite(
    composite: CompositeResult,
    fill_missing_with: str = "error",
) -> tuple[np.ndarray | None, list[str]]:
    """Convert a CompositeResult into a daily array suitable for EWSI.

    Args:
        composite: :class:`CompositeResult` from nearest or linear interpolation.
        fill_missing_with: How to handle missing values.
            "error" — return None if any values are missing.
            "nan" — keep NaN values in the array.

    Returns:
        Tuple of (daily_array_or_none, warnings).
    """
    warnings: list[str] = []
    arr = composite.values

    missing_count = int(np.isnan(arr).sum())
    interpolated_count = int(sum(composite.interpolated_mask))

    if missing_count > 0:
        if fill_missing_with == "error":
            warnings.append(
                f"{missing_count} dates have missing EWSI input values "
                f"(no satellite observation within range)."
            )
            return None, warnings
        warnings.append(
            f"{missing_count} dates have NaN values (filled as NaN)."
        )

    if interpolated_count > 0:
        warnings.append(
            f"{interpolated_count} dates use interpolated values "
            f"(not direct satellite observations)."
        )

    return arr, warnings
