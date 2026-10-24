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

Note: the submodules are resolved lazily via ``__getattr__``.  Importing them
eagerly here meant that ``engine`` was still initialising while a deep
``engine.hydroma.*`` import was running, which made
``from engine.hydroma.<pkg>.<mod> import <name>`` fail depending on import
order.  Lazy resolution removes the re-entrancy.
"""

from __future__ import annotations

import importlib
from typing import Any

#: Public name -> submodule that defines it.
_EXPORTS: dict[str, str] = {
    "DataConnector": "data_connector",
    "connector": "data_connector",
    "MemoryManager": "memory_monitor",
    "MemoryTracker": "memory_monitor",
    "memory_monitor": "memory_monitor",
    "monitor_memory": "memory_monitor",
    "track_memory": "memory_monitor",
    "CircuitBreaker": "resilience",
    "CircuitOpenError": "resilience",
    "circuit_breaker": "resilience",
    "get_circuit_breaker": "resilience",
    "with_retry": "resilience",
    "with_timeout": "resilience",
    "cleanup_resources": "resource_manager",
    "get_memory_usage_mb": "resource_manager",
    "managed_connection": "resource_manager",
    "managed_session": "resource_manager",
    "nan_guard": "safe_math",
    "safe_divide": "safe_math",
    "safe_exp": "safe_math",
    "safe_log": "safe_math",
    "safe_power": "safe_math",
    "safe_sqrt": "safe_math",
    "validate_numeric": "safe_math",
    "with_safe_math": "safe_math",
}

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


def __getattr__(name: str) -> Any:
    """Resolve a public name by importing its defining submodule on demand."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))
