"""
سرویس مرکز توسعه روستا (Village Development Hub Service)
=========================================================

این سرویس شامل منطق کسب‌وکار برای 18 ماژول توسعه روستا است:
1. پروفایل روستا — اطلاعات جامع + داشبورد
2. ظرفیت‌ها — ظرفیت‌های اقتصادی/گردشگيری
3. فرصت‌ها — فرصت‌های سرمایه‌گذاری و کارآفرینی
4. پروژه‌ها — پروژه‌های در حال اجرا با پیگیری پیشرفت
5. کارآفرینان — پروفایل مهارت‌ها و علاقه‌ها
6. سرمایه‌گذاری — درخواست/تأیید سرمایه
7. گردشگيری — سرویس‌های اقامتگاه/تور/فعالیت
8. رویدادها — رویدادهای فرهنگی و گردشگيری
9. نیازها — نیازهای توسعه شناسایی شده
10. برند — داستان و ارزش‌های برند روستا
11. تجربه‌ها — گردشگری تجربه‌ای
12. مقصد — صفحه مقصد گردشگری روستا
13. تقاضاهای B2B — تطبیق تقاضا با ظرفیت روستا
14. اتصال — پیوند توانمندی با کارآفرین
15. شکاف‌های توسعه — تحلیل هوشمند شکاف‌ها
16. جشنواره‌ها — جشنواره و نمایشگاه روستایی
17. جوامع عشایری — امکانات و نیازهای جوامع عشایری
18. پرونده — پرونده توسعه روستا

حکمرانی: هر مسیر نوشتاری (ثبت/ویرایش) کنترل دسترسی دارد — فقط ادمین پلتفرم
یا عضو فعال شورای منظر با یکی از نقش‌های نوشتاری ``_GOVERNANCE_WRITE_ROLES``
مجاز است (``_ensure_village_write`` / ``_check_governance_permission``)، و
موجودیت‌های بدون دامنهٔ روستا (جوامع عشایری، جشنواره) در سطح منظر کنترل
می‌شوند (``_ensure_landscape_write``). مسیرهای خواندنی آزاد هستند.
"""

import logging
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.landscape.models import (
    LandscapeGovernanceMember,
    LandscapeVillage,
)
from services.marketplace.models import MarketplaceCommissionRule
from services.marketplace.models.village_hub import (
    B2BDemand,
    EntrepreneurProfile,
    NomadicCommunity,
    OpportunityMaturity,
    OpportunityStatus,
    VillageBrand,
    VillageCapability,
    VillageDestination,
    VillageDevelopmentGap,
    VillageEngagement,
    VillageEvent,
    VillageEventRegistration,
    VillageExperience,
    VillageFestival,
    VillageInvestment,
    VillageNeed,
    VillageOpportunity,
    VillageOpportunityInterest,
    VillageProject,
    VillageTourismService,
)
from services.territory.models import TerritoryFund

logger = logging.getLogger(__name__)


async def _emit_hub_event(
    event_type: str, aggregate_type: str, aggregate_id: str, payload: dict
) -> None:
    """Publish a village-hub domain event (best-effort, failure-isolated).

    Gated on the same ``enable_event_bus`` flag the gateway uses, and every
    failure is logged and swallowed so a broker outage never breaks the
    committed row. Uses the generic publisher on the ``hub`` domain. Imported
    lazily to keep the gateway stack off the module import path.
    """
    try:
        from engine.hydroma.config.settings import get_settings

        if not get_settings().enable_event_bus:
            return
        from services.api_gateway.eventbus.publisher import publish_event

        await publish_event("hub", event_type, aggregate_type, aggregate_id, payload)
    except Exception as exc:  # noqa: BLE001 - broker failure must not propagate
        logger.warning("hub event %r not published: %s", event_type, exc)


def _notify(user_id: str, title: str, body: str = "", ntype: str = "system") -> None:
    """Deliver one owner-scoped in-app notification (best-effort, failure-isolated).

    ``NotificationDbService`` is a synchronous session API, so the notification
    is written on its own short-lived session rather than the caller's
    ``AsyncSession``; a failure here never breaks the committed row. Imported
    lazily to keep the notification module out of the import path.
    """
    try:
        from database.hub import hub
        from services.notification.db_service import NotificationDbService

        with hub.get_session() as session:
            NotificationDbService(session).notify(user_id, title, body=body, ntype=ntype)
    except Exception as exc:  # noqa: BLE001 - notification failure must not propagate
        logger.warning("notification to %s not delivered: %s", user_id, exc)


class PermissionDenied(ValueError):
    """Raised when a user lacks the role required to mutate village data."""


# نقش‌های قابل قبول برای مدیریت محتوای روستا
_GOVERNANCE_WRITE_ROLES = {
    "council_member",
    "landscape_manager",
    "marketplace_rep",
    "tourism_rep",
    "agriculture_rep",
}


class _WriteActor:
    """Adapter connecting an actor id to the ``User``-shaped permission helper.

    مسیرهای نوشتاری فقط شناسهٔ کاربر را دارند (``user_id: str``) نه شیء
    ``User`` را؛ ``_check_governance_permission`` صرفاً به ``user.id`` نیاز
    دارد، پس این آداپتور آن را بدون تغییر در آن ارائه می‌کند.
    """

    __slots__ = ("id", "role")

    def __init__(self, user_id: str | None) -> None:
        self.id = "" if user_id is None else str(user_id)
        self.role = ""


class VillageDevelopmentHubService:
    """سرویس مدیریت جامع مرکز توسعه روستا.

    این سرویس یک لایهٔ انتزاعی بین API Router و لایهٔ داده فراهم می‌کند.
    تمام منطق تجاری، اعتبارسنجی، و بررسی دسترسی در این لایه قرار می‌گیرد.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # Helper: Governance Permission Check
    # ========================================================================

    async def _check_governance_permission(
        self, village_id: str, user: User, write_access: bool = True
    ) -> bool:
        """بررسی دسترسی کاربر به روستا بر اساس نقش حکمرانی.

        اگر write_access True باشد، فقط نقش‌های نوشتاری پذیرفته می‌شوند.
        """
        result = await self.db.execute(
            select(LandscapeGovernanceMember).where(
                LandscapeGovernanceMember.village_id == village_id,
                LandscapeGovernanceMember.user_id == str(user.id),
                LandscapeGovernanceMember.is_active,
            )
        )
        member = result.scalar_one_or_none()

        if member is None:
            return False

        return not (write_access and member.role not in _GOVERNANCE_WRITE_ROLES)

    async def _is_platform_admin(self, user_id: str | None) -> bool:
        """بررسی ادمین بودن کاربر پلتفرم روی مسیرهای نوشتاری بدون شیء User."""
        if user_id is None:
            return False
        result = await self.db.execute(select(User).where(User.id == str(user_id)))
        user = result.scalar_one_or_none()
        return user is not None and user.role == "admin"

    async def _ensure_village_write(
        self, village_ids: list[str], user_id: str | None, is_admin: bool = False
    ) -> None:
        """اجازهٔ نوشتن در روستاها: ادمین پلتفرم یا عضو حکمرانی فعال با نقش نوشتاری.

        مجوز از همان مکانیزم ``_check_governance_permission`` گرفته می‌شود تا
        ``_GOVERNANCE_WRITE_ROLES`` تنها نقطهٔ تعریف نقش‌های نوشتاری بماند.
        """
        if is_admin or await self._is_platform_admin(user_id):
            return
        actor = _WriteActor(user_id)
        for village_id in village_ids:
            if await self._check_governance_permission(village_id, actor, write_access=True):
                return
        raise PermissionDenied("شما دسترسی ندارید")

    async def _ensure_landscape_write(
        self, user_id: str | None, is_admin: bool = False
    ) -> None:
        """اجازهٔ نوشتن موجودیت بدون دامنهٔ روستا: ادمین پلتفرم یا عضو حکمرانی فعال.

        وقتی موجودیت به روستای مشخصی وابسته نیست (مثلاً جوامع عشایری یا جشنوارهٔ
        بدون روستای شرکت‌کننده)، عضویت فعال با نقش نوشتاری در هر روستایی کافی است.
        """
        if is_admin or await self._is_platform_admin(user_id):
            return
        result = await self.db.execute(
            select(LandscapeGovernanceMember).where(
                LandscapeGovernanceMember.user_id == str(user_id),
                LandscapeGovernanceMember.is_active,
            )
        )
        for member in result.scalars().all():
            if member.role in _GOVERNANCE_WRITE_ROLES:
                return
        raise PermissionDenied("شما دسترسی ندارید")

    async def _verify_village_exists(self, village_id: str) -> LandscapeVillage:
        result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        village = result.scalar_one_or_none()
        if not village:
            raise ValueError(f"روستا یافت نشد: {village_id}")
        return village

    # ========================================================================
    # KYC / Marketplace Gate (P7.1: Governance <-> Marketplace)
    # ========================================================================

    async def is_marketplace_eligible(self, village_id: str) -> bool:
        """بررسی مجوزی بودن روستا برایMarkeetplace.

        قرية فقط وقتی قابل ثبت فروشنده/محصول است وقتی:
          * فضای حکمرانی ACTIVE باشد، و
          * LandscapeVillage.verification_status == "approved" (KYC تایید شده)، و
          * representative_identity_verified == True.
        """
        from services.village.models import CommunitySpace, SpaceStatus

        # Check governance space is ACTIVE.
        space_result = await self.db.execute(
            select(CommunitySpace).where(CommunitySpace.village_id == village_id)
        )
        space = space_result.scalar_one_or_none()
        if space is None or space.status != SpaceStatus.ACTIVE.value:
            return False

        # Check landscape village is KYC-approved.
        lv_result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        lv = lv_result.scalar_one_or_none()
        if lv is None:
            return False
        if lv.verification_status != "approved":
            return False
        if not lv.representative_identity_verified:
            return False

        return True

    async def require_marketplace_eligible(self, village_id: str) -> LandscapeVillage:
        """بررسی مجوزی بودن روستا و بازگشت رکورد منظر؛ در غیر این صورت ValueError."""
        from services.village.models import CommunitySpace, SpaceStatus

        space_result = await self.db.execute(
            select(CommunitySpace).where(CommunitySpace.village_id == village_id)
        )
        space = space_result.scalar_one_or_none()
        if space is None or space.status != SpaceStatus.ACTIVE.value:
            raise ValueError(
                f"روستا {village_id} در فضای حکمرانی فعال نیست (市场برای فروشندگی مجاز نیست)"
            )

        lv_result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        lv = lv_result.scalar_one_or_none()
        if lv is None:
            raise ValueError(f"رکورد منظر برای روستا {village_id} یافت نشد")
        if lv.verification_status != "approved":
            raise ValueError(
                f"KYC روستا {village_id} تایید نشده است (وضعیت: {lv.kyc_status})"
            )
        if not lv.representative_identity_verified:
            raise ValueError(
                f"شناسه드جیتال edustنده روستا {village_id} تایید نشده است"
            )

        return lv

    # ========================================================================
    # 1. Village Profile & Dashboard
    # ========================================================================

    async def get_village_profile(self, village_id: str) -> dict:
        """دریافت پروفایل کامل روستا با تمام ماژول‌ها."""
        await self._verify_village_exists(village_id)

        capabilities = await self.get_village_capabilities(village_id)
        opps_result = await self.db.execute(
            select(VillageOpportunity).where(VillageOpportunity.village_id == village_id)
        )
        opportunities = opps_result.scalars().all()
        projects_result = await self.db.execute(
            select(VillageProject).where(VillageProject.village_id == village_id)
        )
        projects = projects_result.scalars().all()

        total_investment = Decimal("0.00")
        for proj in projects:
            total_investment += proj.investment_secured

        entrepreneur_count = await self.db.scalar(
            select(func.count(EntrepreneurProfile.id)).where(
                EntrepreneurProfile.village_id == village_id
            )
        )

        return {
            "village_id": village_id,
            "name": None,
            "region": None,
            "brand_name": None,
            "active_modules": [],
            "total_members": 0,
            "monthly_gmv": 0.0,
            "capabilities": [
                {
                    "id": cap.id,
                    "name": cap.name,
                    "name_en": cap.name_en,
                    "category": cap.category,
                    "capacity_value": float(cap.capacity_value) if cap.capacity_value else None,
                    "unit": cap.unit,
                    "description": cap.description,
                    "is_active": cap.is_active,
                    "confidence": cap.confidence,
                }
                for cap in capabilities
            ],
            "opportunities_count": len(opportunities),
            "projects_count": len(projects),
            "active_projects_count": sum(
                1 for p in projects if p.status in ("in_progress", "planned")
            ),
            "total_investment_secured": float(total_investment),
            "total_entrepreneurs": int(entrepreneur_count or 0),
        }

    async def get_village_dashboard(self, village_id: str) -> dict:
        """دریافت داشبورد توسعه روستا — متریک‌های ترکیبی."""
        await self._verify_village_exists(village_id)

        total_caps = await self.db.scalar(
            select(func.count(VillageCapability.id)).where(
                VillageCapability.village_id == village_id,
                VillageCapability.is_active,
            )
        )
        total_opps = await self.db.scalar(
            select(func.count(VillageOpportunity.id)).where(
                VillageOpportunity.village_id == village_id
            )
        )
        active_projects = await self.db.scalar(
            select(func.count(VillageProject.id)).where(
                VillageProject.village_id == village_id,
                VillageProject.status.in_(["planned", "in_progress"]),
            )
        )
        completed_projects = await self.db.scalar(
            select(func.count(VillageProject.id)).where(
                VillageProject.village_id == village_id,
                VillageProject.status == "completed",
            )
        )

        investment_result = await self.db.execute(
            select(
                func.sum(VillageProject.investment_secured).label("total"),
            ).where(VillageProject.village_id == village_id)
        )
        investment_row = investment_result.scalar_one_or_none()
        total_investment_secured = float(investment_row or Decimal("0.00"))

        total_entrepreneurs = await self.db.scalar(
            select(func.count(EntrepreneurProfile.id)).where(
                EntrepreneurProfile.village_id == village_id
            )
        )

        registered_events = await self.db.scalar(
            select(func.count(VillageEvent.id)).where(VillageEvent.village_id == village_id)
        )
        tourism_services = await self.db.scalar(
            select(func.count(VillageTourismService.id)).where(
                VillageTourismService.village_id == village_id,
                VillageTourismService.is_verified,
            )
        )
        needs_count = await self.db.scalar(
            select(func.count(VillageNeed.id)).where(
                VillageNeed.village_id == village_id,
                not VillageNeed.is_resolved,
            )
        )

        recent_opps_result = await self.db.execute(
            select(VillageOpportunity)
            .where(VillageOpportunity.village_id == village_id)
            .order_by(desc(VillageOpportunity.created_at))
            .limit(5)
        )
        recent_opps = recent_opps_result.scalars().all()

        recent_projects_result = await self.db.execute(
            select(VillageProject)
            .where(VillageProject.village_id == village_id)
            .order_by(desc(VillageProject.created_at))
            .limit(5)
        )
        recent_projects = recent_projects_result.scalars().all()

        return {
            "village_id": village_id,
            "total_capabilities": int(total_caps or 0),
            "total_opportunities": int(total_opps or 0),
            "active_projects": int(active_projects or 0),
            "completed_projects": int(completed_projects or 0),
            "total_investment": total_investment_secured,
            "investment_secured": total_investment_secured,
            "total_entrepreneurs": int(total_entrepreneurs or 0),
            "registered_events": int(registered_events or 0),
            "tourism_services_count": int(tourism_services or 0),
            "needs_count": int(needs_count or 0),
            "recent_opportunities": [self._serialize_opportunity(o) for o in recent_opps],
            "recent_projects": [self._serialize_project(p) for p in recent_projects],
        }

    # ========================================================================
    # 2. Capabilities
    # ========================================================================

    async def get_village_capabilities(
        self,
        village_id: str,
        category: str | None = None,
    ) -> list[VillageCapability]:
        """دریافت ظرفیت‌های اقتصادی/گردشگيری یک روستا."""
        await self._verify_village_exists(village_id)

        query = select(VillageCapability).where(VillageCapability.village_id == village_id)
        if category:
            query = query.where(VillageCapability.category == category)
        query = query.order_by(asc(VillageCapability.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_capability(
        self, village_id: str, data: dict, user_id: str, is_admin: bool = False
    ) -> VillageCapability:
        """ایجاد یا بروزرسانی یک ظرفیت روستا."""
        await self._verify_village_exists(village_id)
        await self._ensure_village_write([village_id], user_id, is_admin)

        capability = VillageCapability(
            village_id=village_id,
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            name=data.get("name"),
            name_en=data.get("name_en"),
            capacity_value=data.get("capacity_value"),
            unit=data.get("unit"),
            description=data.get("description"),
            confidence=data.get("confidence", "medium"),
            source=data.get("source"),
        )

        self.db.add(capability)
        await self.db.commit()
        await self.db.refresh(capability)
        return capability

    async def update_capability(
        self, capability_id: str, data: dict, user: User
    ) -> VillageCapability:
        """بروزرسانی ظرفیت — نیاز به دسترسی حکمرانی روستا."""
        result = await self.db.execute(
            select(VillageCapability).where(VillageCapability.id == capability_id)
        )
        capability = result.scalar_one_or_none()
        if not capability:
            raise ValueError(f"ظرفیت یافت نشد: {capability_id}")

        has_access = await self._check_governance_permission(capability.village_id, user)
        if not has_access and not (user.role == "admin"):
            raise PermissionDenied("شما دسترسی ندارید")

        for key, value in data.items():
            if value is not None:
                setattr(capability, key, value)

        capability.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(capability)
        return capability

    async def delete_capability(self, capability_id: str, user: User) -> None:
        result = await self.db.execute(
            select(VillageCapability).where(VillageCapability.id == capability_id)
        )
        capability = result.scalar_one_or_none()
        if not capability:
            raise ValueError(f"ظرفیت یافت نشد: {capability_id}")

        has_access = await self._check_governance_permission(capability.village_id, user)
        if not has_access and user.role != "admin":
            raise PermissionDenied("شما دسترسی ندارید")

        await self.db.delete(capability)
        await self.db.commit()

    # ========================================================================
    # 3. Opportunities
    # ========================================================================

    async def get_village_opportunities(
        self,
        village_id: str,
        maturity: str | None = None,
        status: str | None = None,
    ) -> list[VillageOpportunity]:
        """دریافت فرصت‌های توسعهٔ روستا."""
        await self._verify_village_exists(village_id)

        query = select(VillageOpportunity).where(VillageOpportunity.village_id == village_id)
        if maturity:
            query = query.where(VillageOpportunity.maturity == maturity)
        if status:
            query = query.where(VillageOpportunity.status == status)
        query = query.order_by(desc(VillageOpportunity.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_opportunities(
        self,
        q: str | None = None,
        category: str | None = None,
        village_id: str | None = None,
        limit: int = 50,
    ) -> list[VillageOpportunity]:
        """جستجوی فرصت‌ها در تمام روستاها."""
        query = select(VillageOpportunity)
        if q:
            query = query.where(
                or_(
                    VillageOpportunity.name.ilike(f"%{q}%"),
                    VillageOpportunity.description.ilike(f"%{q}%"),
                )
            )
        if category:
            query = query.where(VillageOpportunity.category == category)
        if village_id:
            query = query.where(VillageOpportunity.village_id == village_id)
        query = query.order_by(desc(VillageOpportunity.created_at)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_opportunity(
        self, village_id: str, data: dict, user_id: str, is_admin: bool = False
    ) -> VillageOpportunity:
        """ایجاد فرصت توسعه جدید."""
        await self._verify_village_exists(village_id)
        await self._ensure_village_write([village_id], user_id, is_admin)

        opportunity = VillageOpportunity(
            village_id=village_id,
            capability_id=data.get("capability_id"),
            name=data.get("name"),
            name_en=data.get("name_en"),
            category=data.get("category"),
            description=data.get("description"),
            business_model=data.get("business_model"),
            required_investment=data.get("required_investment"),
            required_skills=data.get("required_skills", []),
            target_markets=data.get("target_markets", []),
            expected_revenue=data.get("expected_revenue"),
            maturity=data.get("maturity", "idea"),
            status=data.get("status", "draft"),
            created_by=user_id,
        )

        self.db.add(opportunity)
        await self.db.commit()
        await self.db.refresh(opportunity)
        return opportunity

    async def update_opportunity(
        self, opportunity_id: str, data: dict, user: User
    ) -> VillageOpportunity:
        """بروزرسانی فرصت توسعه — نیاز به دسترسی حکمرانی."""
        result = await self.db.execute(
            select(VillageOpportunity).where(VillageOpportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        if not opportunity:
            raise ValueError(f"فرصت یافت نشد: {opportunity_id}")

        has_access = await self._check_governance_permission(opportunity.village_id, user)
        if not has_access and user.role != "admin":
            raise PermissionDenied("شما دسترسی ندارید")

        for key, value in data.items():
            if value is not None:
                setattr(opportunity, key, value)

        opportunity.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(opportunity)
        return opportunity

    async def express_interest(
        self, opportunity_id: str, user_id: str, note: str | None = None
    ) -> VillageOpportunityInterest:
        """یک کارآفرین علاقه خود را به یک فرصت اعلام می‌کند."""
        result = await self.db.execute(
            select(VillageOpportunity).where(VillageOpportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        if not opportunity:
            raise ValueError(f"فرصت یافت نشد: {opportunity_id}")

        entrepreneur_result = await self.db.execute(
            select(EntrepreneurProfile).where(EntrepreneurProfile.user_id == user_id)
        )
        entrepreneur = entrepreneur_result.scalar_one_or_none()
        if not entrepreneur:
            entrepreneur = EntrepreneurProfile(user_id=user_id)
            self.db.add(entrepreneur)
            await self.db.commit()
            await self.db.refresh(entrepreneur)

        existing_result = await self.db.execute(
            select(VillageOpportunityInterest).where(
                VillageOpportunityInterest.opportunity_id == opportunity_id,
                VillageOpportunityInterest.entrepreneur_id == entrepreneur.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.status = "interested"
            existing.note = note
            existing.expressed_at = datetime.now(UTC)
        else:
            interest = VillageOpportunityInterest(
                opportunity_id=opportunity_id,
                entrepreneur_id=entrepreneur.id,
                note=note,
            )
            self.db.add(interest)

        await self.db.commit()
        await self.db.refresh(entrepreneur)

        interest_result = await self.db.execute(
            select(VillageOpportunityInterest).where(
                VillageOpportunityInterest.opportunity_id == opportunity_id,
                VillageOpportunityInterest.entrepreneur_id == entrepreneur.id,
            )
        )
        return interest_result.scalar_one()

    async def search_entrepreneurs(
        self,
        skills: list[str] | None = None,
        village_id: str | None = None,
    ) -> list[EntrepreneurProfile]:
        """جستجوی کارآفرینان بر اساس مهارت یا روستا."""
        query = select(EntrepreneurProfile).where(EntrepreneurProfile.is_available)
        if village_id:
            query = query.where(EntrepreneurProfile.village_id == village_id)
        if skills:
            skill_matches = []
            for skill in skills:
                skill_matches.append(EntrepreneurProfile.skills.contains([skill]))
            if skill_matches:
                query = query.where(or_(*skill_matches))

        result = await self.db.execute(query)
        return result.scalars().all()

    # ========================================================================
    # 4. Projects
    # ========================================================================

    async def create_project(self, village_id: str, data: dict, user_id: str) -> VillageProject:
        """ایجاد یا بروزرسانی یک پروژه توسعه."""
        await self._verify_village_exists(village_id)
        await self._ensure_village_write([village_id], user_id)

        project = VillageProject(
            village_id=village_id,
            opportunity_id=data.get("opportunity_id"),
            name=data.get("name"),
            name_en=data.get("name_en"),
            description=data.get("description"),
            category=data.get("category"),
            status=data.get("status", "planned"),
            progress_pct=data.get("progress_pct", 0),
            investment_needed=data.get("investment_needed"),
            team_size=data.get("team_size", 0),
            start_date=data.get("start_date"),
            expected_completion=data.get("expected_completion"),
            created_by=user_id,
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_village_projects(
        self,
        village_id: str,
        status: str | None = None,
    ) -> list[VillageProject]:
        """لیست پروژه‌های یک روستا."""
        await self._verify_village_exists(village_id)

        query = select(VillageProject).where(VillageProject.village_id == village_id)
        if status:
            query = query.where(VillageProject.status == status)
        query = query.order_by(desc(VillageProject.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_project_progress(
        self, project_id: str, progress_pct: int, user: User
    ) -> VillageProject:
        """بروزرسانی درصد پیشرفت یک پروژه."""
        result = await self.db.execute(
            select(VillageProject).where(VillageProject.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"پروژه یافت نشد: {project_id}")

        has_access = await self._check_governance_permission(project.village_id, user)
        if not has_access and user.role != "admin":
            raise PermissionDenied("شما دسترسی ندارید")

        if progress_pct < 0 or progress_pct > 100:
            raise ValueError("پیشرفت باید بین 0 و 100 باشد")

        project.progress_pct = progress_pct
        if progress_pct >= 100:
            project.status = "completed"
            project.actual_completion = datetime.now(UTC).date()

        project.updated_at = datetime.now(UTC)

        # Cascade progress to parent project: recompute as average of direct
        # sub-projects' progress (weighted equally). Skipped for root projects.
        if project.parent_project_id is not None:
            await self._recompute_parent_progress(project.parent_project_id)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def _recompute_parent_progress(self, parent_id: str):
        """Recompute a parent project's progress as the mean of its children."""
        parent = (
            await self.db.execute(
                select(VillageProject).where(VillageProject.id == parent_id)
            )
        ).scalar_one_or_none()
        if parent is None:
            return
        children = (
            await self.db.execute(
                select(VillageProject).where(
                    VillageProject.parent_project_id == parent_id
                )
            )
        ).scalars().all()
        if not children:
            return
        avg = sum(c.progress_pct or 0 for c in children) / len(children)
        parent.progress_pct = int(round(avg))
        if parent.progress_pct >= 100:
            parent.status = "completed"
            parent.actual_completion = datetime.now(UTC).date()
        parent.updated_at = datetime.now(UTC)
        # Recurse up the chain.
        if parent.parent_project_id is not None:
            await self._recompute_parent_progress(parent.parent_project_id)

    async def create_sub_project(
        self,
        parent_project_id: str,
        data: dict,
        user_id: str,
    ) -> VillageProject:
        """Create a sub-project nested under a parent project."""
        parent = (
            await self.db.execute(
                select(VillageProject).where(VillageProject.id == parent_project_id)
            )
        ).scalar_one_or_none()
        if parent is None:
            raise ValueError(f"parent project not found: {parent_project_id}")
        project = VillageProject(
            village_id=parent.village_id,
            parent_project_id=parent_project_id,
            opportunity_id=data.get("opportunity_id"),
            name=data.get("name"),
            name_en=data.get("name_en"),
            description=data.get("description"),
            category=data.get("category"),
            status=data.get("status", "planned"),
            progress_pct=data.get("progress_pct", 0),
            investment_needed=data.get("investment_needed"),
            investment_secured=data.get("investment_secured", Decimal("0.00")),
            investors_count=data.get("investors_count", 0),
            start_date=data.get("start_date"),
            expected_completion=data.get("expected_completion"),
            team_size=data.get("team_size", 0),
            created_by=user_id,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_sub_projects(self, parent_project_id: str) -> list[VillageProject]:
        """List direct sub-projects of a parent project."""
        result = await self.db.execute(
            select(VillageProject).where(
                VillageProject.parent_project_id == parent_project_id
            )
        )
        return result.scalars().all()


    async def get_project_investors(self, project_id: str) -> list[dict]:
        """دریافت لیست سرمایه‌گذاران یک پروژه."""
        result = await self.db.execute(
            select(VillageInvestment).where(VillageInvestment.project_id == project_id)
        )
        investments = result.scalars().all()
        return [
            {
                "user_id": inv.investor_user_id,
                "amount": float(inv.amount),
                "currency": inv.currency,
                "status": inv.status,
                "invested_at": inv.created_at.isoformat() if inv.created_at else None,
            }
            for inv in investments
        ]

    # ========================================================================
    # 5. Entrepreneurs
    # ========================================================================

    async def get_entrepreneur_profile(self, user_id: str) -> EntrepreneurProfile | None:
        """دریافت پروفایل کارآفرین."""
        result = await self.db.execute(
            select(EntrepreneurProfile).where(EntrepreneurProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_entrepreneur_profile(
        self,
        user_id: str,
        data: dict,
        village_id: str | None = None,
    ) -> EntrepreneurProfile:
        """ایجاد یا بروزرسانی پروفایل کارآفرین."""
        result = await self.db.execute(
            select(EntrepreneurProfile).where(EntrepreneurProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if profile:
            for key, value in data.items():
                if value is not None:
                    setattr(profile, key, value)
            if village_id:
                profile.village_id = village_id
        else:
            profile = EntrepreneurProfile(
                user_id=user_id,
                village_id=village_id,
                skills=data.get("skills", []),
                interests=data.get("interests", []),
                capacity_description=data.get("capacity_description"),
                experience_years=data.get("experience_years"),
                is_available=data.get("is_available", True),
            )
            self.db.add(profile)

        profile.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    # ========================================================================
    # 6. Investments
    # ========================================================================

    async def create_investment(
        self, project_id: str, amount: Decimal, investor_id: str, notes: str | None = None
    ) -> VillageInvestment:
        """ثبت سرمایه‌گذاری در یک پروژه."""
        result = await self.db.execute(
            select(VillageProject).where(VillageProject.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"پروژه یافت نشد: {project_id}")

        if amount <= 0:
            raise ValueError("مبلغ سرمایه‌گذاری باید مثبت باشد")

        investment = VillageInvestment(
            project_id=project_id,
            investor_user_id=investor_id,
            amount=amount,
            notes=notes,
        )
        self.db.add(investment)

        project.investment_secured += amount
        project.investors_count += 1
        project.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(investment)
        return investment

    async def confirm_investment(
        self, investment_id: str, confirmed_by: str, status: str = "confirmed"
    ) -> VillageInvestment:
        """تأیید یا رد درخواست سرمایه‌گذاری."""
        result = await self.db.execute(
            select(VillageInvestment).where(VillageInvestment.id == investment_id)
        )
        investment = result.scalar_one_or_none()
        if not investment:
            raise ValueError(f"سرمایه‌گذاری یافت نشد: {investment_id}")

        investment.status = status
        if status == "confirmed":
            investment.confirmed_by = confirmed_by
            investment.confirmed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(investment)
        return investment

    async def invest_from_territory_fund(
        self,
        *,
        territory_id: str,
        territory_fund_id: str,
        project_id: str,
        amount: Decimal,
        notes: str | None = None,
    ) -> VillageInvestment:
        """ تخصیص از صندوق قلمرو به یک پروژه روستا.

        Checks that the territory fund exists and is active, that the project
        exists, and that the fund has sufficient pending balance. Creates a
        VillageInvestment record flagged with territory_id/territory_fund_id,
        deducts from the fund balance, and updates the project's secured
        investment.
        """
        # Verify territory fund exists and is active.
        fund = await self.db.execute(
            select(TerritoryFund).where(TerritoryFund.id == territory_fund_id)
        )
        fund = fund.scalar_one_or_none()
        if fund is None:
            raise ValueError(f"صندوق قلمرو یافت نشد: {territory_fund_id}")
        if str(fund.territory_id) != str(territory_id):
            raise ValueError("صندوق قلمرو متعلق به قلمرو دیگر است")
        if not fund.is_active:
            raise ValueError("صندوق قلمرو غیرفعال است")
        if (fund.pending_balance or Decimal("0")) < amount:
            raise ValueError("موجودی صندوق کافی نیست")

        # Verify project exists.
        project = await self.db.execute(
            select(VillageProject).where(VillageProject.id == project_id)
        )
        project = project.scalar_one_or_none()
        if project is None:
            raise ValueError(f"پروژه یافت نشد: {project_id}")

        if amount <= 0:
            raise ValueError("مبلغ سرمایه‌گذاری باید مثبت باشد")

        # Deduct from territory fund.
        fund.pending_balance = (fund.pending_balance or Decimal("0")) - amount
        fund.total_distributed = (fund.total_distributed or Decimal("0")) + amount

        # Create investment record.
        investment = VillageInvestment(
            project_id=project_id,
            investor_user_id=str(territory_id),
            amount=amount,
            currency=fund.currency,
            status="confirmed",
            confirmed_by=str(territory_id),
            confirmed_at=datetime.now(UTC),
            notes=notes,
            territory_id=territory_id,
            territory_fund_id=territory_fund_id,
        )
        self.db.add(investment)

        # Update project.
        project.investment_secured = (project.investment_secured or Decimal("0")) + amount
        project.investors_count += 1
        project.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(investment)
        return investment

    async def get_my_investments(self, user_id: str) -> list[VillageInvestment]:
        """دریافت سرمایه‌گذاری‌های یک کاربر."""
        result = await self.db.execute(
            select(VillageInvestment).where(VillageInvestment.investor_user_id == user_id)
        )
        return result.scalars().all()

    # ========================================================================
    # 7. Tourism Services
    # ========================================================================

    async def get_village_tourism_services(self, village_id: str) -> list[VillageTourismService]:
        """دریافت سرویس‌های گردشگيری روستا."""
        await self._verify_village_exists(village_id)

        result = await self.db.execute(
            select(VillageTourismService)
            .where(VillageTourismService.village_id == village_id)
            .order_by(desc(VillageTourismService.created_at))
        )
        return result.scalars().all()

    async def create_tourism_service(
        self,
        village_id: str,
        data: dict,
        user_id: str,
        nomadic_community_id: str | None = None,
    ) -> VillageTourismService:
        """ثبت سرویس گردشگيری جدید.

        اگر ``nomadic_community_id`` داده شود، سرویس توسط جامعه عشایری ارائه می‌شود
        و به آن پیوند می‌شود.
        """
        await self._verify_village_exists(village_id)
        await self._ensure_village_write([village_id], user_id)

        service = VillageTourismService(
            village_id=village_id,
            nomadic_community_id=nomadic_community_id,
            owner_user_id=user_id,
            service_type=data.get("service_type"),
            name=data.get("name"),
            name_en=data.get("name_en"),
            description=data.get("description"),
            location=data.get("location"),
            coordinates=data.get("coordinates"),
            price_per_unit=data.get("price_per_unit"),
            capacity=data.get("capacity"),
            is_organic=data.get("is_organic", True),
            is_regenerative=data.get("is_regenerative", True),
            images=data.get("images", []),
            contact_phone=data.get("contact_phone"),
            contact_email=data.get("contact_email"),
        )

        self.db.add(service)
        await self.db.commit()
        await self.db.refresh(service)
        return service

    # ========================================================================
    # 8. Events
    # ========================================================================

    async def get_village_events(self, village_id: str) -> list[VillageEvent]:
        """دریافت رویدادهای فرهنگی و گردشگيری روستا."""
        await self._verify_village_exists(village_id)

        result = await self.db.execute(
            select(VillageEvent)
            .where(VillageEvent.village_id == village_id)
            .order_by(VillageEvent.start_date)
        )
        return result.scalars().all()

    async def create_event(self, village_id: str, data: dict, user_id: str) -> VillageEvent:
        """ایجاد رویداد جدید برای روستا."""
        await self._verify_village_exists(village_id)
        await self._ensure_village_write([village_id], user_id)

        event = VillageEvent(
            village_id=village_id,
            title=data.get("title"),
            title_en=data.get("title_en"),
            description=data.get("description"),
            event_type=data.get("event_type"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            location=data.get("location"),
            coordinates=data.get("coordinates"),
            max_participants=data.get("max_participants"),
            registration_fee=data.get("registration_fee", Decimal("0.00")),
            created_by=user_id,
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def register_event(
        self, event_id: str, user_id: str, fee_paid: bool = False
    ) -> VillageEventRegistration:
        """ثبت‌نام کاربر در یک رویداد."""
        result = await self.db.execute(select(VillageEvent).where(VillageEvent.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise ValueError(f"رویداد یافت نشد: {event_id}")

        if event.status in ("cancelled", "completed"):
            raise ValueError("رویداد در وضعیت ثبت‌نام فعال نیست")

        existing_result = await self.db.execute(
            select(VillageEventRegistration).where(
                VillageEventRegistration.event_id == event_id,
                VillageEventRegistration.user_id == user_id,
            )
        )
        if existing_result.scalar_one_or_none():
            raise ValueError("قبلاً در این رویداد ثبت‌نام کرده‌اید")

        registration = VillageEventRegistration(
            event_id=event_id,
            user_id=user_id,
            status="registered",
        )
        self.db.add(registration)
        await self.db.commit()
        await self.db.refresh(registration)

        await _emit_hub_event(
            "event_registration_created",
            "village_event",
            str(registration.id),
            {
                "event_id": str(registration.event_id),
                "village_id": str(event.village_id),
                "user_id": str(registration.user_id),
            },
        )
        _notify(str(registration.user_id), "Your event registration is confirmed.", ntype="system")
        return registration

    # ========================================================================
    # 9. Needs
    # ========================================================================

    async def get_village_needs(
        self, village_id: str, priority: str | None = None
    ) -> list[VillageNeed]:
        """دریافت نیازهای شناسایی شدهٔ روستا."""
        await self._verify_village_exists(village_id)

        query = select(VillageNeed).where(VillageNeed.village_id == village_id)
        if priority:
            query = query.where(VillageNeed.priority == priority)
        query = query.order_by(
            desc(VillageNeed.priority).nullslast(),
            desc(VillageNeed.created_at),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_need(
        self, village_id: str, data: dict, user_id: str | None = None, is_admin: bool = False
    ) -> VillageNeed:
        """ثبت نیاز جدید برای روستا."""
        await self._verify_village_exists(village_id)
        await self._ensure_village_write([village_id], user_id, is_admin)

        need = VillageNeed(
            village_id=village_id,
            category=data.get("category"),
            title=data.get("title"),
            description=data.get("description"),
            priority=data.get("priority", "medium"),
            estimated_investment=data.get("estimated_investment"),
        )

        self.db.add(need)
        await self.db.commit()
        await self.db.refresh(need)
        return need

    async def resolve_need(self, need_id: str, user_id: str) -> VillageNeed:
        """علامت‌گذاری یک نیاز به عنوان حل شده."""
        result = await self.db.execute(select(VillageNeed).where(VillageNeed.id == need_id))
        need = result.scalar_one_or_none()
        if not need:
            raise ValueError(f"نیاز یافت نشد: {need_id}")

        need.is_resolved = True
        need.resolved_by = user_id
        need.resolved_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(need)
        return need

    # ========================================================================
    # 10. Brand
    # ========================================================================

    async def get_or_create_brand(
        self,
        village_id: str,
        data: dict | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> VillageBrand:
        """دریافت یا ایجاد برند روستا."""
        await self._verify_village_exists(village_id)

        if data:
            await self._ensure_village_write([village_id], user_id, is_admin)

        result = await self.db.execute(
            select(VillageBrand).where(VillageBrand.village_id == village_id)
        )
        brand = result.scalar_one_or_none()

        if brand:
            if data:
                for key, value in data.items():
                    if value is not None:
                        setattr(brand, key, value)
                brand.updated_at = datetime.now(UTC)
                await self.db.commit()
                await self.db.refresh(brand)
        else:
            brand = VillageBrand(
                village_id=village_id,
                story=data.get("story") if data else None,
                vision=data.get("vision") if data else None,
                values=data.get("values", []) if data else [],
                heritage=data.get("heritage") if data else None,
                certifications=data.get("certifications", []) if data else [],
            )
            self.db.add(brand)
            await self.db.commit()
            await self.db.refresh(brand)

        return brand

    # ========================================================================
    # AI Recommendations
    # ========================================================================

    async def ai_recommendations(self, village_id: str) -> dict:
        """تحلیل هوشمند ظرفیت روستا و پیشنهاد فرصت.

        این یک stub اولیه است — بعداً با موتور AI موجود در `services/ai/`
        یاپانه شود. فعلاً تحلیل ساده بر اساس داده‌های موجود.
        """
        await self._verify_village_exists(village_id)

        capabilities = await self.get_village_capabilities(village_id)
        await self.get_village_opportunities(village_id)
        projects = await self.db.execute(
            select(VillageProject).where(VillageProject.village_id == village_id)
        )
        projects_list = projects.scalars().all()

        categories = {}
        for cap in capabilities:
            cat = cap.category
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        top_capabilities = sorted(categories.keys(), key=lambda x: categories[x], reverse=True)[:3]

        needs_result = await self.db.execute(
            select(VillageNeed).where(
                VillageNeed.village_id == village_id,
                not VillageNeed.is_resolved,
            )
        )
        unresolved_needs = needs_result.scalars().all()

        needs_titles = [n.title for n in unresolved_needs]

        investment_need = Decimal("0.00")
        for proj in projects_list:
            if (
                proj.status in ("planned", "in_progress")
                and proj.investment_needed
                and proj.investment_secured
            ):
                remaining = proj.investment_needed - proj.investment_secured
                if remaining > 0:
                    investment_need += remaining

        return {
            "village_id": village_id,
            "top_capabilities": top_capabilities,
            "recommended_opportunities": [
                {
                    "category": "processing",
                    "title": f"Processing opportunity from {cat}",
                    "confidence": "medium",
                    "estimated_revenue": 5000000,
                }
                for cat in top_capabilities
            ],
            "missing_needs": needs_titles,
            "recommended_investment": float(investment_need),
            "confidence_score": 0.75 if len(capabilities) > 0 else 0.0,
        }

    # ========================================================================
    # 11. Experiences (گردشگری تجربه‌ای)
    # ========================================================================

    async def get_village_experiences(
        self, village_id: str, experience_type: str | None = None
    ) -> list[VillageExperience]:
        """دریافت تجربیات گردشگیری یک روستا."""
        await self._verify_village_exists(village_id)
        query = select(VillageExperience).where(VillageExperience.village_id == village_id)
        if experience_type:
            query = query.where(VillageExperience.experience_type == experience_type)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_experience(
        self, village_id: str, data: dict, user_id: str
    ) -> VillageExperience:
        """ثبت یک تجربهٔ گردشگیری جدید."""
        await self._verify_village_exists(village_id)
        await self._ensure_village_write([village_id], user_id)
        experience = VillageExperience(
            village_id=village_id,
            name=data.get("name"),
            name_en=data.get("name_en"),
            description=data.get("description"),
            experience_type=data.get("experience_type"),
            duration_minutes=data.get("duration_minutes"),
            price_range_min=data.get("price_range_min"),
            price_range_max=data.get("price_range_max"),
            guide_required=data.get("guide_required", False),
            max_participants=data.get("max_participants"),
            image_url=data.get("image_url"),
        )
        self.db.add(experience)
        await self.db.commit()
        await self.db.refresh(experience)
        return experience

    # ========================================================================
    # 12. Destination (صفحه مقصد گردشگری)
    # ========================================================================

    async def get_or_create_destination(
        self,
        village_id: str,
        data: dict | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> VillageDestination:
        """دریافت یا ایجاد صفحهٔ مقصد گردشگری روستا."""
        await self._verify_village_exists(village_id)

        if data:
            await self._ensure_village_write([village_id], user_id, is_admin)

        result = await self.db.execute(
            select(VillageDestination).where(VillageDestination.village_id == village_id)
        )
        dest = result.scalar_one_or_none()
        if dest:
            if data:
                for key, value in data.items():
                    if value is not None:
                        setattr(dest, key, value)
                dest.updated_at = datetime.now(UTC)
                await self.db.commit()
                await self.db.refresh(dest)
        else:
            dest = VillageDestination(
                village_id=village_id,
                natural_attractions=data.get("natural_attractions", []) if data else [],
                cultural_attractions=data.get("cultural_attractions", []) if data else [],
                experiences=data.get("experiences", []) if data else [],
                accommodations=data.get("accommodations", []) if data else [],
                tagline=data.get("tagline") if data else None,
                hero_image_url=data.get("hero_image_url") if data else None,
            )
            self.db.add(dest)
            await self.db.commit()
            await self.db.refresh(dest)
        return dest

    # ========================================================================
    # ========================================================================
    # 20. Localized brand / destination (deep dive)
    # ========================================================================

    def localize_brand(
        self,
        brand: VillageBrand,
        language: str = "fa",
    ) -> dict:
        """Return brand fields in the requested language (fallback to primary)."""
        if language == "en":
            story = brand.story_en or brand.story
            vision = brand.vision_en or brand.vision
            heritage = brand.heritage_en or brand.heritage
        else:
            story = brand.story
            vision = brand.vision
            heritage = brand.heritage
        return {
            "village_id": brand.village_id,
            "language": language,
            "story": story,
            "vision": vision,
            "values": brand.values,
            "heritage": heritage,
            "certifications": brand.certifications,
            "media_kit_url": brand.media_kit_url,
            "brand_guidelines_url": brand.brand_guidelines_url,
        }

    def localize_destination(
        self,
        destination: VillageDestination,
        language: str = "fa",
    ) -> dict:
        """Return destination fields in the requested language."""
        tagline = destination.tagline_en if language == "en" else destination.tagline
        return {
            "village_id": destination.village_id,
            "language": language,
            "natural_attractions": destination.natural_attractions,
            "cultural_attractions": destination.cultural_attractions,
            "experiences": destination.experiences,
            "accommodations": destination.accommodations,
            "tagline": tagline,
            "hero_image_url": destination.hero_image_url,
        }


    # 13. B2B Demands
    # ========================================================================

    async def create_b2b_demand(self, data: dict, buyer_id: str) -> B2BDemand:
        """ثبت درخواست خرید B2B از یک شرکت/فروشگاه."""
        demand = B2BDemand(
            buyer_id=buyer_id,
            buyer_name=data.get("buyer_name"),
            commodity=data.get("commodity"),
            category=data.get("category"),
            quantity_required=data.get("quantity_required"),
            unit=data.get("unit"),
            frequency=data.get("frequency", "monthly"),
            target_regions=data.get("target_regions", []),
            min_quality_cert=data.get("min_quality_cert"),
            price_range=data.get("price_range", []),
        )
        self.db.add(demand)
        await self.db.commit()
        await self.db.refresh(demand)

        await _emit_hub_event(
            "b2b_demand_created",
            "b2b_demand",
            str(demand.id),
            {
                "commodity": str(demand.commodity),
                "buyer_id": str(demand.buyer_id),
            },
        )
        _notify(str(demand.buyer_id), "Your B2B demand has been posted.", ntype="system")
        return demand

    async def match_b2b_demands(self, village_id: str) -> list[dict]:
        """یافتن درخواست‌های B2B مناسب یک روستا و تبدیل آن‌ها به فرصت توسعه.

        برای هر درخواست باز (open) که با ظرفیت روستا تطبیق پیدا می‌کند،
        یک ``VillageOpportunity`` ساخته می‌شود و در ``matched_villages``
        درخواست ثبت می‌شود. درخواست در حالت ``matched`` قرار می‌گیرد.
        """
        result = await self.db.execute(select(B2BDemand).where(B2BDemand.status == "open"))
        demands = result.scalars().all()
        matches = []
        for demand in demands:
            cap_result = await self.db.execute(
                select(VillageCapability).where(
                    VillageCapability.village_id == village_id,
                    VillageCapability.category == demand.category
                    or VillageCapability.name.ilike(f"%{demand.commodity}%"),
                )
            )
            caps = cap_result.scalars().all()
            for cap in caps:
                # Create a village opportunity from this demand-capability match.
                opportunity = VillageOpportunity(
                    village_id=village_id,
                    capability_id=cap.id,
                    name=f"تأمین {demand.commodity} برای {demand.buyer_name or 'خریدار'}",
                    category=demand.category or cap.category,
                    description=(
                        f"درخواست B2B برای تأمین {demand.quantity_required} {demand.unit} "
                        f"{demand.commodity} با فرکانس {demand.frequency}"
                    ),
                    business_model="B2B supply",
                    required_investment=None,
                    required_skills=None,
                    target_markets=[demand.buyer_id] if demand.buyer_id else [],
                    expected_revenue=None,
                    maturity=OpportunityMaturity.IDEA,
                    status=OpportunityStatus.PUBLISHED,
                    created_by=str(demand.buyer_id),
                    matched_demand_id=str(demand.id),
                )
                self.db.add(opportunity)
                await self.db.flush()

                # Link demand → opportunity and record village match.
                demand.matched_opportunity_id = str(opportunity.id)
                demand.status = "matched"
                matched = list(demand.matched_villages or [])
                if village_id not in matched:
                    matched.append(village_id)
                demand.matched_villages = matched

                matches.append(
                    {
                        "demand_id": demand.id,
                        "opportunity_id": str(opportunity.id),
                        "buyer_name": demand.buyer_name,
                        "commodity": demand.commodity,
                        "quantity_required": float(demand.quantity_required),
                        "unit": demand.unit,
                        "frequency": demand.frequency,
                        "capability_id": cap.id,
                        "capability_name": cap.name,
                        "capacity_value": float(cap.capacity_value) if cap.capacity_value else None,
                        "unit_cap": cap.unit,
                        "confidence": cap.confidence,
                        "status": "matched",
                    }
                )

        await self.db.commit()
        return matches

    async def confirm_b2b_match(
        self,
        *,
        demand_id: str,
        opportunity_id: str,
        confirmed_by: str,
    ) -> dict:
        """تأیید نهایی تطبیق درخواست B2B با فرصت روستا.

        اطمینان می‌گیرد که درخواست و فرصت واقعاً به هم پیوند یافته‌اند و
        هر دو را در حالت 'matched'/'accepted' قرار می‌دهد.
        """
        demand = await self.db.execute(
            select(B2BDemand).where(B2BDemand.id == demand_id)
        )
        demand = demand.scalar_one_or_none()
        if demand is None:
            raise ValueError(f"درخواست B2B یافت نشد: {demand_id}")

        opportunity = await self.db.execute(
            select(VillageOpportunity).where(VillageOpportunity.id == opportunity_id)
        )
        opportunity = opportunity.scalar_one_or_none()
        if opportunity is None:
            raise ValueError(f"فرصت توسعه یافت نشد: {opportunity_id}")

        if str(demand.matched_opportunity_id) != str(opportunity_id):
            raise ValueError("درخواست با این فرصت تطبیق نیافته است")
        if str(opportunity.matched_demand_id) != str(demand_id):
            raise ValueError("فرصت با این درخواست تطبیق نیافته است")

        demand.status = "matched"
        opportunity.status = OpportunityStatus.ACCEPTED

        await self.db.commit()
        return {
            "demand_id": demand_id,
            "opportunity_id": opportunity_id,
            "status": "confirmed",
        }

    async def get_b2b_demands_for_buyer(self, buyer_id: str) -> list[B2BDemand]:
        """دریافت درخواست‌های B2B یک خریدار."""
        result = await self.db.execute(select(B2BDemand).where(B2BDemand.buyer_id == buyer_id))
        return result.scalars().all()

    # ========================================================================
    # 14. Village Engagement (اتصال توانمندی به کارآفرین)
    # ========================================================================

    async def create_engagement(self, data: dict, user_id: str) -> VillageEngagement:
        """ثبت علاقه یا شرکت یک کاربر در یک فرصت/پروژه."""
        engagement = VillageEngagement(
            user_id=user_id,
            opportunity_id=data.get("opportunity_id"),
            project_id=data.get("project_id"),
            role=data.get("role"),
            note=data.get("note"),
        )
        self.db.add(engagement)
        await self.db.commit()
        await self.db.refresh(engagement)
        return engagement

    async def get_opportunity_team(self, opportunity_id: str) -> list[VillageEngagement]:
        """دریافت لیست تیم یک فرصت (کارآفرینان، سرمایه‌گذاران، مربیان، ...)."""
        result = await self.db.execute(
            select(VillageEngagement).where(
                VillageEngagement.opportunity_id == opportunity_id,
                VillageEngagement.status == "accepted",
            )
        )
        return result.scalars().all()

    async def get_project_engagements(self, project_id: str) -> list[VillageEngagement]:
        """دریافت لیست مشارکت‌کنندگان در یک پروژه."""
        result = await self.db.execute(
            select(VillageEngagement).where(
                VillageEngagement.project_id == project_id,
                VillageEngagement.status == "accepted",
            )
        )
        return result.scalars().all()

    # ========================================================================
    # 15. Development Gaps (AI)
    # ========================================================================

    async def create_development_gap(
        self, village_id: str, data: dict, user_id: str | None = None, is_admin: bool = False
    ) -> VillageDevelopmentGap:
        """ثبت یک شکاف توسعه برای روستا."""
        await self._ensure_village_write([village_id], user_id, is_admin)
        gap = VillageDevelopmentGap(
            village_id=village_id,
            gap_type=data.get("gap_type"),
            severity=data.get("severity", "medium"),
            description=data.get("description"),
            proposed_solution=data.get("proposed_solution"),
            suggested_opportunity_id=data.get("suggested_opportunity_id"),
            ai_generated=data.get("ai_generated", True),
            confidence_score=data.get("confidence_score"),
        )
        self.db.add(gap)
        await self.db.commit()
        await self.db.refresh(gap)
        return gap

    async def get_village_gaps(
        self, village_id: str, gap_type: str | None = None
    ) -> list[VillageDevelopmentGap]:
        """دریافت شکاف‌های توسعهٔ روستا."""
        query = select(VillageDevelopmentGap).where(VillageDevelopmentGap.village_id == village_id)
        if gap_type:
            query = query.where(VillageDevelopmentGap.gap_type == gap_type)
        result = await self.db.execute(query)
        return result.scalars().all()

    # ========================================================================
    # 16. Festivals & Exhibitions
    # ========================================================================

    async def get_village_festivals(self, village_id: str) -> list[VillageFestival]:
        """دریافت جشنواره‌های مرتبط با روستا."""
        result = await self.db.execute(select(VillageFestival))
        festivals = result.scalars().all()
        # Filter in Python for cross-database compatibility (SQLite doesn't support JSON contains like PostgreSQL)
        return [
            f
            for f in festivals
            if f.participating_villages and village_id in f.participating_villages
        ]

    async def create_festival(
        self, data: dict, user_id: str, is_admin: bool = False
    ) -> VillageFestival:
        """ایجاد جشنواره یا نمایشگاه."""
        villages = [v for v in (data.get("participating_villages") or []) if v]
        if villages:
            await self._ensure_village_write(villages, user_id, is_admin)
        else:
            await self._ensure_landscape_write(user_id, is_admin)
        festival = VillageFestival(
            name=data.get("name"),
            name_en=data.get("name_en"),
            description=data.get("description"),
            scope=data.get("scope", "local"),
            mode=data.get("mode", "both"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            participating_villages=data.get("participating_villages", []),
            registration_link=data.get("registration_link"),
            featured_products=data.get("featured_products", []),
            created_by=user_id,
        )
        self.db.add(festival)
        await self.db.commit()
        await self.db.refresh(festival)
        return festival

    # ========================================================================
    # 17. Nomadic Communities
    # ========================================================================

    async def get_nomadic_communities(self, approved_only: bool = True) -> list[NomadicCommunity]:
        """دریافت لیست جوامع عشایری."""
        query = select(NomadicCommunity).where(NomadicCommunity.is_active)
        if approved_only:
            query = query.where(NomadicCommunity.is_approved)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_nomadic_community(
        self, data: dict, user_id: str | None = None, is_admin: bool = False
    ) -> NomadicCommunity:
        """ثبت یک جامعهٔ عشایری تازه (نیازمند تأیید برای نمایش عمومی)."""
        await self._ensure_landscape_write(user_id, is_admin)
        community = NomadicCommunity(
            village_id=data.get("village_id"),
            owner_user_id=user_id,
            created_by=user_id,
            name=data.get("name"),
            name_en=data.get("name_en"),
            region=data.get("region"),
            country=data.get("country", "IR"),
            capacities=data.get("capacities", []),
            pasture_area_ha=data.get("pasture_area_ha"),
            migration_route=data.get("migration_route"),
            herd_size_estimate=data.get("herd_size_estimate"),
            tourism_experience=data.get("tourism_experience"),
            has_tented_accommodation=data.get("has_tented_accommodation", False),
            contact_person=data.get("contact_person"),
            contact_phone=data.get("contact_phone"),
        )
        self.db.add(community)
        await self.db.commit()
        await self.db.refresh(community)

        await _emit_hub_event(
            "nomadic_community_created",
            "nomadic_community",
            str(community.id),
            {
                "village_id": str(community.village_id or ""),
                "owner_user_id": str(community.owner_user_id or ""),
                "name": str(community.name or ""),
            },
        )
        _recipient = community.owner_user_id or community.created_by
        if _recipient:
            _notify(
                str(_recipient),
                "Your nomadic community was submitted for review.",
                ntype="system",
            )
        return community

    async def get_nomadic_community(self, community_id: str) -> NomadicCommunity:
        """دریافت یک جامعهٔ عشایری بر اساس شناسه."""
        result = await self.db.execute(
            select(NomadicCommunity).where(NomadicCommunity.id == community_id)
        )
        community = result.scalar_one_or_none()
        if not community:
            raise ValueError(f"جامعهٔ عشایری یافت نشد: {community_id}")
        return community

    async def _ensure_nomadic_mutation(
        self,
        community: NomadicCommunity,
        user_id: str | None,
        is_admin: bool,
        allow_owner: bool,
    ) -> None:
        """اجازهٔ ویرایش/حذف: مالک رکورد یا ادمین پلتفرم/عضو حکمرانی فعال.

        مالک (owner_user_id) می‌تواند رکورد خودش را ویرایش کند؛ در غیر این صورت
        از همان مجوز سطح‑منظره (_ensure_landscape_write) استفاده می‌شود.
        """
        if (
            allow_owner
            and community.owner_user_id is not None
            and str(community.owner_user_id) == str(user_id)
        ):
            return
        await self._ensure_landscape_write(user_id, is_admin)

    async def approve_nomadic_community(
        self, community_id: str, approver_user_id: str | None, is_admin: bool = False
    ) -> NomadicCommunity:
        """تأیید یک جامعهٔ عشایری — فقط ادمین پلتفرم یا عضو حکمرانی فعال."""
        community = await self.get_nomadic_community(community_id)
        await self._ensure_landscape_write(approver_user_id, is_admin)
        community.is_approved = True
        community.approved_by = approver_user_id
        community.approved_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(community)

        await _emit_hub_event(
            "nomadic_community_approved",
            "nomadic_community",
            str(community.id),
            {"approved_by": str(approver_user_id or "")},
        )
        _recipient = community.owner_user_id or community.created_by
        if _recipient:
            _notify(str(_recipient), "Your nomadic community has been approved.", ntype="system")
        return community

    async def update_nomadic_community(
        self,
        community_id: str,
        data: dict,
        user_id: str | None,
        is_admin: bool = False,
        allow_owner: bool = True,
    ) -> NomadicCommunity:
        """بروزرسانی یک جامعهٔ عشایری — مالک یا حکمرانی/ادمین."""
        community = await self.get_nomadic_community(community_id)
        await self._ensure_nomadic_mutation(community, user_id, is_admin, allow_owner)
        for key, value in data.items():
            if value is not None:
                setattr(community, key, value)
        community.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(community)
        return community

    async def delete_nomadic_community(
        self,
        community_id: str,
        user_id: str | None,
        is_admin: bool = False,
        allow_owner: bool = True,
    ) -> None:
        """حذف یک جامعهٔ عشایری (حذف کامل، مطابق روال delete_capability)."""
        community = await self.get_nomadic_community(community_id)
        await self._ensure_nomadic_mutation(community, user_id, is_admin, allow_owner)
        await self.db.delete(community)
        await self.db.commit()

    # ========================================================================
    # 18. Dossier (پرونده توسعه روستا)
    # ========================================================================

    async def get_village_dossier(self, village_id: str) -> dict:
        """دریافت پروندهٔ توسعهٔ کامل روستا."""
        await self._verify_village_exists(village_id)

        capabilities = await self.get_village_capabilities(village_id)
        opportunities = await self.get_village_opportunities(village_id)
        projects_result = await self.db.execute(
            select(VillageProject).where(VillageProject.village_id == village_id)
        )
        projects = projects_result.scalars().all()
        needs_result = await self.db.execute(
            select(VillageNeed).where(VillageNeed.village_id == village_id)
        )
        needs = needs_result.scalars().all()
        tourism_result = await self.db.execute(
            select(VillageTourismService).where(VillageTourismService.village_id == village_id)
        )
        tourism_services = tourism_result.scalars().all()
        events_result = await self.db.execute(
            select(VillageEvent).where(VillageEvent.village_id == village_id)
        )
        events = events_result.scalars().all()

        total_investment = Decimal("0.00")
        for proj in projects:
            total_investment += proj.investment_secured

        entrepreneur_count = await self.db.scalar(
            select(func.count(EntrepreneurProfile.id)).where(
                EntrepreneurProfile.village_id == village_id
            )
        )

        # The village belongs to the same unit of work as everything else in
        # this dossier: reading it through the injected session keeps the
        # method testable and consistent with the rest of the queries above.
        # It previously went through the global ``hub`` -- a second data path
        # that the service's callers cannot control -- and then read a
        # ``population`` attribute the model does not declare (S17, D-26/T-04).
        # ``village_id`` is the business key, not the primary key, so the row
        # is fetched by column, not with ``session.get``.
        village_result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        v = village_result.scalar_one_or_none()
        pop = v.total_members if v else 0

        return {
            "village_id": village_id,
            "name": v.name if v else None,
            "population": pop,
            "agriculture": [
                self._serialize_capability(c) for c in capabilities if c.category == "agriculture"
            ],
            "handicraft": [
                self._serialize_capability(c) for c in capabilities if c.category == "handicraft"
            ],
            "tourism_services": [self._serialize_tourism_service(s) for s in tourism_services],
            "events": [self._serialize_event(e) for e in events],
            "opportunities": [self._serialize_opportunity(o) for o in opportunities],
            "projects": [self._serialize_project(p) for p in projects],
            "needs": [self._serialize_need(n) for n in needs],
            "entrepreneurs_count": int(entrepreneur_count or 0),
            "total_investment": float(total_investment),
        }

    # ========================================================================
    # Serialization Helpers
    # ========================================================================

    def _serialize_capability(self, cap: VillageCapability) -> dict:
        return {
            "id": cap.id,
            "village_id": cap.village_id,
            "category": cap.category,
            "subcategory": cap.subcategory,
            "name": cap.name,
            "name_en": cap.name_en,
            "capacity_value": float(cap.capacity_value) if cap.capacity_value else None,
            "unit": cap.unit,
            "description": cap.description,
            "is_active": cap.is_active,
            "confidence": cap.confidence,
            "source": cap.source,
            "created_at": cap.created_at.isoformat() if cap.created_at else None,
            "updated_at": cap.updated_at.isoformat() if cap.updated_at else None,
        }

    def _serialize_opportunity(self, opp: VillageOpportunity) -> dict:
        return {
            "id": opp.id,
            "name": opp.name,
            "name_en": opp.name_en,
            "category": opp.category,
            "status": opp.status,
            "maturity": opp.maturity,
            "required_investment": float(opp.required_investment) if opp.required_investment else 0,
            "expected_revenue": float(opp.expected_revenue) if opp.expected_revenue else 0,
            "created_by": opp.created_by,
            "created_at": opp.created_at.isoformat() if opp.created_at else None,
            "updated_at": opp.updated_at.isoformat() if opp.updated_at else None,
        }

    def _serialize_project(self, proj: VillageProject) -> dict:
        return {
            "id": proj.id,
            "name": proj.name,
            "name_en": proj.name_en,
            "status": proj.status,
            "progress_pct": proj.progress_pct,
            "investment_needed": float(proj.investment_needed) if proj.investment_needed else 0,
            "investment_secured": float(proj.investment_secured) if proj.investment_secured else 0,
            "investors_count": proj.investors_count,
            "start_date": proj.start_date.isoformat() if proj.start_date else None,
            "expected_completion": proj.expected_completion.isoformat()
            if proj.expected_completion
            else None,
            "created_at": proj.created_at.isoformat() if proj.created_at else None,
        }

    def _serialize_tourism_service(self, svc: VillageTourismService) -> dict:
        return {
            "id": svc.id,
            "village_id": svc.village_id,
            "owner_user_id": svc.owner_user_id,
            "service_type": svc.service_type,
            "name": svc.name,
            "name_en": svc.name_en,
            "description": svc.description,
            "location": svc.location,
            "coordinates": svc.coordinates,
            "price_per_unit": float(svc.price_per_unit) if svc.price_per_unit else None,
            "capacity": svc.capacity,
            "is_organic": svc.is_organic,
            "is_regenerative": svc.is_regenerative,
            "images": svc.images or [],
            "contact_phone": svc.contact_phone,
            "contact_email": svc.contact_email,
            "is_verified": svc.is_verified,
            "status": svc.status,
            "created_at": svc.created_at.isoformat() if svc.created_at else None,
            "updated_at": svc.updated_at.isoformat() if svc.updated_at else None,
        }

    def _serialize_event(self, evt: VillageEvent) -> dict:
        return {
            "id": evt.id,
            "village_id": evt.village_id,
            "title": evt.title,
            "title_en": evt.title_en,
            "description": evt.description,
            "event_type": evt.event_type,
            "start_date": evt.start_date.isoformat() if evt.start_date else None,
            "end_date": evt.end_date.isoformat() if evt.end_date else None,
            "location": evt.location,
            "coordinates": evt.coordinates,
            "max_participants": evt.max_participants,
            "registration_fee": float(evt.registration_fee),
            "status": evt.status,
            "images": evt.images or [],
            "created_by": evt.created_by,
            "created_at": evt.created_at.isoformat() if evt.created_at else None,
            "updated_at": evt.updated_at.isoformat() if evt.updated_at else None,
            "registrations_count": len(evt.registrations) if evt.registrations else 0,
        }

    def _serialize_need(self, need: VillageNeed) -> dict:
        return {
            "id": need.id,
            "village_id": need.village_id,
            "category": need.category,
            "title": need.title,
            "description": need.description,
            "priority": need.priority,
            "estimated_investment": float(need.estimated_investment)
            if need.estimated_investment
            else None,
            "is_resolved": need.is_resolved,
            "resolved_by": need.resolved_by,
            "resolved_at": need.resolved_at.isoformat() if need.resolved_at else None,
            "created_at": need.created_at.isoformat() if need.created_at else None,
            "updated_at": need.updated_at.isoformat() if need.updated_at else None,
        }


# Singleton pattern
_hub_service: VillageDevelopmentHubService | None = None



# ========================================================================
# 19. B2B Commission (deep dive)
# ========================================================================

async def calculate_b2b_commission(
    self,
    demand_id: str,
    matched_village_id: str,
    agreed_amount: Decimal,
) -> dict:
    """Compute the platform commission for a matched B2B demand."""
    result = await self.db.execute(
        select(MarketplaceCommissionRule).where(
            MarketplaceCommissionRule.village_id == matched_village_id,
            MarketplaceCommissionRule.is_active,
        )
    )
    rule = result.scalar_one_or_none()
    bps = rule.platform_fee_bps if rule else 300
    commission = (agreed_amount * Decimal(bps) / Decimal(10000)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN
    )
    return {
        "demand_id": demand_id,
        "village_id": matched_village_id,
        "agreed_amount": str(agreed_amount),
        "commission_bps": bps,
        "commission_amount": str(commission),
        "net_to_village": str(agreed_amount - commission),
    }

def get_hub_service(db: AsyncSession | None = None) -> VillageDevelopmentHubService:
    """Get or create singleton VillageDevelopmentHubService."""
    global _hub_service
    if _hub_service is None or db is not None:
        _hub_service = VillageDevelopmentHubService(db)
    return _hub_service
