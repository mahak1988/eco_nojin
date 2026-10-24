"""Schemas for Alerting Service."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    SMS = "sms"


class AlertRuleCondition(BaseModel):
    """Condition for triggering an alert."""

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(..., description="Metric name (e.g., 'cpu_usage', 'db_latency_p99')")
    operator: Literal[">", ">=", "<", "<=", "==", "!="] = Field(
        ..., description="Comparison operator"
    )
    threshold: float = Field(..., description="Threshold value")
    duration_seconds: int = Field(60, ge=10, description="Duration condition must persist")
    aggregation: Literal["avg", "max", "min", "sum", "count"] = Field(
        "avg", description="Aggregation function"
    )


class AlertRuleCreate(BaseModel):
    """Request to create an alert rule."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    severity: Literal["info", "warning", "critical"] = "warning"
    condition: AlertRuleCondition
    labels: dict[str, str] = Field(default_factory=dict, description="Labels for routing")
    annotations: dict[str, str] = Field(default_factory=dict, description="Additional info")

    # Notification settings
    notification_channels: list[Literal["email", "slack", "webhook", "pagerduty", "sms"]] = Field(
        default_factory=list, description="Notification channels"
    )
    notification_config: dict[str, Any] = Field(
        default_factory=dict, description="Channel-specific config"
    )

    # Timing
    evaluation_interval_seconds: int = Field(60, ge=10, description="How often to evaluate")
    pending_duration_seconds: int = Field(300, ge=0, description="Time before firing")
    resolved_duration_seconds: int = Field(300, ge=0, description="Time before resolving")

    # Suppression
    suppress_duration_seconds: int = Field(0, ge=0, description="Suppress after firing")
    max_firing_duration_seconds: int | None = Field(
        None, description="Auto-resolve after max duration"
    )

    # Ownership
    owner: str | None = Field(None, max_length=255)
    runbook_url: str | None = Field(None, max_length=500)


class AlertRuleUpdate(BaseModel):
    """Request to update an alert rule."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    severity: Literal["info", "warning", "critical"] | None = None
    condition: dict[str, Any] | None = None
    labels: dict[str, str] | None = None
    annotations: dict[str, str] | None = None
    notification_channels: list[Literal["email", "slack", "webhook", "pagerduty", "sms"]] | None = (
        None
    )
    notification_config: dict[str, Any] | None = None
    evaluation_interval_seconds: int | None = Field(None, ge=10)
    pending_duration_seconds: int | None = Field(None, ge=0)
    resolved_duration_seconds: int | None = Field(None, ge=0)
    suppress_duration_seconds: int | None = Field(None, ge=0)
    max_firing_duration_seconds: int | None = None
    owner: str | None = None
    runbook_url: str | None = None
    enabled: bool | None = None


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    severity: str
    condition: dict[str, Any]
    labels: dict[str, str]
    annotations: dict[str, str]
    notification_channels: list[str]
    notification_config: dict[str, Any]
    evaluation_interval_seconds: int
    pending_duration_seconds: int
    resolved_duration_seconds: int
    suppress_duration_seconds: int
    max_firing_duration_seconds: int | None
    owner: str | None
    runbook_url: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_id: str
    rule_name: str
    severity: str
    status: str
    labels: dict[str, str]
    annotations: dict[str, str]
    value: float
    threshold: float
    started_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    acknowledged_by: str | None
    acknowledged_note: str | None


class AlertSummary(BaseModel):
    """Summary of alert state."""

    total_rules: int
    enabled_rules: int
    firing_alerts: int
    acknowledged_alerts: int
    critical_firing: int
    warning_firing: int
    info_firing: int
    last_evaluation: datetime | None
