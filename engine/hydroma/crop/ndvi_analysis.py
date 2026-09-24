"""NDVI and vegetation index analysis."""

from __future__ import annotations


def calculate_ndvi(red: float, nir: float) -> float:
    """Calculate NDVI from red and NIR bands.

    Parameters
    ----------
    red:
        Red band reflectance.
    nir:
        Near-infrared band reflectance.

    Returns
    -------
    float
        NDVI value in range [-1, 1].
    """
    try:
        from engine.hydroma.wrapper import compute_ndvi

        return compute_ndvi(red, nir)
    except Exception:
        if (nir + red) > 0:
            return (nir - red) / (nir + red)
        return 0.0


def calculate_evi(red: float, nir: float, blue: float) -> float:
    """Calculate EVI from red, NIR and blue bands."""
    try:
        from engine.hydroma.wrapper import compute_evi

        return compute_evi(red, nir, blue)
    except Exception:
        g, c1, c2, l = 2.5, 6.0, 7.5, 1.0
        denominator = nir + c1 * red - c2 * blue + l
        if denominator > 0:
            return g * (nir - red) / denominator
        return 0.0
