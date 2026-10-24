from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import services.api_gateway.routers.marketplace as marketplace_module
from services.api_gateway.auth import require_user


@pytest.mark.asyncio
async def test_create_product_persists_submitted_village_as_origin(monkeypatch):
    created_products = []

    class FakeCatalog:
        def add_product(self, product):
            created_products.append(product)
            return product.id

    monkeypatch.setattr(marketplace_module, "get_catalog", lambda: FakeCatalog())
    app = FastAPI()
    app.include_router(marketplace_module.router)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="user-1",
        role="regular",
        full_name="Test producer",
        email="producer@example.test",
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/marketplace/products",
            json={
                "name": "Local honey",
                "category": "honey",
                "price": 12.5,
                "village_id": "village-42",
                "description": "Harvested locally",
                "stock": 8,
            },
        )

    assert response.status_code == 200, response.text
    assert len(created_products) == 1
    assert created_products[0].origin_location == "village-42"
