"""Tests for provenance service and router."""

import pytest

from services.provenance.models import DataLineage, ModelVersion, ProvenanceRecord
from services.provenance.schemas import (
    LineageQuery,
    ModelVersionCreate,
    ProvenanceCreate,
)


class TestProvenanceModels:
    """Tests for provenance models."""

    def test_provenance_record_model_creation(self):
        """Test creating a ProvenanceRecord model instance."""
        record = ProvenanceRecord(
            provenance_type="scientific_output",
            output_id="output-123",
            output_type="carbon_sequestration",
            input_hashes=["abc123"],
            input_sources=[{"source": "sensor-1"}],
            model_version="v1.0",
            model_name="carbon_model_v1",
            algorithm_parameters={"threshold": 0.5},
            executed_by="user-123",
            uncertainty={"method": "monte_carlo", "stddev": 0.02},
            confidence_level="95%",
            is_validated=True,
            quality_score="high",
            is_reproducible=True,
        )
        assert record.provenance_type == "scientific_output"
        assert record.output_id == "output-123"
        assert record.model_version == "v1.0"
        assert record.is_validated is True

    def test_data_lineage_model_creation(self):
        """Test creating a DataLineage model instance."""
        lineage = DataLineage(
            input_provenance_id="input-001",
            output_provenance_id="output-001",
            transformation_type="model_inference",
            transformation_params={"model": "carbon_model"},
        )
        assert lineage.transformation_type == "model_inference"

    def test_model_version_model_creation(self):
        """Test creating a ModelVersion instance."""
        version = ModelVersion(
            name="carbon_model",
            version="1.0.0",
            description="Initial release",
            algorithm_class="HydromaCore.estimate_carbon",
            framework="custom",
            is_active=True,
        )
        assert version.name == "carbon_model"
        assert version.version == "1.0.0"
        assert version.is_active is True


class TestProvenanceSchemas:
    """Tests for provenance schemas."""

    def test_provenance_create_schema(self):
        """Test ProvenanceCreate schema validation."""
        data = ProvenanceCreate(
            provenance_type="data_transformation",
            output_id="etl-run-456",
            output_type="processed_soil",
            input_hashes=["deadbeef"],
            input_sources=[{"path": "/raw/soil.csv"}],
            model_version="1.0.0",
            model_name="etl_pipeline",
            algorithm_parameters={"delimiter": ","},
            executed_by="etl-service",
            uncertainty={"method": "none"},
            confidence_level="medium",
            is_validated=False,
            is_reproducible=True,
        )
        assert data.provenance_type == "data_transformation"
        assert data.output_id == "etl-run-456"
        assert data.model_name == "etl_pipeline"

    def test_provenance_create_rejects_unknown_type(self):
        """Test ProvenanceCreate rejects an unknown provenance type."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ProvenanceCreate(
                provenance_type="not_a_real_type",
                output_id="x",
                output_type="y",
                model_version="1.0.0",
                model_name="m",
            )

    def test_model_version_create_schema(self):
        """Test ModelVersionCreate schema."""
        data = ModelVersionCreate(
            name="carbon_model",
            version="1.3.0",
            description="Bug fix",
            algorithm_class="HydromaCore.estimate_carbon",
            framework="custom",
            created_by="test-user",
        )
        assert data.name == "carbon_model"
        assert data.version == "1.3.0"
        assert data.framework == "custom"

    def test_model_version_create_rejects_non_semver(self):
        """Test ModelVersionCreate rejects a non-semver version."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ModelVersionCreate(
                name="carbon_model",
                version="v1.3",
            )

    def test_lineage_query_schema(self):
        """Test LineageQuery schema."""
        data = LineageQuery(
            provenance_id="prov-001",
            direction="upstream",
            max_depth=3,
        )
        assert data.provenance_id == "prov-001"
        assert data.direction == "upstream"


class TestProvenanceService:
    """Tests for ProvenanceService (requires database)."""

    @pytest.fixture
    def service(self, db_session):
        from services.provenance.service import ProvenanceService
        return ProvenanceService(db_session)

    async def test_service_instantiation(self, service):
        """Test that service can be instantiated."""
        assert service is not None
        assert hasattr(service, 'create_provenance')
        assert hasattr(service, 'get_provenance')
        assert hasattr(service, 'list_provenance')

    async def test_create_provenance(self, service):
        """Test creating a provenance record."""
        record_data = {
            "provenance_type": "scientific_output",
            "output_id": "output-123",
            "output_type": "carbon_sequestration",
            "input_hashes": ["abc123"],
            "input_sources": [{"source": "sensor-1"}],
            "model_version": "v1.0",
            "model_name": "carbon_model_v1",
            "algorithm_parameters": {"threshold": 0.5},
            "executed_by": "user-123",
            "uncertainty": {"method": "monte_carlo"},
            "confidence_level": "95%",
            "is_validated": True,
            "is_reproducible": True,
        }
        record = await service.create_provenance(ProvenanceCreate(**record_data))
        assert record is not None
        assert record.output_id == "output-123"
        assert record.model_name == "carbon_model_v1"

    async def test_get_provenance(self, service):
        """Test retrieving a provenance record."""
        record_data = {
            "provenance_type": "model_inference",
            "output_id": "output-456",
            "output_type": "soil_moisture",
            "model_version": "v2.3",
            "model_name": "moisture_model",
            "executed_by": "inference-service",
        }
        created = await service.create_provenance(ProvenanceCreate(**record_data))
        retrieved = await service.get_provenance(str(created.id))
        assert retrieved is not None
        assert retrieved.output_id == "output-456"

    async def test_list_provenance(self, service):
        """Test listing provenance records."""
        records = await service.list_provenance(page=1, page_size=10)
        assert records is not None
        assert hasattr(records, "items")

    async def test_register_model_version(self, service):
        """Test registering a model version."""
        data = ModelVersionCreate(
            name="carbon_model",
            version="2.0.0",
            description="Second release",
            framework="custom",
        )
        version = await service.register_model_version(data, "test-user")
        assert version is not None
        assert version.name == "carbon_model"
        assert version.version == "2.0.0"


class TestProvenanceRouter:
    """Tests for provenance router endpoints."""

    def test_router_exists(self):
        """Test that router is defined."""
        from services.provenance.router import router as provenance_router
        assert provenance_router is not None