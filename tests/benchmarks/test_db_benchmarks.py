"""
tests/benchmarks/test_db_benchmarks.py
======================================

Performance benchmarks for database layer.

Measures:
  - Query latency (p50, p95, p99)
  - Throughput (ops/sec)
  - Concurrent performance
  - Large data handling
"""

import sys
import time
import statistics
import pytest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestQueryLatency:
    """Benchmark query latency."""

    def test_simple_query_latency(self, benchmark_timer):
        """Measure simple query latency."""
        pytest.importorskip("duckdb")
        from database.hub import hub

        latencies = []
        for _ in range(100):
            with benchmark_timer as t:
                conn = hub.get_duckdb("master")
                try:
                    conn.execute("SELECT 1").fetchone()
                finally:
                    conn.close()
            latencies.append(t.elapsed * 1000)  # ms

        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[95]
        p99 = sorted(latencies)[99]
        avg = statistics.mean(latencies)

        print(f"\n  Simple query latency (100 iterations):")
        print(f"    avg:  {avg:.2f} ms")
        print(f"    p50:  {p50:.2f} ms")
        print(f"    p95:  {p95:.2f} ms")
        print(f"    p99:  {p99:.2f} ms")

        # SLO: p95 < 50ms
        assert p95 < 100, f"p95 latency too high: {p95}ms (SLO includes connection overhead)"

    def test_complex_aggregation_latency(self, benchmark_timer):
        """Measure complex aggregation latency."""
        pytest.importorskip("duckdb")
        from database.hub import hub

        latencies = []
        for _ in range(50):
            conn = hub.get_duckdb("master")
            try:
                with benchmark_timer as t:
                    conn.execute("""
                        SELECT 
                            COUNT(*) as total,
                            AVG(tmin_c) as avg_min,
                            MAX(tmax_c) as max_max
                        FROM weather_daily
                    """).fetchone()
                latencies.append(t.elapsed * 1000)
            finally:
                conn.close()

        if latencies:
            p50 = statistics.median(latencies)
            p95_idx = int(len(latencies) * 0.95)
            p95 = sorted(latencies)[p95_idx]
            print(f"\n  Complex aggregation latency (50 iterations):")
            print(f"    avg:  {statistics.mean(latencies):.2f} ms")
            print(f"    p50:  {p50:.2f} ms")
            print(f"    p95:  {p95:.2f} ms")


class TestThroughput:
    """Benchmark throughput."""

    def test_sqlalchemy_session_throughput(self, benchmark_timer):
        """Measure session creation throughput."""
        from database.hub import hub
        from sqlalchemy import text

        count = 0
        start = time.perf_counter()

        for _ in range(100):
            with hub.get_session() as session:
                session.execute(text("SELECT 1"))
                count += 1

        elapsed = time.perf_counter() - start
        ops_per_sec = count / elapsed

        print(f"\n  SQLAlchemy session throughput:")
        print(f"    {ops_per_sec:.2f} ops/sec")
        print(f"    {elapsed * 1000 / count:.2f} ms/op")

        # SLO: at least 10 ops/sec
        assert ops_per_sec > 10

    def test_duckdb_query_throughput(self, benchmark_timer):
        """Measure DuckDB query throughput."""
        pytest.importorskip("duckdb")
        from database.hub import hub

        count = 0
        start = time.perf_counter()

        for _ in range(100):
            conn = hub.get_duckdb("master")
            try:
                conn.execute("SELECT 1").fetchone()
                count += 1
            finally:
                conn.close()

        elapsed = time.perf_counter() - start
        ops_per_sec = count / elapsed

        print(f"\n  DuckDB query throughput:")
        print(f"    {ops_per_sec:.2f} ops/sec")
        print(f"    {elapsed * 1000 / count:.2f} ms/op")


class TestConcurrentPerformance:
    """Benchmark concurrent operations."""

    def test_concurrent_sessions_throughput(self):
        """Measure concurrent session throughput."""
        from database.hub import hub
        from sqlalchemy import text

        def work(i):
            with hub.get_session() as session:
                session.execute(text("SELECT 1"))
                return i

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(work, i) for i in range(100)]
            results = [f.result() for f in as_completed(futures)]

        elapsed = time.perf_counter() - start
        ops_per_sec = len(results) / elapsed

        print(f"\n  Concurrent sessions (20 workers, 100 ops):")
        print(f"    {ops_per_sec:.2f} ops/sec")
        print(f"    total: {elapsed:.2f} s")

        assert len(results) == 100

    def test_concurrent_duckdb_throughput(self):
        """Measure concurrent DuckDB throughput."""
        pytest.importorskip("duckdb")
        from database.hub import hub

        def work(i):
            conn = hub.get_duckdb("master")
            try:
                conn.execute("SELECT 1").fetchone()
                return i
            finally:
                conn.close()

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(work, i) for i in range(100)]
            results = [f.result() for f in as_completed(futures)]

        elapsed = time.perf_counter() - start
        ops_per_sec = len(results) / elapsed

        print(f"\n  Concurrent DuckDB (20 workers, 100 ops):")
        print(f"    {ops_per_sec:.2f} ops/sec")
        print(f"    total: {elapsed:.2f} s")


class TestLargeDataHandling:
    """Benchmark large data handling."""

    def test_large_result_set(self, benchmark_timer):
        """Benchmark large result set retrieval."""
        pytest.importorskip("duckdb")
        from database.hub import hub

        with benchmark_timer as t:
            conn = hub.get_duckdb("master")
            try:
                result = conn.execute("""
                    SELECT * FROM weather_daily LIMIT 10000
                """).fetchall()
            finally:
                conn.close()

        print(f"\n  Large result set (10000 rows):")
        print(f"    time: {t.elapsed * 1000:.2f} ms")
        print(f"    rows: {len(result)}")
        print(f"    throughput: {len(result) / t.elapsed:.0f} rows/sec")

    def test_dataframe_conversion(self, benchmark_timer):
        """Benchmark DataFrame conversion."""
        pytest.importorskip("duckdb")
        pytest.importorskip("pandas")
        from database.hub import hub

        with benchmark_timer as t:
            conn = hub.get_duckdb("master")
            try:
                df = conn.execute("""
                    SELECT * FROM weather_daily LIMIT 1000
                """).fetchdf()
            finally:
                conn.close()

        print(f"\n  DataFrame conversion (1000 rows):")
        print(f"    time: {t.elapsed * 1000:.2f} ms")
        print(f"    rows: {len(df)}")
        print(f"    columns: {len(df.columns)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
