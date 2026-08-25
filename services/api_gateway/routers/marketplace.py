"""API endpoints for Marketplace."""

import contextlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.marketplace.models import OrderStatus, ProductCategory
from services.marketplace.order_management import get_order_manager
from services.marketplace.product_catalog import get_catalog
from services.marketplace.traceability import get_traceability

router = APIRouter(prefix="/api/v1/marketplace", tags=["Marketplace"])


# --- Request Models ---


class OrderRequest(BaseModel):
    product_id: str
    buyer_name: str = Field(..., min_length=1, max_length=100)
    quantity_kg: float = Field(..., gt=0)


# --- Product Endpoints ---


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
                "category": p.category.value,
                "price_per_kg": p.price_per_kg,
                "quantity_available_kg": p.quantity_available_kg,
                "organic_certified": p.organic_certified,
                "producer_name": p.producer_name,
                "origin_location": p.origin_location,
                "traceability_code": p.traceability_code,
            }
            for p in products
        ],
        "count": len(products),
    }


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
def create_order(payload: OrderRequest):
    """Create a new order."""
    manager = get_order_manager()

    try:
        order = manager.create_order(
            product_id=payload.product_id,
            buyer_name=payload.buyer_name,
            quantity_kg=payload.quantity_kg,
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
def confirm_order(order_id: str):
    """Confirm an order."""
    manager = get_order_manager()
    if manager.confirm_order(order_id):
        return {"status": "confirmed", "order_id": order_id}
    raise HTTPException(status_code=400, detail="Cannot confirm order")


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
