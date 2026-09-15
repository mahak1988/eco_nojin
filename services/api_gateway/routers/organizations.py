"""Organization management API router.

Endpoints for multi-tenant SaaS organization management.
Uses existing Organization and OrganizationMembership models from database.models.
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from services.api_gateway.auth import require_user
from database.hub import hub
from database.models import User, Organization, OrganizationMembership

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Create a new organization."""
    existing = db.execute(select(Organization).where(Organization.slug == payload.slug)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Organization slug already exists")

    org = Organization(
        name=payload.name,
        slug=payload.slug,
        country=payload.country,
        description=payload.description,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role="admin",
        status="active",
        joined_at=datetime.now(UTC),
    )
    db.add(membership)
    db.commit()

    logger.info("Organization created: %s (%s)", payload.name, org.id)
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "country": org.country,
        "description": org.description,
        "created_at": org.created_at.isoformat() if org.created_at else "",
    }


@router.get("")
def list_organizations(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """List organizations the user belongs to."""
    results = db.execute(
        select(Organization, OrganizationMembership)
        .join(OrganizationMembership, Organization.id == OrganizationMembership.organization_id)
        .where(OrganizationMembership.user_id == user.id, OrganizationMembership.status == "active")
    ).all()

    orgs = [
        {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "country": org.country,
            "description": org.description,
            "role": membership.role,
            "created_at": org.created_at.isoformat() if org.created_at else "",
        }
        for org, membership in results
    ]

    return {"organizations": orgs, "count": len(orgs)}


@router.get("/{org_id}")
def get_organization(
    org_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get organization details."""
    result = db.execute(
        select(Organization, OrganizationMembership)
        .join(OrganizationMembership, Organization.id == OrganizationMembership.organization_id)
        .where(Organization.id == org_id, OrganizationMembership.user_id == user.id)
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Organization not found")

    org, membership = result
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "country": org.country,
        "description": org.description,
        "user_role": membership.role,
        "created_at": org.created_at.isoformat() if org.created_at else "",
    }


@router.post("/{org_id}/members", status_code=status.HTTP_201_CREATED)
def invite_member(
    org_id: str,
    payload: MemberInvite,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Invite a member to the organization."""
    membership = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user.id,
        )
    ).scalar_one_or_none()

    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invite members")

    org = db.execute(select(Organization).where(Organization.id == org_id)).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    new_membership = OrganizationMembership(
        organization_id=org_id,
        user_id=str(uuid.uuid4()),  # Placeholder — would lookup by email in production
        role=payload.role,
        joined_at=datetime.now(UTC),
        status="invited",
    )
    db.add(new_membership)
    db.commit()

    return {
        "id": new_membership.id,
        "organization_id": org_id,
        "email": payload.email,
        "role": payload.role,
        "status": "invited",
        "message": f"Invitation sent to {payload.email}",
    }


@router.delete("/{org_id}/members/{member_id}")
def remove_member(
    org_id: str,
    member_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Remove a member from the organization."""
    caller = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user.id,
        )
    ).scalar_one_or_none()

    if not caller or caller.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove members")

    membership = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.id == member_id,
        )
    ).scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    db.delete(membership)
    db.commit()

    return {"status": "removed", "member_id": member_id}


@router.put("/{org_id}")
def update_organization(
    org_id: str,
    payload: OrgUpdate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Update organization settings."""
    caller = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user.id,
        )
    ).scalar_one_or_none()

    if not caller or caller.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update organization")

    org = db.execute(select(Organization).where(Organization.id == org_id)).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if payload.name is not None:
        org.name = payload.name
    if payload.description is not None:
        org.description = payload.description

    db.commit()

    return {"id": org.id, "name": org.name, "description": org.description}
