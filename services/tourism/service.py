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

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.tourism.departures import TourDeparture
from services.tourism.models import TourismBooking, TourismGuide, TourismTour
from services.village.models import CommunitySpace, SpaceStatus


class TourismService:
    """سرویس مدیریت گردشگری روستایی و عشایری."""

    # کارمزدها (basis points)
    PLATFORM_FEE_BPS = 800  # 8%
    LANDSCAPE_FEE_BPS = 200  # 2%
    INSURANCE_FEE_BPS = 200  # 2%
    HOST_SHARE_BPS = 8800  # 88%

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # مدیریت راهنمایان تور
    # ═══════════════════════════════════════════════════════════

    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_slug(self, title: str) -> str:
        """Generate a unique slug from title."""
        import re
        import secrets
        base = re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-")
        if not base:
            base = "tour"
        suffix = secrets.token_hex(4)
        return f"{base[:100]}-{suffix}"

    def _generate_booking_number(self) -> str:
        """Generate a unique booking number."""
        from datetime import UTC, datetime
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"TR-{timestamp}-{random_suffix}"

    async def register_guide(
        self,
        user_id: str,
        village_id: str,
        full_name: str,
        bio: str | None = None,
        languages: list[str] | None = None,
        specialties: list[str] | None = None,
        license_number: str | None = None,
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
        result = await self.db.execute(select(TourismGuide).where(TourismGuide.id == guide_id))
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
        description: str | None = None,
        max_participants: int = 10,
        min_participants: int = 2,
        difficulty: str = "moderate",
        ecological_capacity: int | None = None,
        is_regenerative: bool = True,
        regenerative_activity: str | None = None,
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

        # Ecotourism tours require the destination village to be governance-active.
        if tour_type == "ecotourism":
            space = (
                await self.db.execute(
                    select(CommunitySpace).where(
                        CommunitySpace.village_id == village_id,
                        CommunitySpace.status == SpaceStatus.ACTIVE.value,
                    )
                )
            ).scalar_one_or_none()
            if space is None:
                raise ValueError(
                    f"تور بوم‌گردی برای روستای {village_id} مجاز نیست: "
                    "حکمرانی روستا هنوز فعال نشده است"
                )

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
        result = await self.db.execute(select(TourismTour).where(TourismTour.id == tour_id))
        tour = result.scalar_one_or_none()

        if not tour:
            raise ValueError(f"تور یافت نشد: {tour_id}")

        tour.status = "active"
        tour.approved_by = approved_by
        tour.approved_at = datetime.now(UTC)

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
        special_requests: str | None = None,
        regenerative_commitment: str | None = None,
        departure_id: str | None = None,
    ) -> TourismBooking:
        """ایجاد رزرو جدید با بررسی ظرفیت و محاسبه خودکار کارمزد."""
        # دریافت تور
        result = await self.db.execute(select(TourismTour).where(TourismTour.id == tour_id))
        tour = result.scalar_one_or_none()

        if not tour:
            raise ValueError(f"تور یافت نشد: {tour_id}")

        if tour.status != "active":
            raise ValueError("این تور فعال نیست")

        # بررسی حداقل شرکت‌کنندگان
        if participants_count < tour.min_participants:
            raise ValueError(f"حداقل {tour.min_participants} شرکت‌کننده نیاز است")

        # بررسی حداکثر شرکت‌کنندگان
        if participants_count > tour.max_participants:
            raise ValueError(f"حداکثر {tour.max_participants} شرکت‌کننده مجاز است")

        # ظرفیت برگزاری (در صورت انتخاب تاریخ مشخص) — همان دفتر صندلی؛ ظرفیت
        # برگزاری هنگام ایجادش روی min(ظرفیت خود، ظرفیت اکولوژیک تور) محدود شده
        departure: TourDeparture | None = None
        if departure_id:
            departure = (
                await self.db.execute(
                    select(TourDeparture).where(TourDeparture.id == departure_id)
                )
            ).scalar_one_or_none()
            if departure is None:
                raise ValueError(f"برگزاری یافت نشد: {departure_id}")
            if str(departure.tour_id) != str(tour_id):
                raise ValueError("این برگزاری به تور دیگری تعلق دارد")
            # The seats a booking consumes belong to the departure it travels on:
            # binding the dates stops a booking for one day from eating a future
            # departure's seats.
            tour_date_utc = (
                tour_date if tour_date.tzinfo else tour_date.replace(tzinfo=UTC)
            ).astimezone(UTC)
            if departure.departure_date != tour_date_utc.date():
                raise ValueError(
                    "تاریخ رزرو با تاریخ برگزاری یکی نیست: "
                    f"{tour_date_utc.date()} != {departure.departure_date}"
                )
            # the one seat rule (status, remaining, booked, auto-close) lives on
            # the model, shared with DepartureService
            departure.take_seats(participants_count)

        # بررسی ظرفیت برد اکولوژیک
        if tour.ecological_capacity and (
            tour.current_bookings + participants_count > tour.ecological_capacity
        ):
            available = tour.ecological_capacity - tour.current_bookings
            raise ValueError(f"ظرفیت برد اکولوژیک تکمیل است. فقط {available} نفر باقی مانده")

        # بررسی تاریخ
        if tour_date <= datetime.now(UTC):
            raise ValueError("تاریخ تور باید در آینده باشد")

        # محاسبه مبالغ با قیمت پویا (نسبت‌پردازی و scarcité)
        subtotal = self.compute_dynamic_price(tour, participants_count)
        # Each fee line is quantised to the cent before the total is formed,
        # mirroring ``commerce/service.py:OrderService._compute_fees`` and
        # ``marketplace/service.py``: the booking used to be built from the
        # unrounded divisions, and the ``Numeric(15, 2)`` columns round each
        # figure independently on read, so the stored fee lines need not sum to
        # the stored total -- a 0.13-per-person single-participant tour stored
        # lines of 0.01, 0.00 and 0.00 (0.01 in fees) against a total of 0.15,
        # a cent no line accounted for.
        platform_fee = (
            subtotal * Decimal(self.PLATFORM_FEE_BPS) / Decimal(10000)
        ).quantize(Decimal("0.01"))
        landscape_fee = (
            subtotal * Decimal(self.LANDSCAPE_FEE_BPS) / Decimal(10000)
        ).quantize(Decimal("0.01"))
        insurance_fee = (
            subtotal * Decimal(self.INSURANCE_FEE_BPS) / Decimal(10000)
        ).quantize(Decimal("0.01"))
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
        # (the departure ledger advanced with take_seats above — one seat rule,
        # one increment path)

        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)

        return booking


    # ═══════════════════════════════════════════════════════════
    # regenerative reporting
    # ═══════════════════════════════════════════════════════════

    async def regenerative_report(
        self,
        village_id: str | None = None,
    ) -> dict:
        """Report on regenerative ecotourism activity and impact."""
        q = select(TourismTour).where(TourismTour.is_regenerative)
        if village_id is not None:
            q = q.where(TourismTour.village_id == village_id)
        tours = (await self.db.execute(q)).scalars().all()
        tour_ids = [str(t.id) for t in tours]
        if tour_ids:
            bookings_q = select(TourismBooking).where(
                TourismBooking.tour_id.in_(tour_ids)
            )
        else:
            bookings_q = select(TourismBooking).where(TourismBooking.id == "nonexistent")
        bookings = (await self.db.execute(bookings_q)).scalars().all()
        completed = sum(1 for b in bookings if b.regenerative_completed)
        participants = sum(b.participants_count for b in bookings)
        total_revenue = sum(float(b.total) for b in bookings)
        landscape_fees = sum(float(b.landscape_fee) for b in bookings)
        return {
            "village_id": village_id,
            "regenerative_tours": len(tours),
            "active_tours": sum(1 for t in tours if t.status == "active"),
            "total_bookings": len(bookings),
            "completed_regenerative_commitments": completed,
            "regenerative_participants": participants,
            "total_revenue": round(total_revenue, 2),
            "landscape_fees_collected": round(landscape_fees, 2),
            "completion_rate": round(completed / len(bookings), 4) if bookings else 0.0,
        }
    # ═══════════════════════════════════════════════════════════
    # dynamic pricing
    # ═══════════════════════════════════════════════════════════

    def compute_dynamic_price(
        self,
        tour: TourismTour,
        participants_count: int = 1,
    ) -> Decimal:
        """Compute a dynamic price for a tour booking."""
        base = tour.price_per_person
        multiplier = Decimal("1.00")

        # Scarcity: as the tour fills, price rises (capped at +50%).
        if tour.max_participants and tour.max_participants > 0:
            fill_ratio = Decimal(tour.current_bookings) / Decimal(
                tour.max_participants
            )
            if fill_ratio >= Decimal("0.8"):
                multiplier += Decimal("0.50")
            elif fill_ratio >= Decimal("0.5"):
                multiplier += Decimal("0.25")

        price = (base * multiplier).quantize(Decimal("0.01"))
        return price * participants_count


    # ═══════════════════════════════════════════════════════════
    # regenerative certificate
    # ═══════════════════════════════════════════════════════════

    async def issue_regenerative_certificate(
        self,
        booking_id: str,
        issued_by: str,
    ) -> dict:
        """Issue a regenerative-tourism certificate for a completed booking."""
        booking = (
            await self.db.execute(
                select(TourismBooking).where(TourismBooking.id == booking_id)
            )
        ).scalar_one_or_none()
        if booking is None:
            raise ValueError(f"booking not found: {booking_id}")
        if not booking.regenerative_completed:
            raise ValueError("regenerative commitment not completed")
        import hashlib
        from uuid import uuid4
        cert_id = f"REG-{str(uuid4())[:8]}"
        payload = f"{booking.booking_number}:{booking.tour_id}:{booking.total}"
        cert_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return {
            "certificate_id": cert_id,
            "certificate_hash": cert_hash,
            "booking_id": booking_id,
            "booking_number": booking.booking_number,
            "tour_id": str(booking.tour_id),
            "village_id": booking.village_id,
            "guest_id": booking.guest_id,
            "issued_by": issued_by,
            "issued_at": datetime.now(UTC).isoformat(),
            "regenerative_completed": booking.regenerative_completed,
            "total": str(booking.total),
            "currency": booking.currency,
        }



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

    async def _update_tour_stats(self, tour_id: str) -> None:
        """Recompute the tour's paid-booking counter.

        ``total_bookings`` counts the bookings whose payment has been
        confirmed; ``current_bookings`` counts the *participants* the tour
        still holds and is maintained by ``create_booking`` / ``cancel_booking``.

        This method was missing from the class. The payment-confirmation path
        calls it, so every ``confirm-payment`` request raised ``AttributeError``
        (HTTP 500), the paid-booking counter never moved, and the
        booking -> pay -> complete chain was unreachable.
        """
        tour = (
            await self.db.execute(
                select(TourismTour).where(TourismTour.id == tour_id)
            )
        ).scalar_one_or_none()
        if tour is None:
            return

        paid = (
            await self.db.execute(
                select(func.count(TourismBooking.id)).where(
                    TourismBooking.tour_id == tour_id,
                    TourismBooking.payment_status == "paid",
                )
            )
        ).scalar_one()

        tour.total_bookings = int(paid or 0)
        await self.db.commit()

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

    async def cancel_booking(
        self, booking_id: str, reason: str, refund_requested: bool = True
    ) -> TourismBooking:
        """ظ„ط؛ظˆ ط±ط²ط±ظˆ با محاسبه بازپرداخت."""
        result = await self.db.execute(
            select(TourismBooking).where(TourismBooking.id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise ValueError(f"ط±ط²ط±ظˆ غŒط§ظپطھ ظ†ط´ط¯: {booking_id}")

        if booking.status == "cancelled":
            raise ValueError("پیش از این لغو شده است")

        # محاسبه بازپرداخت بر اساس فاصله تا تور
        refund_amount = Decimal("0.00")
        if refund_requested:
            refund_amount = self._calculate_refund(booking)

        booking.status = "cancelled"
        booking.cancel_reason = reason

        # ع©ط§ظ‡ط´ ط¢ظ…ط§ط± طھظˆط±
        result = await self.db.execute(select(TourismTour).where(TourismTour.id == booking.tour_id))
        tour = result.scalar_one_or_none()
        if tour:
            tour.current_bookings = max(
                0, tour.current_bookings - booking.participants_count
            )

        # ط¢ط²ط§ط¯ط³ط§ط²غŒ طµظ†ط¯ظ„غŒ ظ‡ظ…ط§ظ† ط¨ط±ع¯ط²ط§ط±غŒ
        tour_date_utc = (
            booking.tour_date
            if booking.tour_date.tzinfo
            else booking.tour_date.replace(tzinfo=UTC)
        ).astimezone(UTC)
        departures = (
            await self.db.execute(
                select(TourDeparture).where(
                    TourDeparture.tour_id == booking.tour_id,
                    TourDeparture.departure_date == tour_date_utc.date(),
                )
            )
        ).scalars().all()
        from services.tourism.safety_service import TourismSafetyService

        safety = TourismSafetyService(self.db)
        for departure in departures:
            may_reopen = not await safety.departure_is_blocked(str(departure.id))
            departure.release_seats(booking.participants_count, may_reopen=may_reopen)

        # ثبت مبلغ بازپرداخت
        if refund_amount > 0:
            booking.refund_amount = refund_amount
            booking.refund_status = "pending"

        await self.db.commit()
        await self.db.refresh(booking)

        # The paid-booking counter follows the cancellation.
        await self._update_tour_stats(booking.tour_id)

        return booking

    def _calculate_refund(self, booking: TourismBooking) -> Decimal:
        """Calculate refund based on days until tour."""
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        tour_date = booking.tour_date if booking.tour_date.tzinfo else booking.tour_date.replace(tzinfo=UTC)
        days_until = (tour_date - now).days

        # Refund policy:
        # - > 30 days: 90% of total
        # - 15-30 days: 70% of total
        # - 7-14 days: 50% of total
        # - 3-6 days: 25% of total
        # - < 3 days: 0%

        if days_until > 30:
            rate = Decimal("0.90")
        elif days_until >= 15:
            rate = Decimal("0.70")
        elif days_until >= 7:
            rate = Decimal("0.50")
        elif days_until >= 3:
            rate = Decimal("0.25")
        else:
            rate = Decimal("0.00")

        refund = (booking.total * rate).quantize(Decimal("0.01"))
        return refund
        return booking
