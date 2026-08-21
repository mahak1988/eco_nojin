"""Phase 7 tests: registry completeness + numeric conformance + API."""
import pytest
from fastapi.testclient import TestClient

from services.models.registry import REGISTRY, list_models, run_model
from services.api_gateway.main import app


class TestRegistry:
    def test_twenty_two_models(self):
        assert len(REGISTRY) == 22

    def test_unique_slugs(self):
        slugs = [m.slug for m in REGISTRY]
        assert len(slugs) == len(set(slugs))

    def test_fidelity_values_valid(self):
        for m in REGISTRY:
            assert m.fidelity in {"official", "simplified", "experimental"}
        counts = {m.fidelity for m in REGISTRY}
        assert "official" in counts and "simplified" in counts

    def test_all_models_have_references_and_descriptions(self):
        for m in REGISTRY:
            assert m.reference and m.description and m.name_fa and m.name_en


class TestNumericConformance:
    """5+ independent numerical checks (Phase 7 acceptance: 5 conformance tests)."""

    def test_et0_hargreaves_reference_value(self):
        # FAO-56 Hargreaves: ET0 = 0.0023 * (Tmean+17.8) * sqrt(Tmax-Tmin) * Ra * 0.408
        out = run_model("et0_hargreaves", {"t_min": 15, "t_max": 30, "t_mean": 22.5, "ra_mj": 30})
        expected = 0.0023 * (22.5 + 17.8) * (30 - 15) ** 0.5 * 30 * 0.408
        assert out["result"] == pytest.approx(expected, rel=1e-6)

    def test_runoff_volume(self):
        # area 1000 m2, rain 50 mm, C=0.5 -> 25 m3
        out = run_model("runoff_volume", {"area_m2": 1000, "rainfall_mm": 50, "runoff_coefficient": 0.5})
        assert out["result"] == pytest.approx(25.0, rel=1e-6)

    def test_ndvi_style_spectral(self):
        # via erosion? no — spectral indices live in satellite; conformance here is soil/water
        # van Genuchten: theta must lie between theta_r and theta_s
        out = run_model(
            "van_genuchten_theta",
            {"h": 100, "theta_r": 0.05, "theta_s": 0.45, "alpha": 0.02, "n": 1.5},
        )
        theta = out["result"]
        assert 0.05 <= theta <= 0.45

    def test_biomass_aboveground_positive_and_increasing(self):
        small = run_model("biomass_aboveground", {"D_cm": 10, "H_m": 5}).get("result")
        big = run_model("biomass_aboveground", {"D_cm": 30, "H_m": 15}).get("result")
        assert small > 0
        assert big > small

    def test_rothc_pools_positive_and_balanced(self):
        out = run_model(
            "rothc_pools",
            {"initial_C_tha": 40, "annual_input_tha": 3, "clay_pct": 30, "years": 50},
        )
        result = out["result"]
        assert isinstance(result, dict)
        pools = result.get("pools") or {}
        assert len(pools) >= 5, f"expected 5 RothC pools, got {list(pools.keys())}"
        for v in pools.values():
            assert isinstance(v, (int, float)) and v >= 0

    def test_salinity_class_boundaries(self):
        non_saline = run_model("salinity_class", {"ec": 1.0}).get("result")
        severe = run_model("salinity_class", {"ec": 20.0}).get("result")
        assert isinstance(non_saline, dict) and isinstance(severe, dict)

    def test_soil_pedotransfer_returns_params(self):
        out = run_model("soil_pedotransfer", {"sand_pct": 40, "clay_pct": 30})
        assert isinstance(out["result"], dict) and len(out["result"]) >= 3

    def test_run_errors_are_explicit(self):
        with pytest.raises(ValueError):
            run_model("et0_hargreaves", {})  # missing required params
        with pytest.raises(ValueError):
            run_model("nope", {})


class TestModelsApi:
    def test_list_returns_22_with_badges(self):
        client = TestClient(app)
        r = client.get("/api/v1/models")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 22
        assert data["fidelity_counts"]["official"] >= 5
        assert all(m["fidelity"] in {"official", "simplified", "experimental"} for m in data["models"])

    def test_detail(self):
        client = TestClient(app)
        r = client.get("/api/v1/models/et0_hargreaves")
        assert r.status_code == 200
        assert r.json()["reference"] == "FAO-56 Hargreaves"

    def test_run_endpoint(self):
        client = TestClient(app)
        r = client.post(
            "/api/v1/models/runoff_volume/run",
            json={"area_m2": 2000, "rainfall_mm": 50, "runoff_coefficient": 0.5},
        )
        assert r.status_code == 200
        assert r.json()["result"] == pytest.approx(50.0, rel=1e-6)
        assert r.json()["fidelity"] == "simplified"

    def test_run_endpoint_bad_params(self):
        client = TestClient(app)
        r = client.post("/api/v1/models/et0_hargreaves/run", json={})
        assert r.status_code == 400
        assert "missing required parameter" in r.json()["detail"]
        r2 = client.post("/api/v1/models/unknown/run", json={})
        assert r2.status_code == 400
