"""Schemas for Alerting Service."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class NotificationChannel(str, Enum):
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
    description: Optional[str] = Field(None, max_length=1000)
    severity: Literal["info", "warning", "critical"] = "warning"
    condition: AlertRuleCondition
    labels: Dict[str, str] = Field(default_factory=dict, description="Labels for routing")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Additional info")

    # Notification settings
    notification_channels: List[Literal["email", "slack", "webhook", "pagerduty", "sms"]] = Field(
        default_factory=list, description="Notification channels"
    )
    notification_config: Dict[str, Any] = Field(
        default_factory=dict, description="Channel-specific config"
    )

    # Timing
    evaluation_interval_seconds: int = Field(60, ge=10, description="How often to evaluate")
    pending_duration_seconds: int = Field(300, ge=0, description="Time before firing")
    resolved_duration_seconds: int = Field(300, ge=0, description="Time before resolving")

    # Suppression
    suppress_duration_seconds: int = Field(0, ge=0, description="Suppress after firing")
    max_firing_duration_seconds: Optional[int] = Field(
        None, description="Auto-resolve after max duration"
    )

    # Ownership
    owner: Optional[str] = Field(None, max_length=255)
    runbook_url: Optional[str] = Field(None, max_length=500)


class AlertRuleUpdate(BaseModel):
    """Request to update an alert rule."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    severity: Optional[Literal["info", "warning", "critical"]] = None
    condition: Optional[Dict[str, Any]] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    notification_channels: Optional[
        List[Literal["email", "slack", "webhook", "pagerduty", "sms"]]
    ] = None
    notification_config: Optional[Dict[str, Any]] = None
    evaluation_interval_seconds: Optional[int] = Field(None, ge=10)
    pending_duration_seconds: Optional[int] = Field(None, ge=0)
    resolved_duration_seconds: Optional[int] = Field(None, ge=0)
    suppress_duration_seconds: Optional[int] = Field(None, ge=0)
    max_firing_duration_seconds: Optional[int] = None
    owner: Optional[str] = None
    runbook_url: Optional[str] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    severity: str
    condition: Dict[str, Any]
    labels: Dict[str, str]
    annotations: Dict[str, str]
    notification_channels: List[str]
    notification_config: Dict[str, Any]
    evaluation_interval_seconds: int
    pending_duration_seconds: int
    resolved_duration_seconds: int
    suppress_duration_seconds: int
    max_firing_duration_seconds: Optional[int]
    owner: Optional[str]
    runbook_url: Optional[str]
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
    labels: Dict[str, str]
    annotations: Dict[str, str]
    value: float
    threshold: float
    started_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    acknowledged_by: Optional[str]
    acknowledged_note: Optional[str]


class AlertSummary(BaseModel):
    """Summary of alert state."""

    total_rules: int
    enabled_rules: int
    firing_alerts: int
    acknowledged_alerts: int
    critical_firing: int
    warning_firing: int
    info_firing: int
    last_evaluation: Optional[datetime]
