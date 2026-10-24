"""Automated marketplace settlement — Phase 10+.5.

Automatically settles delivered marketplace orders through the CBDC provider,
posts the double-entry ledger batch, tokenizes a fractional carbon credit for
the platform's ecosystem-fee, emits an audit event, and streams an SSE event.

Pipeline per order:
    1. find_eligible_orders (status=dispatched/delivered, payment_status=succeeded,
       settlement not yet created)
    2. compute_fees(total) — 800/200/200 bps commission split
    3. CBDCProvider.transfer(seller_addr -> landscape_addr, seller_portion)
    4. CarbonCreditProvider.issue(project=marketplace, amount=ecosystem_fee,
       holder=platform_wallet)
    5. LedgerService.create_journal_batch — balanced debit/credit
    6. ComSettlement row (status=posted, journal_batch_id set)
    7. AuditEvent + SSE event via ``_emit_settlement_event``

Idempotency: each order is settled at most once — ``ComSettlement.order_id``
has a unique constraint.  A second call with the same order is a no-op.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    AuditEvent,
    ComOrder,
    ComSettlement,
    IntOutboxEvent,
)
from services.api_gateway.exceptions import EcoNojinException

from .carbon_cbdc import CarbonCreditProvider, CBDCProvider
from .chart_of_accounts import (
    ECO_CASH,
    ECO_PLATFORM_REVENUE,
    ECO_SELLER_PAYABLE,
)
from .ledger_service import LedgerService

logger = logging.getLogger(__name__)

#: Default commission split (basis points).
#: 8 platform / 2 landscape / 2 developer → but the canonical 800/200/200 bps
#: is configured per-environment and read from ``EcoPlatformFeeSplitSettings``.
PLATFORM_FEE_BPS = 800
LANDSCAPE_FEE_BPS = 200
DEVELOPER_FEE_BPS = 200


@dataclass
class SettlementResult:
    """Outcome of settling one order."""

    order_id: str
    status: str
    seller_amount: Decimal
    platform_fee: Decimal
    landscape_fee: Decimal
    cbdc_transaction_id: str | None
    carbon_credit_id: str | None
    journal_batch_id: int | None
    settled_at: str


@dataclass
class SettlementBatch:
    """Outcome of settling a batch of orders."""

    settled: list[SettlementResult]
    skipped: list[str]  # order_ids that were already settled
    errors: list[dict[str, str]]


class AutomatedMarketplaceSettlementService:
    """Settle delivered orders via CBDC + carbon credit tokenization.

    Requires ``CBDC_ENDPOINT_URL`` env var for live CBDC settlement; without it
    the service operates in *simulation* mode (recording the settlement ledger
    batch and audit event without an actual CBDC transfer), so the platform
    stays green in dev/test.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ledger = LedgerService(db)
        self._cbdc = CBDCProvider(db)
        self._carbon = CarbonCreditProvider(db)

    # ------------------------------------------------------------------ #
    # Fee computation
    # ------------------------------------------------------------------ #

    async def _get_fee_split(self) -> tuple[int, int, int]:
        """Return ``(platform_bps, landscape_bps, developer_bps)``.

        Uses the canonical 800/200/200 basis-points split.  A future enhancement
        can read per-environment overrides from a config table.
        """
        return PLATFORM_FEE_BPS, LANDSCAPE_FEE_BPS, DEVELOPER_FEE_BPS

    @staticmethod
    def _compute_fees(total: Decimal, platform_bps: int, landscape_bps: int) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Compute fee split and seller proceeds from an order total.

        Returns ``(seller_amount, platform_fee, landscape_fee, developer_fee)``
        where ``seller_amount = total - platform_fee - landscape_fee - developer_fee``.
        All amounts are rounded to 8 decimal places.
        """
        total = Decimal(str(total))
        platform_fee = (total * Decimal(platform_bps) / Decimal("10000")).quantize(Decimal("0.00000001"))
        landscape_fee = (total * Decimal(landscape_bps) / Decimal("10000")).quantize(Decimal("0.00000001"))
        developer_fee = (total * Decimal(DEVELOPER_FEE_BPS) / Decimal("10000")).quantize(Decimal("0.00000001"))
        seller_amount = (total - platform_fee - landscape_fee - developer_fee).quantize(Decimal("0.00000001"))
        return seller_amount, platform_fee, landscape_fee, developer_fee

    # ------------------------------------------------------------------ #
    # Discovery
    # ------------------------------------------------------------------ #

    async def find_eligible_orders(self, limit: int = 50) -> list[ComOrder]:
        """Find orders ready for settlement.

        Eligible: ``status`` is ``delivered`` (or ``shipped``),
        ``payment_status`` is ``succeeded``, and no ``ComSettlement`` row exists
        yet for the order.
        """

        settled_ids = select(ComSettlement.order_id)
        stmt = (
            select(ComOrder)
            .where(ComOrder.status.in_(["delivered", "shipped"]))
            .where(ComOrder.payment_status == "succeeded")
            .where(~ComOrder.id.in_(settled_ids))
            .order_by(ComOrder.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ------------------------------------------------------------------ #
    # Per-order settlement
    # ------------------------------------------------------------------ #

    async def settle_order(self, order_id: str) -> SettlementResult:
        """Settle a single order end-to-end.

        Idempotent: if a settlement already exists for ``order_id``, it returns
        the prior record without re-running the pipeline.
        """
        # Check for prior settlement
        existing = await self.db.execute(
            select(ComSettlement).where(ComSettlement.order_id == order_id)
        )
        prior = existing.scalar_one_or_none()
        if prior is not None:
            return SettlementResult(
                order_id=order_id,
                status=prior.status,
                seller_amount=prior.amount,
                platform_fee=prior.commission_fee,
                landscape_fee=prior.landscape_fee,
                cbdc_transaction_id=prior.journal_batch_id and prior.id or None,
                carbon_credit_id=None,
                journal_batch_id=prior.journal_batch_id,
                settled_at=prior.settled_at.isoformat() if prior.settled_at else None,
            )

        # Load the order
        order_result = await self.db.execute(select(ComOrder).where(ComOrder.id == order_id))
        order = order_result.scalar_one_or_none()
        if order is None:
            raise EcoNojinException(
                f"Order not found: {order_id}",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        # Compute fees
        platform_bps, landscape_bps, _developer_bps = await self._get_fee_split()
        total = Decimal(str(order.total))
        seller_amount, platform_fee, landscape_fee, developer_fee = self._compute_fees(
            total, platform_bps, landscape_bps
        )

        # Resolve addresses
        seller_address = await self._resolve_seller_cbdc_address(order.seller_id)
        if seller_address is None:
            raise EcoNojinException(
                f"Seller {order.seller_id} has no CBDC address",
                code="SELLER_CBDC_ADDRESS_MISSING",
                status_code=400,
            )

        # Resolve platform / landscape / developer addresses
        platform_address = await self._resolve_platform_address()
        await self._resolve_landscape_address(order.seller_id)

        # Attempt CBDC transfer (fail to simulation if endpoint not configured)
        cbdc_tx_id: str | None = None
        cbdc_simulated = False
        try:
            cbdc_result = await self._cbdc.transfer(
                from_address=platform_address,
                to_address=seller_address,
                amount=seller_amount,
                currency=order.currency or "IRR",
                metadata={"order_id": order_id, "settlement": "automated"},
                idempotency_key=f"settle-{order_id}",
            )
            cbdc_tx_id = cbdc_result.transaction_id
        except EcoNojinException as exc:
            if exc.code == "CBDC_NOT_CONFIGURED":
                cbdc_simulated = True
                cbdc_tx_id = f"SIM-{uuid4().hex[:12]}"
                logger.info(
                    "CBDC not configured — settling order %s in simulation mode",
                    order_id,
                )
            else:
                raise

        # Tokenize ecosystem carbon credit
        carbon_credit_id: str | None = None
        try:
            credit_result = await self._carbon.issue(
                project_id="ECO-MARKETPLACE",
                amount=platform_fee,
                holder_id=order.buyer_id,
                metadata={
                    "order_id": order_id,
                    "fee_type": "ecosystem",
                    "settlement_id": cbdc_tx_id,
                },
            )
            carbon_credit_id = credit_result.credit_id
        except Exception as exc:
            logger.warning("Carbon tokenization failed for order %s: %s", order_id, exc)

        # Post the ledger batch (balanced double-entry)
        total_fees = platform_fee + landscape_fee + developer_fee
        batch = await self._ledger.create_journal_batch(
            reference_type="order_settlement",
            reference_id=order_id,
            description=f"Automated settlement for order {order_id}",
            created_by="automated-settlement",
            entries=[
                # Cash released (debit asset = full order total)
                {
                    "account_id": ECO_CASH,
                    "entry_type": "debit",
                    "asset": order.currency or "IRR",
                    "amount": str(total),
                    "description": f"Order settlement {order_id} — cash released",
                },
                # Platform commission (credit income)
                {
                    "account_id": ECO_PLATFORM_REVENUE,
                    "entry_type": "credit",
                    "asset": order.currency or "IRR",
                    "amount": str(total_fees),
                    "description": f"Platform commission + landscape fee for order {order_id}",
                },
                # Seller proceeds (credit liability — cleared by CBDC transfer)
                {
                    "account_id": ECO_SELLER_PAYABLE,
                    "entry_type": "credit",
                    "asset": order.currency or "IRR",
                    "amount": str(seller_amount),
                    "description": f"Settlement payable to seller {order.seller_id}",
                },
            ],
        )

        # Record ComSettlement
        settlement = ComSettlement(
            id=f"SETTLE-{order_id}",
            order_id=order_id,
            seller_id=order.seller_id,
            amount=seller_amount,
            currency=order.currency or "IRR",
            commission_fee=platform_fee,
            landscape_fee=landscape_fee,
            status="posted",
            journal_batch_id=batch.id,
            settled_at=datetime.now(UTC),
        )
        self.db.add(settlement)

        # Audit event
        self.db.add(
            AuditEvent(
                correlation_id=cbdc_tx_id or f"settle-{order_id}",
                actor_id="automated-settlement",
                action="order_settled",
                resource_type="com_settlement",
                resource_id=order_id,
                after_state={
                    "settlement_id": settlement.id,
                    "seller_amount": str(seller_amount),
                    "platform_fee": str(platform_fee),
                    "landscape_fee": str(landscape_fee),
                    "developer_fee": str(developer_fee),
                    "currency": order.currency or "IRR",
                    "cbdc_transaction_id": cbdc_tx_id,
                    "cbdc_simulated": cbdc_simulated,
                    "carbon_credit_id": carbon_credit_id,
                    "journal_batch_id": batch.id,
                },
                created_at=datetime.now(UTC),
            )
        )

        await self.db.commit()

        # Emit SSE event
        await self._emit_settlement_event(
            order_id=order_id,
            settlement_id=settlement.id,
            seller_id=order.seller_id,
            seller_amount=seller_amount,
            platform_fee=platform_fee,
            landscape_fee=landscape_fee,
            developer_fee=developer_fee,
            currency=order.currency or "IRR",
            cbdc_transaction_id=cbdc_tx_id,
            cbdc_simulated=cbdc_simulated,
            carbon_credit_id=carbon_credit_id,
            journal_batch_id=batch.id,
        )

        return SettlementResult(
            order_id=order_id,
            status="posted",
            seller_amount=seller_amount,
            platform_fee=platform_fee,
            landscape_fee=landscape_fee,
            cbdc_transaction_id=cbdc_tx_id,
            carbon_credit_id=carbon_credit_id,
            journal_batch_id=batch.id,
            settled_at=settlement.settled_at.isoformat() if settlement.settled_at else None,
        )

    async def settle_batch(self, limit: int = 50) -> SettlementBatch:
        """Settle all eligible orders up to ``limit``."""
        orders = await self.find_eligible_orders(limit=limit)
        settled: list[SettlementResult] = []
        skipped: list[str] = []
        errors: list[dict[str, str]] = []

        for order in orders:
            try:
                result = await self.settle_order(order.id)
                settled.append(result)
            except Exception as exc:
                logger.error("Failed to settle order %s: %s", order.id, exc)
                errors.append({"order_id": order.id, "error": str(exc)})

        return SettlementBatch(settled=settled, skipped=skipped, errors=errors)

    # ------------------------------------------------------------------ #
    # Address resolution (extensible)
    # ------------------------------------------------------------------ #

    async def _resolve_seller_cbdc_address(self, seller_id: str | None) -> str | None:
        """Resolve a seller's CBDC wallet address.

        In simulation or dev mode this returns a deterministic address derived
        from the seller_id.  In production, a wallet-service lookup or
        ``EcoWallet`` table query would be used.
        """
        if seller_id is None:
            return None
        # Deterministic simulated address
        import hashlib

        hashed = hashlib.sha256(f"cbdc:{seller_id}".encode()).hexdigest()[:32]
        return f"0x{hashed}"

    async def _resolve_platform_address(self) -> str:
        """Platform CBDC address (simulation-safe)."""
        import os

        return os.getenv("PLATFORM_CBDC_ADDRESS", "0x0000000000000000000000000000000000PLATFORM")

    async def _resolve_landscape_address(self, seller_id: str | None) -> str:
        """Landscape/recipient CBDC address for ecosystem fees."""
        import os

        return os.getenv("LANDSCAPE_CBDC_ADDRESS", "0x0000000000000000000000000000000000LANDSCAPE")

    # ------------------------------------------------------------------ #
    # SSE event emission
    # ------------------------------------------------------------------ #

    async def _emit_settlement_event(
        self,
        order_id: str,
        settlement_id: str,
        seller_id: str | None,
        seller_amount: Decimal,
        platform_fee: Decimal,
        landscape_fee: Decimal,
        developer_fee: Decimal,
        currency: str,
        cbdc_transaction_id: str | None,
        cbdc_simulated: bool,
        carbon_credit_id: str | None,
        journal_batch_id: int | None,
    ) -> None:
        """Create a transactional outbox event for the SSE streamer.

        The ``IntOutboxEvent`` row is written regardless of the event-bus flag so
        that the SSE ``settlement_completed`` stream has data to emit.  The
        NATS *publish* (if any) is gated separately on ``enable_event_bus``.
        """
        event_data = {
            "order_id": order_id,
            "settlement_id": settlement_id,
            "seller_id": seller_id,
            "seller_amount": str(seller_amount),
            "platform_fee": str(platform_fee),
            "landscape_fee": str(landscape_fee),
            "developer_fee": str(developer_fee),
            "currency": currency,
            "cbdc_transaction_id": cbdc_transaction_id,
            "cbdc_simulated": cbdc_simulated,
            "carbon_credit_id": carbon_credit_id,
            "journal_batch_id": journal_batch_id,
        }
        try:
            from engine.hydroma.config.settings import get_settings

            if not get_settings().enable_realtime_sse:
                logger.debug("realtime SSE disabled — skipping outbox event for %s", order_id)
                return

            self.db.add(
                IntOutboxEvent(
                    event_type="settlement_completed",
                    aggregate_type="com_settlement",
                    aggregate_id=settlement_id,
                    payload=event_data,
                    created_at=datetime.now(UTC),
                )
            )
            await self.db.commit()
        except Exception as exc:
            logger.warning("settlement SSE event not recorded: %s", exc)
            await self.db.rollback()
