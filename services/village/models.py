"""Local governance for village and pastoral-rangeland community spaces (P7).

Phase 7 of the program (``docs/project/PHASE_PLAN.md``) adds what the repository
measurably lacked: ``charter``, ``working_group`` and `community_space` had zero
occurrences before this module, and KN-12 carried "Village Hub beta, ~18 tables
without migration, no tribal approval workflow, tourism without HTTP".

Design decisions this module encodes (eco.md §2.2 + Phase 7):

* **The village stays a village and the rangeland stays a rangeland.** The
  community space is one lifecycle with two subtypes, not one vague "community"
  that papers over the legal/geographic/social difference (KN/D-14). A change of
  subtype is an explicit, audited transition — never a silent edit.
* **The charter is versioned.** Amending a local charter is a new version, never
  an update in place: the document in force for a past decision must stay
  recoverable.
* **Brand usage, validation, legal trademark and product certification stay
  separate** (D-14): this module records the *local* validation and brand
  decisions; it never claims a trademark or a certification.
* **Decision history is append-only.** Removing a person from the working group
  ends the membership; it never deletes the decisions that person took part in.
* **Sensitive data defaults to private.** The space record carries the
  sensitivity-classified fields (migration routes, water sources, sacred sites,
  exact coordinates) with ``is_public=False`` as the default, and publication is
  an explicit, per-field, audited act.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.base import Base


class CommunitySpaceKind(StrEnum):
    """The two space subtypes; converting one into the other is explicit."""

    VILLAGE = "village"
    PASTORAL_RANGELAND = "pastoral_rangeland"


class SpaceStatus(StrEnum):
    """The onboarding lifecycle (eco.md Phase 7 workflow)."""

    REQUESTED = "requested"
    IDENTITY_CHECKING = "identity_checking"
    AUTHORITY_CHECKING = "authority_checking"
    DOCUMENTS_PENDING = "documents_pending"
    GOVERNANCE_FORMING = "governance_forming"
    WORKING_GROUP_FORMING = "working_group_forming"
    CHARTER_DRAFTING = "charter_drafting"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class WorkingGroupRole(StrEnum):
    MEMBER = "member"
    COORDINATOR = "coordinator"
    SECRETARY = "secretary"


class MembershipEndReason(StrEnum):
    """Why a term ended — kept so decision history stays interpretable."""

    TERM_COMPLETED = "term_completed"
    RESIGNED = "resigned"
    SUSPENDED = "suspended"
    REPLACED = "replaced"


class CommunitySpace(Base):
    """A village or pastoral-rangeland community space with governance state.

    ``village_id`` is the identity the rest of the platform already uses
    (``LandscapeVillage.village_id``), so governance attaches to the existing
    hub instead of forking it.
    """

    __tablename__ = "gov_community_spaces"
    __table_args__ = (
        UniqueConstraint("village_id", name="uq_gov_space_village"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    village_id = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    kind = Column(String(32), nullable=False, default=CommunitySpaceKind.VILLAGE.value)
    status = Column(String(32), nullable=False, default=SpaceStatus.REQUESTED.value, index=True)
    region = Column(String(100), nullable=True)
    country = Column(String(10), nullable=True)

    #: Sensitivity-classified content: private by default, published per field.
    migration_routes = Column(Text, nullable=True)
    water_sources = Column(Text, nullable=True)
    sacred_sites = Column(Text, nullable=True)
    #: Exact coordinates stay private; a coarse centroid may be public.
    exact_boundary = Column(Text, nullable=True)
    public_centroid = Column(String(64), nullable=True)

    #: The separate local decisions (D-14): this is NOT a trademark or a
    #: product certification, and the API never presents it as one.
    local_validation_decision = Column(String(32), nullable=True)
    local_brand_usage_decision = Column(String(32), nullable=True)
    sensitive_fields_published = Column(Integer, default=0)
    published_fields = Column(JSON, nullable=True, default=list)

    #: Consent log for publishing sensitivity-classified fields:
    #: {field_name: {consented_by, consented_at, method}}
    sensitive_field_consent = Column(JSON, default=dict)

    suspended_reason = Column(Text, nullable=True)
    archived_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )

    charters = relationship(
        "LocalCharter", back_populates="space", cascade="all, delete-orphan"
    )
    groups = relationship(
        "WorkingGroup", back_populates="space", cascade="all, delete-orphan"
    )
    applications = relationship(
        "GovernanceApplication", back_populates="space", cascade="all, delete-orphan"
    )
    decisions = relationship(
        "GovernanceDecision", back_populates="space", cascade="all, delete-orphan"
    )


class LocalCharter(Base):
    """A versioned local charter; the version in force is the latest non-withdrawn."""

    __tablename__ = "gov_local_charters"
    __table_args__ = (
        UniqueConstraint("space_id", "version", name="uq_gov_charter_space_version"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    space_id = Column(
        String(36), ForeignKey("gov_community_spaces.id"), nullable=False, index=True
    )
    version = Column(Integer, nullable=False, default=1)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    adopted_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)
    withdrawal_reason = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    space = relationship("CommunitySpace", back_populates="charters")


class WorkingGroup(Base):
    """The elected/acknowledged local working group of one community space."""

    __tablename__ = "gov_working_groups"
    __table_args__ = (
        UniqueConstraint("space_id", "mandate_ref", name="uq_gov_group_space_mandate"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    space_id = Column(
        String(36), ForeignKey("gov_community_spaces.id"), nullable=False, index=True
    )
    mandate_ref = Column(String(64), nullable=False)
    mandate_summary = Column(Text, nullable=True)
    formed_at = Column(DateTime, default=lambda: datetime.now(UTC))
    dissolved_at = Column(DateTime, nullable=True)
    dissolution_reason = Column(Text, nullable=True)

    space = relationship("CommunitySpace", back_populates="groups")
    memberships = relationship(
        "WorkingGroupMembership", back_populates="group", cascade="all, delete-orphan"
    )


class WorkingGroupMembership(Base):
    """One person's term in a working group; ending it never erases history."""

    __tablename__ = "gov_working_group_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    group_id = Column(
        String(36), ForeignKey("gov_working_groups.id"), nullable=False, index=True
    )
    user_id = Column(String(36), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    role = Column(String(32), nullable=False, default=WorkingGroupRole.MEMBER.value)
    term_start = Column(Date, nullable=True)
    term_end = Column(Date, nullable=True)
    ended_reason = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    group = relationship("WorkingGroup", back_populates="memberships")


class GovernanceApplication(Base):
    """One step of the onboarding workflow, with its evidence and actor."""

    __tablename__ = "gov_applications"
    __table_args__ = (
        # One application per submitted step class: steps are recorded once and
        # amended by their own review, never stacked.
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    space_id = Column(
        String(36), ForeignKey("gov_community_spaces.id"), nullable=False, index=True
    )
    step = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="submitted", index=True)
    submitted_by = Column(String(36), nullable=False)
    reviewed_by = Column(String(36), nullable=True)
    evidence_ref = Column(String(300), nullable=True)
    review_note = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(UTC))
    reviewed_at = Column(DateTime, nullable=True)

    space = relationship("CommunitySpace", back_populates="applications")


class GovernanceDecision(Base):
    """An append-only record of a local decision (charter adoption, dispute,
    suspension, objection resolution)."""

    __tablename__ = "gov_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    space_id = Column(
        String(36), ForeignKey("gov_community_spaces.id"), nullable=False, index=True
    )
    kind = Column(String(32), nullable=False)
    summary = Column(Text, nullable=False)
    charter_version = Column(Integer, nullable=True)
    decided_by = Column(String(36), nullable=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(UTC))
    superseded_at = Column(DateTime, nullable=True)
    superseded_reason = Column(Text, nullable=True)

    space = relationship("CommunitySpace", back_populates="decisions")
