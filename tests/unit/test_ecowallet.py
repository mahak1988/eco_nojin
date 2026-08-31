"""Tests for ECO Wallet module."""

import uuid

import pytest

from services.ecowallet.earning_rules import EarningCategory, EarningEngine
from services.ecowallet.ledger import EcoLedger
from services.ecowallet.messages import EcoMessages
from services.ecowallet.redemption import RedemptionCategory, RedemptionEngine


def _unique_email(prefix: str) -> str:
    """Unique email per test run so repeated runs never collide."""
    return f"{prefix}-{uuid.uuid4().hex[:10]}@qa.econojin-test.com"


def _register_or_login(client, email: str, password: str = "TestPass123") -> dict:
    """Register (or login, if the email already exists) and return auth headers."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Wallet Tester",
            "password": password,
            "accept_tos": True,
            "accept_privacy": True,
        },
    )
    if response.status_code != 200:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestEcoLedger:
    def test_create_wallet(self):
        ledger = EcoLedger()
        wallet = ledger.create_wallet("user1")
        assert wallet.user_id == "user1"
        assert wallet.balance == 0.0

    def test_create_duplicate_wallet_fails(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_dup")
        with pytest.raises(ValueError):
            ledger.create_wallet("user_dup")

    def test_earn_eco(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_earn")
        tx = ledger.earn("user_earn", 50.0, "tree_planting", "Planted trees")
        assert tx.amount == 50.0
        assert ledger.get_balance("user_earn") == 50.0

    def test_redeem_eco(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_red")
        ledger.earn("user_red", 100.0, "tree_planting", "Trees")
        tx = ledger.redeem("user_red", 30.0, "consultation", "Consultation")
        assert tx.amount == 30.0
        assert ledger.get_balance("user_red") == 70.0

    def test_redeem_insufficient_fails(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_no_balance")
        with pytest.raises(ValueError):
            ledger.redeem("user_no_balance", 100.0, "consultation", "No balance")

    def test_transaction_history(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_hist")
        ledger.earn("user_hist", 50.0, "tree_planting", "Trees")
        ledger.redeem("user_hist", 20.0, "consultation", "Consult")
        history = ledger.get_transaction_history("user_hist")
        assert len(history) == 2
        assert history[0].amount == 50.0
        assert history[1].amount == 20.0


class TestEarningEngine:
    def test_process_earning(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_earn_eng")
        engine = EarningEngine()
        engine.ledger = ledger
        tx = engine.process_earning("user_earn_eng", EarningCategory.TREE_PLANTING)
        assert tx.amount == 50.0

    def test_monthly_limit(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_limit")
        engine = EarningEngine()
        engine.ledger = ledger
        for _ in range(4):
            engine.process_earning("user_limit", EarningCategory.TREE_PLANTING)
        with pytest.raises(ValueError):
            engine.process_earning("user_limit", EarningCategory.TREE_PLANTING)


class TestRedemptionEngine:
    def test_process_redemption(self):
        ledger = EcoLedger()
        ledger.create_wallet("user_red_eng")
        ledger.earn("user_red_eng", 100.0, "tree_planting", "Trees")
        engine = RedemptionEngine()
        engine.ledger = ledger
        tx = engine.process_redemption("user_red_eng", RedemptionCategory.CONSULTATION)
        assert tx.amount == 20.0
        assert ledger.get_balance("user_red_eng") == 80.0


class TestEcoMessages:
    def test_earning_message_positive(self):
        msg = EcoMessages.earning("tree_planting", 50.0, "en")
        assert "Congratulations" in msg
        assert "50.0" in msg
        assert "warning" not in msg.lower()
        assert "risk" not in msg.lower()

    def test_redemption_message_positive(self):
        msg = EcoMessages.redemption("consultation", 80.0, "en")
        assert "booked" in msg.lower() or "used" in msg.lower()
        assert "warning" not in msg.lower()

    def test_balance_message(self):
        msg = EcoMessages.balance(100.0, 1000000.0, "en")
        assert "100.0" in msg

    def test_welcome_message(self):
        msg = EcoMessages.welcome("en")
        assert "Welcome" in msg
        assert "warning" not in msg.lower()


class TestEcoWalletAPI:
    """API tests (pentest fix C2): endpoints require auth; identity comes from token."""

    def test_earn_requires_auth(self, client):
        response = client.post("/api/v1/ecowallet/earn", json={"category": "tree_planting"})
        assert response.status_code == 401

    def test_create_wallet_endpoint(self, client):
        headers = _register_or_login(client, _unique_email("create"))
        response = client.post("/api/v1/ecowallet/wallets", json={"user_id": "ignored"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 0.0
        assert data["user_id"]

    def test_earn_endpoint(self, client):
        headers = _register_or_login(client, _unique_email("earn"))
        response = client.post(
            "/api/v1/ecowallet/earn",
            json={
                "user_id": "someone-else",
                "category": "tree_planting",
                "quantity": 1.0,
                "language": "en",
            },
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["amount_earned"] == 50.0

    def test_earn_ignores_body_user_id(self, client):
        """user_id in the body must never target another wallet (pentest C2)."""
        headers = _register_or_login(client, _unique_email("scope"))
        r = client.post(
            "/api/v1/ecowallet/earn",
            json={"user_id": "victim", "category": "tree_planting"},
            headers=headers,
        )
        assert r.status_code == 200
        balance = client.post(
            "/api/v1/ecowallet/ussd",
            json={"action": "balance"},
            headers=headers,
        ).json()["balance"]
        assert balance == 50.0

    def test_earn_unknown_category_rejected(self, client):
        headers = _register_or_login(client, _unique_email("badcat"))
        r = client.post(
            "/api/v1/ecowallet/earn",
            json={"category": "mint_free_money"},
            headers=headers,
        )
        assert r.status_code == 422

    def test_daily_earning_cap(self, client):
        headers = _register_or_login(client, _unique_email("cap"))
        for _ in range(4):  # 4 x 50 = 200 = cap
            r = client.post(
                "/api/v1/ecowallet/earn",
                json={"category": "tree_planting"},
                headers=headers,
            )
            assert r.status_code == 200
        r = client.post(
            "/api/v1/ecowallet/earn",
            json={"category": "tree_planting"},
            headers=headers,
        )
        assert r.status_code == 400

    def test_redeem_endpoint(self, client):
        headers = _register_or_login(client, _unique_email("redeem"))
        client.post("/api/v1/ecowallet/earn", json={"category": "tree_planting"}, headers=headers)
        response = client.post(
            "/api/v1/ecowallet/redeem",
            json={"user_id": "ignored", "category": "consultation"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["amount_redeemed"] == 20.0

    def test_redeem_insufficient_fails(self, client):
        headers = _register_or_login(client, _unique_email("poor"))
        response = client.post(
            "/api/v1/ecowallet/redeem",
            json={"category": "consultation"},
            headers=headers,
        )
        assert response.status_code == 400

    def test_ussd_balance(self, client):
        headers = _register_or_login(client, _unique_email("ussd"))
        response = client.post(
            "/api/v1/ecowallet/ussd",
            json={"user_id": "ignored", "action": "balance", "language": "fa"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["action"] == "balance"

    def test_stats_requires_auth(self, client):
        response = client.get("/api/v1/ecowallet/stats")
        assert response.status_code == 401

    def test_stats_endpoint(self, client):
        headers = _register_or_login(client, _unique_email("stats"))
        response = client.get("/api/v1/ecowallet/stats", headers=headers)
        assert response.status_code == 200
        assert "total_wallets" in response.json()

    def test_health_endpoint(self, client):
        response = client.get("/api/v1/ecowallet/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["features"]["external_exchange"] is False

    def test_main_health_reachable(self, client):
        """Platform /health contract (previously asserted a non-existent 'modules' key)."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "operational"
