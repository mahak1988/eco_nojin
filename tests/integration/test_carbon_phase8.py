"""Phase 8 integration tests: register -> verify (honest) -> issue -> wallet."""
import pytest
from fastapi.testclient import TestClient

from engine.hydroma.core.database import Base, engine
from services.api_gateway.main import app

client = TestClient(app)


def _reset_db():
    """Reset database (repo-wide pattern)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def setup_function():
    """Reset before module-level tests (kept for consistency)."""
    _reset_db()


def _auth_headers():
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "p8test@example.com",
            "password": "testpass123",
            "full_name": "P8",
            "accept_tos": True,
            "accept_privacy": True,
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _register_project(headers):
    return client.post(
        "/api/v1/carbon/register",
        headers=headers,
        json={
            "name": "P8 afforestation",
            "area_hectares": 10.0,
            "species": "tropical_moist",
            "trees_per_ha": 1000,
            "avg_diameter_cm": 20,
            "avg_height_m": 12,
            "project_years": 30,
            "latitude": 36.0,
            "longitude": 51.0,
            "soil_carbon_tha": 40.0,
            "mean_temperature_C": 25.0,
        },
    )


class TestVerification:
    def setup_method(self):
        """pytest calls setup_method for test classes."""
        _reset_db()

    def test_full_flow(self):
        h = _auth_headers()
        reg = _register_project(h)
        assert reg.status_code == 200, reg.text
        pid = reg.json()["db_id"]

        # 1) honest failure when baseline missing / financing exists
        bad = client.post(
            f"/api/v1/carbon/projects/{pid}/verify",
            headers=h,
            json={"baseline_activity": "", "has_financing": True},
        )
        assert bad.status_code == 200
        v = bad.json()["verification"]
        assert v["passed"] is False
        assert "baseline" in v["failed"]
        assert "additionality" in v["failed"]

        # 2) pass when all checks satisfied
        good = client.post(
            f"/api/v1/carbon/projects/{pid}/verify",
            headers=h,
            json={
                "baseline_activity": "degraded pasture, no tree cover",
                "has_financing": False,
                "would_happen_without_project": False,
                "activity_displacement": False,
                "market_leakage": False,
                "commitment_years": 30,
                "risk_flag": False,
            },
        )
        assert good.status_code == 200
        assert good.json()["verification"]["passed"] is True

        # 3) issue credits -> wallet credited (persistent DB)
        issue = client.post(f"/api/v1/carbon/projects/{pid}/issue", headers=h)
        assert issue.status_code == 200, issue.text
        body = issue.json()
        assert body["credits_issued"] > 0
        assert body["wallet_eco_earned"] > 0
        assert body["wallet_balance"] > 0

        # wallet state visible via /wallet
        w = client.get("/api/v1/carbon/wallet", headers=h)
        assert w.status_code == 200
        assert w.json()["balance"] == body["wallet_balance"]

    def test_issue_without_verify_rejected(self):
        h = _auth_headers()
        pid = _register_project(h).json()["db_id"]
        r = client.post(f"/api/v1/carbon/projects/{pid}/issue", headers=h)
        assert r.status_code == 400
        assert "not verified" in r.json()["detail"]

    def test_ownership_enforced(self):
        h1 = _auth_headers()
        pid = _register_project(h1).json()["db_id"]
        r = client.post(
            "/api/v1/auth/register",
            json={
                "email": "p8other@example.com",
                "password": "testpass123",
                "full_name": "Other",
                "accept_tos": True,
                "accept_privacy": True,
            },
        )
        h2 = {"Authorization": f"Bearer {r.json()['access_token']}"}
        res = client.post(
            f"/api/v1/carbon/projects/{pid}/verify", headers=h2, json={"baseline_activity": "xxx"}
        )
        assert res.status_code == 403

    def test_unknown_project_404(self):
        h = _auth_headers()
        res = client.post(
            "/api/v1/carbon/projects/999999/verify", headers=h, json={"baseline_activity": "xxx"}
        )
        assert res.status_code == 404

    def test_permanence_check(self):
        from services.carbon.verification import check_permanence

        assert check_permanence(10, False)["passed"] is False  # too short
        assert check_permanence(30, True)["passed"] is False   # risk flag
        assert check_permanence(30, False)["passed"] is True
