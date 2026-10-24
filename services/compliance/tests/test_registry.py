"""P9 — the compliance registry enforces the honesty of its own claims.

The phase card's rules, pinned: an assessment requires a classification and
evidence; a compliant claim additionally requires the supporting reasoning
*and* a verified credential behind every mandatory requirement (the code never
upgrades a partial answer into a compliant one); a credential is verified by a
recorded verification; expiry sweeps; and the status view is evidence-linked —
there is no bare "compliant" flag to quote.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.compliance.models import (
    ComplianceAuditLog,
    Credential,
    CredentialStatus,
)
from services.compliance.service import (
    ComplianceConflict,
    ComplianceError,
    ComplianceService,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def _seeded(session, *, verified_credential: bool = True):
    """A jurisdiction, a source, one mandatory requirement, a classified seller.

    With ``verified_credential`` (the default) the seller also holds a
    *verified* credential, which is what a compliant assessment needs per
    mandatory requirement.
    """
    service = ComplianceService(session)
    jurisdiction = await service.add_jurisdiction(code="IR", name="Iran", country="IR")
    source = await service.add_source(
        name="Food and Drug Organisation", jurisdiction="IR", url="https://example.gov"
    )
    requirement = await service.add_requirement(
        source_id=str(source.id),
        jurisdiction_id=str(jurisdiction.id),
        activity_code="food.producer",
        title="Food production licence",
        mandatory=True,
    )
    classification = await service.classify_activity(
        subject_type="seller",
        subject_id="seller-1",
        activity_code="food.producer",
        jurisdiction_id=str(jurisdiction.id),
        classified_by="admin-1",
    )
    if verified_credential:
        credential = await service.register_credential(
            subject_type="seller",
            subject_id="seller-1",
            kind="trade_licence",
            reference="LIC-1",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        await service.verify_credential(
            str(credential.id),
            verifier_id="admin-1",
            method="issuer_api",
            evidence_ref="https://issuer.example/LIC-1",
            approve=True,
        )
    return service, jurisdiction, requirement, classification


async def test_assessment_requires_a_classification(session):
    service, jurisdiction, _r, _c = await _seeded(session)
    with pytest.raises(ComplianceError):
        await service.assess(
            subject_type="seller",
            subject_id="seller-2",  # not classified
            activity_code="food.producer",
            jurisdiction_id=str(jurisdiction.id),
            outcome="partial",
            evidence_ref="doc-1",
            assessed_by="admin-1",
        )


async def test_assessment_requires_evidence(session):
    service, jurisdiction, _r, _c = await _seeded(session)
    with pytest.raises(ComplianceError):
        await service.assess(
            subject_type="seller",
            subject_id="seller-1",
            activity_code="food.producer",
            jurisdiction_id=str(jurisdiction.id),
            outcome="partial",
            evidence_ref="",
            assessed_by="admin-1",
        )


async def test_conflicting_requirements_escalate_to_a_specialist(session):
    """Two sources disagreeing about one requirement never auto-resolve."""
    service = ComplianceService(session)
    jurisdiction = await service.add_jurisdiction(code="IR", name="Iran", country="IR")
    source_a = await service.add_source(
        name="Authority A", jurisdiction="IR", url="https://a.gov"
    )
    source_b = await service.add_source(
        name="Authority B", jurisdiction="IR", url="https://b.gov"
    )
    await service.add_requirement(
        source_id=str(source_a.id),
        jurisdiction_id=str(jurisdiction.id),
        activity_code="food.producer",
        title="Refrigeration log",
        mandatory=True,
    )
    await service.add_requirement(
        source_id=str(source_b.id),
        jurisdiction_id=str(jurisdiction.id),
        activity_code="food.producer",
        title="refrigeration log",
        mandatory=False,
    )
    await service.classify_activity(
        subject_type="seller",
        subject_id="seller-1",
        activity_code="food.producer",
        jurisdiction_id=str(jurisdiction.id),
        classified_by="admin-1",
    )
    with pytest.raises(ComplianceConflict):
        await service.assess(
            subject_type="seller",
            subject_id="seller-1",
            activity_code="food.producer",
            jurisdiction_id=str(jurisdiction.id),
            outcome="partial",
            evidence_ref="doc-1",
            assessed_by="admin-1",
        )


async def test_a_compliant_claim_requires_a_verified_credential(session):
    """A mandatory requirement without a verified credential cannot pass."""
    service, jurisdiction, _r, _c = await _seeded(session, verified_credential=False)
    with pytest.raises(ComplianceError, match="verified credential"):
        await service.assess(
            subject_type="seller",
            subject_id="seller-1",
            activity_code="food.producer",
            jurisdiction_id=str(jurisdiction.id),
            outcome="compliant",
            evidence_ref="doc-1",
            assessed_by="admin-1",
            note="licence claimed but nothing on file",
        )


async def test_a_compliant_claim_requires_its_reasoning(session):
    service, jurisdiction, _r, _c = await _seeded(session)
    with pytest.raises(ComplianceError):
        await service.assess(
            subject_type="seller",
            subject_id="seller-1",
            activity_code="food.producer",
            jurisdiction_id=str(jurisdiction.id),
            outcome="compliant",  # no note
            evidence_ref="doc-1",
            assessed_by="admin-1",
        )
    assessment = await service.assess(
        subject_type="seller",
        subject_id="seller-1",
        activity_code="food.producer",
        jurisdiction_id=str(jurisdiction.id),
        outcome="compliant",
        evidence_ref="doc-1",
        assessed_by="admin-1",
        note="licence on file, verified with the issuer",
    )
    assert assessment.outcome == "compliant"
    assert assessment.evidence_ref == "doc-1"


async def test_credential_verification_is_its_own_record(session):
    service, _j, _r, _c = await _seeded(session)
    credential = await service.register_credential(
        subject_type="seller",
        subject_id="seller-1",
        kind="trade_licence",
        reference="LIC-1",
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    assert credential.status == "pending"
    verified = await service.verify_credential(
        str(credential.id),
        verifier_id="admin-1",
        method="issuer_api",
        evidence_ref="https://issuer.example/LIC-1",
        approve=True,
    )
    assert verified.status == CredentialStatus.VERIFIED.value


async def test_expiry_sweep_marks_expired_credentials(session):
    service, _j, _r, _c = await _seeded(session)
    credential = await service.register_credential(
        subject_type="seller",
        subject_id="seller-1",
        kind="food_safety",
        expires_at=datetime.now(UTC) - timedelta(days=1),  # already past
    )
    expired = await service.sweep_expired()
    assert str(credential.id) in expired
    refreshed = (
        await session.execute(select(Credential).where(Credential.id == credential.id))
    ).scalar_one()
    assert refreshed.status == CredentialStatus.EXPIRED.value


async def test_status_view_is_evidence_linked(session):
    service, jurisdiction, _r, _c = await _seeded(session)
    await service.assess(
        subject_type="seller",
        subject_id="seller-1",
        activity_code="food.producer",
        jurisdiction_id=str(jurisdiction.id),
        outcome="partial",
        evidence_ref="doc-7",
        assessed_by="admin-1",
    )
    status = await service.subject_status("seller", "seller-1", str(jurisdiction.id))
    assert [a["outcome"] for a in status["assessments"]] == ["partial"]
    assert status["assessments"][0]["evidence_ref"] == "doc-7"


async def test_the_audit_log_records_the_path(session):
    service, _j, _r, _c = await _seeded(session)
    entries = (
        await session.execute(select(ComplianceAuditLog))
    ).scalars()
    actions = [entry.action for entry in entries]
    assert "activity_classified" in actions
