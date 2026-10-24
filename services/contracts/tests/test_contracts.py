"""Tests for contracts service and router."""

import pytest

from services.contracts.models import ContractTestRun, ContractVersionModel
from services.contracts.schemas import CompatibilityResult, ContractCreate, ContractResponse


class TestContractsModels:
    """Tests for contracts models."""

    def test_contract_version_model_creation(self):
        """Test creating a ContractVersionModel instance."""
        version = ContractVersionModel(
            service_name="test-service",
            version="1.0.0",
            contract_type="openapi",
            spec={"openapi": "3.0.0", "info": {"title": "Test API"}},
            is_active=True,
        )
        assert version.service_name == "test-service"
        assert version.version == "1.0.0"
        assert version.contract_type == "openapi"
        assert version.is_active is True

    def test_contract_test_run_model_creation(self):
        """Test creating a ContractTestRun instance."""
        test_run = ContractTestRun(
            contract_version_id="type-001",
            test_type="schemathesis",
            test_tool="schemathesis",
            status="passed",
            passed=10,
            failed=0,
            error_details={"party_a": "exists", "party_b": "exists"},
        )
        assert test_run.contract_version_id == "type-001"
        assert test_run.test_type == "schemathesis"
        assert test_run.status == "passed"


class TestContractsSchemas:
    """Tests for contracts schemas."""

    def test_contract_create_schema(self):
        """Test ContractCreate schema validation."""
        data = ContractCreate(
            service_name="test-service",
            version="1.0.0",
            contract_type="openapi",
            spec={"openapi": "3.0.0", "info": {"title": "Test API"}},
            supersedes=None,
            created_by="test-user",
        )
        assert data.service_name == "test-service"
        assert data.version == "1.0.0"
        assert data.contract_type == "openapi"

    def test_contract_create_rejects_bad_version(self):
        """Test ContractCreate rejects a non-semver version."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ContractCreate(
                service_name="test-service",
                version="not-a-version",
                spec={},
            )

    def test_contract_response_schema(self):
        """Test ContractResponse schema."""
        from datetime import datetime
        data = ContractResponse(
            id="test-id",
            service_name="test-service",
            version="1.0.0",
            contract_type="openapi",
            is_active=True,
            created_at=datetime.now(),
            deprecated_at=None,
            supersedes=None,
        )
        assert data.id == "test-id"
        assert data.service_name == "test-service"
        assert data.is_active is True

    def test_compatibility_result_schema(self):
        """Test CompatibilityResult schema."""
        data = CompatibilityResult(
            from_version="1.0.0",
            to_version="2.0.0",
            compatibility="backward",
            breaking_changes=[{"path": "/users", "change": "removed"}],
            safe_changes=[{"path": "/health", "change": "added"}],
            can_upgrade=True,
            warnings=["Breaking changes detected"],
        )
        assert data.from_version == "1.0.0"
        assert data.compatibility == "backward"
        assert data.can_upgrade is True


class TestContractsService:
    """Tests for ContractRegistry (requires database)."""

    @pytest.fixture
    def service(self, db_session):
        from services.contracts.service import ContractRegistry
        return ContractRegistry(db_session)

    async def test_service_instantiation(self, service):
        """Test that service can be instantiated."""
        assert service is not None
        assert hasattr(service, 'register_contract')
        assert hasattr(service, 'get_contract')
        assert hasattr(service, 'list_contracts')

    async def test_register_contract(self, service):
        """Test registering a contract version."""
        contract_data = {
            "service_name": "test-service",
            "version": "1.0.0",
            "contract_type": "openapi",
            "spec": {"openapi": "3.0.0", "info": {"title": "Test API"}},
            "created_by": "test-user",
        }
        contract = await service.register_contract(ContractCreate(**contract_data))
        assert contract is not None
        assert contract.service_name == "test-service"
        assert contract.version == "1.0.0"
        assert contract.is_active is True

    async def test_get_contract(self, service):
        """Test retrieving a contract version."""
        contract_data = {
            "service_name": "test-service-2",
            "version": "1.0.0",
            "contract_type": "openapi",
            "spec": {"openapi": "3.0.0", "info": {"title": "Test API 2"}},
        }
        await service.register_contract(ContractCreate(**contract_data))
        retrieved = await service.get_contract("test-service-2", "1.0.0")
        assert retrieved is not None
        assert retrieved["service_name"] == "test-service-2"
        assert retrieved["version"] == "1.0.0"

    async def test_get_active_contract(self, service):
        """Test retrieving the active contract for a service."""
        contract_data = {
            "service_name": "test-service-3",
            "version": "2.0.0",
            "contract_type": "openapi",
            "spec": {"openapi": "3.0.0", "info": {"title": "Test API 3"}},
        }
        await service.register_contract(ContractCreate(**contract_data))
        active = await service.get_active_contract("test-service-3")
        assert active is not None
        assert active["version"] == "2.0.0"
        assert active["is_active"] is True

    async def test_list_contracts(self, service):
        """Test listing contracts."""
        contracts = await service.list_contracts(page=1, page_size=10)
        assert isinstance(contracts, list)


class TestContractsRouter:
    """Tests for contracts router endpoints."""

    def test_router_exists(self):
        """Test that router is defined."""
        from services.contracts.router import router as contracts_router
        assert contracts_router is not None