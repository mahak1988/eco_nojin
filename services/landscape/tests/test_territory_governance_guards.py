"""HTTP regression tests for the territory + governance write guards.

The ASVS V4 access-control matrix found sixteen unguarded write routes; these
were the landscape half of them. The setup follows the tourism router's
(``services/api_gateway/tests/test_http_tourism.py``): a minimal FastAPI app
with in-memory SQLite, ``get_current_user`` overridden for an authenticated
caller, and the real dependency left in place for the anonymous case.

What is pinned here:

* an anonymous caller cannot drive the territory state machine (401);
* an authenticated caller who is not a governance writer cannot approve,
  reject or publish a territory, and cannot add/remove/deactivate a council
  member (403);
* the governance writer roles (``landscape_manager`` / ``council_member``, the
  same write vocabulary ``services.marketplace.hub_service`` uses) pass the
  authorization decision;
* the village-side half of the machine (submit / resubmit / archive) only
  needs an authenticated caller.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.api_gateway.auth import get_current_user
from services.landscape.api.governance import _get_db as governance_get_db
from services.landscape.api.governance import router as governance_router
from services.landscape.api.territories import _get_db as territory_get_db
from services.landscape.api.territories import router as territory_router
from services.landscape.models import LandscapeVillage

pytestmark = pytest.mark.asyncio

_VILLAGE = "v-guard-1"
_GOVERNANCE = f"/api/v1/landscape/villages/{_VILLAGE}/governance"
_TERRITORIES = "/api/v1/territories"


@pytest.fixture
async def session():
    """One in-memory database shared by every app built in a test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


def _build_app(session, *, user_id: str | None = "farmer-1", role: str = "farmer"):
    """Mount both routers with the DB override, auth optional.

    ``authenticate=False`` leaves the real ``get_current_user`` in place, so a
    request with no token exercises the genuine 401 path. Overriding the one
    ``get_current_user`` callable is enough for ``require_user`` (its alias)
    and ``require_roles`` (which depends on it).
    """
    app = FastAPI()
    app.include_router(territory_router)
    app.include_router(governance_router)

    async def db_override():
        yield session

    for get_db in (territory_get_db, governance_get_db):
        app.dependency_overrides[get_db] = db_override
    if user_id is not None:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=user_id, role=role
        )
    return app


async def _request(app, method: str, path: str, payload: dict | None = None, **params):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path, json=payload, params=params or None)


async def _seed_village(session) -> None:
    """A village, so the workflow handlers have a row to transition.

    ``workflow_status`` starts at ``published``, which is what makes
    ``submit`` reach a 400 from the handler's own state machine rather than
    from a missing row — the test asserts the caller passed authorization.
    """
    session.add(
        LandscapeVillage(
            village_id=_VILLAGE,
            name="گارد",
            region="کردستان",
            workflow_status="published",
        )
    )
    await session.commit()


# ===========================================================================
# Territory state machine
# ===========================================================================


class TestTerritoryWorkflowRequiresAuthentication:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("POST", "submit"),
            ("POST", "review"),
            ("POST", "resubmit"),
            ("POST", "archive"),
            ("PATCH", "verify"),
        ],
    )
    async def test_anonymous_caller_is_refused(self, session, method, path):
        await _seed_village(session)
        app = _build_app(session, user_id=None)

        response = await _request(app, method, f"{_TERRITORIES}/{_VILLAGE}/{path}")

        assert response.status_code == 401, response.text

    @pytest.mark.parametrize("path", ["submit", "resubmit", "archive"])
    async def test_village_side_actions_only_need_an_authenticated_user(
        self, session, path
    ):
        await _seed_village(session)
        app = _build_app(session, user_id="farmer-1", role="farmer")

        response = await _request(app, "POST", f"{_TERRITORIES}/{_VILLAGE}/{path}")

        # The handler's own state-machine check decides 200/400; the point is
        # that the caller got past the authorisation dependency at all.
        assert response.status_code in (200, 400), response.text
        assert response.status_code != 401
        assert response.status_code != 403


class TestTerritoryPublicProjection:
    async def test_public_catalogue_omits_internal_geometry_and_contract_fields(self, session):
        session.add(
            LandscapeVillage(
                village_id=_VILLAGE,
                name="گارد",
                region="کردستان",
                coordinates={"lat": 34.5, "lon": 47.1},
                geo_boundary={"type": "private-shape"},
                monthly_gmv=Decimal("1234.50"),
                smart_contract_address="internal-contract-address",
            )
        )
        await session.commit()
        app = _build_app(session)

        listing = await _request(app, "GET", _TERRITORIES)
        detail = await _request(app, "GET", f"{_TERRITORIES}/{_VILLAGE}")

        assert listing.status_code == 200, listing.text
        assert detail.status_code == 200, detail.text
        item = listing.json()["items"][0]
        assert item["village_id"] == _VILLAGE
        assert item["name"] == "گارد"
        for response_item in (item, detail.json()):
            assert "coordinates" not in response_item
            assert "geo_boundary" not in response_item
            assert "monthly_gmv" not in response_item
            assert "smart_contract_address" not in response_item


class TestTerritoryApprovalRequiresAGovernanceWriter:
    """``verify``/``review`` are governance decisions, not village-side ones."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("PATCH", "verify"),
            ("POST", "review"),
        ],
    )
    async def test_an_authenticated_farmer_is_refused(self, session, method, path):
        await _seed_village(session)
        app = _build_app(session, user_id="farmer-1", role="farmer")

        response = await _request(app, method, f"{_TERRITORIES}/{_VILLAGE}/{path}")

        assert response.status_code == 403, response.text

    async def test_a_landscape_manager_may_verify(self, session):
        app = _build_app(session, user_id="manager-1", role="landscape_manager")

        response = await _request(
            app,
            "PATCH",
            f"{_TERRITORIES}/{_VILLAGE}/verify",
            verification_status="verified",
        )

        assert response.status_code == 404, response.text

    async def test_an_admin_may_review(self, session):
        app = _build_app(session, user_id="admin-1", role="admin")

        response = await _request(
            app,
            "POST",
            f"{_TERRITORIES}/{_VILLAGE}/review",
            reviewer_id="reviewer-9",
        )

        assert response.status_code in (200, 400), response.text

    async def test_a_council_member_may_review(self, session):
        app = _build_app(session, user_id="council-1", role="council_member")

        response = await _request(
            app,
            "POST",
            f"{_TERRITORIES}/{_VILLAGE}/review",
            reviewer_id="reviewer-9",
        )

        assert response.status_code in (200, 400), response.text


# ===========================================================================
# Council membership
# ===========================================================================


class TestGovernanceMembershipRequiresAGovernanceWriter:
    _MEMBER_ROUTES = (
        ("POST", f"{_GOVERNANCE}"),
        ("DELETE", f"{_GOVERNANCE}/member-1"),
        ("PATCH", f"{_GOVERNANCE}/member-1/deactivate"),
        ("PATCH", f"{_GOVERNANCE}/member-1/reactivate"),
        ("PATCH", f"{_GOVERNANCE}/member-1/term"),
    )

    @pytest.mark.parametrize("method,path", _MEMBER_ROUTES)
    async def test_anonymous_caller_is_refused(self, session, method, path):
        app = _build_app(session, user_id=None)

        response = await _request(app, method, path)

        assert response.status_code == 401, response.text

    @pytest.mark.parametrize("method,path", _MEMBER_ROUTES)
    async def test_an_authenticated_farmer_is_refused(self, session, method, path):
        app = _build_app(session, user_id="farmer-1", role="farmer")

        response = await _request(app, method, path)

        assert response.status_code == 403, response.text

    @pytest.mark.parametrize(
        "role", ["landscape_manager", "council_member", "agriculture_rep"]
    )
    async def test_a_governance_writer_gets_past_the_authorisation_decision(
        self, session, role
    ):
        app = _build_app(session, user_id="writer-1", role=role)

        response = await _request(app, "DELETE", f"{_GOVERNANCE}/member-1")

        # 404 (no membership row) is the handler's answer, not the guard's.
        assert response.status_code in (200, 400, 404), response.text

    async def test_a_land_shape_manager_lesser_role_is_refused(self, session):
        """A role outside the write vocabulary must not slip through."""
        app = _build_app(session, user_id="knowledge-1", role="knowledge_rep")

        response = await _request(app, "POST", f"{_GOVERNANCE}")

        assert response.status_code == 403, response.text
