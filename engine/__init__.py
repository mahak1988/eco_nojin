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
from .safe_math import (
    safe_sqrt,
    safe_log,
    safe_divide,
    safe_exp,
    safe_power,
    nan_guard,
    validate_numeric,
    with_safe_math,
)
from .resilience import (
    circuit_breaker,
    with_timeout,
    with_retry,
    CircuitBreaker,
    CircuitOpenError,
    get_circuit_breaker,
)

__all__ = [
    # DataConnector
    "DataConnector",
    "connector",
    # Safe Math
    "safe_sqrt",
    "safe_log",
    "safe_divide",
    "safe_exp",
    "safe_power",
    "nan_guard",
    "validate_numeric",
    "with_safe_math",
    # Resilience
    "circuit_breaker",
    "with_timeout",
    "with_retry",
    "CircuitBreaker",
    "CircuitOpenError",
    "get_circuit_breaker",
]

__version__ = "2.0.0"
