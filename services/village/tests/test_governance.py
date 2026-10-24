"""P7 — the local-governance lifecycle, proven by the rules it refuses to break.

Before this phase ``charter``/``working_group``/`community_space` had zero
occurrences in the repository (KN-12). These tests pin the behaviours the
program demands: the workflow cannot be skipped, activation needs an adopted
charter and a live coordinator, ending a membership never erases decisions,
charter versions are append-only, and sensitive fields stay private until an
explicit per-field publication.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.village.models import SpaceStatus
from services.village.service import GovernanceError, VillageGovernanceService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def _new_space(session, *, actor="user-1") -> object:
    service = VillageGovernanceService(session)
    return await service.register_space(
        village_id="village-1", name="Deh Ali", region="north", actor_id=actor
    )


async def _approved_application(service, space_id: str, step: str) -> None:
    application = await service.submit_application(space_id, step=step, actor_id="user-1")
    await service.review_application(
        str(application.id), approver_id="admin-1", approve=True
    )


async def _advance_to_active(session, space):
    service = VillageGovernanceService(session)
    for step in (
        SpaceStatus.IDENTITY_CHECKING.value,
        SpaceStatus.AUTHORITY_CHECKING.value,
        SpaceStatus.DOCUMENTS_PENDING.value,
        SpaceStatus.GOVERNANCE_FORMING.value,
        SpaceStatus.WORKING_GROUP_FORMING.value,
        SpaceStatus.CHARTER_DRAFTING.value,
    ):
        await _approved_application(service, str(space.id), step)
        await service.advance(str(space.id), actor_id="user-1")
    
    # Add 3 active members (including coordinator) for activation
    group = await service.form_working_group(
        str(space.id), actor_id="user-1", mandate_ref="2026-term"
    )
    await service.add_member(
        str(group.id), user_id="user-2", display_name="Coordinator Ali", role="coordinator"
    )
    await service.add_member(
        str(group.id), user_id="user-3", display_name="Member Bibi", role="member"
    )
    await service.add_member(
        str(group.id), user_id="user-4", display_name="Member Reza", role="member"
    )
    return service


async def test_workflow_cannot_be_skipped_without_an_application(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    with pytest.raises(GovernanceError):
        await service.advance(str(space.id), actor_id="user-1")
    await _approved_application(service, str(space.id), SpaceStatus.IDENTITY_CHECKING.value)
    advanced = await service.advance(str(space.id), actor_id="user-1")
    assert advanced.status == SpaceStatus.IDENTITY_CHECKING.value


async def test_activation_requires_charter_and_coordinator(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    await _advance_to_active(session, space)
    # Working group already created by _advance_to_active
    with pytest.raises(GovernanceError):
        await service.activate(str(space.id), actor_id="user-1")  # no charter yet

    charter = await service.draft_charter(
        str(space.id), actor_id="user-1", title="Charter", body="Local rules"
    )
    await service.adopt_charter(str(charter.id), actor_id="admin-1")
    active = await service.activate(str(space.id), actor_id="admin-1")
    assert active.status == SpaceStatus.ACTIVE.value


async def test_advance_cannot_reach_active_without_the_activation_gate(session):
    """The final workflow step is activation's alone (charter + coordinator)."""
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    await _advance_to_active(session, space)
    # even a submitted application for the final step cannot turn the generic
    # advance() into an activation — that gate is activate()'s alone
    await _approved_application(service, str(space.id), SpaceStatus.ACTIVE.value)
    with pytest.raises(GovernanceError, match="activation"):
        await service.advance(str(space.id), actor_id="user-1")
    still_drafting = await service._require_space(str(space.id))
    assert still_drafting.status == SpaceStatus.CHARTER_DRAFTING.value


async def test_charter_versions_are_append_only(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    await _advance_to_active(session, space)
    first = await service.draft_charter(
        str(space.id), actor_id="user-1", title="v1", body="rules one"
    )
    await service.adopt_charter(str(first.id), actor_id="admin-1")
    # Working group already created by _advance_to_active
    active = await service.activate(str(space.id), actor_id="admin-1")
    second = await service.amend_charter(
        str(space.id), actor_id="user-1", title="v2", body="rules two", reason="review"
    )
    assert second.version == 2
    # the previous version is untouched and still readable
    from sqlalchemy import select

    from services.village.models import LocalCharter

    result = await session.execute(
        select(LocalCharter).where(LocalCharter.space_id == space.id).order_by(LocalCharter.version)
    )
    versions = list(result.scalars())
    assert [c.version for c in versions] == [1, 2]
    assert versions[0].body == "rules one"


async def test_ending_a_membership_keeps_the_decision_history(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    group = await service.form_working_group(
        str(space.id), actor_id="user-1", mandate_ref="2026-term"
    )
    membership = await service.add_member(
        str(group.id), user_id="user-2", display_name="Ali", role="member"
    )
    ended = await service.end_membership(
        str(membership.id), actor_id="admin-1", reason="resigned"
    )
    assert ended.ended_reason == "resigned"
    with pytest.raises(GovernanceError):
        await service.end_membership(str(membership.id), actor_id="admin-1")  # cannot end twice
    # the decision recording the end is in the append-only history
    from sqlalchemy import select

    from services.village.models import GovernanceDecision

    result = await session.execute(
        select(GovernanceDecision).where(GovernanceDecision.space_id == space.id)
    )
    kinds = [d.kind for d in result.scalars()]
    assert "membership_ended" in kinds


async def test_sensitive_fields_are_private_until_published_one_by_one(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    assert space.migration_routes is None
    with pytest.raises(GovernanceError):
        await service.publish_sensitive_field(
            str(space.id), actor_id="admin-1", field="name", value="not sensitive"
        )
    published = await service.publish_sensitive_field(
        str(space.id), actor_id="admin-1", field="water_sources", value="two springs"
    )
    assert published.water_sources == "two springs"
    assert published.sensitive_fields_published == 1
    assert published.published_fields == ["water_sources"]
    assert published.migration_routes is None  # still private


async def test_a_subtype_change_is_an_audited_decision(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    changed = await service.change_kind(
        str(space.id),
        actor_id="admin-1",
        new_kind="pastoral_rangeland",
        reason="seasonal pastures confirmed",
    )
    assert changed.kind == "pastoral_rangeland"
    with pytest.raises(GovernanceError):
        await service.change_kind(
            str(space.id), actor_id="admin-1", new_kind="pastoral_rangeland", reason="again"
        )


async def test_duplicate_space_or_application_is_refused(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    with pytest.raises(GovernanceError):
        await service.register_space(village_id="village-1", name="dup", actor_id="user-1")
    await service.submit_application(
        str(space.id), step=SpaceStatus.IDENTITY_CHECKING.value, actor_id="user-1"
    )
    with pytest.raises(GovernanceError):
        await service.submit_application(
            str(space.id), step=SpaceStatus.IDENTITY_CHECKING.value, actor_id="user-1"
        )


async def test_the_record_of_a_suspension_is_kept(session):
    service = VillageGovernanceService(session)
    space = await _new_space(session)
    await _advance_to_active(session, space)
    charter = await service.draft_charter(
        str(space.id), actor_id="user-1", title="Charter", body="Local rules"
    )
    await service.adopt_charter(str(charter.id), actor_id="admin-1")
    # Working group already created by _advance_to_active
    active = await service.activate(str(space.id), actor_id="admin-1")
    assert active.status == SpaceStatus.ACTIVE.value

    suspended = await service.suspend(str(space.id), actor_id="admin-1", reason="audit hold")
    assert suspended.status == SpaceStatus.SUSPENDED.value
    with pytest.raises(GovernanceError):
        await service.advance(str(space.id), actor_id="user-1")
    resumed = await service.resume(str(space.id), actor_id="admin-1")
    assert resumed.status == SpaceStatus.ACTIVE.value
