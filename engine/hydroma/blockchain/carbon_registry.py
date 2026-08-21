"""Carbon credit registry using blockchain.

Provides immutable registry for carbon projects and credits.
Uses in-memory storage for research mode (simulates blockchain).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ProjectStatus(Enum):
    """Carbon project status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    ACTIVE = "active"
    RETIRED = "retired"


@dataclass
class CarbonProject:
    """Carbon project on blockchain."""

    project_id: str
    owner: str
    project_type: str
    area_ha: float
    duration_years: int
    status: ProjectStatus = ProjectStatus.DRAFT
    credits_issued: float = 0.0
    credits_retired: float = 0.0
    verifier: str | None = None
    verified_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    tx_hash: str = ""


@dataclass
class CarbonCredit:
    """Carbon credit token."""

    credit_id: str
    project_id: str
    owner: str
    amount: float
    issued_at: datetime = field(default_factory=datetime.utcnow)
    retired: bool = False
    retired_at: datetime | None = None
    tx_hash: str = ""


class CarbonRegistry:
    """Carbon credit registry (blockchain simulation)."""

    def __init__(self):
        self.projects: dict[str, CarbonProject] = {}
        self.credits: dict[str, CarbonCredit] = {}
        self._tx_counter = 0

    def _generate_tx_hash(self) -> str:
        """Generate mock transaction hash."""
        self._tx_counter += 1
        return f"0x{uuid.uuid4().hex[:64]}"

    def register_project(
        self, owner: str, project_type: str, area_ha: float, duration_years: int
    ) -> CarbonProject:
        """Register a new carbon project."""
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        project = CarbonProject(
            project_id=project_id,
            owner=owner,
            project_type=project_type,
            area_ha=area_ha,
            duration_years=duration_years,
            status=ProjectStatus.SUBMITTED,
            tx_hash=self._generate_tx_hash(),
        )
        self.projects[project_id] = project
        return project

    def verify_project(self, project_id: str, verifier: str) -> CarbonProject:
        """Verify a carbon project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        project = self.projects[project_id]
        if project.status != ProjectStatus.SUBMITTED:
            raise ValueError(f"Project cannot be verified from status: {project.status.value}")

        project.status = ProjectStatus.VERIFIED
        project.verifier = verifier
        project.verified_at = datetime.utcnow()
        project.tx_hash = self._generate_tx_hash()

        return project

    def issue_credits(self, project_id: str, amount: float, owner: str) -> CarbonCredit:
        """Issue carbon credits for a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        project = self.projects[project_id]
        if project.status not in [ProjectStatus.VERIFIED, ProjectStatus.ACTIVE]:
            raise ValueError("Project must be verified to issue credits")

        credit_id = f"cred_{uuid.uuid4().hex[:8]}"
        credit = CarbonCredit(
            credit_id=credit_id,
            project_id=project_id,
            owner=owner,
            amount=amount,
            tx_hash=self._generate_tx_hash(),
        )

        self.credits[credit_id] = credit
        project.credits_issued += amount
        project.status = ProjectStatus.ACTIVE

        return credit

    def transfer_credits(self, credit_id: str, from_owner: str, to_owner: str) -> CarbonCredit:
        """Transfer carbon credits between owners."""
        if credit_id not in self.credits:
            raise ValueError(f"Credit not found: {credit_id}")

        credit = self.credits[credit_id]
        if credit.owner != from_owner:
            raise ValueError(f"Credit not owned by {from_owner}")

        if credit.retired:
            raise ValueError("Cannot transfer retired credits")

        credit.owner = to_owner
        credit.tx_hash = self._generate_tx_hash()

        return credit

    def retire_credits(self, credit_id: str, owner: str) -> CarbonCredit:
        """Retire carbon credits (permanently remove from circulation)."""
        if credit_id not in self.credits:
            raise ValueError(f"Credit not found: {credit_id}")

        credit = self.credits[credit_id]
        if credit.owner != owner:
            raise ValueError(f"Credit not owned by {owner}")

        if credit.retired:
            raise ValueError("Credits already retired")

        credit.retired = True
        credit.retired_at = datetime.utcnow()
        credit.tx_hash = self._generate_tx_hash()

        # Update project
        project = self.projects[credit.project_id]
        project.credits_retired += credit.amount

        return credit

    def get_project(self, project_id: str) -> CarbonProject | None:
        """Get project by ID."""
        return self.projects.get(project_id)

    def get_credit(self, credit_id: str) -> CarbonCredit | None:
        """Get credit by ID."""
        return self.credits.get(credit_id)

    def get_projects_by_owner(self, owner: str) -> list[CarbonProject]:
        """Get all projects owned by an address."""
        return [p for p in self.projects.values() if p.owner == owner]

    def get_credits_by_owner(self, owner: str) -> list[CarbonCredit]:
        """Get all credits owned by an address."""
        return [c for c in self.credits.values() if c.owner == owner and not c.retired]

    def get_stats(self) -> dict:
        """Get registry statistics."""
        total_projects = len(self.projects)
        verified_projects = sum(
            1 for p in self.projects.values() if p.status == ProjectStatus.VERIFIED
        )
        active_projects = sum(1 for p in self.projects.values() if p.status == ProjectStatus.ACTIVE)

        total_credits = len(self.credits)
        active_credits = sum(1 for c in self.credits.values() if not c.retired)
        retired_credits = sum(1 for c in self.credits.values() if c.retired)

        total_carbon_issued = sum(p.credits_issued for p in self.projects.values())
        total_carbon_retired = sum(p.credits_retired for p in self.projects.values())

        return {
            "total_projects": total_projects,
            "verified_projects": verified_projects,
            "active_projects": active_projects,
            "total_credits": total_credits,
            "active_credits": active_credits,
            "retired_credits": retired_credits,
            "total_carbon_issued_tonnes": round(total_carbon_issued, 2),
            "total_carbon_retired_tonnes": round(total_carbon_retired, 2),
        }


# Singleton
_carbon_registry: CarbonRegistry | None = None


def get_carbon_registry() -> CarbonRegistry:
    """Get singleton carbon registry."""
    global _carbon_registry
    if _carbon_registry is None:
        _carbon_registry = CarbonRegistry()
    return _carbon_registry
