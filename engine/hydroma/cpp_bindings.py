"""Python bindings loader for the Hydroma C++ engine.

This module used to be a second, independent implementation of what
``engine.hydroma.cpp_bridge`` already does. Three problems came with that:

1. **Double registration.** It called ``spec_from_file_location("hydroma_core", ...)``
   and then assigned ``sys.modules["hydroma_core"] = _module``. ``cpp_bridge``
   documents the exact failure that causes: re-executing a pybind11 module
   init raises ``generic_type: type "WaveParameters" is already registered!``.
   ``cpp_bridge`` defends with ``sys.modules.setdefault``; this module had no
   such defence, so the two of them importing in one process was a live crash
   (``orchestrator.py`` imported this one, ``simulation_env/stress.py`` the other).

2. **ABI-blind fallback.** ``_find_library`` fell back to *any* file whose name
   started with ``hydroma_core`` and had a shared-library suffix, so a
   ``cp311`` build could be handed to a 3.12 interpreter. It also had no
   ``is_file()`` guard, so a directory matched.

3. **Duplicated telemetry.** A second copy of the counters, never incremented
   anywhere, so every reported number was permanently zero.

Rather than keep two loaders in sync, this module is now a thin delegation
layer over ``cpp_bridge``, which owns the single load. The public surface is
unchanged: ``is_cpp_available``, ``is_available``, ``get_module``, ``get_info``,
``get_telemetry``, ``reset_telemetry`` and the bridged kernel names all resolve
exactly as before.
"""

from __future__ import annotations

import sys
from typing import Any

from engine.hydroma.cpp_bridge import (
    backend_status,
    get_module as get_module,
    get_telemetry as get_telemetry,
    is_cpp_available,
    reset_telemetry as reset_telemetry,
)

#: Kept for callers that used the alias.
is_available = is_cpp_available


def get_info() -> dict[str, Any]:
    """Capability report, kept compatible with the previous shape."""
    status = backend_status()
    return {
        "available": status["cpp_available"],
        "backend": status["backend"],
        "python_version": f"cp{sys.version_info.major}{sys.version_info.minor}",
        "functions_count": len(
            [n for n in dir(sys.modules.get("hydroma_core", ())) if not n.startswith("_")]
        ),
        "module_path": getattr(sys.modules.get("hydroma_core"), "__file__", "unknown"),
        "error": status["import_error"],
        "telemetry": status["telemetry"],
    }


def has_function(name: str) -> bool:
    """True when the loaded extension exposes ``name``."""
    module = sys.modules.get("hydroma_core")
    return bool(module is not None and hasattr(module, name))


def __getattr__(name: str) -> Any:
    """Forward every other attribute to the single owned extension.

    Raises ``ImportError`` (not ``AttributeError``) for unknown names so that
    ``from engine.hydroma.cpp_bindings import missing`` fails the way callers
    expect.
    """
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = sys.modules.get("hydroma_core")
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    raise ImportError(
        f"module {__name__!r} has no attribute {name!r}. C++ available: {is_cpp_available()}"
    )


def get_module_or_none() -> Any:
    """The raw extension module, or None when it is not loaded."""
    return sys.modules.get("hydroma_core")
