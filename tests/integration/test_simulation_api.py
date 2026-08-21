"""Integration tests for the simulation chain API (Phase 3, sprint 2)."""

from uuid import uuid4

from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)


def _payload(**overrides) -> dict:
    base = {
        "site_id": f"sim-api-{uuid4().hex[:10]}",
        "area_ha": 5.0,
        "scenario": {"name": "Medium", "cn_change": -8.0, "c_factor_factor": 0.85, "p_factor": 0.5},
        "r_factor": 1000.0,
        "k_factor": 0.04,
        "ls_factor": 1.8,
        "c_factor_base": 0.3,
        "initial_soc_t_ha": 50.0,
        "clay_pct": 20.0,
    }
    base.update(overrides)
    return base


class TestSimulationApi:
    def test_run_chain_persists(self):
        payload = _payload()
        response = client.post("/api/v1/simulation/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] > 0
        assert data["scenario"] == "Medium"
        assert data["status"] in ("ok", "partial")
        assert "rusle" in data["outputs"]
        assert "aquacrop" in data["outputs"]
        assert "rothc" in data["outputs"]

    def test_runs_listable_and_filterable(self):
        site = f"sim-api-{uuid4().hex[:10]}"
        client.post("/api/v1/simulation/run", json=_payload(site_id=site))
        response = client.get(f"/api/v1/simulation/runs?site_id={site}")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] >= 1
        assert all(r["site_id"] == site for r in body["runs"])
        assert "outputs" in body["runs"][0]

    def test_invalid_input_rejected(self):
        response = client.post(
            "/api/v1/simulation/run",
            json=_payload(area_ha=-3.0),
        )
        assert response.status_code == 422
