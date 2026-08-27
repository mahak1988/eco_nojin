"""
C++20 parity bridge (Phase 7) — ctypes loader for hydroma_core.dll.

Hot scientific kernels (ET0 Hargreaves, extraterrestrial radiation,
van Genuchten retention) are compiled from engine/cpp_core and called
directly from Python via ctypes. This is the "C++20 parity for hot paths"
acceptance item of the master plan.

Honesty contract
----------------
- ``available`` is True only when the DLL is found and loads.
- Every kernel raises :class:`CppBridgeUnavailable` otherwise —
  never falls back to Python silently (parity means *verified*, and the
  caller must see the difference).

DLL discovery order:
1. env ``HYDROMA_CORE_DLL`` (explicit path)
2. ``engine/cpp_core/hydroma_core.dll`` (repo default)
3. ``hydroma_core.dll`` next to this module / CWD

Build (MSVC, from engine/cpp_core):
    call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools\\
          VC\\Auxiliary\\Build\\vcvars64.bat"
    cl /nologo /std:c++20 /O2 /EHsc /LD /Iinclude bindings\\c_api.cpp ^
       src\\climate.cpp src\\soil.cpp /Fe:hydroma_core.dll
"""
from __future__ import annotations

import ctypes
import logging
import os
import pathlib
from typing import Any

logger = logging.getLogger(__name__)


class CppBridgeUnavailable(RuntimeError):
    """Raised when hydroma_core.dll cannot be loaded."""


def _discover_dll() -> pathlib.Path | None:
    env = os.environ.get("HYDROMA_CORE_DLL")
    if env:
        p = pathlib.Path(env)
        if p.exists():
            return p
    repo = pathlib.Path(__file__).resolve().parents[2] / "engine" / "cpp_core" / "hydroma_core.dll"
    if repo.exists():
        return repo
    local = pathlib.Path("hydroma_core.dll")
    if local.exists():
        return local
    return None


def _load() -> Any:
    path = _discover_dll()
    if path is None:
        raise CppBridgeUnavailable(
            "hydroma_core.dll not found — build it from engine/cpp_core "
            "(see module docstring) or set HYDROMA_CORE_DLL"
        )
    lib = ctypes.CDLL(str(path))
    lib.et0_hargreaves.argtypes = [ctypes.c_double] * 4
    lib.et0_hargreaves.restype = ctypes.c_double
    lib.extraterrestrial_radiation.argtypes = [ctypes.c_double, ctypes.c_int]
    lib.extraterrestrial_radiation.restype = ctypes.c_double
    lib.vg_theta.argtypes = [ctypes.c_double] * 5
    lib.vg_theta.restype = ctypes.c_double
    return lib


try:
    _LIB: Any = _load()
    AVAILABLE = True
except Exception as exc:
    logger.info("cpp bridge unavailable: %s", exc)
    _LIB = None
    AVAILABLE = False


def available() -> bool:
    return AVAILABLE


def _require() -> Any:
    if _LIB is None:
        raise CppBridgeUnavailable("hydroma_core.dll unavailable")
    return _LIB


def et0_hargreaves_cpp(t_min: float, t_max: float, t_mean: float, ra_mj: float) -> float:
    """C++20 Hargreaves ET0 [mm/day] (parity target: registry et0_hargreaves)."""
    return float(_require().et0_hargreaves(t_min, t_max, t_mean, ra_mj))


def extraterrestrial_radiation_cpp(lat_deg: float, doy: int) -> float:
    """C++20 FAO-56 Ra [MJ/m2/day]."""
    return float(_require().extraterrestrial_radiation(lat_deg, int(doy)))


def vg_theta_cpp(h: float, theta_r: float, theta_s: float, alpha: float, n: float) -> float:
    """C++20 van Genuchten theta [cm3/cm3] (parity target: registry van_genuchten_theta)."""
    return float(_require().vg_theta(h, theta_r, theta_s, alpha, n))


def status() -> dict[str, Any]:
    """Honest capability report: available + which kernels are bridged."""
    return {
        "available": AVAILABLE,
        "dll": str(_discover_dll()) if _discover_dll() else None,
        "kernels": ["et0_hargreaves", "extraterrestrial_radiation", "vg_theta"],
        "note": (
            "C++20 kernels active (MSVC /O2)"
            if AVAILABLE
            else "hydroma_core.dll missing — build from engine/cpp_core"
        ),
    }
