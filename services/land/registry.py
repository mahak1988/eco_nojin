"""سرویس ثبت زمین (Land Registry / Cadastre)

مالکیت و حقوق ارتفاق اراضی: قطعهٔ سنددار (parcel)، مالکیت سهامی با تاریخ
اثر و گردش کار تأیید ثبت، و حقوق چراگری و گذرگاه فصلی برای افراد یا
اجوامع عشایری با چرخهٔ pending/active/expired/revoked.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import LandOwnership as LandOwnershipDB
from database.models import LandParcel as LandParcelDB
from database.models import LandTenureRight as LandTenureRightDB
from engine.land.models import (
    CadastralSummary,
    HolderType,
    LandOwnershipInput,
    LandOwnershipRecord,
    LandParcel,
    LandParcelInput,
    LandTenureRight,
    TenureRightStatus,
    TenureRightType,
)

_HUNDRED = Decimal("100")
_ZERO = Decimal("0")
_OPEN_TENURE_STATUSES = (TenureRightStatus.PENDING, TenureRightStatus.ACTIVE)


def _month_window(start: int, end: int) -> set[int]:
    """Month numbers covered by a season window, wrapping across the year end."""
    if start <= end:
        return set(range(start, end + 1))
    return set(range(start, 13)) | set(range(1, end + 1))


def _to_decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _parcel_to_model(row: LandParcelDB) -> LandParcel:
    return LandParcel(
        parcel_id=row.id,
        deed_no=row.deed_no,
        village_id=row.village_id,
        name=row.name,
        area_ha=row.area_ha,
        boundary=row.boundary,
        land_use=row.land_use,
        capability_class=row.capability_class,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _ownership_to_model(row: LandOwnershipDB) -> LandOwnershipRecord:
    return LandOwnershipRecord(
        ownership_id=row.id,
        parcel_id=row.parcel_id,
        owner_user_id=row.owner_user_id,
        ownership_type=row.ownership_type,
        share_pct=row.share_pct,
        effective_from=row.effective_from,
        effective_to=row.effective_to,
        evidence_ref=row.evidence_ref,
        is_verified=row.is_verified,
        verified_by=row.verified_by,
        verified_at=row.verified_at,
        created_at=row.created_at,
    )


def _right_to_model(row: LandTenureRightDB) -> LandTenureRight:
    return LandTenureRight(
        right_id=row.id,
        right_type=row.right_type,
        parcel_id=row.parcel_id,
        holder_type=row.holder_type,
        holder_user_id=row.holder_user_id,
        community_id=row.community_id,
        season_start=row.season_start,
        season_end=row.season_end,
        granted_by=row.granted_by,
        status=row.status,
        created_at=row.created_at,
        activated_at=row.activated_at,
        closed_at=row.closed_at,
    )


class LandRegistryService:
    """Cadastral registry: parcels, effective-dated ownership, tenure rights.

    Session pattern follows ``services.landscape.service``: one
    ``AsyncSession`` per request, explicit ``commit()``/``refresh()`` and
    ``ValueError`` for every domain rejection so routers can map it to a
    4xx without catching broad exceptions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ───────────────────────────────────────────────────────────
    # Parcels
    # ───────────────────────────────────────────────────────────

    async def create_parcel(self, payload: LandParcelInput) -> LandParcel:
        """ثبت قطعهٔ جدید، بدون تکرار بر پایهٔ شماره سند."""
        existing = await self.db.execute(
            select(LandParcelDB.deed_no).where(LandParcelDB.deed_no == payload.deed_no)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError(f"parcel with deed_no '{payload.deed_no}' already exists")
        if payload.parcel_id is not None and await self.get_parcel(payload.parcel_id):
            raise ValueError(f"parcel_id '{payload.parcel_id}' already exists")

        parcel = LandParcelDB(
            id=payload.parcel_id or str(uuid4()),
            deed_no=payload.deed_no,
            village_id=payload.village_id,
            name=payload.name,
            area_ha=payload.area_ha,
            boundary=payload.boundary,
            land_use=payload.land_use.value,
            capability_class=(
                payload.capability_class.value if payload.capability_class is not None else None
            ),
        )
        self.db.add(parcel)
        await self.db.commit()
        await self.db.refresh(parcel)
        return _parcel_to_model(parcel)

    async def get_parcel(self, parcel_id: str) -> LandParcel | None:
        row = await self.db.get(LandParcelDB, parcel_id)
        return _parcel_to_model(row) if row is not None else None

    async def list_parcels_by_village(self, village_id: str) -> list[LandParcel]:
        result = await self.db.execute(
            select(LandParcelDB)
            .where(LandParcelDB.village_id == village_id)
            .order_by(LandParcelDB.created_at, LandParcelDB.deed_no)
        )
        return [_parcel_to_model(row) for row in result.scalars()]

    async def list_parcels_by_owner(self, owner_user_id: str) -> list[LandParcel]:
        result = await self.db.execute(
            select(LandParcelDB)
            .join(LandOwnershipDB, LandOwnershipDB.parcel_id == LandParcelDB.id)
            .where(
                LandOwnershipDB.owner_user_id == owner_user_id,
                or_(
                    LandOwnershipDB.effective_to.is_(None),
                    LandOwnershipDB.effective_to >= date.today(),
                ),
            )
            .distinct()
            .order_by(LandParcelDB.created_at)
        )
        return [_parcel_to_model(row) for row in result.scalars()]

    # ───────────────────────────────────────────────────────────
    # Ownership
    # ───────────────────────────────────────────────────────────

    async def _active_share_total(self, parcel_id: str) -> Decimal:
        """Sum of shares whose record is still open (effective_to is NULL or future)."""
        result = await self.db.execute(
            select(LandOwnershipDB.share_pct).where(
                LandOwnershipDB.parcel_id == parcel_id,
                or_(
                    LandOwnershipDB.effective_to.is_(None),
                    LandOwnershipDB.effective_to >= date.today(),
                ),
            )
        )
        total = _ZERO
        for share in result.scalars():
            total += _to_decimal(share)
        return total

    async def record_ownership(self, payload: LandOwnershipInput) -> LandOwnershipRecord:
        """ثبت مالکیت؛ مجموع سهام فعال هر قطعه نباید از ۱۰۰٪ فراتر رود."""
        if await self.db.get(LandParcelDB, payload.parcel_id) is None:
            raise ValueError(f"parcel not found: {payload.parcel_id}")

        incoming = _to_decimal(payload.share_pct)
        current = await self._active_share_total(payload.parcel_id)
        if current + incoming > _HUNDRED:
            raise ValueError(
                f"ownership shares for parcel {payload.parcel_id} would total "
                f"{current + incoming}%, exceeding the 100% limit"
            )

        record = LandOwnershipDB(
            parcel_id=payload.parcel_id,
            owner_user_id=payload.owner_user_id,
            ownership_type=payload.ownership_type.value,
            share_pct=payload.share_pct,
            effective_from=payload.effective_from or date.today(),
            effective_to=payload.effective_to,
            evidence_ref=payload.evidence_ref,
            is_verified=False,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return _ownership_to_model(record)

    async def get_ownership_record(self, ownership_id: str) -> LandOwnershipRecord | None:
        row = await self.db.get(LandOwnershipDB, ownership_id)
        return _ownership_to_model(row) if row is not None else None

    async def list_ownership_history(self, parcel_id: str) -> list[LandOwnershipRecord]:
        result = await self.db.execute(
            select(LandOwnershipDB)
            .where(LandOwnershipDB.parcel_id == parcel_id)
            .order_by(LandOwnershipDB.effective_from, LandOwnershipDB.created_at)
        )
        return [_ownership_to_model(row) for row in result.scalars()]

    async def transfer_ownership(
        self,
        ownership_id: str,
        new_owner_user_id: str,
        effective_date: date | None = None,
        evidence_ref: str | None = None,
    ) -> LandOwnershipRecord:
        """انتقال مالکیت: بستن رکورد قبلی و افتتاح رکورد جدید در یک تراکنش."""
        record = await self.db.get(LandOwnershipDB, ownership_id)
        if record is None:
            raise ValueError(f"ownership record not found: {ownership_id}")
        if record.effective_to is not None:
            raise ValueError(
                f"ownership record {ownership_id} is closed (effective_to "
                f"{record.effective_to}); cannot transfer"
            )

        transfer_date = effective_date or date.today()
        successor = LandOwnershipDB(
            parcel_id=record.parcel_id,
            owner_user_id=new_owner_user_id,
            ownership_type=record.ownership_type,
            share_pct=record.share_pct,
            effective_from=transfer_date,
            effective_to=None,
            evidence_ref=evidence_ref if evidence_ref is not None else record.evidence_ref,
            is_verified=False,
        )
        try:
            record.effective_to = transfer_date
            self.db.add(successor)
            await self.db.commit()
            await self.db.refresh(record)
            await self.db.refresh(successor)
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(
                f"transfer of ownership {ownership_id} conflicts with an existing record"
            ) from None
        except Exception:
            await self.db.rollback()
            raise
        return _ownership_to_model(successor)

    async def verify_ownership(self, ownership_id: str, verified_by: str) -> LandOwnershipRecord:
        """تأیید مالکیت توسط ثبت‌کننده (گردش کار تأیید)."""
        record = await self.db.get(LandOwnershipDB, ownership_id)
        if record is None:
            raise ValueError(f"ownership record not found: {ownership_id}")
        if record.is_verified:
            raise ValueError(f"ownership record {ownership_id} is already verified")

        record.is_verified = True
        record.verified_by = verified_by
        record.verified_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(record)
        return _ownership_to_model(record)

    # ───────────────────────────────────────────────────────────
    # Tenure rights (grazing / seasonal corridors)
    # ───────────────────────────────────────────────────────────

    async def grant_tenure_right(
        self,
        right_type: TenureRightType,
        parcel_id: str,
        holder_type: HolderType,
        season_start: int,
        season_end: int,
        granted_by: str,
        holder_user_id: str | None = None,
        community_id: str | None = None,
    ) -> LandTenureRight:
        """اعطای حق چراگری/گذرگاه فصل؛ قطعه+فصول تکراری پذیرفته نمی‌شود."""
        if await self.db.get(LandParcelDB, parcel_id) is None:
            raise ValueError(f"parcel not found: {parcel_id}")
        if holder_type is HolderType.USER and not holder_user_id:
            raise ValueError("holder_user_id is required for a user-held right")
        if holder_type is HolderType.COMMUNITY and not community_id:
            raise ValueError("community_id is required for a community-held right")

        window = _month_window(season_start, season_end)
        existing = await self.db.execute(
            select(LandTenureRightDB).where(
                LandTenureRightDB.parcel_id == parcel_id,
                LandTenureRightDB.status.in_([s.value for s in _OPEN_TENURE_STATUSES]),
            )
        )
        for row in existing.scalars():
            if window & _month_window(row.season_start, row.season_end):
                raise ValueError(
                    f"parcel {parcel_id} already has an open {row.right_type} right covering "
                    f"months {row.season_start}-{row.season_end}; seasons must not overlap"
                )

        right = LandTenureRightDB(
            right_type=right_type.value,
            parcel_id=parcel_id,
            holder_type=holder_type.value,
            holder_user_id=holder_user_id if holder_type is HolderType.USER else None,
            community_id=community_id if holder_type is HolderType.COMMUNITY else None,
            season_start=season_start,
            season_end=season_end,
            granted_by=granted_by,
            status=TenureRightStatus.PENDING.value,
        )
        self.db.add(right)
        await self.db.commit()
        await self.db.refresh(right)
        return _right_to_model(right)

    async def _get_right(self, right_id: str) -> LandTenureRightDB:
        right = await self.db.get(LandTenureRightDB, right_id)
        if right is None:
            raise ValueError(f"tenure right not found: {right_id}")
        return right

    async def activate_tenure_right(self, right_id: str) -> LandTenureRight:
        """فعال‌سازی حق در انتظار (pending → active)."""
        right = await self._get_right(right_id)
        if right.status != TenureRightStatus.PENDING.value:
            raise ValueError(f"cannot activate a tenure right in status '{right.status}'")
        right.status = TenureRightStatus.ACTIVE.value
        right.activated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(right)
        return _right_to_model(right)

    async def expire_tenure_right(self, right_id: str) -> LandTenureRight:
        """پایان دورهٔ اعتبار (active → expired)."""
        right = await self._get_right(right_id)
        if right.status != TenureRightStatus.ACTIVE.value:
            raise ValueError(f"cannot expire a tenure right in status '{right.status}'")
        right.status = TenureRightStatus.EXPIRED.value
        right.closed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(right)
        return _right_to_model(right)

    async def revoke_tenure_right(self, right_id: str) -> LandTenureRight:
        """باطل کردن حق (pending|active → revoked)."""
        right = await self._get_right(right_id)
        if right.status not in tuple(s.value for s in _OPEN_TENURE_STATUSES):
            raise ValueError(f"cannot revoke a tenure right in status '{right.status}'")
        right.status = TenureRightStatus.REVOKED.value
        right.closed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(right)
        return _right_to_model(right)

    async def list_rights_by_holder(self, holder_user_id: str) -> list[LandTenureRight]:
        result = await self.db.execute(
            select(LandTenureRightDB)
            .where(LandTenureRightDB.holder_user_id == holder_user_id)
            .order_by(LandTenureRightDB.created_at, LandTenureRightDB.id)
        )
        return [_right_to_model(row) for row in result.scalars()]

    async def list_rights_by_community(self, community_id: str) -> list[LandTenureRight]:
        result = await self.db.execute(
            select(LandTenureRightDB)
            .where(LandTenureRightDB.community_id == community_id)
            .order_by(LandTenureRightDB.created_at, LandTenureRightDB.id)
        )
        return [_right_to_model(row) for row in result.scalars()]

    async def list_rights_for_parcel(self, parcel_id: str) -> list[LandTenureRight]:
        result = await self.db.execute(
            select(LandTenureRightDB)
            .where(LandTenureRightDB.parcel_id == parcel_id)
            .order_by(LandTenureRightDB.created_at, LandTenureRightDB.id)
        )
        return [_right_to_model(row) for row in result.scalars()]

    # ───────────────────────────────────────────────────────────
    # Cadastral summary
    # ───────────────────────────────────────────────────────────

    async def cadastral_summary(self, village_id: str | None = None) -> CadastralSummary:
        """خلاصهٔ سنجش مرکز: تعداد، مساحت به تفکیک کاربری، و شمار حقوق."""
        parcel_stmt = select(LandParcelDB)
        if village_id is not None:
            parcel_stmt = parcel_stmt.where(LandParcelDB.village_id == village_id)
        parcels = (await self.db.execute(parcel_stmt)).scalars().all()
        parcel_ids = [parcel.id for parcel in parcels]

        total_area = _ZERO
        area_by_use: dict[str, Decimal] = {}
        for parcel in parcels:
            area = _to_decimal(parcel.area_ha) if parcel.area_ha is not None else _ZERO
            total_area += area
            area_by_use[parcel.land_use] = area_by_use.get(parcel.land_use, _ZERO) + area

        ownership_count = 0
        verified_count = 0
        tenure_count = 0
        active_tenure = 0
        tenure_by_type: dict[str, int] = {}
        if parcel_ids:
            ownerships = (
                (
                    await self.db.execute(
                        select(LandOwnershipDB).where(
                            LandOwnershipDB.parcel_id.in_(parcel_ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
            ownership_count = len(ownerships)
            verified_count = sum(1 for row in ownerships if row.is_verified)

            rights = (
                (
                    await self.db.execute(
                        select(LandTenureRightDB).where(
                            LandTenureRightDB.parcel_id.in_(parcel_ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
            tenure_count = len(rights)
            active_tenure = sum(
                1 for right in rights if right.status == TenureRightStatus.ACTIVE.value
            )
            for right in rights:
                tenure_by_type[right.right_type] = tenure_by_type.get(right.right_type, 0) + 1

        return CadastralSummary(
            village_id=village_id,
            parcel_count=len(parcels),
            total_area_ha=total_area,
            area_by_land_use=area_by_use,
            ownership_record_count=ownership_count,
            verified_ownership_count=verified_count,
            tenure_right_count=tenure_count,
            active_tenure_count=active_tenure,
            tenure_counts_by_type=tenure_by_type,
        )
