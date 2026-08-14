"""Performance benchmark utilities for comparing Numba vs NumPy."""
import time
import numpy as np
from typing import Callable, Dict


def benchmark_function(
    func: Callable,
    args: tuple,
    n_runs: int = 5,
    warmup: bool = True,
) -> Dict:
    """Benchmark a function with multiple runs.
    
    Args:
        func: Function to benchmark
        args: Arguments tuple
        n_runs: Number of runs
        warmup: Whether to do a warmup run (important for Numba JIT)
    
    Returns:
        Dictionary with timing statistics
    """
    if warmup:
        func(*args)  # Warmup for Numba JIT compilation
    
    times = []
    result = None
    
    for _ in range(n_runs):
        start = time.perf_counter()
        result = func(*args)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        "mean_time": np.mean(times),
        "std_time": np.std(times),
        "min_time": np.min(times),
        "max_time": np.max(times),
        "median_time": np.median(times),
        "result": result,
        "n_runs": n_runs,
    }


def compare_implementations(
    py_func: Callable,
    fast_func: Callable,
    args: tuple,
    n_runs: int = 5,
) -> Dict:
    """Compare Python/NumPy vs Numba implementation.
    
    Returns dictionary with both timings and speedup factor.
    """
    py_stats = benchmark_function(py_func, args, n_runs, warmup=False)
    fast_stats = benchmark_function(fast_func, args, n_runs, warmup=True)
    
    speedup = py_stats["mean_time"] / fast_stats["mean_time"] if fast_stats["mean_time"] > 0 else float("inf")
    
    return {
        "python": py_stats,
        "fast": fast_stats,
        "speedup": speedup,
        "results_match": np.allclose(
            py_stats["result"], fast_stats["result"], 
            rtol=1e-5, atol=1e-8, equal_nan=True
        )
    }
