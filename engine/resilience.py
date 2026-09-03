#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.resilience
=================

Resilience patterns for Eco Nojin services.

Implements:
    - Circuit Breaker (for external service calls)
    - Timeout enforcement
    - Retry with backoff
    - Bulkhead (resource isolation)

Usage:
    from engine.resilience import circuit_breaker, with_timeout

    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    def call_external_api():
        # ... external call
        return result

    @with_timeout(5.0)
    def slow_operation():
        # ... slow operation
        return result

Author: Eco Nojin Architecture Team
Version: 2.0.0
"""

import time
import threading
import asyncio
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Protects against cascading failures by:
    - Monitoring failure rate
    - Opening circuit when threshold exceeded
    - Allowing recovery after cooldown period
    - Testing with half-open state

    Args:
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds to wait before half-open
        success_threshold: Successes needed in half-open to close
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state (may transition from OPEN to HALF_OPEN)."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
            return self._state

    def allow_request(self) -> bool:
        """Check if request should be allowed."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            return True
        else:  # OPEN
            return False

    def record_success(self):
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"Circuit '{self.name}' CLOSED (recovered)")
            else:
                self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit '{self.name}' re-OPENED (test failed)")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit '{self.name}' OPENED after {self._failure_count} failures"
                )

    def reset(self):
        """Reset circuit to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0

    def __repr__(self):
        return (
            f"CircuitBreaker(name={self.name!r}, state={self.state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold})"
        )


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name.

    Args:
        name: Unique name for the circuit breaker
        failure_threshold: Failures before opening
        recovery_timeout: Seconds before half-open
        success_threshold: Successes to close from half-open

    Returns:
        CircuitBreaker instance
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                name=name,
            )
        return _circuit_breakers[name]


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to wrap a function with circuit breaker protection.

    Args:
        name: Circuit breaker name (default: function name)
        failure_threshold: Failures before opening
        recovery_timeout: Seconds before half-open
        success_threshold: Successes to close from half-open
        fallback: Function to call when circuit is open

    Usage:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        def call_external_service():
            # ...
            return result

        @circuit_breaker(fallback=lambda *args: None)
        def call_with_fallback():
            # ...
    """
    def decorator(func):
        cb_name = name or f"{func.__module__}.{func.__name__}"
        breaker = get_circuit_breaker(
            cb_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not breaker.allow_request():
                if fallback is not None:
                    return fallback(*args, **kwargs)
                raise CircuitOpenError(
                    f"Circuit '{cb_name}' is open, request rejected"
                )

            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise

        wrapper.circuit_breaker = breaker
        return wrapper
    return decorator


def with_timeout(timeout_seconds: float, fallback: Any = None):
    """
    Decorator to enforce a timeout on a function.

    Args:
        timeout_seconds: Maximum execution time
        fallback: Value to return on timeout (raises TimeoutError if None)

    Usage:
        @with_timeout(5.0, fallback=None)
        def slow_operation():
            time.sleep(10)  # Would timeout
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout_seconds)
                except FuturesTimeout:
                    logger.warning(
                        f"Timeout after {timeout_seconds}s in {func.__name__}"
                    )
                    if fallback is not None:
                        return fallback
                    raise TimeoutError(
                        f"Function {func.__name__} exceeded {timeout_seconds}s"
                    )
        return wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    fallback: Any = None,
):
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        backoff_factor: Multiplier for backoff time
        exceptions: Exception types to catch
        fallback: Value to return after all retries fail

    Usage:
        @with_retry(max_retries=3, backoff_factor=2.0)
        def flaky_operation():
            # ... might fail
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for "
                            f"{func.__name__} in {wait_time:.2f}s: {e}"
                        )
                        time.sleep(wait_time)

            if fallback is not None:
                return fallback
            raise last_exception
        return wrapper
    return decorator


def get_all_breakers() -> dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    with _registry_lock:
        return dict(_circuit_breakers)


def reset_all_breakers():
    """Reset all circuit breakers to closed state."""
    with _registry_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()


__all__ = [
    "CircuitState",
    "CircuitOpenError",
    "CircuitBreaker",
    "circuit_breaker",
    "with_timeout",
    "with_retry",
    "get_circuit_breaker",
    "get_all_breakers",
    "reset_all_breakers",
]
