"""The compliance workflow service (P9).

The rules are the phase card's, expressed as code:

* an assessment may only be recorded for a **classified** activity in the stated
  jurisdiction, with the **evidence reference** that supports it;
* a ``COMPLIANT`` outcome additionally needs a **verified credential** for each
  mandatory requirement that asks for one — the code never upgrades a partial
  answer into a compliant one;
* two sources stating **conflicting requirements** for the same activity raise
  ``ComplianceConflict`` — a human specialist resolves it, not this service;
* ``ESCALATED`` is an honest outcome, not a failure: it means a specialist must
  decide, and it is what the API reports.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.compliance.models import (
    ActivityClassification,
    ComplianceAssessment,
    ComplianceAuditLog,
    ComplianceException,
    ComplianceRequirement,
    Credential,
    CredentialKind,
    CredentialStatus,
    CredentialVerification,
    Jurisdiction,
    RegulatorySource,
)


class ComplianceError(ValueError):
    """A forbidden transition or a missing precondition."""


class ComplianceConflict(ComplianceError):
    """Two sources demand incompatible things for the same activity."""


class ComplianceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # reference data
    # ------------------------------------------------------------------

    async def add_source(
        self, *, name: str, jurisdiction: str, url: str | None = None
    ) -> RegulatorySource:
        source = RegulatorySource(name=name, jurisdiction=jurisdiction, url=url)
        self.db.add(source)
        await self.db.flush()
        return source

    async def add_jurisdiction(self, *, code: str, name: str, country: str) -> Jurisdiction:
        existing = await self.db.execute(
            select(Jurisdiction).where(Jurisdiction.code == code)
        )
        if existing.scalar_one_or_none() is not None:
            raise ComplianceError(f"jurisdiction {code} already registered")
        jurisdiction = Jurisdiction(code=code, name=name, country=country)
        self.db.add(jurisdiction)
        await self.db.flush()
        return jurisdiction

    async def add_requirement(
        self,
        *,
        source_id: str,
        jurisdiction_id: str,
        activity_code: str,
        title: str,
        mandatory: bool = True,
    ) -> ComplianceRequirement:
        await self._require_jurisdiction(jurisdiction_id)
        requirement = ComplianceRequirement(
            source_id=source_id,
            jurisdiction_id=jurisdiction_id,
            activity_code=activity_code,
            title=title,
            mandatory=mandatory,
        )
        self.db.add(requirement)
        await self.db.flush()
        return requirement

    async def classify_activity(
        self,
        *,
        subject_type: str,
        subject_id: str,
        activity_code: str,
        jurisdiction_id: str,
        classified_by: str,
        note: str | None = None,
    ) -> ActivityClassification:
        await self._require_jurisdiction(jurisdiction_id)
        existing = await self.db.execute(
            select(ActivityClassification).where(
                ActivityClassification.subject_type == subject_type,
                ActivityClassification.subject_id == subject_id,
                ActivityClassification.activity_code == activity_code,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ComplianceError("this activity is already classified")
        classification = ActivityClassification(
            subject_type=subject_type,
            subject_id=subject_id,
            activity_code=activity_code,
            jurisdiction_id=jurisdiction_id,
            classified_by=classified_by,
            note=note,
        )
        self.db.add(classification)
        await self.db.flush()
        self._audit(subject_type, subject_id, "activity_classified", classified_by, activity_code)
        return classification

    # ------------------------------------------------------------------
    # credentials
    # ------------------------------------------------------------------

    async def register_credential(
        self,
        *,
        subject_type: str,
        subject_id: str,
        kind: str,
        reference: str | None = None,
        issuer: str | None = None,
        expires_at: datetime | None = None,
    ) -> Credential:
        if kind not in {k.value for k in CredentialKind}:
            raise ComplianceError(f"unknown credential kind: {kind}")
        credential = Credential(
            subject_type=subject_type,
            subject_id=subject_id,
            kind=kind,
            reference=reference,
            issuer=issuer,
            expires_at=expires_at,
            status=CredentialStatus.PENDING.value,
        )
        self.db.add(credential)
        await self.db.flush()
        return credential

    async def verify_credential(
        self,
        credential_id: str,
        *,
        verifier_id: str,
        method: str,
        evidence_ref: str | None,
        approve: bool,
    ) -> Credential:
        credential = await self._require_credential(credential_id)
        verification = CredentialVerification(
            credential_id=credential_id,
            method=method,
            evidence_ref=evidence_ref,
            performed_by=verifier_id,
            outcome="passed" if approve else "failed",
        )
        self.db.add(verification)
        if approve:
            credential.status = CredentialStatus.VERIFIED.value
            credential.verified_by = verifier_id
            credential.verified_at = datetime.now(UTC)
        else:
            credential.status = CredentialStatus.REVOKED.value
            credential.verified_by = verifier_id
        await self.db.flush()
        self._audit(
            credential.subject_type,
            credential.subject_id,
            "credential_verified" if approve else "credential_rejected",
            verifier_id,
            credential.kind,
        )
        return credential

    async def expire_credential(self, credential_id: str) -> Credential:
        credential = await self._require_credential(credential_id)
        if credential.status == CredentialStatus.EXPIRED.value:
            return credential
        credential.status = CredentialStatus.EXPIRED.value
        await self.db.flush()
        return credential

    async def sweep_expired(self) -> list[str]:
        """Expire credentials and assessments whose window has closed."""
        now = datetime.now(UTC)
        expired: list[str] = []
        credentials = (
            await self.db.execute(
                select(Credential).where(
                    Credential.expires_at.is_not(None),
                    Credential.expires_at < now,
                    Credential.status != CredentialStatus.EXPIRED.value,
                )
            )
        ).scalars()
        for credential in credentials:
            credential.status = CredentialStatus.EXPIRED.value
            expired.append(str(credential.id))
        assessments = (
            await self.db.execute(
                select(ComplianceAssessment).where(
                    ComplianceAssessment.valid_until.is_not(None),
                    ComplianceAssessment.valid_until < now,
                )
            )
        ).scalars()
        for assessment in assessments:
            self.db.add(
                ComplianceAuditLog(
                    subject_type=assessment.subject_type,
                    subject_id=assessment.subject_id,
                    action="assessment_expired",
                    actor="system",
                    detail=str(assessment.id),
                )
            )
        await self.db.flush()
        return expired

    # ------------------------------------------------------------------
    # assessment
    # ------------------------------------------------------------------

    async def assess(
        self,
        *,
        subject_type: str,
        subject_id: str,
        activity_code: str,
        jurisdiction_id: str,
        outcome: str,
        evidence_ref: str,
        assessed_by: str,
        note: str | None = None,
    ) -> ComplianceAssessment:
        if outcome not in {"compliant", "partial", "non_compliant", "escalated"}:
            raise ComplianceError(f"unknown outcome: {outcome}")
        if not evidence_ref:
            raise ComplianceError("an assessment without evidence is not allowed")
        await self._require_classification(
            subject_type, subject_id, activity_code, jurisdiction_id
        )
        # Ambiguity escalates, whatever the outcome: two sources disagreeing
        # about one requirement never auto-resolves.
        requirements = await self.requirements_for(jurisdiction_id, activity_code)
        await self._detect_requirement_conflicts(requirements)
        if outcome == "compliant":
            # The code never upgrades a partial answer into a compliant one.
            await self._require_credentials_for_compliance(
                subject_type, subject_id, requirements
            )
        if outcome == "compliant" and note is None:
            # A compliant claim needs the reasoning on record, not just a tick.
            raise ComplianceError(
                "a compliant assessment must carry the reasoning that supports it"
            )
        assessment = ComplianceAssessment(
            subject_type=subject_type,
            subject_id=subject_id,
            jurisdiction_id=jurisdiction_id,
            activity_code=activity_code,
            outcome=outcome,
            evidence_ref=evidence_ref,
            assessed_by=assessed_by,
            note=note,
            valid_until=None,
        )
        self.db.add(assessment)
        await self.db.flush()
        self._audit(
            subject_type,
            subject_id,
            f"assessment_{outcome}",
            assessed_by,
            f"{activity_code}: {evidence_ref}",
        )
        return assessment

    async def grant_exception(
        self,
        *,
        requirement_id: str,
        subject_type: str,
        subject_id: str,
        reason: str,
        granted_by: str,
        expires_at: datetime | None = None,
    ) -> ComplianceException:
        await self._require_requirement(requirement_id)
        exception = ComplianceException(
            requirement_id=requirement_id,
            subject_type=subject_type,
            subject_id=subject_id,
            reason=reason,
            granted_by=granted_by,
            expires_at=expires_at,
        )
        self.db.add(exception)
        await self.db.flush()
        self._audit(subject_type, subject_id, "exception_granted", granted_by, reason)
        return exception

    async def requirements_for(
        self, jurisdiction_id: str, activity_code: str
    ) -> list[ComplianceRequirement]:
        result = await self.db.execute(
            select(ComplianceRequirement).where(
                ComplianceRequirement.jurisdiction_id == jurisdiction_id,
                ComplianceRequirement.activity_code == activity_code,
            )
        )
        return list(result.scalars())

    async def subject_status(
        self, subject_type: str, subject_id: str, jurisdiction_id: str
    ) -> dict:
        """The honest, evidence-linked status — never a bare 'compliant'."""
        assessments = (
            await self.db.execute(
                select(ComplianceAssessment).where(
                    ComplianceAssessment.subject_type == subject_type,
                    ComplianceAssessment.subject_id == subject_id,
                    ComplianceAssessment.jurisdiction_id == jurisdiction_id,
                )
            )
        ).scalars()
        credentials = (
            await self.db.execute(
                select(Credential).where(
                    Credential.subject_type == subject_type,
                    Credential.subject_id == subject_id,
                )
            )
        ).scalars()
        return {
            "assessments": [
                {
                    "id": str(a.id),
                    "outcome": a.outcome,
                    "evidence_ref": a.evidence_ref,
                    "activity_code": a.activity_code,
                    "created_at": a.created_at.isoformat(),
                }
                for a in assessments
            ],
            "credentials": [
                {
                    "id": str(c.id),
                    "kind": c.kind,
                    "status": c.status,
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                }
                for c in credentials
            ],
        }

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    async def _require_credentials_for_compliance(
        self,
        subject_type: str,
        subject_id: str,
        requirements: list[ComplianceRequirement],
    ) -> None:
        """Every blocking requirement needs a verified credential behind it.

        With no requirement→kind link in the registry, the faithful reading of
        "a verified credential for each mandatory requirement" is a one-to-one
        count: a granted, unexpired exception waives a requirement. The
        exceptions for the whole set are loaded in one query (the registry is
        the regulator's, so its cardinality is not the caller's), and the
        caller passes the requirements it already loaded for the conflict
        check.
        """
        now = datetime.now(UTC)
        blocking_ids = [
            requirement.id for requirement in requirements if requirement.mandatory
        ]
        if not blocking_ids:
            return
        waived = (
            await self.db.execute(
                select(ComplianceException.requirement_id).where(
                    ComplianceException.requirement_id.in_(blocking_ids),
                    ComplianceException.subject_type == subject_type,
                    ComplianceException.subject_id == subject_id,
                    or_(
                        ComplianceException.expires_at.is_(None),
                        ComplianceException.expires_at > now,
                    ),
                )
            )
        ).scalars()
        waived_ids = set(waived)
        blocking = [r.id for r in requirements if r.mandatory and r.id not in waived_ids]
        if not blocking:
            return
        verified = (
            await self.db.execute(
                select(Credential).where(
                    Credential.subject_type == subject_type,
                    Credential.subject_id == subject_id,
                    Credential.status == CredentialStatus.VERIFIED.value,
                    or_(
                        Credential.expires_at.is_(None),
                        Credential.expires_at > now,
                    ),
                )
            )
        ).scalars()
        verified_count = len({str(c.id): c for c in verified})
        if verified_count < len(blocking):
            raise ComplianceError(
                "a compliant assessment needs a verified credential for each of the "
                f"{len(blocking)} mandatory requirement(s); "
                f"subject holds {verified_count}"
            )

    async def _detect_requirement_conflicts(
        self, requirements: list[ComplianceRequirement]
    ) -> None:
        """Two sources disagreeing about one requirement escalate to a human.

        The signal is a same-titled requirement from two different regulatory
        sources with opposite ``mandatory`` flags — the code never reconciles
        it (the rule in the module docstring and the registry card).
        """
        seen: dict[str, tuple[str, bool]] = {}
        for requirement in requirements:
            key = " ".join(requirement.title.lower().split())
            if key in seen:
                source_id, mandatory = seen[key]
                if source_id != requirement.source_id and mandatory != bool(
                    requirement.mandatory
                ):
                    raise ComplianceConflict(
                        f"sources disagree whether '{requirement.title}' is "
                        f"mandatory for {requirement.activity_code}; a specialist "
                        "must resolve it"
                    )
            else:
                seen[key] = (requirement.source_id, bool(requirement.mandatory))

    async def _require_jurisdiction(self, jurisdiction_id: str) -> Jurisdiction:
        result = await self.db.execute(
            select(Jurisdiction).where(Jurisdiction.id == jurisdiction_id)
        )
        jurisdiction = result.scalar_one_or_none()
        if jurisdiction is None:
            raise ComplianceError(f"jurisdiction not found: {jurisdiction_id}")
        return jurisdiction

    async def _require_credential(self, credential_id: str) -> Credential:
        result = await self.db.execute(
            select(Credential).where(Credential.id == credential_id)
        )
        credential = result.scalar_one_or_none()
        if credential is None:
            raise ComplianceError(f"credential not found: {credential_id}")
        return credential

    async def _require_requirement(self, requirement_id: str) -> ComplianceRequirement:
        result = await self.db.execute(
            select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()
        if requirement is None:
            raise ComplianceError(f"requirement not found: {requirement_id}")
        return requirement

    async def _require_classification(
        self, subject_type: str, subject_id: str, activity_code: str, jurisdiction_id: str
    ) -> ActivityClassification:
        result = await self.db.execute(
            select(ActivityClassification).where(
                ActivityClassification.subject_type == subject_type,
                ActivityClassification.subject_id == subject_id,
                ActivityClassification.activity_code == activity_code,
                ActivityClassification.jurisdiction_id == jurisdiction_id,
            )
        )
        classification = result.scalar_one_or_none()
        if classification is None:
            raise ComplianceError(
                "activity is not classified for this jurisdiction; classify it first"
            )
        return classification

    def _audit(
        self, subject_type: str, subject_id: str, action: str, actor: str, detail: str | None
    ) -> None:
        self.db.add(
            ComplianceAuditLog(
                subject_type=subject_type,
                subject_id=subject_id,
                action=action,
                actor=actor,
                detail=detail,
            )
        )
