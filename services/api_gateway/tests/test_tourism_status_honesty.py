"""KN-01 — the tourism status payload must be honest and self-verifying.

P1 of `docs/project/PHASE_PLAN.md`. Before this fix, `GET
/api/v1/tourism/status` returned `status: "requires_setup"` and a "tables not
provisioned in Supabase" note, while the real guide/tour/booking lifecycle was
already served over the same prefix by ``services.tourism.api.router`` — a
payload that understated reality (the eco.md P-01/P-15 violation from the other
direction).

These tests pin the honest shape *and* bind it to the routes that actually
exist, so the claim cannot rot in either direction:

1. ``status`` is ``live`` and no ``requires_setup``/unprovisioned wording
   survives anywhere in the payload;
2. every advertised endpoint — and the four capability sub-paths — is a path of
   the **mounted gateway app** (``app.openapi()``), following the
   ``test_bridge_mounts.py::_assert_all_mounted`` pattern, so deleting the
   lifecycle mount at ``main.py`` fails this test instead of silently
   falsifying the payload;
3. the payload admits its own gaps (``not_yet_available`` is non-empty), so a
   roadmap item can never again be read as a live feature;
4. the table claim is checked against ``database.base.Base`` metadata, not
   against prose.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from database.base import Base
from services.api_gateway.routers import tourism_router
from services.tourism.api.router import router as live_router
from services.tourism.models import TourismBooking, TourismGuide, TourismTour

_STATUS_URL = "/api/v1/tourism/status"

#: The live lifecycle routes the payload's ``capabilities`` claims. The three
#: collection paths are also advertised in ``endpoints``; the sub-paths are the
#: verify/approve/confirm/complete actions named in the capability list.
_ADVERTISED_SUB_PATHS = (
    "/api/v1/tourism/guides/{guide_id}/verify",
    "/api/v1/tourism/tours/{tour_id}/approve",
    "/api/v1/tourism/bookings/{booking_id}/confirm-payment",
    "/api/v1/tourism/bookings/{booking_id}/complete",
)


def _openapi_paths() -> set[str]:
    """Paths of the real, mounted gateway app (lazy import — see bridge test)."""
    from services.api_gateway.main import app

    return set(app.openapi()["paths"].keys())


def _router_paths() -> set[str]:
    """Paths declared by the live lifecycle router module itself."""
    return {getattr(route, "path", "") for route in live_router.routes}


@pytest.fixture
async def status_client() -> AsyncClient:
    """A client for the status route alone (no auth, no DB needed)."""
    app = FastAPI()
    app.include_router(tourism_router.router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _flatten(payload, parent: str = ""):
    """Yield every string key and value in the nested payload."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield f"{parent}.{key}" if parent else str(key)
            yield from _flatten(value, f"{parent}.{key}" if parent else str(key))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            yield from _flatten(item, f"{parent}[{index}]")
    elif isinstance(payload, str):
        yield payload


async def test_status_is_live(status_client: AsyncClient) -> None:
    response = await status_client.get(_STATUS_URL)
    assert response.status_code == 200
    assert response.json()["status"] == "live"


async def test_no_stub_or_unprovisioned_wording_survives(status_client: AsyncClient) -> None:
    payload = (await status_client.get(_STATUS_URL)).json()
    banned = ("requires_setup", "آماده است؛ جداول دیتابیس هنوز", "not provisioned")
    for text in _flatten(payload):
        for phrase in banned:
            assert phrase not in text, f"stale stub wording {phrase!r} in {text!r}"


async def test_advertised_endpoints_are_mounted_gateway_paths(status_client: AsyncClient) -> None:
    """The payload is only allowed to advertise what the *app* serves.

    Binding to ``app.openapi()`` (not to the router object) is what makes the
    payload fail when the mount at ``main.py`` is removed — the failure mode
    this test exists for.
    """
    payload = (await status_client.get(_STATUS_URL)).json()
    mounted = _openapi_paths()
    for name, path in payload["endpoints"].items():
        assert path in mounted, f"{name} advertises {path}, which the gateway does not serve"


def test_advertised_capability_sub_paths_are_mounted() -> None:
    mounted = _openapi_paths()
    missing = [path for path in _ADVERTISED_SUB_PATHS if path not in mounted]
    assert not missing, f"capability sub-paths not mounted: {missing}"


async def test_payload_admits_its_gaps(status_client: AsyncClient) -> None:
    payload = (await status_client.get(_STATUS_URL)).json()
    gaps = payload["not_yet_available"]
    assert isinstance(gaps, list) and gaps, "payload must name what is not yet available"
    assert all(isinstance(item, str) and item.strip() for item in gaps)


async def test_table_claim_matches_the_shared_base_metadata(status_client: AsyncClient) -> None:
    tables = {model.__table__.name for model in (TourismGuide, TourismTour, TourismBooking)}
    assert tables <= set(Base.metadata.tables), (
        "the payload claims shared-Base tables; the models must be registered there"
    )


def test_live_router_declares_the_lifecycle() -> None:
    """Guards the guard: the mount assertions above must have something to bind to."""
    router_paths = _router_paths()
    for path in (
        "/api/v1/tourism/guides",
        "/api/v1/tourism/tours",
        "/api/v1/tourism/bookings",
        *_ADVERTISED_SUB_PATHS,
    ):
        assert path in router_paths, f"{path} is not declared by the live router"
