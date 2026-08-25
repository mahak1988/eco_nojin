"""
تست‌های Integration برای Tourism
═══════════════════════════════════════════════════════════════════════
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta


class TestTourismIntegration:
    """تست‌های یکپارچگی گردشگری."""
    
    @pytest.mark.asyncio
    async def test_complete_booking_flow(self, tourism_service):
        """تست جریان کامل رزرو."""
        # 1. ثبت راهنما
        guide = await tourism_service.register_guide(
            user_id="guide_123",
            village_id="hejij",
            full_name="محمد رضایی",
            bio="راهنمای تورهای عشایری",
            languages=["fa", "en"],
            specialties=["nomadic", "cultural"],
        )
        assert guide is not None
        
        # 2. تأیید راهنما
        guide = await tourism_service.verify_guide(str(guide.id))
        assert guide.is_verified
        
        # 3. ایجاد تور
        tour = await tourism_service.create_tour(
            guide_id=str(guide.id),
            village_id="hejij",
            title="تور عشایری کرمانشاه",
            tour_type="nomadic",
            duration_hours=8,
            price_per_person=Decimal("500000"),
            max_participants=10,
            ecological_capacity=50,
            is_regenerative=True,
            regenerative_activity="کاشت 10 نهال",
        )
        assert tour is not None
        
        # 4. تأیید تور
        tour = await tourism_service.approve_tour(str(tour.id), "manager_123")
        assert tour.status == "active"
        
        # 5. ایجاد رزرو
        tour_date = datetime.now(timezone.utc) + timedelta(days=7)
        booking = await tourism_service.create_booking(
            tour_id=str(tour.id),
            guest_id="guest_123",
            participants_count=4,
            tour_date=tour_date,
            village_id="hejij",
            regenerative_commitment="کاشت 10 نهال در منطقه",
        )
        assert booking is not None
        assert booking.total > 0
        
        # 6. تأیید رزرو
        booking = await tourism_service.confirm_booking(str(booking.id), "tx_hash_123")
        assert booking.status == "confirmed"
        
        # 7. تکمیل رزرو
        booking = await tourism_service.complete_booking(str(booking.id))
        assert booking.status == "completed"
        assert booking.regenerative_completed
