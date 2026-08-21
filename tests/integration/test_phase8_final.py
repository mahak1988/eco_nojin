"""Phase 8 finalization + Phase 9 kickoff tests."""
import pytest
from fastapi.testclient import TestClient

from engine.hydroma.core.database import Base, engine
from services.api_gateway.main import app

client = TestClient(app)


def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def setup_function():
    _reset_db()


def _auth():
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "p8f@example.com",
            "password": "testpass123",
            "full_name": "F8",
            "accept_tos": True,
            "accept_privacy": True,
        },
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _project(h):
    r = client.post(
        "/api/v1/carbon/register",
        headers=h,
        json={
            "name": "P8 final",
            "area_hectares": 10.0,
            "trees_per_ha": 1000,
            "avg_diameter_cm": 20,
            "avg_height_m": 12,
            "project_years": 30,
        },
    )
    return r.json()["db_id"]


class TestDistribution:
    def test_rule_70_15_10_5_exact(self):
        from services.ecowallet.distribution import distribute

        out = distribute(1000)
        assert out["parts"] == {"producer": 700.0, "platform": 150.0, "ecosystem": 100.0, "governance": 50.0}
        assert out["sum"] == 1000.0

    def test_endpoint_and_invalid(self):
        r = client.post("/api/v1/ecowallet/distribute?total=200")
        assert r.status_code == 200
        assert r.json()["parts"]["producer"] == 140.0
        assert client.post("/api/v1/ecowallet/distribute?total=0").status_code == 422


class TestOracle:
    def setup_method(self):
        _reset_db()

    def _verified_issued(self):
        h = _auth()
        pid = _project(h)
        client.post(
            f"/api/v1/carbon/projects/{pid}/verify",
            headers=h,
            json={
                "baseline_activity": "degraded pasture",
                "commitment_years": 30,
            },
        )
        client.post(f"/api/v1/carbon/projects/{pid}/issue", headers=h)
        return h, pid

    def test_oracle_report_certificate(self):
        h, pid = self._verified_issued()
        r = client.get(f"/api/v1/carbon/projects/{pid}/oracle-report", headers=h)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["certificate_id"].startswith("ECO-ORACLE-")
        assert body["verification_status"] == "verified"
        assert body["status"] == "issued"
        assert len(body["checks"]) == 4
        assert body["credits_issued"] > 0

    def test_oracle_ownership(self):
        h, pid = self._verified_issued()
        r = client.post(
            "/api/v1/auth/register",
            json={
                "email": "p8f2@example.com",
                "password": "testpass123",
                "full_name": "Xx",
                "accept_tos": True,
                "accept_privacy": True,
            },
        )
        h2 = {"Authorization": f"Bearer {r.json()['access_token']}"}
        res = client.get(f"/api/v1/carbon/projects/{pid}/oracle-report", headers=h2)
        assert res.status_code == 403


class TestScience:
    def setup_method(self):
        _reset_db()

    def test_citations_offline(self):
        r = client.get("/api/v1/science/citations?slug=et0_hargreaves")
        assert r.status_code == 200
        body = r.json()
        assert "Hargreaves" in body["citation"]
        assert body["doi"] is None

    def test_citations_unknown_slug(self):
        r = client.get("/api/v1/science/citations?slug=nope")
        assert r.status_code == 400

    def test_datasets_honest(self):
        r = client.get("/api/v1/science/datasets")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 5
        for d in body["datasets"]:
            assert d["status"] in ("live", "offline")
