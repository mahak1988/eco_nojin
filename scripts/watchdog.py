"""Compatibility exports for the production security watchdog."""

from services.security.watchdog import CircuitBreaker, HealthWatchdog, circuit_breaker, watchdog


def analyze_samples(latencies_ms: list[float], failures: list[bool]) -> dict[str, object]:
    """Classify a bounded health sample for operational monitoring."""
    if len(latencies_ms) != len(failures) or not latencies_ms:
        raise ValueError("latencies_ms and failures must have the same non-zero length")
    if any(latency < 0 for latency in latencies_ms):
        raise ValueError("latencies_ms cannot contain negative values")
    failure_count = sum(failures)
    if failure_count == len(failures):
        status = "failing"
    elif failure_count or max(latencies_ms) >= 1000:
        status = "degraded"
    else:
        status = "ok"
    return {
        "status": status,
        "sample_count": len(latencies_ms),
        "failure_count": failure_count,
        "max_latency_ms": max(latencies_ms),
    }


__all__ = ["CircuitBreaker", "HealthWatchdog", "analyze_samples", "circuit_breaker", "watchdog"]
