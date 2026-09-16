from sqlalchemy import select
"""API endpoints for Marketplace."""

import contextlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_user, require_admin
from services.marketplace.models import (
    OrderStatus,
    Product,
    ProductCategory,
    Marketplace,
    MarketplaceMember,
    MarketplaceSeller,
)
from services.marketplace.order_management import get_order_manager
from services.marketplace.product_catalog import get_catalog
from services.marketplace.traceability import get_traceability
from services.marketplace.service import get_marketplace_service
from services.business_modules.carbon import get_tokenization_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/marketplace", tags=["Marketplace"])


def get_db():
    with hub.get_session() as session:
        yield session


# --- Request Models ---


class OrderRequest(BaseModel):
    product_id: str
    buyer_name: str = Field(..., min_length=1, max_length=100)
    quantity_kg: float = Field(..., gt=0)


# --- Product Endpoints ---


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    category: str = Field(..., min_length=2)
    price: float = Field(..., gt=0)
    village_id: str = Field(..., min_length=1)
    description: str = Field(default='', max_length=2000)
    stock: int = Field(default=0, ge=0)
    unit: str = Field(default='kg')
    images: list[str] = Field(default_factory=list)


@router.get("/products")
def list_products(
    category: str | None = None,
    organic_only: bool = False,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 50,
):
    """List marketplace products with filters."""
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
                "slug": p.slug if hasattr(p, 'slug') else '',
                "category": p.category.value if hasattr(p.category, 'value') else str(p.category),
                "description": p.description if hasattr(p, 'description') else '',
                "price_per_kg": p.price_per_kg if hasattr(p, 'price_per_kg') else getattr(p, 'price', 0),
                "quantity_available_kg": p.quantity_available_kg if hasattr(p, 'quantity_available_kg') else getattr(p, 'stock', 0),
                "organic_certified": p.organic_certified if hasattr(p, 'organic_certified') else False,
                "producer_name": p.producer_name,
                "origin_location": p.origin_location,
                "traceability_code": p.traceability_code,
                "images": p.images if hasattr(p, 'images') else [],
            }
            for p in products
        ],
        "count": len(products),
    }


@router.post("/products")
async def create_product(
    payload: ProductCreateRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
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
                origin_location="",
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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products/search")
def search_products(q: str):
    """Search products by keyword."""
    catalog = get_catalog()
    results = catalog.search_products(q)

    return {
        "query": q,
        "results": [{"id": p.id, "name": p.name, "price_per_kg": p.price_per_kg} for p in results],
        "count": len(results),
    }


@router.get("/products/{product_id}")
def get_product(product_id: str):
    """Get product details."""
    catalog = get_catalog()
    product = catalog.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

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
        "images": product.images if hasattr(product, 'images') else [],
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
    files: list[UploadFile] = File(...),
    user: User = Depends(require_user),
):
    """Upload images for a product."""
    catalog = get_catalog()
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

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
    existing_images = getattr(product, 'images', [])
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


@router.post("/orders")
def create_order(payload: OrderRequest, user: User = Depends(require_user)):
    """Create a new order."""
    manager = get_order_manager()
    catalog = get_catalog()

    # Get product to find seller
    product = catalog.get_product(payload.product_id)
    seller_id = product.producer_id if product else ""

    try:
        order = manager.create_order(
            product_id=payload.product_id,
            buyer_name=payload.buyer_name,
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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders")
def list_orders(status: str | None = None):
    """List orders."""
    manager = get_order_manager()

    status_enum = None
    if status:
        with contextlib.suppress(ValueError):
            status_enum = OrderStatus(status)

    orders = manager.list_orders(status=status_enum)

    return {
        "orders": [
            {
                "id": o.id,
                "product_name": o.product_name,
                "buyer_name": o.buyer_name,
                "seller_id": getattr(o, 'seller_id', ''),
                "quantity_kg": o.quantity_kg,
                "total_price": o.total_price,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
        "count": len(orders),
    }


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str, user: User = Depends(require_user)):
    """Confirm an order."""
    manager = get_order_manager()
    if manager.confirm_order(order_id):
        return {"status": "confirmed", "order_id": order_id}
    raise HTTPException(status_code=400, detail="Cannot confirm order")


@router.get("/orders/{order_id}/track")
def track_order(order_id: str):
    """Get order tracking timeline."""
    manager = get_order_manager()
    order = manager.get_order(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

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
        timeline.append({
            "timestamp": order.updated_at.isoformat() if hasattr(order, 'updated_at') else order.created_at.isoformat(),
            "status": "confirmed",
            "title": "سفارش تایید شد",
            "description": "فروشنده سفارش را تایید کرد و در حال آماده‌سازی است",
        })

    if order.status in ["shipped", "delivered"]:
        timeline.append({
            "timestamp": order.updated_at.isoformat() if hasattr(order, 'updated_at') else order.created_at.isoformat(),
            "status": "shipped",
            "title": "ارسال شد",
            "description": "سفارش توسط پست/باربری ارسال شد",
        })

    if order.status == "delivered":
        timeline.append({
            "timestamp": order.updated_at.isoformat() if hasattr(order, 'updated_at') else order.created_at.isoformat(),
            "status": "delivered",
            "title": "تحویل داده شد",
            "description": "سفارش به مقصد تحویل داده شد",
        })

    if order.status == "cancelled":
        timeline.append({
            "timestamp": order.updated_at.isoformat() if hasattr(order, 'updated_at') else order.created_at.isoformat(),
            "status": "cancelled",
            "title": "لغو شد",
            "description": "سفارش لغو گردید",
        })

    return {
        "order_id": order.id,
        "order_number": getattr(order, 'order_number', order.id),
        "current_status": order.status.value if hasattr(order.status, 'value') else order.status,
        "timeline": timeline,
    }


@router.get("/stats")
def marketplace_stats():
    """Get marketplace statistics."""
    manager = get_order_manager()
    catalog = get_catalog()

    products = catalog.list_products()
    producers = catalog.list_producers()

    return {
        "total_products": len(products),
        "total_producers": len(producers),
        "organic_products": sum(1 for p in products if p.organic_certified),
        "orders": manager.get_revenue_stats(),
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
    user: User = Depends(require_user),
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
        raise HTTPException(status_code=400, detail=str(e))

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
def get_product_carbon_credits(product_id: str, user: User = Depends(require_user)):
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


@router.post("/cart")
async def add_to_cart(
    payload: AddToCartRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Add items to user's cart."""
    catalog = get_catalog()
    order_manager = get_order_manager()
    try:
        cart = order_manager.add_to_cart(
            buyer_id=user.id,
            items=[{"product_id": i.product_id, "quantity": i.quantity} for i in payload.items],
        )
        return {"cart_id": cart.id, "items": cart.items, "total_items": cart.total_items}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cart")
async def get_cart(user: User = Depends(require_user)):
    """Get user's current cart."""
    order_manager = get_order_manager()
    try:
        cart = order_manager.get_cart(buyer_id=user.id)
        if not cart:
            return {"cart_id": None, "items": [], "total_items": 0, "subtotal": 0}
        return {
            "cart_id": cart.id,
            "items": cart.items,
            "total_items": cart.total_items,
            "subtotal": cart.subtotal,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cart/{product_id}")
async def remove_from_cart(
    product_id: str,
    user: User = Depends(require_user),
):
    """Remove item from cart."""
    order_manager = get_order_manager()
    try:
        order_manager.remove_from_cart(buyer_id=user.id, product_id=product_id)
        return {"removed": product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., gt=0, le=100)


@router.patch("/cart/{product_id}")
async def update_cart_item(
    product_id: str,
    payload: UpdateCartItemRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Update item quantity in cart."""
    order_manager = get_order_manager()
    try:
        cart = order_manager.update_cart_item(
            buyer_id=user.id,
            product_id=product_id,
            quantity=payload.quantity,
        )
        return {"cart_id": cart.id, "items": cart.items, "total_items": cart.total_items}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Wishlist Endpoints ---


class AddToWishlistRequest(BaseModel):
    product_id: str = Field(..., min_length=1)


@router.get("/wishlist")
async def get_wishlist(user: User = Depends(require_user)):
    """Get user's wishlist."""
    order_manager = get_order_manager()
    try:
        wishlist = order_manager.get_wishlist(buyer_id=user.id)
        return {"items": wishlist["items"], "count": wishlist["count"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wishlist")
async def add_to_wishlist(
    payload: AddToWishlistRequest,
    user: User = Depends(require_user),
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
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/wishlist/{product_id}")
async def remove_from_wishlist(
    product_id: str,
    user: User = Depends(require_user),
):
    """Remove product from user's wishlist."""
    order_manager = get_order_manager()
    try:
        order_manager.remove_from_wishlist(buyer_id=user.id, product_id=product_id)
        return {"removed": product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
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
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vendors")
async def list_vendors(
    location: Optional[str] = Query(None, max_length=100),
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
    vendor_products = [p for p in products if p.get("producer_id") == vendor_id]
    return {"products": vendor_products, "vendor_id": vendor_id}


@router.get("/vendors/{vendor_id}/orders")
async def vendor_orders(
    vendor_id: str,
    status: Optional[str] = Query(None),
):
    """Get orders for a vendor."""
    order_manager = get_order_manager()
    orders = order_manager.list_orders()
    # Filter by vendor (seller_id)
    vendor_orders = [o for o in orders if o.get("seller_id") == vendor_id]
    if status:
        vendor_orders = [o for o in vendor_orders if o.get("status") == status]
    return {"orders": vendor_orders, "count": len(vendor_orders)}


# --- Admin Endpoints ---


@router.get("/admin/stats")
async def admin_stats(user: User = Depends(require_admin)):
    """Get marketplace statistics (admin)."""
    order_manager = get_order_manager()
    catalog = get_catalog()
    products = catalog.list_products()
    producers = catalog.list_producers()
    return {
        "total_products": len(products),
        "total_producers": len(producers),
        "organic_products": sum(1 for p in products if p.get("organic_certified")),
        "orders": order_manager.get_revenue_stats(),
    }


@router.patch("/admin/products/{product_id}/approve")
async def admin_approve_product(
    product_id: str,
    approve: bool = Query(True),
    user: User = Depends(require_admin),
):
    """Admin: approve or reject a product."""
    catalog = get_catalog()
    product = catalog.get_product(product_id) if hasattr(catalog, "get_product") else None
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product_id": product_id, "approved": approve, "status": "approved" if approve else "rejected"}

@router.patch("/admin/vendors/{vendor_id}/approve")
async def admin_approve_vendor(
    vendor_id: str,
    approve: bool = Query(True),
    user: User = Depends(require_admin),
):
    """Admin: approve or reject a vendor (real DB mutation, D6 fix)."""
    with hub.get_session() as session:
        row = session.get(MarketplaceSeller, vendor_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Vendor not found")
        row.status = "active" if approve else "suspended"
        row.is_verified = bool(approve)
        row.verified_at = datetime.now(timezone.utc) if approve else None
        session.commit()
        return {"vendor_id": vendor_id, "approved": approve, "status": row.status}


@router.get("/admin/orders")
async def admin_orders(
    status: Optional[str] = Query(None),
    user: User = Depends(require_admin),
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
                "seller_id": getattr(o, 'seller_id', ''),
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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Create a new marketplace (بازارچه). Requires village council approval."""
    if not payload.e_commerce_rules_accepted:
        raise HTTPException(status_code=400, detail="Must accept e-commerce rules")
    if not payload.buy_sell_rules_accepted:
        raise HTTPException(status_code=400, detail="Must accept buy/sell rules")

    service = get_marketplace_service(db)
    try:
        marketplace = await service.register_marketplace({
            "name": payload.name,
            "slug": payload.name.lower().replace(" ", "-"),
            "description": payload.description,
            "marketplace_type": payload.marketplace_type,
            "address": payload.address,
            "postal_code": payload.postal_code,
            "location": payload.location,
            "village_id": payload.village_id,
            "founder_ids": payload.founder_ids + [user.id],
            "e_commerce_rules_accepted": payload.e_commerce_rules_accepted,
            "buy_sell_rules_accepted": payload.buy_sell_rules_accepted,
            "rules_document": payload.rules_document,
            "contact_email": payload.contact_email,
            "contact_phone": payload.contact_phone,
            "status": "pending",
        })
        return {"marketplace_id": marketplace.id, "status": "pending"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/marketplaces")
async def list_marketplaces(
    marketplace_type: Optional[str] = Query(None),
    village_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """List all marketplaces."""
    service = get_marketplace_service(db)
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
async def get_marketplace(marketplace_id: str):
    """Get marketplace details."""
    service = get_marketplace_service(db)
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
    approve: bool = Query(True),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: approve or reject a marketplace."""
    service = get_marketplace_service(db)
    try:
        marketplace = await service.verify_marketplace(marketplace_id, approve=approve, verified_by=user.id)
        return {"marketplace_id": marketplace.id, "approved": approve, "status": marketplace.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/marketplaces/{marketplace_id}/members")
async def add_marketplace_member(
    marketplace_id: str,
    user_id: str,
    role: str = Query("member"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Add a member to a marketplace."""
    service = get_marketplace_service(db)
    try:
        member = await service.add_marketplace_member(marketplace_id, user_id, role)
        return {"member_id": member.id, "status": "active"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/marketplaces/{marketplace_id}/shops")
async def list_marketplace_shops(
    marketplace_id: str,
    limit: int = Query(50, ge=1, le=100),
):
    """List shops in a marketplace."""
    service = get_marketplace_service(db)
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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Create a shop under a marketplace."""
    service = get_marketplace_service(db)
    try:
        shop = await service.create_marketplace_shop(
            marketplace_id=marketplace_id,
            user_id=user.id,
            data=payload,
        )
        return {"shop_id": shop.id, "status": shop.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Payment Endpoints ---


class PaymentRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    payment_method: str = Field(default="wallet")
    amount: float = Field(..., gt=0)


@router.post("/payments")
async def create_payment(
    payload: PaymentRequest,
    user: User = Depends(require_user),
):
    """Create a payment for an order."""
    return {"payment_id": f"pay_{payload.order_id}", "status": "pending", "amount": payload.amount}


@router.post("/payments/{payment_id}/confirm")
async def confirm_payment(
    payment_id: str,
    user: User = Depends(require_user),
):
    """Confirm a payment."""
    return {"payment_id": payment_id, "status": "confirmed"}