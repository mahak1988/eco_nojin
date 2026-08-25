"""
سرویس کامل گردشگری روستایی و عشایری
═══════════════════════════════════════════════════════════════════════
این سرویس شامل:
- مدیریت تورها و راهنمایان
- پردازش رزروها
- بررسی ظرفیت برد اکولوژیک
- محاسبه کارمزد و بیمه
- تورهای احیاکننده (Regenerative)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.tourism.models import TourismTour, TourismBooking, TourismGuide


class TourismService:
    """سرویس مدیریت گردشگری روستایی و عشایری."""
    
    # کارمزدها (basis points)
    PLATFORM_FEE_BPS = 800      # 8%
    LANDSCAPE_FEE_BPS = 200     # 2%
    INSURANCE_FEE_BPS = 200     # 2%
    HOST_SHARE_BPS = 8800       # 88%
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ═══════════════════════════════════════════════════════════
    # مدیریت راهنمایان تور
    # ═══════════════════════════════════════════════════════════
    
    async def register_guide(
        self,
        user_id: str,
        village_id: str,
        full_name: str,
        bio: Optional[str] = None,
        languages: Optional[List[str]] = None,
        specialties: Optional[List[str]] = None,
        license_number: Optional[str] = None,
    ) -> TourismGuide:
        """ثبت راهنمای تور جدید."""
        if not full_name or len(full_name.strip()) == 0:
            raise ValueError("نام کامل نمی‌تواند خالی باشد")
        
        guide = TourismGuide(
            user_id=user_id,
            village_id=village_id,
            full_name=full_name,
            bio=bio,
            languages=languages or [],
            specialties=specialties or [],
            license_number=license_number,
            is_verified=False,
        )
        
        self.db.add(guide)
        await self.db.commit()
        await self.db.refresh(guide)
        
        return guide
    
    async def verify_guide(self, guide_id: str) -> TourismGuide:
        """تأیید راهنمای تور."""
        result = await self.db.execute(
            select(TourismGuide).where(TourismGuide.id == guide_id)
        )
        guide = result.scalar_one_or_none()
        
        if not guide:
            raise ValueError(f"راهنما یافت نشد: {guide_id}")
        
        guide.is_verified = True
        await self.db.commit()
        await self.db.refresh(guide)
        
        return guide
    
    # ═══════════════════════════════════════════════════════════
    # مدیریت تورها
    # ═══════════════════════════════════════════════════════════
    
    async def create_tour(
        self,
        guide_id: str,
        village_id: str,
        title: str,
        tour_type: str,
        duration_hours: int,
        price_per_person: Decimal,
        description: Optional[str] = None,
        max_participants: int = 10,
        min_participants: int = 2,
        difficulty: str = "moderate",
        ecological_capacity: Optional[int] = None,
        is_regenerative: bool = True,
        regenerative_activity: Optional[str] = None,
    ) -> TourismTour:
        """ثبت تور جدید با بررسی ظرفیت اکولوژیک."""
        if not title or len(title.strip()) == 0:
            raise ValueError("عنوان تور نمی‌تواند خالی باشد")
        
        if price_per_person <= 0:
            raise ValueError("قیمت باید مثبت باشد")
        
        if duration_hours <= 0:
            raise ValueError("مدت تور باید مثبت باشد")
        
        if max_participants < min_participants:
            raise ValueError("حداکثر شرکت‌کنندگان نمی‌تواند کمتر از حداقل باشد")
        
        # بررسی وجود راهنما
        guide_result = await self.db.execute(
            select(TourismGuide).where(TourismGuide.id == guide_id)
        )
        guide = guide_result.scalar_one_or_none()
        if not guide:
            raise ValueError(f"راهنما یافت نشد: {guide_id}")
        
        if not guide.is_verified:
            raise ValueError("راهنما هنوز تأیید نشده است")
        
        # تولید slug
        slug = self._generate_slug(title)
        
        # ایجاد تور
        tour = TourismTour(
            guide_id=guide_id,
            village_id=village_id,
            title=title,
            slug=slug,
            description=description,
            tour_type=tour_type,
            duration_hours=duration_hours,
            max_participants=max_participants,
            min_participants=min_participants,
            difficulty=difficulty,
            price_per_person=price_per_person,
            ecological_capacity=ecological_capacity,
            status="pending_approval",
            is_regenerative=is_regenerative,
            regenerative_activity=regenerative_activity,
        )
        
        self.db.add(tour)
        await self.db.commit()
        await self.db.refresh(tour)
        
        return tour
    
    async def approve_tour(self, tour_id: str, approved_by: str) -> TourismTour:
        """تأیید تور توسط مدیر منظر."""
        result = await self.db.execute(
            select(TourismTour).where(TourismTour.id == tour_id)
        )
        tour = result.scalar_one_or_none()
        
        if not tour:
            raise ValueError(f"تور یافت نشد: {tour_id}")
        
        tour.status = "active"
        tour.approved_by = approved_by
        tour.approved_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(tour)
        
        return tour
    
    # ═══════════════════════════════════════════════════════════
    # مدیریت رزروها
    # ═══════════════════════════════════════════════════════════
    
    async def create_booking(
        self,
        tour_id: str,
        guest_id: str,
        participants_count: int,
        tour_date: datetime,
        village_id: str,
        special_requests: Optional[str] = None,
        regenerative_commitment: Optional[str] = None,
    ) -> TourismBooking:
        """ایجاد رزرو جدید با بررسی ظرفیت و محاسبه خودکار کارمزد."""
        # دریافت تور
        result = await self.db.execute(
            select(TourismTour).where(TourismTour.id == tour_id)
        )
        tour = result.scalar_one_or_none()
        
        if not tour:
            raise ValueError(f"تور یافت نشد: {tour_id}")
        
        if tour.status != "active":
            raise ValueError("این تور فعال نیست")
        
        # بررسی حداقل شرکت‌کنندگان
        if participants_count < tour.min_participants:
            raise ValueError(
                f"حداقل {tour.min_participants} شرکت‌کننده نیاز است"
            )
        
        # بررسی حداکثر شرکت‌کنندگان
        if participants_count > tour.max_participants:
            raise ValueError(
                f"حداکثر {tour.max_participants} شرکت‌کننده مجاز است"
            )
        
        # بررسی ظرفیت برد اکولوژیک
        if tour.ecological_capacity:
            if tour.current_bookings + participants_count > tour.ecological_capacity:
                available = tour.ecological_capacity - tour.current_bookings
                raise ValueError(
                    f"ظرفیت برد اکولوژیک تکمیل است. فقط {available} نفر باقی مانده"
                )
        
        # بررسی تاریخ
        if tour_date <= datetime.now(timezone.utc):
            raise ValueError("تاریخ تور باید در آینده باشد")
        
        # محاسبه مبالغ
        subtotal = tour.price_per_person * participants_count
        platform_fee = subtotal * Decimal(self.PLATFORM_FEE_BPS) / Decimal(10000)
        landscape_fee = subtotal * Decimal(self.LANDSCAPE_FEE_BPS) / Decimal(10000)
        insurance_fee = subtotal * Decimal(self.INSURANCE_FEE_BPS) / Decimal(10000)
        total = subtotal + platform_fee + landscape_fee + insurance_fee
        
        # تولید شماره رزرو
        booking_number = self._generate_booking_number()
        
        # ایجاد رزرو
        booking = TourismBooking(
            booking_number=booking_number,
            tour_id=tour_id,
            guest_id=guest_id,
            village_id=village_id,
            participants_count=participants_count,
            tour_date=tour_date,
            subtotal=subtotal,
            platform_fee=platform_fee,
            landscape_fee=landscape_fee,
            insurance_fee=insurance_fee,
            total=total,
            special_requests=special_requests,
            regenerative_commitment=regenerative_commitment,
            status="pending",
        )
        
        # به‌روزرسانی آمار تور
        tour.current_bookings += participants_count
        
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        
        return booking
    
    async def confirm_booking(self, booking_id: str, payment_tx_hash: str) -> TourismBooking:
        """تأیید پرداخت رزرو."""
        result = await self.db.execute(
            select(TourismBooking).where(TourismBooking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise ValueError(f"رزرو یافت نشد: {booking_id}")
        
        booking.payment_status = "paid"
        booking.status = "confirmed"
        booking.blockchain_tx_hash = payment_tx_hash
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        # به‌روزرسانی آمار تور
        await self._update_tour_stats(booking.tour_id)
        
        return booking
    
    async def complete_booking(self, booking_id: str) -> TourismBooking:
        """تکمیل رزرو (پس از برگزاری تور)."""
        result = await self.db.execute(
            select(TourismBooking).where(TourismBooking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise ValueError(f"رزرو یافت نشد: {booking_id}")
        
        if booking.status != "confirmed":
            raise ValueError("رزرو هنوز تأیید نشده است")
        
        booking.status = "completed"
        booking.settlement_status = "completed"
        
        # اگر تور احیاکننده است، فعالیت احیاکننده را تأیید کن
        if booking.regenerative_commitment:
            booking.regenerative_completed = True
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        return booking
    
    async def cancel_booking(self, booking_id: str, reason: str) -> TourismBooking:
        """لغو رزرو."""
        result = await self.db.execute(
            select(TourismBooking).where(TourismBooking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise ValueError(f"رزرو یافت نشد: {booking_id}")
        
        booking.status = "cancelled"
        
        # کاهش آمار تور
        result = await self.db.execute(
            select(TourismTour).where(TourismTour.id == booking.tour_id)
        )
        tour = result.scalar_one_or_none()
        if tour:
            tour.current_bookings -= booking.participants_count
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        return booking
    
    # ═══════════════════════════════════════════════════════════
    # توابع داخلی
    # ═══════════════════════════════════════════════════════════
    
    async def _update_tour_stats(self, tour_id: str):
        """به‌روزرسانی آمار تور."""
        result = await self.db.execute(
            select(TourismTour).where(TourismTour.id == tour_id)
        )
        tour = result.scalar_one_or_none()
        
        if tour:
            tour.total_bookings += 1
            await self.db.commit()
    
    def _generate_slug(self, title: str) -> str:
        """تولید slug یکتا."""
        base_slug = title.lower().replace(" ", "-")[:100]
        random_suffix = secrets.token_hex(4)
        return f"{base_slug}-{random_suffix}"
    
    def _generate_booking_number(self) -> str:
        """تولید شماره رزرو یکتا."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"TR-{timestamp}-{random_suffix}"
