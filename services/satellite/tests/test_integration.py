"""Integration tests for Satellite"""
import pytest

from services.satellite.monitoring_service import (
    SatelliteMonitoringService,
)


@pytest.mark.asyncio
class TestSatelliteIntegration:
    async def test_monitor_field(self, db_session):
        service = SatelliteMonitoringService(db_session)
        result = await service.monitor_field(
            village_id="hejij",
            field_bbox={"north": 35.5, "south": 35.4, "east": 51.5, "west": 51.4},
            days_back=30,
        )
        assert result is not None
        assert result["status"] in ["ok", "no_data"]

    async def test_detect_changes(self, db_session):
        service = SatelliteMonitoringService(db_session)
        result = await service.detect_changes(
            field_bbox={"north": 35.5, "south": 35.4, "east": 51.5, "west": 51.4},
            days_back=90,
        )
        assert "change_detected" in result
