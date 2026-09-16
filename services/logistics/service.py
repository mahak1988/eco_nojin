"""Logistics service — shipment lifecycle: pending → picked_up → in_transit → delivered/failed."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Shipment, ShipmentEvent

VALID_TRANSITIONS = {
    'pending': {'picked_up', 'failed'},
    'picked_up': {'in_transit', 'failed'},
    'in_transit': {'delivered', 'failed'},
    'delivered': set(),
    'failed': set(),
}


class LogisticsService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, order_id: str, carrier: str = 'post', origin: str = '',
               destination: str = '') -> Shipment:
        if carrier not in ('post', 'tipax', 'local_courier', 'pickup'):
            raise ValueError(f'unknown carrier: {carrier}')
        sh = Shipment(order_id=order_id, carrier=carrier, origin=origin, destination=destination)
        self.db.add(sh)
        self.db.commit()
        self.db.refresh(sh)
        self.db.add(ShipmentEvent(shipment_id=sh.id, status='pending', note='created'))
        self.db.commit()
        return sh

    def get(self, shipment_id: str) -> Shipment:
        sh = self.db.get(Shipment, shipment_id)
        if sh is None:
            raise LookupError(f'shipment not found: {shipment_id}')
        return sh

    def by_order(self, order_id: str) -> list[Shipment]:
        stmt = select(Shipment).where(Shipment.order_id == order_id)
        return list(self.db.execute(stmt).scalars().all())

    def update_status(self, shipment_id: str, new_status: str, actor: str = '',
                      note: str | None = None) -> Shipment:
        sh = self.get(shipment_id)
        allowed = VALID_TRANSITIONS.get(sh.status, set())
        if new_status not in allowed:
            raise ValueError(f'illegal transition {sh.status} -> {new_status}')
        sh.status = new_status
        self.db.add(ShipmentEvent(shipment_id=sh.id, status=new_status, actor=actor, note=note))
        self.db.commit()
        return sh

    def events(self, shipment_id: str) -> list[ShipmentEvent]:
        stmt = select(ShipmentEvent).where(ShipmentEvent.shipment_id == shipment_id).order_by(ShipmentEvent.created_at)
        return list(self.db.execute(stmt).scalars().all())
