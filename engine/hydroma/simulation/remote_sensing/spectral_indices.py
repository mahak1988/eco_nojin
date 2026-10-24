"""Spectral indices for satellite reflectance.

Computes NDMI (Normalized Difference Moisture Index) and related indices
from NIR and SWIR reflectance values.  All functions use exact zero-
denominator guards and return results clipped to physically valid ranges.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from engine.hydroma.simulation.remote_sensing.satellite_source import (
    ndmi_from_reflectance,
    validate_reflectance_range,
)


def ndmi(
    nir: np.ndarray | list[float],
    swir: np.ndarray | list[float],
) -> np.ndarray:
    """Compute Normalized Difference Moisture Index.

    NDMI = (NIR - SWIR) / (NIR + SWIR)

    Uses the same exact zero-denominator guard as
    ``engine/hydroma/models/ewsi.py::ndmi``.  Result is clipped to [-1, 1].

    Args:
        nir: NIR reflectance array (dimensionless, 0-1 typical).
        swir: SWIR reflectance array (dimensionless, 0-1 typical).

    Returns:
        NDMI array, clipped to [-1, 1].  Where NIR + SWIR == 0, output is 0.0.
    """
    return ndmi_from_reflectance(nir, swir)


def ndvi(
    nir: np.ndarray | list[float],
    red: np.ndarray | list[float],
) -> np.ndarray:
    """Compute Normalized Difference Vegetation Index.

    NDVI = (NIR - Red) / (NIR + Red)

    Args:
        nir: NIR reflectance array.
        red: Red reflectance array.

    Returns:
        NDVI array, clipped to [-1, 1].
    """
    numerator = np.asarray(nir, dtype=np.float64) - np.asarray(red, dtype=np.float64)
    denominator = np.asarray(nir, dtype=np.float64) + np.asarray(red, dtype=np.float64)
    out = np.zeros(np.broadcast_shapes(numerator.shape, denominator.shape), dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(numerator, denominator, out=out, where=(denominator != 0.0))
    return np.clip(out, -1.0, 1.0)


def ndwi(
    green: np.ndarray | list[float],
    nir: np.ndarray | list[float],
) -> np.ndarray:
    """Compute Normalized Difference Water Index (Gao 1996).

    NDWI = (Green - NIR) / (Green + NIR)

    Args:
        green: Green reflectance array.
        nir: NIR reflectance array.

    Returns:
        NDWI array, clipped to [-1, 1].
    """
    numerator = np.asarray(green, dtype=np.float64) - np.asarray(nir, dtype=np.float64)
    denominator = np.asarray(green, dtype=np.float64) + np.asarray(nir, dtype=np.float64)
    out = np.zeros(np.broadcast_shapes(numerator.shape, denominator.shape), dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(numerator, denominator, out=out, where=(denominator != 0.0))
    return np.clip(out, -1.0, 1.0)


def validate_spectral_indices(
    nir: np.ndarray,
    swir: np.ndarray,
    red: np.ndarray | None = None,
) -> dict[str, Any]:
    """Validate input arrays for spectral index computation.

    Checks:
    - All values finite
    - All values in [0, 1] reflectance range
    - Array shapes match
    - Non-empty arrays

    Args:
        nir: NIR reflectance array.
        swir: SWIR reflectance array.
        red: Optional red reflectance array (for NDVI validation).

    Returns:
        Dict with ``valid`` (bool) and ``errors`` (list of strings).
    """
    errors: list[str] = []

    nir_arr = np.asarray(nir, dtype=float)
    swir_arr = np.asarray(swir, dtype=float)

    if nir_arr.size == 0:
        errors.append("NIR array is empty")
    if swir_arr.size == 0:
        errors.append("SWIR array is empty")

    if nir_arr.shape != swir_arr.shape:
        errors.append(
            f"NIR shape {nir_arr.shape} does not match SWIR shape {swir_arr.shape}"
        )

    nir_errors = validate_reflectance_range(nir_arr, "NIR")
    swir_errors = validate_reflectance_range(swir_arr, "SWIR")
    errors.extend(nir_errors)
    errors.extend(swir_errors)

    if red is not None:
        red_arr = np.asarray(red, dtype=float)
        if red_arr.shape != nir_arr.shape:
            errors.append(
                f"Red shape {red_arr.shape} does not match NIR shape {nir_arr.shape}"
            )
        errors.extend(validate_reflectance_range(red_arr, "Red"))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "n_samples": int(nir_arr.size),
    }


def ndmi_stress(
    ndmi_values: np.ndarray | list[float],
    ndmi_ref: float,
    ndmi_crit: float,
) -> np.ndarray:
    """Convert NDMI values to a water stress index in [0, 1].

    S_NDMI = clip((NDMI_ref - NDMI_t) / (NDMI_ref - NDMI_crit), 0, 1)

    Requires NDMI_ref > NDMI_crit.  When NDMI_ref <= NDMI_crit, returns
    an array of NaN and raises ValueError.

    Args:
        ndmi_values: NDMI array (dimensionless, [-1, 1]).
        ndmi_ref: Reference NDMI under non-stressed conditions.
        ndmi_crit: Critical NDMI at which stress is maximal (1.0).

    Returns:
        Stress array in [0, 1], where 0 = no stress, 1 = severe stress.

    Raises:
        ValueError: if NDMI_ref <= NDMI_crit.
    """
    if ndmi_ref <= ndmi_crit:
        raise ValueError(
            f"NDMI_ref ({ndmi_ref}) must be greater than NDMI_crit ({ndmi_crit})"
        )

    arr = np.asarray(ndmi_values, dtype=float)
    stress = (ndmi_ref - arr) / (ndmi_ref - ndmi_crit)
    return np.clip(stress, 0.0, 1.0)
