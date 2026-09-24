"""Impact Oracle Service - Multi-source verification for ecosystem restoration"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

from services.ecosystem.service import EcosystemService
from services.privacy.vault import PrivacyVault


class DataSource(Enum):
    SATELLITE = "satellite"
    GPS_PHOTO = "gps_photo"
    FIELD = "field"
    LAB = "lab"
    COMMUNITY = "community"


@dataclass
class OracleAttestation:
    attestation_id: str
    activity_id: str
    oracle_node: str
    data_type: str
    confidence: int
    timestamp: datetime
    commitment: str
    signature: str


@dataclass
class ImpactMetrics:
    confidence: int
    impact_score: int  # basis points
    trust_multiplier: int  # basis points
    survival_factor: int
    scarcity_factor: int
    challenge_deadline: datetime


class OracleService:
    """
    Multi-source verification oracle for ecosystem restoration activities.
    Aggregates attestations from multiple sources, computes impact metrics,
    manages challenge periods, and coordinates with on-chain contracts.
    """

    def __init__(self, privacy_vault: PrivacyVault, ecosystem_service: EcosystemService):
        self.privacy_vault = privacy_vault
        self.ecosystem_service = ecosystem_service
        self.registered_nodes = {}  # node_id -> {weight, reputation, public_key}
        self.challenge_window = timedelta(days=7)
        self.min_oracle_weight = 1
        self._pending_reports = {}
        self._challenges = {}

    async def register_oracle_node(
        self, node_id: str, public_key: str, weight: int = 1, reputation: int = 50
    ) -> bool:
        """Register a new oracle node"""
        if node_id in self.registered_nodes:
            return False
        self.registered_nodes[node_id] = {
            "public_key": public_key,
            "weight": weight,
            "reputation": reputation,
            "active": True,
            "stake": 0,
        }
        return True

    async def submit_attestation(
        self,
        activity_id: str,
        node_id: str,
        data_type: str,
        confidence: int,
        commitment: str,
        signature: str,
    ) -> str:
        """Submit an attestation from an oracle node"""
        if node_id not in self.registered_nodes:
            raise ValueError("Unknown oracle node")

        if confidence > 100:
            raise ValueError("Confidence exceeds maximum")

        attestation_id = f"ATT-{secrets.token_hex(8)}"
        {
            "attestation_id": attestation_id,
            "activity_id": activity_id,
            "node_id": node_id,
            "data_type": data_type,
            "confidence": confidence,
            "timestamp": datetime.now(UTC),
            "commitment": commitment,
            "signature": signature,
        }
        # Store attestation (in production: database)
        return attestation_id

    async def submit_impact_report(
        self,
        activity_id: str,
        reporter: str,
        data_type: str,
        confidence: int,
        impact_hash: str,
        evidence_commitment: str,
        methodology_version: int = 1,
    ) -> str:
        """Submit a complete impact report for an activity"""
        # Verify activity exists
        activity = await self.ecosystem_service.get_activity(activity_id)
        if not activity:
            raise ValueError("Activity not found")

        report_id = f"RPT-{secrets.token_hex(8)}"
        challenge_deadline = datetime.now(UTC) + timedelta(days=7)

        report = {
            "report_id": report_id,
            "activity_id": activity_id,
            "reporter": "oracle_service",
            "data_type": data_type,
            "confidence": confidence,
            "impact_hash": impact_hash,
            "evidence_commitment": evidence_commitment,
            "methodology_version": methodology_version,
            "timestamp": datetime.now(UTC),
            "challenged": False,
            "challenge_deadline": challenge_deadline,
        }
        self._pending_reports[activity_id] = {
            "report": report,
            "challenge_deadline": challenge_deadline,
        }
        return report_id

    async def challenge_report(self, activity_id: str, challenger: str) -> bool:
        """Challenge an impact report during challenge window"""
        if activity_id not in self._pending_reports:
            return False

        report = self._pending_reports[activity_id]["report"]
        if report["challenged"]:
            return False
        if datetime.now(UTC) > self._pending_reports[activity_id]["challenge_deadline"]:
            return False

        report["challenged"] = True
        self._challenges[activity_id] = {
            "challenger": "challenger",
            "timestamp": datetime.now(UTC),
        }
        return True

    async def resolve_challenge(self, activity_id: str, upheld: bool) -> bool:
        """Resolve a challenge (admin/DAO only)"""
        if activity_id not in self._challenges:
            return False

        # In production: would have DAO/governance resolution
        # For now, just mark resolved
        if activity_id in self._pending_reports:
            self._pending_reports[activity_id]["report"]["challenged"] = False
        if activity_id in self._challenges:
            del self._challenges[activity_id]
        return True

    async def finalize_impact_metrics(self, activity_id: str) -> dict | None:
        """Finalize impact metrics after challenge window"""
        if activity_id not in self._pending_reports:
            return None

        report = self._pending_reports[activity_id]["report"]
        if report["challenged"]:
            return None
        if datetime.now(UTC) <= self._pending_reports[activity_id]["challenge_deadline"]:
            return None

        # Compute aggregated metrics from all sources
        metrics = await self._compute_aggregated_metrics(activity_id)
        if metrics.confidence == 0:
            return None

        # Store finalized metrics
        finalized = {
            "activity_id": activity_id,
            "metrics": metrics,
            "finalized_at": datetime.now(UTC),
        }
        del self._pending_reports[activity_id]
        return finalized

    async def _compute_aggregated_metrics(self, activity_id: str) -> dict:
        """Compute aggregated impact metrics from all attestations"""
        # In production: aggregate multiple attestations, satellite data, field reports
        # This is a simplified version
        return {
            "confidence": 85,
            "impact_score": 5000,
            "trust_multiplier": 10000,
            "survival_factor": 10000,
            "scarcity_factor": 10000,
            "challenge_deadline": 0,
        }

    async def verify_satellite_data(self, activity_id: str, lat: float, lon: float) -> dict:
        """Verify activity using satellite data (Sentinel-2, etc.)"""
        # In production: query CDSE/Copernicus API for NDVI/EVI/SAVI
        # This is a placeholder
        return {
            "ndvi_change": 0.15,
            "vegetation_increase": True,
            "area_hectares": 2.5,
            "confidence": 80,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def verify_gps_photo(
        self, activity_id: str, lat: float, lon: float, photo_hash: str
    ) -> dict:
        """Verify GPS-tagged photo"""
        # In production: verify EXIF data, check location, check timestamp
        return {
            "location_match": True,
            "timestamp_valid": True,
            "confidence": 85,
        }

    async def verify_lab_certificate(self, certificate_hash: str, lab_id: str) -> dict:
        """Verify lab certificate (organic, soil, water quality)"""
        # In production: verify against lab registry
        return {
            "valid": True,
            "lab_verified": True,
            "parameters": {},
        }

    async def get_trust_multiplier(self, user_id: str) -> int:
        """Get trust multiplier for a user (basis points, 10000 = 1.0x)"""
        # Would query trust score service
        return 10000  # 1.0x default

    async def calculate_impact_score(self, activity_data: dict) -> int:
        """Calculate normalized impact score (0-10000 basis points)"""
        # In production: use ecological models, satellite data, survival models
        # This is a placeholder
        base_score = 5000
        return base_score
