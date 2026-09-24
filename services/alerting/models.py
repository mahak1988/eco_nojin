"""Database models for Alerting Service."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from database.base import Base


class AlertSeverity(enum.StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(enum.StrEnum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class AlertRule(Base):
    """Alert rule definition."""

    __tablename__ = "alert_rules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    severity = Column(
        SQLEnum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False, index=True
    )

    # Condition
    condition = Column(JSON, nullable=False)  # metric, operator, threshold, duration, aggregation

    # Labels and annotations
    labels = Column(JSON, nullable=False, default=dict)
    annotations = Column(JSON, nullable=False, default=dict)

    # Notification settings
    notification_channels = Column(JSON, nullable=False, default=list)
    notification_config = Column(JSON, nullable=False, default=dict)

    # Timing
    evaluation_interval_seconds = Column(Integer, default=60, nullable=False)
    pending_duration_seconds = Column(Integer, default=300, nullable=False)
    resolved_duration_seconds = Column(Integer, default=300, nullable=False)
    suppress_duration_seconds = Column(Integer, default=0, nullable=False)
    max_firing_duration_seconds = Column(Integer, nullable=True)

    # Ownership
    owner = Column(String(255), nullable=True, index=True)
    runbook_url = Column(String(500), nullable=True)

    # State
    enabled = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_by = Column(String(255), nullable=True)

    # Relationships
    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")
    notifications = relationship(
        "AlertNotification", back_populates="rule", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alert_rule_enabled_severity", "enabled", "severity"),
        Index("ix_alert_rule_owner", "owner"),
    )


class Alert(Base):
    """Active or resolved alert instance."""

    __tablename__ = "alerts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    rule_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Alert identification
    fingerprint = Column(String(64), nullable=False, index=True)  # Hash of labels + rule

    # State
    status = Column(
        SQLEnum("firing", "resolved", "acknowledged", "suppressed", name="alert_status"),
        default="firing",
        nullable=False,
        index=True,
    )

    # Values
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    labels = Column(JSON, nullable=False, default=dict)
    annotations = Column(JSON, nullable=False, default=dict)

    # Timing
    started_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Acknowledgment
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_note = Column(Text, nullable=True)

    # Suppression
    suppressed_until = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")
    notifications = relationship(
        "AlertNotification", back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alert_status_started", "status", "started_at"),
        Index("ix_alert_fingerprint", "fingerprint", unique=True),
        Index("ix_alert_rule_status", "rule_id", "status"),
    )


class AlertNotification(Base):
    """Notification sent for an alert."""

    __tablename__ = "alert_notifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    rule_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    alert_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    channel = Column(
        String(50), nullable=False, index=True
    )  # email, slack, webhook, pagerduty, sms
    status = Column(String(20), nullable=False, index=True)  # sent, failed, pending
    recipient = Column(String(255), nullable=True)

    # Content
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)

    # Result
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationships
    rule = relationship("AlertRule", back_populates="notifications")
    alert = relationship("Alert", back_populates="notifications")

    __table_args__ = (
        Index("ix_notification_rule_status", "rule_id", "status"),
        Index("ix_notification_alert", "alert_id"),
    )
