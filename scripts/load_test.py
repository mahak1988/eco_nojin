"""Lightweight load test (Phase 10 — 10k-user readiness step 1).

Sends N concurrent requests to a set of endpoints and reports p50/p95/max
latency plus error count. Not a replacement for k6/Locust, but a repeatable
smoke-scale check that runs anywhere.

Usage:
  python scripts/load_test.py --workers 20 --requests 200 \
      --base http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import concurrent.futures
import statistics
import sys
import time
from typing import List, Tuple

import httpx

ENDPOINTS = [
    "/api/v1/health",
    "/api/v1/science/datasets",
    "/api/v1/science/citations/index",
    "/api/v1/models",
]


def one_request(base: str, path: str, timeout: float) -> Tuple[float, bool]:
    start = time.monotonic()
    try:
        resp = httpx.get(base + path, timeout=timeout)
        return (time.monotonic() - start) * 1000.0, resp.status_code >= 500
    except Exception:
        return timeout * 1000.0, True


def run_load_test(base: str, workers: int, requests: int, timeout: float) -> dict:
    endpoints = ENDPOINTS if base.endswith(("/api", "/api/")) is False else ENDPOINTS
    jobs = [(base, endpoints[i % len(endpoints)], timeout) for i in range(requests)]
    latencies: List[float] = []
    errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one_request, *job) for job in jobs]
        for fut in concurrent.futures.as_completed(futures):
            lat, err = fut.result()
            latencies.append(lat)
            errors += 1 if err else 0
    latencies.sort()
    n = len(latencies)
    p50 = latencies[n // 2] if n else 0.0
    p95 = latencies[int(n * 0.95) - 1] if n else 0.0
    return {
        "base": base,
        "requests": n,
        "workers": workers,
        "p50_ms": round(p50, 1),
        "p95_ms": round(p95, 1),
        "max_ms": round(latencies[-1], 1) if n else 0.0,
        "errors": errors,
        "error_ratio": round(errors / n, 4) if n else 0.0,
    }


def main() -> int:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Eco Nojin load smoke test")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.requests <= 0 or args.workers <= 0:
        print("requests and workers must be positive")
        return 2
    result = run_load_test(args.base, args.workers, args.requests, args.timeout)
    for k, v in result.items():
        print(f"{k}: {v}")
    return 0 if result["error_ratio"] < 0.01 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
