"""HTTP regression tests for the ``/api/v1/land`` write guards.

The ASVS V4 access-control matrix counted the five land mutating routes among
the sixteen unguarded write routes. They are not a data-exposure risk on their
own -- the analysis is compute over a caller-supplied DEM and the service holds
no tenant rows -- but each one mutates an in-process ``LandService`` singleton
that every caller shares, so an anonymous writer could exhaust or corrupt it
for everyone. ``require_user`` is the same guard the marketplace and village
hubs put on their authenticated write paths, and is the minimum the matrix
requires.

Reads stay public (``GET /profiles`` and ``GET /profiles/{id}`` are not
guarded), which is what the module docstring of
``services/api_gateway/routers/land.py`` promises.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from services.api_gateway.auth import get_current_user
from services.api_gateway.routers.land import router

pytestmark = pytest.mark.asyncio

#: The five mutating routes. (method, path, request body)
_LAND_WRITE_ROUTES = (
    ("POST", "/api/v1/land/profiles", {"name": "n", "lat": 1.0, "lon": 2.0}),
    ("DELETE", "/api/v1/land/profiles/{profile_id}", None),
    ("POST", "/api/v1/land/profiles/{profile_id}/terrain-analysis", {"dem": [[1.0]]}),
    ("POST", "/api/v1/land/profiles/{profile_id}/drainage-analysis", {"dem": [[1.0]]}),
    ("POST", "/api/v1/land/profiles/{profile_id}/capability-assessment", None),
)


def _build_app(*, authenticate: bool):
    app = FastAPI()
    app.include_router(router)
    if authenticate:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="farmer-1", role="farmer"
        )
    return app


async def _request(app, method: str, path: str, payload: dict | None = None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path, json=payload)


@pytest.mark.parametrize("method,path,payload", _LAND_WRITE_ROUTES)
async def test_every_write_route_refuses_an_anonymous_caller(method, path, payload):
    response = await _request(_build_app(authenticate=False), method, path, payload)

    assert response.status_code == 401, response.text


@pytest.mark.parametrize("method,path,payload", _LAND_WRITE_ROUTES)
async def test_every_write_route_admits_an_authenticated_caller(method, path, payload):
    response = await _request(_build_app(authenticate=True), method, path, payload)

    # 422 = reached the handler and failed body validation, which is the point:
    # the caller passed the auth dependency. Never 401/403.
    assert response.status_code in (200, 201, 204, 400, 404, 422), response.text


async def test_reads_stay_public():
    app = _build_app(authenticate=False)

    listing = await _request(app, "GET", "/api/v1/land/profiles")
    detail = await _request(app, "GET", "/api/v1/land/profiles/some-profile")

    assert listing.status_code in (200, 500), listing.text
    assert detail.status_code in (200, 404), detail.text
