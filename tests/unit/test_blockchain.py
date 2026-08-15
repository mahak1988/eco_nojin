"""Tests for Blockchain Ledger module."""

import pytest
from fastapi.testclient import TestClient

from engine.hydroma.blockchain.carbon_registry import (
    CarbonRegistry,
    ProjectStatus,
)
from engine.hydroma.blockchain.supply_chain import SupplyChainRegistry
from engine.hydroma.blockchain.web3_provider import get_web3_provider
from services.api_gateway.main import app

client = TestClient(app)


class TestWeb3Provider:
    """Test Web3 provider."""

    def test_connect_to_blockchain(self):
        """Verify connection to test blockchain."""
        provider = get_web3_provider()
        w3 = provider.connect()
        assert w3.is_connected()

    def test_get_accounts(self):
        """Verify test accounts are available."""
        provider = get_web3_provider()
        accounts = provider.get_accounts()
        assert len(accounts) > 0


class TestCarbonRegistry:
    """Test carbon credit registry."""

    def test_register_project(self):
        """Verify project registration."""
        registry = CarbonRegistry()
        project = registry.register_project(
            owner="owner1",
            project_type="afforestation",
            area_ha=100,
            duration_years=10,
        )

        assert project.project_id.startswith("proj_")
        assert project.owner == "owner1"
        assert project.status == ProjectStatus.SUBMITTED
        assert project.tx_hash.startswith("0x")

    def test_verify_project(self):
        """Verify project verification."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)

        verified = registry.verify_project(project.project_id, "verifier1")
        assert verified.status == ProjectStatus.VERIFIED
        assert verified.verifier == "verifier1"
        assert verified.verified_at is not None

    def test_verify_invalid_status(self):
        """Verify cannot verify non-submitted project."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")

        with pytest.raises(ValueError):
            registry.verify_project(project.project_id, "verifier2")

    def test_issue_credits(self):
        """Verify credit issuance."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")

        credit = registry.issue_credits(project.project_id, 50.0, "owner1")

        assert credit.credit_id.startswith("cred_")
        assert credit.amount == 50.0
        assert credit.owner == "owner1"
        assert project.credits_issued == 50.0

    def test_issue_credits_unverified_project(self):
        """Verify cannot issue credits for unverified project."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)

        with pytest.raises(ValueError):
            registry.issue_credits(project.project_id, 50.0, "owner1")

    def test_transfer_credits(self):
        """Verify credit transfer."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")
        credit = registry.issue_credits(project.project_id, 50.0, "owner1")

        transferred = registry.transfer_credits(credit.credit_id, "owner1", "owner2")

        assert transferred.owner == "owner2"

    def test_transfer_wrong_owner(self):
        """Verify cannot transfer credits not owned."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")
        credit = registry.issue_credits(project.project_id, 50.0, "owner1")

        with pytest.raises(ValueError):
            registry.transfer_credits(credit.credit_id, "wrong_owner", "owner2")

    def test_retire_credits(self):
        """Verify credit retirement."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")
        credit = registry.issue_credits(project.project_id, 50.0, "owner1")

        retired = registry.retire_credits(credit.credit_id, "owner1")

        assert retired.retired is True
        assert retired.retired_at is not None
        assert project.credits_retired == 50.0

    def test_retire_already_retired(self):
        """Verify cannot retire already retired credits."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")
        credit = registry.issue_credits(project.project_id, 50.0, "owner1")
        registry.retire_credits(credit.credit_id, "owner1")

        with pytest.raises(ValueError):
            registry.retire_credits(credit.credit_id, "owner1")

    def test_get_stats(self):
        """Verify registry statistics."""
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")
        registry.issue_credits(project.project_id, 50.0, "owner1")

        stats = registry.get_stats()

        assert stats["total_projects"] == 1
        assert stats["active_projects"] == 1
        assert stats["total_credits"] == 1
        assert stats["total_carbon_issued_tonnes"] == 50.0


class TestSupplyChainRegistry:
    """Test supply chain traceability."""

    def test_register_product(self):
        """Verify product registration."""
        registry = SupplyChainRegistry()
        product = registry.register_product(
            producer="producer1",
            batch_number="BATCH001",
            initial_event="harvested",
            location="Golestan",
        )

        assert product.product_id.startswith("prod_")
        assert product.producer == "producer1"
        assert len(product.events) == 1
        assert product.events[0].event_type == "harvested"

    def test_add_trace_event(self):
        """Verify adding trace events."""
        registry = SupplyChainRegistry()
        product = registry.register_product("producer1", "BATCH001")

        event = registry.add_event(
            product_id=product.product_id,
            event_type="processed",
            location="Processing Center",
            actor="processor1",
            notes="Quality check passed",
        )

        assert event.event_type == "processed"
        assert len(product.events) == 2

    def test_verify_product(self):
        """Verify product verification."""
        registry = SupplyChainRegistry()
        product = registry.register_product("producer1", "BATCH001")

        verified = registry.verify_product(product.product_id)

        assert verified.verified is True
        assert verified.verified_at is not None

    def test_get_product_history(self):
        """Verify getting product history."""
        registry = SupplyChainRegistry()
        product = registry.register_product("producer1", "BATCH001")
        registry.add_event(product.product_id, "processed", "Center", "actor1")

        history = registry.get_product_history(product.product_id)

        assert len(history) == 2
        assert history[0].event_type == "harvested"
        assert history[1].event_type == "processed"


class TestBlockchainAPIEndpoints:
    """Test blockchain API endpoints."""

    def test_register_carbon_project_endpoint(self):
        """Verify carbon project registration endpoint."""
        response = client.post(
            "/api/v1/blockchain/carbon/projects",
            json={
                "owner": "api_owner1",
                "project_type": "afforestation",
                "area_ha": 100,
                "duration_years": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["owner"] == "api_owner1"
        assert data["status"] == "submitted"

    def test_verify_carbon_project_endpoint(self):
        """Verify carbon project verification endpoint."""
        # Register first
        reg = client.post(
            "/api/v1/blockchain/carbon/projects",
            json={
                "owner": "api_owner2",
                "project_type": "reforestation",
                "area_ha": 50,
                "duration_years": 15,
            },
        )
        project_id = reg.json()["project_id"]

        # Verify
        response = client.post(
            f"/api/v1/blockchain/carbon/projects/{project_id}/verify",
            json={
                "verifier": "api_verifier",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "verified"

    def test_register_supply_chain_product_endpoint(self):
        """Verify supply chain product registration endpoint."""
        response = client.post(
            "/api/v1/blockchain/supply-chain/products",
            json={
                "producer": "api_producer",
                "batch_number": "BATCH_API_001",
                "initial_event": "harvested",
                "location": "Test Farm",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["producer"] == "api_producer"
        assert data["events_count"] == 1

    def test_blockchain_health_endpoint(self):
        """Verify blockchain health endpoint."""
        response = client.get("/api/v1/blockchain/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["features"]["carbon_registry"] is True
        assert data["features"]["supply_chain"] is True

    def test_main_health_reports_blockchain(self):
        """Verify main health endpoint reports blockchain module."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "blockchain" in data["modules"]
        assert data["blockchain"]["enabled"] is True
