"""
سرویس کامل مدیریت یکپارچه منظر (ILM)
═══════════════════════════════════════════════════════════════════════
این سرویس شامل:
- مدیریت روستاها و منظرها
- مدیریت ساختار حکمرانی
- مدیریت صندوق توسعه
- توزیع وجوه با تأیید شورا
- اتصال به بلاکچین
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.landscape.models import (
    LandscapeFund,
    LandscapeFundDistribution,
    LandscapeGovernanceMember,
    LandscapeVillage,
)


class LandscapeService:
    """سرویس مدیریت یکپارچه منظر."""

    # کارمزد پیش‌فرض صندوق (1%)
    DEFAULT_FEE_BPS = 100

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # مدیریت روستاها
    # ═══════════════════════════════════════════════════════════

    async def register_village(
        self,
        village_id: str,
        name: str,
        region: str,
        country: str = "IR",
        coordinates: dict | None = None,
        geo_boundary: dict | None = None,
        brand_name: str | None = None,
    ) -> LandscapeVillage:
        """ثبت روستای جدید."""
        if not name or len(name.strip()) == 0:
            raise ValueError("نام روستا نمی‌تواند خالی باشد")

        if not region or len(region.strip()) == 0:
            raise ValueError("منطقه نمی‌تواند خالی باشد")

        # بررسی وجود روستا
        existing = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"روستا قبلاً ثبت شده است: {village_id}")

        village = LandscapeVillage(
            village_id=village_id,
            name=name,
            region=region,
            country=country,
            coordinates=coordinates,
            geo_boundary=geo_boundary,
            brand_name=brand_name or name,
            is_active=True,
            active_modules=["marketplace", "tourism"],
        )

        self.db.add(village)
        await self.db.commit()
        await self.db.refresh(village)

        # ایجاد صندوق مدیریت منظر
        await self._create_landscape_fund(village_id)

        return village

    async def update_village(
        self,
        village_id: str,
        name: str | None = None,
        brand_name: str | None = None,
        active_modules: list[str] | None = None,
    ) -> LandscapeVillage:
        """به‌روزرسانی اطلاعات روستا."""
        result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        village = result.scalar_one_or_none()

        if not village:
            raise ValueError(f"روستا یافت نشد: {village_id}")

        if name:
            village.name = name
        if brand_name:
            village.brand_name = brand_name
        if active_modules is not None:
            village.active_modules = active_modules

        village.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(village)

        return village

    async def deactivate_village(self, village_id: str) -> LandscapeVillage:
        """غیرفعال‌سازی روستا."""
        result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        village = result.scalar_one_or_none()

        if not village:
            raise ValueError(f"روستا یافت نشد: {village_id}")

        village.is_active = False
        await self.db.commit()
        await self.db.refresh(village)

        return village

    # ═══════════════════════════════════════════════════════════
    # مدیریت حکمرانی
    # ═══════════════════════════════════════════════════════════

    async def add_governance_member(
        self,
        village_id: str,
        user_id: str,
        role: str,
        term_start: datetime | None = None,
        term_end: datetime | None = None,
    ) -> LandscapeGovernanceMember:
        """افزودن عضو به ساختار حکمرانی."""
        valid_roles = [
            "council_member",
            "landscape_manager",
            "marketplace_rep",
            "tourism_rep",
            "agriculture_rep",
            "knowledge_rep",
        ]

        if role not in valid_roles:
            raise ValueError(f"نقش نامعتبر: {role}. نقش‌های معتبر: {valid_roles}")

        member = LandscapeGovernanceMember(
            village_id=village_id,
            user_id=user_id,
            role=role,
            is_active=True,
            term_start=term_start,
            term_end=term_end,
            elected_at=datetime.now(UTC),
        )

        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)

        return member

    async def remove_governance_member(self, member_id: str) -> LandscapeGovernanceMember:
        """حذف عضو از ساختار حکمرانی."""
        result = await self.db.execute(
            select(LandscapeGovernanceMember).where(LandscapeGovernanceMember.id == member_id)
        )
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError(f"عضو یافت نشد: {member_id}")

        member.is_active = False
        await self.db.commit()
        await self.db.refresh(member)

        return member

    # ═══════════════════════════════════════════════════════════
    # مدیریت صندوق توسعه
    # ═══════════════════════════════════════════════════════════

    async def _create_landscape_fund(self, village_id: str) -> LandscapeFund:
        """ایجاد صندوق مدیریت منظر برای روستا."""
        fund = LandscapeFund(
            village_id=village_id,
            fee_bps=self.DEFAULT_FEE_BPS,
            total_collected=Decimal("0.00"),
            total_distributed=Decimal("0.00"),
            pending_balance=Decimal("0.00"),
            currency="IRR",
            is_active=True,
        )

        self.db.add(fund)
        await self.db.commit()
        await self.db.refresh(fund)

        return fund

    async def get_fund_balance(self, village_id: str) -> dict:
        """دریافت موجودی صندوق روستا."""
        result = await self.db.execute(
            select(LandscapeFund).where(LandscapeFund.village_id == village_id)
        )
        fund = result.scalar_one_or_none()

        if not fund:
            raise ValueError(f"صندوق یافت نشد: {village_id}")

        return {
            "village_id": village_id,
            "total_collected": float(fund.total_collected),
            "total_distributed": float(fund.total_distributed),
            "pending_balance": float(fund.pending_balance),
            "currency": fund.currency,
            "fee_bps": fund.fee_bps,
        }

    async def create_fund_distribution(
        self,
        village_id: str,
        amount: Decimal,
        purpose: str,
        proposed_by: str,
        recipient_user_id: str | None = None,
        recipient_organization: str | None = None,
        description: str | None = None,
    ) -> LandscapeFundDistribution:
        """ایجاد درخواست توزیع وجوه."""
        if amount <= 0:
            raise ValueError("مبلغ باید مثبت باشد")

        # دریافت صندوق
        result = await self.db.execute(
            select(LandscapeFund).where(LandscapeFund.village_id == village_id)
        )
        fund = result.scalar_one_or_none()

        if not fund:
            raise ValueError(f"صندوق یافت نشد: {village_id}")

        # بررسی موجودی
        if amount > fund.pending_balance:
            raise ValueError(
                f"موجودی کافی نیست. موجودی: {fund.pending_balance}, درخواست: {amount}"
            )

        distribution = LandscapeFundDistribution(
            fund_id=fund.id,
            village_id=village_id,
            amount=amount,
            purpose=purpose,
            description=description,
            recipient_user_id=recipient_user_id,
            recipient_organization=recipient_organization,
            proposed_by=proposed_by,
            status="pending",
        )

        self.db.add(distribution)
        await self.db.commit()
        await self.db.refresh(distribution)

        return distribution

    async def approve_distribution(
        self,
        distribution_id: str,
        approved_by: str,
    ) -> LandscapeFundDistribution:
        """تأیید درخواست توزیع وجوه توسط شورا."""
        result = await self.db.execute(
            select(LandscapeFundDistribution).where(LandscapeFundDistribution.id == distribution_id)
        )
        distribution = result.scalar_one_or_none()

        if not distribution:
            raise ValueError(f"درخواست یافت نشد: {distribution_id}")

        if distribution.status != "pending":
            raise ValueError(f"درخواست در وضعیت {distribution.status} است")

        distribution.status = "approved"
        distribution.approved_by = approved_by
        distribution.approved_at = datetime.now(UTC)

        # کاهش موجودی صندوق
        result = await self.db.execute(
            select(LandscapeFund).where(LandscapeFund.id == distribution.fund_id)
        )
        fund = result.scalar_one_or_none()

        if fund:
            fund.pending_balance -= distribution.amount
            fund.total_distributed += distribution.amount

        await self.db.commit()
        await self.db.refresh(distribution)

        return distribution

    async def execute_distribution(
        self,
        distribution_id: str,
        blockchain_tx_hash: str,
    ) -> LandscapeFundDistribution:
        """اجرای توزیع وجوه (پس از تأیید و انتقال روی بلاکچین)."""
        result = await self.db.execute(
            select(LandscapeFundDistribution).where(LandscapeFundDistribution.id == distribution_id)
        )
        distribution = result.scalar_one_or_none()

        if not distribution:
            raise ValueError(f"درخواست یافت نشد: {distribution_id}")

        if distribution.status != "approved":
            raise ValueError("درخواست هنوز تأیید نشده است")

        distribution.status = "executed"
        distribution.blockchain_tx_hash = blockchain_tx_hash
        distribution.executed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(distribution)

        return distribution

    # ═══════════════════════════════════════════════════════════
    # آمار و گزارش‌ها
    # ═══════════════════════════════════════════════════════════

    async def get_village_stats(self, village_id: str) -> dict:
        """دریافت آمار روستا."""
        result = await self.db.execute(
            select(LandscapeVillage).where(LandscapeVillage.village_id == village_id)
        )
        village = result.scalar_one_or_none()

        if not village:
            raise ValueError(f"روستا یافت نشد: {village_id}")

        # شمارش اعضای حکمرانی
        governance_result = await self.db.execute(
            select(LandscapeGovernanceMember).where(
                LandscapeGovernanceMember.village_id == village_id,
                LandscapeGovernanceMember.is_active == True
            )
        )
        governance_members = governance_result.scalars().all()

        return {
            "village_id": village_id,
            "name": village.name,
            "region": village.region,
            "is_active": village.is_active,
            "active_modules": village.active_modules,
            "total_members": village.total_members,
            "active_sellers": village.active_sellers,
            "active_tour_guides": village.active_tour_guides,
            "monthly_gmv": float(village.monthly_gmv),
            "governance_members_count": len(governance_members),
        }
