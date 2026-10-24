"""Organization management API router.

S-STRUCT compliant: all DB access delegated to
``services.organization.service.OrganizationService``.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database.hub import hub
from services.api_gateway.auth import require_user
from services.api_gateway.errors import domain_detail
from services.organization.service import OrganizationService

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])

logger = logging.getLogger(__name__)


def get_db():
    with hub.get_session() as session:
        yield session


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    country: str = Field(..., min_length=2, max_length=2)
    description: str | None = None


class MemberInvite(BaseModel):
    email: str = Field(..., pattern=r"^[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}$")
    role: str = Field("member", pattern="^(admin|member|viewer)$")


class OrgUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


def get_service(db: Annotated[Any, Depends(get_db)]) -> OrganizationService:
    return OrganizationService(db)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    user: Annotated[dict, Depends(require_user)],
    service: Annotated[OrganizationService, Depends(get_service)],
):
    """Create a new organization."""
    try:
        return service.create_organization(
            slug=payload.slug,
            name=payload.name,
            country=payload.country,
            description=payload.description,
            user_id=str(getattr(user, "id", user.get("sub", user.get("user_id")))),
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=domain_detail(e, 409)) from e


@router.get("")
def list_organizations(
    user: Annotated[dict, Depends(require_user)],
    service: Annotated[OrganizationService, Depends(get_service)],
):
    """List organizations the user belongs to."""
    user_id = str(getattr(user, "id", user.get("sub", user.get("user_id"))))
    return {"organizations": service.list_organizations(user_id), "count": len(service.list_organizations(user_id))}


@router.get("/{org_id}")
def get_organization(
    org_id: str,
    user: Annotated[dict, Depends(require_user)],
    service: Annotated[OrganizationService, Depends(get_service)],
):
    """Get organization details."""
    user_id = str(getattr(user, "id", user.get("sub", user.get("user_id"))))
    try:
        return service.get_organization(org_id, user_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Organization not found")


@router.post("/{org_id}/members", status_code=status.HTTP_201_CREATED)
def invite_member(
    org_id: str,
    payload: MemberInvite,
    user: Annotated[dict, Depends(require_user)],
    service: Annotated[OrganizationService, Depends(get_service)],
):
    """Invite a member to the organization."""
    user_id = str(getattr(user, "id", user.get("sub", user.get("user_id"))))
    try:
        return service.invite_member(org_id, payload.email, payload.role, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=domain_detail(e, 403)) from e
    except LookupError:
        raise HTTPException(status_code=404, detail="Organization not found")


@router.delete("/{org_id}/members/{member_id}")
def remove_member(
    org_id: str,
    member_id: str,
    user: Annotated[dict, Depends(require_user)],
    service: Annotated[OrganizationService, Depends(get_service)],
):
    """Remove a member from the organization."""
    user_id = str(getattr(user, "id", user.get("sub", user.get("user_id"))))
    try:
        return service.remove_member(org_id, member_id, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=domain_detail(e, 403)) from e
    except LookupError:
        raise HTTPException(status_code=404, detail="Membership not found")


@router.put("/{org_id}")
def update_organization(
    org_id: str,
    payload: OrgUpdate,
    user: Annotated[dict, Depends(require_user)],
    service: Annotated[OrganizationService, Depends(get_service)],
):
    """Update organization settings."""
    user_id = str(getattr(user, "id", user.get("sub", user.get("user_id"))))
    try:
        return service.update_organization(org_id, payload.name, payload.description, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=domain_detail(e, 403)) from e
    except LookupError:
        raise HTTPException(status_code=404, detail="Organization not found")
