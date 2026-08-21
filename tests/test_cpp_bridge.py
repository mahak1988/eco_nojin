"""C++20 parity tests (skip when hydroma_core.dll is missing)."""
import pytest

from services.models import cpp_bridge
from services.models.registry import run_model

NEEDS_CPP = pytest.mark.skipif(
    not cpp_bridge.available(), reason="hydroma_core.dll not built"
)


def test_status_honest():
    s = cpp_bridge.status()
    assert "available" in s
    assert isinstance(s["available"], bool)
    assert "et0_hargreaves" in s["kernels"]


@NEEDS_CPP
def test_et0_parity_with_registry():
    """C++ ET0 must match the Python registry implementation (1e-9 rel)."""
    import math

    case = {"t_min": 12.0, "t_max": 27.0, "t_mean": 19.5, "ra_mj": 28.4}
    py = run_model("et0_hargreaves", dict(case))["result"]
    cpp = cpp_bridge.et0_hargreaves_cpp(**case)
    assert math.isclose(cpp, py, rel_tol=1e-9, abs_tol=1e-9)


@NEEDS_CPP
def test_ra_sane_bounds():
    ra = cpp_bridge.extraterrestrial_radiation_cpp(36.0, 172)
    # FAO-56 Ra at mid-latitudes mid-year: roughly 35-45 MJ/m2/day
    assert 20.0 < ra < 60.0


@NEEDS_CPP
def test_vg_parity_with_registry():
    import math

    case = {"h": 100.0, "theta_r": 0.05, "theta_s": 0.4, "alpha": 0.02, "n": 1.5}
    py = run_model("van_genuchten_theta", dict(case))["result"]
    cpp = cpp_bridge.vg_theta_cpp(**case)
    assert math.isclose(cpp, py, rel_tol=1e-9, abs_tol=1e-9)


@NEEDS_CPP
def test_vg_bounds():
    theta = cpp_bridge.vg_theta_cpp(1e6, 0.05, 0.4, 0.02, 1.5)
    assert 0.05 <= theta <= 0.4
