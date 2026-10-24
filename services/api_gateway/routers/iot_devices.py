"""IoT device API router.

Endpoints for device provisioning, fleet management, and reading queries.
"""
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from services.api_gateway.auth import ADMIN_ROLES, require_user
from services.api_gateway.errors import safe_detail_for_status
from services.business_modules.iot.device_manager import DeviceManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/iot", tags=["IoT Devices"])


def get_db():
    with hub.get_session() as session:
        yield session


class DeviceRegisterRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=200)
    device_type: str = Field("sensor", pattern="^(sensor|gateway|actuator)$")
    sensor_types: list[str] = Field(default_factory=list)
    location: dict = Field(default_factory=dict)
    firmware_version: str | None = None


class DeviceStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive|error)$")


class DeviceProvisionQR(BaseModel):
    qr_data: dict = Field(default_factory=dict)


_device_manager = DeviceManager()


@router.get("/devices")
def list_devices(
    request: Request,
    status: str | None = None,
    device_type: str | None = None,
    platform_id: str | None = None,
    user: Annotated[Any, Depends(require_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """List IoT devices with optional filters."""
    admin = _is_fleet_admin(user)
    devices = _device_manager.list_devices(
        user_id=user.id,
        status=status,
        device_type=device_type,
        platform_id=platform_id or _get_platform_id(request),
        admin=admin,
    )
    return {
        "devices": [
            {
                "id": d.id,
                "device_name": d.device_name,
                "device_type": d.device_type,
                "sensor_types": d.sensor_types,
                "location": d.location,
                "status": d.status,
                "firmware_version": d.firmware_version,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                "qr_code": d.qr_code,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in devices
        ],
        "count": len(devices),
    }


@router.post("/devices")
def register_device(
    payload: DeviceRegisterRequest,
    request: Request,
    user: Annotated[Any, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new IoT device."""
    try:
        device = _device_manager.register_device(
            user_id=user.id,
            device_name=payload.device_name,
            device_type=payload.device_type,
            sensor_types=payload.sensor_types,
            location=payload.location,
            platform_id=_get_platform_id(request),
        )
    except Exception as exc:
        logger.error("Device registration failed: %s", exc)
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc

    return {
        "id": device.id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "status": device.status,
        "qr_code": device.qr_code,
        "message": "Device registered successfully",
    }


@router.get("/devices/{device_id}")
def get_device(
    device_id: str,
    user: Annotated[Any, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get device details."""
    device = _device_manager.get_device(
        device_id, user_id=str(user.id), admin=_is_fleet_admin(user)
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "id": device.id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "sensor_types": device.sensor_types,
        "location": device.location,
        "status": device.status,
        "firmware_version": device.firmware_version,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "platform_id": device.platform_id,
        "qr_code": device.qr_code,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
    }


@router.put("/devices/{device_id}/status")
def update_device_status(
    device_id: str,
    payload: DeviceStatusUpdate,
    user: Annotated[Any, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update device status."""
    device = _device_manager.update_device_status(
        device_id, payload.status, user_id=str(user.id), admin=_is_fleet_admin(user)
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"id": device.id, "status": device.status, "updated_at": device.updated_at.isoformat()}


@router.delete("/devices/{device_id}")
def deregister_device(
    device_id: str,
    user: Annotated[Any, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Deregister device."""
    success = _device_manager.deregister_device(
        device_id, user_id=str(user.id), admin=_is_fleet_admin(user)
    )
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"id": device_id, "status": "deregistered"}


@router.get("/devices/{device_id}/readings")
def get_device_readings(
    device_id: str,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    user: Annotated[Any, Depends(require_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """Get recent readings for a device."""
    readings = _device_manager.get_device_readings(
        device_id, limit=limit, user_id=str(user.id), admin=_is_fleet_admin(user)
    )
    return {"device_id": device_id, "readings": readings, "count": len(readings)}


@router.post("/devices/provision-qr")
def provision_device_qr(
    payload: DeviceProvisionQR,
    request: Request,
    user: Annotated[Any, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Provision device from QR code scan.

    The owner and the platform both come from the token (review finding 12);
    anything in the QR payload about scope is ignored.
    """
    try:
        device = _device_manager.provision_device_from_qr(
            payload.qr_data,
            user_id=str(user.id),
            platform_id=_get_platform_id(request),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc
    return {"device": device, "message": "Device provisioned from QR"}


@router.get("/health")
def iot_health():
    """IoT module health check."""
    return {
        "status": "operational",
        "module": "iot",
        "features": {
            "device_provisioning": True,
            "mqtt_consumer": True,
            "t tn_v3_webhook": True,
            "qa_qc": True,
            "device_readings": True,
        },
        "mode": "real",
    }


def _get_platform_id(request: Request) -> str | None:
    """Extract the platform/tenant ID **from the token**, never the request.

    SEC-03: this function used to read the ``X-Tenant-Id`` / ``X-Platform-Id``
    headers, which are caller-controlled — any authenticated user could scope
    a device listing (or register a device under) another tenant. The tenant is
    resolved once per request by ``IdentityMiddleware`` from the JWT
    (bearer or cookie) and published on ``request.state``.
    """
    return getattr(request.state, "tenant_id", None)


def _is_fleet_admin(user: Any) -> bool:
    """Whether the caller may see (and manage) the whole device fleet.

    Admins keep the visibility the owner filter removes: devices provisioned
    before the owner column was written carry ``user_id IS NULL`` and would
    otherwise be invisible to everyone, with no way to re-attribute them
    (2026-10-12 review finding 5).
    """
    return getattr(user, "role", None) in ADMIN_ROLES
