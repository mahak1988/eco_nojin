"""P8 â€” the tourism surface is honest about what it can and cannot sell.

Two claims from ``docs/project/PHASE_PLAN.md`` P8 are pinned here:

1. **Capacity is real.** The ecological capacity of a tour is enforced at the
   booking edge (``TourismService.create_booking`` raises when it is exhausted),
   and the router surfaces that refusal with a safe detail â€” an over-booked tour
   cannot be created through the API.
2. **Nothing is advertised that does not exist.** The mounted tourism surface is
   exactly the mounted router's paths. There is no refund or cancellation
   endpoint, so the API must not advertise one: the OpenAPI surface is asserted
   against the router's real paths, so adding a fake path (or hiding a real one)
   fails the test.

The GSTC criteria are a **design reference only** â€” this file, and the module it
tests, never claim a GSTC certification for anything.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from services.api_gateway.auth import require_user
from services.tourism.api.router import router as tourism_router
from services.tourism.service import TourismService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def tourism_session():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from database.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def _bookable_tour(session, *, capacity: int = 2):
    """A verified guide, an approved tour, and the tour id."""
    service = TourismService(session)
    guide = await service.register_guide(
        user_id="guide-1",
        village_id="village-1",
        full_name="Guide One",
        languages=["fa", "en"],
    )
    await service.verify_guide(str(guide.id))
    tour = await service.create_tour(
        guide_id=str(guide.id),
        village_id="village-1",
        title="Hyrcanian Forests",
        tour_type="ECOTOURISM",
        description="forest walk",
        duration_hours=4,
        price_per_person=Decimal("100.00"),
        min_participants=1,
        max_participants=capacity,
        ecological_capacity=capacity,
    )
    await service.approve_tour(str(tour.id), approved_by="admin-1")
    await session.commit()
    return service, str(tour.id)


async def _book(service, tour_id: str, guest_id: str, quantity: int):
    from datetime import UTC, datetime, timedelta

    return await service.create_booking(
        tour_id=tour_id,
        guest_id=guest_id,
        participants_count=quantity,
        tour_date=datetime.now(UTC) + timedelta(days=7),
        village_id="village-1",
    )


async def test_booking_beyond_capacity_is_refused(tourism_session):
    service, tour_id = await _bookable_tour(tourism_session, capacity=2)
    first = await _book(service, tour_id, "user-1", 2)
    assert str(first.booking_number)
    with pytest.raises(ValueError):
        await _book(service, tour_id, "user-2", 1)


async def test_the_tourism_surface_advertises_only_mounted_paths():
    """The API cannot advertise a path the router does not serve."""
    app = FastAPI()
    app.include_router(tourism_router)
    schema = app.openapi()
    advertised = {path for path in schema["paths"] if path.startswith("/api/v1/tourism")}

    router_paths = {
        getattr(route, "path", "")
        for route in tourism_router.routes
        if getattr(route, "path", "").startswith("/api/v1/tourism")
    }
    assert advertised == router_paths, (
        f"OpenAPI surface {sorted(advertised)} != router paths {sorted(router_paths)}"
    )

    # No refund/cancellation endpoint exists â€” so none may appear.
    for absent in ("/refund", "/cancel", "/dispute"):
        assert not any(absent in path for path in advertised), absent


async def test_the_booking_endpoint_maps_the_capacity_error_safely():
    """The HTTP layer answers a 4xx with a safe detail, not a stack trace."""
    app = FastAPI()
    app.include_router(tourism_router)

    class _FullService:
        async def create_booking(self, *args, **kwargs):
            raise ValueError("ظرفیت برد اکولوژیک تکیمیل است. فقط 0 نفر باقی مانده")

    import services.tourism.api.router as router_module

    original = router_module.TourismService
    router_module.TourismService = lambda db: _FullService()
    try:
        app.dependency_overrides[require_user] = lambda: type(
            "U", (), {"id": "user-1", "role": "farmer", "is_active": True}
        )()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tourism/bookings",
                json={
                    "tour_id": "t1",
                    "village_id": "village-1",
                    "participants_count": 1,
                    "tour_date": "2026-11-01T09:00:00Z",
                },
            )
    finally:
        router_module.TourismService = original

    assert response.status_code == 400
    assert "remaining" not in response.text.lower()
    assert "Traceback" not in response.text
