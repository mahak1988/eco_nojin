"""S1-4 acceptance tests: the numerical backend must be visible and consistent.

Covers:
  * the compiled extension is used when present (and reported as such),
  * the double-import hazard that produced a misleading pybind11 error is gone,
  * C++ <-> Python parity for the shared kernels,
  * /health exposes the backend and can never silently hide a fallback.
"""

from __future__ import annotations

import importlib

import pytest

from engine.hydroma import cpp_bridge
from engine.hydroma.cpp_bridge import backend_status

PARITY_CASES = [
    ("rusle_annual_soil_loss", (1000.0, 0.4, 5.0, 0.3, 1.0)),
    ("ls_factor", (50.0, 9.0)),
    ("ls_factor", (100.0, 25.0)),
    ("estimate_rainfall_erosivity", (600.0,)),
    ("estimate_rainfall_erosivity", (1000.0,)),
    ("manning_normal_depth", (10.0, 5.0, 0.001, 0.03)),
]


class TestBackendSurface:
    def test_backend_is_explicit(self):
        assert cpp_bridge.BACKEND in {"cpp", "python"}

    def test_backend_status_shape(self):
        status = backend_status()
        assert set(status) == {"backend", "cpp_available", "import_error", "telemetry"}
        assert isinstance(status["telemetry"], dict)
        assert "fallback_calls" in status["telemetry"]

    def test_status_matches_availability(self):
        status = backend_status()
        if status["cpp_available"]:
            assert status["backend"] == "cpp"
            assert status["import_error"] is None
        else:
            assert status["backend"] == "python"


class TestDoubleImportHazard:
    """Importing the submodule path must not reload the extension.

    Previously ``from engine.hydroma.cpp_bridge import hydroma_core`` loaded the
    same .pyd under a second module name and pybind11 raised
    'generic_type: type "WaveParameters" is already registered!'.
    """

    def test_submodule_import_is_safe(self):
        mod = importlib.import_module("engine.hydroma.cpp_bridge.hydroma_core")
        assert mod is not None
        assert hasattr(mod, "rusle_annual_soil_loss")

    def test_repeated_import_is_stable(self):
        for _ in range(3):
            mod = importlib.import_module("engine.hydroma.cpp_bridge.hydroma_core")
            assert hasattr(mod, "ls_factor")


class TestCppPythonParity:
    def test_rusle_is_exact_product(self):
        assert cpp_bridge.rusle_annual_soil_loss(1000.0, 0.4, 5.0, 0.3, 1.0) == pytest.approx(600.0)

    @pytest.mark.parametrize("fn,args", PARITY_CASES)
    def test_kernel_parity(self, fn, args):
        cpp_only = backend_status()["cpp_available"]
        if not cpp_only:
            pytest.skip("compiled core unavailable - parity is trivially satisfied by the fallback")
        core = importlib.import_module("engine.hydroma.cpp_bridge.hydroma_core")
        cpp_val = getattr(core, fn)(*args)
        bridge_val = getattr(cpp_bridge, fn)(*args)
        assert cpp_val == pytest.approx(bridge_val, rel=1e-9, abs=1e-9)


class TestHealthEndpoint:
    def test_health_reports_the_backend(self):
        from fastapi.testclient import TestClient

        from services.api_gateway.main import app

        with TestClient(app) as client:
            payload = client.get("/health").json()

        checks = payload["checks"]
        assert "cpp_core" in checks
        assert checks["cpp_backend"] in {"cpp", "python", "unknown"}
        assert "degraded_reasons" in payload
        if checks["cpp_core"] == "fallback":
            assert "cpp_core_fallback" in payload["degraded_reasons"]
            assert payload["status"] == "degraded"
