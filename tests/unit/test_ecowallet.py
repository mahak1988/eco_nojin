"""Tests for ECO Wallet module."""

import pytest
from fastapi.testclient import TestClient

from engine.hydroma.ecowallet.earning_rules import EarningCategory, EarningEngine
from engine.hydroma.ecowallet.ledger import EcoLedger
from engine.hydroma.ecowallet.messages import EcoMessages
from engine.hydroma.ecowallet.redemption import RedemptionCategory, RedemptionEngine
from services.api_gateway.main import app

client = TestClient(app)


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
    def test_create_wallet_endpoint(self):
        response = client.post("/api/v1/ecowallet/wallets", json={"user_id": "api_u1"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "api_u1"
        assert data["balance"] == 0.0

    def test_earn_endpoint(self):
        client.post("/api/v1/ecowallet/wallets", json={"user_id": "api_u2"})
        response = client.post(
            "/api/v1/ecowallet/earn",
            json={
                "user_id": "api_u2",
                "category": "tree_planting",
                "quantity": 1.0,
                "language": "en",
            },
        )
        assert response.status_code == 200
        assert response.json()["amount_earned"] == 50.0

    def test_redeem_endpoint(self):
        client.post("/api/v1/ecowallet/wallets", json={"user_id": "api_u3"})
        client.post(
            "/api/v1/ecowallet/earn",
            json={
                "user_id": "api_u3",
                "category": "tree_planting",
            },
        )
        response = client.post(
            "/api/v1/ecowallet/redeem",
            json={
                "user_id": "api_u3",
                "category": "consultation",
            },
        )
        assert response.status_code == 200
        assert response.json()["amount_redeemed"] == 20.0

    def test_ussd_balance(self):
        response = client.post(
            "/api/v1/ecowallet/ussd",
            json={
                "user_id": "ussd_u1",
                "action": "balance",
                "language": "fa",
            },
        )
        assert response.status_code == 200
        assert response.json()["action"] == "balance"

    def test_stats_endpoint(self):
        response = client.get("/api/v1/ecowallet/stats")
        assert response.status_code == 200
        assert "total_wallets" in response.json()

    def test_health_endpoint(self):
        response = client.get("/api/v1/ecowallet/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["features"]["external_exchange"] is False

    def test_main_health_has_ecowallet(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "ecowallet" in response.json()["modules"]
