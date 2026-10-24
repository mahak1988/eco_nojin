"""S17 -- Services strict: facade contracts, engine<->facade parity, architecture.

Hard-scrutiny suite for the services layer.

Coverage
--------
* Facade contract: every public facade entry point returns the shape its
  type/signature advertises (rich ET dicts, plain floats, plain dicts).
* Engine-facade parity: the facade is a thin pass-through over the gateway,
  so its ``data`` (or values) must equal ``EngineGateway.execute(...).values``
  for matching inputs, and must equal the underlying engine function on the
  scientific fields.
* Architecture (ECO-03.1 import guard): ``tools/detect_imports.py`` reports
  0 violations -- the SERVICES_NO_ENGINE_INTERNALS invariant is enforced and
  the facade stays the only services file that may touch engine internals.
* Malformed-input contract: non-finite / negative inputs surface as a
  ``RuntimeError`` from the facade (never an escaped exception).
* Determinism: identical inputs yield byte-identical values.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import services._gateway_facade as f
from engine.gateway import (
    EngineGateway,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)

# The hydrama package spelling is discovered at runtime (see S16 for rationale).
_REPO = Path(__file__).resolve().parents[3]
_ENGINE = _REPO / "engine"
_HYD = next(
    d for d in os.listdir(_ENGINE) if d.lower().startswith("hydr") and (_ENGINE / d).is_dir()
)
_carbon_mod = importlib.import_module(f"engine.{_HYD}.carbon.calculator")
_et_mod = importlib.import_module(f"engine.{_HYD}.climate.et_calculator")
_runoff_mod = importlib.import_module(f"engine.{_HYD}.runoff")

CarbonProjectType = _carbon_mod.CarbonProjectType
calculate_carbon_sequestration_engine = _carbon_mod.calculate_carbon_sequestration
calc_et0_hargreaves_engine = _et_mod.calc_et0_hargreaves
ClimateData = _et_mod.ClimateData
compute_runoff_engine = _runoff_mod.compute_runoff

_GW = EngineGateway()
_PROV = ProvenanceSpec(source="s17", source_type="TEST")
_ENGINE_ROOT = str(_REPO)


def _gw_values(model_id: str, inputs: dict, units: dict | None = None) -> dict:
    r = _GW.execute(
        GatewayRequest(
            model_id=model_id,
            inputs=inputs,
            input_units=units or {},
            provenance=_PROV,
        )
    )
    assert isinstance(r, GatewayResult), f"gateway failure: {r.error_code}: {r.message}"
    return r.values


# --------------------------------------------------------------------------- #
# Facade contract                                                              #
# --------------------------------------------------------------------------- #
class TestFacadeContracts:
    def test_calculate_cec_shape(self) -> None:
        r = f.calculate_cec(clay_pct=25.0, organic_matter_pct=1.5, ph=6.5)
        assert isinstance(r, dict)
        assert r["cec"] == pytest.approx(16.25, rel=1e-9)

    def test_classify_texture_returns_usda_label(self) -> None:
        assert f.classify_texture(40.0, 40.0, 20.0) == "loam"

    @pytest.mark.parametrize(
        "texture,expected",
        [("sand", True), ("loam", False), ("sandy_loam", True), ("clay", False)],
    )
    def test_is_sandy_uses_engine_sets(self, texture: str, expected: bool) -> None:
        assert f.is_sandy(texture) is expected

    @pytest.mark.parametrize(
        "texture,expected",
        [("clay", True), ("silty_clay", True), ("sand", False), ("loam", False)],
    )
    def test_is_clayey_uses_engine_sets(self, texture: str, expected: bool) -> None:
        assert f.is_clayey(texture) is expected

    def test_texture_triangle_coords_is_two_tuple(self) -> None:
        coords = f.texture_triangle_coords(40.0, 40.0, 20.0)
        assert isinstance(coords, tuple) and len(coords) == 2
        assert coords == pytest.approx((0.6, 0.2), abs=1e-12)

    def test_texture_names_is_label_dict(self) -> None:
        assert isinstance(f.TEXTURE_NAMES, dict)
        assert f.TEXTURE_NAMES["clay"] == "Clay"
        assert len(f.TEXTURE_NAMES) == 12

    def test_get_soil_taxonomy_returns_taxonomy(self) -> None:
        r = f.get_soil_taxonomy(clay=20.0, silt=30.0, sand=50.0, organic_matter=1.5, ph=6.5)
        assert isinstance(r, dict)
        assert "taxonomy" in r and "texture" in r

    def test_estimate_soil_parameters_returns_awc(self) -> None:
        r = f.estimate_soil_parameter(40.0, 25.0, 1.5)
        assert "awc" in r and isinstance(r["awc"], float)

    def test_van_genuchten_theta_returns_float(self) -> None:
        theta = f.van_genuchten_theta(
            matric_potential=-100.0, theta_r=0.05, theta_s=0.45, alpha=0.01, n=1.4
        )
        assert isinstance(theta, float)
        assert 0.05 <= theta <= 0.45

    def test_generate_recommendations_returns_payload(self) -> None:
        r = f.generate_recommendations(
            {"sand": 40.0, "silt": 40.0, "clay": 20.0, "ph": 6.5, "organic_matter": 1.5}
        )
        assert isinstance(r, dict)
        assert "priority_actions" in r

    def test_calculate_runoff_scs_shape(self) -> None:
        r = f.calculate_runoff(100.0, 72.0, area_ha=2.0)
        assert r["runoff_volume_m3"] == pytest.approx(719.3711, rel=1e-3)
        assert r["method"] == "SCS-CN"

    def test_calculate_runoff_rational_shape(self) -> None:
        r = f.calculate_runoff(
            40.0, 75.0, method="Rational", rational_coefficient=0.45, area_ha=2.0
        )
        assert r["runoff_volume_m3"] == pytest.approx(360.0, rel=1e-12)
        assert r["method"] == "Rational"

    def test_calc_et0_hargreaves_rich_contract(self) -> None:
        r = f.calc_et0_hargreaves(
            temp_max=25.0, temp_min=10.0, elevation=0.0, latitude=40.0, doy=150
        )
        assert r["model_id"] == "CANON-002"
        assert "data" in r and "provenance" in r and "execution_metadata" in r
        assert "et0_mm_day" in r["data"]

    def test_hargreaves_et0_returns_float(self) -> None:
        et = f.hargreaves_et0(t_min=10.0, t_max=25.0, latitude=40.0, doy=150)
        assert isinstance(et, float)
        # FAO-56 eq. 52 at the PUBLISHED exponent 0.5 (S17): the previous
        # expectation 5.00078205064849 was the 0.48 form, which the official
        # text does not publish and which ran ~5 % low.
        assert et == pytest.approx(5.279098340839128, rel=1e-6)

    def test_calculate_carbon_sequestration_contract(self) -> None:
        r = f.calculate_carbon_sequestration(
            "afforestation", 100.0, duration_years=10, region="temperate"
        )
        assert r["total_carbon_tonnes"] == pytest.approx(6800.0, rel=1e-9)
        assert r["project_type"] == "afforestation"

    def test_calculate_payback_contract(self) -> None:
        r = f.calculate_payback([-100.0, 30.0, 40.0, 50.0])
        assert r["payback_years"] == 4


# --------------------------------------------------------------------------- #
# Facade <-> gateway parity (the facade is a thin pass-through)               #
# --------------------------------------------------------------------------- #
class TestFacadeGatewayParity:
    def test_carbon_facade_equals_gateway_values(self) -> None:
        inputs = {
            "project_type": "afforestation",
            "area_ha": 100.0,
            "duration_years": 10,
            "region": "temperate",
        }
        assert f.calculate_carbon_sequestration(
            "afforestation", 100.0, 10, "temperate"
        ) == _gw_values("CARBON_SEQ", inputs)

    def test_runoff_scs_facade_equals_gateway_values(self) -> None:
        inputs = {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0}
        assert f.calculate_runoff(100.0, 72.0, area_ha=2.0) == _gw_values("CANON-004", inputs)

    def test_runoff_rational_facade_equals_gateway_values(self) -> None:
        inputs = {
            "precipitation": 40.0,
            "curve_number": 75.0,
            "area_ha": 2.0,
            "method": "Rational",
            "rational_coefficient": 0.45,
        }
        assert f.calculate_runoff(
            40.0, 75.0, method="Rational", rational_coefficient=0.45, area_ha=2.0
        ) == _gw_values("CANON-004", inputs)

    def test_hargreaves_facade_data_equals_gateway_values(self) -> None:
        inputs = {
            "temp_max": 25.0,
            "temp_min": 10.0,
            "elevation": 0.0,
            "latitude": 40.0,
            "doy": 150,
        }
        gw = _gw_values("CANON-002", inputs)
        assert (
            f.calc_et0_hargreaves(
                temp_max=25.0, temp_min=10.0, elevation=0.0, latitude=40.0, doy=150
            )["data"]
            == gw
        )


# --------------------------------------------------------------------------- #
# Facade <-> engine function parity (scientific fields)                       #
# --------------------------------------------------------------------------- #
class TestFacadeEngineParity:
    def test_carbon_facade_matches_engine_fn(self) -> None:
        direct = calculate_carbon_sequestration_engine(
            CarbonProjectType.AFFORESTATION, 100.0, 10, "temperate"
        )
        via_facade = f.calculate_carbon_sequestration("afforestation", 100.0, 10, "temperate")
        for key in ("total_carbon_tonnes", "annual_rate_tonnes", "estimated_revenue_usd"):
            assert via_facade[key] == pytest.approx(direct[key], rel=1e-12)

    def test_runoff_facade_matches_engine_fn(self) -> None:
        direct = compute_runoff_engine(
            {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0}, {}
        )
        via_facade = f.calculate_runoff(100.0, 72.0, area_ha=2.0)
        assert via_facade["runoff_volume_m3"] == pytest.approx(
            direct["runoff_volume_m3"], rel=1e-12
        )

    def test_hargreaves_facade_matches_engine_fn(self) -> None:
        data = ClimateData(tmin=10.0, tmax=25.0, elevation=0.0, latitude=40.0, doy=150)
        direct = calc_et0_hargreaves_engine(data=data)
        via_facade = f.calc_et0_hargreaves(
            temp_max=25.0, temp_min=10.0, elevation=0.0, latitude=40.0, doy=150
        )["data"]["et0_mm_day"]
        assert via_facade == pytest.approx(direct, rel=1e-12)


# --------------------------------------------------------------------------- #
# Architecture (import guard)                                                  #
# --------------------------------------------------------------------------- #
class TestImportGuard:
    def test_services_have_no_forbidden_engine_imports(self) -> None:
        """ECO-03.1: the services package must not import engine internals
        except through the sanctioned allowlist (and the facade file)."""
        proc = subprocess.run(
            [sys.executable, "tools/detect_imports.py", "--root", "."],
            cwd=_ENGINE_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0, combined
        assert "Violations found: 0" in combined
        assert "PASS" in combined


# --------------------------------------------------------------------------- #
# Malformed-input contract (facade)                                            #
# --------------------------------------------------------------------------- #
class TestMalformedInputs:
    def test_nan_temperature_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError, match="finite"):
            f.calc_et0_hargreaves(
                temp_max=25.0,
                temp_min=float("nan"),
                elevation=0.0,
                latitude=40.0,
                doy=150,
            )

    def test_inf_temperature_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError):
            f.hargreaves_et0(t_min=10.0, t_max=float("inf"), latitude=40.0, doy=150)

    def test_negative_area_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError):
            f.calculate_carbon_sequestration("afforestation", -1.0, 10, "temperate")

    def test_negative_curve_number_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError):
            f.calculate_runoff(100.0, -5.0, area_ha=2.0)


# --------------------------------------------------------------------------- #
# Determinism                                                                  #
# --------------------------------------------------------------------------- #
class TestDeterminism:
    def test_carbon_facade_is_deterministic(self) -> None:
        args = ("afforestation", 100.0, 10, "temperate")
        assert f.calculate_carbon_sequestration(*args) == f.calculate_carbon_sequestration(*args)

    def test_runoff_facade_is_deterministic(self) -> None:
        assert f.calculate_runoff(100.0, 72.0, area_ha=2.0) == f.calculate_runoff(
            100.0, 72.0, area_ha=2.0
        )

    def test_hargreaves_facade_values_are_deterministic(self) -> None:
        a = f.calc_et0_hargreaves(
            temp_max=25.0, temp_min=10.0, elevation=0.0, latitude=40.0, doy=150
        )
        b = f.calc_et0_hargreaves(
            temp_max=25.0, temp_min=10.0, elevation=0.0, latitude=40.0, doy=150
        )
        assert a["data"] == b["data"]


# --------------------------------------------------------------------------- #
# T-03: latent NameError defects outside every test's reach                   #
# --------------------------------------------------------------------------- #
class TestLatentNameErrors:
    """Three defects the green suites never executed: a typo'd import in the
    economics router, two facade wrappers that kept pre-S17 signatures the
    router and the engine's own integration layer no longer use, and an
    unimported ``datetime`` in the oracle router. Each test below invokes the
    real code path -- the router runner functions through the facade into the
    engine -- so a regression fails here, not in production.
    """

    def test_econ_roi_runner_executes_end_to_end(self) -> None:
        """The ROI runner must resolve ``calculate_financial_metrics`` and
        return the engine's real metrics."""
        from services.api_gateway.routers.hydroma_economics import _run_econ_roi

        out = _run_econ_roi(
            {
                "initial_investment": 1000.0,
                "cash_flows": [300.0, 400.0, 500.0],
                "discount_rate": 0.1,
            }
        )
        assert isinstance(out, dict)
        assert out["project_lifetime_years"] == 3
        # The facade's terminal_value defaults to 0, so this is the plain
        # NPV of [-1000, 300, 400, 500] at 10 %; with salvage it would be
        # 16.5289 (see S17 engine suite).
        assert out["npv_irr"] == pytest.approx(-21.0368144252443, rel=1e-9)

    def test_risk_runner_accepts_the_keyword_contract(self) -> None:
        """The risk runner calls the facade wrappers with the keyword contract
        the router's own spec advertises (base_price/volatility/... and
        expected_yield/yield_std_dev/...)."""
        from services.api_gateway.routers.hydroma_economics import _run_econ_risk

        out = _run_econ_risk(
            {
                "base_price": 300.0,
                "volatility": 0.2,
                "time_horizon_years": 1,
                "confidence_level": 0.05,
                "expected_yield": 4.2,
                "yield_std_dev": 0.5,
                "area_hectares": 10.0,
                "price_per_unit": 300.0,
            }
        )
        assert out["market_price_risk"]["base_price_irr"] == pytest.approx(300.0)
        assert out["market_price_risk"]["value_at_risk_irr"] > 0.0
        assert out["yield_risk"]["expected_total_revenue_irr"] == pytest.approx(
            12600.0, rel=1e-9
        )

    def test_facade_risk_wrappers_match_engine_signatures(self) -> None:
        """The facade wrappers themselves must take the keyword contract:
        the engine's own integration layer calls them that way."""
        price = f.assess_market_price_risk(
            base_price=200.0, volatility=0.15, time_horizon_years=1
        )
        assert price["base_price_irr"] == pytest.approx(200.0)
        assert price["value_at_risk_irr"] > 0.0
        yield_risk = f.assess_yield_risk(
            expected_yield=4.2,
            yield_std_dev=0.5,
            area_hectares=10.0,
            price_per_unit=200.0,
        )
        assert yield_risk["expected_total_revenue_irr"] == pytest.approx(8400.0, rel=1e-9)

    def test_oracle_challenge_window_uses_a_defined_datetime(self) -> None:
        """The expired-challenge branch of the real router function reaches
        ``datetime.now()``; before the fix the name was undefined."""
        import asyncio
        from datetime import datetime as _dt

        from fastapi import HTTPException

        from services.oracle import router as oracle_router

        class _Result:
            def scalar_one_or_none(self):
                return SimpleNamespace(
                    activity_id="a1",
                    challenged=False,
                    challenge_deadline=_dt(2020, 1, 1),
                )

        class _Session:
            async def execute(self, *_args, **_kwargs):
                return _Result()

        data = SimpleNamespace(activity_id="a1")
        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(oracle_router.create_challenge(data, _Session()))
        assert excinfo.value.status_code == 410

    def test_nojin_service_factory_is_single_and_resolvable(self) -> None:
        """The dead duplicate factory in ``repository.py`` referenced an
        undefined ``NojinService`` and would NameError on any call; the
        canonical factory in ``service.py`` must stay the only one."""
        from services.nojin import repository, service

        assert not hasattr(repository, "get_nojin_service"), (
            "repository.py must not carry a duplicate factory; service.py owns it"
        )
        assert hasattr(service, "get_nojin_service")
        assert service.NojinService.__name__ == "NojinService"
        # Real constructor invocation with a stub repository (the service's
        # own dependency contract), not a mock of the computation.
        svc = service.NojinService(SimpleNamespace(db=None))
        assert svc.repo is not None
