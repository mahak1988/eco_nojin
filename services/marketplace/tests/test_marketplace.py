"""Tests for the Marketplace Hub Service — village development platform."""

from __future__ import annotations


class TestMarketplaceModels:
    def test_village_capability_model(self):
        from services.marketplace.models.village_hub import VillageCapability

        cap = VillageCapability(
            village_id="v-001",
            category="agriculture",
            subcategory="fruit",
            name="Apple Production",
            capacity_value=100.0,
            unit="tons",
        )
        assert cap.village_id == "v-001"
        assert cap.category == "agriculture"
        assert cap.name == "Apple Production"

    def test_village_investment_model(self):
        from services.marketplace.models.village_hub import VillageInvestment

        inv = VillageInvestment(
            project_id="p-001",
            investor_user_id="e-001",
            amount=50000000,
        )
        assert inv.project_id == "p-001"
        assert inv.investor_user_id == "e-001"
        assert inv.amount == 50000000

    def test_village_brand_model(self):
        from services.marketplace.models.village_hub import VillageBrand

        brand = VillageBrand(
            village_id="v-001",
            story="A sustainable village",
            values=["sustainability", "community"],
        )
        assert brand.village_id == "v-001"
        assert brand.story == "A sustainable village"
        assert "sustainability" in brand.values


class TestMarketplaceService:
    def test_service_initialization(self):
        from services.marketplace.hub_service import VillageDevelopmentHubService

        service = VillageDevelopmentHubService(db=None)
        assert service.db is None
        assert hasattr(service, "create_capability")
        assert hasattr(service, "create_opportunity")
        assert hasattr(service, "create_project")

    def test_governance_roles(self):
        from services.marketplace.hub_service import _GOVERNANCE_WRITE_ROLES

        assert "council_member" in _GOVERNANCE_WRITE_ROLES
        assert "landscape_manager" in _GOVERNANCE_WRITE_ROLES
