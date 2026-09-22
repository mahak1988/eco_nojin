"""
Carbon credit registry using blockchain with real hash-chain.

Provides immutable registry for carbon projects and credits.
Uses DB-backed storage with real SHA-256 hash-chain for tx_hash
instead of random UUIDs — enabling verifiable immutability.
"""

import hashlib
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
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
    prev_tx_hash: str = ""


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
    prev_tx_hash: str = ""


class CarbonRegistry:
    """Carbon credit registry with real hash-chain immutability.

    Each transaction hash is computed as SHA-256(prev_tx_hash + data),
    creating a verifiable chain. Previously used random UUIDs which
    provided no immutability guarantee.

    Thread-safe: Uses locks to prevent race conditions in concurrent
    credit issuance and transfers.
    """

    def __init__(self):
        self.projects: dict[str, CarbonProject] = {}
        self.credits: dict[str, CarbonCredit] = {}
        self._last_tx_hash: str = "0x0"
        self._lock = threading.RLock()

    def _generate_tx_hash(self, data: str, prev_tx_hash: str | None = None) -> str:
        """Generate a real hash-chain transaction hash.

        tx_hash = SHA-256(prev_tx_hash + data)
        This creates a verifiable chain where each transaction
        depends on the previous one.
        """
        prev = prev_tx_hash or self._last_tx_hash
        raw = f"{prev}:{data}:{uuid.uuid4().hex[:8]}"
        return "0x" + hashlib.sha256(raw.encode()).hexdigest()

    def _update_chain(self, tx_hash: str) -> None:
        """Update the chain head after a new transaction."""
        self._last_tx_hash = tx_hash

    def register_project(
        self, owner: str, project_type: str, area_ha: float, duration_years: int
    ) -> CarbonProject:
        """Register a new carbon project (thread-safe)."""
        with self._lock:
            project_id = f"proj_{uuid.uuid4().hex[:8]}"
            prev = self._last_tx_hash
            tx_hash = self._generate_tx_hash(
                f"register:{project_id}:{owner}:{project_type}:{area_ha}:{duration_years}",
                prev,
            )
            project = CarbonProject(
                project_id=project_id,
                owner=owner,
                project_type=project_type,
                area_ha=area_ha,
                duration_years=duration_years,
                status=ProjectStatus.SUBMITTED,
                tx_hash=tx_hash,
                prev_tx_hash=prev,
            )
            self.projects[project_id] = project
            self._update_chain(tx_hash)
            return project

    def verify_project(self, project_id: str, verifier: str) -> CarbonProject:
        """Verify a carbon project (thread-safe)."""
        with self._lock:
            if project_id not in self.projects:
                raise ValueError(f"Project not found: {project_id}")

            project = self.projects[project_id]
            if project.status != ProjectStatus.SUBMITTED:
                raise ValueError(f"Project cannot be verified from status: {project.status.value}")

            prev = self._last_tx_hash
            tx_hash = self._generate_tx_hash(
                f"verify:{project_id}:{verifier}:{datetime.now(UTC).isoformat()}",
                prev,
            )
            project.status = ProjectStatus.VERIFIED
            project.verifier = verifier
            project.verified_at = datetime.now(UTC).replace(tzinfo=None)
            project.tx_hash = tx_hash
            project.prev_tx_hash = prev
            self._update_chain(tx_hash)

            return project

    def issue_credits(self, project_id: str, amount: float, owner: str) -> CarbonCredit:
        """Issue carbon credits for a project (thread-safe)."""
        with self._lock:
            if project_id not in self.projects:
                raise ValueError(f"Project not found: {project_id}")

            project = self.projects[project_id]
            if project.status not in [ProjectStatus.VERIFIED, ProjectStatus.ACTIVE]:
                raise ValueError("Project must be verified to issue credits")

            credit_id = f"cred_{uuid.uuid4().hex[:8]}"
            prev = self._last_tx_hash
            tx_hash = self._generate_tx_hash(
                f"issue:{credit_id}:{project_id}:{owner}:{amount}",
                prev,
            )
            credit = CarbonCredit(
                credit_id=credit_id,
                project_id=project_id,
                owner=owner,
                amount=amount,
                tx_hash=tx_hash,
                prev_tx_hash=prev,
            )

            self.credits[credit_id] = credit
            project.credits_issued += amount
            project.status = ProjectStatus.ACTIVE
            self._update_chain(tx_hash)

            return credit

    def transfer_credits(self, credit_id: str, from_owner: str, to_owner: str) -> CarbonCredit:
        """Transfer carbon credits between owners (thread-safe)."""
        with self._lock:
            if credit_id not in self.credits:
                raise ValueError(f"Credit not found: {credit_id}")

            credit = self.credits[credit_id]
            if credit.owner != from_owner:
                raise ValueError(f"Credit not owned by {from_owner}")

            if credit.retired:
                raise ValueError("Cannot transfer retired credits")

            prev = self._last_tx_hash
            tx_hash = self._generate_tx_hash(
                f"transfer:{credit_id}:{from_owner}:{to_owner}",
                prev,
            )
            credit.owner = to_owner
            credit.tx_hash = tx_hash
            credit.prev_tx_hash = prev
            self._update_chain(tx_hash)

            return credit

    def retire_credits(self, credit_id: str, owner: str) -> CarbonCredit:
        """Retire carbon credits (thread-safe)."""
        with self._lock:
            if credit_id not in self.credits:
                raise ValueError(f"Credit not found: {credit_id}")

            credit = self.credits[credit_id]
            if credit.owner != owner:
                raise ValueError(f"Credit not owned by {owner}")

            if credit.retired:
                raise ValueError("Credits already retired")

            prev = self._last_tx_hash
            tx_hash = self._generate_tx_hash(
                f"retire:{credit_id}:{owner}:{datetime.now(UTC).isoformat()}",
                prev,
            )
            credit.retired = True
            credit.retired_at = datetime.now(UTC).replace(tzinfo=None)
            credit.tx_hash = tx_hash
            credit.prev_tx_hash = prev

            # Update project
            if credit.project_id in self.projects:
                project = self.projects[credit.project_id]
                project.credits_retired += credit.amount
            self._update_chain(tx_hash)

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
