"""Tests for the land registry (cadastral ownership and tenure) service."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from engine.land.models import (
    CadastralSummary,
    HolderType,
    LandCapabilityClass,
    LandOwnershipInput,
    LandParcelInput,
    LandTenureRight,
    LandUseType,
    OwnershipType,
    TenureRightStatus,
    TenureRightType,
)
from services.land.registry import LandRegistryService
from services.marketplace.models import NomadicCommunity


def _boundary() -> dict:
    """A small GeoJSON polygon (closed ring)."""
    return {
        "type": "Polygon",
        "coordinates": [
            [[51.0, 32.0], [51.1, 32.0], [51.1, 32.1], [51.0, 32.1], [51.0, 32.0]]
        ],
    }


@pytest.fixture
async def service(db_session):
    return LandRegistryService(db_session)


async def _make_parcel(service: LandRegistryService, **overrides) -> object:
    payload = LandParcelInput(
        parcel_id=overrides.pop("parcel_id", None),
        deed_no=overrides.pop("deed_no", "D-001"),
        village_id=overrides.pop("village_id", "village-1"),
        name=overrides.pop("name", "پارسل شالیزار"),
        area_ha=overrides.pop("area_ha", Decimal("12.50")),
        land_use=overrides.pop("land_use", LandUseType.AGRICULTURAL),
        boundary=overrides.pop("boundary", _boundary()),
    )
    return await service.create_parcel(payload)


def _ownership_input(parcel_id: str, owner_user_id: str, share_pct, **kwargs) -> LandOwnershipInput:
    return LandOwnershipInput(
        parcel_id=parcel_id,
        owner_user_id=owner_user_id,
        ownership_type=OwnershipType.INDIVIDUAL,
        share_pct=share_pct,
        **kwargs,
    )


class TestParcels:
    async def test_create_persists_and_reads_back(self, service):
        parcel = await _make_parcel(service, deed_no="D-100")
        assert parcel.parcel_id
        assert parcel.area_ha == Decimal("12.50")
        assert parcel.boundary == _boundary()
        assert parcel.created_at is not None

        fetched = await service.get_parcel(parcel.parcel_id)
        assert fetched is not None
        assert fetched.deed_no == "D-100"
        assert fetched.land_use is LandUseType.AGRICULTURAL

        by_village = await service.list_parcels_by_village("village-1")
        assert [p.parcel_id for p in by_village] == [parcel.parcel_id]

        assert await service.get_parcel("missing-parcel") is None

    async def test_capability_class_round_trip(self, service):
        payload = LandParcelInput(
            deed_no="D-CAP",
            village_id="village-1",
            name="دامنه",
            area_ha=Decimal("5"),
            land_use=LandUseType.AGRICULTURAL,
            capability_class=LandCapabilityClass.CLASS_III,
        )
        parcel = await service.create_parcel(payload)
        fetched = await service.get_parcel(parcel.parcel_id)
        assert fetched is not None
        assert fetched.capability_class is LandCapabilityClass.CLASS_III

    async def test_duplicate_deed_no_rejected(self, service):
        await _make_parcel(service, deed_no="D-DUP")
        with pytest.raises(ValueError, match="deed_no"):
            await _make_parcel(service, deed_no="D-DUP")

    async def test_supplied_parcel_id_is_honoured(self, service):
        parcel = await _make_parcel(service, parcel_id=None)
        with pytest.raises(ValueError, match="already exists"):
            await _make_parcel(service, deed_no="D-OTHER", parcel_id=parcel.parcel_id)


class TestOwnership:
    async def test_share_overflow_rejected(self, service):
        parcel = await _make_parcel(service)
        first = await service.record_ownership(
            _ownership_input(parcel.parcel_id, "user-a", Decimal("60"))
        )
        assert first.share_pct == Decimal("60")
        assert first.is_verified is False

        with pytest.raises(ValueError, match="100% limit"):
            await service.record_ownership(
                _ownership_input(parcel.parcel_id, "user-b", Decimal("50"))
            )

        second = await service.record_ownership(
            _ownership_input(parcel.parcel_id, "user-b", Decimal("40"))
        )
        assert second.owner_user_id == "user-b"

        with pytest.raises(ValueError, match="100% limit"):
            await service.record_ownership(
                _ownership_input(parcel.parcel_id, "user-c", Decimal("0.01"))
            )

    async def test_record_ownership_requires_existing_parcel(self, service):
        with pytest.raises(ValueError, match="parcel not found"):
            await service.record_ownership(
                _ownership_input("missing-parcel", "user-a", Decimal("10"))
            )

    async def test_transfer_closes_old_and_opens_new(self, service):
        parcel = await _make_parcel(service)
        original = await service.record_ownership(
            _ownership_input(
                parcel.parcel_id,
                "user-a",
                Decimal("100"),
                effective_from=date(2020, 1, 1),
                evidence_ref="deed-scan-1",
            )
        )
        successor = await service.transfer_ownership(
            original.ownership_id, "user-b", date(2020, 6, 1)
        )
        assert successor.owner_user_id == "user-b"
        assert successor.share_pct == Decimal("100")
        assert successor.effective_from == date(2020, 6, 1)
        assert successor.is_verified is False

        closed = await service.get_ownership_record(original.ownership_id)
        assert closed is not None
        assert closed.effective_to == date(2020, 6, 1)

        history = await service.list_ownership_history(parcel.parcel_id)
        assert [record.owner_user_id for record in history] == ["user-a", "user-b"]

        assert await service.list_parcels_by_owner("user-a") == []
        owned_by_b = await service.list_parcels_by_owner("user-b")
        assert [p.parcel_id for p in owned_by_b] == [parcel.parcel_id]

    async def test_transfer_of_closed_record_rejected(self, service):
        parcel = await _make_parcel(service)
        original = await service.record_ownership(
            _ownership_input(
                parcel.parcel_id, "user-a", Decimal("100"), effective_from=date(2020, 1, 1)
            )
        )
        await service.transfer_ownership(original.ownership_id, "user-b", date(2020, 6, 1))
        with pytest.raises(ValueError, match="closed"):
            await service.transfer_ownership(original.ownership_id, "user-c", date(2020, 9, 1))

    async def test_transfer_is_atomic_on_failure(self, service, monkeypatch):
        parcel = await _make_parcel(service)
        original = await service.record_ownership(
            _ownership_input(parcel.parcel_id, "user-a", Decimal("100"))
        )

        async def failing_commit():
            raise RuntimeError("commit failed")

        monkeypatch.setattr(service.db, "commit", failing_commit)
        with pytest.raises(RuntimeError):
            await service.transfer_ownership(original.ownership_id, "user-b", date(2020, 6, 1))

        unchanged = await service.get_ownership_record(original.ownership_id)
        assert unchanged is not None
        assert unchanged.effective_to is None
        history = await service.list_ownership_history(parcel.parcel_id)
        assert len(history) == 1

    async def test_verify_ownership_workflow(self, service):
        parcel = await _make_parcel(service)
        record = await service.record_ownership(
            _ownership_input(
                parcel.parcel_id, "user-a", Decimal("100"), evidence_ref="deed-scan-9"
            )
        )
        assert record.evidence_ref == "deed-scan-9"

        verified = await service.verify_ownership(record.ownership_id, "registrar-1")
        assert verified.is_verified is True
        assert verified.verified_by == "registrar-1"
        assert verified.verified_at is not None

        with pytest.raises(ValueError, match="already verified"):
            await service.verify_ownership(record.ownership_id, "registrar-2")

    async def test_verify_missing_record_rejected(self, service):
        with pytest.raises(ValueError, match="not found"):
            await service.verify_ownership("missing-ownership", "registrar-1")


class TestTenureRights:
    async def test_grazing_overlap_rejected(self, service):
        parcel = await _make_parcel(service, land_use=LandUseType.RANGELAND)
        first = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            parcel.parcel_id,
            HolderType.USER,
            4,
            7,
            "council-1",
            holder_user_id="user-a",
        )
        assert first.status is TenureRightStatus.PENDING
        assert first.right_type is TenureRightType.GRAZING

        with pytest.raises(ValueError, match="overlap"):
            await service.grant_tenure_right(
                TenureRightType.GRAZING,
                parcel.parcel_id,
                HolderType.USER,
                6,
                9,
                "council-1",
                holder_user_id="user-b",
            )

        non_overlapping = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            parcel.parcel_id,
            HolderType.USER,
            8,
            11,
            "council-1",
            holder_user_id="user-b",
        )
        assert non_overlapping.season_start == 8
        assert len(await service.list_rights_for_parcel(parcel.parcel_id)) == 2

    async def test_expired_right_frees_the_season(self, service):
        parcel = await _make_parcel(service, land_use=LandUseType.RANGELAND)
        first = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            parcel.parcel_id,
            HolderType.USER,
            4,
            7,
            "council-1",
            holder_user_id="user-a",
        )
        activated = await service.activate_tenure_right(first.right_id)
        assert activated.status is TenureRightStatus.ACTIVE
        assert activated.activated_at is not None

        expired = await service.expire_tenure_right(first.right_id)
        assert expired.status is TenureRightStatus.EXPIRED
        assert expired.closed_at is not None

        second = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            parcel.parcel_id,
            HolderType.USER,
            5,
            6,
            "council-1",
            holder_user_id="user-b",
        )
        assert second.status is TenureRightStatus.PENDING

    async def test_season_window_wraps_year_end(self, service):
        parcel = await _make_parcel(service, land_use=LandUseType.RANGELAND)
        winter = await service.grant_tenure_right(
            TenureRightType.SEASONAL_CORRIDOR,
            parcel.parcel_id,
            HolderType.USER,
            11,
            3,
            "council-1",
            holder_user_id="user-a",
        )
        await service.activate_tenure_right(winter.right_id)
        with pytest.raises(ValueError, match="overlap"):
            await service.grant_tenure_right(
                TenureRightType.GRAZING,
                parcel.parcel_id,
                HolderType.USER,
                1,
                2,
                "council-1",
                holder_user_id="user-b",
            )

    async def test_lifecycle_transitions_and_revocation(self, service):
        parcel = await _make_parcel(service)
        right = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            parcel.parcel_id,
            HolderType.USER,
            5,
            8,
            "council-1",
            holder_user_id="user-a",
        )
        with pytest.raises(ValueError, match="cannot expire"):
            await service.expire_tenure_right(right.right_id)

        await service.activate_tenure_right(right.right_id)
        with pytest.raises(ValueError, match="cannot activate"):
            await service.activate_tenure_right(right.right_id)

        revoked = await service.revoke_tenure_right(right.right_id)
        assert revoked.status is TenureRightStatus.REVOKED
        assert revoked.closed_at is not None

        with pytest.raises(ValueError, match="cannot revoke"):
            await service.revoke_tenure_right(right.right_id)

    async def test_grant_requires_matching_holder(self, service):
        parcel = await _make_parcel(service)
        with pytest.raises(ValueError, match="holder_user_id is required"):
            await service.grant_tenure_right(
                TenureRightType.GRAZING,
                parcel.parcel_id,
                HolderType.USER,
                4,
                6,
                "council-1",
            )
        with pytest.raises(ValueError, match="community_id is required"):
            await service.grant_tenure_right(
                TenureRightType.GRAZING,
                parcel.parcel_id,
                HolderType.COMMUNITY,
                4,
                6,
                "council-1",
            )

    async def test_grant_requires_existing_parcel(self, service):
        with pytest.raises(ValueError, match="parcel not found"):
            await service.grant_tenure_right(
                TenureRightType.GRAZING,
                "missing-parcel",
                HolderType.USER,
                4,
                6,
                "council-1",
                holder_user_id="user-a",
            )

    async def test_rights_are_queryable_by_holder(self, service):
        parcel = await _make_parcel(service)
        right = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            parcel.parcel_id,
            HolderType.USER,
            4,
            6,
            "council-1",
            holder_user_id="user-a",
        )
        held = await service.list_rights_by_holder("user-a")
        assert [r.right_id for r in held] == [right.right_id]
        assert await service.list_rights_by_holder("user-b") == []


class TestCadastralSummary:
    async def test_summary_aggregates(self, service):
        agricultural = await _make_parcel(
            service, deed_no="D-AG", area_ha=Decimal("10"), land_use=LandUseType.AGRICULTURAL
        )
        rangeland = await _make_parcel(
            service, deed_no="D-RNG", area_ha=Decimal("25.5"), land_use=LandUseType.RANGELAND
        )
        await _make_parcel(
            service,
            deed_no="D-ELSEWHERE",
            village_id="village-2",
            area_ha=Decimal("100"),
            land_use=LandUseType.FOREST,
        )

        record = await service.record_ownership(
            _ownership_input(agricultural.parcel_id, "user-a", Decimal("100"))
        )
        await service.record_ownership(
            LandOwnershipInput(
                parcel_id=rangeland.parcel_id,
                owner_user_id="community-owner",
                ownership_type=OwnershipType.TRIBAL_COMMUNAL,
                share_pct=Decimal("100"),
            )
        )
        await service.verify_ownership(record.ownership_id, "registrar-1")

        right = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            rangeland.parcel_id,
            HolderType.COMMUNITY,
            4,
            6,
            "council-1",
            community_id="comm-1",
        )
        await service.activate_tenure_right(right.right_id)

        summary = await service.cadastral_summary("village-1")
        assert summary.village_id == "village-1"
        assert summary.parcel_count == 2
        assert summary.total_area_ha == Decimal("35.5")
        assert summary.area_by_land_use["agricultural"] == Decimal("10")
        assert summary.area_by_land_use["rangeland"] == Decimal("25.5")
        assert summary.ownership_record_count == 2
        assert summary.verified_ownership_count == 1
        assert summary.tenure_right_count == 1
        assert summary.active_tenure_count == 1
        assert summary.tenure_counts_by_type == {"grazing": 1}

        whole_registry = await service.cadastral_summary()
        assert whole_registry.parcel_count == 3
        assert whole_registry.village_id is None

    async def test_summary_for_village_without_parcels(self, service):
        summary = await service.cadastral_summary("empty-village")
        assert summary.parcel_count == 0
        assert summary.total_area_ha == Decimal("0")
        assert summary.area_by_land_use == {}
        assert summary.ownership_record_count == 0
        assert summary.tenure_right_count == 0


class TestNomadicCommunityTenancy:
    async def test_tribal_community_holds_grazing_rights_on_rangeland(self, service, db_session):
        rangeland = await _make_parcel(
            service,
            deed_no="D-RNG-TRIBAL",
            land_use=LandUseType.RANGELAND,
            area_ha=Decimal("500"),
        )
        community = NomadicCommunity(
            name="عشایر قشقایی",
            village_id="village-1",
            pasture_area_ha=Decimal("500"),
        )
        db_session.add(community)
        await db_session.commit()

        right = await service.grant_tenure_right(
            TenureRightType.GRAZING,
            rangeland.parcel_id,
            HolderType.COMMUNITY,
            4,
            6,
            "council-1",
            community_id=community.id,
        )
        activated = await service.activate_tenure_right(right.right_id)
        assert activated.holder_type is HolderType.COMMUNITY
        assert activated.community_id == community.id
        assert activated.holder_user_id is None
        assert activated.status is TenureRightStatus.ACTIVE

        held = await service.list_rights_by_community(community.id)
        assert [r.right_id for r in held] == [right.right_id]
        assert held[0].right_type is TenureRightType.GRAZING

    async def test_community_can_own_parcels_communally(self, service):
        parcel = await _make_parcel(service, deed_no="D-COMMUNAL")
        record = await service.record_ownership(
            LandOwnershipInput(
                parcel_id=parcel.parcel_id,
                owner_user_id="community-lead",
                ownership_type=OwnershipType.TRIBAL_COMMUNAL,
                share_pct=Decimal("100"),
            )
        )
        assert record.ownership_type is OwnershipType.TRIBAL_COMMUNAL


class TestRegistryContracts:
    def test_land_tenure_right_contract_validates_holder(self):
        base = {
            "right_id": "right-1",
            "right_type": TenureRightType.GRAZING,
            "parcel_id": "parcel-1",
            "season_start": 1,
            "season_end": 2,
            "granted_by": "council-1",
            "created_at": datetime.now(UTC),
        }
        with pytest.raises(ValidationError):
            LandTenureRight(holder_type=HolderType.USER, **base)
        with pytest.raises(ValidationError):
            LandTenureRight(holder_type=HolderType.COMMUNITY, **base)

        ok = LandTenureRight(holder_type=HolderType.USER, holder_user_id="user-a", **base)
        assert ok.holder_user_id == "user-a"
        assert ok.status is TenureRightStatus.PENDING

    def test_cadastral_summary_defaults(self):
        summary = CadastralSummary()
        assert summary.parcel_count == 0
        assert summary.total_area_ha == Decimal("0")
        assert summary.area_by_land_use == {}
        assert summary.tenure_counts_by_type == {}

    def test_ownership_input_share_bounds(self):
        payload = LandOwnershipInput(
            parcel_id="p",
            owner_user_id="u",
            ownership_type=OwnershipType.STATE,
            share_pct=Decimal("25.5"),
        )
        assert payload.share_pct == Decimal("25.5")
        with pytest.raises(ValidationError):
            LandOwnershipInput(
                parcel_id="p",
                owner_user_id="u",
                ownership_type=OwnershipType.STATE,
                share_pct=Decimal("101"),
            )

    def test_parcel_input_defaults(self):
        payload = LandParcelInput(
            deed_no="D-1", village_id="v", name="n", area_ha=Decimal("3")
        )
        assert payload.land_use is LandUseType.AGRICULTURAL
        assert payload.capability_class is None
        assert payload.parcel_id is None
