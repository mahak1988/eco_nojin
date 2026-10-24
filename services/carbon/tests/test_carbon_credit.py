"""Tests for the sustainable & auditable carbon-credit MRV backend.

These tests exercise ``CarbonService`` (the backend for the register/verify/
issue/transfer/retire/freeze/unfreeze/history/stats operations) against the
real ``CarbonMrvMotor`` accounting engine on an in-memory SQLite database.

Honesty assertions embedded in the suite:
  * Idempotency keys are stored verbatim (no fabricated hash).
  * No "verified by VVB" claim is ever produced.
  * Credits are only issued when ``field_verified`` or MRV documents exist.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from database.models import (
    CarbonCredit,
    CarbonEvent,
    CarbonProject,
    CreditAuditLog,
    IdempotencyKey,
)
from services.carbon.schemas import (
    CreditNotFoundError,
    CreditState,
    CreditStateError,
    DoubleIssuanceError,
    FrozenCreditError,
    InsufficientAvailableError,
    IssueNotAllowedError,
    NotHolderError,
    ProjectNotVerifiedError,
)
from services.carbon.service import CarbonService


# --------------------------------------------------------------------------- #
# Fixtures / builders
# --------------------------------------------------------------------------- #
@pytest.fixture
def service(async_db_session):
    return CarbonService(async_db_session)


async def _register(
    svc: CarbonService,
    project_id: str = "P-001",
    owner: str = "owner-1",
    mrv_documents: list[str] | None = None,
) -> None:
    await svc.register_project(
        {
            "project_id": project_id,
            "name": "Demo agroforestry",
            "project_type": "afforestation",
            "area_ha": 100.0,
            "methodology": "vm0032",
            "region": "IR-KH",
            "duration_years": 30,
            "owner_id": owner,
            "mrv_documents": mrv_documents,
        }
    )


SOC_PARAMS = {
    "soc_initial_t_ha": 100.0,
    "soc_final_t_ha": 120.0,
    "area_ha": 100.0,
    "methodology": "vm0032",
    "permanence_factor": 0.85,
    "baseline_activity": "degraded pasture",
}


async def _verify(
    svc: CarbonService, project_id: str = "P-001", measured_soc: float | None = 100.0
) -> None:
    await svc.verify_project(
        {
            "project_id": project_id,
            **SOC_PARAMS,
            "measured_soc_t_ha": measured_soc,
        }
    )


async def _issue(
    svc: CarbonService,
    project_id: str = "P-001",
    idempotency_key: str = "issue-key-aaaaaaaa",
    measured_soc: float | None = 100.0,
    issuer: str = "issuer-A",
) -> dict:
    return await svc.issue_credits(
        {
            "project_id": project_id,
            "vintage_year": 2024,
            **SOC_PARAMS,
            "measured_soc_t_ha": measured_soc,
            "idempotency_key": idempotency_key,
            "issued_by": issuer,
        }
    )


# --------------------------------------------------------------------------- #
# Project lifecycle
# --------------------------------------------------------------------------- #
async def test_register_project_creates_draft(service, async_db_session):
    await _register(service)
    project = await async_db_session.scalar(
        select(CarbonProject).where(CarbonProject.project_id == "P-001")
    )
    assert project.status == CreditState.DRAFT.value
    assert project.verification_status == "unverified"
    assert project.field_verified is False


async def test_register_is_idempotent(service):
    first = await service.register_project(
        {
            "project_id": "P-DUP",
            "name": "a",
            "project_type": "afforestation",
            "area_ha": 10.0,
            "methodology": "vm0032",
            "duration_years": 30,
            "owner_id": "owner-1",
        }
    )
    second = await service.register_project(
        {
            "project_id": "P-DUP",
            "name": "a",
            "project_type": "afforestation",
            "area_ha": 10.0,
            "methodology": "vm0032",
            "duration_years": 30,
            "owner_id": "owner-1",
        }
    )
    assert first["already_registered"] is False
    assert second["already_registered"] is True
    assert second["project_id"] == "P-DUP"


async def test_submit_transitions_to_submitted(service, async_db_session):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    project = await async_db_session.scalar(
        select(CarbonProject).where(CarbonProject.project_id == "P-001")
    )
    assert project.status == CreditState.SUBMITTED.value
    events = (
        await async_db_session.scalars(
            select(CarbonEvent).where(CarbonEvent.aggregate_id == "P-001")
        )
    ).all()
    assert any(e.event_type == "submit" for e in events)


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #
async def test_verify_without_field_data_passes_checks(service, async_db_session):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    res = await service.verify_project(
        {**SOC_PARAMS, "project_id": "P-001", "measured_soc_t_ha": None}
    )
    assert res["methodology_checks"]["passed"] is True
    assert res["data_mode"] == "modelled_estimate"
    project = await async_db_session.scalar(
        select(CarbonProject).where(CarbonProject.project_id == "P-001")
    )
    assert project.field_verified is False
    assert project.verification_status == "verified"
    assert project.status == CreditState.VERIFIED.value


async def test_verify_with_field_data_marks_field_verified(service, async_db_session):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    res = await service.verify_project(
        {**SOC_PARAMS, "project_id": "P-001", "measured_soc_t_ha": 100.0}
    )
    assert res["data_mode"] == "field_verified"
    project = await async_db_session.scalar(
        select(CarbonProject).where(CarbonProject.project_id == "P-001")
    )
    assert project.field_verified is True


async def test_issue_blocked_when_project_not_verified(service):
    await _register(service)  # DRAFT, not verified
    with pytest.raises(ProjectNotVerifiedError):
        await _issue(service)


async def test_issue_blocked_without_field_verified_or_mrv(service, async_db_session):
    await _register(service)  # no mrv_documents
    await service.submit_project("P-001", "owner-1")
    await service.verify_project({**SOC_PARAMS, "project_id": "P-001", "measured_soc_t_ha": None})
    with pytest.raises(IssueNotAllowedError):
        await _issue(service, measured_soc=None)


# --------------------------------------------------------------------------- #
# Issuance + idempotency + double-issuance
# --------------------------------------------------------------------------- #
async def test_issue_mints_active_credit(service, async_db_session):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await _verify(service)
    res = await _issue(service)
    assert res["state"] == CreditState.ACTIVE.value
    assert Decimal(res["total_amount"]) > 0
    assert Decimal(res["available_amount"]) == Decimal(res["total_amount"])
    credit = await async_db_session.scalar(
        select(CarbonCredit).where(CarbonCredit.credit_id == res["credit_id"])
    )
    assert credit.data_mode == "field_verified"
    assert credit.holder_id == "owner-1"


async def test_issue_amount_matches_motor(service, async_db_session):
    from services.scientific_motors.carbon_mrv import CarbonMrvMotor

    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await _verify(service)
    res = await _issue(service)
    expected = CarbonMrvMotor().execute(
        {
            **SOC_PARAMS,
            "measured_soc_t_ha": 100.0,
        }
    )
    expected_amount = Decimal(str(expected.outputs["certified_delta_co2e_total"]))
    assert Decimal(res["total_amount"]) == expected_amount


async def test_issue_idempotent_same_key_no_double_mint(service, async_db_session):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await _verify(service)
    first = await _issue(service, idempotency_key="issue-key-aaaaaaaa")
    second = await _issue(service, idempotency_key="issue-key-aaaaaaaa")
    assert first["credit_id"] == second["credit_id"]
    assert second["replay"] == "idempotent-replay"
    # only one credit row exists
    total = (await async_db_session.scalars(select(CarbonCredit))).all()
    assert len(total) == 1


async def test_pending_idempotency_key_blocks_double_issuance(service):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await _verify(service)
    # Simulate an in-flight key by reserving it manually with status pending.
    idem = IdempotencyKey(
        key="issue-key-inflight",
        action="issue",
        status="pending",
        created_at=datetime.now(UTC),
    )
    service.db.add(idem)
    service.db.commit()
    with pytest.raises(DoubleIssuanceError):
        await _issue(service, idempotency_key="issue-key-inflight")


async def test_idempotency_key_stored_verbatim_not_hashed(service, async_db_session):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await _verify(service)
    await _issue(service, idempotency_key="issue-key-verbatim----")
    idem = await async_db_session.get(IdempotencyKey, "issue-key-verbatim----")
    assert idem is not None
    assert idem.key == "issue-key-verbatim----"  # verbatim, no digest
    assert idem.action == "issue"
    assert idem.status == "completed"


async def test_no_fake_vvb_claim_in_issue_result(service):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await _verify(service)
    res = await _issue(service)
    note = res["note"]
    assert "Not a certification by any VVB" in note
    assert "verified tonnage" not in note.lower()


# --------------------------------------------------------------------------- #
# MRV documents evidence floor (field_verified False but docs present)
# --------------------------------------------------------------------------- #
async def test_mrv_documents_allow_issuance_without_field_verified(service, async_db_session):
    await _register(service, mrv_documents=["doc/1", "doc/2"])
    await service.submit_project("P-001", "owner-1")
    await service.verify_project({**SOC_PARAMS, "project_id": "P-001", "measured_soc_t_ha": None})
    project = await async_db_session.scalar(
        select(CarbonProject).where(CarbonProject.project_id == "P-001")
    )
    assert project.field_verified is False
    assert project.mrv_documents == ["doc/1", "doc/2"]
    res = await _issue(service, measured_soc=None)  # credit data_mode modelled, still issued
    assert res["state"] == CreditState.ACTIVE.value


# --------------------------------------------------------------------------- #
# Transfer
# --------------------------------------------------------------------------- #
async def _full_issue(service) -> dict:
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await _verify(service)
    return await _issue(service)


async def test_transfer_blocked_for_non_holder(service):
    credit = await _full_issue(service)
    with pytest.raises(NotHolderError):
        await service.transfer_credit(
            {
                "credit_id": credit["credit_id"],
                "to_holder_id": "user-2",
                "actor": "not-the-holder",
                "idempotency_key": "tr-key-aaaaaaaa",
            }
        )


async def test_transfer_updates_holder(service, async_db_session):
    credit = await _full_issue(service)
    await service.transfer_credit(
        {
            "credit_id": credit["credit_id"],
            "to_holder_id": "user-2",
            "actor": "owner-1",
            "idempotency_key": "tr-key-aaaaaaaa",
        }
    )
    c = await async_db_session.scalar(
        select(CarbonCredit).where(CarbonCredit.credit_id == credit["credit_id"])
    )
    assert c.holder_id == "user-2"


async def test_transfer_frozen_blocked(service):
    credit = await _full_issue(service)
    await service.freeze_credit(
        {
            "credit_id": credit["credit_id"],
            "actor": "regulator",
            "authority": "Auth",
            "reason": "dispute",
        }
    )
    with pytest.raises(FrozenCreditError):
        await service.transfer_credit(
            {
                "credit_id": credit["credit_id"],
                "to_holder_id": "user-3",
                "actor": "owner-1",
                "idempotency_key": "tr-key-bbbbbbbb",
            }
        )


# --------------------------------------------------------------------------- #
# Freeze / unfreeze
# --------------------------------------------------------------------------- #
async def test_freeze_records_actor_and_authority(service, async_db_session):
    credit = await _full_issue(service)
    await service.freeze_credit(
        {
            "credit_id": credit["credit_id"],
            "actor": "regulator",
            "authority": "Gov Agency",
            "reason": "under review",
        }
    )
    c = await async_db_session.scalar(
        select(CarbonCredit).where(CarbonCredit.credit_id == credit["credit_id"])
    )
    assert c.frozen is True
    assert c.frozen_by == "regulator"
    assert c.frozen_authority == "Gov Agency"
    assert c.frozen_reason == "under review"
    assert c.frozen_at is not None


async def test_unfreeze_requires_matching_authority(service, async_db_session):
    credit = await _full_issue(service)
    await service.freeze_credit(
        {
            "credit_id": credit["credit_id"],
            "actor": "regulator",
            "authority": "Gov Agency",
            "reason": "under review",
        }
    )
    with pytest.raises(FrozenCreditError):
        await service.unfreeze_credit(
            {
                "credit_id": credit["credit_id"],
                "actor": "regulator",
                "authority": "Someone Else",
                "reason": "done",
            }
        )
    await service.unfreeze_credit(
        {
            "credit_id": credit["credit_id"],
            "actor": "regulator",
            "authority": "Gov Agency",
            "reason": "resolved",
        }
    )
    c = await async_db_session.scalar(
        select(CarbonCredit).where(CarbonCredit.credit_id == credit["credit_id"])
    )
    assert c.frozen is False


async def test_unfreeze_non_frozen_raises(service):
    credit = await _full_issue(service)
    with pytest.raises(CreditStateError):
        await service.unfreeze_credit(
            {
                "credit_id": credit["credit_id"],
                "actor": "regulator",
                "authority": "Gov Agency",
                "reason": "nope",
            }
        )


# --------------------------------------------------------------------------- #
# Retirement / double counting
# --------------------------------------------------------------------------- #
async def test_retire_partial_reduces_available(service, async_db_session):
    credit = await _full_issue(service)
    total = Decimal(credit["total_amount"])
    await service.retire_credit(
        {
            "credit_id": credit["credit_id"],
            "reason": "offset",
            "amount": 100.0,
            "actor": "owner-1",
            "idempotency_key": "ret-key-aaaaaaaa",
        }
    )
    c = await async_db_session.scalar(
        select(CarbonCredit).where(CarbonCredit.credit_id == credit["credit_id"])
    )
    assert c.retired_amount == Decimal("100.0")
    assert c.available_amount == total - Decimal("100.0")
    assert c.state.value == CreditState.ACTIVE.value


async def test_retire_full_marks_retired(service, async_db_session):
    credit = await _full_issue(service)
    total = Decimal(credit["total_amount"])
    await service.retire_credit(
        {
            "credit_id": credit["credit_id"],
            "reason": "full offset",
            "actor": "owner-1",
            "idempotency_key": "ret-key-bbbbbbbb",
        }
    )
    c = await async_db_session.scalar(
        select(CarbonCredit).where(CarbonCredit.credit_id == credit["credit_id"])
    )
    assert c.state.value == CreditState.RETIRED.value
    assert c.retired_amount == total
    assert c.available_amount == Decimal("0")


async def test_retire_over_available_blocked(service):
    credit = await _full_issue(service)
    with pytest.raises(InsufficientAvailableError):
        await service.retire_credit(
            {
                "credit_id": credit["credit_id"],
                "reason": "offset",
                "amount": 1_000_000,
                "actor": "owner-1",
                "idempotency_key": "ret-key-cccccccc",
            }
        )


async def test_retire_already_retired_blocked(service):
    credit = await _full_issue(service)
    await service.retire_credit(
        {
            "credit_id": credit["credit_id"],
            "reason": "full",
            "actor": "owner-1",
            "idempotency_key": "ret-key-dddddddd",
        }
    )
    with pytest.raises(CreditStateError):
        await service.retire_credit(
            {
                "credit_id": credit["credit_id"],
                "reason": "again",
                "actor": "owner-1",
                "idempotency_key": "ret-key-eeeeeeee",
            }
        )


async def test_retire_frozen_blocked(service):
    credit = await _full_issue(service)
    await service.freeze_credit(
        {
            "credit_id": credit["credit_id"],
            "actor": "regulator",
            "authority": "Gov Agency",
            "reason": "review",
        }
    )
    with pytest.raises(FrozenCreditError):
        await service.retire_credit(
            {
                "credit_id": credit["credit_id"],
                "reason": "offset",
                "amount": 1.0,
                "actor": "owner-1",
                "idempotency_key": "ret-key-ffffffff",
            }
        )


async def test_retire_idempotent_same_key(service, async_db_session):
    credit = await _full_issue(service)
    payload = {
        "credit_id": credit["credit_id"],
        "reason": "offset",
        "amount": 50.0,
        "actor": "owner-1",
        "idempotency_key": "ret-key-0000000a",
    }
    await service.retire_credit(payload)
    await service.retire_credit(payload)  # second call must not double-retire
    c = await async_db_session.scalar(
        select(CarbonCredit).where(CarbonCredit.credit_id == credit["credit_id"])
    )
    assert c.retired_amount == Decimal("50.0")


# --------------------------------------------------------------------------- #
# History + stats
# --------------------------------------------------------------------------- #
async def test_history_records_lifecycle_events(service, async_db_session):
    credit = await _full_issue(service)
    cid = credit["credit_id"]
    await service.transfer_credit(
        {
            "credit_id": cid,
            "to_holder_id": "user-2",
            "actor": "owner-1",
            "idempotency_key": "tr-key-history",
        }
    )
    await service.freeze_credit(
        {
            "credit_id": cid,
            "actor": "regulator",
            "authority": "Gov",
            "reason": "x",
        }
    )
    await service.unfreeze_credit(
        {
            "credit_id": cid,
            "actor": "regulator",
            "authority": "Gov",
            "reason": "ok",
        }
    )
    await service.retire_credit(
        {
            "credit_id": cid,
            "reason": "offset",
            "amount": 10.0,
            "actor": "user-2",
            "idempotency_key": "ret-key-history1",
        }
    )
    history = await service.credit_history(cid)
    types = [h["event_type"] for h in history]
    assert "issue" in types
    assert "transfer" in types
    assert "freeze" in types
    assert "unfreeze" in types
    assert "retire" in types
    assert all(h["event_id"].startswith("EVT-") for h in history)
    audit = (
        await async_db_session.scalars(
            select(CreditAuditLog).where(CreditAuditLog.credit_id == cid)
        )
    ).all()
    assert len(audit) >= 4  # issue, transfer, freeze, retire (+unfreeze)


async def test_stats_project_and_overall(service):
    credit = await _full_issue(service)
    before = await service.credit_stats(project_id="P-001")
    assert Decimal(before["total_issued"]) > 0
    assert before["by_state"][CreditState.ACTIVE.value] == 1
    # retire everything, then stats should reflect RETIRED
    await service.retire_credit(
        {
            "credit_id": credit["credit_id"],
            "reason": "full",
            "actor": "owner-1",
            "idempotency_key": "ret-key-stats--1",
        }
    )
    after = await service.credit_stats(project_id="P-001")
    assert Decimal(after["total_retired"]) > Decimal("0")
    assert after["by_state"].get(CreditState.RETIRED.value, 0) == 1
    assert after["by_state"].get(CreditState.ACTIVE.value, 0) == 0
    overall = await service.credit_stats()
    assert Decimal(overall["total_issued"]) >= Decimal(before["total_issued"])


# --------------------------------------------------------------------------- #
# Pydantic input validation
# --------------------------------------------------------------------------- #
async def test_pydantic_rejects_negative_area(service):
    with pytest.raises(ValidationError):
        await service.register_project(
            {
                "project_id": "P-X",
                "name": "x",
                "project_type": "a",
                "area_ha": -5,
                "methodology": "vm0032",
                "duration_years": 30,
                "owner_id": "o",
            }
        )


async def test_pydantic_rejects_short_idempotency_key(service):
    await _register(service)
    await service.submit_project("P-001", "owner-1")
    await service.verify_project({**SOC_PARAMS, "project_id": "P-001", "measured_soc_t_ha": 100.0})
    with pytest.raises(ValidationError):
        await service.issue_credits(
            {
                "project_id": "P-001",
                "vintage_year": 2024,
                **SOC_PARAMS,
                "measured_soc_t_ha": 100.0,
                "idempotency_key": "short",
                "issued_by": "issuer-A",
            }
        )


async def test_pydantic_rejects_negative_retire_amount(service):
    credit = await _full_issue(service)
    with pytest.raises(ValidationError):
        await service.retire_credit(
            {
                "credit_id": credit["credit_id"],
                "reason": "x",
                "amount": -5,
                "actor": "owner-1",
                "idempotency_key": "ret-key-neg-a",
            }
        )


async def test_credit_not_found_raises(service):
    with pytest.raises(CreditNotFoundError):
        await service.retire_credit(
            {
                "credit_id": "CR-DoesNotExist",
                "reason": "x",
                "amount": 1.0,
                "actor": "owner-1",
                "idempotency_key": "ret-key-nnnnnnn1",
            }
        )
