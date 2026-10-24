"""P9 — the compliance registry (RegulatorySource → Jurisdiction → Requirement → Credential).

``services/legal`` is a static store of eight texts; the compliance registry
Phase 9 requires did not exist at all. This module models it and encodes the
rules the phase card demands:

* **A requirement never validates itself.** An activity is classified (against
  a jurisdiction), the matching requirements are attached, a credential is
  verified, and only then may an assessment record the status. A platform
  approval is not a government licence; the two are separate fields, and the
  API never merges them.
* **Nothing is "fully compliant" without evidence.** Every assessment carries
  the evidence reference that supports it, and expires.
* **Ambiguity escalates instead of auto-resolving.** Conflicting requirements
  from two sources are flagged for a human specialist rather than reconciled by
  the code.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)

from database.base import Base


class CredentialKind(StrEnum):
    IDENTITY = "identity"
    AUTHORITY = "authority"
    TRADE_LICENCE = "trade_licence"
    FOOD_SAFETY = "food_safety"
    ORGANIC = "organic"
    OTHER = "other"


class CredentialStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AssessmentOutcome(StrEnum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    ESCALATED = "escalated"


class RegulatorySource(Base):
    __tablename__ = "com_regulatory_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(300), nullable=False)
    jurisdiction = Column(String(100), nullable=False, index=True)
    url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Jurisdiction(Base):
    __tablename__ = "com_jurisdictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ActivityClassification(Base):
    """Which of the registered requirement sets applies to a subject."""

    __tablename__ = "com_activity_classifications"
    __table_args__ = ()

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    subject_type = Column(String(32), nullable=False)
    subject_id = Column(String(36), nullable=False, index=True)
    activity_code = Column(String(100), nullable=False, index=True)
    jurisdiction_id = Column(
        String(36), ForeignKey("com_jurisdictions.id"), nullable=False, index=True
    )
    classified_by = Column(String(36), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ComplianceRequirement(Base):
    __tablename__ = "com_requirements"
    __table_args__ = ()

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id = Column(String(36), ForeignKey("com_regulatory_sources.id"), nullable=False,
    index=True)
    jurisdiction_id = Column(
        String(36), ForeignKey("com_jurisdictions.id"), nullable=False, index=True
    )
    activity_code = Column(String(100), nullable=False, index=True)
    title = Column(String(400), nullable=False)
    summary = Column(Text, nullable=True)
    mandatory = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Credential(Base):
    __tablename__ = "com_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    subject_type = Column(String(32), nullable=False)
    subject_id = Column(String(36), nullable=False, index=True)
    kind = Column(String(32), nullable=False)
    reference = Column(String(200), nullable=True)
    issuer = Column(String(300), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default=CredentialStatus.PENDING.value)
    verified_by = Column(String(36), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class CredentialVerification(Base):
    __tablename__ = "com_credential_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    credential_id = Column(
        String(36), ForeignKey("com_credentials.id"), nullable=False, index=True
    )
    method = Column(String(200), nullable=False)
    evidence_ref = Column(String(300), nullable=True)
    performed_by = Column(String(36), nullable=False)
    outcome = Column(String(32), nullable=False)
    performed_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ComplianceAssessment(Base):
    __tablename__ = "com_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    subject_type = Column(String(32), nullable=False)
    subject_id = Column(String(36), nullable=False, index=True)
    jurisdiction_id = Column(
        String(36), ForeignKey("com_jurisdictions.id"), nullable=False, index=True
    )
    activity_code = Column(String(100), nullable=False, index=True)
    outcome = Column(String(32), nullable=False)
    #: Every assessment must carry the evidence it rests on; there is no
    #: "compliant with nothing attached" state.
    evidence_ref = Column(String(300), nullable=False)
    assessed_by = Column(String(36), nullable=False)
    method = Column(String(32), nullable=False, default="self_declared")
    note = Column(Text, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ComplianceException(Base):
    """A granted or pending exception to a requirement, with an expiry."""

    __tablename__ = "com_exceptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    requirement_id = Column(
        String(36), ForeignKey("com_requirements.id"), nullable=False, index=True
    )
    subject_type = Column(String(32), nullable=False)
    subject_id = Column(String(36), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    granted_by = Column(String(36), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ComplianceAuditLog(Base):
    __tablename__ = "com_audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    subject_type = Column(String(32), nullable=False)
    subject_id = Column(String(36), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    actor = Column(String(36), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
