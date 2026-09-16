"""
CarbonService — sustainable & auditable carbon-credit MRV backend (Phase 8).

Public API surface (each maps to an intended API operation):
    register_project  -> POST /mrv/projects
    submit_project    -> POST /mrv/projects/{id}/submit
    verify_project    -> POST /mrv/projects/{id}/verify
    issue_credits     -> POST /mrv/credits/issue
    transfer_credit   -> POST /mrv/credits/{id}/transfer
    retire_credit     -> POST /mrv/credits/{id}/retire
    freeze_credit     -> POST /mrv/credits/{id}/freeze
    unfreeze_credit   -> POST /mrv/credits/{id}/unfreeze
    credit_history    -> GET  /mrv/credits/{id}/history
    credit_stats      -> GET  /mrv/credits/stats

Honesty contract (no fabricated hashes / no fake VVB claim):
  * Issuance amount comes from ``CarbonMrvMotor`` (IPCC tC->tCO2e x3.667 with a
    permanence deduction). That figure is reported as a *modelled/field*
    estimate, never as a "verified tonnage" by an external VVB.
  * Credits are ONLY issued when the project is ``field_verified`` OR carries
    MRV documents. Purely-modelled estimates may be registered & verified but
    yield no credit.
  * Idempotency keys are stored verbatim (no digest fabricated) so retries
    cannot mint a second credit or retire twice.

Double-issuance / double-counting safeguards:
  * ``issue``: idempotency-key guard + unique ``credit_id``/``serial``.
  * ``retire``: DB CHECK (``retired_amount <= total_amount``) + service check
    (``requested <= available_amount``) + idempotency on retire.
  * ``transfer``: only the current holder may transfer; frozen credits blocked;
    retirement cannot exceed available amount.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    CarbonCredit,
    CarbonCreditState,
    CarbonEvent,
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
    IssueCreditsRequest,
    IssueNotAllowedError,
    NotHolderError,
    ProjectNotFoundError,
    ProjectNotVerifiedError,
    RegisterProjectRequest,
    VerifyProjectRequest,
)
from services.scientific_motors.carbon_mrv import CarbonMrvMotor


def _now() -> datetime:
    return datetime.now(UTC)


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class CarbonService:
    """Transactional carbon-credit service backed by SQLAlchemy + CarbonMrvMotor."""

    def __init__(
        self,
        db: Session,
        motor: CarbonMrvMotor | None = None,
    ) -> None:
        self.db = db
        self.motor = motor if motor is not None else CarbonMrvMotor()

    # ------------------------------------------------------------------ #
    # Project lifecycle
    # ------------------------------------------------------------------ #
    def register_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        from database.models import CarbonProject

        req = RegisterProjectRequest(**payload)
        existing = self.db.scalar(
            select(CarbonProject).where(CarbonProject.project_id == req.project_id)
        )
        if existing is not None:
            return {
                "project_id": existing.project_id,
                "name": existing.name,
                "status": existing.status,
                "field_verified": existing.field_verified,
                "already_registered": True,
            }

        project = CarbonProject(
            project_id=req.project_id,
            name=req.name,
            project_type=req.project_type,
            area_hectares=req.area_ha,
            user_id=req.owner_id,
            status=CreditState.DRAFT.value,
            methodology=req.methodology,
            region=req.region,
            duration_years=req.duration_years,
            field_verified=False,
            verification_status="unverified",
            mrv_documents=list(req.mrv_documents) if req.mrv_documents else None,
        )
        self.db.add(project)
        self._event(
            aggregate="project",
            aggregate_id=req.project_id,
            event_type="register",
            actor=req.owner_id,
            payload={"project_type": req.project_type, "area_ha": req.area_ha},
        )
        self.db.commit()
        self.db.refresh(project)
        return {
            "project_id": project.project_id,
            "name": project.name,
            "status": project.status,
            "field_verified": project.field_verified,
            "already_registered": False,
        }

    def submit_project(self, project_id: str, actor: str) -> dict[str, Any]:

        project = self._get_project(project_id)
        project.status = CreditState.SUBMITTED.value
        project.updated_at = _now()
        self._event(aggregate="project", aggregate_id=project_id, event_type="submit", actor=actor)
        self.db.commit()
        self.db.refresh(project)
        return {"project_id": project_id, "status": project.status}

    def verify_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        from services.carbon.verification import run_verification

        req = VerifyProjectRequest(**payload)
        project = self._get_project(req.project_id)

        # Methodology checks (baseline / additionality / leakage / permanence)
        checks = run_verification(
            baseline_activity=req.baseline_activity,
            has_financing=req.has_financing,
            would_happen_without_project=req.would_happen_without_project,
            activity_displacement=req.activity_displacement,
            market_leakage=req.market_leakage,
            commitment_years=req.commitment_years,
            risk_flag=req.risk_flag,
        )

        # Honest MRV motor run -> establishes data provenance (data_mode)
        motor_result = self._run_motor(
            req.soc_initial_t_ha,
            req.soc_final_t_ha,
            req.area_ha,
            req.measured_soc_t_ha,
            req.measurements,
            req.methodology,
            req.permanence_factor,
        )
        if motor_result.status.value != "completed":
            raise ValueError(motor_result.error_message or "MRV motor execution failed")

        data_mode = motor_result.outputs.get("data_mode", "modelled_estimate")
        project.verification_detail = json.dumps(
            {"methodology_checks": checks, "mrv_motor": motor_result.outputs}
        )
        project.field_verified = data_mode == "field_verified"
        project.verification_status = "verified" if checks["passed"] else "rejected"
        project.status = (
            CreditState.VERIFIED.value if checks["passed"] else CreditState.SUBMITTED.value
        )
        project.updated_at = _now()

        self._event(
            aggregate="project",
            aggregate_id=req.project_id,
            event_type="verify",
            actor="verifier",
            payload={
                "checks_passed": checks["passed"],
                "failed_checks": checks["failed"],
                "data_mode": data_mode,
                "delta_co2e_total": motor_result.outputs.get("delta_co2e_total"),
            },
        )
        self.db.commit()
        self.db.refresh(project)
        return {
            "project_id": project.project_id,
            "status": project.status,
            "verification_status": project.verification_status,
            "field_verified": project.field_verified,
            "data_mode": data_mode,
            "methodology_checks": checks,
        }

    # ------------------------------------------------------------------ #
    # Issuance
    # ------------------------------------------------------------------ #
    def issue_credits(self, payload: dict[str, Any]) -> dict[str, Any]:
        req = IssueCreditsRequest(**payload)
        project = self._get_project(req.project_id)
        if project.verification_status != "verified":
            raise ProjectNotVerifiedError(req.project_id)

        # Evidence floor: no credits from purely-modelled estimates.
        reasons: list[str] = []
        if not project.field_verified:
            reasons.append("field_verified is false")
        if not project.mrv_documents:
            reasons.append("no MRV documents on project")
        if not (project.field_verified or project.mrv_documents):
            raise IssueNotAllowedError(req.project_id, reasons)

        # Idempotency: identical client key => same result, no second credit.
        existing = self.db.get(IdempotencyKey, req.idempotency_key)
        if existing is not None and existing.status == "completed":
            already = self.db.scalar(
                select(CarbonCredit).where(CarbonCredit.credit_id == existing.result_reference)
            )
            if already is not None:
                return self._issue_result(already, req.idempotency_key, "idempotent-replay")
        if existing is not None and existing.status == "pending":
            raise DoubleIssuanceError(existing.result_reference or req.idempotency_key)

        # Honest motor run -> the creditable amount.
        motor_result = self._run_motor(
            req.soc_initial_t_ha,
            req.soc_final_t_ha,
            req.area_ha,
            req.measured_soc_t_ha,
            req.measurements,
            req.methodology,
            req.permanence_factor,
        )
        if motor_result.status.value != "completed":
            raise ValueError(motor_result.error_message or "MRV motor execution failed")

        data_mode = motor_result.outputs.get("data_mode", "modelled_estimate")
        certified_delta = _to_decimal(motor_result.outputs.get("certified_delta_co2e_total", 0.0))
        if certified_delta <= 0:
            raise IssueNotAllowedError(
                req.project_id,
                [
                    "motor reported non-positive sequestration "
                    f"(delta={motor_result.outputs.get('delta_co2e_total')})"
                ],
            )

        # Reserve the idempotency key BEFORE committing the credit so a
        # concurrent duplicate request cannot slip through.
        idem = IdempotencyKey(
            key=req.idempotency_key,
            action="issue",
            result_reference=None,
            status="pending",
            created_at=_now(),
        )
        self.db.add(idem)
        self.db.flush()

        credit = CarbonCredit(
            credit_id=f"CR-{uuid4().hex}",
            project_id=req.project_id,
            vintage_year=req.vintage_year,
            methodology=req.methodology,
            standard=req.methodology,
            data_mode=data_mode,
            mrv_documents=project.mrv_documents,
            total_amount=certified_delta,
            retired_amount=Decimal("0"),
            available_amount=certified_delta,
            holder_id=project.user_id,
            state=CarbonCreditState.ACTIVE,
            issued_by=req.issued_by,
            issued_at=_now(),
            version=1,
        )
        self.db.add(credit)
        self.db.flush()

        idem.result_reference = credit.credit_id
        idem.status = "completed"

        project.credits_issued = _to_decimal(project.credits_issued) + certified_delta
        project.issued_at = project.issued_at or _now()
        project.updated_at = _now()

        self._event(
            aggregate="credit",
            aggregate_id=credit.credit_id,
            event_type="issue",
            actor=req.issued_by,
            correlation_id=req.idempotency_key,
            payload={
                "amount": str(certified_delta),
                "vintage_year": req.vintage_year,
                "data_mode": data_mode,
                "delta_co2e_total": motor_result.outputs.get("delta_co2e_total"),
                "permanence_factor": motor_result.outputs.get("permanence_factor"),
            },
        )
        self._audit(
            action="issue",
            credit_id=credit.credit_id,
            project_id=req.project_id,
            actor=req.issued_by,
            after_state=credit.state.value,
            delta_amount=certified_delta,
            correlation_id=req.idempotency_key,
        )
        self.db.commit()
        self.db.refresh(credit)
        return self._issue_result(credit, req.idempotency_key, "newly-issued")

    # ------------------------------------------------------------------ #
    # Transfer
    # ------------------------------------------------------------------ #
    def transfer_credit(self, payload: dict[str, Any]) -> dict[str, Any]:
        from services.carbon.schemas import TransferRequest

        req = TransferRequest(**payload)
        credit = self._get_credit(req.credit_id)
        if credit.state != CarbonCreditState.ACTIVE:
            raise CreditStateError(
                credit.credit_id, f"cannot transfer credit in state {credit.state.value}"
            )
        if credit.frozen:
            raise FrozenCreditError(credit.credit_id)
        # Only the current holder may move the credit.
        if credit.holder_id is not None and credit.holder_id != req.actor:
            raise NotHolderError(credit.credit_id, credit.holder_id)

        if req.idempotency_key:
            existing = self.db.get(IdempotencyKey, req.idempotency_key)
            target_ref = f"transfer:{credit.credit_id}:{req.to_holder_id}"
            if (
                existing is not None
                and existing.status == "completed"
                and existing.result_reference == target_ref
            ):
                self._event(
                    aggregate="credit",
                    aggregate_id=credit.credit_id,
                    event_type="transfer_replayed",
                    actor=req.actor,
                    correlation_id=req.idempotency_key,
                    payload={"to_holder_id": req.to_holder_id, "idempotent": True},
                )
                self.db.commit()
                return self._credit_view(credit)

        previous_holder = credit.holder_id
        credit.holder_id = req.to_holder_id
        credit.updated_at = _now()
        credit.version = credit.version + 1

        if req.idempotency_key:
            self.db.add(
                IdempotencyKey(
                    key=req.idempotency_key,
                    action="transfer",
                    result_reference=target_ref,
                    status="completed",
                    created_at=_now(),
                )
            )

        self._event(
            aggregate="credit",
            aggregate_id=credit.credit_id,
            event_type="transfer",
            actor=req.actor,
            correlation_id=req.idempotency_key,
            payload={"from": previous_holder, "to": req.to_holder_id},
        )
        self._audit(
            action="transfer",
            credit_id=credit.credit_id,
            project_id=credit.project_id,
            actor=req.actor,
            before_state=credit.state.value,
            after_state=credit.state.value,
            delta_amount=Decimal("0"),
            correlation_id=req.idempotency_key,
            reason=f"holder {previous_holder} -> {req.to_holder_id}",
        )
        self.db.commit()
        self.db.refresh(credit)
        return self._credit_view(credit)

    # ------------------------------------------------------------------ #
    # Retirement
    # ------------------------------------------------------------------ #
    def retire_credit(self, payload: dict[str, Any]) -> dict[str, Any]:
        from services.carbon.schemas import RetireRequest

        req = RetireRequest(**payload)
        credit = self._get_credit(req.credit_id)
        if credit.state == CarbonCreditState.RETIRED:
            raise CreditStateError(credit.credit_id, "credit already fully retired")
        if credit.frozen:
            raise FrozenCreditError(credit.credit_id)

        available = _to_decimal(credit.available_amount)
        amount = _to_decimal(req.amount) if req.amount is not None else available

        if req.idempotency_key:
            existing = self.db.get(IdempotencyKey, req.idempotency_key)
            if (
                existing is not None
                and existing.status == "completed"
                and existing.result_reference == f"retire:{credit.credit_id}:{amount!s}"
            ):
                self._event(
                    aggregate="credit",
                    aggregate_id=credit.credit_id,
                    event_type="retire_replayed",
                    actor=req.actor,
                    correlation_id=req.idempotency_key,
                    payload={"amount": str(amount), "idempotent": True},
                )
                self.db.commit()
                return self._credit_view(credit)

        if amount <= 0:
            raise InsufficientAvailableError(credit.credit_id, amount, available)
        if amount > available:
            raise InsufficientAvailableError(credit.credit_id, amount, available)

        credit.retired_amount = _to_decimal(credit.retired_amount) + amount
        credit.available_amount = _to_decimal(credit.available_amount) - amount
        credit.version = credit.version + 1
        if credit.available_amount <= 0:
            credit.state = CarbonCreditState.RETIRED
            credit.available_amount = Decimal("0")

        if req.idempotency_key:
            self.db.add(
                IdempotencyKey(
                    key=req.idempotency_key,
                    action="retire",
                    result_reference=f"retire:{credit.credit_id}:{amount!s}",
                    status="completed",
                    created_at=_now(),
                )
            )

        self._event(
            aggregate="credit",
            aggregate_id=credit.credit_id,
            event_type="retire",
            actor=req.actor,
            authority=req.authority,
            reason=req.reason,
            correlation_id=req.idempotency_key,
            payload={"amount": str(amount), "new_retired": str(credit.retired_amount)},
        )
        self._audit(
            action="retire",
            credit_id=credit.credit_id,
            project_id=credit.project_id,
            actor=req.actor,
            authority=req.authority,
            before_state=None,
            after_state=(
                CarbonCreditState.RETIRED.value
                if credit.state == CarbonCreditState.RETIRED
                else credit.state.value
            ),
            delta_amount=-amount,
            correlation_id=req.idempotency_key,
            reason=req.reason,
        )
        self.db.commit()
        self.db.refresh(credit)
        return self._credit_view(credit)

    # ------------------------------------------------------------------ #
    # Freeze / unfreeze
    # ------------------------------------------------------------------ #
    def freeze_credit(self, payload: dict[str, Any]) -> dict[str, Any]:
        from services.carbon.schemas import FreezeRequest

        req = FreezeRequest(**payload)
        credit = self._get_credit(req.credit_id)
        if credit.frozen:
            raise CreditStateError(credit.credit_id, "credit is already frozen")

        credit.frozen = True
        credit.frozen_by = req.actor
        credit.frozen_authority = req.authority
        credit.frozen_reason = req.reason
        credit.frozen_at = _now()
        credit.version = credit.version + 1

        self._event(
            aggregate="credit",
            aggregate_id=credit.credit_id,
            event_type="freeze",
            actor=req.actor,
            authority=req.authority,
            reason=req.reason,
        )
        self._audit(
            action="freeze",
            credit_id=credit.credit_id,
            project_id=credit.project_id,
            actor=req.actor,
            authority=req.authority,
            before_state=None,
            after_state=f"frozen:{credit.state.value}",
            reason=req.reason,
        )
        self.db.commit()
        self.db.refresh(credit)
        return self._credit_view(credit)

    def unfreeze_credit(self, payload: dict[str, Any]) -> dict[str, Any]:
        from services.carbon.schemas import UnfreezeRequest

        req = UnfreezeRequest(**payload)
        credit = self._get_credit(req.credit_id)
        if not credit.frozen:
            raise CreditStateError(credit.credit_id, "credit is not frozen")
        if credit.frozen_authority != req.authority:
            raise FrozenCreditError(credit.credit_id)

        credit.frozen = False
        credit.frozen_reason = req.reason
        credit.frozen_at = _now()
        credit.version = credit.version + 1

        self._event(
            aggregate="credit",
            aggregate_id=credit.credit_id,
            event_type="unfreeze",
            actor=req.actor,
            authority=req.authority,
            reason=req.reason,
        )
        self._audit(
            action="unfreeze",
            credit_id=credit.credit_id,
            project_id=credit.project_id,
            actor=req.actor,
            authority=req.authority,
            before_state="frozen",
            after_state=credit.state.value,
            reason=req.reason,
        )
        self.db.commit()
        self.db.refresh(credit)
        return self._credit_view(credit)

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def credit_history(self, credit_id: str) -> list[dict[str, Any]]:
        self._get_credit(credit_id)
        rows = self.db.scalars(
            select(CarbonEvent)
            .where(CarbonEvent.aggregate_type == "credit")
            .where(CarbonEvent.aggregate_id == credit_id)
            .order_by(CarbonEvent.created_at)
        ).all()
        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "actor": e.actor,
                "authority": e.authority,
                "reason": e.reason,
                "payload": e.payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ]

    def credit_stats(self, project_id: str | None = None) -> dict[str, Any]:
        stmt = select(CarbonCredit)
        if project_id:
            stmt = stmt.where(CarbonCredit.project_id == project_id)
        credits = self.db.scalars(stmt).all()

        total_issued = Decimal("0")
        total_retired = Decimal("0")
        total_active = Decimal("0")
        by_state: dict[str, int] = {}
        for c in credits:
            total_issued += _to_decimal(c.total_amount)
            total_retired += _to_decimal(c.retired_amount)
            total_active += _to_decimal(c.available_amount)
            by_state[c.state.value] = by_state.get(c.state.value, 0) + 1
        return {
            "total_issued": str(total_issued),
            "total_retired": str(total_retired),
            "total_active": str(total_active),
            "by_state": by_state,
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _run_motor(
        self,
        soc_initial_t_ha: float,
        soc_final_t_ha: float,
        area_ha: float,
        measured_soc_t_ha: float | None,
        measurements: list[dict[str, Any]],
        methodology: str,
        permanence_factor: float,
    ):
        return self.motor.execute(
            {
                "soc_initial_t_ha": soc_initial_t_ha,
                "soc_final_t_ha": soc_final_t_ha,
                "area_ha": area_ha,
                "measured_soc_t_ha": measured_soc_t_ha,
                "measurements": measurements,
                "methodology": methodology,
                "permanence_factor": permanence_factor,
            }
        )

    def _get_project(self, project_id: str):
        from database.models import CarbonProject

        project = self.db.scalar(
            select(CarbonProject).where(CarbonProject.project_id == project_id)
        )
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    def _get_credit(self, credit_id: str):
        credit = self.db.scalar(select(CarbonCredit).where(CarbonCredit.credit_id == credit_id))
        if credit is None:
            raise CreditNotFoundError(credit_id)
        return credit

    def _event(
        self,
        aggregate: str,
        aggregate_id: str,
        event_type: str,
        actor: str | None = None,
        authority: str | None = None,
        reason: str | None = None,
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.db.add(
            CarbonEvent(
                event_id=f"EVT-{uuid4().hex}",
                aggregate_type=aggregate,
                aggregate_id=aggregate_id,
                event_type=event_type,
                actor=actor,
                authority=authority,
                reason=reason,
                payload=payload,
                correlation_id=correlation_id,
                created_at=_now(),
            )
        )

    def _audit(
        self,
        action: str,
        credit_id: str | None = None,
        project_id: str | None = None,
        actor: str | None = None,
        authority: str | None = None,
        reason: str | None = None,
        before_state: str | None = None,
        after_state: str | None = None,
        delta_amount: Decimal | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.db.add(
            CreditAuditLog(
                audit_id=f"AUD-{uuid4().hex}",
                credit_id=credit_id,
                project_id=project_id,
                action=action,
                actor=actor,
                authority=authority,
                reason=reason,
                before_state=before_state,
                after_state=after_state,
                delta_amount=delta_amount,
                correlation_id=correlation_id,
                created_at=_now(),
            )
        )

    @staticmethod
    def _issue_result(credit: CarbonCredit, idempotency_key: str, replay: str) -> dict[str, Any]:
        return {
            "credit_id": credit.credit_id,
            "serial": credit.serial,
            "state": credit.state.value,
            "total_amount": str(credit.total_amount),
            "available_amount": str(credit.available_amount),
            "retired_amount": str(credit.retired_amount),
            "data_mode": credit.data_mode,
            "issued_at": credit.issued_at.isoformat() if credit.issued_at else None,
            "idempotency_key": idempotency_key,
            "replay": replay,
            "note": (
                "Accounting figure from CarbonMrvMotor (IPCC tC->tCO2e x3.667) with a "
                "permanence/uncertainty deduction. Not a certification by any VVB."
            ),
        }

    @staticmethod
    def _credit_view(credit: CarbonCredit) -> dict[str, Any]:
        return {
            "credit_id": credit.credit_id,
            "serial": credit.serial,
            "state": credit.state.value,
            "total_amount": str(credit.total_amount),
            "available_amount": str(credit.available_amount),
            "retired_amount": str(credit.retired_amount),
            "holder_id": credit.holder_id,
            "frozen": credit.frozen,
            "frozen_by": credit.frozen_by,
            "frozen_authority": credit.frozen_authority,
            "frozen_reason": credit.frozen_reason,
            "frozen_at": credit.frozen_at.isoformat() if credit.frozen_at else None,
            "data_mode": credit.data_mode,
            "version": credit.version,
        }


__all__ = ["CarbonService"]
