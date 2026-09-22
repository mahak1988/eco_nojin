"""Schemas for API Contract Registry."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ContractType(str, Enum):
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    GRPC = "grpc"


class CompatibilityLevel(str, Enum):
    NONE = "none"  # Breaking changes
    BACKWARD = "backward"  # Backward compatible
    FORWARD = "forward"  # Forward compatible
    FULL = "full"  # Fully compatible


class ContractSpec(BaseModel):
    """API contract specification."""

    model_config = ConfigDict(extra="forbid")

    type: ContractType = ContractType.OPENAPI
    spec: Dict[str, Any] = Field(..., description="Full OpenAPI/GraphQL/gRPC spec")


class ContractVersion(BaseModel):
    """API contract version record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    service_name: str
    version: str
    contract_type: ContractType
    spec: Dict[str, Any]
    is_active: bool
    created_at: datetime
    created_by: Optional[str]
    deprecated_at: Optional[datetime]
    deprecation_reason: Optional[str]
    supersedes: Optional[str]  # Previous version ID


class ContractCreate(BaseModel):
    """Request to register a new contract version."""

    service_name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$")
    contract_type: Literal["openapi", "graphql", "grpc"] = "openapi"
    spec: Dict[str, Any]
    supersedes: Optional[str] = None  # Previous version ID
    created_by: Optional[str] = None


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_name: str
    version: str
    contract_type: str
    is_active: bool
    created_at: datetime
    deprecated_at: Optional[datetime]
    supersedes: Optional[str]


class ContractDiff(BaseModel):
    """Difference between two contract versions."""

    model_config = ConfigDict(extra="forbid")

    added_endpoints: List[str] = []
    removed_endpoints: List[str] = []
    modified_endpoints: List[str] = []
    added_schemas: List[str] = []
    removed_schemas: List[str] = []
    modified_schemas: List[str] = []
    breaking_changes: List[Dict[str, Any]] = []
    safe_changes: List[Dict[str, Any]] = []


class CompatibilityResult(BaseModel):
    """Result of compatibility check between two versions."""

    model_config = ConfigDict(extra="forbid")

    from_version: str
    to_version: str
    compatibility: Literal["none", "backward", "forward", "full"]
    breaking_changes: List[Dict[str, Any]]
    safe_changes: List[Dict[str, Any]]
    can_upgrade: bool
    warnings: List[str] = []
