"""
تست‌های Integration برای Landscape
═══════════════════════════════════════════════════════════════════════
"""


import pytest


class TestLandscapeIntegration:
    """تست‌های یکپارچگی مدیریت منظر."""

    @pytest.mark.asyncio
    async def test_complete_village_flow(self, landscape_service):
        """تست جریان کامل روستا."""
        # 1. ثبت روستا
        village = await landscape_service.register_village(
            village_id="hejij",
            name="روستای هجیج",
            region="کرمانشاه",
            country="IR",
            coordinates={"lat": 34.5, "lon": 47.1},
        )
        assert village is not None
        assert village.is_active

        # 2. افزودن اعضای حکمرانی
        manager = await landscape_service.add_governance_member(
            village_id="hejij",
            user_id="manager_123",
            role="landscape_manager",
        )
        assert manager is not None

        council = await landscape_service.add_governance_member(
            village_id="hejij",
            user_id="council_123",
            role="council_member",
        )
        assert council is not None

        # 3. بررسی موجودی صندوق
        balance = await landscape_service.get_fund_balance("hejij")
        assert balance is not None
        assert balance["village_id"] == "hejij"

        # 4. دریافت آمار روستا
        stats = await landscape_service.get_village_stats("hejij")
        assert stats is not None
        assert stats["name"] == "روستای هجیج"
        assert stats["governance_members_count"] == 2
