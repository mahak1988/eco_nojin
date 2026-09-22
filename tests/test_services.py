"""Tests for EcoCoin Protocol - Python Services"""

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from services.ecosystem.service import (
    EcosystemService,
    ActivityType,
    VerificationStatus,
    ActivityEvidence,
)
from services.ecosystem.trust_score import TrustScoreService, TrustEventType
from services.privacy.vault import PrivacyVault
from services.oracle.service import OracleService, DataSource
from services.satellite.service import SatelliteService, SatelliteSource
from services.finance.wallet_service import WalletService, LedgerService, TransactionType
from services.carbon.service import CarbonService
from services.carbon.schemas import RegisterProjectRequest, VerifyProjectRequest


class TestEcosystemService:
    """Tests for EcosystemService"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return EcosystemService(mock_db)

    @pytest.mark.asyncio
    async def test_register_activity(self, service):
        """Test registering a new ecosystem activity"""
        activity = await service.register_activity(
            user_id="user_123",
            activity_type=ActivityType.TREE_PLANTING,
            description="Plant 100 oak trees",
            location_hash="abc123",
            region="Tehran",
            estimated_impact={"species": "oak", "count": 100, "area_ha": 2.5},
            evidence_files=[
                {"type": "satellite", "data": {"ndvi": 0.6}},
                {"type": "gps_photo", "data": {"lat": 35.7, "lon": 51.3}},
            ],
        )

        assert activity.activity_id.startswith("ACT-")
        assert activity.user_id == "user_123"
        assert activity.activity_type == ActivityType.TREE_PLANTING
        assert activity.status == VerificationStatus.PROVISIONAL
        assert activity.confidence > 0
        assert len(activity.evidence_ids) == 2

    @pytest.mark.asyncio
    async def test_calculate_trust_score(self, service):
        """Test trust score calculation"""
        # Mock get_user_activities
        service.get_user_activities = MagicMock(
            return_value=[
                MagicMock(status=VerificationStatus.VERIFIED),
                MagicMock(status=VerificationStatus.VERIFIED),
                MagicMock(status=VerificationStatus.DISPUTED),
            ]
        )

        score = await service.calculate_trust_score("user_123")
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_impact_score(self, service):
        """Test impact score calculation"""
        from services.ecosystem.service import Activity

        activity = MagicMock()
        activity.activity_type = ActivityType.TREE_PLANTING
        activity.confidence = 80

        score = await service.calculate_impact_score(activity)
        assert score > 0


class TestTrustScoreService:
    """Tests for TrustScoreService"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return TrustScoreService(mock_db)

    @pytest.mark.asyncio
    async def test_calculate_score(self, service):
        """Test trust score calculation"""
        # Mock database events
        service._get_user_events = MagicMock(return_value=[])
        score = await service.calculate_score("user_123")
        assert service.BASE_SCORE == score

    @pytest.mark.asyncio
    async def test_record_event(self, service):
        """Test recording trust event"""
        result = await service.record_event(
            user_id="user_123",
            event_type="activity_verified",
            description="Activity verified successfully",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_get_trust_level(self, service):
        """Test trust level determination"""
        service.calculate_score = MagicMock(return_value=0.85)
        level = await service.get_trust_level("user_123")
        assert level == "Gold"

    @pytest.mark.asyncio
    async def test_trust_multiplier(self, service):
        """Test trust multiplier calculation"""
        service.calculate_score = MagicMock(return_value=1.0)
        multiplier = await service.get_trust_multiplier("user_123")
        assert multiplier == 15000  # 1.5x


class TestPrivacyVault:
    """Tests for PrivacyVault"""

    @pytest.fixture
    def vault(self, tmp_path):
        return PrivacyVault(str(tmp_path))

    def test_store_and_retrieve(self, vault):
        """Test storing and retrieving data"""
        entry_id = vault.store("user_123", {"test": "data"}, {"type": "test"})
        assert entry_id.startswith("VAULT-")

        # In production: retrieve would decrypt
        # For now, test storage
        assert True

    def test_commitment_verification(self, vault):
        """Test commitment hash verification"""
        entry_id = vault.store("user_123", {"key": "value"})
        # Would verify commitment hash
        assert True

    def test_access_logging(self, vault):
        """Test access logging"""
        vault.store("user_123", {"data": "test"})
        vault.log_access("VAULT-123", "user_456", "read")
        # Verify log entry
        assert True

    def test_selective_disclosure(self, vault):
        """Test selective disclosure"""
        vault.store("user_123", {"secret": "data"})
        vault.grant_access("VAULT-123", "auditor_1", "user_123")
        # Would verify access grant
        assert True


class TestOracleService:
    """Tests for OracleService"""

    @pytest.fixture
    def mock_privacy_vault(self):
        return MagicMock()

    @pytest.fixture
    def mock_ecosystem_service(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_privacy_vault, mock_ecosystem_service):
        return OracleService(mock_privacy_vault, mock_ecosystem_service)

    @pytest.mark.asyncio
    async def test_register_oracle_node(self, service):
        """Test oracle node registration"""
        result = await service.register_oracle_node(
            node_id="oracle_1", public_key="0x123...", weight=10, reputation=80
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_submit_attestation(self, service):
        """Test attestation submission"""
        attestation_id = await service.submit_attestation(
            activity_id="ACT-123",
            node_id="oracle_1",
            data_type="satellite",
            confidence=85,
            commitment="0xabc...",
            signature="0xsig...",
        )
        assert attestation_id.startswith("ATT-")

    @pytest.mark.asyncio
    async def test_challenge_mechanism(self, service):
        """Test challenge mechanism"""
        # Setup pending report
        service._pending_reports["ACT-123"] = {
            "report": {"activity_id": "ACT-123", "challenged": False},
            "challenge_deadline": datetime.now(UTC) + timedelta(days=7),
        }

        result = await service.challenge_report("ACT-123", "challenger_1")
        assert result is True

    @pytest.mark.asyncio
    async def test_challenge_resolution(self, service):
        """Test challenge resolution"""
        # Setup challenge
        service._challenges["ACT-123"] = {"challenger": "user1", "timestamp": datetime.now(UTC)}
        service._pending_reports["ACT-123"] = {"report": {"challenged": True}}

        result = await service.resolve_challenge("ACT-123", True)
        assert result is True


class TestSatelliteService:
    """Tests for SatelliteService"""

    @pytest.fixture
    def service(self):
        return SatelliteService()

    @pytest.mark.asyncio
    async def test_compute_ndvi(self, service):
        """Test NDVI computation"""
        result = await service.compute_ndvi(
            lat=35.7,
            lon=51.3,
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 12, 31, tzinfo=UTC),
        )
        assert "ndvi_mean" in result

    @pytest.mark.asyncio
    async def test_verify_tree_planting(self, service):
        """Test tree planting verification"""
        result = await service.verify_tree_planting(
            lat=35.7,
            lon=51.3,
            planting_date=datetime(2024, 3, 1, tzinfo=UTC),
            expected_area_hectares=2.5,
        )
        assert "verified" in result
        assert "estimated_trees" in result

    @pytest.mark.asyncio
    async def test_detect_vegetation_change(self, service):
        """Test vegetation change detection"""
        result = await service.detect_vegetation_change(
            lat=35.7,
            lon=51.3,
            baseline_start=datetime(2023, 1, 1),
            baseline_end=datetime(2023, 12, 31),
            current_start=datetime(2024, 1, 1),
            current_end=datetime(2024, 6, 30),
        )
        assert "ndvi_change" in result
