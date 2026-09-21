"""Carbon Credit Service - Sustainable & auditable carbon-credit MRV backend"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    CarbonCredit,
    CarbonCreditState,
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
    FreezeRequest,
    FrozenCreditError,
    InsufficientAvailableError,
    IssueCreditsRequest,
    IssueNotAllowedError,
    NotHolderError,
    ProjectNotFoundError,
    ProjectNotVerifiedError,
    RegisterProjectRequest,
    RetireRequest,
    TransferRequest,
    UnfreezeRequest,
    VerifyProjectRequest,
)
from services.carbon.verification import run_verification
from services.scientific_motors.base import MotorResult
from services.scientific_motors.carbon_mrv import CarbonMrvMotor


class DataMode(StrEnum):
    MODELLED_ESTIMATE = "modelled_estimate"
    FIELD_VERIFIED = "field_verified"


def _as_request(model, payload):
    """Accept a Pydantic request model or a plain mapping (legacy callers/tests)."""
    if isinstance(payload, model):
        return payload
    return model(**payload)


class CarbonService:
    """
    Sustainable & auditable carbon-credit MRV backend (Phase 8).

    Honesty contract (no fabricated hashes / no fake VVB claim):
    * Issuance amount comes from CarbonMrvMotor (IPCC tC->tCO2e x3.667 with
      a permanence deduction). That figure is reported as a *modelled/field*
      estimate, never as a "verified tonnage" by an external VVB.
    * Credits are ONLY issued when the project is `field_verified` OR carries
      MRV documents. Purely-modelled estimates may be registered & verified but
      yield no credit.
    * Idempotency keys are stored verbatim (no digest fabricated) so retries
      are safe.
    * No claim of endorsement by any real Validation/Verification Body (VVB).
      Verification is the honest, methodology-aligned check produced by
      `services.carbon.verification` plus the data-provenance flag returned by
      `CarbonMrvMotor` (`modelled_estimate` vs `field_verified`).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_project(self, project_id: str) -> CarbonProject:
        project = await self.db.scalar(
            select(CarbonProject).where(CarbonProject.project_id == project_id)
        )
        if not project:
            raise ProjectNotFoundError(project_id)
        return project

    async def _get_credit(self, credit_id: str) -> CarbonCredit:
        credit = await self.db.scalar(
            select(CarbonCredit).where(CarbonCredit.credit_id == credit_id)
        )
        if not credit:
            raise CreditNotFoundError(credit_id)
        return credit

    async def _get_idempotency(self, key: str, action: str) -> IdempotencyKey:
        return await self.db.scalar(
            select(IdempotencyKey).where(
                IdempotencyKey.key == key,
                IdempotencyKey.action == action,
            )
        )

    def _set_idempotency(
        self, key: str, action: str, result_reference: str, status: str = "completed"
    ):
        self.db.add(
            IdempotencyKey(
                key=key,
                action=action,
                result_reference=result_reference,
                status=status,
            )
        )

    async def register_project(self, req: RegisterProjectRequest) -> dict:
        req = _as_request(RegisterProjectRequest, req)
        existing = await self.db.scalar(
            select(CarbonProject).where(CarbonProject.project_id == req.project_id)
        )
        if existing:
            return {
                "project_id": existing.project_id,
                "status": "already_exists",
                "already_registered": True,
            }

        project = CarbonProject(
            project_id=req.project_id,
            name=req.name,
            user_id=req.owner_id,
            project_type=req.project_type,
            methodology=req.methodology,
            region=req.region or "",
            duration_years=req.duration_years,
            verification_status="unverified",
            field_verified=False,
            mrv_documents=req.mrv_documents or [],
            status=CarbonCreditState.DRAFT.value,
        )
        self.db.add(project)
        await self.db.flush()

        self._log_event(
            "project",
            req.project_id,
            "registered",
            req.owner_id,
            None,
            {"methodology": req.methodology},
        )

        return {"project_id": req.project_id, "status": "registered", "already_registered": False}

    async def submit_project(self, project_id: str, owner_id: str) -> dict:
        project = await self._get_project(project_id)
        if project.user_id != owner_id:
            raise ValueError("Not project owner")

        project.status = CarbonCreditState.SUBMITTED.value
        self._log_event("project", project_id, "submit", owner_id, None, {})
        return {"project_id": project_id, "status": "submitted"}

    async def verify_project(self, req: VerifyProjectRequest) -> dict:
        req = _as_request(VerifyProjectRequest, req)
        project = await self._get_project(req.project_id)

        # Run methodology checks
        checks = run_verification(
            baseline_activity=req.baseline_activity,
            has_financing=req.has_financing,
        )

        # Run MRV motor for data provenance
        motor_result = self._run_motor(
            soc_initial_t_ha=req.soc_initial_t_ha,
            soc_final_t_ha=req.soc_final_t_ha,
            area_ha=req.area_ha,
            measured_soc_t_ha=req.measured_soc_t_ha,
            baseline_activity=req.baseline_activity,
        )

        if motor_result.status.value != "completed":
            raise ValueError(motor_result.error_message or "MRV motor execution failed")

        data_mode = motor_result.outputs.get("data_mode", "modelled_estimate")

        project.verification_detail = json.dumps(
            {
                "methodology_checks": checks,
                "mrv_motor": motor_result.outputs,
            }
        )
        project.field_verified = data_mode == "field_verified"
        project.verification_status = "verified" if checks["passed"] else "rejected"
        project.status = (
            CarbonCreditState.VERIFIED.value
            if checks["passed"]
            else CarbonCreditState.SUBMITTED.value
        )

        self._log_event(
            "project",
            req.project_id,
            "verified",
            "system",
            None,
            {
                "checks_passed": checks["passed"],
                "data_mode": data_mode,
            },
        )

        return {
            "project_id": req.project_id,
            "status": project.status,
            "verification_status": project.verification_status,
            "field_verified": project.field_verified,
            "data_mode": data_mode,
            "methodology_checks": checks,
            "checks": checks,
        }

    def _run_motor(
        self,
        soc_initial_t_ha: float,
        soc_final_t_ha: float,
        area_ha: float,
        measured_soc_t_ha: float | None,
        baseline_activity: str,
        methodology: str = "vm0032",
        permanence_factor: float = 0.85,
    ) -> MotorResult:
        motor = CarbonMrvMotor()
        parameters = {
            "soc_initial_t_ha": soc_initial_t_ha,
            "soc_final_t_ha": soc_final_t_ha,
            "area_ha": area_ha,
            "measured_soc_t_ha": measured_soc_t_ha,
            "methodology": methodology,
            "permanence_factor": permanence_factor,
            "baseline_activity": baseline_activity,
        }
        return motor.execute(parameters)

    async def issue_credits(self, req: IssueCreditsRequest) -> dict:
        req = _as_request(IssueCreditsRequest, req)
        # Check idempotency (keys are stored verbatim, never hashed)
        existing = await self._get_idempotency(req.idempotency_key, "issue")
        if existing and existing.status == "completed":
            return {"credit_id": existing.result_reference, "replay": "idempotent-replay"}
        if existing:
            # An in-flight (pending) key means another issuance is already running.
            raise DoubleIssuanceError(existing.result_reference or req.project_id)

        project = await self._get_project(req.project_id)
        if project.verification_status != "verified":
            raise ProjectNotVerifiedError(req.project_id)

        reasons = []
        if not project.field_verified:
            reasons.append("field_verified is false")
        if not project.mrv_documents:
            reasons.append("no MRV documents on project")
        if not (project.field_verified or project.mrv_documents):
            raise IssueNotAllowedError(req.project_id, reasons)

        motor_result = self._run_motor(
            soc_initial_t_ha=req.soc_initial_t_ha,
            soc_final_t_ha=req.soc_final_t_ha,
            area_ha=req.area_ha,
            measured_soc_t_ha=req.measured_soc_t_ha,
            baseline_activity="degraded pasture",
        )

        if motor_result.status.value != "completed":
            raise ValueError(motor_result.error_message or "MRV motor execution failed")

        data_mode = motor_result.outputs.get("data_mode", "modelled_estimate")
        certified_delta = Decimal(str(motor_result.outputs.get("certified_delta_co2e_total", 0.0)))

        if certified_delta <= 0:
            raise ValueError("No certified delta CO2e from MRV motor")

        issuer = req.issued_by or "system"
        credit = CarbonCredit(
            credit_id=f"CR-{uuid.uuid4().hex}",
            project_id=req.project_id,
            serial=f"SER-{uuid.uuid4().hex}",
            vintage_year=datetime.now(UTC).year,
            methodology=project.methodology,
            standard=project.standard if hasattr(project, "standard") else "",
            data_mode=data_mode,
            mrv_documents=project.mrv_documents,
            total_amount=certified_delta,
            retired_amount=Decimal("0"),
            available_amount=certified_delta,
            holder_id=project.user_id,
            state=CarbonCreditState.ACTIVE.value,
            issued_by=issuer,
            issued_at=datetime.now(UTC),
        )
        self.db.add(credit)
        await self.db.flush()

        self._log_credit_event(
            credit.credit_id, "issue", issuer, None, credit.total_amount, "credit_issuance"
        )

        self._set_idempotency(req.idempotency_key, "issue", credit.credit_id)

        return self._issue_result(credit, req.idempotency_key, "first_time")

    def _issue_result(self, credit: CarbonCredit, idempotency_key: str, replay: str) -> dict:
        return {
            "credit_id": credit.credit_id,
            "project_id": credit.project_id,
            "serial": credit.serial,
            "vintage_year": credit.vintage_year,
            "methodology": credit.methodology,
            "standard": credit.standard,
            "data_mode": credit.data_mode,
            "total_amount": str(credit.total_amount),
            "available_amount": str(credit.available_amount),
            "holder_id": credit.holder_id,
            "state": credit.state,
            "issued_by": credit.issued_by,
            "issued_at": credit.issued_at.isoformat() if credit.issued_at else None,
            "note": (
                "Accounting figure from CarbonMrvMotor (IPCC tC->tCO2e x3.667) with a "
                "permanence/uncertainty deduction. Not a certification by any VVB."
            ),
            "replay": replay,
        }

    async def transfer_credit(self, req: TransferRequest | dict[str, Any]) -> dict:
        req = _as_request(TransferRequest, req)
        credit_id = req.credit_id
        credit = await self._get_credit(credit_id)
        if credit.holder_id != req.actor:
            raise NotHolderError(credit_id, req.actor)
        if credit.frozen:
            raise FrozenCreditError(credit_id)
        if credit.state != CreditState.ACTIVE.value:
            raise CreditStateError(
                credit_id, f"cannot transfer credit in state {credit.state.value}"
            )

        existing = await self._get_idempotency(req.idempotency_key, "transfer_credit")
        if existing and existing.status == "completed":
            return {"credit_id": credit_id, "replay": "idempotent-replay"}

        amount = Decimal("0") if req.amount is None else Decimal(str(req.amount))
        old_holder = credit.holder_id
        credit.holder_id = req.to_holder_id
        credit.available_amount -= amount

        self._log_credit_event(credit_id, "transfer", "system", old_holder, amount, "transfer")
        self._log_credit_event(
            credit_id, "transfer", "system", req.to_holder_id, amount, "transfer"
        )

        self._set_idempotency(req.idempotency_key, "transfer_credit", credit_id)

        return {"credit_id": credit_id, "new_holder": req.to_holder_id, "amount": str(amount)}

    async def retire_credit(self, req: RetireRequest | dict[str, Any]) -> dict:
        req = _as_request(RetireRequest, req)
        credit_id = req.credit_id
        credit = await self._get_credit(credit_id)
        if credit.holder_id != req.actor:
            raise NotHolderError(credit_id, req.actor)
        if credit.state == CreditState.RETIRED.value:
            raise CreditStateError(credit_id, "credit already fully retired")
        if credit.frozen:
            raise FrozenCreditError(credit_id)

        existing = await self._get_idempotency(req.idempotency_key, "retire")
        if existing and existing.status == "completed":
            return {"credit_id": credit_id, "replay": "idempotent-replay"}

        amount = Decimal(str(req.amount)) if req.amount is not None else credit.available_amount
        if credit.available_amount < amount:
            raise InsufficientAvailableError(credit_id, amount, credit.available_amount)

        credit.retired_amount += amount
        credit.available_amount -= amount
        credit.version += 1
        if credit.available_amount <= 0:
            credit.state = CreditState.RETIRED.value

        self._log_credit_event(credit_id, "retire", req.actor, None, amount, "retirement")
        self._set_idempotency(req.idempotency_key, "retire", credit_id)

        return {
            "credit_id": credit_id,
            "retired_amount": str(amount),
            "remaining_amount": str(credit.available_amount),
            "state": credit.state.value if hasattr(credit.state, "value") else credit.state,
        }

    async def freeze_credit(self, freeze: FreezeRequest | dict[str, Any]) -> dict:
        req = _as_request(FreezeRequest, freeze)
        credit_id = req.credit_id
        credit = await self._get_credit(credit_id)
        if credit.frozen:
            return {"credit_id": credit_id, "status": "already_frozen"}

        old_state = credit.state.value if hasattr(credit.state, "value") else credit.state
        credit.frozen = True
        credit.frozen_by = req.actor
        credit.frozen_authority = req.authority
        credit.frozen_reason = req.reason
        credit.frozen_at = datetime.now(UTC)

        self._log_credit_event(
            credit_id,
            "freeze",
            req.actor,
            req.authority,
            None,
            "freeze",
            before_state=old_state,
            after_state="FROZEN",
        )
        return {"credit_id": credit_id, "status": "frozen"}

    async def unfreeze_credit(self, unfreeze: UnfreezeRequest | dict[str, Any]) -> dict:
        req = _as_request(UnfreezeRequest, unfreeze)
        credit_id = req.credit_id
        credit = await self._get_credit(credit_id)
        if not credit.frozen:
            raise CreditStateError(credit_id, "credit is not frozen")

        if credit.frozen_by != req.actor or credit.frozen_authority != req.authority:
            raise FrozenCreditError(credit_id)

        credit.frozen = False
        credit.frozen_by = None
        credit.frozen_authority = None
        credit.frozen_reason = None
        credit.frozen_at = None

        self._log_credit_event(
            credit_id,
            "unfreeze",
            req.actor,
            req.authority,
            None,
            "unfreeze",
            before_state="FROZEN",
            after_state=credit.state.value if hasattr(credit.state, "value") else credit.state,
        )
        return {"credit_id": credit_id, "status": "unfrozen"}

    async def credit_history(self, credit_id: str) -> list[dict]:
        result = await self.db.scalars(
            select(CreditAuditLog)
            .where(CreditAuditLog.credit_id == credit_id)
            .order_by(CreditAuditLog.created_at)
        )
        events = result.all()
        return [
            {
                "event_id": e.event_id,
                "event_type": e.action,
                "audit_id": e.audit_id,
                "actor": e.actor,
                "authority": e.authority,
                "reason": e.reason,
                "before_state": e.before_state,
                "after_state": e.after_state,
                "delta_amount": str(e.delta_amount) if e.delta_amount else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ]

    async def credit_stats(self, project_id: str | None = None) -> dict:
        stmt = select(CarbonCredit)
        if project_id:
            stmt = stmt.where(CarbonCredit.project_id == project_id)
        credits = (await self.db.scalars(stmt)).all()

        by_state: dict[str, int] = {}
        by_data_mode: dict[str, int] = {}
        total_issued = Decimal("0")
        total_retired = Decimal("0")
        for c in credits:
            state = c.state if isinstance(c.state, str) else c.state.value
            by_state[state] = by_state.get(state, 0) + 1
            data_mode = c.data_mode if isinstance(c.data_mode, str) else "modelled_estimate"
            by_data_mode[data_mode] = by_data_mode.get(data_mode, 0) + 1
            total_issued += Decimal(str(c.total_amount))
            total_retired += Decimal(str(c.retired_amount))

        return {
            "total_issued": total_issued,
            "total_retired": total_retired,
            "total_active": sum(1 for c in credits if c.state == CarbonCreditState.ACTIVE.value),
            "by_state": by_state,
            "by_data_mode": by_data_mode,
        }

    def _log_event(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        actor: str,
        authority: str | None,
        payload: dict,
        correlation_id: str | None = None,
    ):
        event = CarbonEvent(
            event_id=f"EVT-{uuid.uuid4().hex}",
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            actor=actor,
            authority=authority,
            reason=json.dumps(payload),
            correlation_id=correlation_id,
        )
        self.db.add(event)

    def _log_credit_event(
        self,
        credit_id: str,
        action: str,
        actor: str,
        authority: str | None,
        delta_amount: Decimal | None,
        reason: str,
        before_state: str | None = None,
        after_state: str | None = None,
    ):
        audit = CreditAuditLog(
            event_id=f"EVT-{uuid.uuid4().hex}",
            audit_id=f"AUD-{uuid.uuid4().hex}",
            credit_id=credit_id,
            project_id=None,  # would be filled from credit
            action=action,
            actor=actor,
            authority=authority,
            reason=reason,
            before_state=before_state,
            after_state=after_state,
            delta_amount=delta_amount,
        )
        self.db.add(audit)
