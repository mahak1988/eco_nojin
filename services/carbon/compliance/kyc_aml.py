"""Carbon credit compliance module.

Provides KYC/AML, greenwashing prevention, and regulatory safeguards for
carbon credit issuance and tokenization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RiskLevel(StrEnum):
    """Risk level for KYC/AML assessment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KYCStatus(StrEnum):
    """KYC verification status."""

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class AMLCheck:
    """Anti-money laundering check result."""

    check_type: str
    status: str  # passed, failed, flagged
    risk_level: RiskLevel
    details: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KYCRecord:
    """Know Your Customer record."""

    user_id: str
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    date_of_birth: str | None = None
    kyc_level: str = "basic"  # basic, enhanced, institutional
    status: KYCStatus = KYCStatus.PENDING
    risk_level: RiskLevel = RiskLevel.LOW
    aml_checks: list[AMLCheck] = field(default_factory=list)
    verified_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# Sanctioned jurisdictions (FATF, OFAC, EU, UN)
SANCTIONED_JURISDICTIONS = {
    "AF",
    "BY",
    "CF",
    "CD",
    "CY",
    "ER",
    "IR",
    "IQ",
    "LB",
    "LY",
    "KP",
    "SD",
    "SY",
    "VE",
    "YE",
    "RU",
    "MM",
}

HIGH_RISK_JURISDICTIONS = {
    "AF",
    "BD",
    "BO",
    "BR",
    "CF",
    "CG",
    "IQ",
    "IR",
    "LA",
    "LY",
    "MM",
    "NP",
    "PA",
    "SD",
    "SY",
    "YE",
}


class KYCService:
    """Know Your Customer and Anti-Money Laundering service."""

    def __init__(self):
        self._records: dict[str, KYCRecord] = {}

    def register_user(self, user_id: str, **kwargs) -> KYCRecord:
        """Register a new KYC record for a user."""
        if user_id in self._records:
            raise ValueError(f"KYC record already exists for user {user_id}")

        record = KYCRecord(user_id=user_id, **kwargs)
        self._records[user_id] = record
        return record

    def get_record(self, user_id: str) -> KYCRecord | None:
        """Get KYC record for a user."""
        return self._records.get(user_id)

    def update_record(self, user_id: str, **kwargs) -> KYCRecord | None:
        """Update an existing KYC record."""
        record = self._records.get(user_id)
        if not record:
            return None
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record.updated_at = datetime.now(UTC)
        return record

    def run_aml_checks(self, user_id: str) -> list[AMLCheck]:
        """Run AML checks for a user."""
        record = self._records.get(user_id)
        if not record:
            raise ValueError(f"No KYC record for user {user_id}")

        checks = []

        # Check 1: Sanctioned jurisdiction
        jurisdiction_ok = record.country not in SANCTIONED_JURISDICTIONS
        checks.append(
            AMLCheck(
                check_type="sanctioned_jurisdiction",
                status="passed" if jurisdiction_ok else "failed",
                risk_level=RiskLevel.HIGH if not jurisdiction_ok else RiskLevel.LOW,
                details=f"Country {record.country} is {'not ' if jurisdiction_ok else ''}sanctioned",
            )
        )

        # Check 2: High-risk jurisdiction
        high_risk = record.country in HIGH_RISK_JURISDICTIONS
        checks.append(
            AMLCheck(
                check_type="high_risk_jurisdiction",
                status="flagged" if high_risk else "passed",
                risk_level=RiskLevel.MEDIUM if high_risk else RiskLevel.LOW,
                details=f"Country {record.country} is {'high-risk' if high_risk else 'standard'}",
            )
        )

        # Check 3: Email format
        email_ok = bool(record.email) and bool(
            re.match(r"^[^@]+@[^@]+\.[^@]+$", record.email or "")
        )
        checks.append(
            AMLCheck(
                check_type="email_format",
                status="passed" if email_ok else "failed",
                risk_level=RiskLevel.LOW,
                details="Email format valid" if email_ok else "Invalid email format",
            )
        )

        # Check 4: Phone format
        phone_ok = bool(record.phone) and bool(re.match(r"^\+?[0-9]{10,15}$", record.phone or ""))
        checks.append(
            AMLCheck(
                check_type="phone_format",
                status="passed" if phone_ok else "failed",
                risk_level=RiskLevel.LOW,
                details="Phone format valid" if phone_ok else "Invalid phone format",
            )
        )

        # Check 5: Date of birth
        dob_ok = bool(record.date_of_birth)
        checks.append(
            AMLCheck(
                check_type="date_of_birth",
                status="passed" if dob_ok else "failed",
                risk_level=RiskLevel.LOW,
                details="Date of birth provided" if dob_ok else "Missing date of birth",
            )
        )

        record.aml_checks = checks

        # Calculate overall risk level
        max_risk = RiskLevel.LOW
        for check in checks:
            if check.risk_level.value > max_risk.value:
                max_risk = check.risk_level
        record.risk_level = max_risk

        return checks

    def assess_risk(self, user_id: str) -> RiskLevel:
        """Assess overall risk level for a user."""
        record = self._records.get(user_id)
        if not record:
            return RiskLevel.CRITICAL
        return record.risk_level

    def is_compliant(self, user_id: str) -> bool:
        """Check if user passes all AML checks."""
        record = self._records.get(user_id)
        if not record:
            return False
        return all(check.status != "failed" for check in record.aml_checks)

    def verify_kyc(self, user_id: str) -> bool:
        """Mark KYC record as verified."""
        record = self._records.get(user_id)
        if not record:
            return False
        record.status = KYCStatus.VERIFIED
        record.verified_at = datetime.now(UTC)
        return True

    def reject_kyc(self, user_id: str, reason: str = "") -> bool:
        """Reject KYC record."""
        record = self._records.get(user_id)
        if not record:
            return False
        record.status = KYCStatus.REJECTED
        return True


# Singleton
_kyc_service: KYCService | None = None


def get_kyc_service() -> KYCService:
    """Get singleton KYC service."""
    global _kyc_service
    if _kyc_service is None:
        _kyc_service = KYCService()
    return _kyc_service
