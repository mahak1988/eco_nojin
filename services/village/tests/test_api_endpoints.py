"""P7/P5 — the governance endpoints the frontend actually calls."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.api_gateway.auth import require_user
from services.village import api as governance_api
from services.village.api import router as governance_router
from services.village.models import CommunitySpace
from services.village.service import VillageGovernanceService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seeded():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with maker() as session:
        service = VillageGovernanceService(session)
        mine = await service.register_space(
            village_id="village-1", name="Deh Ali", actor_id="user-1"
        )
        theirs = await service.register_space(
            village_id="village-2", name="Deh Shahri", actor_id="user-2"
        )
        group = await service.form_working_group(
            str(mine.id), actor_id="user-1", mandate_ref="2026"
        )
        await service.add_member(
            str(group.id), user_id="user-1", display_name="Ali", role="coordinator"
        )
        await session.commit()
        # the public centroid is the only coordinate the map may see
        space = (
            await session.execute(
                select(CommunitySpace).where(CommunitySpace.id == mine.id)
            )
        ).scalar_one()
        space.public_centroid = "35.6942,51.4251"
        await session.commit()
    yield maker, str(mine.id), str(theirs.id)
    await engine.dispose()


def _client(maker, *, user_id: str, role: str = "farmer"):
    app = FastAPI()
    app.include_router(governance_router)
    app.dependency_overrides[governance_api.get_db] = _session_factory(maker)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id=user_id, role=role, is_active=True
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _session_factory(maker):
    """A dependency that yields ONE session per request (FastAPI closes it)."""

    async def _dependency():
        session = maker()
        try:
            yield session
        finally:
            await session.close()

    return _dependency


def _admin_client(maker):
    """A client whose caller passes every ``require_roles`` dependency.

    ``require_roles`` returns a fresh closure per call, so the override is keyed
    by that closure's name on each route (never on the route's ``get_db``).
    """
    app = FastAPI()
    app.include_router(governance_router)
    app.dependency_overrides[governance_api.get_db] = _session_factory(maker)
    admin = SimpleNamespace(id="admin-1", role="admin", is_active=True)
    app.dependency_overrides[require_user] = lambda: admin
    for route in governance_router.routes:
        for dependency in getattr(route.dependant, "dependencies", []):
            if getattr(dependency.call, "__name__", "") == "_dependency":
                app.dependency_overrides[dependency.call] = lambda: admin
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_activate_of_an_unknown_space_is_404(seeded):
    """Like every sibling route, an unknown space is a 404, not a conflict."""
    maker, _mine, _theirs = seeded
    async with _admin_client(maker) as client:
        response = await client.post(
            "/api/v1/village-governance/spaces/no-such-space/activate"
        )
    assert response.status_code == 404


async def test_list_returns_only_the_callers_spaces(seeded):
    maker, mine, _theirs = seeded
    async with _client(maker, user_id="user-1") as client:
        response = await client.get("/api/v1/village-governance/spaces")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [mine]


async def test_an_admin_sees_all_spaces(seeded):
    maker, mine, theirs = seeded
    async with _client(maker, user_id="admin-1", role="admin") as client:
        response = await client.get("/api/v1/village-governance/spaces")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert ids == {mine, theirs}


async def test_the_detail_exposes_the_centroid_but_never_the_boundary(seeded):
    maker, mine, _theirs = seeded
    app = FastAPI()
    app.include_router(governance_router)
    app.dependency_overrides[governance_api.get_db] = _session_factory(maker)
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="user-1", role="farmer", is_active=True
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/village-governance/spaces/{mine}")
    assert response.status_code == 200
    body = response.text
    assert "35.6942,51.4251" in body
    for private in ("exact_boundary", "migration_routes", "water_sources", "sacred_sites"):
        assert private not in body, private


async def test_a_stranger_cannot_read_another_villages_space(seeded):
    maker, _mine, theirs = seeded
    async with _client(maker, user_id="user-1") as client:
        response = await client.get(f"/api/v1/village-governance/spaces/{theirs}")
    assert response.status_code == 403
