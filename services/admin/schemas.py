"""Pydantic schemas for Admin"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

class ServiceHealthCheck(BaseModel):
    name: str
    status: ServiceStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None

class SystemHealth(BaseModel):
    overall_status: ServiceStatus
    services: List[ServiceHealthCheck]
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
    actor_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime

class AdminStats(BaseModel):
    total_orders: int = 0
    total_bookings: int = 0
    total_villages: int = 0
    uptime_seconds: int = 0
    