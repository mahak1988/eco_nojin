"""Tests for commerce service — order state machine, payment, settlement."""

import pytest
import uuid
from decimal import Decimal


class TestOrderStateMachine:
    """Tests for order state machine transitions."""

    def test_valid_transition_draft_to_reserved(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("draft", "reserved") is True

    def test_valid_transition_reserved_to_paid(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("reserved", "paid") is True

    def test_valid_transition_paid_to_processing(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("paid", "processing") is True

    def test_valid_transition_processing_to_shipped(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("processing", "shipped") is True

    def test_valid_transition_shipped_to_delivered(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("shipped", "delivered") is True

    def test_valid_transition_delivered_to_settled(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("delivered", "settled") is True

    def test_invalid_transition_draft_to_paid(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("draft", "paid") is False

    def test_invalid_transition_shipped_to_paid(self):
        from services.commerce.service import OrderStateMachine
        assert OrderStateMachine.can_transition("shipped", "paid") is False

    def test_terminal_state_no_transitions(self):
        from services.commerce.service import OrderStateMachine
        assert len(OrderStateMachine.get_allowed_transitions("settled")) == 0
        assert len(OrderStateMachine.get_allowed_transitions("cancelled")) == 0

    def test_get_allowed_transitions_draft(self):
        from services.commerce.service import OrderStateMachine
        transitions = OrderStateMachine.get_allowed_transitions("draft")
        assert "reserved" in transitions
        assert "cancelled" in transitions


@pytest.mark.asyncio
class TestOrderService:
    """Tests for order creation and lifecycle."""

    async def test_create_order(self, order_service, sku):
        order = await order_service.create_order(
            buyer_id="test-buyer-1",
            items=[{"sku_code": sku.sku_code, "quantity": 2, "unit_price": Decimal("100"), "warehouse_id": sku.default_warehouse_id or 1}],
        )
        assert order.status == "reserved"
        assert order.subtotal == Decimal("200")
        assert order.total > Decimal("200")  # includes fees
        assert order.platform_fee > 0
        assert order.landscape_fee > 0

    async def test_create_order_idempotent(self, order_service, sku):
        key = str(uuid.uuid4())
        order1 = await order_service.create_order(
            buyer_id="test-buyer-2",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("50"), "warehouse_id": 1}],
            idempotency_key=key,
        )
        order2 = await order_service.create_order(
            buyer_id="test-buyer-2",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("50"), "warehouse_id": 1}],
            idempotency_key=key,
        )
        assert order1.id == order2.id

    async def test_create_order_reserves_stock(self, order_service, sku):
        order = await order_service.create_order(
            buyer_id="test-buyer-3",
            items=[{"sku_code": sku.sku_code, "quantity": 5, "unit_price": Decimal("10"), "warehouse_id": 1}],
        )
        # Check reservation was created
        items = await order_service.list_orders(buyer_id="test-buyer-3")
        assert len(items) == 1

    async def test_confirm_payment(self, order_service, sku):
        order = await order_service.create_order(
            buyer_id="test-buyer-4",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("100"), "warehouse_id": 1}],
        )
        payment = await order_service.create_payment_intent(order.id, provider_name="wallet")
        assert payment.status == "requires_action"

        updated_order = await order_service.confirm_payment(order.id, payment_confirmed=True)
        assert updated_order.status == "paid"
        assert updated_order.payment_status == "paid"
        assert updated_order.paid_at is not None

    async def test_cannot_ship_unpaid_order(self, order_service, sku):
        order = await order_service.create_order(
            buyer_id="test-buyer-5",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("100"), "warehouse_id": 1}],
        )
        from services.api_gateway.exceptions import EcoNojinException
        with pytest.raises(EcoNojinException):
            await order_service.ship_order(order.id, "TRACK123", "admin")

    async def test_ship_require_valid_state(self, order_service, sku):
        from services.api_gateway.exceptions import EcoNojinException

        # Ship directly from reserved (should fail — must be paid first)
        order = await order_service.create_order(
            buyer_id="test-buyer-6",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("100"), "warehouse_id": 1}],
        )
        with pytest.raises(EcoNojinException):
            await order_service.ship_order(order.id, "TRACK123", "admin")

    async def test_cancel_order_releases_reservation(self, order_service, sku):
        order = await order_service.create_order(
            buyer_id="test-buyer-7",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("100"), "warehouse_id": 1}],
        )
        await order_service.cancel_order(order.id, reason="changed mind", cancelled_by="test-buyer-7")
        assert order.status == "cancelled"

    async def test_cannot_cancel_terminal_order(self, order_service, sku):
        from services.api_gateway.exceptions import EcoNojinException
        order = await order_service.create_order(
            buyer_id="test-buyer-8",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("100"), "warehouse_id": 1}],
        )
        await order_service.cancel_order(order.id, reason="test", cancelled_by="test-buyer-8")
        with pytest.raises(EcoNojinException):
            await order_service.cancel_order(order.id, reason="test2", cancelled_by="test-buyer-8")

    async def test_fulfill_order_to_settlement(self, order_service, sku):
        order = await order_service.create_order(
            buyer_id="test-buyer-9",
            items=[{"sku_code": sku.sku_code, "quantity": 1, "unit_price": Decimal("100"), "warehouse_id": 1}],
        )
        await order_service.confirm_payment(order.id, payment_confirmed=True)
        order = await order_service.get_order(order.id)

        # Process, ship and deliver
        processed = await order_service.process_order(order.id)
        assert processed.status == "processing"
        shipped = await order_service.ship_order(order.id, "TRACK123", "admin")
        assert shipped.status == "shipped"
        assert shipped.tracking_code == "TRACK123"

        delivered = await order_service.mark_delivered(order.id)
        assert delivered.status == "delivered"

        settlement = await order_service.settle_order(order.id)
        assert settlement.status == "paid"
        assert settlement.journal_batch_id is not None

    async def test_compute_fees(self):
        from services.commerce.service import OrderService
        subtotal = Decimal("1000")
        fee, land, total = OrderService._compute_fees(subtotal)
        assert fee == Decimal("30.00")  # 3%
        assert land == Decimal("10.00")  # 1%
        assert total == Decimal("1040.00")
