"""C++ backend engine bindings for the gateway facade.

Owns the facade's engine imports from ``engine.hydroma.cpp_bridge``: the
accelerated kernels (``penman_monteith_et0``, ``rusle_annual_soil_loss``,
``ndvi_array``), the telemetry helpers and the compiled-extension capability
probe ``is_cpp_available`` inspects.

Every name imported here was previously imported directly by
``services/_gateway_facade.py``; each kernel has a documented Python fallback
in ``engine.hydroma.cpp_bridge``. A capability probe must never raise, which is
why the wrapped ``is_cpp_available`` catches both outcomes.
"""

from __future__ import annotations

from typing import Any

from engine.hydroma.cpp_bridge import (
    get_telemetry,
    ndvi_array,
    penman_monteith_et0,
    reset_telemetry,
    rusle_annual_soil_loss,
)

__all__ = [
    "backend_status",
    "get_cpp_backend_status",
    "get_telemetry",
    "is_cpp_available",
    "ndvi_array",
    "penman_monteith_et0",
    "reset_telemetry",
    "rusle_annual_soil_loss",
]


def is_cpp_available() -> bool:
    """Check if C++ backends are available."""
    try:
        from engine.hydroma.cpp_bridge import hydroma_core  # type: ignore[attr-defined]

        return True
    except (ImportError, Exception):
        return False


def get_cpp_backend_status() -> dict[str, Any]:
    """Get C++ backend status."""
    available = is_cpp_available()
    return {
        "available": available,
        "backend": "cpp" if available else "python_fallback",
    }


def backend_status() -> dict[str, Any]:
    """Get C++ backend status."""
    return get_cpp_backend_status()
