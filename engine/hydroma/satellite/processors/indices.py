"""Vegetation and water index calculations with proper clipping.

All formulas follow standard remote sensing literature with output clipping
to ensure results stay in valid ranges.
"""

import numpy as np


def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Vegetation Index (NDVI).

    Formula: (NIR - Red) / (NIR + Red)
    Range: -1 to +1 (clipped)
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (nir.astype(float) - red.astype(float)) / (nir + red)
    ndvi = np.nan_to_num(ndvi, nan=0.0)
    return np.clip(ndvi, -1.0, 1.0)


def calculate_evi(red: np.ndarray, nir: np.ndarray, blue: np.ndarray) -> np.ndarray:
    """Enhanced Vegetation Index (EVI).

    Formula: 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    Range: -1 to +1 (clipped)
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        evi = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)
    evi = np.nan_to_num(evi, nan=0.0)
    return np.clip(evi, -1.0, 1.0)


def calculate_savi(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
    """Soil Adjusted Vegetation Index (SAVI).

    Formula: (NIR - Red) / (NIR + Red + L) * (1 + L)
    Range: -1 to +1 (clipped)
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        savi = ((nir - red) / (nir + red + L)) * (1 + L)
    savi = np.nan_to_num(savi, nan=0.0)
    return np.clip(savi, -1.0, 1.0)


def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Water Index (NDWI).

    Formula: (Green - NIR) / (Green + NIR)
    Range: -1 to +1 (clipped)
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        ndwi = (green - nir) / (green + nir)
    ndwi = np.nan_to_num(ndwi, nan=0.0)
    return np.clip(ndwi, -1.0, 1.0)


def calculate_nbr(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Normalized Burn Ratio (NBR).

    Formula: (NIR - SWIR) / (NIR + SWIR)
    Range: -1 to +1 (clipped)
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        nbr = (nir - swir) / (nir + swir)
    nbr = np.nan_to_num(nbr, nan=0.0)
    return np.clip(nbr, -1.0, 1.0)


def interpret_ndvi(ndvi_value: float) -> dict:
    """Provide human-readable interpretation of NDVI value."""
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
