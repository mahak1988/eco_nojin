"""Service for organization management — business logic layer."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from services.organization.repository import OrganizationRepository

logger = logging.getLogger(__name__)


class OrganizationService:
    """Business logic for organization management."""

    def __init__(self, db: Session):
        self.repo = OrganizationRepository(db)

    def create_organization(
        self,
        slug: str,
        name: str,
        country: str,
        description: str | None,
        user_id: str,
    ) -> dict:
        existing = self.repo.get_by_slug(slug)
        if existing:
            raise ValueError("Organization slug already exists")

        org = self.repo.create(name, slug, country, description)
        self.repo.create_membership(org.id, user_id, role="admin", status="active")

        logger.info("Organization created: %s (%s)", name, org.id)
        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "country": org.country,
            "description": org.description,
            "created_at": org.created_at.isoformat() if org.created_at else "",
        }

    def list_organizations(self, user_id: str) -> list[dict]:
        results = self.repo.list_user_orgs(user_id)
        return [
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

    def get_organization(self, org_id: str, user_id: str) -> dict:
        result = self.repo.get_user_org(org_id, user_id)
        if not result:
            raise LookupError("Organization not found")
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

    def invite_member(
        self,
        org_id: str,
        slug_email: str,
        role: str,
        user_id: str,
    ) -> dict:
        caller = self.repo.get_membership(org_id, user_id)
        if not caller or caller.role != "admin":
            raise PermissionError("Only admins can invite members")

        org = self.repo.get_by_id(org_id)
        if not org:
            raise LookupError("Organization not found")

        membership = self.repo.add_member(org_id, slug_email, role)
        return {
            "id": membership.id,
            "organization_id": org_id,
            "email": slug_email,
            "role": role,
            "status": "invited",
            "message": f"Invitation sent to {slug_email}",
        }

    def remove_member(
        self,
        org_id: str,
        member_id: str,
        user_id: str,
    ) -> dict:
        caller = self.repo.get_membership(org_id, user_id)
        if not caller or caller.role != "admin":
            raise PermissionError("Only admins can remove members")

        membership = self.repo.get_membership_by_id(org_id, member_id)
        if not membership:
            raise LookupError("Membership not found")

        self.repo.delete_membership(membership)
        return {"status": "removed", "member_id": member_id}

    def update_organization(
        self,
        org_id: str,
        name: str | None,
        description: str | None,
        user_id: str,
    ) -> None:
        caller = self.repo.get_membership(org_id, user_id)
        if not caller or caller.role != "admin":
            raise PermissionError("Only admins can update organization")

        org = self.repo.get_by_id(org_id)
        if not org:
            raise LookupError("Organization not found")

        self.repo.update_org(org, name, description)
        return {"id": org.id, "name": org.name, "description": org.description}
