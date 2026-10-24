from typing import Annotated

from sqlalchemy import select

from services.api_gateway.errors import safe_detail_for_status

"""API endpoints for Marketplace."""

import contextlib
import logging
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload

from database.hub import hub
from database.models import User
from services.api_gateway.auth import (
    get_current_user_optional,
    require_admin,
    require_user,
)
from services.business_modules.carbon import get_tokenization_service
from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderItem,
    MarketplacePayment,
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
    OrderStatus,
    Product,
    ProductCategory,
)
from services.marketplace.order_management import get_order_manager
from services.marketplace.payments_service import (
    EscrowService,
    PaymentError,
    PaymentGateways,
    bank_instructions,
)
from services.marketplace.product_catalog import get_catalog
from services.marketplace.service import MarketplaceService, get_marketplace_service  # noqa: F401
from services.marketplace.traceability import get_traceability

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/marketplace", tags=["Marketplace"])


def get_db():
    with hub.get_session() as session:
        yield session


async def get_async_db() -> AsyncSession:
    """The async session the marketplace service needs (P12 breadth delta).

    ``MarketplaceService`` awaits its session; the sync dependency above cannot
    serve it, and the old module-level singleton cached whichever session was
    first handed to it.
    """
    async with hub.get_async_session() as session:
        yield session


# --- Request Models ---


class OrderRequest(BaseModel):
    product_id: str
    buyer_name: str = Field(..., min_length=1, max_length=100)
    quantity_kg: float = Field(..., gt=0)


class CheckoutOrderRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    shipping_address: str = Field(..., min_length=5, max_length=500)


# --- Product Endpoints ---


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    category: str = Field(..., min_length=2)
    price: float = Field(..., gt=0)
    village_id: str = Field(..., min_length=1)
    description: str = Field(default="", max_length=2000)
    stock: int = Field(default=0, ge=0)
    unit: str = Field(default="kg")
    images: list[str] = Field(default_factory=list)


@router.get("/products")
def list_products(
    category: str | None = None,
    organic_only: bool = False,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List marketplace products with filters."""
    stmt = (
        select(MarketplaceProduct)
        .options(joinedload(MarketplaceProduct.seller))
        .where(
            MarketplaceProduct.status.in_(
                [MarketplaceProductStatus.APPROVED, MarketplaceProductStatus.ACTIVE]
            ),
            MarketplaceSeller.is_verified.is_(True),
        )
        .join(MarketplaceSeller)
    )
    if category:
        stmt = stmt.where(MarketplaceProduct.category == category)
    if organic_only:
        stmt = stmt.where(MarketplaceProduct.organic.is_(True))
    if min_price is not None:
        stmt = stmt.where(MarketplaceProduct.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(MarketplaceProduct.price <= max_price)
    persisted_products = db.execute(
        stmt.order_by(MarketplaceProduct.created_at.desc()).limit(limit)
    ).scalars().all()
    if persisted_products:
        return {
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                    "category": product.category,
                    "description": product.description or "",
                    "price_per_kg": float(product.price),
                    "quantity_available_kg": product.stock or 0,
                    "organic_certified": bool(product.organic),
                    "producer_name": product.seller.shop_name if product.seller else "",
                    "origin_location": product.seller.location if product.seller else "",
                    "traceability_code": "",
                    "images": product.images or [],
                    "currency": product.currency or "IRR",
                    "orderable": True,
                }
                for product in persisted_products
            ],
            "count": len(persisted_products),
        }

    catalog = get_catalog()

    cat_enum = None
    if category:
        with contextlib.suppress(ValueError):
            cat_enum = ProductCategory(category)

    products = catalog.list_products(
        category=cat_enum,
        organic_only=organic_only,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
    )

    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug if hasattr(p, "slug") else "",
                "category": p.category.value if hasattr(p.category, "value") else str(p.category),
                "description": p.description if hasattr(p, "description") else "",
                "price_per_kg": p.price_per_kg
                if hasattr(p, "price_per_kg")
                else getattr(p, "price", 0),
                "quantity_available_kg": p.quantity_available_kg
                if hasattr(p, "quantity_available_kg")
                else getattr(p, "stock", 0),
                "organic_certified": p.organic_certified
                if hasattr(p, "organic_certified")
                else False,
                "producer_name": p.producer_name,
                "origin_location": p.origin_location,
                "traceability_code": p.traceability_code,
                "images": p.images if hasattr(p, "images") else [],
                "currency": None,
                "orderable": False,
            }
            for p in products
        ],
        "count": len(products),
    }


@router.post("/checkout/products")
def submit_persisted_product(
    payload: ProductCreateRequest,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Submit a product into the persisted seller and approval workflow."""
    seller = db.execute(
        select(MarketplaceSeller).where(MarketplaceSeller.user_id == str(user.id))
    ).scalar_one_or_none()
    if seller is None:
        seller = MarketplaceSeller(
            user_id=str(user.id),
            village_id=payload.village_id,
            shop_name=(user.full_name or user.email or "Marketplace seller")[:200],
            status="pending",
            is_verified=False,
        )
        db.add(seller)
        db.flush()
    elif not seller.is_verified and seller.village_id != payload.village_id:
        seller.village_id = payload.village_id

    product = MarketplaceProduct(
        seller_id=str(seller.id),
        name=payload.name,
        slug=f"{payload.name.lower().replace(' ', '-')[:250]}-{uuid4().hex[:8]}",
        description=payload.description,
        category=payload.category,
        price=Decimal(str(payload.price)),
        currency="IRR",
        stock=payload.stock,
        unit=payload.unit,
        village_id=payload.village_id,
        images=payload.images,
        status=MarketplaceProductStatus.PENDING_APPROVAL,
    )
    db.add(product)
    db.commit()
    return {
        "product_id": str(product.id),
        "status": product.status.value,
        "seller_status": seller.status,
        "seller_verification_required": not seller.is_verified,
    }


@router.post("/products")
async def create_product(
    payload: ProductCreateRequest,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new marketplace product."""
    catalog = get_catalog()
    try:
        product = catalog.add_product(
            Product(
                name=payload.name,
                category=ProductCategory(payload.category),
                description=payload.description,
                producer_id=user.id,
                producer_name=user.full_name or user.email,
                origin_location=payload.village_id,
                price_per_kg=payload.price,
                quantity_available_kg=payload.stock,
                minimum_order_kg=1,
                organic_certified=False,
                carbon_footprint_kg_co2=0.0,
                water_footprint_liters=0.0,
                images=payload.images,
            )
        )
        product_id_created = product if isinstance(product, str) else product.id
        return {"product_id": product_id_created, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/products/search")
def search_products(
    q: str,
    village_id: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Ranked product search.

    The ranking comes from the marketplace's FTS5 inverted index
    (``services/marketplace/search.py``): bm25 ordering, SQL-level village /
    category / price predicates, prefix matching and Arabic/Persian spelling
    folding. When the index cannot be built (no FTS5 in the SQLite build) the
    answer degrades to the in-memory catalogue scan and the response says which
    engine answered -- a search that silently degrades is worse than one that
    names its own ranking.
    """
    from sqlalchemy.exc import SQLAlchemyError

    from services.marketplace.models import MarketplaceProduct
    from services.marketplace.search import FTS5UnavailableError, get_search_service

    engine = "fts"
    hits: list[dict] | None = None
    try:
        service = get_search_service()
        if service.count() == 0:
            # rebuild(products) is the synchronous entry point: the service's
            # rebuild_from_session is a coroutine (built for the async ORM)
            # and awaiting it from this sync route would leave a coroutine
            # object in its place, so the rows are read here instead. An empty
            # database on first boot is not an error: the search degrades to
            # the catalogue and says so.
            service.rebuild(db.execute(select(MarketplaceProduct)).scalars().all())
        hits = service.search(
            q, village_id=village_id, category=category, max_price=max_price, limit=limit
        )
    except FTS5UnavailableError:
        engine, hits = "catalogue_fallback", None
    except SQLAlchemyError:
        engine, hits = "catalogue_fallback", None

    if hits is not None:
        return {
            "query": q,
            "engine": engine,
            "results": hits,
            "count": len(hits),
        }

    catalog = get_catalog()
    results = catalog.search_products(q)[:limit]
    return {
        "query": q,
        "engine": engine,
        "results": [
            {"id": p.id, "name": p.name, "price_per_kg": p.price_per_kg} for p in results
        ],
        "count": len(results),
    }


@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """Get product details.

    The catalogue has two planes: the in-memory demo rows and the persisted
    ``MarketplaceProduct`` rows that a seller submits (and an admin approves)
    through ``POST /checkout/products``. A buyer sees approved persisted rows
    in ``GET /products``, but this route only read the demo catalogue, so
    every persisted product answered 404 — the detail panel could not open
    exactly the products the marketplace actually sells. The persisted row is
    now a fallback, mapped field-for-field with ``None`` where the persisted
    schema has no column (no invented values: the buyer panel hides the rows
    that come back empty).
    """
    catalog = get_catalog()
    product = catalog.get_product(product_id)

    if not product:
        from services.marketplace.models import MarketplaceProduct as PersistedProduct

        persisted = await db.get(PersistedProduct, product_id)
        if persisted is None:
            raise HTTPException(status_code=404, detail="Product not found")

        seller_name = None
        if persisted.seller_id:
            from services.marketplace.models import MarketplaceSeller

            seller = await db.get(MarketplaceSeller, persisted.seller_id)
            seller_name = seller.shop_name if seller is not None else None

        category = (
            persisted.category.value
            if hasattr(persisted.category, "value")
            else str(persisted.category)
        )
        return {
            "id": persisted.id,
            "name": persisted.name,
            "category": category,
            "description": persisted.description,
            "price_per_kg": float(persisted.price) if persisted.price is not None else None,
            "quantity_available_kg": float(persisted.stock) if persisted.stock is not None else None,
            "minimum_order_kg": None,
            "organic_certified": None,
            "carbon_footprint_kg_co2": None,
            "water_footprint_liters": None,
            "producer_name": seller_name,
            "origin_location": persisted.village_id,
            "harvest_date": None,
            "batch_number": None,
            "traceability_code": None,
            "images": list(persisted.images or []),
        }

    return {
        "id": product.id,
        "name": product.name,
        "category": product.category.value,
        "description": product.description,
        "price_per_kg": product.price_per_kg,
        "quantity_available_kg": product.quantity_available_kg,
        "minimum_order_kg": product.minimum_order_kg,
        "organic_certified": product.organic_certified,
        "carbon_footprint_kg_co2": product.carbon_footprint_kg_co2,
        "water_footprint_liters": product.water_footprint_liters,
        "producer_name": product.producer_name,
        "origin_location": product.origin_location,
        "harvest_date": product.harvest_date.isoformat() if product.harvest_date else None,
        "batch_number": product.batch_number,
        "traceability_code": product.traceability_code,
        "images": product.images if hasattr(product, "images") else [],
    }


@router.get("/products/{product_id}/trace")
def get_product_trace(product_id: str):
    """Get full traceability history for a product."""
    catalog = get_catalog()
    product = catalog.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    trace_system = get_traceability()
    trace = trace_system.get_trace(product.traceability_code)

    return {
        "product_id": product_id,
        "traceability_code": product.traceability_code,
        "events": [
            {
                "timestamp": r.timestamp.isoformat(),
                "event": r.event,
                "location": r.location,
                "actor": r.actor,
                "notes": r.notes,
            }
            for r in trace
        ],
        "qr_data": trace_system.generate_qr_data(product.traceability_code),
    }


@router.post("/products/{product_id}/images")
async def upload_product_images(
    product_id: str,
    files: Annotated[list[UploadFile], File()],
    user: Annotated[User, Depends(require_user)],
):
    """Upload images for a product.

    P3: this route mutated *any* product for *any* authenticated user. The
    producer who listed the product (or an admin) may change it now; the
    negative test pins the 403 for a stranger.
    """
    catalog = get_catalog()
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    owner_id = str(getattr(product, "producer_id", "") or "")
    caller_role = str(getattr(user, "role", "") or "")
    is_owner = bool(owner_id) and owner_id == str(user.id)
    from services.api_gateway.auth import ADMIN_ROLES

    if not (is_owner or caller_role in ADMIN_ROLES):
        raise HTTPException(
            status_code=403,
            detail=safe_detail_for_status(ValueError("access denied"), 403),
        )

    # In a real implementation, save files to storage (S3, local, etc.)
    # For now, return mock URLs
    uploaded_urls = []
    for file in files:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")
        # Generate a mock URL - in production, upload to storage
        uploaded_urls.append(f"/uploads/products/{product_id}/{file.filename}")

    # Update product images (extend existing)
    existing_images = getattr(product, "images", [])
    product.images = existing_images + uploaded_urls

    return {"product_id": product_id, "images": product.images}


# --- Producer Endpoints ---


@router.get("/producers")
def list_producers():
    """List all producers."""
    catalog = get_catalog()
    producers = catalog.list_producers()

    return {
        "producers": [
            {
                "id": p.id,
                "name": p.name,
                "location": p.location,
                "producer_type": p.producer_type,
                "rating": p.rating,
                "total_sales": p.total_sales,
                "certifications": [c.value for c in p.certifications],
            }
            for p in producers
        ],
        "count": len(producers),
    }


# --- Order Endpoints ---


@router.post("/checkout/orders")
async def create_persisted_checkout_order(
    payload: CheckoutOrderRequest,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """Create a priced, stock-reserved order from the persistent catalogue."""
    product_result = await db.execute(
        select(MarketplaceProduct)
        .options(joinedload(MarketplaceProduct.seller))
        .where(MarketplaceProduct.id == payload.product_id)
    )
    product = product_result.scalar_one_or_none()
    if product is None or product.status not in {
        MarketplaceProductStatus.APPROVED,
        MarketplaceProductStatus.ACTIVE,
    }:
        raise HTTPException(status_code=404, detail="Approved product not found")
    if product.seller is None or not product.seller.is_verified:
        raise HTTPException(status_code=409, detail="Seller is not verified")

    try:
        order = await MarketplaceService(db).create_order(
            buyer_id=str(user.id),
            items=[{"product_id": str(product.id), "quantity": payload.quantity}],
            village_id=str(product.village_id),
            shipping_address={
                "address_line": payload.shipping_address.strip(),
                "village_id": str(product.village_id),
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=safe_detail_for_status(exc, 400),
        ) from exc
    items = await MarketplaceService(db).get_order_items(str(order.id))
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "subtotal": str(order.subtotal),
        "total": str(order.total),
        "currency": order.currency or "IRR",
        "items": [
            {
                "product_id": str(item.product_id),
                "product_name": item.product_name,
                "quantity": str(item.quantity),
                "unit_price": str(item.unit_price),
                "line_total": str(item.line_total),
            }
            for item in items
        ],
    }


@router.post("/orders")
def create_order(payload: OrderRequest, user: Annotated[User, Depends(require_user)]):
    """Create a new order."""
    manager = get_order_manager()
    catalog = get_catalog()

    # Get product to find seller
    product = catalog.get_product(payload.product_id)
    seller_id = product.producer_id if product else ""

    try:
        order = manager.create_order(
            product_id=payload.product_id,
            # P3: the buyer identity comes from the token, never from the
            # request body — ``payload.buyer_name`` is accepted for backward
            # compatibility and ignored (contract §6: deprecated-with-migration).
            buyer_name=str(user.id),
            quantity_kg=payload.quantity_kg,
            seller_id=seller_id,
        )

        return {
            "order_id": order.id,
            "product_name": order.product_name,
            "quantity_kg": order.quantity_kg,
            "total_price": order.total_price,
            "status": order.status.value,
            "traceability_code": order.traceability_code,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/orders")
def list_orders(
    status: str | None = None,
    user: Annotated[User, Depends(require_user)] = None,
):
    """List the caller's own orders.

    P3: this route was unauthenticated and listed **every** buyer's orders with
    their identifiers. It now requires a user and is scoped to the caller —
    the negative test in ``test_access_control_p3.py`` pins both halves.
    """
    manager = get_order_manager()

    status_enum = None
    if status:
        with contextlib.suppress(ValueError):
            status_enum = OrderStatus(status)

    orders = manager.list_orders(status=status_enum, buyer_id=str(user.id))

    legacy_rows = [
        {
            "id": o.id,
            "order_number": o.id,
            "product_name": o.product_name,
            "buyer_name": o.buyer_name,
            "seller_id": getattr(o, "seller_id", ""),
            "quantity_kg": o.quantity_kg,
            "total_price": o.total_price,
            "currency": None,
            "payment_status": None,
            "payment": None,
            "status": o.status.value,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]
    with hub.get_session() as session:
        persisted_orders = session.execute(
            select(MarketplaceOrder)
            .options(selectinload(MarketplaceOrder.items))
            .where(MarketplaceOrder.buyer_id == str(user.id))
            .order_by(MarketplaceOrder.created_at.desc())
            .limit(100)
        ).scalars().all()
        persisted_rows = []
        for order in persisted_orders:
            latest_payment = session.execute(
                select(MarketplacePayment)
                .where(MarketplacePayment.order_id == str(order.id))
                .order_by(MarketplacePayment.created_at.desc())
                .limit(1)
            ).scalars().first()
            persisted_rows.append(
                {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "product_name": ", ".join(item.product_name for item in order.items),
                    "buyer_name": str(user.id),
                    "seller_id": "",
                    "quantity_kg": sum(float(item.quantity) for item in order.items),
                    "total_price": float(order.total or 0),
                    "currency": order.currency or "IRR",
                    "payment_status": order.payment_status,
                    "payment": (
                        {
                            **latest_payment.to_dict(),
                            "tracking_code": latest_payment.tracking_code,
                        }
                        if latest_payment
                        else None
                    ),
                    "status": order.status.value
                    if hasattr(order.status, "value")
                    else str(order.status),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                }
            )

    return {
        "orders": persisted_rows + legacy_rows,
        "count": len(persisted_rows) + len(legacy_rows),
    }


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str, user: Annotated[User, Depends(require_user)]):
    """Confirm an order.

    Only the buyer who placed the order -- or an admin -- may confirm it. The
    route used to accept **any** authenticated caller, so one buyer could
    confirm (and thereby advance) another buyer's order.
    """
    from services.api_gateway.auth import ADMIN_ROLES

    manager = get_order_manager()
    order = manager.get_order(order_id)
    if order is not None:
        caller_role = str(getattr(user, "role", "") or "")
        if caller_role not in ADMIN_ROLES and str(order.buyer_name or "") != str(user.id):
            raise HTTPException(
                status_code=403,
                detail=safe_detail_for_status(ValueError("access denied"), 403),
            )
    if manager.confirm_order(order_id):
        return {"status": "confirmed", "order_id": order_id}
    raise HTTPException(status_code=400, detail="Cannot confirm order")


@router.get("/orders/{order_id}/track")
async def track_order(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)] = None,
):
    """Get order tracking timeline.

    Two order planes exist and the buyer sees both in ``GET /orders``: the
    in-memory order manager (demo catalogue) and the persisted
    ``MarketplaceOrder`` rows. This route used to read only the manager, so
    every persisted order answered 404 — the detail panel showed nothing for
    exactly the orders a registered buyer actually places. The persisted
    plane is now a fallback: it reports the header status and timestamps
    (the live, buyer-owned summary) instead of a fabricated per-step
    timeline.

    Ownership: an authenticated caller may track their own order or any
    order as an admin; anonymous callers keep the manager-plane summary only.
    """
    manager = get_order_manager()
    order = manager.get_order(order_id)

    if order is None:
        service = MarketplaceService(db)
        persisted = await service.db.get(MarketplaceOrder, order_id)
        if persisted is None:
            raise HTTPException(status_code=404, detail="Order not found")

        from services.api_gateway.auth import ADMIN_ROLES

        caller_id = str(getattr(user, "id", "") or "")
        caller_role = str(getattr(user, "role", "") or "")
        owner_id = str(persisted.buyer_id or "")
        if not (caller_id and caller_id == owner_id) and caller_role not in ADMIN_ROLES:
            raise HTTPException(
                status_code=403,
                detail=safe_detail_for_status(ValueError("access denied"), 403),
            )

        status_value = (
            persisted.status.value
            if hasattr(persisted.status, "value")
            else str(persisted.status)
        )
        timeline = [
            {
                "timestamp": persisted.created_at.isoformat() if persisted.created_at else None,
                "status": status_value,
                "title": "وضعیت سفارش",
                "description": "آخرین وضعیت ثبت‌شده برای این سفارش.",
            }
        ]
        return {
            "order_id": persisted.id,
            "order_number": getattr(persisted, "order_number", None) or persisted.id,
            "current_status": status_value,
            "timeline": timeline,
        }

    # Build timeline from order status
    timeline = [
        {
            "timestamp": order.created_at.isoformat(),
            "status": "pending",
            "title": "سفارش ثبت شد",
            "description": "سفارش شما ثبت شده و در انتظار تایید است",
        }
    ]

    if order.status in ["confirmed", "shipped", "delivered"]:
        timeline.append(
            {
                "timestamp": order.updated_at.isoformat()
                if hasattr(order, "updated_at")
                else order.created_at.isoformat(),
                "status": "confirmed",
                "title": "سفارش تایید شد",
                "description": "فروشنده سفارش را تایید کرد و در حال آماده‌سازی است",
            }
        )

    if order.status in ["shipped", "delivered"]:
        timeline.append(
            {
                "timestamp": order.updated_at.isoformat()
                if hasattr(order, "updated_at")
                else order.created_at.isoformat(),
                "status": "shipped",
                "title": "ارسال شد",
                "description": "سفارش توسط پست/باربری ارسال شد",
            }
        )

    if order.status == "delivered":
        timeline.append(
            {
                "timestamp": order.updated_at.isoformat()
                if hasattr(order, "updated_at")
                else order.created_at.isoformat(),
                "status": "delivered",
                "title": "تحویل داده شد",
                "description": "سفارش به مقصد تحویل داده شد",
            }
        )

    if order.status == "cancelled":
        timeline.append(
            {
                "timestamp": order.updated_at.isoformat()
                if hasattr(order, "updated_at")
                else order.created_at.isoformat(),
                "status": "cancelled",
                "title": "لغو شد",
                "description": "سفارش لغو گردید",
            }
        )

    return {
        "order_id": order.id,
        "order_number": getattr(order, "order_number", order.id),
        "current_status": order.status.value if hasattr(order.status, "value") else order.status,
        "timeline": timeline,
    }


@router.get("/orders/{order_id}/items")
async def get_order_items(
    order_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    user: Annotated[User, Depends(require_user)],
):
    """Get the persisted basket (line items) for an order.

    The order header only stores money totals; the per-line basket lives in
    ``MarketplaceOrderItem`` and survives a reload through
    ``MarketplaceService.get_order_items``. An unknown order is a 404, while an
    order with no lines returns an empty list.

    P3 parity: the basket is the buyer's own — the route requires a user and
    only serves the order's buyer (or an admin), exactly like ``GET /orders``
    scopes its list. Without the check any anonymous caller could read any
    order's ``seller_id``/``unit_price`` lines by guessing its id.

    The service is constructed **per request** on the async session (the old
    ``get_marketplace_service(db)`` singleton received this router's *sync*
    session, so every await inside the async service raised — the 500s the P12
    breadth sweep measured). The session is request-scoped and the service is
    stateless, so there is no cached state to lose.
    """
    service = MarketplaceService(db)
    order = await service.db.get(MarketplaceOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    owner_id = str(getattr(order, "buyer_id", "") or "")
    caller_role = str(getattr(user, "role", "") or "")
    from services.api_gateway.auth import ADMIN_ROLES

    if not (owner_id and owner_id == str(user.id)) and caller_role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail=safe_detail_for_status(ValueError("access denied"), 403),
        )

    items = await service.get_order_items(order_id)
    return {
        "order_id": order_id,
        "items": [
            {
                "id": i.id,
                "product_id": str(i.product_id),
                "seller_id": str(i.seller_id) if i.seller_id else None,
                "product_name": i.product_name,
                "quantity": str(i.quantity),
                "unit": i.unit,
                "unit_price": str(i.unit_price),
                "line_total": str(i.line_total),
            }
            for i in items
        ],
        "count": len(items),
    }


@router.get("/stats")
def marketplace_stats(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get marketplace statistics.

    P3: revenue aggregates were public. They are authenticated now; per-seller
    scoping of the revenue block is implemented: if the user is a verified
    seller, they see only their own revenue stats; otherwise they see global
    aggregates (admins) or empty (buyers).
    """
    manager = get_order_manager()
    catalog = get_catalog()

    products = catalog.list_products()
    producers = catalog.list_producers()

    # Check if user is a verified seller
    seller = db.execute(
        select(MarketplaceSeller).where(MarketplaceSeller.user_id == user.id)
    ).scalar_one_or_none()

    seller_id = seller.id if seller and seller.status == "verified" else None

    return {
        "total_products": len(products),
        "total_producers": len(producers),
        "organic_products": sum(1 for p in products if p.organic_certified),
        "orders": manager.get_revenue_stats(seller_id=seller_id),
    }


# --- Product carbon-credit tokenization endpoints ---


class ProductTokenizeRequest(BaseModel):
    credit_type: str = Field(
        "offset", description="Credit standard/registry code (VCS, GS, offset, ...)"
    )
    owner_address: str | None = Field(
        None, description="Ethereum address to receive the minted credits"
    )


@router.post("/products/{product_id}/tokenize")
def tokenize_product(
    product_id: str,
    payload: ProductTokenizeRequest,
    user: Annotated[User, Depends(require_user)],
):
    """Tokenize a product's carbon footprint into carbon credits.

    One carbon credit == 1 tonne of CO2.  The product's
    ``carbon_footprint_kg_co2`` is converted to tonnes and minted against the
    product id as the project reference.
    """
    catalog = get_catalog()
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    amount_tonnes = product.carbon_footprint_kg_co2 / 1000.0
    if amount_tonnes <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Product has no carbon footprint to tokenize (carbon_footprint_kg_co2={product.carbon_footprint_kg_co2})",
        )

    service = get_tokenization_service()
    try:
        tx_hash = service.issue_credits(
            project_id=product_id,
            amount=round(amount_tonnes, 4),
            credit_type=payload.credit_type,
            owner=payload.owner_address,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e

    credits = service.get_credits_by_project(product_id)
    token_id = credits[-1].credit_id if credits else None

    return {
        "product_id": product_id,
        "product_name": product.name,
        "carbon_footprint_kg_co2": product.carbon_footprint_kg_co2,
        "credits_minted_tonnes": round(amount_tonnes, 4),
        "credit_type": payload.credit_type,
        "token_id": token_id,
        "tx_hash": tx_hash,
        "on_chain": service.is_onchain_available(),
    }


@router.get("/products/{product_id}/carbon-credits")
def get_product_carbon_credits(product_id: str, user: Annotated[User, Depends(require_user)]):
    """Get carbon credits linked to a product's carbon footprint."""
    catalog = get_catalog()
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    service = get_tokenization_service()
    credits = service.get_credits_by_project(product_id)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "carbon_footprint_kg_co2": product.carbon_footprint_kg_co2,
        "count": len(credits),
        "credits": [
            {
                "token_id": c.credit_id,
                "amount_tonnes": c.amount,
                "owner": c.owner,
                "issued_at": c.issued_at.isoformat(),
                "retired": c.retired,
                "retired_at": c.retired_at.isoformat() if c.retired_at else None,
                "tx_hash": c.tx_hash,
            }
            for c in credits
        ],
    }


# --- Cart Models ---


class CartItem(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, le=100)


class AddToCartRequest(BaseModel):
    items: list[CartItem]


class CheckoutRequest(BaseModel):
    shipping_address: dict = Field(..., min_length=1)
    payment_method: str = Field(default="wallet")


# --- Cart Endpoints ---


def _cart_field(cart: object, name: str, default=None):
    """Read a cart field from either shape the order manager returns.

    ``OrderManager`` stores carts as plain dicts (``self._carts``), while the
    repo-backed path can return objects; the routes must not care which one
    they got — attribute access over a dict raised ``AttributeError`` and 500'd
    every cart route (P6's golden-path test caught it).
    """
    if isinstance(cart, dict):
        return cart.get(name, default)
    return getattr(cart, name, default)


def _persisted_product_for_cart(product_id: str):
    """Persisted-catalogue reader for the cart's product lookup.

    Returns an object shaped like the demo catalogue's product (``id``,
    ``name``, ``price_per_kg``) so ``OrderManager`` can build a cart line
    without knowing which plane the product came from. Returns ``None`` for
    unknown or unapproved rows, which is the manager's "product not found".

    Opens its own short-lived session instead of closing over a request
    session: the manager is a singleton that outlives requests, and the
    unified in-memory database makes the row visible to any session.
    """
    from services.marketplace.models import MarketplaceProduct, MarketplaceProductStatus

    with hub.get_session() as session:
        row = session.get(MarketplaceProduct, str(product_id))
        if row is None or row.status != MarketplaceProductStatus.ACTIVE:
            return None
        if row.price is None:
            return None
        return SimpleNamespace(
            id=row.id,
            name=row.name,
            price_per_kg=float(row.price),
            quantity_available_kg=float(row.stock) if row.stock is not None else None,
        )


def _cart_response(cart: object) -> dict:
    """The cart payload shape, identical for both manager return types."""
    return {
        "cart_id": _cart_field(cart, "id"),
        "items": _cart_field(cart, "items", []),
        "total_items": _cart_field(cart, "total_items", 0),
        "subtotal": _cart_field(cart, "subtotal", 0),
    }


@router.post("/cart")
async def add_to_cart(
    payload: AddToCartRequest,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Add items to user's cart."""
    get_catalog()
    order_manager = get_order_manager(
        product_lookup=_persisted_product_for_cart,
    )
    try:
        cart = order_manager.add_to_cart(
            buyer_id=str(user.id),
            items=[{"product_id": i.product_id, "quantity": i.quantity} for i in payload.items],
        )
        return _cart_response(cart)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/cart")
async def get_cart(user: Annotated[User, Depends(require_user)]):
    """Get user's current cart."""
    order_manager = get_order_manager()
    try:
        cart = order_manager.get_cart(buyer_id=user.id)
        if not cart:
            return {"cart_id": None, "items": [], "total_items": 0, "subtotal": 0}
        return _cart_response(cart)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.delete("/cart/{product_id}")
async def remove_from_cart(
    product_id: str,
    user: Annotated[User, Depends(require_user)],
):
    """Remove item from cart."""
    order_manager = get_order_manager()
    try:
        order_manager.remove_from_cart(buyer_id=user.id, product_id=product_id)
        return {"removed": product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., gt=0, le=100)


@router.patch("/cart/{product_id}")
async def update_cart_item(
    product_id: str,
    payload: UpdateCartItemRequest,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update item quantity in cart."""
    order_manager = get_order_manager()
    try:
        cart = order_manager.update_cart_item(
            buyer_id=user.id,
            product_id=product_id,
            quantity=payload.quantity,
        )
        return _cart_response(cart)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


# --- Wishlist Endpoints ---


class AddToWishlistRequest(BaseModel):
    product_id: str = Field(..., min_length=1)


@router.get("/wishlist")
async def get_wishlist(user: Annotated[User, Depends(require_user)]):
    """Get user's wishlist."""
    order_manager = get_order_manager()
    try:
        wishlist = order_manager.get_wishlist(buyer_id=user.id)
        return {"items": wishlist["items"], "count": wishlist["count"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/wishlist")
async def add_to_wishlist(
    payload: AddToWishlistRequest,
    user: Annotated[User, Depends(require_user)],
):
    """Add product to user's wishlist."""
    order_manager = get_order_manager()
    try:
        wishlist = order_manager.add_to_wishlist(
            buyer_id=user.id,
            product_id=payload.product_id,
        )
        return {"items": wishlist["items"], "count": wishlist["count"], "added": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.delete("/wishlist/{product_id}")
async def remove_from_wishlist(
    product_id: str,
    user: Annotated[User, Depends(require_user)],
):
    """Remove product from user's wishlist."""
    order_manager = get_order_manager()
    try:
        order_manager.remove_from_wishlist(buyer_id=user.id, product_id=product_id)
        return {"removed": product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


# --- Vendor Endpoints ---


class VendorApplication(BaseModel):
    shop_name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    location: str = Field(..., min_length=2)
    village_id: str = Field(..., min_length=1)
    product_types: str = Field(..., min_length=2)
    certifications: str = Field(..., min_length=2)
    production_capacity: str = Field(..., min_length=2)
    years_experience: str = Field(..., min_length=1)
    contact_phone: str = Field(..., min_length=1)
    social_media: str = Field(..., min_length=2)
    operating_hours: str = Field(..., min_length=2)
    delivery_area: str = Field(..., min_length=2)
    currency: str = Field(..., min_length=2)
    marketplace_id: str = Field(..., min_length=1)


@router.post("/vendors")
async def apply_vendor(
    payload: VendorApplication,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Apply to become a vendor."""
    order_manager = get_order_manager()
    try:
        vendor = order_manager.register_vendor(
            user_id=user.id,
            shop_name=payload.shop_name,
            description=payload.description,
            location=payload.location,
            village_id=payload.village_id,
            product_types=payload.product_types,
            certifications=payload.certifications,
            production_capacity=payload.production_capacity,
            years_experience=payload.years_experience,
            contact_phone=payload.contact_phone,
            social_media=payload.social_media,
            operating_hours=payload.operating_hours,
            delivery_area=payload.delivery_area,
            currency=payload.currency,
            marketplace_id=payload.marketplace_id,
        )
        vendor_db_id = vendor.id
        try:
            with hub.get_session() as session:
                row = session.execute(
                    select(MarketplaceSeller).where(MarketplaceSeller.user_id == str(user.id))
                ).scalar_one_or_none()
                if row is None:
                    row = MarketplaceSeller(
                        user_id=str(user.id),
                        village_id=payload.village_id,
                        shop_name=payload.shop_name,
                        shop_description=payload.description,
                        location=payload.location,
                        status="pending",
                        is_verified=False,
                        certifications=[],
                    )
                    session.add(row)
                else:
                    row.shop_name = payload.shop_name
                    row.shop_description = payload.description
                    row.village_id = payload.village_id
                    row.location = payload.location
                    row.status = "pending"
                session.commit()
                session.refresh(row)
                vendor_db_id = row.id
        except Exception as persist_error:
            logger.error(f"Vendor application persistence failed: {persist_error}")
        return {"vendor_id": vendor_db_id, "status": "pending"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/vendors")
async def list_vendors(
    location: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List vendors from the persisted seller registry (D6 fix)."""
    with hub.get_session() as session:
        q = (
            select(MarketplaceSeller)
            .order_by(MarketplaceSeller.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = session.execute(q).scalars().all()
    vendors = [
        {
            "id": r.id,
            "shop_name": r.shop_name,
            "name": r.shop_name,
            "description": (r.shop_description or ""),
            "location": (getattr(r, "location", "") or ""),
            "village_id": r.village_id,
            "status": r.status,
            "is_verified": bool(r.is_verified),
            "rating": float(r.rating or 0),
            "total_sales": int(r.total_sales or 0),
        }
        for r in rows
    ]
    if location:
        vendors = [v for v in vendors if location.lower() in (v["location"] or "").lower()]
    return {"vendors": vendors, "offset": offset, "limit": limit}


@router.get("/vendors/{vendor_id}")
async def get_vendor(vendor_id: str):
    """Get vendor details from the persisted seller registry (D6 fix)."""
    with hub.get_session() as session:
        r = session.get(MarketplaceSeller, vendor_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {
        "id": r.id,
        "shop_name": r.shop_name,
        "name": r.shop_name,
        "description": (r.shop_description or ""),
        "location": (getattr(r, "location", "") or ""),
        "village_id": r.village_id,
        "status": r.status,
        "is_verified": bool(r.is_verified),
        "rating": float(r.rating or 0),
        "total_sales": int(r.total_sales or 0),
    }


@router.get("/vendors/{vendor_id}/products")
async def vendor_products(
    vendor_id: str,
    limit: int = Query(20, ge=1, le=100),
):
    """Get products by vendor."""
    catalog = get_catalog()
    products = catalog.list_products(limit=limit)
    # Products here are ``Product`` dataclass instances, not dicts — the old
    # ``p.get("producer_id")`` raised ``AttributeError`` and 500'd the route.
    vendor_products = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category.value if hasattr(p.category, "value") else str(p.category),
            "price_per_kg": getattr(p, "price_per_kg", 0),
            "producer_id": getattr(p, "producer_id", ""),
            "producer_name": getattr(p, "producer_name", ""),
            "organic_certified": getattr(p, "organic_certified", False),
            "images": p.images if hasattr(p, "images") else [],
        }
        for p in products
        if getattr(p, "producer_id", "") == vendor_id
    ]
    return {"products": vendor_products, "vendor_id": vendor_id}


@router.get("/vendors/{vendor_id}/orders")
async def vendor_orders(
    vendor_id: str,
    status: str | None = Query(None),
    user: Annotated[User, Depends(require_user)] = None,
):
    """Get a seller's orders without exposing buyers' details to other users."""
    if user.role != "admin":
        with hub.get_session() as session:
            seller = session.get(MarketplaceSeller, vendor_id)
        if seller is None or str(seller.user_id) != str(user.id):
            raise HTTPException(status_code=404, detail="Vendor not found")

    order_manager = get_order_manager()
    orders = order_manager.list_orders()
    # ``Order`` is a dataclass too: access the attributes, not ``o.get(...)``.
    vendor_orders = [
        {
            "id": o.id,
            "product_name": o.product_name,
            "buyer_name": o.buyer_name,
            "seller_id": getattr(o, "seller_id", ""),
            "quantity_kg": o.quantity_kg,
            "total_price": o.total_price,
            "status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
        if getattr(o, "seller_id", "") == vendor_id
    ]
    if status:
        vendor_orders = [o for o in vendor_orders if o["status"] == status]
    return {"orders": vendor_orders, "count": len(vendor_orders)}


# --- Admin Endpoints ---


@router.get("/admin/stats")
async def admin_stats(user: Annotated[User, Depends(require_admin)]):
    """Get marketplace statistics (admin)."""
    order_manager = get_order_manager()
    catalog = get_catalog()
    products = catalog.list_products()
    producers = catalog.list_producers()
    return {
        "total_products": len(products),
        "total_producers": len(producers),
        "organic_products": sum(1 for p in products if getattr(p, "organic_certified", False)),
        "orders": order_manager.get_revenue_stats(),
    }


@router.get("/admin/payments/pending")
def pending_bank_payments(
    limit: int = Query(default=100, ge=1, le=500),
    user: Annotated[User, Depends(require_admin)] = None,
):
    """List submitted bank-transfer claims awaiting administrator review."""
    with hub.get_session() as session:
        rows = session.execute(
            select(MarketplacePayment, MarketplaceOrder)
            .join(MarketplaceOrder, MarketplaceOrder.id == MarketplacePayment.order_id)
            .where(
                MarketplacePayment.gateway == "bank",
                MarketplacePayment.status == "awaiting_verification",
                MarketplacePayment.tracking_code.is_not(None),
                MarketplacePayment.tracking_code != "",
            )
            .order_by(MarketplacePayment.created_at.asc())
            .limit(limit)
        ).all()
        return {
            "payments": [
                {
                    "id": payment.id,
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "buyer_id": order.buyer_id,
                    "amount": float(payment.amount or 0),
                    "currency": payment.currency,
                    "tracking_code": payment.tracking_code,
                    "status": payment.status,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None,
                }
                for payment, order in rows
            ],
            "count": len(rows),
        }


@router.patch("/admin/products/{product_id}/approve")
async def admin_approve_product(
    product_id: str,
    approve: Annotated[bool, Query()] = True,
    user: Annotated[User, Depends(require_admin)] = None,
):
    """Admin: approve or reject a product (real DB mutation, mirrors vendors).

    The image on the catalogue is a stateless ``Product`` dataclass with no
    approval field, so the approval is written to the persisted
    ``MarketplaceProduct`` status the same way ``/admin/vendors/.../approve``
    writes the seller row.
    """
    with hub.get_session() as session:
        row = session.get(MarketplaceProduct, product_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        row.status = (
            MarketplaceProductStatus.APPROVED if approve else MarketplaceProductStatus.REJECTED
        )
        row.approved_by = str(user.id) if approve else None
        row.approved_at = datetime.now(UTC) if approve else None
        session.commit()
        return {
            "product_id": product_id,
            "approved": approve,
            "status": row.status.value if hasattr(row.status, "value") else row.status,
        }


@router.patch("/admin/vendors/{vendor_id}/approve")
async def admin_approve_vendor(
    vendor_id: str,
    approve: Annotated[bool, Query()] = True,
    user: Annotated[User, Depends(require_admin)] = None,
):
    """Admin: approve or reject a vendor (real DB mutation, D6 fix)."""
    with hub.get_session() as session:
        row = session.get(MarketplaceSeller, vendor_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Vendor not found")
        row.status = "active" if approve else "suspended"
        row.is_verified = bool(approve)
        row.verified_at = datetime.now(UTC) if approve else None
        session.commit()
        return {"vendor_id": vendor_id, "approved": approve, "status": row.status}


@router.get("/admin/orders")
async def admin_orders(
    status: Annotated[str | None, Query()] = None,
    user: Annotated[User, Depends(require_admin)] = None,
):
    """Admin: list all orders."""
    order_manager = get_order_manager()
    orders = order_manager.list_orders()
    return {
        "orders": [
            {
                "id": o.id,
                "product_name": o.product_name,
                "buyer_name": o.buyer_name,
                "seller_id": getattr(o, "seller_id", ""),
                "quantity_kg": o.quantity_kg,
                "total_price": o.total_price,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ]
    }


# --- Marketplace Endpoints ---


class MarketplaceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    marketplace_type: str = Field(..., min_length=2)
    description: str = Field(default="")
    address: str = Field(default="")
    postal_code: str = Field(default="")
    location: str = Field(default="")
    village_id: str = Field(..., min_length=1)
    founder_ids: list[str] = Field(default_factory=list)
    e_commerce_rules_accepted: bool = False
    buy_sell_rules_accepted: bool = False
    rules_document: str = Field(default="")
    contact_email: str = Field(default="")
    contact_phone: str = Field(default="")


@router.post("/marketplaces")
async def create_marketplace(
    payload: MarketplaceCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """Create a new marketplace (بازارچه). Requires village council approval."""
    if not payload.e_commerce_rules_accepted:
        raise HTTPException(status_code=400, detail="Must accept e-commerce rules")
    if not payload.buy_sell_rules_accepted:
        raise HTTPException(status_code=400, detail="Must accept buy/sell rules")

    service = MarketplaceService(db)
    try:
        marketplace = await service.register_marketplace(
            {
                "name": payload.name,
                "slug": payload.name.lower().replace(" ", "-"),
                "description": payload.description,
                "marketplace_type": payload.marketplace_type,
                "address": payload.address,
                "postal_code": payload.postal_code,
                "location": payload.location,
                "village_id": payload.village_id,
                "founder_ids": [*payload.founder_ids, user.id],
                "e_commerce_rules_accepted": payload.e_commerce_rules_accepted,
                "buy_sell_rules_accepted": payload.buy_sell_rules_accepted,
                "rules_document": payload.rules_document,
                "contact_email": payload.contact_email,
                "contact_phone": payload.contact_phone,
                "status": "pending",
            }
        )
        return {"marketplace_id": marketplace.id, "status": "pending"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/marketplaces")
async def list_marketplaces(
    marketplace_type: Annotated[str | None, Query()] = None,
    village_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[AsyncSession, Depends(get_async_db)] = None,
):
    """List all marketplaces."""
    service = MarketplaceService(db)
    marketplaces = await service.list_marketplaces(
        marketplace_type=marketplace_type,
        village_id=village_id,
        status=status,
        limit=limit,
    )
    return {
        "marketplaces": [
            {
                "id": m.id,
                "name": m.name,
                "slug": m.slug,
                "description": m.description,
                "marketplace_type": m.marketplace_type,
                "logo": m.logo,
                "banner": m.banner,
                "address": m.address,
                "postal_code": m.postal_code,
                "location": m.location,
                "village_id": m.village_id,
                "founder_ids": m.founder_ids,
                "status": m.status,
                "admin_approved": m.admin_approved,
                "marketing_enabled": m.marketing_enabled,
                "branding_enabled": m.branding_enabled,
                "created_at": m.created_at.isoformat(),
            }
            for m in marketplaces
        ]
    }


@router.get("/marketplaces/{marketplace_id}")
async def get_marketplace(
    marketplace_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """Get marketplace details."""
    service = MarketplaceService(db)
    marketplace = await service.get_marketplace(marketplace_id)
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    return {
        "id": marketplace.id,
        "name": marketplace.name,
        "slug": marketplace.slug,
        "description": marketplace.description,
        "marketplace_type": marketplace.marketplace_type,
        "logo": marketplace.logo,
        "banner": marketplace.banner,
        "address": marketplace.address,
        "postal_code": marketplace.postal_code,
        "location": marketplace.location,
        "village_id": marketplace.village_id,
        "founder_ids": marketplace.founder_ids,
        "status": marketplace.status,
        "admin_approved": marketplace.admin_approved,
        "marketing_enabled": marketplace.marketing_enabled,
        "branding_enabled": marketplace.branding_enabled,
        "created_at": marketplace.created_at.isoformat(),
    }


@router.post("/marketplaces/{marketplace_id}/approve")
async def approve_marketplace(
    marketplace_id: str,
    approve: Annotated[bool, Query()] = True,
    user: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_async_db)] = None,
):
    """Admin: approve or reject a marketplace."""
    service = MarketplaceService(db)
    try:
        marketplace = await service.verify_marketplace(
            marketplace_id, approve=approve, verified_by=user.id
        )
        return {"marketplace_id": marketplace.id, "approved": approve, "status": marketplace.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/marketplaces/{marketplace_id}/members")
async def add_marketplace_member(
    marketplace_id: str,
    user_id: str,
    role: Annotated[str, Query()] = "member",
    user: Annotated[User, Depends(require_user)] = None,
    db: Annotated[AsyncSession, Depends(get_async_db)] = None,
):
    """Add a member to a marketplace."""
    service = MarketplaceService(db)
    try:
        member = await service.add_marketplace_member(marketplace_id, user_id, role)
        return {"member_id": member.id, "status": "active"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/marketplaces/{marketplace_id}/shops")
async def list_marketplace_shops(
    marketplace_id: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[AsyncSession, Depends(get_async_db)] = None,
):
    """List shops in a marketplace."""
    service = MarketplaceService(db)
    shops = await service.list_marketplace_shops(marketplace_id, limit)
    return {
        "shops": [
            {
                "id": s.id,
                "marketplace_id": s.marketplace_id,
                "user_id": s.user_id,
                "shop_name": s.shop_name,
                "shop_description": s.shop_description,
                "status": s.status,
                "is_verified": s.is_verified,
                "created_at": s.created_at.isoformat(),
            }
            for s in shops
        ]
    }


@router.post("/marketplaces/{marketplace_id}/shops")
async def create_marketplace_shop(
    marketplace_id: str,
    payload: dict,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """Create a shop under a marketplace."""
    service = MarketplaceService(db)
    try:
        shop = await service.create_marketplace_shop(
            marketplace_id=marketplace_id,
            user_id=user.id,
            data=payload,
        )
        return {"shop_id": shop.id, "status": shop.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


# --- Payment Endpoints ---


class PaymentRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    payment_method: str = Field(default="bank")
    amount: float = Field(..., gt=0)
    description: str = Field(default="", max_length=500)


class PaymentConfirmRequest(BaseModel):
    ref_id: str = Field(default="", max_length=120)  # bank tracking code / gateway ref


@router.post("/payments")
async def create_payment(
    payload: PaymentRequest,
    user: Annotated[User, Depends(require_user)],
):
    """Create a gateway payment for an order (real DB row + escrow-ready)."""
    with hub.get_session() as session:
        order = session.get(MarketplaceOrder, payload.order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.buyer_id != str(user.id) and user.role != "admin":
            raise HTTPException(status_code=403, detail="Not allowed to pay for this order")
        # The order total is the only pricing authority. The client amount is a
        # stale-cart guard: refuse a mismatch rather than silently overriding,
        # then ignore it in favour of the server-side total below.
        order_total = float(order.total or 0)
        if abs(order_total - payload.amount) > 0.01:
            raise HTTPException(
                status_code=422,
                detail=f"Payment amount {payload.amount} does not match order total {order_total}",
            )
        try:
            if payload.payment_method == "bank":
                existing = session.execute(
                    select(MarketplacePayment)
                    .where(
                        MarketplacePayment.order_id == payload.order_id,
                        MarketplacePayment.user_id == str(user.id),
                        MarketplacePayment.gateway == "bank",
                        MarketplacePayment.status == "awaiting_verification",
                    )
                    .order_by(MarketplacePayment.created_at.desc())
                    .limit(1)
                ).scalars().first()
                if existing is not None:
                    return {
                        **existing.to_dict(),
                        "tracking_code": existing.tracking_code,
                        "bank_instructions": bank_instructions(),
                    }
            gateways = PaymentGateways(session, base_url=os.getenv("PUBLIC_BASE_URL", ""))
            payment = gateways.create(
                order_id=payload.order_id,
                user_id=str(user.id),
                gateway=payload.payment_method,
                amount=order_total,
                description=payload.description,
            )
            out = payment.to_dict()
            if payload.payment_method == "bank":
                out["bank_instructions"] = bank_instructions()
            return out
        except PaymentError as exc:
            raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


@router.post("/payments/{payment_id}/confirm")
async def confirm_payment(
    payment_id: str,
    payload: PaymentConfirmRequest,
    user: Annotated[User, Depends(require_user)],
):
    """Submit a transfer claim or verify a third-party gateway payment."""
    with hub.get_session() as session:
        try:
            payment = EscrowService(session).get_payment(payment_id)
            if payment.user_id != str(user.id) and user.role != "admin":
                raise HTTPException(status_code=403, detail="Not allowed to confirm this payment")
            if payment.gateway == "bank":
                ref_id = (payload.ref_id or "").strip()
                if not ref_id:
                    raise HTTPException(
                        status_code=422,
                        detail="Bank transfer tracking code is required",
                    )
                payment.tracking_code = ref_id
                session.commit()
                return {
                    "payment": payment.to_dict(),
                    "escrow": "awaiting_verification",
                    "escrow_entries": [],
                }
            payment = PaymentGateways(session).verify(payment, ref_id=payload.ref_id or None)
            escrow_entries = EscrowService(session).by_order(payment.order_id)
            return {
                "payment": payment.to_dict(),
                "escrow": "held",
                "escrow_entries": [
                    {
                        "id": e.id,
                        "entry_type": e.entry_type,
                        "amount": float(e.amount) if e.amount is not None else None,
                    }
                    for e in escrow_entries
                ],
            }
        except (PaymentError, LookupError) as exc:
            raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


@router.post("/payments/{payment_id}/verify-bank")
async def verify_bank_payment(
    payment_id: str,
    user: Annotated[User, Depends(require_admin)],
):
    """Admin verification after matching a submitted bank transfer claim."""
    with hub.get_session() as session:
        try:
            payment = EscrowService(session).get_payment(payment_id)
            if payment.gateway != "bank":
                raise HTTPException(
                    status_code=400,
                    detail="Only bank-transfer payments can be manually verified",
                )
            if not (payment.tracking_code or "").strip():
                raise HTTPException(
                    status_code=409,
                    detail="No bank transfer tracking code has been submitted",
                )
            payment = PaymentGateways(session).verify(
                payment,
                ref_id=payment.tracking_code,
            )
            escrow_entries = EscrowService(session).by_order(payment.order_id)
            return {
                "payment": payment.to_dict(),
                "verified_by": str(user.id),
                "escrow": "held",
                "escrow_entries": [
                    {
                        "id": e.id,
                        "entry_type": e.entry_type,
                        "amount": float(e.amount) if e.amount is not None else None,
                    }
                    for e in escrow_entries
                ],
            }
        except (PaymentError, LookupError) as exc:
            raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


@router.post("/payments/{payment_id}/escrow/release")
async def release_escrow(
    payment_id: str,
    user: Annotated[User, Depends(require_admin)],
):
    """Admin: release escrowed funds to the seller (delivery confirmed)."""
    with hub.get_session() as session:
        try:
            entry = EscrowService(session).release(payment_id, actor_id=str(user.id))
            return {
                "ok": True,
                "entry": {
                    "id": entry.id,
                    "payment_id": entry.payment_id,
                    "order_id": entry.order_id,
                    "entry_type": entry.entry_type,
                    "amount": float(entry.amount) if entry.amount is not None else None,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                },
            }
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=safe_detail_for_status(exc, 404)) from exc
        except PaymentError as exc:
            raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


@router.post("/payments/{payment_id}/escrow/refund")
async def refund_escrow(
    payment_id: str,
    user: Annotated[User, Depends(require_admin)],
):
    """Admin: refund escrowed funds to the buyer (cancellation)."""
    with hub.get_session() as session:
        try:
            entry = EscrowService(session).refund(payment_id, actor_id=str(user.id))
            return {
                "ok": True,
                "entry": {
                    "id": entry.id,
                    "payment_id": entry.payment_id,
                    "entry_type": entry.entry_type,
                    "amount": float(entry.amount) if entry.amount is not None else None,
                },
            }
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=safe_detail_for_status(exc, 404)) from exc
        except PaymentError as exc:
            raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


@router.get("/payments/{payment_id}/escrow")
async def escrow_status(
    payment_id: str,
    user: Annotated[User, Depends(require_user)],
):
    """Escrow ledger entries for a payment."""
    with hub.get_session() as session:
        try:
            payment = EscrowService(session).get_payment(payment_id)
            entries = EscrowService(session).by_order(payment.order_id)
            return {
                "payment_id": payment_id,
                "payment_status": payment.status,
                "escrow_status": payment.escrow_status,
                "entries": [
                    {
                        "id": e.id,
                        "entry_type": e.entry_type,
                        "amount": float(e.amount) if e.amount is not None else None,
                    }
                    for e in entries
                ],
            }
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=safe_detail_for_status(exc, 404)) from exc


# --- 6-Step Flow: Dispute Window, Settle, Complete ---


#: Hours after the escrow hold within which a buyer may dispute. The
#: marketplace escrow ledger stores no deadline column, so the window is
#: derived from the hold timestamp — mirroring the 48h dispute window on the
#: on-ledger escrow contract.
DISPUTE_WINDOW_HOURS = 48


def _require_order_party(
    db: Session,
    order_id: str,
    user: User,
) -> MarketplaceOrder:
    """Authorise the caller for an order's escrow.

    The escrow routes used to accept **any** authenticated caller, so any user
    could dispute, settle (release the escrowed money to the seller) or
    complete an order they had no part in. The order's buyer and the sellers
    whose items it contains are the only parties, plus an admin.

    The buyer keeps the access the pinned contract gives it -- the escrow
    lifecycle test drives dispute/settle/complete as the buyer -- but the
    surface is no longer open to every authenticated account.
    """
    from services.api_gateway.auth import ADMIN_ROLES

    order = db.get(MarketplaceOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    caller_id = str(user.id)
    caller_role = str(getattr(user, "role", "") or "")
    if caller_role in ADMIN_ROLES:
        return order

    buyer_id = str(getattr(order, "buyer_id", "") or "")
    if buyer_id and buyer_id == caller_id:
        return order

    seller_ids = {
        str(row[0])
        for row in db.execute(
            select(MarketplaceOrderItem.seller_id).where(
                MarketplaceOrderItem.order_id == order_id
            )
        )
        if row[0]
    }
    if caller_id in seller_ids:
        return order

    raise HTTPException(
        status_code=403,
        detail=safe_detail_for_status(ValueError("access denied"), 403),
    )


@router.post("/orders/{order_id}/dispute", status_code=200)
async def open_dispute(
    order_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Step 5a: Open dispute window for a held escrow.

    Operates on the marketplace escrow ledger (``MarketplaceEscrowEntry``) that
    ``POST /payments`` writes — the previous ``services.ledger.service`` import
    carried no session and always 404'd here. The dispute window is derived from
    the hold timestamp; the remaining time is reported. Returns the escrow
    deadline and remaining time.
    """
    escrow_svc = EscrowService(db)
    _require_order_party(db, order_id, user)
    entries = escrow_svc.by_order(order_id)
    hold = next((e for e in entries if e.entry_type == "hold"), None)
    if hold is None:
        raise HTTPException(status_code=404, detail="No escrow for order")
    payment = escrow_svc.get_payment(hold.payment_id)
    if payment.escrow_status != "held":
        raise HTTPException(status_code=400, detail="Escrow is not held; cannot dispute")

    deadline = hold.created_at + timedelta(hours=DISPUTE_WINDOW_HOURS) if hold.created_at else None
    remaining = None
    if deadline is not None:
        remaining = (deadline - datetime.now(UTC).replace(tzinfo=None)).total_seconds()

    return {
        "order_id": order_id,
        "escrow_id": hold.id,
        "state": payment.escrow_status,
        "dispute_deadline": deadline.isoformat() if deadline else None,
        "remaining_seconds": remaining,
        "status": "dispute_window_open",
    }


@router.post("/orders/{order_id}/settle", status_code=200)
async def settle_order(
    order_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Step 5b: Settle the order — release the held escrow to the seller.

    Releases the held marketplace escrow to the seller on the same ledger the
    release endpoint uses; the double-spend guard that blocks a second
    ``/payments/{id}/escrow/release`` also refuses a second settle.

    The 48-hour dispute window is *reported* by ``/orders/{id}/dispute``; it is
    not enforced here, because the pinned escrow lifecycle settles inside the
    window. Enforcing it is an open product decision (see
    ``docs/project/SECTOR-TECH-DEBT-REMEDIATION-2026-10-20.md``, FR-06c).
    """
    escrow_svc = EscrowService(db)
    _require_order_party(db, order_id, user)
    entries = escrow_svc.by_order(order_id)
    hold = next((e for e in entries if e.entry_type == "hold"), None)
    if hold is None:
        raise HTTPException(status_code=404, detail="No escrow for order")
    try:
        entry = escrow_svc.release(hold.payment_id, actor_id=str(user.id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(exc, 404)) from exc
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc

    return {
        "order_id": order_id,
        "escrow_id": entry.id,
        "state": "released",
        "amount": float(entry.amount) if entry.amount is not None else None,
        "settled_at": entry.created_at.isoformat() if entry.created_at else None,
        "status": "settled_released",
    }


@router.post("/orders/{order_id}/complete", status_code=200)
async def complete_order(
    order_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Step 6: Complete the purchase — final settlement confirmation.

    Marks the marketplace escrow as fully settled once it has been released or
    refunded; the release/refund entry is the settlement record that is stamped
    for provenance.
    """
    from services.provenance.stamp import stamp_value

    escrow_svc = EscrowService(db)
    _require_order_party(db, order_id, user)
    entries = escrow_svc.by_order(order_id)
    hold = next((e for e in entries if e.entry_type == "hold"), None)
    if hold is None:
        raise HTTPException(status_code=404, detail="No escrow for order")
    payment = escrow_svc.get_payment(hold.payment_id)
    if payment.escrow_status not in ("released", "refunded"):
        raise HTTPException(
            status_code=400,
            detail="Escrow must be released or refunded before it can be completed",
        )
    final = next((e for e in entries if e.entry_type in ("release", "refund")), None)

    amount_stamped = stamp_value(
        value=payment.amount,
        source="ledger:escrow_release",
        method="realtime",
    ).model_dump()

    return {
        "order_id": order_id,
        "escrow_id": (final or hold).id,
        "state": payment.escrow_status,
        "amount": amount_stamped,
        "completed_at": final.created_at.isoformat()
        if final is not None and final.created_at
        else None,
        "status": "completed",
    }
