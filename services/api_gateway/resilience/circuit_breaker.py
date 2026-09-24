"""
Circuit Breaker Implementation for Eco Nojin
============================================
Provides circuit breaker pattern for external service calls.
Based on pybreaker with custom configuration.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from engine.hydroma.config.settings import get_settings

logger = logging.getLogger("econojin.resilience.circuit_breaker")

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation, requests go through
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    success_threshold: int = 2
    recovery_timeout: float = 30.0  # seconds
    excluded_exceptions: tuple = (asyncio.CancelledError,)
    name: str = "default"


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""

    name: str = "default"
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    last_state_change: float | None = None
    current_state: CircuitState = CircuitState.CLOSED


class CircuitBreaker:
    """
    Circuit breaker implementation with three states:
    - CLOSED: Normal operation, counting failures
    - OPEN: Short-circuiting requests, waiting for recovery_timeout
    - HALF_OPEN: Testing with limited requests before fully closing
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._lock = asyncio.Lock()
        self.stats = CircuitBreakerStats(name=config.name)

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_available(self) -> bool:
        """Check if requests should be allowed through."""
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (
                self._last_failure_time
                and time.time() - self._last_failure_time >= self.config.recovery_timeout
            ):
                return True  # Will transition to HALF_OPEN on next call
            return False
        return True  # HALF_OPEN allows test requests

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            self.stats.total_calls += 1

            if not self.is_available:
                self.stats.rejected_calls += 1
                logger.warning(f"Circuit breaker '{self.config.name}' OPEN, rejecting call")
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.config.name}' is OPEN")

            # Transition to HALF_OPEN if recovering
            if self._state == CircuitState.OPEN:
                self._transition_to_half_open()

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except self.config.excluded_exceptions:
            raise
        except Exception:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.stats.successful_calls += 1
            self.stats.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0  # Reset failure count on success

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.stats.failed_calls += 1
            self.stats.last_failure_time = time.time()
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN goes back to OPEN
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        if self._state != CircuitState.OPEN:
            self._state = CircuitState.OPEN
            self.stats.state_changes += 1
            self.stats.last_state_change = time.time()
            self.stats.current_state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.config.name}' opened after {self._failure_count} failures"
            )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        if self._state != CircuitState.HALF_OPEN:
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0
            self.stats.state_changes += 1
            self.stats.last_state_change = time.time()
            self.stats.current_state = CircuitState.HALF_OPEN
            logger.info(f"Circuit breaker '{self.config.name}' half-open, testing recovery")

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        if self._state != CircuitState.CLOSED:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self.stats.state_changes += 1
            self.stats.last_state_change = time.time()
            self.stats.current_state = CircuitState.CLOSED
            logger.info(f"Circuit breaker '{self.config.name}' closed, service recovered")

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.config.name,
            "state": self._state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "rejected_calls": self.stats.rejected_calls,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "state_changes": self.stats.state_changes,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "last_state_change": self.stats.last_state_change,
        }

    async def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self.stats.current_state = CircuitState.CLOSED
            logger.info(f"Circuit breaker '{self.config.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting calls."""

    pass


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        if config is None:
            # Load from settings
            settings = get_settings()
            cb_config = CircuitBreakerConfig(
                failure_threshold=getattr(settings, "circuit_breaker_failure_threshold", 5),
                recovery_timeout=getattr(settings, "circuit_breaker_recovery_timeout", 30.0),
                success_threshold=getattr(settings, "circuit_breaker_success_threshold", 2),
                name=name,
            )
        else:
            cb_config = config
        _circuit_breakers[name] = CircuitBreaker(cb_config)
    return _circuit_breakers[name]


async def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers."""
    for cb in _circuit_breakers.values():
        await cb.reset()


def get_all_circuit_breaker_stats() -> dict[str, dict]:
    """Get statistics for all circuit breakers."""
    return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}
