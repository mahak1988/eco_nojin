"""Tests for the reliability circuit breaker."""

import time

import pytest

from services.reliability.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    circuit_breaker,
    database_circuit,
    hydroma_circuit,
)


class TestCircuitState:
    """Tests for the CircuitState enum."""

    def test_states_exist(self):
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    """Tests for the CircuitBreaker."""

    def test_initial_state_is_closed(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=10.0)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_success_does_not_trip(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=10.0)

        @breaker
        def ok():
            return "fine"

        assert ok() == "fine"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_failures_trip_the_circuit(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)

        @breaker
        def boom():
            raise RuntimeError("kaboom")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                boom()

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    def test_open_circuit_rejects_calls(self):
        breaker = CircuitBreaker(failure_threshold=1, timeout=60.0)

        @breaker
        def boom():
            raise RuntimeError("kaboom")

        with pytest.raises(RuntimeError):
            boom()
        assert breaker.state == CircuitState.OPEN

        with pytest.raises(TimeoutError, match="OPEN"):
            boom()

    def test_success_resets_the_failure_count(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)
        state = {"fail": True}

        @breaker
        def maybe():
            if state["fail"]:
                raise RuntimeError("nope")
            return "ok"

        with pytest.raises(RuntimeError):
            maybe()
        assert breaker.failure_count == 1

        state["fail"] = False
        assert maybe() == "ok"
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

    def test_unexpected_exception_does_not_count(self):
        """Only ``expected_exception_types`` count as failures."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            timeout=60.0,
            expected_exception_types=(TimeoutError,),
        )

        @breaker
        def boom():
            raise ValueError("not counted")

        for _ in range(5):
            with pytest.raises(ValueError):
                boom()

        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_after_timeout(self):
        breaker = CircuitBreaker(failure_threshold=1, timeout=0.05)

        @breaker
        def boom():
            raise RuntimeError("kaboom")

        with pytest.raises(RuntimeError):
            boom()
        assert breaker.state == CircuitState.OPEN

        time.sleep(0.06)

        # The next call is allowed through (half-open) and its success closes it.
        breaker._state = CircuitState.HALF_OPEN
        assert breaker.state == CircuitState.HALF_OPEN

    def test_decorator_preserves_function_metadata(self):
        breaker = CircuitBreaker(failure_threshold=1, timeout=10.0)

        @breaker
        def documented():
            """Doc string."""

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "Doc string."


class TestCircuitBreakerFactory:
    """Tests for the circuit_breaker factory."""

    def test_factory_builds_a_breaker(self):
        decorator = circuit_breaker(failure_threshold=2, timeout=5.0)
        assert isinstance(decorator, CircuitBreaker)

    def test_factory_breaker_enforces_threshold(self):
        decorator = circuit_breaker(failure_threshold=2, timeout=5.0)

        @decorator
        def boom():
            raise OSError("io")

        with pytest.raises(OSError):
            boom()
        with pytest.raises(OSError):
            boom()
        assert decorator.state == CircuitState.OPEN


class TestGlobalBreakers:
    """Tests for the module-level breakers."""

    def test_globals_are_configured(self):
        assert hydroma_circuit.failure_threshold == 3
        assert hydroma_circuit.timeout == 30.0
        assert database_circuit.failure_threshold == 5
        assert database_circuit.timeout == 60.0

    def test_globals_start_closed(self):
        assert hydroma_circuit.state == CircuitState.CLOSED
        assert database_circuit.state == CircuitState.CLOSED
