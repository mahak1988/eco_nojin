"""Python bindings loader for the Hydroma C++ engine.

The native library is `hydroma_core` located at:
  engine/cpp_core/build2/Release/hydroma_core.cp311-win_amd64.pyd

This module provides a unified interface with automatic fallback to pure Python.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any

# Try to find the library
_LIB_SEARCH_PATHS = [
    Path(__file__).parent.parent / "cpp_core" / "build2" / "Release",
    Path(__file__).parent.parent / "cpp_core" / "build" / "Release",
    Path(__file__).parent.parent / "cpp_core" / "build",
    Path(__file__).parent.parent.parent.parent / "build" / "Release",
]

_module = None
_available = False
_load_error = None


def _find_library():
    """Find the hydroma_core library matching current Python version."""
    py_ver = f"cp{sys.version_info.major}{sys.version_info.minor}"

    for search_dir in _LIB_SEARCH_PATHS:
        if not search_dir.exists():
            continue

        # First try: exact Python version match
        for f in search_dir.iterdir():
            if f.name.startswith("hydroma_core") and py_ver in f.name:
                return f

        # Fallback: any hydroma_core library
        for f in search_dir.iterdir():
            if f.name.startswith("hydroma_core") and (
                f.suffix in [".pyd", ".so", ".dylib", ".dll"]
            ):
                return f

    return None


def _load_library():
    """Load the C++ library."""
    global _module, _available, _load_error

    lib_path = _find_library()
    if lib_path is None:
        _load_error = "Library file not found"
        return False

    try:
        spec = importlib.util.spec_from_file_location("hydroma_core", str(lib_path))
        _module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_module)
        sys.modules["hydroma_core"] = _module
        _available = True
        return True
    except Exception as e:
        _load_error = str(e)
        return False


# Load on import
_load_library()


def is_available() -> bool:
    """Check if C++ backend is available."""
    return _available


def get_module():
    """Get the raw C++ module or None."""
    return _module


def get_info() -> dict:
    """Get information about the C++ backend."""
    info = {
        "available": _available,
        "python_version": f"cp{sys.version_info.major}{sys.version_info.minor}",
    }
    if _available and _module:
        funcs = [f for f in dir(_module) if not f.startswith("_")]
        info["functions_count"] = len(funcs)
        info["functions"] = funcs[:20]
        info["module_path"] = getattr(_module, "__file__", "unknown")
    else:
        info["error"] = _load_error
    return info


# Expose all C++ functions at module level
def __getattr__(name: str) -> Any:
    """Dynamically expose C++ functions as module attributes."""
    if _module is not None and hasattr(_module, name):
        return getattr(_module, name)
    raise AttributeError(
        f"module 'cpp_bindings' has no attribute '{name}'. C++ available: {_available}"
    )


# Convenience functions for common operations
if _available:
    # Direct function exports
    compute_wave_parameters = _module.compute_wave_parameters
    soil_water_content = _module.soil_water_content
    hydraulic_conductivity = _module.hydraulic_conductivity
    rusle_annual_soil_loss = _module.rusle_annual_soil_loss

    # Function existence checkers
    def has_function(name: str) -> bool:
        """Check if a C++ function is available."""
        return hasattr(_module, name)
else:
    # Fallback stubs
    def compute_wave_parameters(*args, **kwargs):
        raise RuntimeError("C++ backend not available - install hydroma_core first")

    def soil_water_content(*args, **kwargs):
        raise RuntimeError("C++ backend not available")

    def hydraulic_conductivity(*args, **kwargs):
        raise RuntimeError("C++ backend not available")

    def rusle_annual_soil_loss(*args, **kwargs):
        raise RuntimeError("C++ backend not available")

    def has_function(name: str) -> bool:
        return False
