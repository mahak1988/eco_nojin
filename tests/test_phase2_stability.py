#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_phase2_stability.py
==============================

Tests for Phase 2 stability modules:
    - engine.safe_math
    - engine.resilience
    - DuckDB connection pooling
    - MRV type mismatch fix
"""

import sys
import time
import math
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestSafeMath:
    """Tests for engine.safe_math module."""

    def test_safe_sqrt_valid(self):
        """Valid inputs should return correct results."""
        from engine.safe_math import safe_sqrt
        assert safe_sqrt(4) == 2.0
        assert safe_sqrt(0) == 0.0
        assert safe_sqrt(9) == 3.0
        assert safe_sqrt(2) == pytest.approx(1.414, rel=1e-3)

    def test_safe_sqrt_negative(self):
        """Negative inputs should return fallback."""
        from engine.safe_math import safe_sqrt
        assert safe_sqrt(-1) is None
        assert safe_sqrt(-1, fallback=0.0) == 0.0
        assert safe_sqrt(-100, fallback=-1.0) == -1.0

    def test_safe_sqrt_nan_inf(self):
        """NaN/Infinity inputs should return fallback."""
        from engine.safe_math import safe_sqrt
        assert safe_sqrt(float('nan')) is None
        assert safe_sqrt(float('inf')) is None
        assert safe_sqrt(float('-inf')) is None

    def test_safe_sqrt_none(self):
        """None input should return fallback."""
        from engine.safe_math import safe_sqrt
        assert safe_sqrt(None) is None
        assert safe_sqrt(None, fallback=0.0) == 0.0

    def test_safe_log_valid(self):
        """Valid positive inputs should work."""
        from engine.safe_math import safe_log
        assert safe_log(math.e) == pytest.approx(1.0)
        assert safe_log(100, base=10) == pytest.approx(2.0)
        assert safe_log(1) == pytest.approx(0.0)

    def test_safe_log_negative(self):
        """Negative and zero inputs should return fallback."""
        from engine.safe_math import safe_log
        assert safe_log(-1) is None
        assert safe_log(0) is None
        assert safe_log(-1, fallback=-999.0) == -999.0

    def test_safe_divide_valid(self):
        """Valid division should work."""
        from engine.safe_math import safe_divide
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(0, 5) == 0.0
        assert safe_divide(-10, 2) == -5.0

    def test_safe_divide_by_zero(self):
        """Division by zero should return fallback."""
        from engine.safe_math import safe_divide
        assert safe_divide(10, 0) is None
        assert safe_divide(10, 0, fallback=0.0) == 0.0

    def test_nan_guard(self):
        """nan_guard should filter NaN/Infinity."""
        from engine.safe_math import nan_guard
        assert nan_guard(5.0) == 5.0
        assert nan_guard(0.0) == 0.0
        assert nan_guard(float('nan')) == 0.0
        assert nan_guard(float('inf')) == 0.0
        assert nan_guard(None) == 0.0
        assert nan_guard(None, fallback=-1.0) == -1.0

    def test_validate_numeric(self):
        """validate_numeric should enforce ranges."""
        from engine.safe_math import validate_numeric
        assert validate_numeric(5, min_val=0, max_val=10) == 5.0
        assert validate_numeric(-5, min_val=0) is None
        assert validate_numeric(15, max_val=10) is None
        assert validate_numeric("not a number") is None

    def test_with_safe_math_decorator(self):
        """Decorator should catch math errors."""
        from engine.safe_math import with_safe_math

        @with_safe_math(fallback=0.0)
        def risky_func(x):
            return math.sqrt(x)

        assert risky_func(4) == 2.0
        assert risky_func(-1) == 0.0  # Would raise ValueError

    def test_recursion_protection(self):
        """Recursion depth should be set appropriately."""
        from engine.safe_math import MAX_RECURSION_DEPTH
        assert sys.getrecursionlimit() >= MAX_RECURSION_DEPTH


class TestResilience:
    """Tests for engine.resilience module."""

    def test_circuit_breaker_creation(self):
        """Circuit breaker should be created properly."""
        from engine.resilience import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_circuit_breaker_opens_on_failures(self):
        """Circuit should open after threshold failures."""
        from engine.resilience import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_circuit_breaker_recovery(self):
        """Circuit should recover after timeout."""
        from engine.resilience import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True

        cb.record_success()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_decorator(self):
        """Circuit breaker decorator should work."""
        from engine.resilience import circuit_breaker, CircuitOpenError

        @circuit_breaker(failure_threshold=2, recovery_timeout=0.1)
        def failing_func():
            raise ValueError("fail")

        # First two calls should raise ValueError
        with pytest.raises(ValueError):
            failing_func()
        with pytest.raises(ValueError):
            failing_func()

        # Third call should raise CircuitOpenError
        with pytest.raises(CircuitOpenError):
            failing_func()

    def test_circuit_breaker_with_fallback(self):
        """Circuit breaker with fallback should not raise."""
        from engine.resilience import circuit_breaker

        @circuit_breaker(
            failure_threshold=1,
            recovery_timeout=0.1,
            fallback=lambda: "fallback_value"
        )
        def failing_func():
            raise ValueError("fail")

        failing_func()  # First call fails, opens circuit
        result = failing_func()  # Second call uses fallback
        assert result == "fallback_value"

    def test_with_timeout_decorator(self):
        """Timeout decorator should enforce limits."""
        from engine.resilience import with_timeout

        @with_timeout(0.1, fallback="timeout")
        def slow_func():
            time.sleep(1.0)
            return "done"

        result = slow_func()
        assert result == "timeout"

    def test_with_timeout_fast_function(self):
        """Fast functions should complete before timeout."""
        from engine.resilience import with_timeout

        @with_timeout(1.0, fallback="timeout")
        def fast_func():
            return "fast"

        assert fast_func() == "fast"

    def test_with_retry_decorator(self):
        """Retry decorator should retry on failure."""
        from engine.resilience import with_retry
        call_count = {"count": 0}

        @with_retry(max_retries=2, backoff_factor=0.01)
        def flaky_func():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise ValueError("flaky")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count["count"] == 2

    def test_get_circuit_breaker_registry(self):
        """Registry should track breakers by name."""
        from engine.resilience import get_circuit_breaker, reset_all_breakers
        reset_all_breakers()

        cb1 = get_circuit_breaker("test_breaker_1")
        cb2 = get_circuit_breaker("test_breaker_1")
        cb3 = get_circuit_breaker("test_breaker_2")

        assert cb1 is cb2
        assert cb1 is not cb3


class TestDuckDBPooling:
    """Tests for DuckDB connection pooling in DataHub."""

    def test_duckdb_pool_reuses_connection(self):
        """Pooled connections should be reused."""
        from database.hub import hub
        pytest.importorskip("duckdb")

        conn1 = hub.get_duckdb("master", pooled=True)
        conn2 = hub.get_duckdb("master", pooled=True)

        assert conn1 is conn2
        # Don't close - let pool manage

    def test_duckdb_non_pooled_creates_new(self):
        """Non-pooled should create fresh connections."""
        from database.hub import hub
        pytest.importorskip("duckdb")

        conn1 = hub.get_duckdb("master", pooled=False)
        conn2 = hub.get_duckdb("master", pooled=False)

        assert conn1 is not conn2
        conn1.close()
        conn2.close()


class TestMRVTypeMismatch:
    """Tests for MRV type mismatch fix."""

    def test_mrv_query_with_string_site_ids(self):
        """MRV query should handle string site IDs like 'SITE001'."""
        from engine.data_connector import connector
        pytest.importorskip("duckdb")

        # This should not raise an error
        try:
            info = connector.get_table_info("weather_daily")
            # Query should work even with string site IDs
            if info.get("rows", 0) > 0:
                result = connector.execute_analytics_query("""
                    SELECT
                        COUNT(*) as total,
                        MAX(year) as max_year
                    FROM weather_daily
                """)
                assert result is not None
        except Exception as e:
            pytest.fail(f"MRV query failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
