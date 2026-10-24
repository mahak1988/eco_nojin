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
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from database.hub import hub

if TYPE_CHECKING:
    # Only the annotation on DeviceManager._cache names this; the runtime
    # methods import it locally as DbDevice.
    from database.models import IoTDevice

logger = logging.getLogger(__name__)


class DeviceStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PROVISIONING = "provisioning"


class DeviceType(StrEnum):
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
                # SEC-03: the provisioning caller owns the device. The column
                # existed but was never written, which left every device
                # unowned and every read/mutation route unscopable.
                user_id=str(user_id) if user_id is not None else None,
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

    def get_device(
        self, device_id: str, user_id: str | None = None, admin: bool = False
    ) -> Any | None:
        """Get device details by ID (SEC-03: owner-scoped, admins see all).

        ``admin`` also re-admits devices provisioned before the owner column
        was written (``user_id IS NULL``): without it every pre-existing device
        would vanish from the fleet with no way to re-attribute it
        (2026-10-12 review finding 5).
        """
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            query = select(DbDevice).where(DbDevice.id == device_id)
            if not admin and user_id is not None:
                query = query.where(DbDevice.user_id == str(user_id))
            result = db.execute(query)
            return result.scalar_one_or_none()
        finally:
            db.close()

    def list_devices(
        self,
        user_id: str | None = None,
        status: str | None = None,
        device_type: str | None = None,
        platform_id: str | None = None,
        admin: bool = False,
    ) -> list:
        """List devices (SEC-03: the caller's own devices; admins see the fleet).

        ``user_id`` is now a real filter — the argument existed before but the
        query never applied it, so any authenticated caller could enumerate
        every device in the fleet by passing a ``platform_id`` of their
        choosing. ``platform_id`` remains an optional explicit refinement, never
        a scope taken from a request header.

        ``admin`` removes the owner filter so the admin console can still see
        — and re-attribute — devices provisioned before the owner column was
        written (``user_id IS NULL``); without it those rows are invisible to
        everyone (2026-10-12 review finding 5).
        """
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            query = select(DbDevice)
            if not admin and user_id is not None:
                query = query.where(DbDevice.user_id == str(user_id))
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

    def update_device_status(
        self, device_id: str, status: str, user_id: str | None = None, admin: bool = False
    ) -> Any | None:
        """Update device status (active/inactive/error) — SEC-03 owner-scoped."""
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            query = select(DbDevice).where(DbDevice.id == device_id)
            if not admin and user_id is not None:
                query = query.where(DbDevice.user_id == str(user_id))
            result = db.execute(query)
            device = result.scalar_one_or_none()
            if device:
                device.status = status
                device.updated_at = datetime.now(UTC)
                db.commit()
                db.refresh(device)
            return device
        finally:
            db.close()

    def deregister_device(
        self, device_id: str, user_id: str | None = None, admin: bool = False
    ) -> bool:
        """Remove device from fleet (SEC-03: owner-scoped, admins see all)."""
        from database.models import IoTDevice as DbDevice

        db = hub.get_session()
        try:
            query = select(DbDevice).where(DbDevice.id == device_id)
            if not admin and user_id is not None:
                query = query.where(DbDevice.user_id == str(user_id))
            result = db.execute(query)
            device = result.scalar_one_or_none()
            if device:
                db.delete(device)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def get_device_readings(
        self,
        device_id: str,
        limit: int = 100,
        user_id: str | None = None,
        admin: bool = False,
    ) -> list[dict]:
        """Get recent MRV observations for a device (SEC-03: owner-scoped)."""
        from database.models import MRVObservation

        if not admin and user_id is not None and self.get_device(device_id, user_id=user_id) is None:
            # Do not leak another tenant's readings; an empty result, not a
            # 404, keeps the endpoint's response shape stable.
            return []
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

    def provision_device_from_qr(
        self,
        qr_data: dict,
        user_id: str | None = None,
        platform_id: str | None = None,
    ) -> Any | None:
        """Provision a device via QR code scan.

        SEC-03 + review finding 12: the owner is the authenticated caller and
        the platform comes from the token — both are now **required** arguments.
        The previous implementation read ``user_id`` and ``platform_id`` out of
        the QR payload, which is client-supplied and let a caller provision
        devices under another identity or attribute a device to an arbitrary
        platform; the ``qr_data.get("user_id", "anonymous")`` fallback is gone
        because it re-opened exactly the cross-identity path this closes.
        """
        if user_id is None:
            raise ValueError("user_id (the authenticated owner) is required")
        device_name = qr_data.get("device_name", "Unknown Device")
        device_type = qr_data.get("device_type", DeviceType.SENSOR.value)
        sensor_types = qr_data.get("sensor_types", [])
        location = qr_data.get("location", {})
        return self.register_device(
            user_id=user_id,
            device_name=device_name,
            device_type=device_type,
            sensor_types=sensor_types,
            location=location,
            platform_id=platform_id,
        )
