"""EcoCoin Ecosystem Service - Core business logic for activity registration and verification"""

from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    EcoWallet,
    FinAccount,
    FinJournalBatch,
    FinJournalEntry,
    DailyEarnings,
)


class ActivityType(Enum):
    TREE_PLANTING = "tree_planting"
    SOIL_RESTORATION = "soil_restoration"
    WATER_CONSERVATION = "water_conservation"
    BIODIVERSITY = "biodiversity"
    CLEANUP = "cleanup"
    REGENERATIVE_FARMING = "regenerative_farming"
    CARBON_SEQUESTRATION = "carbon_sequestration"


class VerificationStatus(Enum):
    PENDING = "pending"
    PROVISIONAL = "provisional"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    REJECTED = "rejected"


@dataclass
class ActivityEvidence:
    """Off-chain evidence stored in Privacy Vault"""

    evidence_id: str
    activity_id: str
    user_id: str
    data_type: str  # satellite, gps_photo, field, lab, community
    encrypted_data: bytes
    commitment_hash: str  # SHA256 of raw data
    metadata: dict
    uploaded_at: datetime
    access_log: list = field(default_factory=list)


@dataclass
class Activity:
    """Ecosystem restoration activity"""

    activity_id: str
    user_id: str
    activity_type: ActivityType
    description: str
    location_hash: str  # geohash or hashed coordinates
    region: str
    estimated_impact: dict  # species, area, expected_survival, etc.
    evidence_ids: list[str]
    status: VerificationStatus
    confidence: int  # 0-100
    trust_score: float  # 0.0-1.0
    impact_score: float  # calculated by oracle
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None
    challenge_deadline: Optional[datetime] = None


class EcosystemService:
    """Core service for ecosystem restoration activities"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._privacy_vault = {}  # In production: encrypted DB or IPFS

    async def register_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        description: str,
        location_hash: str,
        region: str,
        estimated_impact: dict,
        evidence_files: list[dict],
    ) -> Activity:
        """Register a new ecosystem restoration activity"""

        # Generate activity ID
        activity_id = f"ACT-{uuid.uuid4().hex[:12].upper()}"

        # Store evidence in Privacy Vault
        evidence_ids = []
        for ev in evidence_files:
            evidence_id = f"EVI-{uuid.uuid4().hex[:10]}"
            raw_data = json.dumps(ev.get("data", {})).encode()
            commitment = hashlib.sha256(raw_data).hexdigest()

            evidence = ActivityEvidence(
                evidence_id=evidence_id,
                activity_id=activity_id,
                user_id=user_id,
                data_type=ev.get("type", "unknown"),
                encrypted_data=raw_data,  # In production: encrypt with user's key
                commitment_hash=commitment,
                metadata=ev.get("metadata", {}),
                uploaded_at=datetime.now(UTC),
            )
            self._privacy_vault[evidence_id] = evidence
            evidence_ids.append(evidence_id)

        # Calculate initial confidence based on evidence types
        confidence = self._calculate_initial_confidence(evidence_files)

        # Create activity record
        activity = Activity(
            activity_id=activity_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            location_hash=location_hash,
            region=region,
            estimated_impact=estimated_impact,
            evidence_ids=evidence_ids,
            status=VerificationStatus.PROVISIONAL,
            confidence=confidence,
            trust_score=0.5,  # Start neutral
            impact_score=0.0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Store in database (would use actual ORM model)
        # await self._save_activity(activity)

        return activity

    def _calculate_initial_confidence(self, evidence_files: list[dict]) -> int:
        """Calculate initial confidence based on evidence types"""
        weights = {
            "satellite": 30,
            "gps_photo": 25,
            "field": 20,
            "lab": 15,
            "community": 10,
        }
        total = sum(weights.get(e.get("type", "").lower(), 5) for e in evidence_files)
        return min(100, total)

    async def submit_evidence(
        self,
        activity_id: str,
        user_id: str,
        evidence_type: str,
        data: dict,
        metadata: dict = None,
    ) -> str:
        """Add additional evidence to existing activity"""
        # Verify ownership
        activity = await self.get_activity(activity_id)
        if activity.user_id != user_id:
            raise ValueError("Not activity owner")

        evidence_id = f"EVI-{uuid.uuid4().hex[:10]}"
        raw_data = json.dumps(data).encode()
        commitment = hashlib.sha256(raw_data).hexdigest()

        evidence = ActivityEvidence(
            evidence_id=evidence_id,
            activity_id=activity_id,
            user_id=user_id,
            data_type=evidence_type,
            encrypted_data=json.dumps(data).encode(),
            commitment_hash=commitment,
            metadata=metadata or {},
            uploaded_at=datetime.now(UTC),
        )
        self._privacy_vault[evidence_id] = evidence

        # Update activity
        activity = await self.get_activity(activity_id)
        activity.evidence_ids.append(evidence_id)
        activity.confidence = min(
            100, activity.confidence + self._evidence_confidence_boost(evidence_type)
        )
        activity.updated_at = datetime.now(UTC)

        return evidence_id

    def _evidence_confidence_boost(self, evidence_type: str) -> int:
        boosts = {
            "satellite": 15,
            "gps_photo": 10,
            "field": 10,
            "lab": 20,
            "community": 5,
        }
        return boosts.get(evidence_type.lower(), 5)

    async def get_activity(self, activity_id: str) -> Activity:
        """Retrieve activity by ID"""
        # In production: query database
        # For now, return mock
        return Activity(
            activity_id=activity_id,
            user_id="user_123",
            activity_type=ActivityType.TREE_PLANTING,
            description="Test activity",
            location_hash="abc123",
            region="test",
            estimated_impact={},
            evidence_ids=[],
            status=VerificationStatus.PROVISIONAL,
            confidence=50,
            trust_score=0.5,
            impact_score=0.0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def get_user_activities(
        self, user_id: str, status: VerificationStatus = None
    ) -> list[Activity]:
        """Get all activities for a user"""
        # In production: query database
        return []

    async def get_evidence(self, evidence_id: str, requester_id: str) -> Optional[ActivityEvidence]:
        """Retrieve evidence with access control"""
        evidence = self._privacy_vault.get(evidence_id)
        if not evidence:
            return None

        # Log access
        evidence.access_log.append(
            {
                "requester": requester_id,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # In production: check permissions
        return evidence

    async def grant_evidence_access(
        self, evidence_id: str, requester_id: str, granted_by: str
    ) -> bool:
        """Grant selective access to evidence (for VVB/auditors)"""
        evidence = self._privacy_vault.get(evidence_id)
        if not evidence:
            return False

        # In production: verify grantor has permission
        evidence.access_log.append(
            {
                "requester": requester_id,
                "granted_by": granted_by,
                "timestamp": datetime.now(UTC).isoformat(),
                "action": "access_granted",
            }
        )
        return True

    async def calculate_trust_score(self, user_id: str) -> float:
        """Calculate user trust score based on history"""
        activities = await self.get_user_activities(user_id)
        if not activities:
            return 0.5  # neutral

        total = len(activities)
        verified = sum(1 for a in activities if a.status == VerificationStatus.VERIFIED)
        disputed = sum(1 for a in activities if a.status == VerificationStatus.DISPUTED)
        rejected = sum(1 for a in activities if a.status == VerificationStatus.REJECTED)

        base = 0.5
        base += (verified / total) * 0.4
        base -= (disputed / total) * 0.15
        base -= (rejected / total) * 0.25

        return max(0.0, min(1.0, base))

    async def calculate_impact_score(self, activity: Activity) -> float:
        """Calculate ecological impact score for an activity"""
        # This would integrate with satellite data, soil models, etc.
        base = activity.confidence / 100.0

        # Factor in activity type
        type_multipliers = {
            ActivityType.TREE_PLANTING: 1.0,
            ActivityType.SOIL_RESTORATION: 1.2,
            ActivityType.WATER_CONSERVATION: 1.1,
            ActivityType.BIODIVERSITY: 1.15,
            ActivityType.CLEANUP: 0.8,
            ActivityType.REGENERATIVE_FARMING: 1.1,
            ActivityType.CARBON_SEQUESTRATION: 1.25,
        }

        multiplier = type_multipliers.get(activity.activity_type, 1.0)
        return activity.confidence / 100.0 * multiplier * 10000  # basis points
