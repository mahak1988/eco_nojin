"""Alerting Service - Core business logic for alert management."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.alerting.models import Alert, AlertRule
from services.alerting.schemas import (
    AlertRuleCreate,
    AlertRuleUpdate,
)


class AlertService:
    """Service for managing alert rules and alerts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Alert Rule CRUD
    # =========================================================================

    async def create_rule(
        self, data: AlertRuleCreate, user_id: str | None = None
    ) -> dict[str, Any]:
        """Create a new alert rule."""
        rule = AlertRule(
            name=data.name,
            description=data.description,
            severity=data.severity,
            condition=data.condition.model_dump()
            if hasattr(data.condition, "model_dump")
            else data.condition,
            labels=data.labels,
            annotations=data.annotations,
            notification_channels=data.notification_channels,
            notification_config=data.notification_config,
            evaluation_interval_seconds=data.evaluation_interval_seconds,
            pending_duration_seconds=data.pending_duration_seconds,
            resolved_duration_seconds=data.resolved_duration_seconds,
            suppress_duration_seconds=data.suppress_duration_seconds,
            max_firing_duration_seconds=data.max_firing_duration_seconds,
            owner=data.owner,
            runbook_url=data.runbook_url,
            enabled=True,
            created_by=user_id,
        )

        self.db.add(rule)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(rule)

        return self._rule_to_dict(rule)

    async def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        """Get an alert rule by ID."""
        result = await self.db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if rule:
            return self._rule_to_dict(rule)
        return None

    async def list_rules(
        self,
        severity: str | None = None,
        enabled: bool | None = None,
        owner: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """List alert rules with filters."""
        query = select(AlertRule)

        if severity:
            query = query.where(AlertRule.severity == severity)
        if enabled is not None:
            query = query.where(AlertRule.enabled == enabled)
        if owner:
            query = query.where(AlertRule.owner == owner)

        query = query.order_by(desc(AlertRule.created_at))
        query = query.offset((page - 1) * 20).limit(page_size)

        result = await self.db.execute(query)
        rules = result.scalars().all()

        return [self._rule_to_dict(r) for r in rules]

    async def update_rule(self, rule_id: str, data: AlertRuleUpdate) -> dict[str, Any] | None:
        """Update an alert rule."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return None

        # Get the actual model instance
        result = await self.db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule_obj = result.scalar_one_or_none()
        if not rule_obj:
            return None

        # Update fields
        if data.name is not None:
            rule_obj.name = data.name
        if data.description is not None:
            rule_obj.description = data.description
        if data.severity is not None:
            rule_obj.severity = data.severity
        if data.condition is not None:
            rule_obj.condition = data.condition
        if data.labels is not None:
            rule_obj.labels = data.labels
        if data.annotations is not None:
            rule_obj.annotations = data.annotations
        if data.notification_channels is not None:
            rule_obj.notification_channels = data.notification_channels
        if data.notification_config is not None:
            rule_obj.notification_config = data.notification_config
        if data.evaluation_interval_seconds is not None:
            rule_obj.evaluation_interval_seconds = data.evaluation_interval_seconds
        if data.pending_duration_seconds is not None:
            rule_obj.pending_duration_seconds = data.pending_duration_seconds
        if data.resolved_duration_seconds is not None:
            rule_obj.resolved_duration_seconds = data.resolved_duration_seconds
        if data.suppress_duration_seconds is not None:
            rule_obj.suppress_duration_seconds = data.suppress_duration_seconds
        if data.max_firing_duration_seconds is not None:
            rule_obj.max_firing_duration_seconds = data.max_firing_duration_seconds
        if data.owner is not None:
            rule_obj.owner = data.owner
        if data.runbook_url is not None:
            rule_obj.runbook_url = data.runbook_url
        if data.enabled is not None:
            rule_obj.enabled = data.enabled

        await self.db.commit()
        await self.db.refresh(rule_obj)

        return self._rule_to_dict(rule_obj)

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        result = await self.db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return False

        await self.db.delete(rule)
        await self.db.commit()
        return True

    # =========================================================================
    # Alert Management
    # =========================================================================

    async def get_alert(self, alert_id: str) -> dict[str, Any] | None:
        """Get an alert by ID."""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if alert:
            return self._alert_to_dict(alert)
        return None

    async def list_alerts(
        self,
        status: str | None = None,
        severity: str | None = None,
        rule_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """List alerts with filters."""
        query = select(Alert)

        if status:
            query = query.where(Alert.status == status)
        if severity:
            query = query.where(Alert.severity == severity)
        if rule_id:
            query = query.where(Alert.rule_id == rule_id)

        query = query.order_by(desc(Alert.started_at))
        query = query.offset((page - 1) * 20).limit(page_size)

        result = await self.db.execute(query)
        alerts = result.scalars().all()

        return [self._alert_to_dict(a) for a in alerts]

    async def acknowledge_alert(self, alert_id: str, user_id: str, note: str | None = None) -> bool:
        """Acknowledge an alert."""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return False

        if alert.status == "resolved":
            return False  # Already resolved

        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(UTC)
        alert.acknowledged_by = user_id
        alert.acknowledged_note = note

        await self.db.commit()
        return True

    async def resolve_alert(self, alert_id: str) -> bool:
        """Manually resolve an alert."""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return False

        alert.status = "resolved"
        alert.resolved_at = datetime.now(UTC)

        await self.db.commit()
        return True

    async def suppress_alert(self, alert_id: str, duration_seconds: int) -> bool:
        """Suppress an alert for a duration."""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return False

        alert.status = "suppressed"
        alert.suppressed_until = datetime.now(UTC) + timedelta(seconds=duration_seconds)

        await self.db.commit()
        return True

    # =========================================================================
    # Summary & Stats
    # =========================================================================

    async def get_summary(self) -> dict[str, Any]:
        """Get alert summary statistics."""

        # Rule counts
        total_rules = await self.db.scalar(select(func.count(AlertRule.id))) or 0
        enabled_rules = (
            await self.db.scalar(select(func.count(AlertRule.id)).where(AlertRule.enabled)) or 0
        )

        # Alert counts by status
        status_counts = await self.db.execute(
            select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
        )
        status_counts = {str(s): c for s, c in status_counts.all()}

        firing = status_counts.get("firing", 0)
        acknowledged = status_counts.get("acknowledged", 0)
        resolved = status_counts.get("resolved", 0)
        suppressed = status_counts.get("suppressed", 0)

        # Firing by severity
        severity_counts = await self.db.execute(
            select(Alert.severity, func.count(Alert.id))
            .where(Alert.status == "firing")
            .group_by(Alert.severity)
        )
        severity_counts = {str(s): c for s, c in severity_counts.all()}

        # Last evaluation
        last_eval = await self.db.scalar(select(func.max(Alert.started_at)))

        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "firing_alerts": firing,
            "acknowledged_alerts": acknowledged,
            "resolved_alerts": resolved,
            "suppressed_alerts": suppressed,
            "critical_firing": severity_counts.get("critical", 0),
            "warning_firing": severity_counts.get("warning", 0),
            "info_firing": severity_counts.get("info", 0),
            "last_evaluation": last_eval,
        }

    # =========================================================================
    # Evaluation (called by background worker)
    # =========================================================================

    async def evaluate_rules(self) -> dict[str, int]:
        """Evaluate all enabled rules and fire/resolve alerts.

        This should be called periodically by a background worker.
        Returns count of alerts fired/resolved.
        """
        # This is a placeholder - actual implementation would:
        # 1. Query metrics from Prometheus/InfluxDB
        # 2. Evaluate each rule's condition
        # 3. Fire new alerts or resolve existing ones
        # 4. Send notifications
        return {"fired": 0, "resolved": 0}

    # =========================================================================
    # Helpers
    # =========================================================================

    def _rule_to_dict(self, rule: AlertRule) -> dict[str, Any]:
        return {
            "id": str(rule.id),
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity.value,
            "condition": rule.condition,
            "labels": rule.labels,
            "annotations": rule.annotations,
            "notification_channels": rule.notification_channels,
            "notification_config": rule.notification_config,
            "evaluation_interval_seconds": rule.evaluation_interval_seconds,
            "pending_duration_seconds": rule.pending_duration_seconds,
            "resolved_duration_seconds": rule.resolved_duration_seconds,
            "suppress_duration_seconds": rule.suppress_duration_seconds,
            "max_firing_duration_seconds": rule.max_firing_duration_seconds,
            "owner": rule.owner,
            "runbook_url": rule.runbook_url,
            "enabled": rule.enabled,
            "created_at": rule.created_at,
            "updated_at": rule.updated_at,
        }

    def _alert_to_dict(self, alert: Alert) -> dict[str, Any]:
        return {
            "id": str(alert.id),
            "rule_id": str(alert.rule_id),
            "rule_name": alert.rule.name if alert.rule else "unknown",
            "severity": alert.rule.severity.value if alert.rule else "unknown",
            "status": alert.status.value,
            "labels": alert.labels,
            "annotations": alert.annotations,
            "value": alert.value,
            "threshold": alert.threshold,
            "started_at": alert.started_at,
            "acknowledged_at": alert.acknowledged_at,
            "resolved_at": alert.resolved_at,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_note": alert.acknowledged_note,
        }
