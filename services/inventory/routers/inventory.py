"""Inventory/WMS router — stock operations, reservations, and stocktakes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import InvSKU, InvWarehouse
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.exceptions import EcoNojinException
from services.inventory.service import StockService

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _uid(user) -> str:
    return str(user.id) if hasattr(user, 'id') else str(user.get('id'))


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


# ---------------------------------------------------------------------------
# SKU / Warehouse / Location endpoints
# ---------------------------------------------------------------------------

@router.post("/skus", response_model=dict)
async def create_sku(body: SKUCreate, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    service = StockService(db)
    try:
        sku = await service.create_sku(
            body.sku_code, body.name, body.uom,
            body.category_id, body.standard_cost, body.warehouse_id,
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"id": sku.id, "sku_code": sku.sku_code, "name": sku.name, "uom": sku.uom}


@router.get("/skus", response_model=list[dict])
async def list_skus(
    is_active: bool = True, limit: int = 100,
    db: AsyncSession = Depends(get_db), user=Depends(require_user),
):
    result = await db.execute(
        __import__("sqlalchemy").select(InvSKU).where(InvSKU.is_active == is_active).limit(limit)
    )
    skus = result.scalars().all()
    return [{"id": s.id, "sku_code": s.sku_code, "name": s.name, "uom": s.uom, "is_active": s.is_active} for s in skus]


@router.get("/skus/{sku_code}", response_model=dict)
async def get_sku(sku_code: str, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
    service = StockService(db)
    sku = await service.get_sku(sku_code)
    return {"id": sku.id, "sku_code": sku.sku_code, "name": sku.name, "uom": sku.uom, "is_trackable": sku.is_trackable}


@router.post("/warehouses", response_model=dict)
async def create_warehouse(body: WarehouseCreate, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    service = StockService(db)
    wh = await service.create_warehouse(body.code, body.name, body.city)
    return {"id": wh.id, "code": wh.code, "name": wh.name, "city": wh.city}


@router.get("/warehouses", response_model=list[dict])
async def list_warehouses(db: AsyncSession = Depends(get_db), user=Depends(require_user)):
    from sqlalchemy import select
    result = await db.execute(select(InvWarehouse).where(InvWarehouse.is_active == True))
    whs = result.scalars().all()
    return [{"id": w.id, "code": w.code, "name": w.name, "city": w.city} for w in whs]


@router.post("/locations", response_model=dict)
async def create_location(body: LocationCreate, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    service = StockService(db)
    loc = await service.create_location(body.warehouse_id, body.code, body.location_type)
    return {"id": loc.id, "warehouse_id": loc.warehouse_id, "code": loc.code, "location_type": loc.location_type}


# ---------------------------------------------------------------------------
# Stock movement endpoints
# ---------------------------------------------------------------------------

@router.post("/movements/receipt", response_model=dict)
async def receipt(body: ReceiptRequest, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
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
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/issue", response_model=dict)
async def issue(body: IssueRequest, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
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
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/transfer", response_model=dict)
async def transfer(body: TransferRequest, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
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
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/adjust", response_model=dict)
async def adjust(body: AdjustRequest, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
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
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(abs(m.qty))}


@router.post("/movements/return", response_model=dict)
async def return_goods(body: ReturnRequest, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
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
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.post("/movements/scrap", response_model=dict)
async def scrap(body: ScrapRequest, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
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
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"movement_id": m.id, "type": m.movement_type, "qty": str(m.qty)}


@router.get("/movements", response_model=list[dict])
async def list_movements(
    sku_code: str | None = None,
    warehouse_id: int | None = None,
    movement_type: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_user),
):
    service = StockService(db)
    sku_id = None
    if sku_code:
        sku = await service.get_sku(sku_code)
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
    db: AsyncSession = Depends(get_db),
    user=Depends(require_user),
):
    service = StockService(db)
    sku = await service.get_sku(sku_code)
    balance = await service.get_balance(sku.id, warehouse_id) if warehouse_id else None
    if not balance:
        return {"sku_code": sku_code, "on_hand": "0", "reserved": "0", "available": "0", "blocked": "0", "in_transit": "0"}
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
async def reserve_stock(body: ReservationRequest, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
    service = StockService(db)
    try:
        sku = await service.get_sku(body.sku_code)
        r = await service.reserve_stock(
            sku_id=sku.id,
            warehouse_id=body.warehouse_id,
            qty=body.qty,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            reference_line_id=body.reference_line_id,
            expires_at=__import__("datetime").datetime.fromisoformat(body.expires_at) if body.expires_at else None,
            created_by=_uid(user),
        )
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"reservation_id": r.id, "qty": str(r.qty), "status": r.status}


@router.post("/reservations/{reservation_id}/consume")
async def consume_reservation(
    reservation_id: int,
    qty: Decimal | None = Query(default=None, description="Qty to consume (partial ok). If omitted, consumes all."),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_user),
):
    service = StockService(db)
    try:
        m = await service.consume_reservation(reservation_id, qty)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"movement_id": m.id, "qty": str(m.qty)}


@router.post("/reservations/{reservation_id}/release")
async def release_reservation(reservation_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_user)):
    service = StockService(db)
    try:
        r = await service.release_reservation(reservation_id)
    except EcoNojinException as e:
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    return {"reservation_id": r.id, "status": r.status}


# ---------------------------------------------------------------------------
# Stocktake endpoints
# ---------------------------------------------------------------------------

@router.post("/stocktakes", response_model=dict)
async def create_stocktake(body: StocktakeCreate, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    service = StockService(db)
    st = await service.create_stocktake(body.warehouse_id, _uid(user), [l.model_dump() for l in body.lines])
    return {"stocktake_id": st.id, "stocktake_number": st.stocktake_number, "status": st.status}


@router.post("/stocktakes/{stocktake_id}/approve")
async def approve_stocktake(stocktake_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    service = StockService(db)
    st = await service.approve_stocktake(stocktake_id, _uid(user))
    return {"stocktake_id": st.id, "status": st.status, "approved_by": st.approved_by}


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

@router.post("/reconcile", response_model=dict)
async def reconcile_inventory(db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    service = StockService(db)
    return await service.reconcile_inventory()
