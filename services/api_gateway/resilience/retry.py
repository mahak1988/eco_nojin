"""
Retry Policy Implementation for Eco Nojin
=========================================
Provides configurable retry logic with exponential backoff and jitter.
Based on tenacity with custom configuration.
"""

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union

from engine.hydroma.config.settings import get_settings

logger = logging.getLogger("econojin.resilience.retry")

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry policy."""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1  # 10% jitter
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    stop_exceptions: Tuple[Type[Exception], ...] = ()
    before_retry: Optional[Callable[[int, Exception], None]] = None
    name: str = "default"


class RetryPolicy:
    """Retry policy with exponential backoff and jitter."""

    def __init__(self, config: RetryConfig):
        self.config = config

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter."""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        if self.config.jitter:
            # Add jitter: delay * (1 +/- jitter_factor)
            jitter_range = delay * self.config.jitter_factor
            delay = delay + random.uniform(-jitter_range, jitter_range)
        return max(0, delay)

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry policy."""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except self.config.stop_exceptions:
                # Don't retry these exceptions
                raise

            except self.config.retry_exceptions as e:
                last_exception = e

                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry policy '{self.config.name}': attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    if self.config.before_retry:
                        try:
                            self.config.before_retry(attempt + 1, e)
                        except Exception:
                            pass  # Ignore callback errors

                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Retry policy '{self.config.name}': all {self.config.max_attempts} attempts failed"
                    )
                    raise

        # Should not reach here, but just in case
        raise last_exception

    @asynccontextmanager
    async def retrying(self):
        """Context manager for manual retry control."""
        attempt = 0
        while True:
            try:
                yield attempt
                break  # Success, exit loop
            except self.config.stop_exceptions:
                raise
            except self.config.retry_exceptions as e:
                last_exception = e
                attempt += 1
                if attempt >= self.config.max_attempts:
                    logger.error(
                        f"Retry policy '{self.config.name}': all {self.config.max_attempts} attempts failed"
                    )
                    raise
                delay = self._calculate_delay(attempt - 1)
                logger.warning(
                    f"Retry policy '{self.config.name}': attempt {attempt} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                if self.config.before_retry:
                    try:
                        self.config.before_retry(attempt, e)
                    except Exception:
                        pass
                await asyncio.sleep(delay)


def create_retry_policy(
    name: str,
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    **kwargs
) -> RetryPolicy:
    """Create retry policy from settings or explicit params."""
    settings = get_settings()
    config = RetryConfig(
        name=name,
        max_attempts=max_attempts or getattr(settings, f"retry_{name}_max_attempts", 3),
        base_delay=base_delay or getattr(settings, f"retry_{name}_base_delay", 1.0),
        max_delay=max_delay or getattr(settings, f"retry_{name}_max_delay", 60.0),
        **kwargs
    )
    return RetryPolicy(config)


# Predefined retry policies for common external services
def get_cdse_retry_policy() -> RetryPolicy:
    """Retry policy for CDSE/Copernicus API calls."""
    return create_retry_policy(
        "cdse",
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        retry_exceptions=(ConnectionError, TimeoutError, IOError),
    )


def get_nasa_power_retry_policy() -> RetryPolicy:
    """Retry policy for NASA POWER API calls."""
    return create_retry_policy(
        "nasa_power",
        max_attempts=3,
        base_delay=1.0,
        max_delay=20.0,
        retry_exceptions=(ConnectionError, TimeoutError, IOError),
    )


def get_supabase_retry_policy() -> RetryPolicy:
    """Retry policy for Supabase API calls."""
    return create_retry_policy(
        "supabase",
        max_attempts=3,
        base_delay=1.0,
        max_delay=15.0,
        retry_exceptions=(ConnectionError, TimeoutError, IOError),
    )


def get_blockchain_retry_policy() -> RetryPolicy:
    """Retry policy for Blockchain RPC calls."""
    return create_retry_policy(
        "blockchain",
        max_attempts=5,
        base_delay=2.0,
        max_delay=60.0,
        retry_exceptions=(ConnectionError, TimeoutError, IOError, ValueError),
    )


def get_default_retry_policy() -> RetryPolicy:
    """Default retry policy for general external calls."""
    return create_retry_policy(
        "default",
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
    )


# Decorator for easy retry application
def with_retry(policy_name: str = "default", **policy_kwargs):
    """Decorator to apply retry policy to a function."""
    policy = create_retry_policy(policy_name, **policy_kwargs)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            return await policy.execute(func, *args, **kwargs)
        return wrapper
    return decorator


def with_cdse_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for CDSE API calls."""
    policy = get_cdse_retry_policy()
    async def wrapper(*args, **kwargs) -> T:
        return await policy.execute(func, *args, **kwargs)
    return wrapper


def get_supabase_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for Supabase API calls."""
    policy = get_supabase_retry_policy()
    async def wrapper(*args, **kwargs) -> T:
        return await policy.execute(func, *args, **kwargs)
    return wrapper


def get_blockchain_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for Blockchain RPC calls."""
    policy = get_blockchain_retry_policy()
    async def wrapper(*args, **kwargs) -> T:
        return await policy.execute(func, *args, **kwargs)
    return wrapper