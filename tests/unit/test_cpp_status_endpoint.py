"""Tests that the two capability endpoints agree.

``GET /health`` and ``GET /api/v1/models/cpp-status`` answer the same question
about the same native core. They used to read different loaders: ``/health`` read
the pybind11 module, while ``/cpp-status`` read a ctypes loader probing for a
``hydroma_core.dll`` that no build produced, so it always answered
``available: false``. An operator saw ``cpp_core: "ok"`` and
``available: false`` for one capability.
"""

from __future__ import annotations

from engine.hydroma.cpp_bridge import backend_status
from services.api_gateway.routers.models import cpp_status


def test_cpp_status_reports_the_same_availability_as_the_bridge():
    payload = cpp_status()

    assert payload["available"] == backend_status()["cpp_available"]
    assert payload["backend"] == backend_status()["backend"]


def test_cpp_status_no_longer_mentions_a_dll():
    """The deleted loader keyed everything on a .dll that was never built."""
    payload = cpp_status()

    assert "dll" not in payload
    assert "dll" not in str(payload).lower()


def test_cpp_status_reports_the_module_actually_in_use():
    import engine.hydroma.cpp_bridge as bridge

    payload = cpp_status()

    assert payload["module_path"] == getattr(bridge.get_module(), "__file__", None)


def test_cpp_status_exposes_dispatch_inputs():
    """Operators need the Numba state and the array threshold to read telemetry."""
    import engine.hydroma.cpp_bridge as bridge

    payload = cpp_status()

    assert payload["numba_available"] == bridge._NUMBA_AVAILABLE
    assert payload["array_cpp_threshold"] == bridge._ARRAY_CPP_THRESHOLD


def test_cpp_status_symbol_count_matches_the_module():
    import engine.hydroma.cpp_bridge as bridge

    module = bridge.get_module()
    expected = len([n for n in dir(module) if not n.startswith("_")]) if module else 0

    assert cpp_status()["symbols"] == expected


def test_health_and_cpp_status_cannot_disagree():
    """The regression: one capability, two loaders, two answers."""
    payload = cpp_status()
    state = backend_status()

    assert payload["available"] is state["cpp_available"]
    assert payload["backend"] == state["backend"]


def test_deleted_ctypes_loader_is_not_importable():
    import importlib

    try:
        importlib.import_module("services.models.cpp_bridge")
    except ModuleNotFoundError:
        pass
    else:
        raise AssertionError(
            "services.models.cpp_bridge still importable; the ctypes loader and its "
            "unbuilt DLL surface should be gone"
        )


def test_c_api_source_is_not_in_the_cmake_build():
    """c_api.cpp is removed, so no build target may still name it."""
    from pathlib import Path

    cmake = Path("engine/cpp_core/CMakeLists.txt")
    if not cmake.is_file():
        return
    text = cmake.read_text(encoding="utf-8", errors="replace")

    assert "c_api" not in text, "CMakeLists still references the removed c_api.cpp"
    assert not Path("engine/cpp_core/bindings/c_api.cpp").exists()
