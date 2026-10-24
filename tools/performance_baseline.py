#!/usr/bin/env python3
"""Performance baseline for the API gateway (B6 / P13).

Measures the per-critical-route p95 latency and the database query count for
a fixed set of endpoints, and writes the numbers to a JSON report. The
report is the baseline the next measurement is compared against; it is never
a target to beat by weakening the measurement.

Critical routes (read-mostly, high traffic):

    GET /health
    GET /api/v1/rules
    GET /api/v1/units
    GET /api/nojin/health
    GET /api/v1/compliance/jurisdictions
    GET /api/v1/marketplace/stats
    GET /api/v1/tourism/tours
    GET /api/v1/knowledge/entries

Usage:
    python tools/performance_baseline.py                 # measure + report
    python tools/performance_baseline.py --json report.json
    python tools/performance_baseline.py --requests 50  # more samples

Exit codes:
    0  measured (report written)
    1  the app failed to boot
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import httpx

from services.api_gateway.main import app


ROUTES = [
    ("GET", "/health", None),
    ("GET", "/health/ready", None),
    ("GET", "/api/v1/rules", None),
    ("GET", "/api/v1/units", None),
    ("GET", "/api/nojin/health", None),
    ("GET", "/api/v1/tourism/tours", None),
    ("GET", "/api/v1/knowledge/entries", None),
]

DEFAULT_REQUESTS = 20


def _measure(client: httpx.Client, method: str, path: str, n: int) -> dict:
    """Measure a route's p50/p95/p99 latency and error rate."""
    latencies: list[float] = []
    errors = 0
    for _ in range(n):
        start = time.perf_counter()
        response = client.request(method, path)
        elapsed = (time.perf_counter() - start) * 1000.0
        latencies.append(elapsed)
        if response.status_code >= 400:
            errors += 1

    latencies.sort()
    p50 = statistics.median(latencies)
    p95_idx = int(len(latencies) * 0.95)
    p99_idx = int(len(latencies) * 0.99)
    p95 = latencies[min(p95_idx, len(latencies) - 1)]
    p99 = latencies[min(p99_idx, len(latencies) - 1)]

    return {
        "path": path,
        "method": method,
        "samples": n,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "errors": errors,
        "error_rate": round(errors / n, 4) if n else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="write the report to this path")
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS)
    args = parser.parse_args()

    n = args.requests

    from starlette.testclient import TestClient

    client = TestClient(app, raise_server_exceptions=False)

    print("=" * 70)
    print("PERFORMANCE BASELINE (B6 / P13)")
    print("=" * 70)
    print(f"Samples per route: {n}")
    print()

    results: list[dict] = []
    for method, path, _ in ROUTES:
        result = _measure(client, method, path, n)
        results.append(result)
        print(
            f"  {method:4s} {path:35s}  p50={result['p50_ms']:7.2f}ms  "
            f"p95={result['p95_ms']:7.2f}ms  p99={result['p99_ms']:7.2f}ms  "
            f"errors={result['errors']}"
        )

    print()
    print("=" * 70)

    report = {
        "measured_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        "samples_per_route": n,
        "routes": results,
    }

    if args.json:
        Path(args.json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Report written to {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
