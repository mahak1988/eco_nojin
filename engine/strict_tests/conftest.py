"""Shared configuration and reference constants for the strict engine suite.

Recovered 2026-09-28 from ``__pycache__/conftest.cpython-312.pyc``, which
predated an accidental overwrite of an untracked file. Every value below was
read back by executing the original bytecode, not retyped from memory; see
docs/ENGINE_PHASE1_F1_FA_2026-09-28.md. Comments were not preserved by the
bytecode and are the one thing here that could not be recovered.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st

# The engine root, not this suite's directory. Four things in test_s01 depend on
# that distinction and all four agree: _discover_modules builds dotted paths as
# `relative_to(ENGINE_ROOT.parent)`, which only yields importable `engine.*`
# names when the root is the engine package; _walk_engine_sources skips
# `rel.parts[0] == "strict_tests"`, which is only ever true when the suite is a
# child of the root; KNOWN_DISCARDED_SITES keys are engine-relative
# (`hydroma/soil/physics.py`); and the importability sweep runs with
# `cwd=ENGINE_ROOT.parent`, i.e. the repository root.
ENGINE_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Hypothesis profiles
# --------------------------------------------------------------------------
# `strict-engine-ci` is the one CI selects. A local run and a CI run are then
# the same run at different depths, rather than two different runs.

settings.register_profile(
    "strict-engine",
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
settings.register_profile("strict-engine-ci", max_examples=25, deadline=None)
settings.register_profile("strict-engine-deep", max_examples=2000, deadline=None)
settings.load_profile("strict-engine")

# --------------------------------------------------------------------------
# External reference values
# --------------------------------------------------------------------------
# Each is a published figure the suite asserts against, not a value captured
# from the engine. Capturing the engine's own output and calling it a reference
# is the failure mode this suite exists to prevent.

FAO56_REFERENCE_DAY = {
    "tmin": 22.6,
    "tmax": 30.5,
    "rh_min": 62.0,
    "rh_max": 82.0,
    "wind_speed": 1.7,
    "solar_radiation": 28.4,
    "elevation": 100.0,
    "latitude": 41.9,
    "doy": 193,
}

NRCS_SCS_CN_WORKED_EXAMPLE = {
    "precipitation_mm": 50.0,
    "curve_number": 70.0,
    "retention_mm": 108.85714285714283,
    "retention_inches": 4.2857142857142865,
    "initial_abstraction_mm": 21.77142857142857,
    "runoff_mm": 5.812802953611626,
}

THEIS_REFERENCE = {
    "transmissivity_m2day": 2000.0,
    "storativity": 0.0002,
    "pumping_rate_m3day": 760.0,
    "distance_m": 30.0,
    "time_days": 1.0,
}

SAXTON_RAWLS_2006_AWC_MM_PER_M = {
    "sand": 91.0,
    "loamy_sand": 121.0,
    "sandy_loam": 143.0,
    "loam": 180.0,
    "silt_loam": 199.0,
    "sandy_clay_loam": 193.0,
    "clay_loam": 212.0,
    "silty_clay_loam": 190.0,
    "sandy_clay": 175.0,
    "silty_clay": 185.0,
    "clay": 201.0,
    "silt": 211.0,
}

USDA_TEXTURE_FINENESS_ORDER = [
    "sand",
    "loamy_sand",
    "sandy_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_clay_loam",
    "loam_clay",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay",
    "silty_clay",
    "clay",
]

PHYSICAL_BOUNDS = {
    "theta_r": (0.0, 0.3),
    "theta_s": (0.3, 1.0),
    "alpha_cm_inv": (0.0001, 1.0),
    "n": (1.0, 3.0),
    "ks_cm_day": (0.01, 5000.0),
}


# --------------------------------------------------------------------------
# Unit conversions
# --------------------------------------------------------------------------


def pa_m3s_to_cm_day(pa_s: float) -> float:
    """Convert hydraulic conductivity from m/s to cm/day."""
    return pa_s * 100.0 * 86400.0


def cm_day_to_m_s(cm_day: float) -> float:
    """Convert hydraulic conductivity from cm/day to m/s."""
    return cm_day / (100.0 * 86400.0)


def mm_per_cm3cm3_to_awc_mm_per_m(theta_a: float, theta_b: float) -> float:
    """Difference in volumetric water content expressed as mm per metre."""
    return (theta_a - theta_b) * 1000.0


def fao56_ra_extremes() -> dict:
    """Admissible range of FAO-56 extraterrestrial radiation over a calendar year.

    At the equator the daily mean top-of-atmosphere flux tops out near
    40 MJ/m2/day (annual mean) with a summer-solstice peak of ~40.4; at 45 deg
    latitude the solstice peak is ~32.0; the poles integrate to zero at the
    solstice. 0.0 to 45.0 brackets all of it.
    """
    return {"min": 0.0, "max": 45.0}


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture
def vg_table():
    """The engine's own van Genuchten table, shared across tests."""
    from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG

    return SOIL_PARAMETERS_VG


@pytest.fixture
def fano_consts():
    """Physical constants, gathered once so tests can cross-check conversions."""
    return {
        "mj_to_mm_equiv": 0.408,
        "mm_per_cm": 10.0,
        "ha_to_m2": 10000.0,
        "sec_per_hour": 3600.0,
        "dbar_per_kpa": 10.0,
        "co2_per_c": 3.6666666666666665,
        "g": 9.80665,
    }


@st.composite
def climate_day(draw):
    """Draw one physically coherent FAO-56 daily climate record.

    The joint-admissibility rules matter more than the individual ranges. A day
    with Rs above the clear-sky value, or RH_min above RH_max, is not weather;
    it is a number that would let a property test pass or fail for the wrong
    reason.

    Every value is drawn and the record is returned as a plain dict, so nothing
    is left to rejection sampling. RH_max exceeds RH_min structurally because
    it is built as rh_min plus a positive offset, and Rs stays inside the
    clear-sky band by construction. `ra` rides along so a test can check the
    engine's own extraterrestrial radiation against an independent integration
    rather than against the engine's own arithmetic.
    """
    latitude = draw(st.floats(-89.0, 89.0))
    doy = draw(st.integers(1, 365))
    ra = _oracle_ra(latitude, doy)
    dtr = draw(st.floats(2.0, 20.0))
    t_mean = draw(st.floats(-10.0, 40.0))
    rh_min = draw(st.floats(10.0, 60.0))
    return {
        "tmin": t_mean - dtr / 2.0,
        "tmax": t_mean + dtr / 2.0,
        "rh_min": rh_min,
        "rh_max": rh_min + draw(st.floats(5.0, 35.0)),
        "wind_speed": draw(st.floats(0.5, 8.0)),
        "solar_radiation": draw(st.floats(0.05 * ra, 0.78 * ra)),
        "elevation": draw(st.floats(0.0, 3000.0)),
        "latitude": latitude,
        "doy": doy,
        "ra": ra,
    }


def _oracle_ra(latitude: float, doy: int) -> float:
    """FAO-56 eq. 21 by explicit day-length integration (see test_s02)."""
    phi = math.radians(latitude)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
    delta = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
    cos_ws = -math.tan(phi) * math.tan(delta)
    ws = math.acos(max(-1.0, min(1.0, cos_ws)))
    return (24.0 * 60.0 / math.pi) * 0.082 * dr * (
        ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws)
    )


def assert_close(actual: float, expected: float, rel: float, label: str) -> None:
    """Assert relative closeness with a message that states the reference."""
    if not math.isclose(actual, expected, rel_tol=rel):
        pytest.fail(f"{label}: {actual!r} against reference {expected!r} at rel={rel}")


# --------------------------------------------------------------------------
# requires_cpp
# --------------------------------------------------------------------------
# Twenty tests here compare the Python engine against the compiled C++ core, or
# read a value out of the C++ copy of the soil table. They have no Python
# fallback to compare against, so with the extension absent they cannot be
# answered at all -- the correct outcome is to skip, not to fail.
#
# The markers are applied per test, not per class. The seven classes involved
# hold 56 tests between them and only 20 need the extension, so a class-level
# skip would silently drop 36 passing tests.


def _cpp_status() -> tuple[bool, str]:
    """Report whether the compiled core loaded, and say why not if it did not.

    A skip that does not explain itself is indistinguishable from a test that
    quietly stopped running, which is the failure mode this suite exists to
    prevent.
    """
    try:
        from engine.hydroma.cpp_bridge import get_module
    except Exception as exc:  # pragma: no cover - import-time environment problem
        return False, f"cpp_bridge could not be imported: {type(exc).__name__}: {exc}"

    try:
        module = get_module()
    except Exception as exc:  # pragma: no cover - the loader reports its own reason
        return False, f"cpp_bridge loader failed: {type(exc).__name__}: {exc}"

    if module is None:
        try:
            from engine.hydroma.cpp_bridge import backend_status

            detail = backend_status().get("import_error") or "no detail reported"
        except Exception:
            detail = "no detail reported"
        return False, f"hydroma_core extension not loaded: {detail}"

    return True, "hydroma_core loaded"


CPP_AVAILABLE, CPP_DETAIL = _cpp_status()

# The reason is fixed, not interpolated, so it names the condition rather than
# whatever happened to be true when the module loaded. The header below reports
# the live state instead.
_SKIP_REASON = (
    "requires the compiled C++ core -- these tests compare Python against C++ or "
    "read a value out of the C++ soil table, and have no Python fallback to "
    "compare with. Build it with: cmake -B engine/cpp_core/build -S engine/cpp_core "
    "-DHYDROMA_BUILD_PYTHON_BINDINGS=ON && cmake --build engine/cpp_core/build && "
    "cp engine/cpp_core/build/hydroma_core*.so engine/hydroma/cpp_bridge/"
)

requires_cpp = pytest.mark.skipif(not CPP_AVAILABLE, reason=_SKIP_REASON)


def pytest_report_header(config: pytest.Config) -> list[str]:
    """State the backend once, so a shorter run is explained before it is counted."""
    state = "available" if CPP_AVAILABLE else "NOT available"
    return [f"engine strict suite: C++ core {state} ({CPP_DETAIL})"]
