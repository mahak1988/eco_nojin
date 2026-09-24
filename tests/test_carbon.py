"""Tests for Carbon Credit Service"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.carbon.schemas import (
    IssueCreditsRequest,
    RegisterProjectRequest,
    VerifyProjectRequest,
)
from services.carbon.service import CarbonService


class TestCarbonService:
    """Tests for CarbonService"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        service = CarbonService(mock_db)
        service._run_motor = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_register_project(self, service):
        """Test project registration"""
        req = RegisterProjectRequest(
            project_id="PROJ-001",
            name="Reforestation Project",
            owner_id="owner_123",
            geometry="POLYGON((...))",
            methodology="VM0042",
            standard="VCS",
            baseline_activity="degraded_land",
            has_financing=False,
            duration_years=30,
            soc_initial_t_ha=Decimal("50"),
        )

        # Mock database
        service.db.scalar = AsyncMock(return_value=None)
        service.db.add = MagicMock()
        service.db.flush = AsyncMock()

        result = await service.register_project(req)
        assert result["project_id"] == "PROJ-001"
        assert result["status"] == "registered"

    @pytest.mark.asyncio
    async def test_duplicate_project(self, service):
        """Test duplicate project registration"""
        req = RegisterProjectRequest(
            project_id="PROJ-001",
            name="Project",
            owner_id="owner_123",
            geometry="POLYGON((...))",
            methodology="VM0042",
            standard="VCS",
            baseline_activity="degraded_land",
            has_financing=False,
            duration_years=30,
        )

        # Mock existing project
        existing_project = MagicMock()
        existing_project.project_id = "PROJ-001"
        service.db.scalar = AsyncMock(return_value=existing_project)

        result = await service.register_project(req)
        assert result["status"] == "already_exists"

    @pytest.mark.asyncio
    async def test_verify_project(self, service):
        """Test project verification"""
        req = VerifyProjectRequest(
            project_id="PROJ-001",
            baseline_activity="degraded_land",
            has_financing=False,
        )

        # Mock project
        project = MagicMock()
        project.project_id = "PROJ-001"
        project.verification_status = "unverified"
        project.field_verified = False
        project.mrv_documents = []
        project.status = "SUBMITTED"
        project.user_id = "owner_123"

        service.db.scalar = AsyncMock(return_value=MagicMock(project_id="PROJ-001"))
        service._run_motor = MagicMock(
            return_value=MagicMock(
                status=MagicMock(value="completed"),
                outputs={"data_mode": "modelled_estimate", "certified_delta_co2e_total": 1000},
            )
        )

        result = await service.verify_project(req)
        assert result["project_id"] == "PROJ-001"
        assert "checks" in result

    @pytest.mark.asyncio
    async def test_issue_credits_not_verified(self, service):
        """Test issuing credits for unverified project"""
        req = IssueCreditsRequest(
            project_id="PROJ-001",
            idempotency_key="idem-123",
            issued_by="verifier_123",
        )

        project = MagicMock()
        project.project_id = "PROJ-001"
        project.verification_status = "unverified"
        project.field_verified = False
        project.mrv_documents = []

        service.db.scalar = AsyncMock(return_value=MagicMock(project_id="PROJ-001"))

        with pytest.raises(Exception):
            await service.issue_credits(req)

    @pytest.mark.asyncio
    async def test_issue_credits_field_verified(self, service):
        """Test issuing credits for field verified project"""
        req = IssueCreditsRequest(
            project_id="PROJ-001",
            idempotency_key="idem-123",
            issued_by="verifier_123",
        )

        project = MagicMock()
        project.project_id = "PROJ-001"
        project.verification_status = "verified"
        project.field_verified = True
        project.mrv_documents = ["doc1", "doc2"]
        project.user_id = "owner_123"
        project.methodology = "VM0042"
        project.standard = "VCS"

        service.db.scalar = AsyncMock(return_value=MagicMock(project_id="PROJ-001"))
        service._run_motor = MagicMock(
            return_value=MagicMock(
                status=MagicMock(value="completed"),
                outputs={"data_mode": "field_verified", "certified_delta_co2e_total": 1000},
            )
        )

        result = await service.issue_credits(req)
        assert "credit_id" in result
        assert result["data_mode"] == "field_verified"

    @pytest.mark.asyncio
    async def test_transfer_credit(self, service):
        """Test credit transfer"""
        from services.carbon.schemas import TransferRequest

        req = TransferRequest(
            credit_id="CR-123",
            from_holder="holder_1",
            to_holder="holder_2",
            amount=Decimal("100"),
            idempotency_key="idem-456",
        )

        credit = MagicMock()
        credit.credit_id = "CR-123"
        credit.holder_id = "holder_1"
        credit.state = "ACTIVE"
        credit.available_amount = Decimal("200")
        credit.version = 1

        service.db.scalar = AsyncMock(return_value=MagicMock())
        service._get_idempotency = MagicMock(return_value=None)

        result = await service.transfer_credit(req)
        assert result["credit_id"] == "CR-123"
        assert result["new_holder"] == "holder_2"

    @pytest.mark.asyncio
    async def test_retire_credit(self, service):
        """Test credit retirement"""
        from services.carbon.schemas import RetireRequest

        req = RetireRequest(
            credit_id="CR-123",
            holder_id="holder_1",
            amount=Decimal("50"),
            retirement_reason="Carbon offset",
            idempotency_key="idem-789",
        )

        credit = MagicMock()
        credit.credit_id = "CR-123"
        credit.holder_id = "holder_1"
        credit.state = "ACTIVE"
        credit.frozen = False
        credit.available_amount = Decimal("100")
        credit.retired_amount = Decimal("0")
        credit.version = 1

        service.db.scalar = AsyncMock(return_value=MagicMock())
        service._get_idempotency = MagicMock(return_value=None)

        result = await service.retire_credit(req)
        assert result["credit_id"] == "CR-123"
        assert result["retired_amount"] == "50"
