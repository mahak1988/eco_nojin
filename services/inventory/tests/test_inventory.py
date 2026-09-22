"""Tests for inventory service — atomic stock operations, reservations, stocktakes."""

from decimal import Decimal

import pytest

from services.api_gateway.exceptions import EcoNojinException

pytestmark = pytest.mark.asyncio


class TestStockService:
    """Tests for atomic stock operations."""

    async def test_create_sku(self, stock_service):
        sku = await stock_service.create_sku(
            "TEST-SKU-001", "Test Product", uom="kg", standard_cost=Decimal("10")
        )
        assert sku.sku_code == "TEST-SKU-001"

    async def test_create_duplicate_sku_fails(self, stock_service):
        await stock_service.create_sku("TEST-SKU-002", "Product A")
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.create_sku("TEST-SKU-002", "Product B")
        assert exc_info.value.code == "SKU_EXISTS"

    async def test_create_warehouse(self, stock_service):
        wh = await stock_service.create_warehouse("WH-001", "Test Warehouse", city="Tehran")
        assert wh.code == "WH-001"

    async def test_receipt_increases_stock(self, stock_service, sku):
        movement = await stock_service.receipt(
            sku_id=sku.id,
            warehouse_id=stock_service._default_wh.id,
            qty=Decimal("100"),
            created_by="test-user",
        )
        assert movement.movement_type == "receipt"
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("100")

    async def test_issue_decreases_stock(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("100"), created_by="test-user"
        )
        movement = await stock_service.issue(
            sku.id, stock_service._default_wh.id, Decimal("30"), created_by="test-user"
        )
        assert movement.movement_type == "issue"
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("70")

    async def test_issue_insufficient_stock_fails(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("10"), created_by="test-user"
        )
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.issue(
                sku.id, stock_service._default_wh.id, Decimal("50"), created_by="test-user"
            )
        assert exc_info.value.code == "INSUFFICIENT_STOCK"

    async def test_transfer_stock(self, stock_service, sku):
        wh2 = await stock_service.create_warehouse("WH-002", "Second Warehouse")
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("100"), created_by="test-user"
        )
        movement = await stock_service.transfer(
            sku.id, stock_service._default_wh.id, wh2.id, Decimal("40"), created_by="test-user"
        )
        assert movement.movement_type == "transfer"
        src_balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        dst_balance = await stock_service.get_balance(sku.id, wh2.id)
        assert src_balance.on_hand == Decimal("60")
        assert dst_balance.on_hand == Decimal("40")

    async def test_adjust_stock(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("50"), created_by="test-user"
        )
        await stock_service.adjust(
            sku.id,
            stock_service._default_wh.id,
            Decimal("-5"),
            reason="damaged",
            created_by="admin",
        )
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("45")

    async def test_scrap_reduces_stock(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("50"), created_by="test-user"
        )
        await stock_service.scrap(
            sku.id,
            stock_service._default_wh.id,
            Decimal("10"),
            reason="damaged",
            created_by="admin",
        )
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("40")

    async def test_return_increases_stock(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("50"), created_by="test-user"
        )
        await stock_service.issue(
            sku.id, stock_service._default_wh.id, Decimal("20"), created_by="test-user"
        )
        await stock_service.return_goods(
            sku.id, stock_service._default_wh.id, Decimal("10"), created_by="test-user"
        )
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("40")

    async def test_reservation_blocks_stock(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("100"), created_by="test-user"
        )
        reservation = await stock_service.reserve_stock(
            sku_id=sku.id,
            warehouse_id=stock_service._default_wh.id,
            qty=Decimal("50"),
            reference_type="order",
            reference_id="order-1",
            created_by="test-user",
        )
        assert reservation.status == "active"
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("100")
        assert balance.reserved == Decimal("50")
        assert balance.available == Decimal("50")

    async def test_reservation_insufficient_available_fails(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("30"), created_by="test-user"
        )
        await stock_service.reserve_stock(
            sku_id=sku.id,
            warehouse_id=stock_service._default_wh.id,
            qty=Decimal("20"),
            reference_type="order",
            reference_id="order-1",
            created_by="test-user",
        )
        with pytest.raises(EcoNojinException) as exc_info:
            await stock_service.reserve_stock(
                sku_id=sku.id,
                warehouse_id=stock_service._default_wh.id,
                qty=Decimal("50"),
                reference_type="order",
                reference_id="order-2",
                created_by="test-user",
            )
        assert exc_info.value.code == "INSUFFICIENT_AVAILABLE_STOCK"

    async def test_release_reservation(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("100"), created_by="test-user"
        )
        reservation = await stock_service.reserve_stock(
            sku_id=sku.id,
            warehouse_id=stock_service._default_wh.id,
            qty=Decimal("50"),
            reference_type="order",
            reference_id="order-1",
            created_by="test-user",
        )
        await stock_service.release_reservation(reservation.id)
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.reserved == Decimal("0")
        assert balance.available == Decimal("100")

    async def test_consume_reservation(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("100"), created_by="test-user"
        )
        reservation = await stock_service.reserve_stock(
            sku_id=sku.id,
            warehouse_id=stock_service._default_wh.id,
            qty=Decimal("50"),
            reference_type="order",
            reference_id="order-1",
            created_by="test-user",
        )
        await stock_service.consume_reservation(reservation.id)
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("50")
        assert balance.reserved == Decimal("0")

    async def test_stocktake_creates_adjustments(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("100"), created_by="test-user"
        )
        stocktake = await stock_service.create_stocktake(
            warehouse_id=stock_service._default_wh.id,
            created_by="admin",
            lines=[{"sku_id": sku.id, "counted_qty": Decimal("95")}],
        )
        await stock_service.approve_stocktake(stocktake.id, "admin")
        balance = await stock_service.get_balance(sku.id, stock_service._default_wh.id)
        assert balance.on_hand == Decimal("95")

    async def test_reconcile_inventory_ok(self, stock_service, sku):
        await stock_service.receipt(
            sku.id, stock_service._default_wh.id, Decimal("100"), created_by="test-user"
        )
        result = await stock_service.reconcile_inventory()
        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0
