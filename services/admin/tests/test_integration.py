"""Integration tests for Admin"""
import pytest


@pytest.mark.asyncio
class TestAdminIntegration:
    async def test_system_health(self, admin_service):
        health = await admin_service.get_system_health()
        assert health.overall_status
        assert health.uptime_seconds >= 0

    async def test_audit_logging(self, admin_service):
        log = await admin_service.log_action(
            action="test_action", actor_id="admin_123",
        )
        assert log.action == "test_action"
        logs = await admin_service.get_audit_logs()
        assert len(logs) >= 1
