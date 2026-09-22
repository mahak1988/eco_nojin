"""IoT device management — provisioning, fleet management, and status tracking.

Integrates with:
- ``engine.hydroma.mrv.iot_ingest`` (persist_iot_reading, parse_ttn_v3)
- ``engine.hydroma.mrv.schemas`` (IoTReading)
- ``database.models`` (IoTDevice, MRVObservation)

Requirements:
- paho-mqtt (optional, for live MQTT fleet management)
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import select

from database.hub import hub

logger = logging.getLogger(__name__)


class DeviceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PROVISIONING = "provisioning"


class DeviceType(str, Enum):
    SENSOR = "sensor"
    GATEWAY = "gateway"
    ACTUATOR = "actuator"


@dataclass
class DeviceReading:
    device_id: str
    reading_type: str
    value: float
    unit: str
    qa_status: str
    recorded_at: datetime


class DeviceManager:
    """Device management service for IoT fleet."""

    def __init__(self):
        self._cache: dict[str, IoTDevice] = {}

    def register_device(
        self,
        user_id: str,
        device_name: str,
        device_type: str = DeviceType.SENSOR.value,
        sensor_types: list[str] | None = None,
        location: dict | None = None,
        platform_id: str | None = None,
    ) -> Any:
        """Provision a new IoT device."""
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            device = DbDevice(
                device_name=device_name,
                device_type=device_type,
                sensor_types=sensor_types or [],
                location=location or {},
                platform_id=platform_id,
                status=DeviceStatus.PROVISIONING.value,
                qr_code=f"QR-{uuid.uuid4().hex[:12].upper()}",
            )
            db.add(device)
            db.commit()
            db.refresh(device)
            device.status = DeviceStatus.ACTIVE.value
            db.commit()
            db.refresh(device)
            logger.info("Device registered: %s (%s)", device.device_name, device.id)
            return device
        finally:
            db.close()

    def get_device(self, device_id: str) -> Any | None:
        """Get device details by ID."""
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            result = db.execute(select(DbDevice).where(DbDevice.id == device_id))
            return result.scalar_one_or_none()
        finally:
            db.close()

    def list_devices(
        self,
        user_id: str | None = None,
        status: str | None = None,
        device_type: str | None = None,
        platform_id: str | None = None,
    ) -> list:
        """List devices with optional filters."""
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            query = select(DbDevice)
            if status:
                query = query.where(DbDevice.status == status)
            if device_type:
                query = query.where(DbDevice.device_type == device_type)
            if platform_id:
                query = query.where(DbDevice.platform_id == platform_id)
            result = db.execute(query)
            devices = result.scalars().all()
            return devices
        finally:
            db.close()

    def update_device_status(self, device_id: str, status: str) -> Any | None:
        """Update device status (active/inactive/error)."""
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            result = db.execute(select(DbDevice).where(DbDevice.id == device_id))
            device = result.scalar_one_or_none()
            if device:
                device.status = status
                device.updated_at = datetime.now(UTC)
                db.commit()
                db.refresh(device)
            return device
        finally:
            db.close()

    def deregister_device(self, device_id: str) -> bool:
        """Remove device from fleet."""
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            result = db.execute(select(DbDevice).where(DbDevice.id == device_id))
            device = result.scalar_one_or_none()
            if device:
                db.delete(device)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def get_device_readings(self, device_id: str, limit: int = 100) -> list[dict]:
        """Get recent MRV observations for a device."""
        from database.models import MRVObservation

        db = hub.get_session()
        try:
            query = (
                select(MRVObservation)
                .where(MRVObservation.site_id == device_id)
                .order_by(MRVObservation.created_at.desc())
                .limit(limit)
            )
            result = db.execute(query)
            return [
                {
                    "id": obs.id,
                    "sensor_type": obs.sensor_type,
                    "value": obs.value,
                    "unit": obs.unit,
                    "qa_status": obs.qa_status,
                    "qa_message": obs.qa_message,
                    "observed_at": obs.observed_at.isoformat() if obs.observed_at else None,
                    "data_source": obs.data_source,
                }
                for obs in result.scalars().all()
            ]
        finally:
            db.close()

    def provision_device_from_qr(self, qr_data: dict) -> Any | None:
        """Provision a device via QR code scan."""
        device_name = qr_data.get("device_name", "Unknown Device")
        device_type = qr_data.get("device_type", DeviceType.SENSOR.value)
        sensor_types = qr_data.get("sensor_types", [])
        location = qr_data.get("location", {})
        platform_id = qr_data.get("platform_id")
        return self.register_device(
            user_id=qr_data.get("user_id", "anonymous"),
            device_name=device_name,
            device_type=device_type,
            sensor_types=sensor_types,
            location=location,
            platform_id=platform_id,
        )
