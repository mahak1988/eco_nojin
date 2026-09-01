"""Performance benchmarks"""
import structlog

logger = structlog.get_logger()
import pytest, time, statistics

class TestPerformance:
    @pytest.mark.benchmark
    def test_numpy_speed(self):
        import numpy as np
        t0 = time.perf_counter()
        for _ in range(100): np.random.rand(100,100)
        t1 = time.perf_counter()
        logger.info(f"\n  Time: {(t1-t0)*1000:.2f}ms")
        assert (t1-t0) < 10  # should be fast

    def test_dict_operations(self):
        t0 = time.perf_counter()
        for _ in range(1000): d={i:i*2 for i in range(500)}
        t1 = time.perf_counter()
        logger.info(f"\n  Dict Time: {(t1-t0)*1000:.2f}ms")
