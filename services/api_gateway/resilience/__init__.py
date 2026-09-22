"""
Resilience Package for Eco Nojin
================================
Circuit Breaker, Retry Policy, and Timeout Management.
"""

from __future__ import annotations

from services.api_gateway.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    get_circuit_breaker,
    get_all_circuit_breaker_stats,
    reset_all_circuit_breakers,
)

from services.api_gateway.resilience.retry import (
    RetryPolicy,
    RetryConfig,
    create_retry_policy,
    get_cdse_retry_policy,
    get_nasa_power_retry_policy,
    get_supabase_retry_policy,
    get_blockchain_retry_policy,
    get_default_retry_policy,
    with_retry,
    with_cdse_retry,
)

from services.api_gateway.resilience.timeout import (
    TimeoutManager,
    TimeoutConfig,
    get_timeout_manager,
    get_deadline,
    set_deadline,
    reset_deadline,
    deadline_context,
    with_timeout,
    get_cdse_timeout,
    get_nasa_power_timeout,
    get_supabase_timeout,
    get_blockchain_timeout,
    call_with_timeout,
    timeout_decorator,
)

# Unified resilience decorator
def with_resilience(
    service_name: str,
    circuit_breaker: bool = True,
    retry: bool = True,
    timeout: bool = True,
    fallback: Optional[Callable] = None,
):
    """
    Unified decorator applying circuit breaker, retry, and timeout.

    Args:
        service_name: Name of the external service (e.g., "cdse", "supabase", "blockchain")
        circuit_breaker: Enable circuit breaker
        retry: Enable retry policy
        timeout: Enable timeout
        fallback: Optional fallback function when all resilience mechanisms fail
    """
    def decorator(func: Callable) -> Callable:
        # Get resilience components for this service
        cb = get_circuit_breaker(service_name) if circuit_breaker else None
        retry_policy = create_retry_policy(service_name) if retry else None
        timeout_mgr = get_timeout_manager() if timeout else None

        async def wrapper(*args, **kwargs):
            # Apply timeout
            if timeout_mgr:
                async with timeout_mgr.deadline():
                    return await _execute_with_resilience(
                        func, args, kwargs, cb, retry_policy, fallback
                    )
            else:
                return await _execute_with_resilience(
                    func, args, kwargs, cb, retry_policy, fallback
                )

        return wrapper

    return decorator


async def _execute_with_resilience(
    func: Callable,
    args: tuple,
    kwargs: dict,
    circuit_breaker: Optional[CircuitBreaker],
    retry_policy: Optional[RetryPolicy],
    fallback: Optional[Callable],
) -> Any:
    """Execute function with circuit breaker and retry."""
    async def _call():
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    # Apply circuit breaker
    if circuit_breaker:
        try:
            return await circuit_breaker.call(_call)
        except CircuitBreakerOpenError:
            if fallback:
                logger.warning(f"Circuit breaker open for {func.__name__}, using fallback")
                return await fallback(*args, **kwargs)
            raise

    # Apply retry policy
    if retry_policy:
        return await retry_policy.execute(_call)

    # No resilience, direct call
    return await _call()


# Import for use in _execute_with_resilience
import asyncio
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("econojin.resilience")


__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitState",
    "get_circuit_breaker",
    "get_all_circuit_breaker_stats",
    "reset_all_circuit_breakers",
    # Retry
    "RetryPolicy",
    "RetryConfig",
    "create_retry_policy",
    "get_cdse_retry_policy",
    "get_nasa_power_retry_policy",
    "get_supabase_retry_policy",
    "get_blockchain_retry_policy",
    "get_default_retry_policy",
    "with_retry",
    "with_cdse_retry",
    # Timeout
    "TimeoutManager",
    "TimeoutConfig",
    "get_timeout_manager",
    "get_deadline",
    "set_deadline",
    "reset_deadline",
    "deadline_context",
    "with_timeout",
    "get_cdse_timeout",
    "get_nasa_power_timeout",
    "get_supabase_timeout",
    "get_blockchain_timeout",
    "call_with_timeout",
    "timeout_decorator",
    # Unified
    "with_resilience",
]