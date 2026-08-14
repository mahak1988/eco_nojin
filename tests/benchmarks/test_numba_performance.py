"""Performance tests comparing Numba vs NumPy.

These tests verify that Numba implementations are actually faster
and produce equivalent results.
"""
import numpy as np
import pytest

from engine.hydroma.cpp_bridge.indices_fast import ndvi_fast, is_numba_available
from engine.hydroma.performance.benchmarks import compare_implementations


def ndvi_numpy(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Pure NumPy NDVI for comparison."""
    with np.errstate(divide='ignore', invalid='ignore'):
        result = (nir - red) / (nir + red)
    result = np.nan_to_num(result, nan=0.0)
    return np.clip(result, -1.0, 1.0)


@pytest.mark.skipif(not is_numba_available(), reason="Numba not available")
def test_ndvi_performance_large_array():
    """Verify Numba is faster than NumPy for large arrays.
    
    Uses 2000x2000 array (4 million pixels, typical Sentinel-2 tile).
    """
    np.random.seed(42)
    size = 2000
    red = np.random.uniform(200, 1000, (size, size))
    nir = np.random.uniform(1000, 4000, (size, size))
    
    comparison = compare_implementations(
        ndvi_numpy,
        ndvi_fast,
        args=(red, nir),
        n_runs=3,
    )
    
    # Verify results match
    assert comparison["results_match"], "Numba and NumPy results should match"
    
    # Verify Numba is faster (with reasonable threshold)
    speedup = comparison["speedup"]
    print(f"\nNDVI Benchmark ({size}x{size}):")
    print(f"  NumPy:  {comparison['python']['mean_time']*1000:.2f} ms")
    print(f"  Numba:  {comparison['fast']['mean_time']*1000:.2f} ms")
    print(f"  Speedup: {speedup:.2f}x")
    
    # Should be at least 2x faster (conservative due to CI variability)
    assert speedup > 2.0, f"Expected at least 2x speedup, got {speedup:.2f}x"


@pytest.mark.skipif(not is_numba_available(), reason="Numba not available")
def test_ndvi_performance_small_array():
    """Benchmark on smaller arrays (overhead is more visible)."""
    np.random.seed(42)
    size = 200
    red = np.random.uniform(200, 1000, (size, size))
    nir = np.random.uniform(1000, 4000, (size, size))
    
    comparison = compare_implementations(
        ndvi_numpy,
        ndvi_fast,
        args=(red, nir),
        n_runs=5,
    )
    
    assert comparison["results_match"]
    
    print(f"\nNDVI Benchmark ({size}x{size}):")
    print(f"  NumPy:  {comparison['python']['mean_time']*1000:.3f} ms")
    print(f"  Numba:  {comparison['fast']['mean_time']*1000:.3f} ms")
    print(f"  Speedup: {comparison['speedup']:.2f}x")
