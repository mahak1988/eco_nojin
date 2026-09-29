"""Numba-accelerated vegetation index calculations.

These functions provide 10-50x speedup over pure NumPy for large satellite images.
Falls back to NumPy if Numba is not available.

Scientific references:
- NDVI: Rouse et al. 1974
- EVI: Huete et al. 2002
- SAVI: Huete 1988
- NDWI: McFeeters 1996
- NBR: Key & Benson 2006
"""

import numpy as np

# Try to import Numba; fallback gracefully
try:
    from numba import njit, prange

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    # Mock decorator for fallback
    def njit(*args, **kwargs):
        def decorator(func):
            return func

        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    prange = range


@njit(parallel=True, cache=True)
def _ndvi_fast(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Numba-optimized NDVI calculation with parallel execution."""
    rows, cols = red.shape
    result = np.empty((rows, cols), dtype=np.float64)

    for i in prange(rows):
        for j in range(cols):
            r = red[i, j]
            n = nir[i, j]
            denom = n + r
            if denom == 0:
                result[i, j] = 0.0
            else:
                val = (n - r) / denom
                # Clip to [-1, 1]
                if val > 1.0:
                    result[i, j] = 1.0
                elif val < -1.0:
                    result[i, j] = -1.0
                else:
                    result[i, j] = val

    return result


@njit(parallel=True, cache=True)
def _evi_fast(red: np.ndarray, nir: np.ndarray, blue: np.ndarray) -> np.ndarray:
    """Numba-optimized EVI calculation."""
    rows, cols = red.shape
    result = np.empty((rows, cols), dtype=np.float64)

    for i in prange(rows):
        for j in range(cols):
            r = red[i, j]
            n = nir[i, j]
            b = blue[i, j]
            denom = n + 6.0 * r - 7.5 * b + 1.0
            if denom == 0:
                result[i, j] = 0.0
            else:
                val = 2.5 * (n - r) / denom
                if val > 1.0:
                    result[i, j] = 1.0
                elif val < -1.0:
                    result[i, j] = -1.0
                else:
                    result[i, j] = val

    return result


@njit(parallel=True, cache=True)
def _savi_fast(red: np.ndarray, nir: np.ndarray, L: float) -> np.ndarray:
    """Numba-optimized SAVI calculation."""
    rows, cols = red.shape
    result = np.empty((rows, cols), dtype=np.float64)

    for i in prange(rows):
        for j in range(cols):
            r = red[i, j]
            n = nir[i, j]
            denom = n + r + L
            if denom == 0:
                result[i, j] = 0.0
            else:
                val = ((n - r) / denom) * (1.0 + L)
                if val > 1.0:
                    result[i, j] = 1.0
                elif val < -1.0:
                    result[i, j] = -1.0
                else:
                    result[i, j] = val

    return result


@njit(parallel=True, cache=True)
def _nbr_fast(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Numba-optimized NBR calculation."""
    rows, cols = nir.shape
    result = np.empty((rows, cols), dtype=np.float64)

    for i in prange(rows):
        for j in range(cols):
            n = nir[i, j]
            s = swir[i, j]
            denom = n + s
            if denom == 0:
                result[i, j] = 0.0
            else:
                val = (n - s) / denom
                if val > 1.0:
                    result[i, j] = 1.0
                elif val < -1.0:
                    result[i, j] = -1.0
                else:
                    result[i, j] = val

    return result


# ============================================================================
# Public API - uses Numba if available, NumPy otherwise
# ============================================================================


def _prepare(*arrays: np.ndarray) -> tuple[list[np.ndarray], bool]:
    """Coerce inputs to contiguous 2-D float64 for the Numba kernels.

    The kernels index ``arr[i, j]`` and unpack ``rows, cols = arr.shape``, so
    they only compile for a 2-D layout. A 1-D array -- the normal shape of a
    satellite reflectance time series -- previously raised
    ``numba.core.errors.TypingError`` at the first call.

    Returns the prepared arrays and whether the caller must flatten the result
    back to the original rank.
    """
    prepared = [np.ascontiguousarray(a, dtype=np.float64) for a in arrays]
    rank = prepared[0].ndim
    if rank == 1:
        prepared = [a.reshape(-1, 1) for a in prepared]
    elif rank != 2:
        raise ValueError(f"expected a 1-D or 2-D array, got {rank}-D")
    return prepared, rank == 1


def ndvi_fast(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Calculate NDVI with Numba acceleration.

    Falls back to NumPy if Numba is unavailable.
    Accepts 1-D (time series) or 2-D (raster) input; the output keeps the rank.
    """
    (red, nir), flatten = _prepare(red, nir)
    result = _ndvi_fast(red, nir)
    return result.reshape(-1) if flatten else result


def evi_fast(red: np.ndarray, nir: np.ndarray, blue: np.ndarray) -> np.ndarray:
    """Calculate EVI with Numba acceleration. Accepts 1-D or 2-D input."""
    (red, nir, blue), flatten = _prepare(red, nir, blue)
    result = _evi_fast(red, nir, blue)
    return result.reshape(-1) if flatten else result


def savi_fast(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
    """Calculate SAVI with Numba acceleration. Accepts 1-D or 2-D input."""
    (red, nir), flatten = _prepare(red, nir)
    result = _savi_fast(red, nir, float(L))
    return result.reshape(-1) if flatten else result


def nbr_fast(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Calculate NBR with Numba acceleration. Accepts 1-D or 2-D input."""
    (nir, swir), flatten = _prepare(nir, swir)
    result = _nbr_fast(nir, swir)
    return result.reshape(-1) if flatten else result


def is_numba_available() -> bool:
    """Check if Numba is installed and available."""
    return HAS_NUMBA
