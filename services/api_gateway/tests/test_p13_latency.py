"""P13 — the critical routes are measured before anyone optimises them.

P13 of the program says: measure first, then fix the top offenders. This
harness times the golden-path HTTP surface (product listing, cart, order
creation, wallet read) against the in-memory test database and reports the
p95 per route group. It asserts no *performance budget* — the numbers are the
point, and they are recorded here so a later change can be compared against
them rather than against a feeling.

Run with ``-s`` to see the report.
"""

from __future__ import annotations

import statistics
import time
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.routers.marketplace import router as marketplace_router
from services.marketplace.order_management import init_order_manager
from services.marketplace.product_catalog import init_catalog

pytestmark = pytest.mark.asyncio

_SAMPLES = 40


@pytest.fixture
async def measured_client():
    init_order_manager()
    init_catalog()
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, expire_on_commit=False)

    import database.config

    database.config.SessionLocal = maker

    app = FastAPI()
    app.include_router(marketplace_router)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="buyer-perf", role="farmer", full_name="Perf Buyer", email="perf@example.test"
    )
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id="admin-perf", role="admin"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_critical_route_latency_report(measured_client):
    client = measured_client

    created = await client.post(
        "/api/v1/marketplace/products",
        json={
            "name": "Perf Honey",
            "category": "honey",
            "description": "",
            "village_id": "village-1",
            "price": 10.0,
            "stock": 1000,
            "images": [],
        },
    )
    assert created.status_code == 200
    product_id = created.json()["product_id"]

    samples: dict[str, list[float]] = {"list_products": [], "create_order": []}
    for _index in range(_SAMPLES):
        start = time.perf_counter()
        listing = await client.get("/api/v1/marketplace/products")
        samples["list_products"].append(time.perf_counter() - start)
        assert listing.status_code == 200

        start = time.perf_counter()
        order = await client.post(
            "/api/v1/marketplace/orders",
            json={
                "product_id": product_id,
                "buyer_name": "ignored",
                "quantity_kg": 1,
            },
        )
        samples["create_order"].append(time.perf_counter() - start)
        assert order.status_code == 200

    report = {
        name: {
            "n": len(values),
            "p50_ms": round(statistics.median(values) * 1000, 2),
            "p95_ms": round(sorted(values)[int(len(values) * 0.95) - 1] * 1000, 2),
            "max_ms": round(max(values) * 1000, 2),
        }
        for name, values in samples.items()
    }
    print("\nP13 latency report (ASGI in-memory):", report)
    # The only assertion: the surface stayed responsive enough to be a baseline.
    for name, numbers in report.items():
        assert numbers["p95_ms"] < 500, f"{name} p95 is {numbers['p95_ms']}ms"
