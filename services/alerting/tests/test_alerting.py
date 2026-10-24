"""Tests for alerting service and router."""

import pytest

from services.alerting.models import Alert, AlertRule
from services.alerting.schemas import AlertRuleCreate, AlertRuleUpdate


class TestAlertingModels:
    """Tests for alerting models."""

    def test_alert_model_creation(self):
        """Test creating an Alert model instance."""
        alert = Alert(
            rule_id="test-rule-id",
            fingerprint="test-fingerprint",
            status="firing",
            value=95.0,
            threshold=90.0,
            labels={"host": "server-1", "metric": "cpu"},
            annotations={"description": "High CPU usage"},
        )
        assert alert.rule_id == "test-rule-id"
        assert alert.fingerprint == "test-fingerprint"
        assert alert.status == "firing"
        assert alert.value == 95.0

    def test_alert_rule_model_creation(self):
        """Test creating an AlertRule model instance."""
        rule = AlertRule(
            name="Test Rule",
            description="Test description",
            severity="critical",
            condition={"metric": "cpu_usage", "threshold": 90},
            labels={"team": "platform"},
        )
        assert rule.name == "Test Rule"
        assert rule.severity == "critical"


class TestAlertingSchemas:
    """Tests for alerting schemas."""

    def test_alert_rule_create_schema(self):
        """Test AlertRuleCreate schema validation."""
        data = AlertRuleCreate(
            name="CPU Alert",
            description="Alert when CPU exceeds threshold",
            severity="warning",
            condition={"metric": "cpu_percent", "operator": ">", "threshold": 80},
            labels={"environment": "production"},
            notification_channels=["email", "slack"],
            evaluation_interval_seconds=60,
        )
        assert data.name == "CPU Alert"
        assert data.severity == "warning"

    def test_alert_rule_update_schema(self):
        """Test AlertRuleUpdate schema."""
        data = AlertRuleUpdate(
            name="Updated CPU Alert",
            severity="critical",
        )
        assert data.name == "Updated CPU Alert"
        assert data.severity == "critical"


class TestAlertingService:
    """Tests for AlertService (requires database)."""

    @pytest.fixture
    def service(self, db_session):
        from services.alerting.service import AlertService
        return AlertService(db_session)

    async def test_service_instantiation(self, service):
        """Test that service can be instantiated."""
        assert service is not None
        assert hasattr(service, 'create_rule')
        assert hasattr(service, 'get_rule')
        assert hasattr(service, 'list_rules')

    async def test_create_rule(self, service):
        """Test creating an alert rule."""
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "severity": "warning",
            "condition": {
                "metric": "cpu_usage",
                "operator": ">",
                "threshold": 80,
                "duration_seconds": 60,
            },
            "labels": {"team": "platform"},
        }
        rule_create = AlertRuleCreate(**rule_data)
        rule = await service.create_rule(rule_create, user_id="test-user")
        assert rule is not None
        assert rule["name"] == "Test Rule"
        assert rule["severity"] == "warning"

    async def test_get_rule(self, service):
        """Test retrieving an alert rule."""
        rule_data = {
            "name": "Test Rule 2",
            "description": "Test description",
            "severity": "critical",
            "condition": {
                "metric": "memory_usage",
                "operator": ">=",
                "threshold": 95,
                "duration_seconds": 60,
            },
        }
        rule_create = AlertRuleCreate(**rule_data)
        created = await service.create_rule(rule_create, user_id="test-user")
        retrieved = await service.get_rule(created["id"])
        assert retrieved is not None
        assert retrieved["id"] == created["id"]

    async def test_list_rules(self, service):
        """Test listing alert rules."""
        rules = await service.list_rules(page=1, page_size=10)
        assert isinstance(rules, list)


class TestAlertingRouter:
    """Tests for alerting router endpoints."""

    def test_router_exists(self):
        """Test that router is defined."""
        from services.alerting.router import router as alerting_router
        assert alerting_router is not None