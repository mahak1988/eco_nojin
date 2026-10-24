"""HTTP regression tests for the village-hub endpoints repaired in waves 1-3
(P0-5/P1-10/P1-11), over a minimal app with in-memory SQLite.

Pins:
* the global literal routes (``/opportunities``, ``/entrepreneurs``,
  ``/investments``, ``/nomadic-communities``) resolve to their own handlers
  and are no longer shadowed by the parameterized ``/{village_id}`` route;
* the nomadic-community workflow: an authorised create → admin approval →
  visibility in the approved listing → owner-only update, with non-owners
  refused;
* the guarded create paths reject an unauthorised caller (403).

Permission decisions live in ``HubService`` and re-read the ``users`` /
``landscape_governance`` tables (not the injected auth principal), so the
tests seed real rows: a platform admin and a governance member.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# The nomadic lifecycle delivers best-effort notifications to
# ``app_notifications``; provision the table so those writes stay clean.
import services.notification.models_db  # noqa: F401,E402
from database.base import Base
from database.models import User
from services.api_gateway.auth import get_current_user
from services.api_gateway.routers.village_hub import _get_db, router
from services.landscape.models import LandscapeGovernanceMember
from services.marketplace.models.village_hub import (
    EntrepreneurProfile,
    VillageInvestment,
    VillageOpportunity,
    VillageProject,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


def _build_app(session, *, user_id: str | None = "owner-1"):
    app = FastAPI()
    app.include_router(router)

    async def db_override():
        yield session

    app.dependency_overrides[_get_db] = db_override
    if user_id is not None:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=user_id, role="farmer"
        )
    return app


async def _request(app, method: str, path: str, payload: dict | None = None, params=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path, json=payload, params=params)


async def _seed_actors(session) -> None:
    """A platform admin and an active governance member (the write actor)."""
    session.add(User(id="admin-1", email="admin@econ", username="admin1", role="admin"))
    session.add(
        LandscapeGovernanceMember(
            village_id="v-1", user_id="owner-1", role="council_member", is_active=True
        )
    )
    await session.commit()


# ===========================================================================
# Literal routes not shadowed by /{village_id}
# ===========================================================================


class TestGlobalLiteralRoutesNotShadowed:
    async def test_opportunities_route_is_reachable(self, session):
        await _seed_actors(session)
        session.add(
            VillageOpportunity(
                id="opp-1",
                village_id="v-1",
                name="Apple Packaging Line",
                category="agri",
                created_by="owner-1",
                status="active",
            )
        )
        await session.commit()
        app = _build_app(session, user_id="owner-1")
        response = await _request(app, "GET", "/api/v1/marketplace/villages/opportunities")
        assert response.status_code == 200, response.text
        body = response.json()
        assert isinstance(body, list)
        assert any(o["name"] == "Apple Packaging Line" for o in body)

    async def test_entrepreneurs_route_is_reachable(self, session):
        await _seed_actors(session)
        session.add(
            EntrepreneurProfile(
                id="ent-1",
                user_id="owner-1",
                village_id="v-1",
                skills=["welding"],
                is_available=True,
            )
        )
        await session.commit()
        app = _build_app(session, user_id="owner-1")
        response = await _request(app, "GET", "/api/v1/marketplace/villages/entrepreneurs")
        assert response.status_code == 200, response.text
        body = response.json()
        assert isinstance(body, dict)
        assert "profiles" in body
        assert any(p["user_id"] == "owner-1" for p in body["profiles"])

    async def test_investments_route_is_reachable(self, session):
        await _seed_actors(session)
        session.add(
            VillageProject(id="proj-1", village_id="v-1", name="Trout Farm", created_by="owner-1")
        )
        await session.flush()
        session.add(
            VillageInvestment(
                id="inv-1", project_id="proj-1", investor_user_id="owner-1", amount=1000
            )
        )
        await session.commit()
        app = _build_app(session, user_id="owner-1")
        response = await _request(app, "GET", "/api/v1/marketplace/villages/investments")
        assert response.status_code == 200, response.text
        body = response.json()
        assert isinstance(body, list)
        assert any(i["id"] == "inv-1" for i in body)

    async def test_nomadic_communities_list_is_reachable_without_auth(self, session):
        # This literal route is public and returns a list; if it were still
        # shadowed by /{village_id} it would 404 (unknown village) or 500.
        app = _build_app(session, user_id=None)
        response = await _request(app, "GET", "/api/v1/marketplace/villages/nomadic-communities")
        assert response.status_code == 200, response.text
        assert isinstance(response.json(), list)

    async def test_empty_literal_routes_return_empty_containers(self, session):
        await _seed_actors(session)
        app = _build_app(session, user_id="owner-1")
        opps = await _request(app, "GET", "/api/v1/marketplace/villages/opportunities")
        assert opps.json() == []
        nomads = await _request(
            app, "GET", "/api/v1/marketplace/villages/nomadic-communities"
        )
        assert nomads.json() == []


# ===========================================================================
# Nomadic community workflow
# ===========================================================================


class TestNomadicWorkflow:
    async def test_create_approve_and_become_visible(self, session):
        await _seed_actors(session)
        owner_app = _build_app(session, user_id="owner-1")
        admin_app = _build_app(session, user_id="admin-1")

        created = await _request(
            owner_app,
            "POST",
            "/api/v1/marketplace/villages/nomadic-communities",
            {"village_id": "v-1", "name": "Qashqai Tribe", "region": "Fars", "country": "IR"},
        )
        assert created.status_code == 200, created.text
        community = created.json()
        assert community["is_approved"] is False
        assert community["owner_user_id"] == "owner-1"
        assert community["name"] == "Qashqai Tribe"
        community_id = community["id"]

        # A freshly created community is not in the default (approved-only) list.
        approved_only = await _request(
            owner_app, "GET", "/api/v1/marketplace/villages/nomadic-communities"
        )
        assert approved_only.json() == []

        # Admin approves it.
        approved = await _request(
            admin_app,
            "PATCH",
            f"/api/v1/marketplace/villages/nomadic-communities/{community_id}/approve",
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["is_approved"] is True
        assert approved.json()["approved_by"] == "admin-1"

        # Now visible in the approved listing and by id.
        listed = await _request(
            owner_app, "GET", "/api/v1/marketplace/villages/nomadic-communities"
        )
        assert any(c["id"] == community_id for c in listed.json())
        detail = await _request(
            owner_app, "GET", f"/api/v1/marketplace/villages/nomadic-communities/{community_id}"
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["is_approved"] is True

    async def test_unapproved_visible_only_when_included(self, session):
        await _seed_actors(session)
        owner_app = _build_app(session, user_id="owner-1")
        created = await _request(
            owner_app,
            "POST",
            "/api/v1/marketplace/villages/nomadic-communities",
            {"village_id": "v-1", "name": "Not Yet Approved"},
        )
        community_id = created.json()["id"]
        with_all = await _request(
            owner_app,
            "GET",
            "/api/v1/marketplace/villages/nomadic-communities",
            params={"approved_only": False},
        )
        assert any(c["id"] == community_id for c in with_all.json())

    async def test_owner_can_update_own_community(self, session):
        await _seed_actors(session)
        owner_app = _build_app(session, user_id="owner-1")
        created = await _request(
            owner_app,
            "POST",
            "/api/v1/marketplace/villages/nomadic-communities",
            {"village_id": "v-1", "name": "Original Name"},
        )
        community_id = created.json()["id"]
        updated = await _request(
            owner_app,
            "PUT",
            f"/api/v1/marketplace/villages/nomadic-communities/{community_id}",
            {"name": "Updated Name"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["name"] == "Updated Name"

    async def test_non_owner_cannot_update_or_delete(self, session):
        await _seed_actors(session)
        owner_app = _build_app(session, user_id="owner-1")
        stranger_app = _build_app(session, user_id="stranger-1")
        created = await _request(
            owner_app,
            "POST",
            "/api/v1/marketplace/villages/nomadic-communities",
            {"village_id": "v-1", "name": "Owned Community"},
        )
        community_id = created.json()["id"]

        updated = await _request(
            stranger_app,
            "PUT",
            f"/api/v1/marketplace/villages/nomadic-communities/{community_id}",
            {"name": "Hijacked"},
        )
        assert updated.status_code == 403, updated.text

        deleted = await _request(
            stranger_app,
            "DELETE",
            f"/api/v1/marketplace/villages/nomadic-communities/{community_id}",
        )
        assert deleted.status_code == 403, deleted.text

        # The record is untouched.
        detail = await _request(
            owner_app,
            "GET",
            f"/api/v1/marketplace/villages/nomadic-communities/{community_id}",
        )
        assert detail.json()["name"] == "Owned Community"

    async def test_owner_can_delete_own_community(self, session):
        await _seed_actors(session)
        owner_app = _build_app(session, user_id="owner-1")
        created = await _request(
            owner_app,
            "POST",
            "/api/v1/marketplace/villages/nomadic-communities",
            {"village_id": "v-1", "name": "To Be Removed"},
        )
        community_id = created.json()["id"]
        deleted = await _request(
            owner_app,
            "DELETE",
            f"/api/v1/marketplace/villages/nomadic-communities/{community_id}",
        )
        assert deleted.status_code == 204, deleted.text


class TestNomadicGuards:
    async def test_unauthorised_create_is_rejected(self, session):
        # A plain user with no governance membership and no admin role.
        session.add(User(id="plain-1", email="plain@econ", username="plain1", role="farmer"))
        await session.commit()
        plain_app = _build_app(session, user_id="plain-1")
        response = await _request(
            plain_app,
            "POST",
            "/api/v1/marketplace/villages/nomadic-communities",
            {"village_id": "v-1", "name": "Sneaky"},
        )
        assert response.status_code == 403, response.text

    async def test_approve_unknown_community_is_404(self, session):
        await _seed_actors(session)
        admin_app = _build_app(session, user_id="admin-1")
        response = await _request(
            admin_app,
            "PATCH",
            "/api/v1/marketplace/villages/nomadic-communities/missing/approve",
        )
        assert response.status_code == 404, response.text

    async def test_update_unknown_community_is_404(self, session):
        owner_app = _build_app(session, user_id="owner-1")
        response = await _request(
            owner_app,
            "PUT",
            "/api/v1/marketplace/villages/nomadic-communities/missing",
            {"name": "New Name"},
        )
        assert response.status_code == 404, response.text

    async def test_delete_unknown_community_is_404(self, session):
        owner_app = _build_app(session, user_id="owner-1")
        response = await _request(
            owner_app,
            "DELETE",
            "/api/v1/marketplace/villages/nomadic-communities/missing",
        )
        assert response.status_code == 404, response.text
