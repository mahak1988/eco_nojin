"""Anti-greenwashing guard for carbon credit compliance.

Provides:
- Greenwashing detection by comparing declared claims against MRV data
- Disclosure record management (public/restricted/confidential)
- Suspicious pattern flagging (overstated sequestration, methodology mismatches)
- Project owner accountability through KYC linkage
- Public disclosure generation for audit trails

Honesty rules:
  * All assessments are based on REAL stored data (project state + MRV motor outputs).
  * No project is automatically approved; flags are advisory and require human review.
  * Disclosure content is verbatim (no fabricated or sanitized summaries).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from services.carbon.compliance.kyc_aml import KYCService

logger = logging.getLogger(__name__)


class DisclosureStatus(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


@dataclass
class DisclosureRecord:
    project_id: str
    credit_id: str | None
    disclosure_type: str
    status: DisclosureStatus
    content: dict[str, Any]
    disclosed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    reviewer: str | None = None
    methodology: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        if self.status == DisclosureStatus.CONFIDENTIAL:
            return {
                "project_id": self.project_id,
                "disclosure_type": self.disclosure_type,
                "status": self.status.value,
                "disclosed_at": self.disclosed_at.isoformat(),
                "redacted": True,
                "note": "Confidential disclosure — not available for public view",
            }
        if self.status == DisclosureStatus.RESTRICTED:
            return {
                "project_id": self.project_id,
                "disclosure_type": self.disclosure_type,
                "status": self.status.value,
                "disclosed_at": self.disclosed_at.isoformat(),
                "reviewer": self.reviewer,
                "methodology": self.methodology,
                "summary": self.content.get("summary", ""),
            }
        return {
            "project_id": self.project_id,
            "credit_id": self.credit_id,
            "disclosure_type": self.disclosure_type,
            "status": self.status.value,
            "disclosed_at": self.disclosed_at.isoformat(),
            "content": self.content,
            "reviewer": self.reviewer,
            "methodology": self.methodology,
        }


@dataclass
class GreenwashingFlag:
    flag_id: str
    project_id: str
    flag_type: str
    severity: str  # info, warning, critical
    description: str
    claim_value: Any
    actual_value: Any
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved: bool = False
    resolution_note: str | None = None


class GreenwashingGuard:
    """Detects and prevents greenwashing in carbon credit projects.

    Compares declared claims (from project registration / verification payloads)
    against actual MRV motor outputs and stored project state. All assessments
    are advisory — they produce flags that require human review before any
    enforcement action is taken.
    """

    def __init__(self, kyc_service: KYCService | None = None) -> None:
        self._kyc = kyc_service if kyc_service is not None else KYCService()
        self._flags: list[GreenwashingFlag] = []
        self._disclosures: list[DisclosureRecord] = []

    # ------------------------------------------------------------------ #
    # Greenwashing detection
    # ------------------------------------------------------------------ #

    def check_sequestration_claim(
        self,
        project_id: str,
        claimed_tonnes: float,
        actual_tonnes: float,
        methodology: str = "vm0032",
    ) -> list[GreenwashingFlag]:
        """Compare claimed vs actual sequestration for overstatement."""
        flags: list[GreenwashingFlag] = []
        if claimed_tonnes <= 0 or actual_tonnes <= 0:
            return flags

        ratio = actual_tonnes / claimed_tonnes
        if ratio < 0.5:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="sequestration_overstatement",
                    severity="critical",
                    description=(
                        f"Claimed {claimed_tonnes}t CO2e but MRV motor reports "
                        f"{actual_tonnes}t CO2e ({ratio:.1%} of claim)"
                    ),
                    claim_value=claimed_tonnes,
                    actual_value=actual_tonnes,
                )
            )
        elif ratio < 0.8:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="sequestration_discrepancy",
                    severity="warning",
                    description=(
                        f"Claimed {claimed_tonnes}t CO2e but MRV motor reports "
                        f"{actual_tonnes}t CO2e ({ratio:.1%} of claim)"
                    ),
                    claim_value=claimed_tonnes,
                    actual_value=actual_tonnes,
                )
            )
        else:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="sequestration_consistent",
                    severity="info",
                    description=(
                        f"Claimed {claimed_tonnes}t CO2e consistent with MRV "
                        f"motor ({actual_tonnes}t, {ratio:.1%})"
                    ),
                    claim_value=claimed_tonnes,
                    actual_value=actual_tonnes,
                )
            )
        return flags

    def check_methodology_consistency(
        self,
        project_id: str,
        registered_methodology: str,
        verified_methodology: str,
        motor_methodology: str,
    ) -> list[GreenwashingFlag]:
        """Ensure methodology is consistent across registration, verification, and motor."""
        flags: list[GreenwashingFlag] = []
        if registered_methodology != verified_methodology:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="methodology_mismatch",
                    severity="critical",
                    description=(
                        f"Registered as '{registered_methodology}' but verified as "
                        f"'{verified_methodology}'"
                    ),
                    claim_value=registered_methodology,
                    actual_value=verified_methodology,
                )
            )
        if verified_methodology != motor_methodology:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="motor_methodology_mismatch",
                    severity="warning",
                    description=(
                        f"Verified as '{verified_methodology}' but motor ran with "
                        f"'{motor_methodology}'"
                    ),
                    claim_value=verified_methodology,
                    actual_value=motor_methodology,
                )
            )
        return flags

    def check_permanence_claim(
        self,
        project_id: str,
        claimed_permanence: float,
        motor_permanence_factor: float,
    ) -> list[GreenwashingFlag]:
        """Verify permanence factor claims match motor output."""
        flags: list[GreenwashingFlag] = []
        if claimed_permanence > motor_permanence_factor + 0.05:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="permanence_overstatement",
                    severity="warning",
                    description=(
                        f"Claimed permanence {claimed_permanence:.2f} exceeds "
                        f"motor factor {motor_permanence_factor:.2f}"
                    ),
                    claim_value=claimed_permanence,
                    actual_value=motor_permanence_factor,
                )
            )
        return flags

    def check_credit_volume(
        self,
        project_id: str,
        area_ha: float,
        issued_tonnes: float,
        methodology: str = "vm0032",
    ) -> list[GreenwashingFlag]:
        """Check if issued credits are reasonable for the project area."""
        flags: list[GreenwashingFlag] = []
        typical_rate = 5.0  # tCO2e/ha/year (mid-range)
        max_expected = area_ha * typical_rate * 5  # 5-year generous window

        if issued_tonnes > max_expected * 2:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="excessive_credit_volume",
                    severity="critical",
                    description=(
                        f"Issued {issued_tonnes}t CO2e for {area_ha}ha — "
                        f"exceeds 2x typical rate ({max_expected:.0f}t expected)"
                    ),
                    claim_value=issued_tonnes,
                    actual_value=max_expected,
                )
            )
        elif issued_tonnes > max_expected:
            flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="high_credit_volume",
                    severity="warning",
                    description=(
                        f"Issued {issued_tonnes}t CO2e for {area_ha}ha — "
                        f"above typical rate ({max_expected:.0f}t expected)"
                    ),
                    claim_value=issued_tonnes,
                    actual_value=max_expected,
                )
            )
        return flags

    def run_full_assessment(
        self,
        project_id: str,
        *,
        claimed_tonnes: float | None = None,
        actual_tonnes: float | None = None,
        registered_methodology: str | None = None,
        verified_methodology: str | None = None,
        motor_methodology: str | None = None,
        claimed_permanence: float | None = None,
        motor_permanence_factor: float | None = None,
        area_ha: float | None = None,
        issued_tonnes: float | None = None,
    ) -> dict[str, Any]:
        """Run all greenwashing checks and return consolidated results."""
        all_flags: list[GreenwashingFlag] = []

        if claimed_tonnes is not None and actual_tonnes is not None:
            all_flags.extend(
                self.check_sequestration_claim(project_id, claimed_tonnes, actual_tonnes)
            )
        if registered_methodology and verified_methodology and motor_methodology:
            all_flags.extend(
                self.check_methodology_consistency(
                    project_id, registered_methodology, verified_methodology, motor_methodology
                )
            )
        if claimed_permanence is not None and motor_permanence_factor is not None:
            all_flags.extend(
                self.check_permanence_claim(project_id, claimed_permanence, motor_permanence_factor)
            )
        if area_ha is not None and issued_tonnes is not None:
            all_flags.extend(self.check_credit_volume(project_id, area_ha, issued_tonnes))

        self._flags.extend(all_flags)

        critical = [f for f in all_flags if f.severity == "critical"]
        warnings = [f for f in all_flags if f.severity == "warning"]

        return {
            "project_id": project_id,
            "total_flags": len(all_flags),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "assessment_passed": len(critical) == 0,
            "flags": [f.to_dict() for f in all_flags],
            "assessment_summary": (
                "CLEAN"
                if not critical and not warnings
                else "REVIEW_REQUIRED"
                if critical
                else "WATCH"
            ),
        }

    # ------------------------------------------------------------------ #
    # Flag management
    # ------------------------------------------------------------------ #

    def get_flags(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """Return flags, optionally filtered by project_id."""
        if project_id:
            return [f.to_dict() for f in self._flags if f.project_id == project_id]
        return [f.to_dict() for f in self._flags]

    def resolve_flag(self, flag_id: str, resolution: str) -> bool:
        """Mark a flag as resolved with a resolution note."""
        for flag in self._flags:
            if flag.flag_id == flag_id:
                flag.resolved = True
                flag.resolution_note = resolution
                return True
        return False

    def get_unresolved_flags(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """Return unresolved flags."""
        flags = self.get_flags(project_id)
        return [f for f in flags if not f.get("resolved", False)]

    # ------------------------------------------------------------------ #
    # Disclosure management
    # ------------------------------------------------------------------ #

    def create_disclosure(
        self,
        project_id: str,
        credit_id: str | None,
        disclosure_type: str,
        content: dict[str, Any],
        status: DisclosureStatus = DisclosureStatus.RESTRICTED,
        methodology: str | None = None,
    ) -> DisclosureRecord:
        """Create a disclosure record for a project/credit."""
        record = DisclosureRecord(
            project_id=project_id,
            credit_id=credit_id,
            disclosure_type=disclosure_type,
            status=status,
            content=content,
            methodology=methodology,
        )
        self._disclosures.append(record)
        logger.info(
            "Disclosure created: project=%s type=%s status=%s",
            project_id,
            disclosure_type,
            status.value,
        )
        return record

    def get_disclosures(
        self,
        project_id: str | None = None,
        credit_id: str | None = None,
        status: DisclosureStatus | None = None,
    ) -> list[DisclosureRecord]:
        """Return disclosures, optionally filtered."""
        results = self._disclosures
        if project_id:
            results = [d for d in results if d.project_id == project_id]
        if credit_id:
            results = [d for d in results if d.credit_id == credit_id]
        if status:
            results = [d for d in results if d.status == status]
        return results

    def public_disclosure(self, project_id: str) -> dict[str, Any]:
        """Generate a public-facing disclosure summary for a project.

        Only includes PUBLIC and RESTRICTED disclosures (not CONFIDENTIAL).
        """
        disclosures = [
            d.to_public_dict()
            for d in self._disclosures
            if d.project_id == project_id and d.status != DisclosureStatus.CONFIDENTIAL
        ]
        flags = self.get_flags(project_id)
        unresolved = self.get_unresolved_flags(project_id)

        return {
            "project_id": project_id,
            "disclosure_note": (
                "This disclosure is for informational purposes only and does not "
                "constitute certification by any Validation/Verification Body."
            ),
            "disclosures": disclosures,
            "greenwashing_flags": flags,
            "unresolved_flags": unresolved,
            "compliance_status": ("CLEAR" if not unresolved else "UNDER_REVIEW"),
            "generated_at": datetime.now(UTC).isoformat(),
        }

    # ------------------------------------------------------------------ #
    # KYC linkage for project owner accountability
    # ------------------------------------------------------------------ #

    def verify_project_owner(
        self,
        project_id: str,
        owner_id: str,
    ) -> dict[str, Any]:
        """Link project owner to KYC record and verify compliance."""
        record = self._kyc.get_record(owner_id)
        if record is None:
            return {
                "project_id": project_id,
                "owner_id": owner_id,
                "kyc_status": "NO_RECORD",
                "compliant": False,
                "action_required": "Register owner in KYC system before issuance",
            }

        kyc_compliant = self._kyc.is_compliant(owner_id)
        risk = self._kyc.assess_risk(owner_id)

        result = {
            "project_id": project_id,
            "owner_id": owner_id,
            "kyc_status": record.status.value,
            "compliant": kyc_compliant,
            "risk_level": risk.value,
            "kyc_level": record.kyc_level,
        }

        if not kyc_compliant:
            result["action_required"] = "Resolve AML failures before credit issuance"
            self._flags.append(
                GreenwashingFlag(
                    flag_id=f"GW-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                    project_id=project_id,
                    flag_type="owner_aml_failure",
                    severity="critical",
                    description=f"Project owner {owner_id} has unresolved AML issues (risk: {risk.value})",
                    claim_value="compliant",
                    actual_value=f"risk={risk.value}",
                )
            )

        return result


@dataclass
class _FlagDictAdapter:
    """Helper to convert GreenwashingFlag to dict."""

    @staticmethod
    def to_dict(flag: GreenwashingFlag) -> dict[str, Any]:
        return {
            "flag_id": flag.flag_id,
            "project_id": flag.project_id,
            "flag_type": flag.flag_type,
            "severity": flag.severity,
            "description": flag.description,
            "claim_value": flag.claim_value,
            "actual_value": flag.actual_value,
            "detected_at": flag.detected_at.isoformat(),
            "resolved": flag.resolved,
            "resolution_note": flag.resolution_note,
        }


GreenwashingFlag.to_dict = _FlagDictAdapter.to_dict  # type: ignore[assignment]
