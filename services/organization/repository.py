"""Repository for organization management — moves DB access out of router."""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Organization, OrganizationMembership


class OrganizationRepository:
    """All DB access for organization management lives here."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_slug(self, slug: str) -> Organization | None:
        return self.db.execute(
            select(Organization).where(Organization.slug == slug)
        ).scalar_one_or_none()

    def get_by_id(self, org_id: str) -> Organization | None:
        return self.db.execute(
            select(Organization).where(Organization.id == org_id)
        ).scalar_one_or_none()

    def create(self, name: str, slug: str, country: str, description: str | None) -> Organization:
        org = Organization(name=name, slug=slug, country=country, description=description)
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        return org

    def create_membership(
        self, org_id: str, user_id: str, role: str = "admin", status: str = "active"
    ) -> OrganizationMembership:
        membership = OrganizationMembership(
            organization_id=org_id,
            user_id=user_id,
            role=role,
            status=status,
            joined_at=datetime.now(UTC),
        )
        self.db.add(membership)
        self.db.commit()
        return membership

    def get_membership(
        self, org_id: str, user_id: str
    ) -> OrganizationMembership | None:
        return self.db.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.user_id == user_id,
            )
        ).scalar_one_or_none()

    def list_user_orgs(self, user_id: str) -> list[tuple[Organization, OrganizationMembership]]:
        return self.db.execute(
            select(Organization, OrganizationMembership)
            .join(OrganizationMembership, Organization.id == OrganizationMembership.organization_id)
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.status == "active",
            )
        ).all()

    def get_user_org(
        self, org_id: str, user_id: str
    ) -> tuple[Organization, OrganizationMembership] | None:
        return self.db.execute(
            select(Organization, OrganizationMembership)
            .join(OrganizationMembership, Organization.id == OrganizationMembership.organization_id)
            .where(
                Organization.id == org_id,
                OrganizationMembership.user_id == user_id,
            )
        ).first()

    def get_membership_by_id(self, org_id: str, member_id: str) -> OrganizationMembership | None:
        return self.db.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.id == member_id,
            )
        ).scalar_one_or_none()

    def delete_membership(self, membership: OrganizationMembership) -> None:
        self.db.delete(membership)
        self.db.commit()

    def update_org(self, org: Organization, name: str | None, description: str | None) -> None:
        if name is not None:
            org.name = name
        if description is not None:
            org.description = description
        self.db.commit()

    def add_member(
        self,
        org_id: str,
        email: str,
        role: str,
    ) -> OrganizationMembership:
        new_membership = OrganizationMembership(
            organization_id=org_id,
            user_id=str(_uuid.uuid4()),
            role=role,
            joined_at=datetime.now(UTC),
            status="invited",
        )
        self.db.add(new_membership)
        self.db.commit()
        return new_membership
