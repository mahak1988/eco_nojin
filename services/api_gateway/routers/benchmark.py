"""API endpoints for performance benchmarks."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import time
import numpy as np

from engine.hydroma.cpp_bridge.indices_fast import ndvi_fast, is_numba_available

router = APIRouter(prefix="/api/v1/benchmark", tags=["Performance Benchmark"])


class BenchmarkRequest(BaseModel):
    array_size: int = Field(1000, ge=100, le=5000)
    iterations: int = Field(5, ge=1, le=50)


@router.post("/ndvi")
def run_ndvi_benchmark(payload: BenchmarkRequest):
    """Run NDVI benchmark comparing NumPy vs Numba."""
    np.random.seed(42)
    size = payload.array_size

    red = np.random.uniform(200, 1000, (size, size))
    nir = np.random.uniform(1000, 4000, (size, size))

    def ndvi_numpy(red, nir):
        with np.errstate(divide='ignore', invalid='ignore'):
            result = (nir - red) / (nir + red)
        result = np.nan_to_num(result, nan=0.0)
        return np.clip(result, -1.0, 1.0)

    # Warmup for Numba
    if is_numba_available():
        ndvi_fast(red, nir)

    # Benchmark NumPy
    numpy_times = []
    for _ in range(payload.iterations):
        start = time.perf_counter()
        ndvi_numpy(red, nir)
        numpy_times.append(time.perf_counter() - start)

    # Benchmark Numba
    numba_times = []
    for _ in range(payload.iterations):
        start = time.perf_counter()
        ndvi_fast(red, nir)
        numba_times.append(time.perf_counter() - start)

    numpy_mean = np.mean(numpy_times) * 1000
    numba_mean = np.mean(numba_times) * 1000
    speedup = numpy_mean / numba_mean if numba_mean > 0 else 0

    return {
        "array_size": size,
        "iterations": payload.iterations,
        "numpy_time_ms": round(numpy_mean, 2),
        "numba_time_ms": round(numba_mean, 2),
        "speedup": round(speedup, 2),
        "numba_available": is_numba_available(),
    }


@router.get("/status")
def benchmark_status():
    """Get benchmark system status."""
    return {
        "numba_available": is_numba_available(),
        "supported_benchmarks": ["ndvi"],
    }
