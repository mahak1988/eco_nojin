"""Tests for rangeland service and router."""

from decimal import Decimal

import pytest

from services.rangeland.models import Rangeland
from services.rangeland.schemas import RangelandCreate, RangelandStats, RangelandUpdate


class TestRangelandModels:
    """Tests for rangeland models."""

    def test_rangeland_model_creation(self):
        """Test creating a Rangeland model instance."""
        from datetime import UTC, datetime
        rangeland = Rangeland(
            rangeland_id="RL-001",
            name="North Pasture",
            village_id="village-001",
            area_ha=Decimal("500.50"),
            vegetation_type="native_grassland",
            carrying_capacity_per_ha=Decimal("0.20"),
            usage_type="grazing",
            condition="good",
            productivity_index=Decimal("72.00"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert rangeland.rangeland_id == "RL-001"
        assert rangeland.name == "North Pasture"
        assert rangeland.village_id == "village-001"
        assert rangeland.area_ha == Decimal("500.50")
        assert rangeland.usage_type == "grazing"


class TestRangelandSchemas:
    """Tests for rangeland schemas."""

    def test_rangeland_create_schema(self):
        """Test RangelandCreate schema validation."""
        data = RangelandCreate(
            rangeland_id="RL-002",
            name="East Pasture",
            village_id="village-002",
            area_ha=Decimal("300.00"),
            carrying_capacity_per_ha=Decimal("0.15"),
            usage_type="grazing",
            condition="fair",
        )
        assert data.rangeland_id == "RL-002"
        assert data.name == "East Pasture"
        assert data.village_id == "village-002"
        assert data.area_ha == Decimal("300.00")

    def test_rangeland_create_rejects_negative_area(self):
        """Test RangelandCreate rejects a negative area."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RangelandCreate(
                rangeland_id="RL-003",
                name="Bad",
                village_id="village-003",
                area_ha=Decimal("-1"),
            )

    def test_rangeland_update_schema(self):
        """Test RangelandUpdate schema."""
        data = RangelandUpdate(
            name="Updated Pasture",
            condition="poor",
        )
        assert data.name == "Updated Pasture"
        assert data.condition == "poor"

    def test_rangeland_stats_schema(self):
        """Test RangelandStats schema."""
        data = RangelandStats(
            village_id="village-001",
            count=3,
            total_area_ha=Decimal("900.00"),
            condition_distribution={"good": 1, "fair": 2},
            usage_type_distribution={"grazing": 3},
        )
        assert data.village_id == "village-001"
        assert data.count == 3
        assert data.provenance["synthetic"] is False


class TestRangelandService:
    """Tests for RangelandService (requires database)."""

    @pytest.fixture
    def service(self, db_session):
        from services.rangeland.service import RangelandService
        return RangelandService(db_session)

    async def test_service_instantiation(self, service):
        """Test that service can be instantiated."""
        assert service is not None
        assert hasattr(service, 'create_rangeland')
        assert hasattr(service, 'get_rangeland')
        assert hasattr(service, 'list_rangelands')

    async def test_create_rangeland(self, service):
        """Test creating a rangeland."""
        rangeland_data = {
            "rangeland_id": "RL-TEST-001",
            "name": "Test Rangeland",
            "village_id": "village-001",
            "area_ha": Decimal("200.00"),
            "usage_type": "grazing",
            "condition": "good",
        }
        rangeland = await service.create_rangeland(**rangeland_data)
        assert rangeland is not None
        assert rangeland.name == "Test Rangeland"
        assert rangeland.village_id == "village-001"

    async def test_create_duplicate_rangeland_raises(self, service):
        """Test that a duplicate rangeland_id is rejected (not an IntegrityError)."""
        rangeland_data = {
            "rangeland_id": "RL-DUP-001",
            "name": "First",
            "village_id": "village-001",
            "area_ha": Decimal("100.00"),
        }
        await service.create_rangeland(**rangeland_data)
        with pytest.raises(ValueError, match="already exists"):
            await service.create_rangeland(**rangeland_data)

    async def test_get_rangeland(self, service):
        """Test retrieving a rangeland."""
        rangeland_data = {
            "rangeland_id": "RL-GET-001",
            "name": "Get Rangeland",
            "village_id": "village-001",
            "area_ha": Decimal("150.00"),
        }
        created = await service.create_rangeland(**rangeland_data)
        retrieved = await service.get_rangeland(created.rangeland_id)
        assert retrieved is not None
        assert retrieved.rangeland_id == created.rangeland_id

    async def test_list_rangelands(self, service):
        """Test listing rangelands."""
        rangelands = await service.list_rangelands(village_id="village-001")
        assert isinstance(rangelands, list)