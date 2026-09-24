"""
engine
======

Processing engine for Eco Nojin project.

Submodules:
    - data_connector: Unified data access for processing engines
    - safe_math: Safe mathematical operations with NaN/Overflow protection
    - resilience: Circuit breakers, timeouts, retries

Usage:
    from engine.data_connector import connector
    from engine.safe_math import safe_sqrt, safe_log, nan_guard
    from engine.resilience import circuit_breaker, with_timeout

Author: Eco Nojin Architecture Team
Version: 2.0.0
"""

from .data_connector import DataConnector, connector
from .memory_monitor import (
    MemoryManager,
    MemoryTracker,
    memory_monitor,
    monitor_memory,
    track_memory,
)
from .resilience import (
    CircuitBreaker,
    CircuitOpenError,
    circuit_breaker,
    get_circuit_breaker,
    with_retry,
    with_timeout,
)
from .resource_manager import (
    cleanup_resources,
    get_memory_usage_mb,
    managed_connection,
    managed_session,
)
from .safe_math import (
    nan_guard,
    safe_divide,
    safe_exp,
    safe_log,
    safe_power,
    safe_sqrt,
    validate_numeric,
    with_safe_math,
)

__all__ = [
    "CircuitBreaker",
    "CircuitOpenError",
    # DataConnector
    "DataConnector",
    "MemoryManager",
    # Memory Monitoring
    "MemoryTracker",
    # Resilience
    "circuit_breaker",
    "cleanup_resources",
    "connector",
    "get_circuit_breaker",
    "get_memory_usage_mb",
    # Resource Management
    "managed_connection",
    "managed_session",
    "memory_monitor",
    "monitor_memory",
    "nan_guard",
    "safe_divide",
    "safe_exp",
    "safe_log",
    "safe_power",
    # Safe Math
    "safe_sqrt",
    "track_memory",
    "validate_numeric",
    "with_retry",
    "with_safe_math",
    "with_timeout",
]

__version__ = "2.0.0"
