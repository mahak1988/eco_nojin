"""Reconciliation service for financial integrity."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    ComOrder,
    ComPaymentIntent,
    ComSettlement,
    EcoWallet,
    FinAccount,
    FinJournalBatch,
    FinJournalEntry,
    InvInventoryBalance,
    InvReservation,
    InvStockMovement,
)

#: The two documented notes prefixes the adjustment writers use to carry the
#: signed delta beside the always-positive ``qty`` column (KN-07, P5).
_ADJUSTMENT_PREFIXES = ("Adjustment: ", "Stocktake variance: ")


def _signed_adjustment_delta(notes: str | None) -> Decimal | None:
    """Recover the signed adjustment delta from a movement's notes.

    Returns ``None`` when the notes are missing or use an unrecognised
    format — the caller then leaves the movement out of the signed sum so it
    surfaces as drift, rather than guessing a direction.
    """
    if not notes:
        return None
    for prefix in _ADJUSTMENT_PREFIXES:
        if not notes.startswith(prefix):
            continue
        remainder = notes[len(prefix) :].strip()
        token = remainder.split(" ", 1)[0] if remainder else ""
        try:
            return Decimal(token)
        except InvalidOperation:
            return None
    return None


class ReconciliationService:
    """Service for financial reconciliation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def reconcile_wallet_ledger(self, as_of: datetime | None = None) -> dict:
        """
        Reconcile wallet balances with ledger entries.

        Returns:
            Dict with reconciliation results
        """
        if not as_of:
            as_of = datetime.now(UTC)

        # Get all wallet balances
        from sqlalchemy import select

        result = await self.db.execute(select(EcoWallet))
        wallets = result.scalars().all()

        discrepancies = []

        for wallet in wallets:
            # Calculate ledger balance
            ledger_balance = await self._get_ledger_balance(wallet.user_id, "ECO")

            if wallet.balance != ledger_balance:
                discrepancies.append(
                    {
                        "user_id": wallet.user_id,
                        "wallet_balance": float(wallet.balance),
                        "ledger_balance": float(ledger_balance),
                        "difference": float(wallet.balance - ledger_balance),
                    }
                )

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_wallets": len(wallets),
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "overall_ok": len(discrepancies) == 0,
        }

    async def _get_ledger_balance(self, user_id: str, asset: str) -> Decimal:
        """Calculate ledger balance for user/asset from REWARD_LIABILITY account.

        The wallet balance represents ECO tokens owned by the user, which corresponds
        to the platform's REWARD_LIABILITY account (credits = platform owes user).

        The join to the chart of accounts previously used
        ``FinJournalEntry.account_id == FinAccount.id`` — a String column
        against an Integer primary key, so it never matched and every wallet
        reconciled against a ledger balance of zero. See
        ``services/finance/account_ref.py``.
        """
        from sqlalchemy import case

        from services.finance.account_ref import account_join_condition

        result = await self.db.execute(
            select(
                func.sum(
                    FinJournalEntry.amount
                    * case((FinJournalEntry.entry_type == "credit", 1), else_=-1)
                )
            )
            .select_from(FinJournalEntry)
            .join(FinJournalBatch, FinJournalEntry.batch_id == FinJournalBatch.id)
            .join(FinAccount, account_join_condition())
            .where(
                FinJournalBatch.created_by == user_id,
                FinAccount.code == "REWARD_LIABILITY",
                FinJournalEntry.asset == asset,
            )
        )
        return result.scalar() or Decimal("0")

    async def reconcile_orders_payments(self) -> dict:
        """Reconcile orders with their payment intents and settlements.

        Checks, per order:
        - an order that requires payment (``payment_status == "paid"``
          or a status at/past ``paid``) must have a
          :class:`ComPaymentIntent` with status ``"succeeded"``;
        - the payment intent amount must equal the order total;
        - a settled order must have a :class:`ComSettlement` whose
          amount plus commission and landscape fees equals the order
          total, and whose ``journal_batch_id`` references an existing
          **posted** :class:`FinJournalBatch`;
        - every payment intent must reference an existing order —
          orphaned intents are flagged.

        Orders still in unpaid states (draft/reserved/cancelled/refunded
        with ``payment_status != "paid"``) are not required to carry a
        payment intent yet.

        Returns:
            Dict with ``checked_at``, ``total_orders_checked``,
            ``discrepancies_count``, ``discrepancies`` and
            ``overall_ok``. Amounts come from ``Numeric`` columns and
            are compared with Decimal arithmetic only (no float), then
            serialised with ``str()``.
        """
        orders = (await self.db.execute(select(ComOrder))).scalars().all()
        intents = (await self.db.execute(select(ComPaymentIntent))).scalars().all()
        settlements = (await self.db.execute(select(ComSettlement))).scalars().all()
        batches = (await self.db.execute(select(FinJournalBatch))).scalars().all()

        posted_batch_ids = {batch.id for batch in batches if batch.is_posted}
        order_ids = {order.id for order in orders}

        intents_by_order: dict[str, list[ComPaymentIntent]] = {}
        for intent in intents:
            intents_by_order.setdefault(intent.order_id, []).append(intent)

        settlements_by_order = {
            settlement.order_id: settlement for settlement in settlements
        }

        discrepancies: list[dict] = []

        # Payment intents whose order does not exist (orphans).
        for intent in intents:
            if intent.order_id not in order_ids:
                discrepancies.append(
                    {
                        "order_id": intent.order_id,
                        "payment_intent_id": intent.id,
                        "type": "orphaned_payment_intent",
                        "payment_amount": str(intent.amount),
                    }
                )

        paid_states = {"paid", "processing", "shipped", "delivered", "settled"}

        for order in orders:
            order_intents = intents_by_order.get(order.id, [])
            payment_required = (
                order.payment_status == "paid" or order.status in paid_states
            )

            if payment_required and not order_intents:
                discrepancies.append(
                    {
                        "order_id": order.id,
                        "type": "missing_payment_intent",
                        "order_total": str(order.total),
                    }
                )

            for intent in order_intents:
                if payment_required and intent.status != "succeeded":
                    discrepancies.append(
                        {
                            "order_id": order.id,
                            "payment_intent_id": intent.id,
                            "type": "unconfirmed_payment_intent",
                            "payment_status": intent.status,
                        }
                    )
                if intent.amount != order.total:
                    discrepancies.append(
                        {
                            "order_id": order.id,
                            "payment_intent_id": intent.id,
                            "type": "payment_amount_mismatch",
                            "order_total": str(order.total),
                            "payment_amount": str(intent.amount),
                        }
                    )

            if order.status != "settled":
                continue

            settlement = settlements_by_order.get(order.id)
            if settlement is None:
                discrepancies.append(
                    {
                        "order_id": order.id,
                        "type": "missing_settlement",
                        "order_total": str(order.total),
                    }
                )
                continue

            settled_total = (
                settlement.amount + settlement.commission_fee + settlement.landscape_fee
            )
            if settled_total != order.total:
                discrepancies.append(
                    {
                        "order_id": order.id,
                        "type": "settlement_amount_mismatch",
                        "order_total": str(order.total),
                        "settlement_amount": str(settlement.amount),
                        "commission_fee": str(settlement.commission_fee),
                        "landscape_fee": str(settlement.landscape_fee),
                    }
                )
            if settlement.journal_batch_id not in posted_batch_ids:
                discrepancies.append(
                    {
                        "order_id": order.id,
                        "type": "unposted_settlement_journal_batch",
                        "journal_batch_id": settlement.journal_batch_id,
                    }
                )

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_orders_checked": len(orders),
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "overall_ok": not discrepancies,
        }

    async def reconcile_inventory(self) -> dict:
        """Reconcile inventory balances with the stock movement ledger.

        Per ``(sku_id, warehouse_id)``:
        - ``on_hand`` is compared against the signed movement sums.
          Inbound legs add (``receipt``/``return`` and ``unblock``),
          outbound legs subtract (``issue``/``scrap``), and a
          ``transfer`` subtracts from its source warehouse and adds to
          ``to_warehouse_id``. ``unblock`` is the mirror of ``scrap``:
          ``StockService.unblock_stock`` restores ``on_hand`` and
          decrements ``blocked`` and the weighted-average valuation
          prices the leg as inbound, so omitting it from this sum makes
          every scrap-then-unblock report the restored quantity as
          phantom ``on_hand_drift``. A transfer is stored as a single
          :class:`InvStockMovement` row on the source warehouse, so both
          legs must be applied explicitly — counting it as an inbound
          movement only double-counts transfers and never subtracts the
          outbound leg. ``reservation``/``release`` are excluded, and
          correctly so: they move the ``reserved`` counter, never
          ``on_hand``;
        - ``reserved`` is compared against the open reservations
          (``qty - consumed_qty`` of ``status == "active"`` rows).
          Consuming a reservation decrements ``reserved`` through a
          plain ``issue`` movement that carries no reservation lineage
          (``consume_reservation`` reuses movement_type ``issue``), so a
          movement-only reserved sum would report phantom drift on
          every consumed reservation; the reservation table is the
          authoritative expected value.

        ``adjustment`` movements ARE folded into the signed sum (KN-07, fixed
        in P5). They change ``on_hand`` (``StockService.adjust`` and
        ``approve_stocktake`` write the new balance) and carry ``abs(qty)`` in
        the ``qty`` column, but the signed delta is written by the two callers
        into the movement's ``notes`` under two documented prefixes:
        ``"Adjustment: {signed_qty} - ..."`` and ``"Stocktake variance:
        {signed_variance}"``. :func:`_signed_adjustment_delta` recovers it
        strictly — only those two prefixes parse, and anything else returns
        ``None`` so an unknown adjustment still surfaces as drift instead of
        being silently guessed into agreement. The valuation side of the same
        movements posts to ``ECO_INVENTORY_VARIANCE`` through
        ``_post_value_pair``, so value and quantity now move under the same
        reconciliation.

        Returns:
            Dict with ``checked_at``, ``total_balances_checked``,
            ``discrepancies_count``, ``discrepancies`` and
            ``overall_ok``. All arithmetic is Decimal (``Numeric``
            columns), serialised with ``str()``.
        """
        balances = (await self.db.execute(select(InvInventoryBalance))).scalars().all()
        movements = (await self.db.execute(select(InvStockMovement))).scalars().all()
        reservations = (
            (await self.db.execute(select(InvReservation))).scalars().all()
        )

        on_hand_ledger: dict[tuple[int, int], Decimal] = {}
        for movement in movements:
            source_key = (movement.sku_id, movement.warehouse_id)
            qty = movement.qty
            if movement.movement_type in ("receipt", "return", "unblock"):
                on_hand_ledger[source_key] = (
                    on_hand_ledger.get(source_key, Decimal("0")) + qty
                )
            elif movement.movement_type in ("issue", "scrap"):
                on_hand_ledger[source_key] = (
                    on_hand_ledger.get(source_key, Decimal("0")) - qty
                )
            elif movement.movement_type == "transfer":
                # Out of the source warehouse, into to_warehouse_id.
                on_hand_ledger[source_key] = (
                    on_hand_ledger.get(source_key, Decimal("0")) - qty
                )
                if movement.to_warehouse_id is not None:
                    dest_key = (movement.sku_id, movement.to_warehouse_id)
                    on_hand_ledger[dest_key] = (
                        on_hand_ledger.get(dest_key, Decimal("0")) + qty
                    )
            elif movement.movement_type == "adjustment":
                # KN-07: the column is abs(qty); the signed delta is recovered
                # from the documented notes prefix, or left as drift.
                signed = _signed_adjustment_delta(movement.notes)
                if signed is not None:
                    on_hand_ledger[source_key] = (
                        on_hand_ledger.get(source_key, Decimal("0")) + signed
                    )

        reserved_expected: dict[tuple[int, int], Decimal] = {}
        for reservation in reservations:
            if reservation.status != "active":
                continue
            key = (reservation.sku_id, reservation.warehouse_id)
            open_qty = reservation.qty - reservation.consumed_qty
            reserved_expected[key] = (
                reserved_expected.get(key, Decimal("0")) + open_qty
            )

        discrepancies: list[dict] = []
        for balance in balances:
            key = (balance.sku_id, balance.warehouse_id)
            expected_on_hand = on_hand_ledger.get(key, Decimal("0"))
            expected_reserved = reserved_expected.get(key, Decimal("0"))
            on_hand_drift = balance.on_hand - expected_on_hand
            reserved_drift = balance.reserved - expected_reserved
            if on_hand_drift == 0 and reserved_drift == 0:
                continue
            discrepancies.append(
                {
                    "sku_id": balance.sku_id,
                    "warehouse_id": balance.warehouse_id,
                    "on_hand": str(balance.on_hand),
                    "ledger_on_hand": str(expected_on_hand),
                    "on_hand_drift": str(on_hand_drift),
                    "reserved": str(balance.reserved),
                    "expected_reserved": str(expected_reserved),
                    "reserved_drift": str(reserved_drift),
                }
            )

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_balances_checked": len(balances),
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "overall_ok": not discrepancies,
        }

    async def run_full_reconciliation(self) -> dict:
        """Run all reconciliation checks."""
        wallet_result = await self.reconcile_wallet_ledger()
        orders_result = await self.reconcile_orders_payments()
        inventory_result = await self.reconcile_inventory()

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "checks": {
                "wallet_ledger": wallet_result,
                "orders_payments": orders_result,
                "inventory": inventory_result,
            },
            "overall_ok": all(
                check.get("overall_ok", False)
                for check in (wallet_result, orders_result, inventory_result)
            ),
        }
