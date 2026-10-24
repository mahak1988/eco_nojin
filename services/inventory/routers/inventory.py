"""Inventory/WMS router — stock operations, reservations, lots and valuation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import InvLot, InvSKU, InvWarehouse
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.exceptions import EcoNojinException
from services.inventory.service import StockService

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _uid(user) -> str:
    return str(user.id) if hasattr(user, "id") else str(user.get("id"))


def _lot_json(lot: InvLot) -> dict:
    """One lot as a JSON-safe dict (Decimals as strings, dates ISO)."""
    return {
        "id": lot.id,
        "sku_id": lot.sku_id,
        "lot_number": lot.lot_number,
        "expiry_date": lot.expiry_date.isoformat() if lot.expiry_date else None,
        "received_at": lot.received_at.isoformat() if lot.received_at else None,
        "unit_cost": str(lot.unit_cost),
        "qty_received": str(lot.qty_received),
        "qty_remaining": str(lot.qty_remaining),
        "supplier_ref": lot.supplier_ref,
        "status": lot.status,
        "created_at": lot.created_at.isoformat() if lot.created_at else None,
    }


def _money_json(value):
    """Recursively render Decimals as strings so no precision is lost in JSON."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, list):
        return [_money_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _money_json(item) for key, item in value.items()}
    return value


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class SKUCreate(BaseModel):
    sku_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    uom: str = "kg"
    category_id: int | None = None
    standard_cost: Decimal | None = None
    warehouse_id: int | None = None


class WarehouseCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    city: str | None = None


class LocationCreate(BaseModel):
    warehouse_id: int
    code: str = Field(..., min_length=1, max_length=20)
    location_type: str = "bin"


class ReceiptRequest(BaseModel):
    sku_code: str
    warehouse_id: int
    qty: Decimal = Field(..., gt=0)
    location_id: int | None = None
    lot_id: int | None = None
    lot_number: str | None = Field(default=None, max_length=100)
    expiry_date: date | None = None
    unit_cost: Decimal | None = None
    reference_id: str | None = None


class IssueRequest(BaseModel):
    sku_code: str
    warehouse_id: int
    qty: Decimal = Field(..., gt=0)
    location_id: int | None = None
    reference_id: str | None = None


class TransferRequest(BaseModel):
    sku_code: str
    from_warehouse_id: int
    to_warehouse_id: int
    qty: Decimal = Field(..., gt=0)
    from_location_id: int | None = None
    to_location_id: int | None = None


class AdjustRequest(BaseModel):
    sku_code: str
    warehouse_id: int
    qty: Decimal = Field(..., description="Signed adjustment (+ or -)")
    reason: str | None = None


class ReturnRequest(BaseModel):
    sku_code: str
    warehouse_id: int
    qty: Decimal = Field(..., gt=0)
    location_id: int | None = None
    reference_id: str | None = None
    unit_cost: Decimal | None = None


class ScrapRequest(BaseModel):
    sku_code: str
    warehouse_id: int
    qty: Decimal = Field(..., gt=0)
    reason: str | None = None


class ReservationRequest(BaseModel):
    sku_code: str
    warehouse_id: int
    qty: Decimal = Field(..., gt=0)
    reference_type: str = "order"
    reference_id: str
    reference_line_id: str | None = None
    expires_at: str | None = None


class StocktakeLine(BaseModel):
    sku_id: int
    location_id: int | None = None
    lot_id: int | None = None
    counted_qty: Decimal = Field(..., ge=0)


class StocktakeCreate(BaseModel):
    warehouse_id: int
    lines: list[StocktakeLine]


class LotCreate(BaseModel):
    sku_code: str = Field(..., min_length=1, max_length=50)
    lot_number: str = Field(..., min_length=1, max_length=100)
    expiry_date: date | None = None
    unit_cost: Decimal | None = None
    qty_received: Decimal = Decimal("0")
    supplier_ref: str | None = Field(default=None, max_length=255)


class LotCloseRequest(BaseModel):
    status: str = Field(default="quarantine", max_length=20)


# ---------------------------------------------------------------------------
# SKU / Warehouse / Location endpoints
# ---------------------------------------------------------------------------


@router.post("/skus", response_model=dict)
async def create_sku(
    body: SKUCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    try:
        sku = await service.create_sku(
            body.sku_code,
            body.name,
            body.uom,
            body.category_id,
            body.standard_cost,
            body.warehouse_id,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"id": sku.id, "sku_code": sku.sku_code, "name": sku.name, "uom": sku.uom}


@router.get("/skus", response_model=list[dict])
async def list_skus(
    is_active: bool | None = None,
    limit: int = 100,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    stmt = select(InvSKU)
    if is_active is not None:
        stmt = stmt.where(InvSKU.is_active == is_active)
    result = await db.execute(stmt.limit(limit))
    skus = result.scalars().all()
    return [
        {
            "id": s.id,
            "sku_code": s.sku_code,
            "name": s.name,
            "uom": s.uom,
            "is_active": s.is_active,
            "is_trackable": s.is_trackable,
        }
        for s in skus
    ]


@router.get("/skus/{sku_code}", response_model=dict)
async def get_sku(
    sku_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    try:
        sku = await service.get_sku(sku_code)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {
        "id": sku.id,
        "sku_code": sku.sku_code,
        "name": sku.name,
        "uom": sku.uom,
        "is_trackable": sku.is_trackable,
    }


@router.post("/warehouses", response_model=dict)
async def create_warehouse(
    body: WarehouseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    wh = await service.create_warehouse(body.code, body.name, body.city)
    return {"id": wh.id, "code": wh.code, "name": wh.name, "city": wh.city}


@router.get("/warehouses", response_model=list[dict])
async def list_warehouses(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    result = await db.execute(select(InvWarehouse).where(InvWarehouse.is_active.is_(True)))
    whs = result.scalars().all()
    return [{"id": w.id, "code": w.code, "name": w.name, "city": w.city} for w in whs]


@router.post("/locations", response_model=dict)
async def create_location(
    body: LocationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    loc = await service.create_location(body.warehouse_id, body.code, body.location_type)
    return {
        "id": loc.id,
        "warehouse_id": loc.warehouse_id,
        "code": loc.code,
        "location_type": loc.location_type,
    }


# ---------------------------------------------------------------------------
# Stock movement endpoints
# ---------------------------------------------------------------------------


@router.post("/movements/receipt", response_model=dict)
async def receipt(
    body: ReceiptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    try:
        m = await service.receipt(
            sku_id=(await service.get_sku(body.sku_code)).id,
            warehouse_id=body.warehouse_id,
            qty=body.qty,
            location_id=body.location_id,
            lot_id=body.lot_id,
            unit_cost=body.unit_cost,
            reference_id=body.reference_id,
            created_by=_uid(user),
            lot_number=body.lot_number,
            expiry_date=body.expiry_date,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/issue", response_model=dict)
async def issue(
    body: IssueRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    try:
        m = await service.issue(
            sku_id=(await service.get_sku(body.sku_code)).id,
            warehouse_id=body.warehouse_id,
            qty=body.qty,
            location_id=body.location_id,
            reference_id=body.reference_id,
            created_by=_uid(user),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/transfer", response_model=dict)
async def transfer(
    body: TransferRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    try:
        m = await service.transfer(
            sku_id=(await service.get_sku(body.sku_code)).id,
            from_warehouse_id=body.from_warehouse_id,
            to_warehouse_id=body.to_warehouse_id,
            qty=body.qty,
            from_location_id=body.from_location_id,
            to_location_id=body.to_location_id,
            created_by=_uid(user),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/adjust", response_model=dict)
async def adjust(
    body: AdjustRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    try:
        m = await service.adjust(
            sku_id=(await service.get_sku(body.sku_code)).id,
            warehouse_id=body.warehouse_id,
            qty=body.qty,
            reason=body.reason,
            created_by=_uid(user),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(abs(m.qty))}


@router.post("/movements/return", response_model=dict)
async def return_goods(
    body: ReturnRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    try:
        m = await service.return_goods(
            sku_id=(await service.get_sku(body.sku_code)).id,
            warehouse_id=body.warehouse_id,
            qty=body.qty,
            location_id=body.location_id,
            reference_id=body.reference_id,
            unit_cost=body.unit_cost,
            created_by=_uid(user),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/scrap", response_model=dict)
async def scrap(
    body: ScrapRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    try:
        m = await service.scrap(
            sku_id=(await service.get_sku(body.sku_code)).id,
            warehouse_id=body.warehouse_id,
            qty=body.qty,
            reason=body.reason,
            created_by=_uid(user),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.get("/movements", response_model=list[dict])
async def list_movements(
    sku_code: str | None = None,
    warehouse_id: int | None = None,
    movement_type: str | None = None,
    limit: int = 100,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    service = StockService(db)
    sku_id = None
    if sku_code:
        try:
            sku = await service.get_sku(sku_code)
        except EcoNojinException as e:
            raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
        sku_id = sku.id
    movements = await service.get_movements(sku_id, warehouse_id, movement_type, limit)
    return [
        {
            "id": m.id,
            "type": m.movement_type,
            "sku_id": m.sku_id,
            "qty": str(m.qty),
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in movements
    ]


# ---------------------------------------------------------------------------
# Balance & reservation endpoints
# ---------------------------------------------------------------------------


@router.get("/balances/{sku_code}", response_model=dict)
async def get_balance(
    sku_code: str,
    warehouse_id: int | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    service = StockService(db)
    try:
        sku = await service.get_sku(sku_code)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    balance = await service.get_balance(sku.id, warehouse_id) if warehouse_id else None
    if not balance:
        return {
            "sku_code": sku_code,
            "on_hand": "0",
            "reserved": "0",
            "available": "0",
            "blocked": "0",
            "in_transit": "0",
        }
    return {
        "sku_code": sku_code,
        "warehouse_id": balance.warehouse_id,
        "location_id": balance.location_id,
        "on_hand": str(balance.on_hand),
        "reserved": str(balance.reserved),
        "blocked": str(balance.blocked),
        "in_transit": str(balance.in_transit),
        "available": str(balance.available),
    }


@router.post("/reservations", response_model=dict)
async def reserve_stock(
    body: ReservationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    expires_at = None
    if body.expires_at:
        try:
            expires_at = datetime.fromisoformat(body.expires_at)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid expires_at timestamp: {body.expires_at!r}",
            ) from e
    try:
        sku = await service.get_sku(body.sku_code)
        r = await service.reserve_stock(
            sku_id=sku.id,
            warehouse_id=body.warehouse_id,
            qty=body.qty,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            reference_line_id=body.reference_line_id,
            expires_at=expires_at,
            created_by=_uid(user),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"reservation_id": r.id, "qty": str(r.qty), "status": r.status}


@router.post("/reservations/{reservation_id}/consume")
async def consume_reservation(
    reservation_id: int,
    qty: Annotated[
    Decimal | None, Query(description="Qty to consume (partial ok). If omitted, consumes all.")
] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    service = StockService(db)
    try:
        m = await service.consume_reservation(reservation_id, qty)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"movement_id": m.id, "qty": str(m.qty)}


@router.post("/reservations/{reservation_id}/release")
async def release_reservation(
    reservation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    try:
        r = await service.release_reservation(reservation_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return {"reservation_id": r.id, "status": r.status}


# ---------------------------------------------------------------------------
# Stocktake endpoints
# ---------------------------------------------------------------------------


@router.post("/stocktakes", response_model=dict)
async def create_stocktake(
    body: StocktakeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    st = await service.create_stocktake(
        body.warehouse_id, _uid(user), [line.model_dump() for line in body.lines]
    )
    return {"stocktake_id": st.id, "stocktake_number": st.stocktake_number, "status": st.status}


@router.post("/stocktakes/{stocktake_id}/approve")
async def approve_stocktake(
    stocktake_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    st = await service.approve_stocktake(stocktake_id, _uid(user))
    return {"stocktake_id": st.id, "status": st.status, "approved_by": st.approved_by}


# ---------------------------------------------------------------------------
# Lot / batch endpoints (FEFO expiry picking)
# ---------------------------------------------------------------------------


@router.post("/lots", response_model=dict)
async def create_lot(
    body: LotCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    try:
        sku = await service.get_sku(body.sku_code)
        lot = await service.create_lot(
            sku_id=sku.id,
            lot_number=body.lot_number,
            expiry_date=body.expiry_date,
            unit_cost=body.unit_cost,
            qty_received=body.qty_received,
            supplier_ref=body.supplier_ref,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return _lot_json(lot)


@router.get("/lots", response_model=list[dict])
async def list_lots(
    sku_code: str | None = None,
    status: str | None = None,
    expiry_before: date | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    service = StockService(db)
    sku_id = None
    if sku_code:
        try:
            sku = await service.get_sku(sku_code)
        except EcoNojinException as e:
            raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
        sku_id = sku.id
    lots = await service.list_lots(sku_id=sku_id, status=status, expiry_before=expiry_before)
    return [_lot_json(lot) for lot in lots]


@router.post("/lots/expire-due", response_model=dict)
async def expire_due_lots(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    expired = await service.expire_due_lots()
    return {"expired": expired}


@router.get("/lots/{lot_id}", response_model=dict)
async def get_lot(
    lot_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    try:
        lot = await service.get_lot(lot_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return _lot_json(lot)


@router.post("/lots/{lot_id}/close", response_model=dict)
async def close_lot(
    lot_id: str,
    body: LotCloseRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    try:
        lot = await service.close_lot(lot_id, body.status)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return _lot_json(lot)


# ---------------------------------------------------------------------------
# Valuation endpoints
# ---------------------------------------------------------------------------


@router.get("/valuation/report", response_model=dict)
async def valuation_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
):
    service = StockService(db)
    return _money_json(await service.valuation_report())


@router.get("/valuation/{sku_code}", response_model=dict)
async def get_sku_valuation(
    sku_code: str,
    warehouse_id: int | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
):
    service = StockService(db)
    try:
        sku = await service.get_sku(sku_code)
        valuation = await service.sku_valuation(sku.id, warehouse_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message) from e
    return _money_json(valuation)


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


@router.post("/reconcile", response_model=dict)
async def reconcile_inventory(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Any, Depends(require_admin)],
):
    service = StockService(db)
    return await service.reconcile_inventory()


# ---------------------------------------------------------------------------
# Sweep expired reservations
# ---------------------------------------------------------------------------


@router.post("/sweep-expired", response_model=dict)
async def sweep_expired_reservations(
    sku_code: str | None = Query(None),
    warehouse_id: int | None = Query(None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_admin)] = None,
):
    """Release reservations past expires_at; return how many were released.

    Admin-only. Can be wired to a cron scheduler (APScheduler/cron) for
    background execution. On each call it releases active reservations whose
    expires_at is at or before now, returning them to available stock.
    """
    service = StockService(db)
    sku_id = None
    if sku_code is not None:
        sku = await service.get_sku(sku_code)
        sku_id = sku.id
    released = await service.sweep_expired_reservations(
        sku_id=sku_id, warehouse_id=warehouse_id
    )
    return {"released": released}
