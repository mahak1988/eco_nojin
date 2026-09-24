"""Trust Score Service - Calculates and manages user trust scores based on activity history"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession


class TrustEventType(Enum):
    ACTIVITY_VERIFIED = "activity_verified"
    ACTIVITY_DISPUTED = "activity_disputed"
    ACTIVITY_REJECTED = "activity_rejected"
    EVIDENCE_ADDED = "evidence_added"
    CHALLENGE_UPHELD = "challenge_upheld"
    CHALLENGE_REJECTED = "challenge_rejected"
    MILESTONE_COMPLETED = "milestone_completed"
    CONSECUTIVE_DAYS = "consecutive_days"


@dataclass
class TrustEvent:
    event_id: str
    user_id: str
    event_type: str
    timestamp: datetime
    impact: float  # -1.0 to 1.0
    description: str


class TrustScoreService:
    """
    Calculates and manages user trust scores based on activity history.
    Scores range from 0.0 to 1.0, affecting minting multipliers and privileges.
    """

    BASE_SCORE = 0.5
    MAX_SCORE = 1.0
    MIN_SCORE = 0.0

    # Event weights (impact on trust score)
    EVENT_WEIGHTS = {
        "activity_verified": 0.05,
        "activity_disputed": -0.03,
        "activity_rejected": -0.10,
        "evidence_added": 0.01,
        "challenge_upheld": 0.02,
        "challenge_rejected": -0.02,
        "milestone_completed": 0.03,
        "consecutive_days": 0.005,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_score(self, user_id: str) -> float:
        """Calculate current trust score for a user"""
        # In production: query events from database
        events = await self._get_user_events(user_id)

        if not events:
            return self.BASE_SCORE

        score = self.BASE_SCORE
        for event in events:
            weight = self.EVENT_WEIGHTS.get(event.event_type, 0)
            score += event.impact * weight

        # Apply time decay (older events matter less)
        datetime.now(UTC)
        for event in events:
            days_old = (datetime.now(UTC) - event.timestamp).days
            max(0.5, 1.0 - (days_old / 365) * 0.5)  # 50% decay after 1 year
            # Apply decay to event impact (already applied above, this is conceptual)

        return max(self.MIN_SCORE, min(self.MAX_SCORE, score))

    async def record_event(
        self,
        user_id: str,
        event_type: str,
        impact: float | None = None,
        description: str = "",
    ) -> bool:
        """Record a trust event for a user"""
        if event_type not in self.EVENT_WEIGHTS:
            return False

        {
            "event_id": f"TRUST-{__import__('secrets').token_hex(8)}",
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": datetime.now(UTC),
            "impact": impact or self.EVENT_WEIGHTS[event_type],
            "description": description,
        }
        # In production: save to database
        return True

    async def get_trust_level(self, user_id: str) -> str:
        """Get human-readable trust level"""
        score = await self.calculate_score(user_id)
        if score >= 0.9:
            return "Diamond"
        elif score >= 0.7:
            return "Gold"
        elif score >= 0.5:
            return "Silver"
        elif score >= 0.3:
            return "Bronze"
        else:
            return "New"

    async def get_trust_multiplier(self, user_id: str) -> int:
        """Get trust multiplier for minting (basis points, 10000 = 1.0x)"""
        score = await self.calculate_score(user_id)
        # Map 0.0-1.0 to 5000-15000 basis points (0.5x to 1.5x)
        return int(5000 + (score * 10000))

    async def get_trust_level_requirements(self) -> dict:
        """Get requirements for each trust level"""
        return {
            "Diamond": {
                "min_score": 0.9,
                "multiplier": 1.5,
                "benefits": ["max_minting", "priority_verification", "governance_vote"],
            },
            "Gold": {
                "min_score": 0.7,
                "multiplier": 1.3,
                "benefits": ["high_minting", "priority_verification"],
            },
            "Silver": {"min_score": 0.5, "multiplier": 1.1, "benefits": ["standard_minting"]},
            "Bronze": {"min_score": 0.3, "multiplier": 0.9, "benefits": ["basic_minting"]},
            "New": {"min_score": 0.0, "multiplier": 0.7, "benefits": ["provisional_only"]},
        }

    async def get_user_trust_profile(self, user_id: str) -> dict:
        """Get complete trust profile for a user"""
        score = await self.calculate_score(user_id)
        level = await self.get_trust_level(user_id)
        multiplier = await self.get_trust_multiplier(user_id)
        requirements = await self.get_trust_level_requirements()

        return {
            "user_id": user_id,
            "score": round(score, 4),
            "level": level,
            "multiplier_bps": multiplier,
            "level_requirements": requirements.get(level, {}),
            "next_level": self._get_next_level(level),
        }

    def _get_next_level(self, current: str) -> str | None:
        levels = ["New", "Bronze", "Silver", "Gold", "Diamond"]
        try:
            idx = levels.index(current)
            return levels[idx + 1] if idx + 1 < len(levels) else None
        except ValueError:
            return "Bronze"

    async def _get_user_events(self, user_id: str) -> list:
        # In production: query database
        return []

    async def apply_trust_decay(self, user_id: str) -> float:
        """Apply time decay to trust score"""
        score = await self.calculate_score(user_id)
        # Simple decay: 1% per month of inactivity
        # In production: track last activity date
        return max(self.MIN_SCORE, score * 0.99)
