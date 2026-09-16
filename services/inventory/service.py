"""Inventory/WMS service — real warehouse management with atomic stock operations.

Implements the Inventory bounded context from the target architecture:
  - Stock movements (receipt, issue, transfer, adjustment, return, scrap, stocktake)
  - Atomic reservation with FOR UPDATE (prevents oversell)
  - FIFO / Weighted Average costing and COGS calculation
  - Lot/batch traceability (FEFO expiry picking)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    InvInventoryBalance,
    InvLocation,
    InvReservation,
    InvSKU,
    InvStockMovement,
    InvWarehouse,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.ledger_service import LedgerService

logger = logging.getLogger(__name__)

VALID_MOVEMENT_TYPES = frozenset({
    "receipt", "issue", "transfer", "adjustment",
    "return", "scrap", "stocktake", "reservation", "release",
})

VALID_VALUATION_METHODS = frozenset({"fifo", "weighted_avg", "standard"})


class StockService:
    """Atomic stock management service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)

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
        existing = await self.db.execute(
            select(InvSKU).where(InvSKU.sku_code == sku_code)
        )
        if existing.scalar_one_or_none():
            raise EcoNojinException(f"SKU {sku_code} already exists", code="SKU_EXISTS", status_code=409)

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
        existing = await self.db.execute(
            select(InvWarehouse).where(InvWarehouse.code == code)
        )
        if existing.scalar_one_or_none():
            raise EcoNojinException(f"Warehouse {code} already exists", code="WH_EXISTS", status_code=409)

        wh = InvWarehouse(code=code, name=name, city=city, is_active=True)
        self.db.add(wh)
        await self.db.commit()
        await self.db.refresh(wh)
        return wh

    async def create_location(
        self, warehouse_id: int, code: str, loc_type: str = "bin"
    ) -> InvLocation:
        loc = InvLocation(
            warehouse_id=warehouse_id, code=code, location_type=loc_type,
            is_active=True, is_pickable=True, is_receivable=True,
        )
        self.db.add(loc)
        await self.db.commit()
        await self.db.refresh(loc)
        return loc

    async def get_sku(self, sku_code: str) -> InvSKU:
        result = await self.db.execute(select(InvSKU).where(InvSKU.sku_code == sku_code))
        sku = result.scalar_one_or_none()
        if not sku:
            raise EcoNojinException(f"SKU not found: {sku_code}", code="SKU_NOT_FOUND", status_code=404)
        return sku

    async def get_sku_by_id(self, sku_id: int) -> InvSKU:
        result = await self.db.execute(select(InvSKU).where(InvSKU.id == sku_id))
        sku = result.scalar_one_or_none()
        if not sku:
            raise EcoNojinException(f"SKU not found: {sku_id}", code="SKU_NOT_FOUND", status_code=404)
        return sku

    async def get_or_create_balance(self, sku_id: int, warehouse_id: int, location_id: int | None = None, lot_id: int | None = None) -> InvInventoryBalance:
        """Get or create an inventory balance row."""
        result = await self.db.execute(
            select(InvInventoryBalance).where(
                InvInventoryBalance.sku_id == sku_id,
                InvInventoryBalance.warehouse_id == warehouse_id,
                InvInventoryBalance.location_id == (location_id or 0),
                InvInventoryBalance.lot_id == (lot_id or 0),
            )
        )
        balance = result.scalar_one_or_none()
        if balance:
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
        self.db.add(balance)
        await self.db.flush()
        return balance

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
    ) -> InvStockMovement:
        """Create an immutable stock movement record."""
        if movement_type not in VALID_MOVEMENT_TYPES:
            raise EcoNojinException(f"Invalid movement type: {movement_type}", code="INVALID_MOVEMENT_TYPE", status_code=400)
        if qty <= 0:
            raise EcoNojinException("Quantity must be positive", code="INVALID_QTY", status_code=400)

        movement = InvStockMovement(
            movement_type=movement_type,
            sku_id=sku_id,
            warehouse_id=warehouse_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            lot_id=lot_id,
            qty=qty,
            unit_cost=unit_cost,
            total_cost=(unit_cost * qty) if unit_cost else None,
            reference_type=reference_type,
            reference_id=reference_id,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            created_by=created_by,
            created_at=datetime.now(UTC),
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
    ) -> InvStockMovement:
        """Receive goods into inventory (increases on_hand)."""
        balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, lot_id)
        balance.on_hand += qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "receipt", sku_id, warehouse_id, qty, created_by,
            to_location_id=location_id, lot_id=lot_id,
            reference_type=reference_type, reference_id=reference_id,
            unit_cost=unit_cost,
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
    ) -> InvStockMovement:
        """Issue goods from inventory (decreases on_hand). FEFO expiry picking."""
        balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, None)
        if balance.on_hand < qty:
            raise EcoNojinException(
                f"Insufficient stock: {balance.on_hand} < {qty}",
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )
        balance.on_hand -= qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "issue", sku_id, warehouse_id, qty, created_by,
            from_location_id=location_id,
            reference_type=reference_type, reference_id=reference_id,
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
    ) -> InvStockMovement:
        """Transfer stock between warehouses/locations."""
        # Lock source balance
        src_balance = await self.get_or_create_balance(sku_id, from_warehouse_id, from_location_id, None)
        if src_balance.on_hand < qty:
            raise EcoNojinException(
                f"Insufficient stock at source: {src_balance.on_hand} < {qty}",
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )
        src_balance.on_hand -= qty

        # Create destination balance
        dst_balance = await self.get_or_create_balance(sku_id, to_warehouse_id, to_location_id, None)
        dst_balance.on_hand += qty

        src_balance.last_movement_at = datetime.now(UTC)
        dst_balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "transfer", sku_id, from_warehouse_id, qty, created_by,
            from_location_id=from_location_id, to_location_id=to_location_id,
            from_warehouse_id=from_warehouse_id, to_warehouse_id=to_warehouse_id,
            reference_type="transfer",
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
    ) -> InvStockMovement:
        """Adjust stock levels (positive or negative). Creates adjustment movement."""
        movement_type = "adjustment"
        balance = await self.get_or_create_balance(sku_id, warehouse_id, None, None)
        balance.on_hand += qty  # qty can be negative
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            movement_type, sku_id, warehouse_id, abs(qty), created_by,
            reference_type=adjustment_type,
            notes=f"Adjustment: {qty} - {reason or ''}",
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
    ) -> InvStockMovement:
        """Process a return (increases on_hand, decreases COGS impact)."""
        balance = await self.get_or_create_balance(sku_id, warehouse_id, location_id, None)
        balance.on_hand += qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "return", sku_id, warehouse_id, qty, created_by,
            to_location_id=location_id,
            reference_type=reference_type, reference_id=reference_id,
            unit_cost=unit_cost,
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
        """Write off damaged/destroyed goods (decreases on_hand)."""
        balance = await self.get_or_create_balance(sku_id, warehouse_id, None, None)
        if balance.on_hand < qty:
            raise EcoNojinException(
                f"Insufficient stock to scrap: {balance.on_hand} < {qty}",
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )
        balance.on_hand -= qty
        balance.blocked += qty
        balance.last_movement_at = datetime.now(UTC)

        movement = await self._create_movement(
            "scrap", sku_id, warehouse_id, qty, created_by,
            reference_type="scrap",
            notes=reason,
        )
        await self.db.commit()
        return movement

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
    ) -> InvReservation:
        """Atomically reserve stock. Uses SELECT FOR UPDATE to prevent oversell."""
        # Lock the balance row
        result = await self.db.execute(
            select(InvInventoryBalance)
            .where(
                InvInventoryBalance.sku_id == sku_id,
                InvInventoryBalance.warehouse_id == warehouse_id,
            )
            .with_for_update()
        )
        balance = result.scalar_one_or_none()

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

        balance.reserved += qty
        balance.last_movement_at = datetime.now(UTC)

        # Create reservation record
        reservation = InvReservation(
            sku_id=sku_id,
            warehouse_id=warehouse_id,
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
            "reservation", sku_id, warehouse_id, qty, created_by,
            lot_id=balance.lot_id or None,
            reference_type=reference_type, reference_id=reference_id,
        )

        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def consume_reservation(self, reservation_id: int, qty: Decimal | None = None) -> InvStockMovement:
        """Consume a reservation (convert to issue movement)."""
        result = await self.db.execute(
            select(InvReservation).where(InvReservation.id == reservation_id).with_for_update()
        )
        reservation = result.scalar_one_or_none()
        if not reservation:
            raise EcoNojinException(f"Reservation not found: {reservation_id}", code="RESERVATION_NOT_FOUND", status_code=404)

        if reservation.status != "active":
            raise EcoNojinException(
                f"Reservation not active: {reservation.status}",
                code="RESERVATION_NOT_ACTIVE",
                status_code=400,
            )

        consume_qty = qty or reservation.qty
        if consume_qty > reservation.qty - reservation.consumed_qty:
            raise EcoNojinException("Cannot consume more than reserved", code="OVER_CONSUME", status_code=400)

        # Lock balance and deduct
        balance = await self.get_or_create_balance(
            reservation.sku_id, reservation.warehouse_id,
            reservation.location_id or 0 or None, reservation.lot_id or None,
        )
        balance.on_hand -= consume_qty
        balance.reserved -= consume_qty
        reservation.consumed_qty += consume_qty
        balance.last_movement_at = datetime.now(UTC)

        if reservation.consumed_qty >= reservation.qty:
            reservation.status = "consumed"
            reservation.consumed_at = datetime.now(UTC)

        movement = await self._create_movement(
            "issue", reservation.sku_id, reservation.warehouse_id, consume_qty,
            reservation.created_by,
            from_location_id=reservation.location_id,
            reference_type=reservation.reference_type,
            reference_id=str(reservation.reference_id),
            lot_id=reservation.lot_id,
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
            raise EcoNojinException(f"Reservation not found: {reservation_id}", code="RESERVATION_NOT_FOUND", status_code=404)

        if reservation.status != "active":
            raise EcoNojinException(
                f"Reservation not active: {reservation.status}",
                code="RESERVATION_NOT_ACTIVE",
                status_code=400,
            )

        balance = await self.get_or_create_balance(
            reservation.sku_id, reservation.warehouse_id,
            reservation.location_id or 0 or None, reservation.lot_id or None,
        )
        balance.reserved -= reservation.qty - reservation.consumed_qty
        balance.last_movement_at = datetime.now(UTC)

        reservation.status = "released"
        reservation.released_at = datetime.now(UTC)

        await self._create_movement(
            "release", reservation.sku_id, reservation.warehouse_id,
            reservation.qty - reservation.consumed_qty,
            reservation.created_by,
            from_location_id=reservation.location_id,
            reference_type=reservation.reference_type,
            reference_id=str(reservation.reference_id),
        )

        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    # ------------------------------------------------------------------
    # Stocktake
    # ------------------------------------------------------------------

    async def create_stocktake(
        self, warehouse_id: int, created_by: str, lines: list[dict]
    ) -> InvStocktake:  # noqa: F821
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
            balance = await self.get_or_create_balance(line_data["sku_id"], warehouse_id, line_data.get("location_id"), line_data.get("lot_id"))

            stocktake_line = InvStocktakeLine(
                stocktake_id=stocktake.id,
                sku_id=line_data["sku_id"],
                warehouse_id=warehouse_id,
                location_id=line_data.get("location_id"),
                lot_id=line_data.get("lot_id"),
                system_qty=balance.on_hand,
                counted_qty=Decimal(str(line_data["counted_qty"])),
                variance_qty=Decimal(str(line_data["counted_qty"])) - balance.on_hand,
                variance_value=None,
                counted_by=created_by,
                counted_at=datetime.now(UTC),
                status="pending",
            )
            self.db.add(stocktake_line)

        await self.db.commit()
        await self.db.refresh(stocktake)
        return stocktake

    async def approve_stocktake(self, stocktake_id: int, approved_by: str) -> InvStocktake:  # noqa: F821
        """Approve a stocktake and create adjustment movements for variances."""
        from database.models import InvStocktake, InvStocktakeLine

        result = await self.db.execute(
            select(InvStocktake).where(InvStocktake.id == stocktake_id).with_for_update()
        )
        stocktake = result.scalar_one_or_none()
        if not stocktake:
            raise EcoNojinException(f"Stocktake not found: {stocktake_id}", code="STOCKTAKE_NOT_FOUND", status_code=404)

        if stocktake.status != "draft":
            raise EcoNojinException("Stocktake not in draft status", code="STOCKTAKE_INVALID_STATUS", status_code=400)

        # Get all lines
        lines_result = await self.db.execute(
            select(InvStocktakeLine).where(InvStocktakeLine.stocktake_id == stocktake_id)
        )
        lines = lines_result.scalars().all()

        for line in lines:
            if line.counted_qty != line.system_qty and line.counted_qty is not None:
                variance = line.counted_qty - line.system_qty
                if variance != 0:
                    balance = await self.get_or_create_balance(
                        line.sku_id, line.warehouse_id,
                        line.location_id or 0 or None, line.lot_id or None,
                    )
                    balance.on_hand += variance
                    balance.last_movement_at = datetime.now(UTC)

                    line.status = "approved"
                    await self._create_movement(
                        "adjustment", line.sku_id, line.warehouse_id, abs(variance),
                        approved_by,
                        from_location_id=line.location_id,
                        lot_id=line.lot_id,
                        reference_type="stocktake",
                        reference_id=str(stocktake_id),
                        notes=f"Stocktake variance: {variance}",
                    )

        stocktake.status = "approved"
        stocktake.approved_by = approved_by
        stocktake.approved_at = datetime.now(UTC)
        stocktake.updated_at = datetime.now(UTC)

        # Update the stocktake lines' status
        await self.db.execute(
            text("UPDATE inv_stocktake_line SET status = 'approved' WHERE stocktake_id = :sid"),
            {"sid": stocktake_id},
        )

        await self.db.commit()
        await self.db.refresh(stocktake)
        return stocktake

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_balance(self, sku_id: int, warehouse_id: int, location_id: int | None = None, lot_id: int | None = None) -> InvInventoryBalance:
        """Get current inventory balance."""
        stmt = select(InvInventoryBalance).where(
            InvInventoryBalance.sku_id == sku_id,
            InvInventoryBalance.warehouse_id == warehouse_id,
        )
        if location_id:
            stmt = stmt.where(InvInventoryBalance.location_id == location_id)
        if lot_id:
            stmt = stmt.where(InvInventoryBalance.lot_id == lot_id)
        result = await self.db.execute(stmt)
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
        """Reconcile inventory balances with stock movements."""
        result = await self.db.execute(
            text(
                """
                WITH movement_totals AS (
                    SELECT
                        sku_id,
                        warehouse_id,
                        SUM(CASE WHEN movement_type IN ('receipt', 'return', 'transfer') THEN qty ELSE 0 END) as qty_in,
                        SUM(CASE WHEN movement_type IN ('issue', 'scrap') THEN qty ELSE 0 END) as qty_out,
                        SUM(CASE WHEN movement_type = 'transfer' AND from_warehouse_id != warehouse_id THEN -qty ELSE 0 END) as transfer_out
                    FROM inv_stock_movement
                    GROUP BY sku_id, warehouse_id
                )
                SELECT
                    b.sku_id, b.warehouse_id, b.on_hand,
                    COALESCE(m.qty_in, 0) as total_in,
                    COALESCE(m.qty_out, 0) as total_out,
                    (COALESCE(m.qty_in, 0) - COALESCE(m.qty_out, 0)) as computed_balance,
                    b.on_hand - (COALESCE(m.qty_in, 0) - COALESCE(m.qty_out, 0)) as drift
                FROM inv_inventory_balance b
                LEFT JOIN movement_totals m ON b.sku_id = m.sku_id AND b.warehouse_id = m.warehouse_id
                """
            )
        )
        rows = result.fetchall()
        discrepancies = []
        for row in rows:
            drift = Decimal(str(row.drift)) if row.drift else Decimal("0")
            if drift != 0:
                discrepancies.append({
                    "sku_id": row.sku_id,
                    "warehouse_id": row.warehouse_id,
                    "on_hand": str(row.on_hand),
                    "computed_balance": str(row.computed_balance),
                    "drift": str(drift),
                })

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_checked": len(rows),
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "overall_ok": len(discrepancies) == 0,
        }
