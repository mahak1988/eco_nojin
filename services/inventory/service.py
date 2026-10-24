"""Inventory/WMS service — real warehouse management with atomic stock operations.

Implements the Inventory bounded context from the target architecture:
  - Stock movements (receipt, issue, transfer, adjustment, return, scrap, stocktake)
  - Atomic reservation with FOR UPDATE (prevents oversell) — the lock is
    emitted on dialects that support row locking (PostgreSQL, MySQL);
    SQLAlchemy silently no-ops ``SELECT ... FOR UPDATE`` on SQLite, so
    the row-selection guarantee (exactly one balance row, keyed by
    sku/warehouse/location/lot) is what the tests pin there
  - Weighted-average valuation and COGS accounting (below)
  - Lot/batch traceability (FEFO expiry picking)

Valuation and accounting, in one place:

* **Weighted-average cost** per ``(sku_id, warehouse_id)`` is computed from the
  movement ledger (``_moving_average_costs``): every inbound leg — a
  ``receipt``/``return``/``unblock`` at its own cost, a ``transfer``'s inbound
  leg at the source's average — blends into the warehouse's (quantity, value)
  pool, and every outbound leg (an ``issue``/``scrap``, a ``transfer``'s
  outbound leg) draws from that pool at the current average, which leaves the
  average unchanged. The resolved cost is written back to
  ``InvStockMovement.unit_cost``/``total_cost`` on every movement type.
  **Lots (below) are the additive second costing policy: they do not touch this
  one.**
* **Lot/batch traceability with FEFO expiry picking** — the module docstring's
  long-standing promise, implemented additively by
  :class:`~database.models.InvLot` plus the nullable ``lot_uuid`` column on
  ``InvInventoryBalance``/``InvStockMovement``/``InvReservation``:

  * **Non-lot-tracked stock** (``lot_uuid`` is NULL, the legacy
    Integer ``lot_id`` 0-sentinel path) is valued exactly as above, at the
    warehouse moving average. Every pre-lot behaviour — receipts, issues,
    transfers, adjustments, scraps, stocktakes, reservations, the unique
    constraint on ``(sku_id, warehouse_id, location_id, lot_id)`` and the
    valuation read API — is unchanged for it, byte for byte, because no lot
    query runs when the balance row carries no ``lot_uuid``.
  * **Lot-tracked stock** (the balance row carries a ``lot_uuid``) issues and
    consumes by **FEFO**: the SKU's active lots with ``qty_remaining`` left are
    ordered by ``expiry_date`` (earliest first, undated lots last), the
    requested quantity is allocated across them in that order, each leg is
    costed at *that lot's* ``unit_cost`` and written as its own movement
    carrying that lot's ``lot_uuid``, and the lot's ``qty_remaining`` is
    decremented (a drained lot flips to ``depleted``). An expired lot is never
    picked — the lazy check flips it to ``expired`` — and requesting stock that
    only exists as expired/quarantined lots is refused with ``EXPIRED_LOT``
    unless the caller passes ``allow_expired=True``.

  The duality is deliberate: the legacy Integer ``lot_id`` is a NOT NULL
  0-sentinel inside a unique constraint (P2-18), so it cannot carry a uuid and
  cannot be re-typed without a data migration; ``lot_uuid`` is a nullable
  String(36) foreign key that means exactly one thing — "this row is backed by
  a real lot". ``fifo``/``standard`` stay rejected as unimplemented valuation
  methods; FEFO is per-lot costing, not a second warehouse-level method.
* **Journal posting** goes through the module-level ``_post_journal`` helper,
  not ``LedgerService``: the ledger service is async-only and commits on create
  *and* on post, which would tear a stock mutation and its batch apart. The
  helper writes the same rows with the same guarantees (positive Decimal
  amounts, debits == credits, allowlisted asset) but flushes them into the
  caller's transaction with ``is_posted=True``/``posted_at`` already set — the
  P0-1 convention the wallet and settlement batches follow.
* **Failure rule**: the batch is posted before the mutator's ``db.commit()``,
  so a posting failure propagates and discards the movement *and* the batch —
  neither is ever persisted alone. Two documented escapes keep that rule from
  biting: a zero-value movement books nothing (there is no value to recognise),
  and a database carrying the inventory tables without the finance ones still
  values its stock, just without journaling (``_can_post_journal``).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    FinJournalBatch,
    FinJournalEntry,
    InvInventoryBalance,
    InvLocation,
    InvLot,
    InvReservation,
    InvSKU,
    InvStockMovement,
    InvWarehouse,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.chart_of_accounts import (
    ACCOUNT_ASSETS,
    ECO_ACCOUNTS_PAYABLE,
    ECO_CASH,
    ECO_COGS,
    ECO_INVENTORY,
    ECO_INVENTORY_VARIANCE,
    UnknownAccountCode,
    ensure_account,
    get_account_spec,
)
from services.finance.ledger_service import LedgerService

if TYPE_CHECKING:  # annotation-only import; InvStocktake lives in database.models
    from database.models import InvStocktake

logger = logging.getLogger(__name__)

VALID_MOVEMENT_TYPES = frozenset(
    {
        "receipt",
        "issue",
        "transfer",
        "adjustment",
        "return",
        "scrap",
        "stocktake",
        "reservation",
        "release",
        "unblock",
    }
)

VALID_VALUATION_METHODS = frozenset({"fifo", "weighted_avg", "standard"})

#: The valuation method this module implements: weighted-average cost per
#: ``(sku_id, warehouse_id)``. ``fifo``/``standard`` stay in
#: :data:`VALID_VALUATION_METHODS` (the public allowlist) but are rejected as
#: unimplemented: FEFO lot costing is per-lot, not a second warehouse-level
#: averaging rule, so there is nothing to enable behind those names here.
VALUATION_METHOD = "weighted_avg"

#: Lot lifecycle. ``active`` is the only status FEFO may pick from;
#: ``quarantine`` is a manual hold, ``expired`` is set by
#: :meth:`StockService.expire_due_lots` (or lazily by the FEFO paths), and
#: ``depleted`` marks a lot whose ``qty_remaining`` reached zero.
LOT_STATUS_ACTIVE = "active"
LOT_STATUS_QUARANTINE = "quarantine"
LOT_STATUS_EXPIRED = "expired"
LOT_STATUS_DEPLETED = "depleted"
VALID_LOT_STATUSES = frozenset(
    {LOT_STATUS_ACTIVE, LOT_STATUS_QUARANTINE, LOT_STATUS_EXPIRED, LOT_STATUS_DEPLETED}
)

#: The asset every inventory valuation journal is booked in. Inventory value is
#: money in the reporting currency, so it follows ``ECO_CASH`` and
#: ``ECO_OPERATING_EXPENSE`` (both IRR) rather than the ECO-token accounts,
#: while the quantities themselves stay in the ``inv_*`` tables.
INVENTORY_VALUATION_ASSET = "IRR"

#: Journal reference types the inventory legs are booked under, so a batch can
#: always be traced back to the movement that caused it.
JOURNAL_RECEIPT = "inventory_receipt"
JOURNAL_COGS = "inventory_cogs"
JOURNAL_VARIANCE = "inventory_variance"
JOURNAL_RETURN = "inventory_return"

#: Money scale shared by ``InvStockMovement.unit_cost``/``total_cost``,
#: ``FinJournalEntry.amount`` and the valuation read API (Numeric(18, 8)).
_MONEY_QUANT = Decimal("0.00000001")


def _money(value: Decimal) -> Decimal:
    """Quantise ``value`` to the 8-decimal money scale of the Numeric columns."""
    return Decimal(value).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)


def _as_date(value: date | datetime | str | None, field: str = "expiry_date") -> date | None:
    """Coerce ``value`` to a :class:`~datetime.date`, or ``None``.

    Accepts a ``date`` (returned as is), a ``datetime`` (its calendar day) and
    an ISO ``YYYY-MM-DD`` string; anything else is a caller error rather than a
    silently ignored expiry, so it raises ``INVALID_EXPIRY_DATE`` (400).
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise EcoNojinException(
            f"Invalid {field}: {value!r} (expected an ISO YYYY-MM-DD date)",
            code="INVALID_EXPIRY_DATE",
            status_code=400,
        ) from exc


def _lot_is_expired(lot: InvLot, today: date | None = None) -> bool:
    """Whether ``lot``'s ``expiry_date`` has passed.

    ``None`` means "no expiry recorded" and is never expired. The comparison is
    a date-to-date one, so a lot expiring today is still usable today.
    """
    expiry = lot.expiry_date
    if expiry is None:
        return False
    return expiry < (today or date.today())


def _fefo_sorted(lots: list[InvLot]) -> list[InvLot]:
    """Order lots for FEFO: earliest expiry first, undated lots last."""
    return sorted(
        lots,
        key=lambda lot: (lot.expiry_date is None, lot.expiry_date or date.min, lot.id or ""),
    )


def _fifo_sorted(lots: list[InvLot]) -> list[InvLot]:
    """Order lots for FIFO: earliest received/created first, undated lots last."""
    return sorted(
        lots,
        key=lambda lot: (
            lot.received_at is None,
            lot.received_at or lot.created_at or date.min,
            lot.id or "",
        ),
    )


def _lot_unit_cost(lot: InvLot) -> Decimal:
    """The lot's ``unit_cost`` as a Decimal (Numeric round-trips safely)."""
    return Decimal(str(lot.unit_cost)) if lot.unit_cost is not None else Decimal("0")


def _allocate_fefo(
    candidates: list[InvLot], qty: Decimal
) -> tuple[list[tuple[InvLot, Decimal]], Decimal]:
    """Split ``qty`` across ``candidates`` (already FEFO-ordered).

    Returns the ``(lot, taken_qty)`` plan and the quantity left unallocated.
    A lot is drawn down to at most its ``qty_remaining``, and a drained lot is
    skipped rather than over-drawn.
    """
    plan: list[tuple[InvLot, Decimal]] = []
    remaining = Decimal(str(qty))
    for lot in candidates:
        if remaining <= 0:
            break
        available = Decimal(str(lot.qty_remaining or 0))
        if available <= 0:
            continue
        take = available if available < remaining else remaining
        plan.append((lot, take))
        remaining -= take
    return plan, remaining


def _is_cash_payment(payment_mode: str | None) -> bool:
    """Whether a receipt's ``payment_mode`` settles the supplier in cash.

    Documented rule: exactly ``"cash"`` (case-insensitive, surrounding
    whitespace ignored). Every other value — including ``None``, the default —
    is a purchase on account and books against ``ECO_ACCOUNTS_PAYABLE``.
    """
    return payment_mode is not None and payment_mode.strip().lower() == "cash"


def _build_movement(
    movement_type: str,
    sku_id: int,
    warehouse_id: int,
    qty: Decimal,
    created_by: str,
    from_location_id: int | None = None,
    to_location_id: int | None = None,
    lot_id: int | None = None,
    from_warehouse_id: int | None = None,
    to_warehouse_id: int | None = None,
    reference_type: str | None = None,
    reference_id: str | None = None,
    unit_cost: Decimal | None = None,
    notes: str | None = None,
    lot_uuid: str | None = None,
    signed_qty: Decimal | None = None,
    user_id: str | None = None,
) -> InvStockMovement:
    """Validate and build an immutable stock movement record (no DB I/O).

    ``unit_cost``/``total_cost`` are the movement's valuation: the quantity is
    priced on the way in (a receipt at its purchase cost) and on the way out
    (an issue, scrap, adjustment or transfer at the moving average of the
    moment), and both are quantised to the money scale of the Numeric columns.
    A caller-passed ``unit_cost`` of ``None`` stays ``None`` — the valuation
    fallback (standard cost, then zero) is resolved by the mutator, not here.

    ``lot_uuid`` is the additive lot-tracking seam: a lot-tracked leg carries
    the :class:`~database.models.InvLot` it moved, and everything else leaves it
    ``None`` exactly as before.
    """
    if movement_type not in VALID_MOVEMENT_TYPES:
        raise EcoNojinException(
            f"Invalid movement type: {movement_type}",
            code="INVALID_MOVEMENT_TYPE",
            status_code=400,
        )
    if qty <= 0:
        raise EcoNojinException(
            "Quantity must be positive", code="INVALID_QTY", status_code=400
        )

    priced = _money(unit_cost) if unit_cost is not None else None

    return InvStockMovement(
        movement_type=movement_type,
        sku_id=sku_id,
        warehouse_id=warehouse_id,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        lot_id=lot_id,
        lot_uuid=lot_uuid,
        signed_qty=signed_qty,
        qty=qty,
        unit_cost=priced,
        total_cost=_money(priced * qty) if priced is not None else None,
        reference_type=reference_type,
        reference_id=reference_id,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        created_by=created_by,
        created_at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Valuation (weighted average) and journal posting
# ---------------------------------------------------------------------------


def _average_costs_from_movements(
    movements: list[InvStockMovement],
    fallback_cost: Decimal = Decimal("0"),
) -> dict[int, Decimal]:
    """Moving-average unit cost per warehouse for one SKU's ordered movements.

    The pool of a warehouse is a ``(quantity, value)`` pair:

    * an **inbound** leg (``receipt``, ``return``, ``unblock``, and a
      ``transfer``'s inbound leg) adds ``qty`` at its cost;
    * an **outbound** leg (``issue``, ``scrap``, and a ``transfer``'s outbound
      leg) removes ``qty`` valued at the pool's current average, so the average
      itself is unchanged by an outflow;
    * an empty pool re-bases on the next inbound cost.

    ``fallback_cost`` prices an inbound leg that carries no ``unit_cost`` —
    only possible on rows written before valuation existed — with the SKU's
    standard cost, the documented receipt fallback.

    ``adjustment`` movements store ``abs(qty)`` with the signed delta only in a
    free-text note, so they cannot be replayed deterministically; they are
    booked at the current average anyway (which leaves it unchanged), so
    skipping them here is exact rather than approximate.
    """
    pools: dict[int, list[Decimal]] = {}

    def _inbound(warehouse_id: int, qty: Decimal, unit_cost: Decimal) -> None:
        pool = pools.setdefault(warehouse_id, [Decimal("0"), Decimal("0")])
        pool[0] += qty
        pool[1] += qty * unit_cost

    def _outbound(warehouse_id: int, qty: Decimal) -> None:
        pool = pools.setdefault(warehouse_id, [Decimal("0"), Decimal("0")])
        if pool[0] <= 0:  # nothing valued to draw from: leave the pool alone
            return
        average = pool[1] / pool[0]
        pool[0] -= qty
        if pool[0] <= 0:  # drained: re-base instead of keeping rounding dust
            pool[0] = Decimal("0")
            pool[1] = Decimal("0")
        else:
            pool[1] = average * pool[0]

    for movement in movements:
        qty = Decimal(str(movement.qty))
        unit_cost = (
            Decimal(str(movement.unit_cost)) if movement.unit_cost is not None else fallback_cost
        )
        warehouse_id = int(movement.warehouse_id)
        if movement.movement_type in ("receipt", "return", "unblock"):
            _inbound(warehouse_id, qty, unit_cost)
        elif movement.movement_type in ("issue", "scrap"):
            _outbound(warehouse_id, qty)
        elif movement.movement_type == "transfer":
            # One row carries both legs: out of the source warehouse it is
            # stored on, into ``to_warehouse_id``.
            _outbound(warehouse_id, qty)
            if movement.to_warehouse_id is not None:
                _inbound(int(movement.to_warehouse_id), qty, unit_cost)
        # reservation / release / stocktake change no value; adjustment is
        # unsigned by design (see the docstring).

    return {
        warehouse_id: (value / qty if qty > 0 else Decimal("0"))
        for warehouse_id, (qty, value) in pools.items()
    }


async def _ledger_schema_present(db: AsyncSession) -> bool:
    """Whether the finance tables this module journals against are deployed.

    Inventory can legitimately run against a database carrying the ``inv_*``
    tables only (a partial schema, exactly how
    ``services/inventory/tests/test_p0_3_http500_repair.py`` builds its
    engine). Valuing stock must not break such a deployment, so the posting
    path checks once per service instance and skips the journal when the
    batch table is absent.
    """
    connection = await db.connection()
    return await connection.run_sync(
        lambda sync_connection: inspect(sync_connection).has_table(
            FinJournalBatch.__tablename__
        )
    )


async def _post_journal(
    db: AsyncSession,
    *,
    reference_type: str,
    reference_id: str,
    entries: list[dict],
    description: str | None = None,
    created_by: str | None = None,
) -> FinJournalBatch:
    """Write one balanced, posted journal batch inside the caller's transaction.

    The guarantees mirror ``LedgerService.create_journal_batch`` — a non-empty
    entry list, positive Decimal amounts, a valid entry type, an allowlisted
    asset and debits == credits — with two deliberate differences:

    * ``is_posted``/``posted_at`` are written on creation (the P0-1 convention
      the wallet and settlement batches follow), so ``trial_balance`` and
      ``profit_and_loss`` see the rows without a second round trip;
    * the rows are flushed, never committed: they land in the caller's
      transaction, so the stock mutation and its journal commit together or not
      at all (the failure rule in the module docstring).

    Accounts are resolved through the canonical chart with
    :func:`~services.finance.chart_of_accounts.ensure_account`, and
    ``account_id`` carries the account **code** — the convention
    ``services/finance/account_ref.py`` names.
    """
    if not entries:
        raise EcoNojinException(
            "Journal batch must have at least one entry", code="EMPTY_JOURNAL"
        )

    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for entry in entries:
        amount = Decimal(str(entry["amount"]))
        if amount <= 0:
            raise EcoNojinException(f"Amount must be positive: {amount}", code="INVALID_AMOUNT")

        if entry["entry_type"] == "debit":
            total_debit += amount
        elif entry["entry_type"] == "credit":
            total_credit += amount
        else:
            raise EcoNojinException(
                f"Invalid entry_type: {entry['entry_type']}", code="INVALID_ENTRY_TYPE"
            )

        if entry["asset"] not in ACCOUNT_ASSETS:
            raise EcoNojinException(f"Invalid asset: {entry['asset']}", code="INVALID_ASSET")

    if total_debit != total_credit:
        raise EcoNojinException(
            f"Journal not balanced: debits={total_debit}, credits={total_credit}",
            code="UNBALANCED_JOURNAL",
        )

    for code in sorted({str(entry["account_id"]) for entry in entries}):
        spec = get_account_spec(code)
        if spec is None:
            raise UnknownAccountCode(f"Unknown chart account code: {code!r}")
        await ensure_account(
            db,
            code=spec.code,
            name=spec.name,
            type=spec.type,
            asset=spec.asset,
            currency=spec.currency,
            parent_code=spec.parent_code,
            description=spec.description,
        )

    batch = FinJournalBatch(
        batch_number=f"JB-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}",
        batch_date=date.today(),
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
        created_by=created_by,
        is_posted=True,
        posted_at=datetime.now(UTC),
    )
    db.add(batch)
    await db.flush()

    for entry in entries:
        db.add(
            FinJournalEntry(
                batch_id=batch.id,
                account_id=str(entry["account_id"]),
                entry_type=entry["entry_type"],
                asset=entry["asset"],
                amount=Decimal(str(entry["amount"])),
                description=entry.get("description"),
            )
        )
    await db.flush()
    return batch


async def _is_expired(reservation: InvReservation, now: datetime) -> bool:
    """True when ``reservation`` has an ``expires_at`` at or before ``now``.

    Naive timestamps (SQLite stores ``DateTime(timezone=True)`` as naive
    UTC strings) are read as UTC so the comparison stays dialect-proof.
    """
    expires_at: datetime | None = reservation.expires_at
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= now


async def sweep_expired_reservations(
    db: AsyncSession,
    sku_id: int | None = None,
    warehouse_id: int | None = None,
) -> int:
    """Release active reservations past ``expires_at``; return how many.

    Each expired reservation releases the quantity it still holds
    (``qty - consumed_qty``) back to its balance's ``reserved`` counter
    (so ``available`` stops counting it), is marked ``status='expired'``
    with ``released_at`` set, and leaves a ``release`` movement for the
    audit ledger. ``sku_id``/``warehouse_id`` optionally scope the sweep
    to one balance key — ``StockService.reserve_stock`` calls it lazily
    for the pair it is about to reserve against, which is why an expired
    reservation can no longer block a new reservation even though
    nothing else ever runs a scheduled sweep.

    The sweep commits its own work when it released something (every
    public method in this service commits), so callers that wrap it in a
    larger transaction should pass through the service method that
    already invokes it rather than calling it mid-transaction. Returns
    the number of reservations released (0 when nothing was expired).
    """
    now = datetime.now(UTC)
    stmt = select(InvReservation).where(
        InvReservation.status == "active",
        InvReservation.expires_at.is_not(None),
    )
    if sku_id is not None:
        stmt = stmt.where(InvReservation.sku_id == sku_id)
    if warehouse_id is not None:
        stmt = stmt.where(InvReservation.warehouse_id == warehouse_id)

    reservations = (await db.execute(stmt.with_for_update())).scalars().all()

    released = 0
    for reservation in reservations:
        if not await _is_expired(reservation, now):
            continue

        remaining = reservation.qty - reservation.consumed_qty
        if remaining > 0:
            balance = (
                (
                    await db.execute(
                        select(InvInventoryBalance)
                        .where(
                            InvInventoryBalance.sku_id == reservation.sku_id,
                            InvInventoryBalance.warehouse_id == reservation.warehouse_id,
                            InvInventoryBalance.location_id
                            == (reservation.location_id or 0),
                            InvInventoryBalance.lot_id == (reservation.lot_id or 0),
                        )
                        .with_for_update()
                    )
                )
                .scalars()
                .one_or_none()
            )
            if balance is not None:
                if balance.reserved >= remaining:
                    balance.reserved -= remaining
                else:  # pragma: no cover - defensive against manual tampering
                    balance.reserved = Decimal("0")
                balance.last_movement_at = now
            db.add(
                _build_movement(
                    "release",
                    reservation.sku_id,
                    reservation.warehouse_id,
                    remaining,
                    reservation.created_by,
                    from_location_id=reservation.location_id,
                    reference_type=reservation.reference_type,
                    reference_id=str(reservation.reference_id),
                    notes=f"Reservation {reservation.id} expired; released {remaining}",
                )
            )

        reservation.status = "expired"
        reservation.released_at = now
        released += 1

    if released:
        await db.flush()
        await db.commit()
    return released


class StockService:
    """Atomic stock management service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)
        # Whether journal posting is possible on this database; resolved once by
        # ``_can_post_journal`` (see ``_ledger_schema_present``).
        self._ledger_ready: bool | None = None

    # ------------------------------------------------------------------
    # SKU / Warehouse / Location management
    # ------------------------------------------------------------------

    async def create_sku(
        self,
        sku_code: str,
        name: str,
        uom: str = "kg",
        category_id: int | None = None,
        standard_cost: Decimal | None = None,
        warehouse_id: int | None = None,
    ) -> InvSKU:
        existing = await self.db.execute(select(InvSKU).where(InvSKU.sku_code == sku_code))
        if existing.scalar_one_or_none():
            raise EcoNojinException(
                f"SKU {sku_code} already exists", code="SKU_EXISTS", status_code=409
            )

        sku = InvSKU(
            sku_code=sku_code,
            name=name,
            uom=uom,
            category_id=category_id,
            standard_cost=standard_cost,
            default_warehouse_id=warehouse_id,
        )
        self.db.add(sku)
        await self.db.commit()
        await self.db.refresh(sku)
        return sku

    async def create_warehouse(self, code: str, name: str, city: str | None = None) -> InvWarehouse:
        existing = await self.db.execute(select(InvWarehouse).where(InvWarehouse.code == code))
        if existing.scalar_one_or_none():
            raise EcoNojinException(
                f"Warehouse {code} already exists", code="WH_EXISTS", status_code=409
            )

        wh = InvWarehouse(code=code, name=name, city=city, is_active=True)
        self.db.add(wh)
        await self.db.commit()
        await self.db.refresh(wh)
        return wh

    async def create_location(
        self, warehouse_id: int, code: str, loc_type: str = "bin"
    ) -> InvLocation:
        loc = InvLocation(
            warehouse_id=warehouse_id,
            code=code,
            location_type=loc_type,
            is_active=True,
            is_pickable=True,
            is_receivable=True,
        )
        self.db.add(loc)
        await self.db.commit()
        await self.db.refresh(loc)
        return loc

    async def get_sku(self, sku_code: str) -> InvSKU:
        result = await self.db.execute(select(InvSKU).where(InvSKU.sku_code == sku_code))
        sku = result.scalar_one_or_none()
        if not sku:
            raise EcoNojinException(
                f"SKU not found: {sku_code}", code="SKU_NOT_FOUND", status_code=404
            )
        return sku

    async def get_sku_by_id(self, sku_id: int) -> InvSKU:
        result = await self.db.execute(select(InvSKU).where(InvSKU.id == sku_id))
        sku = result.scalar_one_or_none()
        if not sku:
            raise EcoNojinException(
                f"SKU not found: {sku_id}", code="SKU_NOT_FOUND", status_code=404
            )
        return sku

    async def _lock_balance(
        self,
        sku_id: int,
        warehouse_id: int,
        location_id: int | None = None,
        lot_id: int | None = None,
    ) -> InvInventoryBalance | None:
        """Return the balance row for the full (sku, warehouse, location, lot) key.

        The row is locked with ``SELECT ... FOR UPDATE`` where the dialect
        supports it (PostgreSQL/MySQL); on SQLite SQLAlchemy drops the
        locking clause, so the statement degrades to a plain SELECT and
        the guarantee tested there is the row *selection* (exactly one
        row, thanks to the unique constraint) rather than the lock. The
        0 sentinels for ``location_id``/``lot_id`` match the column
        defaults and the unique index.
        """
        result = await self.db.execute(
            select(InvInventoryBalance)
            .where(
                InvInventoryBalance.sku_id == sku_id,
                InvInventoryBalance.warehouse_id == warehouse_id,
                InvInventoryBalance.location_id == (location_id or 0),
                InvInventoryBalance.lot_id == (lot_id or 0),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_or_create_balance(
        self,
        sku_id: int,
        warehouse_id: int,
        location_id: int | None = None,
        lot_id: int | None = None,
    ) -> InvInventoryBalance:
        """Get or create the balance row for the full (sku, wh, location, lot) key.

        The lookup locks the row, and the INSERT runs inside a SAVEPOINT
        guarded by the unique constraint on
        (sku_id, warehouse_id, location_id, lot_id): two concurrent
        first touches cannot both insert — the loser's INSERT fails with
        ``IntegrityError``, the savepoint rolls back, and the winner's
        row is re-read under the lock. Without the unique constraint the
        loser would silently keep a second row and split the balance.
        """
        balance = await self._lock_balance(sku_id, warehouse_id, location_id, lot_id)
        if balance is not None:
            return balance

        balance = InvInventoryBalance(
            sku_id=sku_id,
            warehouse_id=warehouse_id,
            location_id=location_id or 0,
            lot_id=lot_id or 0,
            on_hand=Decimal("0"),
            reserved=Decimal("0"),
            blocked=Decimal("0"),
            in_transit=Decimal("0"),
        )
        try:
            async with self.db.begin_nested():
                self.db.add(balance)
                await self.db.flush()
        except IntegrityError:
            # Lost a concurrent first-touch race: re-read the winner's row.
            balance = await self._lock_balance(sku_id, warehouse_id, location_id, lot_id)
            if balance is None:  # pragma: no cover - defensive re-raise
                raise
        return balance

    # ------------------------------------------------------------------
    # Valuation and journal posting
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_valuation_method(method: str) -> str:
        """Validate ``method``; weighted average, standard cost and FIFO pass.

        ``fifo`` is implemented for lot-tracked SKUs (issues draw from the
        oldest received lot first). Non-lot-tracked FIFO issues fall back to
        the moving-average cost because receipt-order tracking is not
        maintained outside lots.
        """
        if method not in VALID_VALUATION_METHODS:
            raise EcoNojinException(
                f"Invalid valuation method: {method}", code="INVALID_VALUATION_METHOD"
            )
        return method

    async def _can_post_journal(self) -> bool:
        """Whether this database can take a journal batch (cached per instance).

        A database carrying the inventory tables but not the finance ones still
        values its stock: the batch is skipped — and the reason logged once —
        rather than the stock mutation failing.
        """
        if self._ledger_ready is None:
            self._ledger_ready = await _ledger_schema_present(self.db)
            if not self._ledger_ready:
                logger.warning(
                    "Finance tables absent: stock movements will not journal to %s",
                    FinJournalBatch.__tablename__,
                )
        return self._ledger_ready

    async def _sku_standard_cost(self, sku_id: int) -> Decimal:
        """The SKU's ``standard_cost``, or zero when it is unset.

        The documented valuation fallback for a movement that carries no cost of
        its own (a receipt booked without ``unit_cost``) and the price an
        inbound leg written before valuation existed is replayed at.
        """
        result = await self.db.execute(
            select(InvSKU.standard_cost).where(InvSKU.id == sku_id)
        )
        value = result.scalar_one_or_none()
        return Decimal(str(value)) if value is not None else Decimal("0")

    async def _moving_average_costs(self, sku_id: int) -> dict[int, Decimal]:
        """Moving-average unit cost per warehouse for one SKU, from the ledger."""
        movements = (
            (
                await self.db.execute(
                    select(InvStockMovement)
                    .where(InvStockMovement.sku_id == sku_id)
                    .order_by(InvStockMovement.created_at, InvStockMovement.id)
                )
            )
            .scalars()
            .all()
        )
        return _average_costs_from_movements(movements, await self._sku_standard_cost(sku_id))

    async def _current_average_cost(self, sku_id: int, warehouse_id: int) -> Decimal:
        """The moving-average unit cost of one ``(sku, warehouse)`` key right now."""
        costs = await self._moving_average_costs(sku_id)
        return costs.get(warehouse_id, Decimal("0"))

    async def _post_value_pair(
        self,
        reference_type: str,
        reference_id: str,
        *,
        debit_code: str,
        credit_code: str,
        amount: Decimal,
        description: str,
        created_by: str | None,
    ) -> FinJournalBatch | None:
        """Post one balanced debit/credit pair for ``amount``.

        Returns ``None`` when there is nothing to book — a zero-value movement
        has no value to recognise, and a database without the finance tables
        cannot take the batch (``_can_post_journal``).
        """
        amount = _money(amount)
        if amount <= 0 or not await self._can_post_journal():
            return None

        return await _post_journal(
            self.db,
            reference_type=reference_type,
            reference_id=reference_id,
            entries=[
                {
                    "account_id": debit_code,
                    "entry_type": "debit",
                    "asset": INVENTORY_VALUATION_ASSET,
                    "amount": str(amount),
                    "description": description,
                },
                {
                    "account_id": credit_code,
                    "entry_type": "credit",
                    "asset": INVENTORY_VALUATION_ASSET,
                    "amount": str(amount),
                    "description": description,
                },
            ],
            description=description,
            created_by=created_by,
        )

    # ------------------------------------------------------------------
    # Stock movements (append-only ledger)
    # ------------------------------------------------------------------

    async def _create_movement(
        self,
        movement_type: str,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        created_by: str,
        from_location_id: int | None = None,
        to_location_id: int | None = None,
        lot_id: int | None = None,
        from_warehouse_id: int | None = None,
        to_warehouse_id: int | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
        unit_cost: Decimal | None = None,
        notes: str | None = None,
        lot_uuid: str | None = None,
        signed_qty: Decimal | None = None,
        user_id: str | None = None,
    ) -> InvStockMovement:
        """Create an immutable stock movement record."""
        movement = _build_movement(
            movement_type,
            sku_id,
            warehouse_id,
            qty,
            created_by,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            lot_id=lot_id,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            reference_type=reference_type,
            reference_id=reference_id,
            unit_cost=unit_cost,
            notes=notes,
            lot_uuid=lot_uuid,
            signed_qty=signed_qty,
            user_id=user_id,
        )
        self.db.add(movement)
        await self.db.flush()
        return movement

    async def receipt(
        self,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        location_id: int | None = None,
        lot_id: int | None = None,
        unit_cost: Decimal | None = None,
        reference_type: str = "purchase_receipt",
        reference_id: str | None = None,
        created_by: str = "system",
        payment_mode: str | None = None,
        lot_number: str | None = None,
        expiry_date: date | datetime | str | None = None,
        user_id: str | None = None,
    ) -> InvStockMovement:
        """Receive goods into inventory (increases on_hand).

        The target balance row is locked through
        ``get_or_create_balance`` (FOR UPDATE on row-locking dialects,
        a plain SELECT on SQLite) before the read-modify-write.

        Valuation: the receipt is booked at ``unit_cost`` when the caller
        prices it, otherwise at the SKU's ``standard_cost`` and finally at zero
        — so a movement written through this path always carries a cost the
        moving average can blend. Accounting: debit ``ECO_INVENTORY`` for
        ``qty x cost`` against ``ECO_ACCOUNTS_PAYABLE``, or against ``ECO_CASH``
        when ``payment_mode`` is ``"cash"`` (see :func:`_is_cash_payment`).

        Lots: passing ``lot_number`` (optionally with ``expiry_date``) receives
        the goods into a real :class:`~database.models.InvLot` — created on
        first receipt of that number for this SKU, reused (and topped up) on a
        repeat — stamps ``lot_uuid`` on the balance row and the movement, and
        prices the lot at this receipt's cost. Omitting it keeps the legacy
        sentinel path untouched: no lot row is written, ``lot_uuid`` stays NULL
        and the stock is still valued by the warehouse moving average.
        """
        cost = unit_cost if unit_cost is not None else await self._sku_standard_cost(sku_id)

        lot: InvLot | None = None
        if lot_number:
            lot = await self._get_or_create_lot(
                sku_id=sku_id,
                lot_number=lot_number,
                qty=qty,
                unit_cost=cost,
                expiry_date=expiry_date,
            )

        balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, lot_id)
        if lot is not None and balance.lot_uuid is None:
            # First lot-tracked receipt for this (sku, warehouse, location)
            # key: the row becomes lot-tracked from here on. A later non-lot
            # receipt into the same row must not un-track it.
            balance.lot_uuid = lot.id
        balance.on_hand += qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "receipt",
            sku_id,
            warehouse_id,
            qty,
            created_by,
            to_location_id=location_id,
            lot_id=lot_id,
            lot_uuid=lot.id if lot is not None else None,
            reference_type=reference_type,
            reference_id=reference_id,
            unit_cost=cost,
            user_id=user_id,
        )
        await self._post_value_pair(
            JOURNAL_RECEIPT,
            str(movement.id),
            debit_code=ECO_INVENTORY,
            credit_code=(
                ECO_CASH if _is_cash_payment(payment_mode) else ECO_ACCOUNTS_PAYABLE
            ),
            amount=cost * qty,
            description=(
                f"Goods receipt: sku={sku_id} warehouse={warehouse_id} "
                f"qty={qty} @ {cost}"
            ),
            created_by=created_by,
        )
        await self.db.commit()
        return movement

    async def issue(
        self,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        location_id: int | None = None,
        reference_type: str = "sales_issue",
        reference_id: str | None = None,
        created_by: str = "system",
        allow_expired: bool = False,
        valuation_method: str = VALUATION_METHOD,
        user_id: str | None = None,
    ) -> InvStockMovement:
        """Issue goods from inventory (decreases on_hand). FEFO expiry picking.

        The target balance row is locked through ``get_or_create_balance``
        (FOR UPDATE on row-locking dialects, a plain SELECT on SQLite)
        before the availability check and the decrement, so two
        concurrent issues cannot both pass the check against a stale
        read.

        Valuation/accounting, and the two policies selected by the row's
        ``lot_uuid``:

        * **not lot-tracked** — the issue is valued at the warehouse's current
          moving-average cost and posts debit ``ECO_COGS`` / credit
          ``ECO_INVENTORY`` for that value, as one movement and one batch.
        * **lot-tracked** — the quantity is allocated **FEFO** across the SKU's
          active lots (:meth:`_lot_tracked_candidates` orders them by
          ``expiry_date``), each leg is costed at its own lot's ``unit_cost``
          and carries that lot's ``lot_uuid``, the lot's ``qty_remaining`` is
          decremented (a drained lot flips to ``depleted``), and every leg posts
          its own ``ECO_COGS``/``ECO_INVENTORY`` batch. A lot whose expiry has
          passed is never picked (the lazy check flips it to ``expired``); an
          issue that can only be served from expired lots is refused with
          ``EXPIRED_LOT`` unless ``allow_expired=True``.

        Returns the first (FEFO-earliest) movement; the remaining legs of a
        split issue are in the ledger via :meth:`get_movements`.
        """
        balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, None)
        if balance.on_hand < qty:
            raise EcoNojinException(
                f"Insufficient stock: {balance.on_hand} < {qty}",
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )

        method = self._resolve_valuation_method(valuation_method)

        if balance.lot_uuid is not None:
            sorter = _fifo_sorted if method == "fifo" else None
            first = await self._issue_from_lots(
                balance=balance,
                sku_id=sku_id,
                warehouse_id=warehouse_id,
                qty=qty,
                location_id=location_id,
                reference_type=reference_type,
                reference_id=reference_id,
                created_by=created_by,
                allow_expired=allow_expired,
                sorter=sorter,
            )
            await self.db.commit()
            return first

        if method == "standard":
            unit_cost = await self._sku_standard_cost(sku_id)
        else:
            unit_cost = await self._current_average_cost(sku_id, warehouse_id)
        balance.on_hand -= qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "issue",
            sku_id,
            warehouse_id,
            qty,
            created_by,
            from_location_id=location_id,
            reference_type=reference_type,
            reference_id=reference_id,
            unit_cost=unit_cost,
            user_id=user_id,
        )
        await self._post_value_pair(
            JOURNAL_COGS,
            str(movement.id),
            debit_code=ECO_COGS,
            credit_code=ECO_INVENTORY,
            amount=unit_cost * qty,
            description=(
                f"COGS: sku={sku_id} warehouse={warehouse_id} "
                f"qty={qty} @ {unit_cost}"
            ),
            created_by=created_by,
        )
        await self.db.commit()
        return movement

    async def transfer(
        self,
        sku_id: int,
        from_warehouse_id: int,
        to_warehouse_id: int,
        qty: Decimal,
        from_location_id: int | None = None,
        to_location_id: int | None = None,
        created_by: str = "system",
        user_id: str | None = None,
    ) -> InvStockMovement:
        """Transfer stock between warehouses/locations.

        Both balance rows are locked (FOR UPDATE on row-locking dialects,
        a plain SELECT on SQLite) in a sorted (warehouse, location) order
        before any read-modify-write, so a concurrent reverse transfer
        B→A cannot deadlock against this A→B by taking the same two row
        locks in opposite order. The source check still runs before the
        destination is touched in the ledger.

        Valuation: both legs are recorded at the **source** warehouse's
        moving-average cost, so the transferred value is preserved and the
        destination pool re-bases on it. No journal batch is posted: the value
        stays inside ``ECO_INVENTORY``, so a batch would debit and credit the
        same account.

        Lots: a lot-tracked source row propagates its ``lot_uuid`` onto the
        movement row and, when the destination row is not lot-tracked yet,
        onto that row — the goods are the same batch at the other end. The
        lot's own ``qty_remaining`` is untouched (a transfer moves a batch
        between places, it does not consume it), so FEFO availability keeps
        following the lot rather than the warehouse.
        """
        src_key = (from_warehouse_id, from_location_id or 0)
        dst_key = (to_warehouse_id, to_location_id or 0)
        balances: dict[tuple[int, int], InvInventoryBalance] = {}
        for key in sorted({src_key, dst_key}):
            balances[key] = await self.get_or_create_balance(sku_id, *key)

        src_balance = balances[src_key]
        if src_balance.on_hand < qty:
            raise EcoNojinException(
                f"Insufficient stock at source: {src_balance.on_hand} < {qty}",
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )

        unit_cost = await self._current_average_cost(sku_id, from_warehouse_id)
        lot_uuid = src_balance.lot_uuid

        dst_balance = balances[dst_key]
        if lot_uuid is not None and dst_balance.lot_uuid is None:
            dst_balance.lot_uuid = lot_uuid
        src_balance.on_hand -= qty
        dst_balance.on_hand += qty

        src_balance.last_movement_at = datetime.now(UTC)
        dst_balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "transfer",
            sku_id,
            from_warehouse_id,
            qty,
            created_by,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            reference_type="transfer",
            unit_cost=unit_cost,
            lot_uuid=lot_uuid,
            user_id=user_id,
        )
        await self.db.commit()
        return movement

    async def adjust(
        self,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        adjustment_type: str = "stocktake",
        reason: str | None = None,
        created_by: str = "system",
        user_id: str | None = None,
    ) -> InvStockMovement:
        """Adjust stock levels (positive or negative). Creates adjustment movement.

        ``on_hand`` has a -0 floor: a negative adjustment that would
        drive it below zero is rejected (``NEGATIVE_ON_HAND``) instead of
        silently writing a negative balance. The movement row records
        ``abs(qty)`` because the ledger column must stay positive for
        every movement type; the signed delta lives in ``notes``, so
        ``reconcile_inventory`` cannot fold adjustments into its signed
        movement sum (see the method docstring there).

        Valuation/accounting: the delta is valued at the moving-average
        cost and posts against ``ECO_INVENTORY_VARIANCE`` — a positive
        adjustment (found stock) debits ``ECO_INVENTORY`` against the
        variance account, a negative one (shrinkage) does the reverse.

        Lots: on a lot-tracked row the adjustment movement carries that row's
        ``lot_uuid`` so the variance is traceable to the batch it was booked
        against. ``qty_remaining`` is deliberately not re-allocated here —
        only the FEFO paths of :meth:`issue` / :meth:`consume_reservation`
        split quantities across lots.
        """
        movement_type = "adjustment"
        balance = await self.get_or_create_balance(sku_id, warehouse_id, None, None)
        new_on_hand = balance.on_hand + qty
        if new_on_hand < Decimal("0"):
            raise EcoNojinException(
                f"Adjustment would drive on_hand negative: {balance.on_hand} + {qty}",
                code="NEGATIVE_ON_HAND",
                status_code=400,
            )
        unit_cost = await self._current_average_cost(sku_id, warehouse_id)
        balance.on_hand = new_on_hand
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            movement_type,
            sku_id,
            warehouse_id,
            abs(qty),
            created_by,
            reference_type=adjustment_type,
            notes=f"Adjustment: {qty} - {reason or ''}",
            unit_cost=unit_cost,
            lot_uuid=balance.lot_uuid,
            signed_qty=qty,
            user_id=user_id,
        )
        await self._post_value_pair(
            JOURNAL_VARIANCE,
            str(movement.id),
            # Found stock adds inventory value; shrinkage writes it off.
            debit_code=ECO_INVENTORY if qty > 0 else ECO_INVENTORY_VARIANCE,
            credit_code=ECO_INVENTORY_VARIANCE if qty > 0 else ECO_INVENTORY,
            amount=abs(qty) * unit_cost,
            description=(
                f"Adjustment {qty}: sku={sku_id} warehouse={warehouse_id} "
                f"qty={abs(qty)} @ {unit_cost} - {reason or ''}"
            ),
            created_by=created_by,
        )
        await self.db.commit()
        return movement

    async def return_goods(
        self,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        location_id: int | None = None,
        reference_type: str = "return",
        reference_id: str | None = None,
        unit_cost: Decimal | None = None,
        created_by: str = "system",
        user_id: str | None = None,
    ) -> InvStockMovement:
        """Process a return (increases on_hand, decreases COGS impact).

        The target balance row is locked through ``get_or_create_balance``
        (FOR UPDATE on row-locking dialects, a plain SELECT on SQLite).

        Valuation/accounting: a customer return is the reverse of the issue
        that shipped it — the goods come back at the moving-average cost of
        the warehouse (or at ``unit_cost`` when the caller prices the return),
        and the batch posts debit ``ECO_INVENTORY`` / credit ``ECO_COGS``.
        """
        balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, None)
        cost = (
            unit_cost
            if unit_cost is not None
            else await self._current_average_cost(sku_id, warehouse_id)
        )
        balance.on_hand += qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "return",
            sku_id,
            warehouse_id,
            qty,
            created_by,
            to_location_id=location_id,
            reference_type=reference_type,
            reference_id=reference_id,
            unit_cost=cost,
        )
        await self._post_value_pair(
            JOURNAL_RETURN,
            str(movement.id),
            debit_code=ECO_INVENTORY,
            credit_code=ECO_COGS,
            amount=cost * qty,
            description=(
                f"Return: sku={sku_id} warehouse={warehouse_id} qty={qty} @ {cost}"
            ),
            created_by=created_by,
        )
        await self.db.commit()
        return movement

    async def scrap(
        self,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        reason: str | None = None,
        created_by: str = "system",
    ) -> InvStockMovement:
        """Write off damaged/destroyed goods (decreases on_hand).

        Valuation/accounting: the write-off is valued at the moving-average
        cost and posts debit ``ECO_INVENTORY_VARIANCE`` / credit
        ``ECO_INVENTORY``. ``unblock_stock`` is the exact reverse of this
        batch, so returning goods to usable stock books the value back.

        Lots: on a lot-tracked row the scrap movement carries that row's
        ``lot_uuid``; the lot's ``qty_remaining`` is left to the FEFO paths
        rather than partially written off here, so a scrap is traceable to its
        batch without splitting it.
        """
        balance = await self.get_or_create_balance(sku_id, warehouse_id, None, None)
        if balance.on_hand < qty:
            raise EcoNojinException(
                f"Insufficient stock to scrap: {balance.on_hand} < {qty}",
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )
        unit_cost = await self._current_average_cost(sku_id, warehouse_id)
        balance.on_hand -= qty
        balance.blocked += qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "scrap",
            sku_id,
            warehouse_id,
            qty,
            created_by,
            reference_type="scrap",
            notes=reason,
            unit_cost=unit_cost,
            lot_uuid=balance.lot_uuid,
        )
        await self._post_value_pair(
            JOURNAL_VARIANCE,
            str(movement.id),
            debit_code=ECO_INVENTORY_VARIANCE,
            credit_code=ECO_INVENTORY,
            amount=unit_cost * qty,
            description=(
                f"Scrap write-off: sku={sku_id} warehouse={warehouse_id} "
                f"qty={qty} @ {unit_cost} - {reason or ''}"
            ),
            created_by=created_by,
        )
        await self.db.commit()
        return movement

    async def unblock_stock(
        self,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        location_id: int | None = None,
        lot_id: int | None = None,
        reason: str | None = None,
        created_by: str = "system",
    ) -> InvStockMovement:
        """Return a blocked (written-off) quantity to usable stock.

        Symmetric with :meth:`scrap`: scrap removes ``qty`` from
        ``on_hand`` and adds it to the ``blocked`` write-off pool, so
        unblocking restores ``on_hand`` and decrements ``blocked`` —
        without this path ``blocked`` could only grow. Refuses to
        unblock more than the pool holds (``INSUFFICIENT_BLOCKED``) so
        the counter can never go negative.

        Valuation/accounting: the restored goods are valued at the
        moving-average cost and post the exact reverse of the scrap batch —
        debit ``ECO_INVENTORY`` / credit ``ECO_INVENTORY_VARIANCE`` — so the
        inventory value and the variance account stay in step.
        """
        balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, lot_id)
        if balance.blocked < qty:
            raise EcoNojinException(
                f"Blocked quantity too small to unblock: {balance.blocked} < {qty}",
                code="INSUFFICIENT_BLOCKED",
                status_code=400,
            )
        unit_cost = await self._current_average_cost(sku_id, warehouse_id)
        balance.blocked -= qty
        balance.on_hand += qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "unblock",
            sku_id,
            warehouse_id,
            qty,
            created_by,
            to_location_id=location_id,
            lot_id=lot_id,
            lot_uuid=balance.lot_uuid,
            reference_type="unblock",
            notes=f"Unblock: {qty} - {reason or ''}",
            unit_cost=unit_cost,
        )
        await self._post_value_pair(
            JOURNAL_VARIANCE,
            str(movement.id),
            debit_code=ECO_INVENTORY,
            credit_code=ECO_INVENTORY_VARIANCE,
            amount=unit_cost * qty,
            description=(
                f"Unblock: sku={sku_id} warehouse={warehouse_id} "
                f"qty={qty} @ {unit_cost} - {reason or ''}"
            ),
            created_by=created_by,
        )
        await self.db.commit()
        return movement

    # ------------------------------------------------------------------
    # Lot / batch management (traceability and FEFO expiry picking)
    # ------------------------------------------------------------------

    async def create_lot(
        self,
        sku_id: int,
        lot_number: str,
        expiry_date: date | datetime | str | None = None,
        unit_cost: Decimal | None = None,
        qty_received: Decimal = Decimal("0"),
        supplier_ref: str | None = None,
        status: str = LOT_STATUS_ACTIVE,
        received_at: datetime | None = None,
    ) -> InvLot:
        """Register a lot/batch of one SKU (``qty_remaining`` starts full).

        The id is generated here (a String(36) uuid) so the lot is
        addressable from ``lot_uuid`` before anything references it. A lot
        registered this way is not yet stock: quantities enter inventory
        through :meth:`receipt` with ``lot_number``, which is what stamps
        ``lot_uuid`` on the balance row and the movement. Registering a lot up
        front is still useful for pre-labelled or in-transit batches.
        """
        await self.get_sku_by_id(sku_id)
        expiry = _as_date(expiry_date)
        status = self._validate_lot_status(status)
        number = self._normalise_lot_number(lot_number)

        clash = await self._active_lot_for_number(sku_id, number)
        if clash is not None:
            raise EcoNojinException(
                f"Lot {number} already exists for sku {sku_id}",
                code="LOT_EXISTS",
                status_code=409,
            )

        lot = InvLot(
            id=str(uuid4()),
            sku_id=str(sku_id),
            lot_number=number,
            expiry_date=expiry,
            received_at=received_at or datetime.now(UTC),
            unit_cost=unit_cost if unit_cost is not None else Decimal("0"),
            qty_received=qty_received,
            qty_remaining=qty_received,
            supplier_ref=supplier_ref,
            status=status,
            created_at=datetime.now(UTC),
        )
        self.db.add(lot)
        await self.db.commit()
        await self.db.refresh(lot)
        return lot

    async def get_lot(self, lot_id: str) -> InvLot:
        """Load one lot by its uuid, or raise ``LOT_NOT_FOUND`` (404)."""
        result = await self.db.execute(select(InvLot).where(InvLot.id == str(lot_id)))
        lot = result.scalar_one_or_none()
        if not lot:
            raise EcoNojinException(
                f"Lot not found: {lot_id}", code="LOT_NOT_FOUND", status_code=404
            )
        return lot

    async def list_lots(
        self,
        sku_id: int | None = None,
        status: str | None = None,
        expiry_before: date | datetime | str | None = None,
    ) -> list[InvLot]:
        """List lots, optionally scoped to one SKU, status or expiry window.

        ``expiry_before`` keeps lots whose ``expiry_date`` is strictly earlier
        than the given date (lots with no expiry recorded never match), so it
        answers "what is about to run out" rather than "what has already".
        """
        stmt = select(InvLot)
        if sku_id is not None:
            stmt = stmt.where(InvLot.sku_id == str(sku_id))
        if status is not None:
            stmt = stmt.where(InvLot.status == status)
        if expiry_before is not None:
            before = _as_date(expiry_before, "expiry_before")
            stmt = stmt.where(
                InvLot.expiry_date.is_not(None), InvLot.expiry_date < before
            )
        result = await self.db.execute(
            stmt.order_by(InvLot.expiry_date, InvLot.created_at, InvLot.id)
        )
        return list(result.scalars().all())

    async def close_lot(self, lot_id: str, status: str = LOT_STATUS_QUARANTINE) -> InvLot:
        """Manually move a lot to ``quarantine``, ``expired`` or ``depleted``.

        Quarantine is a hold: FEFO never picks a quarantined lot, so the stock
        it backs stays on the balance but leaves the pickable pool until the
        lot is reopened (``status="active"``). It does not touch
        ``qty_remaining`` — closing is a status decision, not a quantity one.
        """
        lot = await self.get_lot(lot_id)
        lot.status = self._validate_lot_status(status)
        await self.db.commit()
        await self.db.refresh(lot)
        return lot

    async def expire_due_lots(self, today: date | None = None) -> int:
        """Flip lots past their ``expiry_date`` to ``expired``; return how many.

        The batch counterpart to the lazy check the FEFO paths run: this one
        walks every active, expired lot in one query and commits its work (the
        service convention), so a scheduler can call it while
        :meth:`issue` / :meth:`consume_reservation` keep enforcing expiry for
        the batches nobody scheduled. Quarantined and already-expired lots are
        left exactly as they are.
        """
        cutoff = today or date.today()
        stmt = select(InvLot).where(
            InvLot.status == LOT_STATUS_ACTIVE,
            InvLot.expiry_date.is_not(None),
            InvLot.expiry_date < cutoff,
        )
        due = (await self.db.execute(stmt)).scalars().all()
        for lot in due:
            lot.status = LOT_STATUS_EXPIRED
        if due:
            await self.db.commit()
        return len(due)

    async def lot_valuation(self, sku_id: int) -> dict:
        """Read-side value of one SKU's lots: ``qty_remaining x unit_cost``.

        Cheap enough to be a read: one query over ``inv_lots`` for the SKU, no
        movement replay, because a lot carries its own cost. Complements (not
        replaces) :meth:`sku_valuation` — the warehouse-level moving average
        still values every balance row, lot-tracked or not; this reports what
        the lot ledger itself says is left, per status.
        """
        await self.get_sku_by_id(sku_id)
        lots = (
            (await self.db.execute(select(InvLot).where(InvLot.sku_id == str(sku_id))))
            .scalars()
            .all()
        )

        by_status: dict[str, dict] = {}
        total_remaining = Decimal("0")
        total_value = Decimal("0")
        for lot in lots:
            remaining = Decimal(str(lot.qty_remaining or 0))
            value = _money(remaining * _lot_unit_cost(lot))
            bucket = by_status.setdefault(
                lot.status,
                {
                    "status": lot.status,
                    "qty_remaining": Decimal("0"),
                    "value": Decimal("0"),
                },
            )
            bucket["qty_remaining"] += remaining
            bucket["value"] = _money(bucket["value"] + value)
            total_remaining += remaining
            total_value += value

        return {
            "sku_id": sku_id,
            "lots": len(lots),
            "qty_remaining": total_remaining,
            "value": _money(total_value),
            "statuses": [by_status[key] for key in sorted(by_status)],
        }

    @staticmethod
    def _validate_lot_status(status: str) -> str:
        """Validate a lot status against :data:`VALID_LOT_STATUSES`."""
        if status not in VALID_LOT_STATUSES:
            raise EcoNojinException(
                f"Invalid lot status: {status}",
                code="INVALID_LOT_STATUS",
                status_code=400,
            )
        return status

    @staticmethod
    def _normalise_lot_number(lot_number: str) -> str:
        """Trim a lot number and refuse a blank one (``INVALID_LOT_NUMBER``)."""
        number = str(lot_number).strip()
        if not number:
            raise EcoNojinException(
                "lot_number must not be blank", code="INVALID_LOT_NUMBER", status_code=400
            )
        return number

    async def _get_or_create_lot(
        self,
        *,
        sku_id: int,
        lot_number: str,
        qty: Decimal,
        unit_cost: Decimal | None = None,
        expiry_date: date | datetime | str | None = None,
        supplier_ref: str | None = None,
    ) -> InvLot:
        """Reuse the SKU's active lot with this number, or create it.

        Repeat receipts into a known lot number top up ``qty_received`` and
        ``qty_remaining`` rather than forking a second lot, so one supplier
        label is one row. The first receipt of the number defines its
        ``expiry_date`` (a later receipt only fills one in when the lot has
        none yet) and the latest priced receipt defines ``unit_cost``. Flushes
        but never commits — it runs inside its caller's transaction.
        """
        number = self._normalise_lot_number(lot_number)
        expiry = _as_date(expiry_date)

        existing = await self._active_lot_for_number(sku_id, number)
        if existing is not None:
            existing.qty_received += qty
            existing.qty_remaining += qty
            if unit_cost is not None:
                existing.unit_cost = unit_cost
            if expiry is not None and existing.expiry_date is None:
                existing.expiry_date = expiry
            await self.db.flush()
            return existing

        lot = InvLot(
            id=str(uuid4()),
            sku_id=str(sku_id),
            lot_number=number,
            expiry_date=expiry,
            received_at=datetime.now(UTC),
            unit_cost=unit_cost if unit_cost is not None else Decimal("0"),
            qty_received=qty,
            qty_remaining=qty,
            supplier_ref=supplier_ref,
            status=LOT_STATUS_ACTIVE,
            created_at=datetime.now(UTC),
        )
        self.db.add(lot)
        await self.db.flush()
        return lot

    async def _active_lot_for_number(self, sku_id: int, lot_number: str) -> InvLot | None:
        """The active lot of this SKU carrying ``lot_number``, if any.

        ``lot_number`` is unique per SKU among *active* lots: a closed
        (quarantined/expired/depleted) label can be re-registered, because the
        batch it belonged to is gone. Ordering is FEFO so a pre-existing
        duplicate (a database without the unique index the next wave adds)
        still resolves deterministically instead of raising
        ``MultipleResultsFound``.
        """
        lots = (
            (
                await self.db.execute(
                    select(InvLot).where(
                        InvLot.sku_id == str(sku_id),
                        InvLot.lot_number == lot_number,
                        InvLot.status == LOT_STATUS_ACTIVE,
                    )
                )
            )
            .scalars()
            .all()
        )
        return _fefo_sorted(lots)[0] if lots else None

    async def _lot_tracked_candidates(
        self, sku_id: int, *, allow_expired: bool = False
    ) -> tuple[list[InvLot], list[InvLot]]:
        """The lots FEFO may draw from, and the ones blocking it.

        Candidates are the SKU's **active** lots with quantity left whose
        ``expiry_date`` has not passed, FEFO-ordered. An active lot whose
        expiry has passed is flipped to ``expired`` here — the lazy
        enforcement, so the FEFO paths refuse it without waiting for
        :meth:`expire_due_lots` — and lands in the blocking list instead.
        Quarantined, already-expired and drained lots are blocking too. The
        flip is written to the caller's transaction, never committed here.

        ``allow_expired`` admits expiry-expired lots to the candidate list
        (quarantine still holds); it is what turns ``EXPIRED_LOT`` into a
        deliberate override.
        """
        today = date.today()
        lots = (
            (
                await self.db.execute(
                    select(InvLot).where(
                        InvLot.sku_id == str(sku_id), InvLot.qty_remaining > 0
                    )
                )
            )
            .scalars()
            .all()
        )

        candidates: list[InvLot] = []
        blocked: list[InvLot] = []
        for lot in lots:
            expired = _lot_is_expired(lot, today)
            if lot.status != LOT_STATUS_ACTIVE:
                # quarantine / expired / depleted is never pickable
                blocked.append(lot)
            elif expired:
                # Active but past its expiry: the lazy check records the truth,
                # and only an explicit allow_expired lets it stay pickable.
                lot.status = LOT_STATUS_EXPIRED
                (candidates if allow_expired else blocked).append(lot)
            else:
                candidates.append(lot)
        return _fefo_sorted(candidates), blocked

    async def _fefo_lot_for_reservation(self, sku_id: int, qty: Decimal) -> str | None:
        """Pick the lot a lot-tracked reservation will be consumed from.

        The earliest-expiry active lot holding the whole reserved quantity,
        falling back to the earliest-expiry active lot when no single lot
        covers it (the consumption then spans lots, as FEFO does on issue).
        Refuses with ``EXPIRED_LOT`` when the SKU's only pickable stock is
        expired; returns the balance row's own marker when the SKU has no
        active lots at all, rather than inventing one.
        """
        candidates, blocked = await self._lot_tracked_candidates(sku_id)
        if candidates:
            wanted = Decimal(str(qty))
            for lot in candidates:
                if Decimal(str(lot.qty_remaining or 0)) >= wanted:
                    return lot.id
            return candidates[0].id
        if any(lot.status == LOT_STATUS_EXPIRED for lot in blocked):
            earliest = _fefo_sorted(blocked)[0]
            raise EcoNojinException(
                f"Lot {earliest.lot_number} expired on {earliest.expiry_date}",
                code="EXPIRED_LOT",
                status_code=400,
            )
        return None

    async def _issue_from_lots(
        self,
        *,
        balance: InvInventoryBalance,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        location_id: int | None,
        reference_type: str,
        reference_id: str | None,
        created_by: str,
        allow_expired: bool,
        sorter: callable[[list[InvLot]], list[InvLot]] | None = None,
    ) -> InvStockMovement:
        """Issue ``qty`` from a lot-tracked balance row.

        ``sorter`` re-orders candidates before allocation: ``_fefo_sorted`` for
        FEFO (default), ``_fifo_sorted`` for FIFO. One movement and one
        ``ECO_COGS``/``ECO_INVENTORY`` batch per lot leg, each costed at that
        lot's ``unit_cost`` and carrying its ``lot_uuid``; ``qty_remaining``
        is decremented and a drained lot flips to ``depleted``. Returns the
        earliest leg. Does not commit -- the caller owns the transaction.
        """
        candidates, blocked = await self._lot_tracked_candidates(
            sku_id, allow_expired=allow_expired
        )
        if sorter is not None:
            candidates = sorter(candidates)
        plan, remaining = _allocate_fefo(candidates, qty)
        if remaining > 0:
            available = sum(
                (Decimal(str(lot.qty_remaining or 0)) for lot in candidates), Decimal("0")
            )
            expired = [lot for lot in blocked if lot.status == LOT_STATUS_EXPIRED]
            if expired and not allow_expired:
                earliest = _fefo_sorted(expired)[0]
                raise EcoNojinException(
                    f"Lot {earliest.lot_number} expired on {earliest.expiry_date}; "
                    f"only {available} non-expired units remain",
                    code="EXPIRED_LOT",
                    status_code=400,
                )
            raise EcoNojinException(
                f"Insufficient lot-tracked stock: {available} < {qty}",
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )

        first: InvStockMovement | None = None
        for lot, take in plan:
            lot.qty_remaining -= take
            if lot.qty_remaining <= 0:
                lot.qty_remaining = Decimal("0")
                lot.status = LOT_STATUS_DEPLETED
            balance.on_hand -= take
            balance.last_movement_at = datetime.now(UTC)

            unit_cost = _lot_unit_cost(lot)
            movement = await self._create_movement(
                "issue",
                sku_id,
                warehouse_id,
                take,
                created_by,
                from_location_id=location_id,
                reference_type=reference_type,
                reference_id=reference_id,
                unit_cost=unit_cost,
                lot_uuid=lot.id,
            )
            await self._post_value_pair(
                JOURNAL_COGS,
                str(movement.id),
                debit_code=ECO_COGS,
                credit_code=ECO_INVENTORY,
                amount=unit_cost * take,
                description=(
                    f"COGS (lot {lot.lot_number}): sku={sku_id} warehouse={warehouse_id} "
                    f"qty={take} @ {unit_cost}"
                ),
                created_by=created_by,
            )
            if first is None:
                first = movement
        assert first is not None  # plan is non-empty exactly when remaining == 0
        return first

    # ------------------------------------------------------------------
    # Reservation (atomic stock locking for orders)
    # ------------------------------------------------------------------

    async def reserve_stock(
        self,
        sku_id: int,
        warehouse_id: int,
        qty: Decimal,
        reference_type: str,
        reference_id: str,
        reference_line_id: str | None = None,
        expires_at: datetime | None = None,
        created_by: str = "system",
        location_id: int | None = None,
        lot_id: int | None = None,
    ) -> InvReservation:
        """Atomically reserve stock. Uses SELECT FOR UPDATE to prevent oversell.

        The balance row is selected — and locked with ``SELECT ... FOR
        UPDATE`` on row-locking dialects — on the full
        ``(sku, warehouse, location, lot)`` key, never on
        ``(sku, warehouse)`` alone: a pair can hold several
        location/lot-specific rows, which used to make the lock fan out
        over all of them and make ``scalar_one_or_none()`` raise
        ``MultipleResultsFound``. The caller's ``location_id``/``lot_id``
        pick the row when given; ``None`` deterministically selects the
        0-sentinel default row that ``get_or_create_balance`` maintains
        (the service's "no specific location/lot" convention), and the
        reservation record stores the same key so ``consume_reservation``
        / ``release_reservation`` lock the row it was taken from.

        On SQLite the FOR UPDATE clause is a silent no-op, so the
        cross-transaction serialization itself can only be proven on a
        row-locking backend (PostgreSQL); what SQLite tests pin is the
        row selection (exactly the one targeted row is read and
        mutated).

        Expired reservations for this (sku, warehouse) pair are swept
        first, so ``available`` never counts stock an expired
        reservation still holds.

        Lots: when the selected row is lot-tracked, the reservation records
        the FEFO lot it will be consumed from (the earliest-expiry active lot
        that holds the whole quantity, else the earliest-expiry active lot) on
        both the reservation and its audit movement, and refusing to reserve
        stock that only exists as expired lots with ``EXPIRED_LOT``. Reserving
        does not decrement ``qty_remaining`` — the quantity leaves the lot when
        it is issued/consumed, exactly as ``balance.reserved`` is only a hold
        on ``on_hand``.
        """
        await sweep_expired_reservations(self.db, sku_id=sku_id, warehouse_id=warehouse_id)

        balance = await self._lock_balance(sku_id, warehouse_id, location_id, lot_id)

        if not balance:
            raise EcoNojinException(
                f"No inventory balance for sku={sku_id}, warehouse={warehouse_id}",
                code="NO_INVENTORY",
                status_code=400,
            )

        available = balance.available
        if available < qty:
            raise EcoNojinException(
                f"Insufficient available stock: {available} < {qty}",
                code="INSUFFICIENT_AVAILABLE_STOCK",
                status_code=400,
            )

        lot_uuid = balance.lot_uuid
        if lot_uuid is not None:
            lot_uuid = await self._fefo_lot_for_reservation(sku_id, qty)

        balance.reserved += qty
        balance.last_movement_at = datetime.now(UTC)

        # Create reservation record
        reservation = InvReservation(
            sku_id=sku_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_id=lot_id,
            lot_uuid=lot_uuid,
            qty=qty,
            status="active",
            reference_type=reference_type,
            reference_id=reference_id,
            reference_line_id=reference_line_id,
            expires_at=expires_at or (datetime.now(UTC) + timedelta(hours=48)),
            consumed_qty=Decimal("0"),
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self.db.add(reservation)

        # Record movement for audit
        await self._create_movement(
            "reservation",
            sku_id,
            warehouse_id,
            qty,
            created_by,
            lot_id=balance.lot_id or None,
            lot_uuid=lot_uuid,
            reference_type=reference_type,
            reference_id=reference_id,
        )

        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def consume_reservation(
        self,
        reservation_id: int,
        qty: Decimal | None = None,
        allow_expired: bool = False,
    ) -> InvStockMovement:
        """Consume a reservation (convert to issue movement).

        Lots: a reservation taken from a lot-tracked row records the FEFO lot
        it will be consumed from, so this path costs the consumption at *that
        lot's* ``unit_cost``, carries its ``lot_uuid`` and decrements its
        ``qty_remaining`` (a drained lot flips to ``depleted``) instead of
        using the warehouse moving average. A lot whose expiry has since
        passed is refused with ``EXPIRED_LOT`` unless ``allow_expired=True``.
        A reservation taken from a non-lot-tracked row keeps the moving-average
        costing it always had.
        """
        result = await self.db.execute(
            select(InvReservation).where(InvReservation.id == reservation_id).with_for_update()
        )
        reservation = result.scalar_one_or_none()
        if not reservation:
            raise EcoNojinException(
                f"Reservation not found: {reservation_id}",
                code="RESERVATION_NOT_FOUND",
                status_code=404,
            )

        if reservation.status != "active":
            raise EcoNojinException(
                f"Reservation not active: {reservation.status}",
                code="RESERVATION_NOT_ACTIVE",
                status_code=400,
            )

        consume_qty = qty or reservation.qty
        if consume_qty > reservation.qty - reservation.consumed_qty:
            raise EcoNojinException(
                "Cannot consume more than reserved", code="OVER_CONSUME", status_code=400
            )

        # The lot is resolved (and its expiry enforced) before anything is
        # written, so a refusal leaves the balance and the reservation exactly
        # as they were.
        lot: InvLot | None = None
        if reservation.lot_uuid is not None:
            lot = await self.get_lot(reservation.lot_uuid)
            if _lot_is_expired(lot) and not allow_expired:
                raise EcoNojinException(
                    f"Lot {lot.lot_number} expired on {lot.expiry_date}",
                    code="EXPIRED_LOT",
                    status_code=400,
                )
            unit_cost = _lot_unit_cost(lot)
        else:
            unit_cost = await self._current_average_cost(
                reservation.sku_id, reservation.warehouse_id
            )

        # Lock balance and deduct
        balance = await self.get_or_create_balance(
            reservation.sku_id,
            reservation.warehouse_id,
            reservation.location_id or 0 or None,
            reservation.lot_id or None,
        )
        balance.on_hand -= consume_qty
        balance.reserved -= consume_qty
        reservation.consumed_qty += consume_qty
        balance.last_movement_at = datetime.now(UTC)

        if reservation.consumed_qty >= reservation.qty:
            reservation.status = "consumed"
            reservation.consumed_at = datetime.now(UTC)

        if lot is not None:
            lot.qty_remaining -= consume_qty
            if lot.qty_remaining <= 0:
                lot.qty_remaining = Decimal("0")
                lot.status = LOT_STATUS_DEPLETED

        # A consumed reservation leaves stock for good (the commerce ship
        # path), so it is valued and journalled exactly like a plain issue.
        movement = await self._create_movement(
            "issue",
            reservation.sku_id,
            reservation.warehouse_id,
            consume_qty,
            reservation.created_by,
            from_location_id=reservation.location_id,
            reference_type=reservation.reference_type,
            reference_id=str(reservation.reference_id),
            lot_id=reservation.lot_id,
            lot_uuid=reservation.lot_uuid,
            unit_cost=unit_cost,
        )
        await self._post_value_pair(
            JOURNAL_COGS,
            str(movement.id),
            debit_code=ECO_COGS,
            credit_code=ECO_INVENTORY,
            amount=unit_cost * consume_qty,
            description=(
                f"COGS (reservation {reservation_id}): "
                f"sku={reservation.sku_id} warehouse={reservation.warehouse_id} "
                f"qty={consume_qty} @ {unit_cost}"
            ),
            created_by=reservation.created_by,
        )

        await self.db.commit()
        await self.db.refresh(movement)
        return movement

    async def release_reservation(self, reservation_id: int) -> InvReservation:
        """Release a reservation (return stock to available)."""
        result = await self.db.execute(
            select(InvReservation).where(InvReservation.id == reservation_id).with_for_update()
        )
        reservation = result.scalar_one_or_none()
        if not reservation:
            raise EcoNojinException(
                f"Reservation not found: {reservation_id}",
                code="RESERVATION_NOT_FOUND",
                status_code=404,
            )

        if reservation.status != "active":
            raise EcoNojinException(
                f"Reservation not active: {reservation.status}",
                code="RESERVATION_NOT_ACTIVE",
                status_code=400,
            )

        balance = await self.get_or_create_balance(
            reservation.sku_id,
            reservation.warehouse_id,
            reservation.location_id or 0 or None,
            reservation.lot_id or None,
        )
        balance.reserved -= reservation.qty - reservation.consumed_qty
        balance.last_movement_at = datetime.now(UTC)

        reservation.status = "released"
        reservation.released_at = datetime.now(UTC)

        await self._create_movement(
            "release",
            reservation.sku_id,
            reservation.warehouse_id,
            reservation.qty - reservation.consumed_qty,
            reservation.created_by,
            from_location_id=reservation.location_id,
            reference_type=reservation.reference_type,
            reference_id=str(reservation.reference_id),
            lot_uuid=reservation.lot_uuid,
        )

        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    # ------------------------------------------------------------------
    # Stocktake
    # ------------------------------------------------------------------

    async def create_stocktake(
        self, warehouse_id: int, created_by: str, lines: list[dict]
    ) -> InvStocktake:
        """Create a stocktake with line items (physical count vs system)."""

        from database.models import InvStocktake, InvStocktakeLine

        stocktake = InvStocktake(
            stocktake_number=f"ST-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}",
            warehouse_id=warehouse_id,
            status="draft",
            stocktake_type="full",
            created_by=created_by,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.db.add(stocktake)
        await self.db.flush()

        for line_data in lines:
            balance = await self.get_or_create_balance(
                line_data["sku_id"],
                warehouse_id,
                line_data.get("location_id"),
                line_data.get("lot_id"),
            )

            counted_qty = Decimal(str(line_data["counted_qty"]))
            variance_qty = counted_qty - balance.on_hand
            # The count is valued at the moving-average cost of the moment, so
            # a reviewer sees what the variance is worth before approving it;
            # ``approve_stocktake`` rewrites it with the value actually booked.
            unit_cost = await self._current_average_cost(line_data["sku_id"], warehouse_id)

            stocktake_line = InvStocktakeLine(
                stocktake_id=stocktake.id,
                sku_id=line_data["sku_id"],
                warehouse_id=warehouse_id,
                location_id=line_data.get("location_id"),
                lot_id=line_data.get("lot_id"),
                system_qty=balance.on_hand,
                counted_qty=counted_qty,
                variance_qty=variance_qty,
                variance_value=_money(variance_qty * unit_cost),
                counted_by=created_by,
                counted_at=datetime.now(UTC),
                status="pending",
            )
            self.db.add(stocktake_line)

        await self.db.commit()
        await self.db.refresh(stocktake)
        return stocktake

    async def approve_stocktake(self, stocktake_id: int, approved_by: str) -> InvStocktake:
        """Approve a stocktake and create adjustment movements for variances."""
        from database.models import InvStocktake, InvStocktakeLine

        result = await self.db.execute(
            select(InvStocktake).where(InvStocktake.id == stocktake_id).with_for_update()
        )
        stocktake = result.scalar_one_or_none()
        if not stocktake:
            raise EcoNojinException(
                f"Stocktake not found: {stocktake_id}", code="STOCKTAKE_NOT_FOUND", status_code=404
            )

        if stocktake.status != "draft":
            raise EcoNojinException(
                "Stocktake not in draft status", code="STOCKTAKE_INVALID_STATUS", status_code=400
            )

        # Get all lines
        lines_result = await self.db.execute(
            select(InvStocktakeLine).where(InvStocktakeLine.stocktake_id == stocktake_id)
        )
        lines = lines_result.scalars().all()

        for line in lines:
            if line.counted_qty is None:
                # Not counted yet: it stays 'pending' for the next count
                # instead of being approved by a blanket UPDATE.
                continue
            if line.counted_qty != line.system_qty:
                variance = line.counted_qty - line.system_qty
                if variance != 0:
                    balance = await self.get_or_create_balance(
                        line.sku_id,
                        line.warehouse_id,
                        line.location_id or 0 or None,
                        line.lot_id or None,
                    )
                    new_on_hand = balance.on_hand + variance
                    if new_on_hand < Decimal("0"):
                        raise EcoNojinException(
                            "Stocktake variance would drive on_hand negative: "
                            f"{balance.on_hand} + {variance}",
                            code="NEGATIVE_ON_HAND",
                            status_code=400,
                        )
                    balance.on_hand = new_on_hand
                    balance.last_movement_at = datetime.now(UTC)

                    # Valued like any other adjustment, at the moving average
                    # of the moment the variance is approved.
                    unit_cost = await self._current_average_cost(
                        line.sku_id, line.warehouse_id
                    )
                    adjustment = await self._create_movement(
                        "adjustment",
                        line.sku_id,
                        line.warehouse_id,
                        abs(variance),
                        approved_by,
                        from_location_id=line.location_id,
                        lot_id=line.lot_id,
                        lot_uuid=balance.lot_uuid,
                        reference_type="stocktake",
                        reference_id=str(stocktake_id),
                        notes=f"Stocktake variance: {variance}",
                        unit_cost=unit_cost,
                    )
                    line.variance_value = _money(variance * unit_cost)
                    await self._post_value_pair(
                        JOURNAL_VARIANCE,
                        str(adjustment.id),
                        # Found stock adds inventory value; a shortage writes it off.
                        debit_code=(
                            ECO_INVENTORY if variance > 0 else ECO_INVENTORY_VARIANCE
                        ),
                        credit_code=(
                            ECO_INVENTORY_VARIANCE if variance > 0 else ECO_INVENTORY
                        ),
                        amount=abs(variance) * unit_cost,
                        description=(
                            f"Stocktake {stocktake_id} variance {variance}: "
                            f"sku={line.sku_id} warehouse={line.warehouse_id} "
                            f"qty={abs(variance)} @ {unit_cost}"
                        ),
                        created_by=approved_by,
                    )
            line.status = "approved"

        stocktake.status = "approved"
        stocktake.approved_by = approved_by
        stocktake.approved_at = datetime.now(UTC)
        stocktake.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(stocktake)
        return stocktake

    # ------------------------------------------------------------------
    # Valuation read API
    # ------------------------------------------------------------------

    async def sku_valuation(
        self,
        sku_id: int,
        warehouse_id: int | None = None,
        *,
        method: str = VALUATION_METHOD,
    ) -> dict:
        """Weighted-average valuation of one SKU, optionally one warehouse.

        Returns ``{"sku_id", "warehouse_id", "method", "on_hand",
        "moving_average_cost", "total_value", "warehouses"}``. ``on_hand`` is the
        live balance (the authoritative quantity this service maintains),
        ``moving_average_cost`` comes from the movement ledger
        (``_moving_average_costs``) and ``total_value`` is their product.
        Without ``warehouse_id`` the SKU is valued across every warehouse and
        the average is the value-weighted blend of the per-warehouse averages;
        ``warehouses`` always carries the per-warehouse breakdown.

        Only :data:`VALUATION_METHOD` is implemented — ``fifo``/``standard`` are
        rejected until the lot/FEFO wave lands.
        """
        await self.get_sku_by_id(sku_id)
        self._resolve_valuation_method(method)

        on_hand_stmt = select(
            InvInventoryBalance.warehouse_id, func.sum(InvInventoryBalance.on_hand)
        ).where(InvInventoryBalance.sku_id == sku_id)
        if warehouse_id is not None:
            on_hand_stmt = on_hand_stmt.where(
                InvInventoryBalance.warehouse_id == warehouse_id
            )
        on_hand_rows = (await self.db.execute(on_hand_stmt.group_by(
            InvInventoryBalance.warehouse_id
        ))).all()
        on_hand_by_warehouse = {
            int(row[0]): Decimal(str(row[1])) for row in on_hand_rows
        }

        costs = await self._moving_average_costs(sku_id)
        if warehouse_id is not None:
            costs = {warehouse_id: costs.get(warehouse_id, Decimal("0"))}

        warehouses: list[dict] = []
        total_on_hand = Decimal("0")
        total_value = Decimal("0")
        for wh in sorted(set(on_hand_by_warehouse) | set(costs)):
            on_hand = on_hand_by_warehouse.get(wh, Decimal("0"))
            unit_cost = costs.get(wh, Decimal("0"))
            value = _money(on_hand * unit_cost)
            warehouses.append(
                {
                    "warehouse_id": wh,
                    "on_hand": on_hand,
                    "moving_average_cost": unit_cost,
                    "total_value": value,
                }
            )
            total_on_hand += on_hand
            total_value += value

        return {
            "sku_id": sku_id,
            "warehouse_id": warehouse_id,
            "method": method,
            "on_hand": total_on_hand,
            "moving_average_cost": (
                _money(total_value / total_on_hand) if total_on_hand > 0 else Decimal("0")
            ),
            "total_value": _money(total_value),
            "warehouses": warehouses,
        }

    async def valuation_report(self) -> dict:
        """Aggregate the weighted-average valuation across every SKU/warehouse.

        One query over the balances and one over the movement ledger feed the
        same arithmetic as :meth:`sku_valuation`, so the report is the sum of
        the per-SKU valuations rather than a second implementation. Returns
        ``{"as_of", "method", "total_value", "skus", "warehouses"}``.
        """
        balance_rows = (
            await self.db.execute(
                select(
                    InvInventoryBalance.sku_id,
                    InvInventoryBalance.warehouse_id,
                    func.sum(InvInventoryBalance.on_hand),
                ).group_by(InvInventoryBalance.sku_id, InvInventoryBalance.warehouse_id)
            )
        ).all()
        on_hand: dict[int, dict[int, Decimal]] = {}
        for sku_id, warehouse_id, quantity in balance_rows:
            on_hand.setdefault(int(sku_id), {})[int(warehouse_id)] = Decimal(str(quantity))

        sku_rows = (
            await self.db.execute(select(InvSKU.id, InvSKU.sku_code, InvSKU.standard_cost))
        ).all()
        names = {int(row[0]): row[1] for row in sku_rows}
        standard_costs = {
            int(row[0]): (Decimal(str(row[2])) if row[2] is not None else Decimal("0"))
            for row in sku_rows
        }

        movements = (
            (
                await self.db.execute(
                    select(InvStockMovement).order_by(
                        InvStockMovement.created_at, InvStockMovement.id
                    )
                )
            )
            .scalars()
            .all()
        )
        movements_by_sku: dict[int, list[InvStockMovement]] = {}
        for movement in movements:
            movements_by_sku.setdefault(movement.sku_id, []).append(movement)

        warehouse_totals: dict[int, dict] = {}
        skus: list[dict] = []
        grand_total = Decimal("0")

        for sku_id in sorted(set(on_hand) | set(movements_by_sku)):
            costs = _average_costs_from_movements(
                movements_by_sku.get(sku_id, []), standard_costs.get(sku_id, Decimal("0"))
            )
            on_hand_by_warehouse = on_hand.get(sku_id, {})
            sku_on_hand = Decimal("0")
            sku_value = Decimal("0")
            for wh in sorted(set(on_hand_by_warehouse) | set(costs)):
                quantity = on_hand_by_warehouse.get(wh, Decimal("0"))
                unit_cost = costs.get(wh, Decimal("0"))
                value = _money(quantity * unit_cost)
                sku_on_hand += quantity
                sku_value += value
                bucket = warehouse_totals.setdefault(
                    wh,
                    {
                        "warehouse_id": wh,
                        "on_hand": Decimal("0"),
                        "moving_average_cost": Decimal("0"),
                        "total_value": Decimal("0"),
                    },
                )
                bucket["on_hand"] += quantity
                bucket["total_value"] += value
            skus.append(
                {
                    "sku_id": sku_id,
                    "sku_code": names.get(sku_id),
                    "on_hand": sku_on_hand,
                    "moving_average_cost": (
                        _money(sku_value / sku_on_hand) if sku_on_hand > 0 else Decimal("0")
                    ),
                    "total_value": _money(sku_value),
                }
            )
            grand_total += sku_value

        for bucket in warehouse_totals.values():
            bucket["moving_average_cost"] = (
                _money(bucket["total_value"] / bucket["on_hand"])
                if bucket["on_hand"] > 0
                else Decimal("0")
            )

        return {
            "as_of": datetime.now(UTC).isoformat(),
            "method": VALUATION_METHOD,
            "total_value": _money(grand_total),
            "skus": skus,
            "warehouses": [warehouse_totals[wh] for wh in sorted(warehouse_totals)],
        }

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_balance(
        self,
        sku_id: int,
        warehouse_id: int,
        location_id: int | None = None,
        lot_id: int | None = None,
    ) -> InvInventoryBalance:
        """Get current inventory balance for the (sku, warehouse, location, lot) key.

        An unspecified ``location_id``/``lot_id`` selects the 0-sentinel
        default row — the same convention ``get_or_create_balance`` and
        ``reserve_stock`` use — so the query can never match (and raise
        ``MultipleResultsFound`` on) several location or lot rows of one
        (sku, warehouse) pair. Read-only: it falls back to creating the
        missing row, as before.
        """
        result = await self.db.execute(
            select(InvInventoryBalance).where(
                InvInventoryBalance.sku_id == sku_id,
                InvInventoryBalance.warehouse_id == warehouse_id,
                InvInventoryBalance.location_id == (location_id or 0),
                InvInventoryBalance.lot_id == (lot_id or 0),
            )
        )
        balance = result.scalar_one_or_none()
        if not balance:
            balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, lot_id)
        return balance

    async def get_movements(
        self,
        sku_id: int | None = None,
        warehouse_id: int | None = None,
        movement_type: str | None = None,
        limit: int = 100,
    ) -> list[InvStockMovement]:
        stmt = select(InvStockMovement).order_by(InvStockMovement.created_at.desc())
        if sku_id:
            stmt = stmt.where(InvStockMovement.sku_id == sku_id)
        if warehouse_id:
            stmt = stmt.where(InvStockMovement.warehouse_id == warehouse_id)
        if movement_type:
            stmt = stmt.where(InvStockMovement.movement_type == movement_type)
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def reconcile_inventory(self) -> dict:
        """Reconcile inventory balances with stock movements.

        Per ``(sku_id, warehouse_id, location_id, lot_id)`` — the same key
        the unique constraint on ``inv_inventory_balances`` enforces —
        the balance's ``on_hand`` is compared against the signed movement
        ledger:

        * ``receipt``/``return``/``unblock`` add ``qty`` at the
          movement's ``warehouse_id`` and ``to_location_id``/``lot_id``;
        * ``issue``/``scrap`` subtract ``qty`` at ``warehouse_id`` and
          ``from_location_id``/``lot_id``;
        * a ``transfer`` is a single movement row stored on the source
          warehouse, so **both** legs are applied explicitly: ``-qty`` at
          ``from_warehouse_id``/``from_location_id`` and ``+qty`` at
          ``to_warehouse_id``/``to_location_id``. Counting it as inbound
          only (the previous SQL) double-counted the destination leg and
          never subtracted the source, so every transfer reported drift;
          the computed-but-unused ``transfer_out`` CTE column was
          replaced by the explicit outbound leg.
        * ``unblock`` is the mirror of ``scrap`` and is therefore an
          **inbound** leg: ``StockService.unblock_stock`` restores
          ``on_hand`` and decrements ``blocked``, and the weighted-average
          valuation prices the leg as inbound, so omitting it from this sum
          made every scrap-then-unblock report the restored quantity as
          phantom drift. ``reservation``/``release`` *do* not change
          ``on_hand`` and are correctly excluded;
        * ``adjustment`` movements store ``abs(qty)`` with the signed
          delta only in a free-text note, so they cannot be folded into
          the signed sum deterministically and are excluded (they surface
          as drift, exactly as ``ReconciliationService.reconcile_inventory``
          documents).
        """
        result = await self.db.execute(
            text(
                """
                WITH movement_flows AS (
                    SELECT
                        sku_id,
                        warehouse_id,
                        COALESCE(to_location_id, 0) AS location_id,
                        COALESCE(lot_id, 0) AS lot_id,
                        qty AS qty_in,
                        0 AS qty_out
                    FROM inv_stock_movements
                    WHERE movement_type IN ('receipt', 'return', 'unblock')
                    UNION ALL
                    SELECT
                        sku_id,
                        to_warehouse_id,
                        COALESCE(to_location_id, 0),
                        COALESCE(lot_id, 0),
                        qty,
                        0
                    FROM inv_stock_movements
                    WHERE movement_type = 'transfer' AND to_warehouse_id IS NOT NULL
                    UNION ALL
                    SELECT
                        sku_id,
                        warehouse_id,
                        COALESCE(from_location_id, 0),
                        COALESCE(lot_id, 0),
                        0,
                        qty
                    FROM inv_stock_movements
                    WHERE movement_type IN ('issue', 'scrap')
                    UNION ALL
                    SELECT
                        sku_id,
                        from_warehouse_id,
                        COALESCE(from_location_id, 0),
                        COALESCE(lot_id, 0),
                        0,
                        qty
                    FROM inv_stock_movements
                    WHERE movement_type = 'transfer' AND from_warehouse_id IS NOT NULL
                    UNION ALL
                    SELECT
                        sku_id,
                        warehouse_id,
                        COALESCE(from_location_id, 0),
                        COALESCE(lot_id, 0),
                        CASE WHEN signed_qty > 0 THEN signed_qty ELSE 0 END,
                        CASE WHEN signed_qty < 0 THEN -signed_qty ELSE 0 END
                    FROM inv_stock_movements
                    WHERE movement_type = 'adjustment' AND signed_qty IS NOT NULL
                ),
                movement_totals AS (
                    SELECT
                        sku_id,
                        warehouse_id,
                        location_id,
                        lot_id,
                        SUM(qty_in) AS qty_in,
                        SUM(qty_out) AS qty_out
                    FROM movement_flows
                    GROUP BY sku_id, warehouse_id, location_id, lot_id
                )
                SELECT
                    b.sku_id, b.warehouse_id, b.location_id, b.lot_id, b.on_hand,
                    COALESCE(m.qty_in, 0) as total_in,
                    COALESCE(m.qty_out, 0) as total_out,
                    (COALESCE(m.qty_in, 0) - COALESCE(m.qty_out, 0)) as computed_balance,
                    b.on_hand - (COALESCE(m.qty_in, 0) - COALESCE(m.qty_out, 0)) as drift
                FROM inv_inventory_balances b
                LEFT JOIN movement_totals m
                    ON b.sku_id = m.sku_id
                    AND b.warehouse_id = m.warehouse_id
                    AND b.location_id = m.location_id
                    AND b.lot_id = m.lot_id
                """
            )
        )
        rows = result.fetchall()
        discrepancies = []
        for row in rows:
            drift = Decimal(str(row.drift)) if row.drift else Decimal("0")
            if drift != 0:
                discrepancies.append(
                    {
                        "sku_id": row.sku_id,
                        "warehouse_id": row.warehouse_id,
                        "location_id": row.location_id,
                        "lot_id": row.lot_id,
                        "on_hand": str(row.on_hand),
                        "computed_balance": str(row.computed_balance),
                        "drift": str(drift),
                    }
                )

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_checked": len(rows),
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "overall_ok": len(discrepancies) == 0,
        }
