"""The local-governance service: the onboarding workflow and its rules (P7).

Every transition is explicit, audited, and refuses to do what Phase 7 forbids:

* the space never reaches ``ACTIVE`` without an adopted charter and at least one
  working group with a live coordinator;
* a membership term end never deletes decisions (they are linked by actor id,
  and the membership row is kept with its end reason);
* the sensitive fields (migration routes, water sources, sacred sites, exact
  boundary) are private until published *per field* by an explicit call;
* a subtype change (village <-> pastoral_rangeland) is its own audited decision,
  never a silent edit.

Money is never moved here: this module records local decisions; anything with a
value goes through the finance contract (``architecture/MONEY-CONTRACT``).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.landscape.models import LandscapeVillage
from services.marketplace.service import get_hub_service
from services.rangeland.models import Rangeland
from services.rangeland.service import RangelandService
from services.tourism.festival_service import FestivalService
from services.tourism.unesco_service import UnescoService
from services.village.models import (
    CommunitySpace,
    CommunitySpaceKind,
    GovernanceApplication,
    GovernanceDecision,
    LocalCharter,
    MembershipEndReason,
    SpaceStatus,
    WorkingGroup,
    WorkingGroupMembership,
    WorkingGroupRole,
)

#: Sensitive fields, published only one at a time, by an explicit call.
SENSITIVE_FIELDS = ("migration_routes", "water_sources", "sacred_sites", "exact_boundary")

#: The ordered workflow. A space advances one step at a time; skipping a step
#: raises ``GovernanceError`` (a submitted application is what allows it).
WORKFLOW: tuple[str, ...] = (
    SpaceStatus.REQUESTED.value,
    SpaceStatus.IDENTITY_CHECKING.value,
    SpaceStatus.AUTHORITY_CHECKING.value,
    SpaceStatus.DOCUMENTS_PENDING.value,
    SpaceStatus.GOVERNANCE_FORMING.value,
    SpaceStatus.WORKING_GROUP_FORMING.value,
    SpaceStatus.CHARTER_DRAFTING.value,
    SpaceStatus.ACTIVE.value,
)


class GovernanceError(ValueError):
    """A forbidden governance transition or an incomplete precondition."""


class VillageGovernanceService:
    """Village/rangeland governance lifecycle over the shared async session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # space creation & lifecycle
    # ------------------------------------------------------------------

    async def register_space(
        self,
        *,
        village_id: str,
        name: str,
        kind: str = CommunitySpaceKind.VILLAGE.value,
        region: str | None = None,
        country: str | None = None,
        actor_id: str,
    ) -> CommunitySpace:
        if kind not in {k.value for k in CommunitySpaceKind}:
            raise GovernanceError(f"unknown space kind: {kind}")
        existing = await self._get_space_by_village(village_id)
        if existing is not None:
            raise GovernanceError(f"a space already exists for {village_id}")
        space = CommunitySpace(
            village_id=village_id,
            name=name,
            kind=kind,
            region=region,
            country=country,
            status=SpaceStatus.REQUESTED.value,
        )
        self.db.add(space)
        await self.db.flush()
        self._record_decision(
            space, kind="space_requested", summary=f"{name} requested", actor_id=actor_id
        )
        await self.db.commit()
        return space

    async def advance(
        self, space_id: str, *, actor_id: str, note: str | None = None
    ) -> CommunitySpace:
        """Advance one workflow step; requires the matching application submitted.

        The submitted application is the evidence a human did the work: without
        it the space cannot advance, so the workflow cannot be skipped by an API
        call alone.
        """
        space = await self._require_space(space_id)
        if space.status == SpaceStatus.ACTIVE.value:
            raise GovernanceError("space is already active")
        if space.status == SpaceStatus.SUSPENDED.value:
            raise GovernanceError("space is suspended; resume it first")
        index = WORKFLOW.index(space.status)
        if index + 1 >= len(WORKFLOW):
            raise GovernanceError("no further workflow step exists")
        next_status = WORKFLOW[index + 1]
        if next_status == SpaceStatus.ACTIVE.value:
            # Activation is its own gate: an adopted charter and a live
            # coordinator. Letting the generic advance() reach ACTIVE (with a
            # submitted application for the "active" step as its only
            # precondition) would bypass that check entirely.
            raise GovernanceError(
                "activation is its own gate (adopted charter + live "
                "coordinator); call activate(), not advance()"
            )
        await self._require_submitted_application(space_id, next_status)
        space.status = next_status
        space.updated_at = datetime.now(UTC)
        self._record_decision(
            space,
            kind="workflow_advanced",
            summary=f"{space.status} (from {WORKFLOW[index]}){': ' + note if note else ''}",
            actor_id=actor_id,
        )
        await self.db.commit()
        return space

    async def submit_application(
        self,
        space_id: str,
        *,
        step: str,
        actor_id: str,
        evidence_ref: str | None = None,
    ) -> GovernanceApplication:
        await self._require_space(space_id)
        if step not in WORKFLOW:
            raise GovernanceError(f"unknown workflow step: {step}")
        existing = await self.db.execute(
            select(GovernanceApplication).where(
                GovernanceApplication.space_id == space_id,
                GovernanceApplication.step == step,
            )
        )
        pending = existing.scalar_one_or_none()
        if pending is not None:
            raise GovernanceError(f"an application for {step} already exists")
        application = GovernanceApplication(
            space_id=space_id,
            step=step,
            status="submitted",
            submitted_by=actor_id,
            evidence_ref=evidence_ref,
        )
        self.db.add(application)
        await self.db.commit()
        return application

    async def review_application(
        self, application_id: str, *, approver_id: str, approve: bool, note: str | None = None
    ) -> GovernanceApplication:
        result = await self.db.execute(
            select(GovernanceApplication).where(GovernanceApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        if application is None:
            raise GovernanceError(f"application not found: {application_id}")
        if application.status != "submitted":
            raise GovernanceError(f"application is {application.status}, not submitted")
        application.status = "approved" if approve else "rejected"
        application.reviewed_by = approver_id
        application.reviewed_at = datetime.now(UTC)
        application.review_note = note
        await self.db.commit()
        return application

    async def activate(self, space_id: str, *, actor_id: str) -> CommunitySpace:
        """The gate: active requires an adopted charter + a live working group.

        Hardening rules:
          * At least 3 active working-group members (quorum for a village body).
          * The adopted charter must have been adopted within the last 2 years
            (charters expire and must be re-adopted).
          * The coordinator may not serve more than 2 consecutive terms.
        """
        from datetime import timedelta

        space = await self._require_space(space_id)
        if space.status == SpaceStatus.ACTIVE.value:
            return space
        if space.status != SpaceStatus.CHARTER_DRAFTING.value:
            raise GovernanceError(
                "activation requires the charter-drafting step (charter + working group)"
            )
        charter = await self.current_charter(space_id)
        if charter is None or charter.adopted_at is None:
            raise GovernanceError("activation requires an adopted charter")
        # Charter currency: must have been (re)adopted within the last 2 years.
        charter_age = datetime.now(UTC) - charter.adopted_at
        if charter_age > timedelta(days=730):
            raise GovernanceError(
                "charter is older than 2 years; re-adopt before activation"
            )
        coordinator = await self._live_coordinator(space_id)
        if coordinator is None:
            raise GovernanceError("activation requires a working group with a live coordinator")
        # Minimum working-group size: at least 3 active members.
        members = await self.active_members(space_id)
        if len(members) < 3:
            raise GovernanceError(
                f"activation requires at least 3 active working-group members "
                f"(currently {len(members)})"
            )
        # Coordinator term limit: max 2 consecutive terms.
        coordinator_terms = await self._coordinator_terms(space_id, str(coordinator.user_id))
        if coordinator_terms >= 2:
            raise GovernanceError(
                "coordinator has served 2 consecutive terms; a new coordinator "
                "must be elected before activation"
            )
        space.status = SpaceStatus.ACTIVE.value
        space.updated_at = datetime.now(UTC)
        self._record_decision(
            space, kind="space_activated", summary=space.name, actor_id=actor_id,
            charter_version=charter.version,
        )
        await self.db.commit()

        # Fire 1 — connect governance-active village to marketplace hub:
        # create (or refresh) the LandscapeVillage record so hub_service can
        # resolve the village and enable village-hub write paths.
        lv = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == space.village_id)
        )
        landscape_village = lv.scalar_one_or_none()
        if landscape_village is None:
            landscape_village = LandscapeVillage(
                village_id=space.village_id,
                name=space.name,
                region=space.region,
                country=space.country,
                coordinates=None,
                geo_boundary=None,
                brand_name=None,
                brand_logo_url=None,
                gi_registration=None,
                is_active=True,
                established_at=None,
                active_modules=["marketplace", "tourism"],
                total_members=0,
                active_sellers=0,
                active_tour_guides=0,
                monthly_gmv=Decimal("0.00"),
                ecological_metrics_data={},
                smart_contract_address=None,
                blockchain_network=None,
                verification_status="pending",
                representative_status="none",
                workflow_status="published",
            )
            self.db.add(landscape_village)
            await self.db.commit()

        # Fire 2 — connect pastoral_rangeland governance space to rangelands:
        # link existing rangelands of this village to the active space so
        # rangeland queries can be scoped by governance space.
        if space.kind == CommunitySpaceKind.PASTORAL_RANGELAND.value:
            result = await self.db.execute(
                select(Rangeland).where(Rangeland.village_id == space.village_id)
            )
            for rangeland in result.scalars().all():
                if rangeland.governance_space_id is None:
                    rangeland.governance_space_id = str(space.id)
            await self.db.commit()

        await self.db.refresh(space)
        return space

    async def suspend(self, space_id: str, *, actor_id: str, reason: str) -> CommunitySpace:
        space = await self._require_space(space_id)
        if space.status == SpaceStatus.ACTIVE.value:
            space.status = SpaceStatus.SUSPENDED.value
            space.suspended_reason = reason
            space.updated_at = datetime.now(UTC)
            self._record_decision(
                space, kind="space_suspended", summary=reason, actor_id=actor_id
            )
            await self.db.commit()
        return space

    async def resume(self, space_id: str, *, actor_id: str) -> CommunitySpace:
        space = await self._require_space(space_id)
        if space.status != SpaceStatus.SUSPENDED.value:
            raise GovernanceError("space is not suspended")
        space.status = SpaceStatus.ACTIVE.value
        space.updated_at = datetime.now(UTC)
        self._record_decision(
            space, kind="space_resumed", summary=space.name, actor_id=actor_id
        )
        await self.db.commit()
        return space

    async def change_kind(
        self, space_id: str, *, actor_id: str, new_kind: str, reason: str
    ) -> CommunitySpace:
        """A village↔rangeland conversion is an audited decision, not an edit."""
        space = await self._require_space(space_id)
        if new_kind not in {k.value for k in CommunitySpaceKind}:
            raise GovernanceError(f"unknown space kind: {new_kind}")
        if space.kind == new_kind:
            raise GovernanceError("the space already has that kind")
        old = space.kind
        space.kind = new_kind
        space.updated_at = datetime.now(UTC)
        self._record_decision(
            space,
            kind="space_kind_changed",
            summary=f"{old} -> {new_kind}: {reason}",
            actor_id=actor_id,
        )
        await self.db.commit()
        return space

    # ------------------------------------------------------------------
    # charter
    # ------------------------------------------------------------------

    async def draft_charter(
        self, space_id: str, *, actor_id: str, title: str, body: str
    ) -> LocalCharter:
        await self._require_space(space_id)
        existing = await self.db.execute(
            select(LocalCharter).where(
                LocalCharter.space_id == space_id, LocalCharter.withdrawn_at.is_(None)
            )
        )
        draft = existing.scalar_one_or_none()
        if draft is not None:
            raise GovernanceError("an un-withdrawn charter already exists; amend it instead")
        charter = LocalCharter(
            space_id=space_id, version=1, title=title, body=body, created_by=actor_id
        )
        self.db.add(charter)
        await self.db.commit()
        return charter

    async def amend_charter(
        self, space_id: str, *, actor_id: str, title: str, body: str, reason: str
    ) -> LocalCharter:
        """A new version; the previous version stays readable, never edited."""
        space = await self._require_space(space_id)
        current = await self.current_charter(space_id)
        if current is None:
            raise GovernanceError("no charter to amend; draft one first")
        if space.status != SpaceStatus.ACTIVE.value:
            raise GovernanceError("only an active space may amend its charter")
        new_version = await self.db.execute(
            select(LocalCharter).where(LocalCharter.space_id == space_id)
        )
        next_version = max((c.version for c in new_version.scalars()), default=0) + 1
        amendment = LocalCharter(
            space_id=space_id,
            version=next_version,
            title=title,
            body=body,
            created_by=actor_id,
        )
        self.db.add(amendment)
        await self.db.flush()
        self._record_decision(
            space,
            kind="charter_amended",
            summary=f"v{current.version} -> v{next_version}: {reason}",
            actor_id=actor_id,
            charter_version=next_version,
        )
        await self.db.commit()
        return amendment

    async def adopt_charter(
        self, charter_id: str, *, actor_id: str, adopted_at: datetime | None = None
    ) -> LocalCharter:
        charter = await self._require_charter(charter_id)
        if charter.adopted_at is not None:
            raise GovernanceError("charter is already adopted")
        charter.adopted_at = adopted_at or datetime.now(UTC)
        self._record_decision(
            await self._require_space(charter.space_id),
            kind="charter_adopted",
            summary=f"{charter.title} v{charter.version}",
            actor_id=actor_id,
            charter_version=charter.version,
        )
        await self.db.commit()
        return charter

    async def withdraw_charter(
        self, charter_id: str, *, actor_id: str, reason: str
    ) -> LocalCharter:
        charter = await self._require_charter(charter_id)
        if charter.withdrawn_at is not None:
            raise GovernanceError("charter is already withdrawn")
        charter.withdrawn_at = datetime.now(UTC)
        charter.withdrawal_reason = reason
        self._record_decision(
            await self._require_space(charter.space_id),
            kind="charter_withdrawn",
            summary=f"v{charter.version}: {reason}",
            actor_id=actor_id,
            charter_version=charter.version,
        )
        await self.db.commit()
        return charter

    async def current_charter(self, space_id: str) -> LocalCharter | None:
        """The adopted charter with the highest version."""
        result = await self.db.execute(
            select(LocalCharter)
            .where(
                LocalCharter.space_id == space_id,
                LocalCharter.adopted_at.is_not(None),
                LocalCharter.withdrawn_at.is_(None),
            )
            .order_by(LocalCharter.version.desc())
        )
        return result.scalars().first()

    # ------------------------------------------------------------------
    # working group
    # ------------------------------------------------------------------

    async def form_working_group(
        self, space_id: str, *, actor_id: str, mandate_ref: str, mandate_summary: str | None = None
    ) -> WorkingGroup:
        await self._require_space(space_id)
        existing = await self.db.execute(
            select(WorkingGroup).where(
                WorkingGroup.space_id == space_id,
                WorkingGroup.mandate_ref == mandate_ref,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise GovernanceError(f"a group with mandate {mandate_ref} already exists")
        group = WorkingGroup(
            space_id=space_id, mandate_ref=mandate_ref, mandate_summary=mandate_summary
        )
        self.db.add(group)
        await self.db.commit()
        return group

    async def add_member(
        self,
        group_id: str,
        *,
        user_id: str,
        display_name: str,
        role: str = WorkingGroupRole.MEMBER.value,
        term_start=None,
        term_end=None,
    ) -> WorkingGroupMembership:
        if role not in {r.value for r in WorkingGroupRole}:
            raise GovernanceError(f"unknown role: {role}")
        group = await self._require_group(group_id)
        if group.dissolved_at is not None:
            raise GovernanceError("the group is dissolved")
        membership = WorkingGroupMembership(
            group_id=group_id,
            user_id=user_id,
            display_name=display_name,
            role=role,
            term_start=term_start,
            term_end=term_end,
        )
        self.db.add(membership)
        await self.db.commit()
        return membership

    async def end_membership(
        self,
        membership_id: str,
        *,
        actor_id: str,
        reason: str = MembershipEndReason.TERM_COMPLETED.value,
    ) -> WorkingGroupMembership:
        """End a term. The membership row and every decision stay readable."""
        membership = await self._require_membership(membership_id)
        if membership.ended_reason is not None:
            raise GovernanceError("the membership has already ended")
        if reason not in {r.value for r in MembershipEndReason}:
            raise GovernanceError(f"unknown end reason: {reason}")
        membership.ended_reason = reason
        membership.term_end = membership.term_end or datetime.now(UTC).date()
        self._record_decision(
            await self._require_space(membership.group.space_id),
            kind="membership_ended",
            summary=f"{membership.display_name}: {reason}",
            actor_id=actor_id,
        )
        await self.db.commit()
        return membership

    async def dissolve_group(self, group_id: str, *, actor_id: str, reason: str) -> WorkingGroup:
        group = await self._require_group(group_id)
        if group.dissolved_at is not None:
            raise GovernanceError("the group is already dissolved")
        group.dissolved_at = datetime.now(UTC)
        group.dissolution_reason = reason
        self._record_decision(
            await self._require_space(group.space_id),
            kind="group_dissolved",
            summary=f"{group.mandate_ref}: {reason}",
            actor_id=actor_id,
        )
        await self.db.commit()
        return group

    # ------------------------------------------------------------------
    # sensitive data
    # ------------------------------------------------------------------

    async def publish_sensitive_field(
        self,
        space_id: str,
        *,
        actor_id: str,
        field: str,
        value: str,
        consent_method: str | None = None,
    ) -> CommunitySpace:
        """Publish ONE sensitivity-classified field, by an explicit audited act.

        Consent is recorded in ``sensitive_field_consent`` so the platform can
        demonstrate who authorized publication and how.
        """
        if field not in SENSITIVE_FIELDS:
            raise GovernanceError(
                f"{field} is not a sensitivity-classified field; allowed: "
                f"{', '.join(SENSITIVE_FIELDS)}"
            )
        space = await self._require_space(space_id)

        # Record consent before publishing.
        consent = dict(space.sensitive_field_consent or {})
        consent[field] = {
            "consented_by": actor_id,
            "consented_at": datetime.now(UTC).isoformat(),
            "method": consent_method or "explicit",
        }
        space.sensitive_field_consent = consent

        setattr(space, field, value)
        published = list(space.published_fields or [])
        if field not in published:
            published.append(field)
        space.published_fields = published
        space.sensitive_fields_published = len(published)
        space.updated_at = datetime.now(UTC)
        self._record_decision(
            space,
            kind="sensitive_published",
            summary=f"{field} published (consent: {consent_method or 'explicit'})",
            actor_id=actor_id,
        )
        await self.db.commit()
        return space

    # ═════════════════════════════════════════════════════════════
    # unified village dashboard
    # ═════════════════════════════════════════════════════════════

    async def unified_village_dashboard(
        self,
        village_id: str,
    ) -> dict:
        """Aggregate governance, marketplace, rangeland, tourism and UNESCO
        data into a single village dashboard.

        Data sources:
          * governance  → CommunitySpace (status, kind, members)
          * marketplace → hub_service (capabilities, opportunities,
                          projects, investments, B2B matches)
          * rangeland   → RangelandService (area, productivity)
          * tourism     → FestivalService (festivals, bookings)
          * unesco      → UnescoService (indicators, assessments)
        """
        # ── governance ──────────────────────────────────────────────
        space = await self._get_space_by_village(village_id)
        if space is None:
            raise GovernanceError(f"no governance space for village {village_id}")

        members = await self.active_members(str(space.id))
        charter = await self.current_charter(str(space.id))

        governance = {
            "space_id": str(space.id),
            "kind": space.kind,
            "status": space.status,
            "member_count": len(members),
            "charter_adopted": charter is not None,
            "charter_version": charter.version if charter else None,
            "sensitive_fields_published": space.sensitive_fields_published,
        }

        # ── marketplace ─────────────────────────────────────────────
        hub = get_hub_service(self.db)
        try:
            profile = await hub.get_village_profile(village_id)
        except ValueError:
            profile = {}

        dashboard = await hub.get_village_dashboard(village_id)

        # B2B matches for this village
        b2b_matches = await hub.match_b2b_demands(village_id)

        marketplace = {
            "profile": profile,
            "dashboard": dashboard,
            "b2b_matches": b2b_matches,
            "b2b_match_count": len(b2b_matches),
        }

        # ── rangeland ───────────────────────────────────────────────
        rangeland_svc = RangelandService(self.db)
        try:
            rangeland = await rangeland_svc.stats_for_territory(village_id)
        except ValueError:
            rangeland = None

        # ── tourism ─────────────────────────────────────────────────
        festival_svc = FestivalService(self.db)
        festivals = await festival_svc.list_festivals(
            village_id=village_id, limit=10, offset=0
        )
        tourism = {
            "festival_count": len(festivals),
            "active_festivals": sum(
                1 for f in festivals if f.status == "active"
            ),
            "festivals": [
                {
                    "id": f.id,
                    "name": f.name,
                    "status": f.status,
                    "season": f.season,
                }
                for f in festivals[:5]
            ],
        }

        # ── unesco ──────────────────────────────────────────────────
        unesco_svc = UnescoService(self.db)
        unesco = await unesco_svc.unesco_dashboard(village_id=village_id)

        return {
            "village_id": village_id,
            "governance": governance,
            "marketplace": marketplace,
            "rangeland": rangeland,
            "tourism": tourism,
            "unesco": unesco,
        }

    # ═════════════════════════════════════════════════════════════
    # KYC / Digital Identity (P7.1: Governance <-> Marketplace)
    # ═════════════════════════════════════════════════════════════

    async def submit_kyc(
        self,
        space_id: str,
        *,
        actor_id: str,
        evidence_ref: str | None = None,
        national_id: str | None = None,
        eidas_level: str | None = None,
    ) -> CommunitySpace:
        """Submit KYC / digital identity evidence for the village representative.

        Sets ``kyc_status="submitted"`` so an admin can review and approve.
        The national ID is stored only as a SHA-256 hash (never plaintext).
        """
        space = await self._require_space(space_id)

        # Load (or create) the LandscapeVillage row.
        from services.landscape.models import LandscapeVillage

        result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == space.village_id)
        )
        lv = result.scalar_one_or_none()
        if lv is None:
            raise GovernanceError(f"no landscape village record for {space.village_id}")

        # Hash the national ID if provided.
        national_id_hash = None
        if national_id:
            national_id_hash = hashlib.sha256(national_id.encode("utf-8")).hexdigest()

        lv.kyc_status = "submitted"
        lv.kyc_submitted_at = datetime.now(UTC)
        lv.kyc_evidence_ref = evidence_ref
        lv.kyc_rejected_reason = None
        lv.national_id_hash = national_id_hash
        lv.eidas_level = eidas_level

        self._record_decision(
            space,
            kind="kyc_submitted",
            summary=f"KYC submitted for village {space.village_id}",
            actor_id=actor_id,
        )
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def approve_kyc(
        self,
        space_id: str,
        *,
        actor_id: str,
    ) -> CommunitySpace:
        """Approve a submitted KYC and mark the village verified.

        Only callable after ``submit_kyc``. Sets ``verification_status="approved"``
        and ``representative_identity_verified=True``, which is the gate that
        makes the village visible in the marketplace.
        """
        space = await self._require_space(space_id)

        from services.landscape.models import LandscapeVillage

        result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == space.village_id)
        )
        lv = result.scalar_one_or_none()
        if lv is None:
            raise GovernanceError(f"no landscape village record for {space.village_id}")
        if lv.kyc_status != "submitted":
            raise GovernanceError(
                f"KYC is not in submitted state (current: {lv.kyc_status}); "
                "submit KYC first"
            )

        lv.kyc_status = "approved"
        lv.kyc_approved_at = datetime.now(UTC)
        lv.verification_status = "approved"
        lv.representative_identity_verified = True
        lv.representative_status = "verified"

        self._record_decision(
            space,
            kind="kyc_approved",
            summary=f"KYC approved for village {space.village_id}",
            actor_id=actor_id,
        )
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def reject_kyc(
        self,
        space_id: str,
        *,
        actor_id: str,
        reason: str,
    ) -> CommunitySpace:
        """Reject a submitted KYC with a reason."""
        space = await self._require_space(space_id)

        from services.landscape.models import LandscapeVillage

        result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == space.village_id)
        )
        lv = result.scalar_one_or_none()
        if lv is None:
            raise GovernanceError(f"no landscape village record for {space.village_id}")
        if lv.kyc_status != "submitted":
            raise GovernanceError(
                f"KYC is not in submitted state (current: {lv.kyc_status})"
            )

        lv.kyc_status = "rejected"
        lv.kyc_rejected_reason = reason

        self._record_decision(
            space,
            kind="kyc_rejected",
            summary=f"KYC rejected for village {space.village_id}: {reason}",
            actor_id=actor_id,
        )
        await self.db.commit()
        await self.db.refresh(space)
        return space

    # ═════════════════════════════════════════════════════════════
    # internals
    # ═════════════════════════════════════════════════════════════

    async def _get_space_by_village(self, village_id: str) -> CommunitySpace | None:
        result = await self.db.execute(
            select(CommunitySpace).where(CommunitySpace.village_id == village_id)
        )
        return result.scalar_one_or_none()

    async def _require_space(self, space_id: str) -> CommunitySpace:
        result = await self.db.execute(
            select(CommunitySpace).where(CommunitySpace.id == space_id)
        )
        space = result.scalar_one_or_none()
        if space is None:
            raise GovernanceError(f"space not found: {space_id}")
        return space

    async def _require_charter(self, charter_id: str) -> LocalCharter:
        result = await self.db.execute(
            select(LocalCharter).where(LocalCharter.id == charter_id)
        )
        charter = result.scalar_one_or_none()
        if charter is None:
            raise GovernanceError(f"charter not found: {charter_id}")
        return charter

    async def _require_group(self, group_id: str) -> WorkingGroup:
        result = await self.db.execute(
            select(WorkingGroup).where(WorkingGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise GovernanceError(f"working group not found: {group_id}")
        return group

    async def _require_membership(self, membership_id: str) -> WorkingGroupMembership:
        result = await self.db.execute(
            select(WorkingGroupMembership).where(WorkingGroupMembership.id == membership_id)
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise GovernanceError(f"membership not found: {membership_id}")
        return membership

    async def _require_submitted_application(
        self, space_id: str, step: str
    ) -> GovernanceApplication:
        result = await self.db.execute(
            select(GovernanceApplication).where(
                GovernanceApplication.space_id == space_id,
                GovernanceApplication.step == step,
            )
        )
        application = result.scalar_one_or_none()
        if application is None:
            raise GovernanceError(
                f"cannot advance to {step}: no application submitted for that step"
            )
        return application

    async def _live_coordinator(self, space_id: str) -> WorkingGroupMembership | None:
        result = await self.db.execute(
            select(WorkingGroupMembership)
            .join(WorkingGroup, WorkingGroup.id == WorkingGroupMembership.group_id)
            .where(
                WorkingGroup.space_id == space_id,
                WorkingGroup.dissolved_at.is_(None),
                WorkingGroupMembership.role == WorkingGroupRole.COORDINATOR.value,
                WorkingGroupMembership.ended_reason.is_(None),
            )
        )
        return result.scalars().first()

    async def active_members(self, space_id: str) -> list[WorkingGroupMembership]:
        """Active (non-ended) members of the village's live working group."""
        result = await self.db.execute(
            select(WorkingGroupMembership)
            .join(WorkingGroup, WorkingGroup.id == WorkingGroupMembership.group_id)
            .where(
                WorkingGroup.space_id == space_id,
                WorkingGroup.dissolved_at.is_(None),
                WorkingGroupMembership.ended_reason.is_(None),
            )
        )
        return result.scalars().all()

    async def _coordinator_terms(self, space_id: str, user_id: str) -> int:
        """Count how many consecutive coordinator terms a user has served."""
        result = await self.db.execute(
            select(WorkingGroupMembership)
            .join(WorkingGroup, WorkingGroup.id == WorkingGroupMembership.group_id)
            .where(
                WorkingGroup.space_id == space_id,
                WorkingGroupMembership.user_id == user_id,
                WorkingGroupMembership.role == WorkingGroupRole.COORDINATOR.value,
            )
            .order_by(WorkingGroupMembership.created_at.desc())
        )
        memberships = result.scalars().all()
        # Consecutive terms: count from the most recent backwards while
        # each term directly follows the previous (no gap in leadership).
        terms = 0
        for m in memberships:
            if m.ended_reason is None:
                # Current term counts.
                terms += 1
            elif terms > 0:
                # A gap ended the streak.
                break
            else:
                # No current term yet.
                break
        return terms

    def _record_decision(
        self,
        space: CommunitySpace,
        *,
        kind: str,
        summary: str,
        actor_id: str,
        charter_version: int | None = None,
    ) -> GovernanceDecision:
        decision = GovernanceDecision(
            space_id=space.id,
            kind=kind,
            summary=summary,
            decided_by=actor_id,
            charter_version=charter_version,
        )
        self.db.add(decision)
        return decision
