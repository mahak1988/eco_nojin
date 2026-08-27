"""Pydantic schemas for Admin"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

class ServiceHealthCheck(BaseModel):
    name: str
    status: ServiceStatus
    latency_ms: float | None = None
    message: str | None = None

class SystemHealth(BaseModel):
    overall_status: ServiceStatus
    services: list[ServiceHealthCheck]
    uptime_seconds: int
    checked_at: datetime

class ProjectStatus(BaseModel):
    phase: str
    version: str
    total_modules: int
    active_modules: int
    description: str

class AuditLog(BaseModel):
    id: str
    actor_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any] | None
    created_at: datetime

class AdminStats(BaseModel):
    total_orders: int = 0
    total_bookings: int = 0
    total_villages: int = 0
    uptime_seconds: int = 0
