"""Pydantic schemas for Oracle Challenge API."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ChallengeStatus(StrEnum):
    PENDING = "pending"
    UPHELD = "upheld"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OracleChallengeCreate(BaseModel):
    """Request to create a challenge against an impact report."""

    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(..., min_length=1, max_length=64, description="Activity ID being challenged")
    challenger: str = Field(..., min_length=1, max_length=64, description="Challenger identifier")
    reason: str | None = Field(None, max_length=2000, description="Reason for challenge")


class OracleChallengeUpdate(BaseModel):
    """Request to resolve a challenge (admin/DAO)."""

    model_config = ConfigDict(extra="forbid")

    upheld: bool = Field(..., description="Whether challenge is upheld (true) or rejected (false)")
    resolution_notes: str | None = Field(None, max_length=2000, description="Resolution reasoning")


class OracleChallengeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    challenge_id: str
    activity_id: str
    challenger: str
    timestamp: datetime
    upheld: bool | None = None
    resolved_at: datetime | None = None
    status: ChallengeStatus


class OracleChallengeListResponse(BaseModel):
    items: list[OracleChallengeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OracleImpactReportCreate(BaseModel):
    """Request to submit an impact report for challenge."""

    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(..., min_length=1, max_length=64)
    reporter: str = Field(..., min_length=1, max_length=64)
    data_type: str = Field(..., min_length=1, max_length=32)
    confidence: int = Field(..., ge=0, le=100)
    impact_hash: str = Field(..., min_length=1, max_length=64)
    evidence_commitment: str = Field(..., min_length=1, max_length=64)
    methodology_version: int = Field(1, ge=1)
    challenge_window_days: int = Field(7, ge=1, le=30)


class OracleImpactReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: str
    activity_id: str
    reporter: str
    data_type: str
    confidence: int
    impact_hash: str
    evidence_commitment: str
    methodology_version: int
    timestamp: datetime
    challenged: bool
    challenge_deadline: datetime | None = None


class OracleImpactMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_id: str
    confidence: int
    impact_score: int
    trust_multiplier: int
    survival_factor: int
    scarcity_factor: int
    challenge_deadline: datetime | None = None
    created_at: datetime


# Forward references
OracleChallengeResponse.model_rebuild()
OracleImpactReportResponse.model_rebuild()
OracleImpactMetricsResponse.model_rebuild()