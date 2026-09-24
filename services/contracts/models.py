"""Database models for Contract Registry."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from database.base import Base


class ContractType(enum.StrEnum):
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    GRPC = "grpc"


class ContractVersionModel(Base):
    """API contract version record."""

    __tablename__ = "contract_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    service_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)
    contract_type = Column(String(20), default="openapi", nullable=False)

    # Full contract specification
    spec = Column(JSON, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    created_by = Column(String(255), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    deprecation_reason = Column(Text, nullable=True)
    supersedes_id = Column(PG_UUID(as_uuid=True), ForeignKey("contract_versions.id"), nullable=True)

    # Self-referential
    supersedes = relationship(
        "ContractVersionModel", remote_side="ContractVersionModel.id", backref="superseded_by"
    )

    __table_args__ = (
        Index("ix_contract_service_version", "service_name", "version", unique=True),
        Index("ix_contract_active", "service_name", "is_active"),
    )


class ContractTestRun(Base):
    """Record of contract test execution."""

    __tablename__ = "contract_test_runs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    contract_version_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("contract_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Test info
    test_type = Column(String(50), nullable=False)  # schemathesis, pact, custom
    test_tool = Column(String(50), nullable=True)  # schemathesis, pact-python, etc.

    # Results
    status = Column(String(20), nullable=False, index=True)  # passed, failed, error
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    skipped = Column(Integer, default=0)

    # Details
    duration_seconds = Column(Integer, nullable=True)
    error_details = Column(JSON, nullable=False, default=dict)
    test_output = Column(Text, nullable=True)

    # CI context
    ci_build_id = Column(String(100), nullable=True)
    ci_branch = Column(String(100), nullable=True)
    ci_commit = Column(String(40), nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_contract_test_contract_created", "contract_version_id", "created_at"),
        Index("ix_contract_test_status", "status"),
    )
