"""
Timeout and Deadline Propagation for Eco Nojin
==============================================
Provides timeout management and deadline propagation for external calls.
"""

import asyncio
import contextvars
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

from engine.hydroma.config.settings import get_settings

logger = logging.getLogger("econojin.resilience.timeout")

T = TypeVar("T")

# Context variable for deadline propagation
_deadline_var: contextvars.ContextVar[Optional[float]] = contextvars.ContextVar(
    "deadline", default=None
)


@dataclass
class TimeoutConfig:
    """Configuration for timeout policy."""
    default_timeout: float = 30.0  # seconds
    connect_timeout: float = 5.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0
    name: str = "default"


class TimeoutManager:
    """Manages timeouts and deadline propagation."""

    def __init__(self, config: TimeoutConfig):
        self.config = config
        self._local_deadline: Optional[float] = None

    @property
    def current_deadline(self) -> Optional[float]:
        """Get current deadline from context or local."""
        ctx_deadline = _deadline_var.get()
        if ctx_deadline is not None:
            return ctx_deadline
        return self._local_deadline

    def set_deadline(self, deadline: Optional[float]) -> contextvars.Token:
        """Set deadline in context variable."""
        return _deadline_var.set(deadline)

    def reset_deadline(self, token: contextvars.Token) -> None:
        """Reset deadline from context variable."""
        _deadline_var.reset(token)

    @asynccontextmanager
    async def deadline(self, timeout: Optional[float] = None):
        """Context manager for setting a deadline."""
        if timeout is None:
            timeout = self.config.default_timeout

        deadline = time.time() + timeout
        token = self.set_deadline(deadline)
        self._local_deadline = deadline
        try:
            yield deadline
        finally:
            self.reset_deadline(token)
            self._local_deadline = None

    def get_remaining_time(self) -> Optional[float]:
        """Get remaining time until deadline."""
        deadline = self.current_deadline
        if deadline is None:
            return None
        remaining = deadline - time.time()
        return max(0, remaining)

    def check_deadline(self) -> None:
        """Check if deadline has passed, raise if so."""
        remaining = self.get_remaining_time()
        if remaining is not None and remaining <= 0:
            raise TimeoutError(f"Deadline exceeded for {self.config.name}")

    async def with_timeout(self, coro, timeout: Optional[float] = None) -> Any:
        """Execute coroutine with timeout."""
        if timeout is None:
            timeout = self.config.default_timeout

        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout ({timeout}s) exceeded for {self.config.name}")
            raise TimeoutError(f"Operation timed out after {timeout}s")


# Global timeout manager
_timeout_manager: Optional[TimeoutManager] = None


def get_timeout_manager(config: Optional[TimeoutConfig] = None) -> TimeoutManager:
    """Get or create the global timeout manager."""
    global _timeout_manager
    if _timeout_manager is None:
        if config is None:
            settings = get_settings()
            config = TimeoutConfig(
                default_timeout=getattr(settings, "external_call_timeout", 30.0),
                connect_timeout=getattr(settings, "external_connect_timeout", 5.0),
                read_timeout=getattr(settings, "external_read_timeout", 30.0),
                total_timeout=getattr(settings, "external_total_timeout", 60.0),
            )
        _timeout_manager = TimeoutManager(config)
    return _timeout_manager


def get_deadline() -> Optional[float]:
    """Get current deadline from context."""
    return _deadline_var.get()


def set_deadline(deadline: Optional[float]) -> contextvars.Token:
    """Set deadline in context."""
    return _deadline_var.set(deadline)


def reset_deadline(token: contextvars.Token) -> None:
    """Reset deadline from context."""
    _deadline_var.reset(token)


@asynccontextmanager
async def deadline_context(timeout: float):
    """Context manager for setting a deadline."""
    deadline = time.time() + timeout
    token = _deadline_var.set(deadline)
    try:
        yield deadline
    finally:
        _deadline_var.reset(token)


async def with_timeout(coro, timeout: Optional[float] = None) -> Any:
    """Execute coroutine with timeout using global manager."""
    manager = get_timeout_manager()
    return await manager.with_timeout(coro, timeout)


def timeout_decorator(timeout: float):
    """Decorator to apply timeout to async function."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args, **kwargs) -> Any:
            return await with_timeout(func(*args, **kwargs), timeout)
        return wrapper
    return decorator


# Preconfigured timeouts for common services
def get_cdse_timeout() -> float:
    """Timeout for CDSE API calls."""
    settings = get_settings()
    return getattr(settings, "cdse_timeout", 30.0)


def get_nasa_power_timeout() -> float:
    """Timeout for NASA POWER API calls."""
    settings = get_settings()
    return getattr(settings, "nasa_power_timeout", 30.0)


def get_supabase_timeout() -> float:
    """Timeout for Supabase API calls."""
    settings = get_settings()
    return getattr(settings, "supabase_timeout", 30.0)


def get_blockchain_timeout() -> float:
    """Timeout for Blockchain RPC calls."""
    settings = get_settings()
    return getattr(settings, "blockchain_timeout", 60.0)


# Convenience functions
async def call_with_timeout(
    func: Callable[..., T],
    *args,
    timeout: Optional[float] = None,
    **kwargs
) -> T:
    """Call function with timeout."""
    manager = get_timeout_manager()
    async with manager.deadline(timeout):
        manager.check_deadline()
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)