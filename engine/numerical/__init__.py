"""Numerical — a navigable mirror of the spec §3.1 chain (re-export layer).

What this package is
--------------------
``engine/numerical`` is the spec §3.1 *numerical kernels* node. Today it is a
re-export layer: nothing here computes. The tier has two halves and only one
of them is Python, which is why this shim is a probe plus a re-export rather
than a flat list of kernels.

Module migration happens later, behind a mandate: A-4 step 2 migrates families
into this package one at a time, each behind a parity test. Nothing here has
started that migration.

The TODAY-correct modules mirrored here
---------------------------------------
* ``engine/cpp_core`` — the native kernels themselves (``src/*.cpp`` plus the
  build scripts). It is a C++ *source tree with no Python module surface*, so
  there is nothing to re-export from it and this shim does not pretend
  otherwise: :func:`cpp_core_capabilities` is the capability probe, and it
  reports what is actually reachable instead of inventing a kernel list.
* ``engine/hydroma/cpp_bridge`` — the owned Python door onto those kernels. It
  loads the compiled ``hydroma_core`` extension and falls back to pure Python
  when the extension is absent, so it is the only honest way to reach the
  numerical tier. It is re-exported below as ``cpp_bridge``.

The import is guarded on purpose: when the bridge cannot be imported this
package still imports and exposes a documented placeholder that raises
``NotImplementedError``, so ``import engine.numerical`` never breaks a chain
that only needed the navigation. ``__all__`` says which of the two states is
live.
"""

from __future__ import annotations

from typing import Any

try:
    from engine.hydroma import cpp_bridge as cpp_bridge
except Exception as _exc:  # pragma: no cover - the .pyd and every fallback are gone
    _CPP_BRIDGE_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"

    def cpp_bridge_unavailable(*args: Any, **kwargs: Any) -> Any:
        """Placeholder standing in for the whole C++ bridge surface.

        Raised rather than stored: ``engine.hydroma.cpp_bridge`` failed to
        import, and this shim must not break ``engine.numerical``. Calling
        through this name fails with a diagnostic instead of an
        ``AttributeError`` on a module that is not there.
        """
        raise NotImplementedError(
            "engine.hydroma.cpp_bridge could not be imported "
            f"({_CPP_BRIDGE_IMPORT_ERROR}), so the numerical capability "
            "surface is unavailable through this shim. Restore the compiled "
            "hydroma_core extension or the bridge's Python fallbacks."
        )

    __all__ = ["cpp_bridge_unavailable", "cpp_core_capabilities"]

else:
    _CPP_BRIDGE_IMPORT_ERROR = ""

    __all__ = ["cpp_bridge", "cpp_core_capabilities"]


def cpp_core_capabilities() -> tuple[str, ...]:
    """Return the numerical capability names reachable from ``cpp_core``.

    ``engine/cpp_core`` itself contributes no names: it ships C++ sources and
    build scripts, not Python modules, so importing it yields nothing callable.
    The kernels it contains are only reachable through
    ``engine.hydroma.cpp_bridge``, whose published surface (its ``__all__``) is
    what this probe reports — the same names the bridge declares for itself.

    Returns:
        The bridge's published capability names.

    Raises:
        NotImplementedError: when the bridge could not be imported, so there
            is no native capability to report. The message carries the import
            error rather than returning an invented list of capability names.
    """
    if _CPP_BRIDGE_IMPORT_ERROR:
        raise NotImplementedError(
            "engine/cpp_core is a C++ source tree with no Python module "
            "surface, and engine.hydroma.cpp_bridge could not be imported "
            f"({_CPP_BRIDGE_IMPORT_ERROR}); no numerical capability is "
            "reachable through this shim."
        )

    surface = cpp_bridge.__all__
    if not surface:  # pragma: no cover - the bridge always publishes one today
        raise NotImplementedError(
            "engine.hydroma.cpp_bridge imported but publishes no capability "
            "surface, so nothing can be reported from engine/cpp_core "
            "through this shim."
        )
    return tuple(surface)
