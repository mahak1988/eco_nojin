"""Tests for the consolidated C++ extension loader.

``engine.hydroma.cpp_bindings`` used to load the extension a second time via
``importlib.util.spec_from_file_location`` followed by
``sys.modules["hydroma_core"] = _module``. ``cpp_bridge`` documents the exact
consequence: re-running a pybind11 module init raises
``generic_type: type "WaveParameters" is already registered!``. The two modules
were both reachable in one process, so the crash was live.

``cpp_bindings`` is now a delegation layer: ``cpp_bridge`` owns the single load.
"""

from __future__ import annotations

import sys

import engine.hydroma.cpp_bridge as bridge
import engine.hydroma.cpp_bindings as bindings


def test_both_modules_report_the_same_availability():
    assert bindings.is_cpp_available() == bridge.is_cpp_available()
    assert bindings.is_available() == bindings.is_cpp_available()


def test_both_modules_resolve_to_one_extension_object():
    """Identity, not equality: there must be a single loaded module."""
    module = sys.modules.get("hydroma_core")
    if module is None:
        return  # extension not built in this environment

    assert bindings.get_module() is bridge.get_module()
    assert bindings.get_module_or_none() is module


def test_both_modules_share_telemetry():
    """The duplicate counter dict is gone; there is one set of counters."""
    bridge.reset_telemetry()
    bindings.reset_telemetry()

    red = __import__("numpy").array([0.1, 0.2, 0.3])
    nir = __import__("numpy").array([0.5, 0.6, 0.7])
    bridge.ndvi(red, nir)

    assert bindings.get_telemetry() == bridge.get_telemetry()


def test_attribute_forwarding_reaches_the_extension():
    module = sys.modules.get("hydroma_core")
    if module is None:
        return

    for name in ("ndvi", "penman_monteith_et0", "latin_hypercube"):
        if hasattr(module, name):
            assert getattr(bindings, name) is getattr(module, name)
            break


def test_unknown_attribute_raises_import_error():
    """``from ... import X`` semantics: ImportError, not AttributeError."""
    try:
        bindings.definitely_not_a_real_symbol
    except ImportError as exc:
        assert "C++ available" in str(exc)
    else:
        raise AssertionError("expected ImportError for an unknown symbol")


def test_has_function_matches_the_extension():
    module = sys.modules.get("hydroma_core")
    if module is None:
        return

    assert bindings.has_function("ndvi") is True
    assert bindings.has_function("definitely_not_real") is False


def test_get_info_reports_backend_and_path():
    info = bindings.get_info()

    assert "available" in info
    assert "backend" in info
    assert info["python_version"].startswith("cp3")
    assert "telemetry" in info


def test_abi_blind_fallback_is_gone():
    """The old loader accepted any ABI version; there is no search left.

    Checked against the parsed AST rather than the raw text, so the docstring
    that explains the removed behaviour does not trip the assertion.
    """
    import ast

    tree = ast.parse(open(bindings.__file__, encoding="utf-8").read())

    called: set[str] = set()
    assigned: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            called.add(getattr(node.func, "attr", getattr(node.func, "id", "")))
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    assigned.append(ast.unparse(target.value))

    assert "spec_from_file_location" not in called
    assert "iterdir" not in called
    assert "CDLL" not in called
    assert not any("hydroma_core" in a for a in assigned), (
        f"module still writes to sys.modules for hydroma_core: {assigned}"
    )


def test_module_delegates_to_cpp_bridge():
    """Ownership is explicit: this module imports the owner at top level."""
    import ast

    tree = ast.parse(open(bindings.__file__, encoding="utf-8").read())
    imported: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert "engine.hydroma.cpp_bridge" in imported
