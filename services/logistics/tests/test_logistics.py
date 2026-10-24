"""Tests for the logistics shipment lifecycle.

The state machine is the contract:

``pending -> picked_up -> in_transit -> delivered`` (or ``failed`` from any
open state), and a terminal state accepts no further transition.
"""

import pytest

from services.logistics.service import VALID_TRANSITIONS, LogisticsService


@pytest.fixture
def service(sync_db_session):
    return LogisticsService(sync_db_session)


class TestShipmentCreation:
    """Tests for creating a shipment."""

    def test_a_shipment_is_created_pending(self, service):
        ship = service.create("order-1", carrier="post", origin="A", destination="B")
        assert ship.order_id == "order-1"
        assert ship.status == "pending"
        assert ship.carrier == "post"

    def test_the_creation_is_evented(self, service):
        ship = service.create("order-1")
        events = service.events(ship.id)
        assert len(events) == 1
        assert events[0].status == "pending"

    def test_every_known_carrier_is_accepted(self, service):
        for carrier in ("post", "tipax", "local_courier", "pickup"):
            ship = service.create("order-1", carrier=carrier)
            assert ship.carrier == carrier

    def test_an_unknown_carrier_is_refused(self, service):
        with pytest.raises(ValueError, match="unknown carrier"):
            service.create("order-1", carrier="teleport")

    def test_a_missing_shipment_raises(self, service):
        with pytest.raises(LookupError):
            service.get("no-such-shipment")


class TestStatusTransitions:
    """Tests for the state machine."""

    def test_the_happy_path_walks_the_chain(self, service):
        ship = service.create("order-1")
        for status in ("picked_up", "in_transit", "delivered"):
            ship = service.update_status(ship.id, status)
            assert ship.status == status

    def test_every_transition_is_evented(self, service):
        ship = service.create("order-1")
        service.update_status(ship.id, "picked_up", actor="carrier-1")
        service.update_status(ship.id, "in_transit", actor="carrier-1")
        statuses = [e.status for e in service.events(ship.id)]
        assert statuses == ["pending", "picked_up", "in_transit"]

    def test_a_shipment_can_fail_from_any_open_state(self, service):
        for start, target in (
            ("pending", "failed"),
            ("picked_up", "failed"),
            ("in_transit", "failed"),
        ):
            ship = service.create("order-1")
            for step in VALID_TRANSITIONS[start]:
                if step == "failed":
                    break
                ship = service.update_status(ship.id, step)
            ship = service.update_status(ship.id, target)
            assert ship.status == "failed"

    def test_a_delivered_shipment_is_terminal(self, service):
        ship = service.create("order-1")
        for status in ("picked_up", "in_transit", "delivered"):
            ship = service.update_status(ship.id, status)
        with pytest.raises(ValueError, match="illegal transition"):
            service.update_status(ship.id, "in_transit")

    def test_a_failed_shipment_is_terminal(self, service):
        ship = service.create("order-1")
        service.update_status(ship.id, "failed")
        with pytest.raises(ValueError, match="illegal transition"):
            service.update_status(ship.id, "picked_up")

    def test_skipping_a_state_is_refused(self, service):
        ship = service.create("order-1")
        with pytest.raises(ValueError, match="illegal transition"):
            service.update_status(ship.id, "delivered")

    def test_an_unknown_status_is_refused(self, service):
        ship = service.create("order-1")
        with pytest.raises(ValueError, match="illegal transition"):
            service.update_status(ship.id, "teleported")

    def test_the_event_records_the_actor_and_note(self, service):
        ship = service.create("order-1")
        service.update_status(ship.id, "picked_up", actor="carrier-1", note="collected")
        last = service.events(ship.id)[-1]
        assert last.actor == "carrier-1"
        assert last.note == "collected"


class TestListing:
    """Tests for the listing helpers."""

    def test_shipments_are_listed_by_order(self, service):
        service.create("order-1")
        service.create("order-2")
        service.create("order-1")
        assert len(service.by_order("order-1")) == 2
        assert len(service.by_order("order-2")) == 1

    def test_an_order_without_shipments_lists_nothing(self, service):
        assert service.by_order("order-nothing") == []
