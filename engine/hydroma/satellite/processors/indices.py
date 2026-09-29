"""Vegetation and water index calculations with proper clipping.

All formulas follow standard remote sensing literature with output clipping
to ensure results stay in valid ranges.

The equations here duplicate ``engine/cpp_bridge`` (NumPy and C++ kernels). This
module is the satellite-ingest path, which is why it is separate, but the
expressions must be identical: the previous version differed in two ways that
both changed the numbers.

* ``calculate_ndvi`` cast the numerator to float and left the denominator in the
  input dtype. For a ``uint16`` raw-DN input the denominator wrapped at 65535 and
  the result was wrong. The other functions had the same problem in reverse --
  no cast at all.
* None of the functions applied the zero-denominator guard the native kernels use
  (``denominator == 0.0``); they relied on ``nan_to_num(..., nan=0.0)``, which is
  also applied to *infinite* results and to the NaN that a cloud mask writes.
  Cloud pixels became 0.0, and ``interpret_ndvi(0.0)`` classifies as bare soil, so
  a cloudy scene produced an agronomic recommendation about bare ground.

``nan_to_num`` is kept only for the case where a caller genuinely has no better
option, and it no longer hides an infinity.
"""

import numpy as np


def _safe_ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Divide element-wise, returning 0.0 where the denominator is exactly zero.

    Mirrors ``safe_ratio`` in engine/cpp_core/src/indices.cpp. Inputs are promoted
    to float64 first so an integer band cannot overflow the sum.
    """
    num = np.asarray(numerator, dtype=np.float64)
    den = np.asarray(denominator, dtype=np.float64)
    out = np.zeros(np.broadcast_shapes(num.shape, den.shape), dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(num, den, out=out, where=(den != 0.0))
    return out


def _clip(values: np.ndarray) -> np.ndarray:
    """Clip to [-1, 1], matching the native kernels."""
    return np.clip(values, -1.0, 1.0)


def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Vegetation Index (NDVI).

    Formula: (NIR - Red) / (NIR + Red)
    Range: -1 to +1 (clipped)
    """
    return _clip(_safe_ratio(nir - red, nir + red))


def calculate_evi(red: np.ndarray, nir: np.ndarray, blue: np.ndarray) -> np.ndarray:
    """Enhanced Vegetation Index (EVI).

    Formula: 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    Range: -1 to +1 (clipped)
    """
    return _clip(2.5 * _safe_ratio(nir - red, nir + 6 * red - 7.5 * blue + 1))


def calculate_savi(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
    """Soil Adjusted Vegetation Index (SAVI).

    Formula: (NIR - Red) / (NIR + Red + L) * (1 + L)
    Range: -1 to +1 (clipped)
    """
    return _clip(_safe_ratio((nir - red) * (1 + L), nir + red + L))


def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Water Index (NDWI).

    Formula: (Green - NIR) / (Green + NIR)
    Range: -1 to +1 (clipped)
    """
    return _clip(_safe_ratio(green - nir, green + nir))


def calculate_nbr(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Normalized Burn Ratio (NBR).

    Formula: (NIR - SWIR) / (NIR + SWIR)
    Range: -1 to +1 (clipped)
    """
    return _clip(_safe_ratio(nir - swir, nir + swir))


def interpret_ndvi(ndvi_value: float) -> dict:
    """Human-readable interpretation of an NDVI value.

    ``None`` means the value was not measured, and is reported as such rather
    than falling through the comparisons -- every comparison against ``None`` is
    False, so an unmeasured value would otherwise be reported as
    "non-vegetated, water, cloud, or invalid pixel", which asserts a reading that
    was never taken.
    """
    if ndvi_value is None:
        return {
            "class": "unknown",
            "description": "NDVI not measured (no usable pixels or no scene available)",
        }
    if ndvi_value != ndvi_value:  # NaN
        return {"class": "unknown", "description": "NDVI not available"}

    if ndvi_value < 0:
        return {"class": "non-vegetated", "description": "Water, cloud, or invalid pixel"}
    elif ndvi_value < 0.1:
        return {"class": "bare_soil", "description": "Bare soil, rock, or snow"}
    elif ndvi_value < 0.2:
        return {"class": "sparse", "description": "Sparse vegetation or stressed plants"}
    elif ndvi_value < 0.4:
        return {"class": "moderate", "description": "Moderate vegetation (grassland, shrubs)"}
    elif ndvi_value < 0.6:
        return {"class": "dense", "description": "Dense vegetation (healthy crops)"}
    else:
        return {"class": "very_dense", "description": "Very dense vegetation (forest)"}


def calculate_all_indices(
    red: np.ndarray,
    nir: np.ndarray,
    blue: np.ndarray | None = None,
    swir: np.ndarray | None = None,
    green: np.ndarray | None = None,
    L: float = 0.5,
) -> dict[str, np.ndarray]:
    """Compute whichever indices the supplied bands allow.

    A band that is not supplied is not faked. Callers that previously relied on
    ``nan_to_num`` to paper over a missing band got a plausible-looking number
    from a band that was never measured.
    """
    out: dict[str, np.ndarray] = {
        "ndvi": calculate_ndvi(red, nir),
        "savi": calculate_savi(red, nir, L),
    }
    if blue is not None:
        out["evi"] = calculate_evi(red, nir, blue)
    if swir is not None:
        out["nbr"] = calculate_nbr(nir, swir)
    if green is not None:
        out["ndwi"] = calculate_ndwi(green, nir)
    return out
