"""Credit bridge — off-chain / on-chain integration for carbon credits.

Bridges the SQLAlchemy-backed CarbonService (off-chain ledger) with the
CarbonTokenService (on-chain simulation) to:

- Prevent double-counting between off-chain and on-chain records
- Synchronize state across both systems
- Forward issuance / transfer / retirement events
- Reconcile discrepancies

Honesty rules:
  * No credit can exist in on-chain state without a corresponding
    off-chain record (and vice versa).
  * Every on-chain operation is logged with its off-chain correlation ID.
  * Discrepancies are flagged, never silently resolved.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from services.business_modules.carbon.tokenization import CarbonTokenService
from services.carbon.service import CarbonService

logger = logging.getLogger(__name__)


class BridgeStatus(StrEnum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    RESOLVED = "resolved"


class DoubleCountingRisk(StrEnum):
    NONE = "none"
    OFF_CHAIN_ONLY = "off_chain_only"
    ON_CHAIN_ONLY = "on_chain_only"
    BOTH = "both"
    DISCREPANCY = "discrepancy"


@dataclass
class BridgeEvent:
    event_id: str
    credit_id: str
    event_type: str  # issue, transfer, retire, freeze, unfreeze
    off_chain_state: dict[str, Any]
    on_chain_state: dict[str, Any] | None
    status: BridgeStatus
    correlation_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    synced_at: datetime | None = None
    error: str | None = None


@dataclass
class ReconciliationResult:
    credit_id: str
    risk: DoubleCountingRisk
    off_chain_total: float
    on_chain_total: float
    off_chain_state: dict[str, Any] | None
    on_chain_state: dict[str, Any] | None
    discrepancies: list[str]
    resolved: bool = False
    resolution: str | None = None


class CreditBridge:
    """Bridge between off-chain (CarbonService) and on-chain (CarbonTokenService).

    Prevents double-counting by maintaining a correlation ledger and
    ensuring that every credit has a consistent representation in both
    systems.
    """

    def __init__(
        self,
        off_chain: CarbonService | None = None,
        on_chain: CarbonTokenService | None = None,
    ) -> None:
        self._off_chain = off_chain
        # Only initialize on_chain if explicitly provided
        # This avoids blockchain connectivity issues in offline mode
        self._on_chain = on_chain
        self._correlation: dict[str, dict[str, Any]] = {}
        self._bridge_events: list[BridgeEvent] = []

    # ------------------------------------------------------------------ #
    # Correlation management
    # ------------------------------------------------------------------ #

    def register_correlation(
        self,
        credit_id: str,
        token_id: str,
        project_id: str,
    ) -> None:
        """Register a mapping between off-chain credit and on-chain token."""
        if credit_id in self._correlation:
            logger.warning("Re-registering correlation for credit %s", credit_id)
        self._correlation[credit_id] = {
            "credit_id": credit_id,
            "token_id": token_id,
            "project_id": project_id,
            "registered_at": datetime.now(UTC),
            "off_chain_seen": False,
            "on_chain_seen": False,
        }
        logger.info(
            "Correlation registered: credit=%s token=%s project=%s",
            credit_id,
            token_id,
            project_id,
        )

    def get_correlation(self, credit_id: str) -> dict[str, Any] | None:
        """Get correlation data for a credit."""
        return self._correlation.get(credit_id)

    # ------------------------------------------------------------------ #
    # Double-counting prevention
    # ------------------------------------------------------------------ #

    def check_double_counting_risk(self, credit_id: str) -> ReconciliationResult:
        """Check if a credit exists in both systems or only in one.

        Returns a ReconciliationResult with risk assessment.
        """
        off_chain_state = self._get_off_chain_state(credit_id)
        on_chain_state = self._get_on_chain_state(credit_id)

        off_chain_exists = off_chain_state is not None
        on_chain_exists = on_chain_state is not None

        discrepancies: list[str] = []
        risk = DoubleCountingRisk.NONE

        if off_chain_exists and not on_chain_exists:
            risk = DoubleCountingRisk.OFF_CHAIN_ONLY
            discrepancies.append("Credit exists off-chain but NOT on-chain")
        elif on_chain_exists and not off_chain_exists:
            risk = DoubleCountingRisk.ON_CHAIN_ONLY
            discrepancies.append("Credit exists on-chain but NOT off-chain")
        elif off_chain_exists and on_chain_exists:
            off_amount = off_chain_state.get("total_amount", 0)
            on_amount = on_chain_state.get("amount_tonnes", 0)
            if abs(float(off_amount) - float(on_amount)) > 0.001:
                risk = DoubleCountingRisk.DISCREPANCY
                discrepancies.append(
                    f"Amount mismatch: off-chain={off_amount}, on-chain={on_amount}"
                )
            off_holder = off_chain_state.get("holder_id")
            on_owner = on_chain_state.get("owner_address")
            if off_holder and on_owner and off_holder != on_owner:
                risk = DoubleCountingRisk.DISCREPANCY
                discrepancies.append(
                    f"Holder mismatch: off-chain={off_holder}, on-chain={on_owner}"
                )
            off_state = off_chain_state.get("state")
            on_status = on_chain_state.get("status")
            if off_state and on_status and not self._states_match(off_state, on_status):
                risk = DoubleCountingRisk.DISCREPANCY
                discrepancies.append(f"State mismatch: off-chain={off_state}, on-chain={on_status}")

        return ReconciliationResult(
            credit_id=credit_id,
            risk=risk,
            off_chain_total=float(off_chain_state.get("total_amount", 0))
            if off_chain_exists
            else 0.0,
            on_chain_total=float(on_chain_state.get("amount_tonnes", 0))
            if on_chain_exists
            else 0.0,
            off_chain_state=off_chain_state,
            on_chain_state=on_chain_state,
            discrepancies=discrepancies,
        )

    @staticmethod
    def _states_match(off_state: str, on_status: str) -> bool:
        """Map off-chain states to on-chain status for comparison."""
        mapping = {
            "ACTIVE": "active",
            "RETIRED": "retired",
            "DRAFT": "draft",
            "SUBMITTED": "submitted",
            "VERIFIED": "verified",
            "FROZEN": "frozen",
        }
        return mapping.get(off_state) == on_status

    # ------------------------------------------------------------------ #
    # State synchronization
    # ------------------------------------------------------------------ #

    def sync_issuance(
        self,
        credit_id: str,
        token_id: str,
        project_id: str,
        amount: float,
        holder_id: str,
        data_mode: str,
        correlation_id: str | None = None,
    ) -> BridgeEvent:
        """Synchronize an issuance across off-chain and on-chain.

        Must be called within the same transaction as the off-chain issuance
        to ensure atomicity.
        """
        event = BridgeEvent(
            event_id=f"BR-{uuid4().hex}",
            credit_id=credit_id,
            event_type="issue",
            off_chain_state={
                "credit_id": credit_id,
                "total_amount": amount,
                "available_amount": amount,
                "holder_id": holder_id,
                "data_mode": data_mode,
            },
            on_chain_state=None,
            status=BridgeStatus.PENDING,
            correlation_id=correlation_id,
        )

        self.register_correlation(credit_id, token_id, project_id)

        try:
            on_chain_result = self._on_chain.issue_credits(
                project_id=project_id,
                amount=amount,
                credit_type="VCS",
                recipient_address=holder_id,
            )
            event.on_chain_state = on_chain_result
            event.status = BridgeStatus.SYNCED
            event.synced_at = datetime.now(UTC)
            logger.info(
                "Issuance synced: credit=%s token=%s amount=%s",
                credit_id,
                token_id,
                amount,
            )
        except Exception as exc:
            event.status = BridgeStatus.FAILED
            event.error = str(exc)
            logger.error("Issuance sync failed for credit %s: %s", credit_id, exc)

        self._bridge_events.append(event)
        return event

    def sync_transfer(
        self,
        credit_id: str,
        token_id: str,
        from_holder: str,
        to_holder: str,
        correlation_id: str | None = None,
    ) -> BridgeEvent:
        """Synchronize a transfer across off-chain and on-chain."""
        event = BridgeEvent(
            event_id=f"BR-{uuid4().hex}",
            credit_id=credit_id,
            event_type="transfer",
            off_chain_state={"from": from_holder, "to": to_holder},
            on_chain_state=None,
            status=BridgeStatus.PENDING,
            correlation_id=correlation_id,
        )

        try:
            on_chain_result = self._on_chain.transfer_credits(
                from_address=from_holder,
                to_address=to_holder,
                token_id=token_id,
            )
            event.on_chain_state = on_chain_result
            event.status = BridgeStatus.SYNCED
            event.synced_at = datetime.now(UTC)
            logger.info(
                "Transfer synced: credit=%s from=%s to=%s",
                credit_id,
                from_holder,
                to_holder,
            )
        except Exception as exc:
            event.status = BridgeStatus.FAILED
            event.error = str(exc)
            logger.error("Transfer sync failed for credit %s: %s", credit_id, exc)

        self._bridge_events.append(event)
        return event

    def sync_retirement(
        self,
        credit_id: str,
        token_id: str,
        amount: float,
        reason: str,
        actor: str,
        correlation_id: str | None = None,
    ) -> BridgeEvent:
        """Synchronize a retirement across off-chain and on-chain."""
        event = BridgeEvent(
            event_id=f"BR-{uuid4().hex}",
            credit_id=credit_id,
            event_type="retire",
            off_chain_state={"amount": amount, "reason": reason, "actor": actor},
            on_chain_state=None,
            status=BridgeStatus.PENDING,
            correlation_id=correlation_id,
        )

        try:
            on_chain_result = self._on_chain.retire_credits(
                token_id=token_id,
                retirement_justification=f"{reason} (actor: {actor})",
            )
            event.on_chain_state = on_chain_result
            event.status = BridgeStatus.SYNCED
            event.synced_at = datetime.now(UTC)
            logger.info(
                "Retirement synced: credit=%s amount=%s",
                credit_id,
                amount,
            )
        except Exception as exc:
            event.status = BridgeStatus.FAILED
            event.error = str(exc)
            logger.error("Retirement sync failed for credit %s: %s", credit_id, exc)

        self._bridge_events.append(event)
        return event

    # ------------------------------------------------------------------ #
    # Reconciliation
    # ------------------------------------------------------------------ #

    def reconcile_all(self) -> list[ReconciliationResult]:
        """Reconcile all correlated credits between off-chain and on-chain.

        Returns a list of ReconciliationResult with risk assessments
        for each credit. Discrepancies are NOT auto-resolved.
        """
        results: list[ReconciliationResult] = []
        for credit_id in self._correlation:
            result = self.check_double_counting_risk(credit_id)
            results.append(result)
        return results

    def reconcile_project(self, project_id: str) -> dict[str, Any]:
        """Reconcile all credits for a specific project."""
        results: list[ReconciliationResult] = []
        for c in self._correlation.values():
            if c.get("project_id") == project_id:
                result = self.check_double_counting_risk(c["credit_id"])
                results.append(result)

        critical = [
            r
            for r in results
            if r.risk in (DoubleCountingRisk.ON_CHAIN_ONLY, DoubleCountingRisk.OFF_CHAIN_ONLY)
        ]
        return {
            "project_id": project_id,
            "total_credits": len(results),
            "critical_issues": len(critical),
            "reconciliation_passed": len(critical) == 0,
            "results": [
                {
                    "credit_id": r.credit_id,
                    "risk": r.risk.value,
                    "off_chain_total": r.off_chain_total,
                    "on_chain_total": r.on_chain_total,
                    "discrepancies": r.discrepancies,
                    "resolved": r.resolved,
                }
                for r in results
            ],
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get_off_chain_state(self, credit_id: str) -> dict[str, Any] | None:
        """Fetch credit state from off-chain database."""
        if self._off_chain is None:
            return None
        try:
            from sqlalchemy import select

            from database.models import CarbonCredit

            credit = self._off_chain.db.scalar(
                select(CarbonCredit).where(CarbonCredit.credit_id == credit_id)
            )
            if credit is None:
                return None
            return {
                "credit_id": credit.credit_id,
                "total_amount": float(credit.total_amount),
                "available_amount": float(credit.available_amount),
                "retired_amount": float(credit.retired_amount),
                "holder_id": credit.holder_id,
                "state": credit.state.value,
                "frozen": credit.frozen,
                "data_mode": credit.data_mode,
                "project_id": credit.project_id,
            }
        except Exception as exc:
            logger.warning("Off-chain state fetch failed for %s: %s", credit_id, exc)
            return None

    def _get_on_chain_state(self, credit_id: str) -> dict[str, Any] | None:
        """Fetch credit state from on-chain registry."""
        try:
            credit = self._on_chain._credits.get(credit_id)
            if credit is None:
                correlation = self._correlation.get(credit_id)
                if correlation:
                    token_id = correlation["token_id"]
                    credit = self._on_chain._credits.get(token_id)
                else:
                    return None
            if credit is None:
                return None
            return {
                "token_id": credit.token_id,
                "project_id": credit.project_id,
                "amount_tonnes": credit.amount_tonnes,
                "owner_address": credit.owner_address,
                "status": credit.status.value,
                "credit_type": credit.credit_type.value,
                "transaction_hash": credit.transaction_hash,
            }
        except Exception as exc:
            logger.warning("On-chain state fetch failed for %s: %s", credit_id, exc)
            return None

    def get_bridge_events(self, credit_id: str | None = None) -> list[dict[str, Any]]:
        """Return bridge events, optionally filtered by credit_id."""
        events = self._bridge_events
        if credit_id:
            events = [e for e in events if e.credit_id == credit_id]
        return [
            {
                "event_id": e.event_id,
                "credit_id": e.credit_id,
                "event_type": e.event_type,
                "off_chain_state": e.off_chain_state,
                "on_chain_state": e.on_chain_state,
                "status": e.status.value,
                "correlation_id": e.correlation_id,
                "created_at": e.created_at.isoformat(),
                "synced_at": e.synced_at.isoformat() if e.synced_at else None,
                "error": e.error,
            }
            for e in events
        ]


# Singleton
_bridge: CreditBridge | None = None


def get_credit_bridge() -> CreditBridge:
    """Get the singleton credit bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = CreditBridge()
    return _bridge


def set_credit_bridge(bridge: CreditBridge) -> None:
    """Set a custom bridge instance (for testing or custom config)."""
    global _bridge
    _bridge = bridge
