"""Circuit breaker for resilience against failures and attacks.

Provides protection against:
- Thread pool saturation
- Slowloris attacks
- Cascading failures
- Resource exhaustion

Usage:
    from services.reliability.circuit_breaker import circuit_breaker

    @circuit_breaker(failure_threshold=5, timeout=60.0)
    def critical_operation():
        ...
"""

import threading
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Tripped due to failures
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Thread-safe circuit breaker with configurable thresholds.

    Prevents cascading failures by "breaking" the circuit when
    failure rate exceeds threshold, allowing time for recovery.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception_types: tuple = (Exception,),
        failure_count: int = 0,
        last_failure_time: float = 0.0,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception_types = expected_exception_types

        self._state = CircuitState.CLOSED
        self._failure_count = failure_count
        self._last_failure_time = last_failure_time
        self._lock = threading.RLock()

    def _now(self) -> float:
        return time.time()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failure_count

    def _on_success(self) -> None:
        """Reset failure count on success."""
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED

    def _on_failure(self, exc: Exception) -> None:
        """Handle failure."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = self._now()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for circuit breaker."""

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            if self._state == CircuitState.OPEN:
                if self._now() - self._last_failure_time < self.timeout:
                    raise TimeoutError(
                        f"Circuit breaker is OPEN. Half-open timeout: {self.timeout}s remaining."
                    )
                self._state = CircuitState.HALF_OPEN

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception_types as e:
                self._on_failure(e)
                raise

        return wrapper


# Global circuit breakers for critical services
hydroma_circuit = CircuitBreaker(
    failure_threshold=3,
    timeout=30.0,
    expected_exception_types=(TimeoutError, OSError, ConnectionError, RuntimeError),
)

database_circuit = CircuitBreaker(
    failure_threshold=5,
    timeout=60.0,
    expected_exception_types=(TimeoutError, ConnectionError, OSError),
)


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 60.0,
    expected_exception_types: tuple = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Factory function for custom circuit breakers.

    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting half-open state
        expected_exception_types: Tuple of exceptions that count as failures

    Returns:
        Decorator function
    """
    return CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        expected_exception_types=expected_exception_types,
    )


__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "circuit_breaker",
    "database_circuit",
    "hydroma_circuit",
]
