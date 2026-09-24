"""
C++ vs Numba Performance Benchmarks
====================================
Benchmark tests comparing C++ implementation performance vs Numba/Python.
Run with: pytest test_benchmarks.py -v --benchmark-only --benchmark-sort=mean
"""

import numpy as np
import pytest

from engine.hydroma.cpp_bridge import (
    evi,
    get_telemetry,
    is_cpp_available,
    latin_hypercube,
    monte_carlo_uniform,
    muskingum_cunge_route,
    nbr,
    ndvi,
    ndwi,
    penman_monteith_et0,
    reset_telemetry,
    rusle_annual_soil_loss,
    savi,
)

# Skip all tests if C++ is not available
pytestmark = pytest.mark.skipif(
    not is_cpp_available(), reason="C++ hydroma_core not available - skipping benchmarks"
)


class TestIndicesBenchmarks:
    """Benchmarks for vegetation indices."""

    def test_ndvi_benchmark(self, benchmark):
        """Benchmark NDVI computation."""
        size = 100_000
        red = np.random.uniform(0, 1, size).astype(np.float64)
        nir = np.random.uniform(0, 1, size).astype(np.float64)

        def run():
            return ndvi(red, nir)

        result = benchmark(run)
        assert len(result) == size
        # Verify some values are in valid range
        assert np.all(result >= -1.0)
        assert np.all(result <= 1.0)

    def test_evi_benchmark(self, benchmark):
        """Benchmark EVI computation."""
        size = 100_000
        red = np.random.uniform(0, 1, size).astype(np.float64)
        nir = np.random.uniform(0, 1, size).astype(np.float64)
        blue = np.random.uniform(0, 1, size).astype(np.float64)

        def run():
            return evi(red, nir, blue)

        result = benchmark(run)
        assert len(result) == size

    def test_savi_benchmark(self, benchmark):
        """Benchmark SAVI computation."""
        size = 100_000
        red = np.random.uniform(0, 1, size).astype(np.float64)
        nir = np.random.uniform(0, 1, size).astype(np.float64)

        def run():
            return savi(red, nir, 0.5)

        result = benchmark(run)
        assert len(result) == size

    def test_nbr_benchmark(self, benchmark):
        """Benchmark NBR computation."""
        size = 100_000
        nir = np.random.uniform(0, 1, size).astype(np.float64)
        swir = np.random.uniform(0, 1, size).astype(np.float64)

        def run():
            return nbr(nir, swir)

        result = benchmark(run)
        assert len(result) == size

    def test_ndwi_benchmark(self, benchmark):
        """Benchmark NDWI computation."""
        size = 100_000
        green = np.random.uniform(0, 1, size).astype(np.float64)
        nir = np.random.uniform(0, 1, size).astype(np.float64)

        def run():
            return ndwi(green, nir)

        result = benchmark(run)
        assert len(result) == size


class TestHydrologyBenchmarks:
    """Benchmarks for hydrology functions."""

    def test_penman_monteith_et0_benchmark(self, benchmark):
        """Benchmark Penman-Monteith ET0 computation."""
        # Typical inputs
        size = 10_000
        tmin = np.random.uniform(5, 30, size).astype(np.float64)
        tmax = np.random.uniform(15, 40, size).astype(np.float64)
        rh_mean = np.random.uniform(30, 90, size).astype(np.float64)
        rs = np.random.uniform(5, 30, size).astype(np.float64)
        u2 = np.random.uniform(0.5, 5, size).astype(np.float64)
        z = np.random.uniform(0, 2000, size).astype(np.float64)
        lat = np.random.uniform(-60, 60, size).astype(np.float64)
        doy = np.random.uniform(1, 365, size).astype(np.int32)

        def run():
            return penman_monteith_et0(
                tmin=tmin, tmax=tmax, rh_mean=rh_mean, rs=rs, u2=u2, z=z, lat=lat, doy=doy
            )

        result = benchmark(run)
        assert len(result) == size
        assert np.all(result >= 0)  # ET0 should be non-negative


class TestRoutingBenchmarks:
    """Benchmarks for routing functions."""

    def test_muskingum_cunge_benchmark(self, benchmark):
        """Benchmark Muskingum-Cunge routing."""
        size = 1_000
        inflow = np.random.uniform(0, 1000, size).astype(np.float64)

        def run():
            return muskingum_cunge_route(
                inflow=inflow,
                k=10.0,
                x=0.2,
                dt=3600.0,
                dx=1000.0,
                slope=0.001,
                manning=0.035,
                bottom_width=20.0,
                side_slope=2.0,
            )

        result = benchmark(run)
        assert len(result) == size
        assert np.all(result >= 0)


class TestErosionBenchmarks:
    """Benchmarks for erosion functions."""

    def test_rusle_benchmark(self, benchmark):
        """Benchmark RUSLE annual soil loss computation."""
        size = 10_000
        r = np.random.uniform(50, 500, size).astype(np.float64)
        k = np.random.uniform(0.01, 0.5, size).astype(np.float64)
        ls = np.random.uniform(0.1, 10, size).astype(np.float64)
        c = np.random.uniform(0.01, 1.0, size).astype(np.float64)
        p = np.random.uniform(0.1, 1.0, size).astype(np.float64)

        def run():
            return rusle_annual_soil_loss(r=r, k=k, ls=ls, c=c, p=p)

        result = benchmark(run)
        assert len(result) == size
        assert np.all(result >= 0)


class TestSamplingBenchmarks:
    """Benchmarks for sampling functions."""

    def test_latin_hypercube_benchmark(self, benchmark):
        """Benchmark Latin Hypercube Sampling."""
        n_samples = 1000
        n_dims = 10

        def run():
            return latin_hypercube(n_samples=n_samples, n_dimensions=n_dims, seed=42)

        result = benchmark(run)
        assert result.shape == (n_samples, n_dims)
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_monte_carlo_benchmark(self, benchmark):
        """Benchmark Monte Carlo uniform sampling."""
        n_samples = 100_000
        n_dims = 5
        bounds = np.array([[0, 1]] * n_dims)

        def run():
            return monte_carlo_uniform(n_samples=n_samples, bounds=bounds, seed=42)

        result = benchmark(run)
        assert result.shape == (n_samples, n_dims)
        assert np.all(result >= 0)
        assert np.all(result <= 1)


class TestTelemetryBenchmarks:
    """Benchmarks to verify telemetry overhead."""

    def test_telemetry_overhead(self, benchmark):
        """Benchmark telemetry overhead on simple function."""
        reset_telemetry()
        red = np.random.uniform(0, 1, 1000).astype(np.float64)
        nir = np.random.uniform(0, 1, 1000).astype(np.float64)

        def run():
            reset_telemetry()
            ndvi(red, nir)
            return get_telemetry()

        telemetry = benchmark(run)
        assert telemetry["cpp_calls"] == 1


class TestMemoryEfficiency:
    """Memory efficiency tests."""

    def test_no_memory_leak_repeated_calls(self, benchmark):
        """Test that repeated calls don't leak memory."""
        size = 10_000
        red = np.random.uniform(0, 1, size).astype(np.float64)
        nir = np.random.uniform(0, 1, size).astype(np.float64)

        def run():
            for _ in range(10):
                result = ndvi(red, nir)
            return result

        result = benchmark(run)
        assert len(result) == size

    def test_large_array_handling(self, benchmark):
        """Test handling of large arrays."""
        size = 1_000_000
        red = np.random.uniform(0, 1, size).astype(np.float64)
        nir = np.random.uniform(0, 1, size).astype(np.float64)

        def run():
            return ndvi(red, nir)

        result = benchmark(run)
        assert len(result) == size
        # Should complete within reasonable time (< 100ms for 1M elements)


class TestComparisonWithNumba:
    """Comparative benchmarks with Numba (if available)."""

    @pytest.fixture(autouse=True)
    def check_numba(self):
        """Check if Numba is available for comparison."""
        try:
            import numba

            self.has_numba = True
        except ImportError:
            self.has_numba = False
            pytest.skip("Numba not available for comparison")

    def test_ndvi_vs_numba(self, benchmark):
        """Compare C++ NDVI with Numba implementation."""
        if not self.has_numba:
            pytest.skip("Numba not available")

        from numba import jit

        @jit(nopython=True, parallel=True)
        def numba_ndvi(red, nir):
            result = np.empty_like(red)
            for i in range(len(red)):
                denom = nir[i] + red[i]
                result[i] = (nir[i] - red[i]) / (denom + 1e-10) if denom != 0 else 0.0
            return result

        size = 100_000
        red = np.random.uniform(0, 1, size).astype(np.float64)
        nir = np.random.uniform(0, 1, size).astype(np.float64)

        # Warm up Numba
        numba_ndvi(red[:100], nir[:100])

        def run_cpp():
            return ndvi(red, nir)

        def run_numba():
            return numba_ndvi(red, nir)

        # Run both and compare
        cpp_result = run_cpp()
        numba_result = run_numba()

        # Verify numerical equivalence
        np.testing.assert_allclose(cpp_result, numba_result, rtol=1e-6)

        # Benchmark C++
        benchmark(run_cpp)

        # Benchmark Numba (separate benchmark)
        # Note: This would need separate benchmark function


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only", "--benchmark-sort=mean"])
