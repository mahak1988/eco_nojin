"""Schemas for API Contract Registry."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractType(StrEnum):
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    GRPC = "grpc"


class CompatibilityLevel(StrEnum):
    NONE = "none"  # Breaking changes
    BACKWARD = "backward"  # Backward compatible
    FORWARD = "forward"  # Forward compatible
    FULL = "full"  # Fully compatible


class ContractSpec(BaseModel):
    """API contract specification."""

    model_config = ConfigDict(extra="forbid")

    type: ContractType = ContractType.OPENAPI
    spec: dict[str, Any] = Field(..., description="Full OpenAPI/GraphQL/gRPC spec")


class ContractVersion(BaseModel):
    """API contract version record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    service_name: str
    version: str
    contract_type: ContractType
    spec: dict[str, Any]
    is_active: bool
    created_at: datetime
    created_by: str | None
    deprecated_at: datetime | None
    deprecation_reason: str | None
    supersedes: str | None  # Previous version ID


class ContractCreate(BaseModel):
    """Request to register a new contract version."""

    service_name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$")
    contract_type: Literal["openapi", "graphql", "grpc"] = "openapi"
    spec: dict[str, Any]
    supersedes: str | None = None  # Previous version ID
    created_by: str | None = None


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_name: str
    version: str
    contract_type: str
    is_active: bool
    created_at: datetime
    deprecated_at: datetime | None
    supersedes: str | None


class ContractDiff(BaseModel):
    """Difference between two contract versions."""

    model_config = ConfigDict(extra="forbid")

    added_endpoints: list[str] = []
    removed_endpoints: list[str] = []
    modified_endpoints: list[str] = []
    added_schemas: list[str] = []
    removed_schemas: list[str] = []
    modified_schemas: list[str] = []
    breaking_changes: list[dict[str, Any]] = []
    safe_changes: list[dict[str, Any]] = []


class CompatibilityResult(BaseModel):
    """Result of compatibility check between two versions."""

    model_config = ConfigDict(extra="forbid")

    from_version: str
    to_version: str
    compatibility: Literal["none", "backward", "forward", "full"]
    breaking_changes: list[dict[str, Any]]
    safe_changes: list[dict[str, Any]]
    can_upgrade: bool
    warnings: list[str] = []
