"""Ecotourism (بوم‌گردی) — honest module status.

The tourism domain service (services/tourism) is implemented (guides, tours,
bookings, token payments) but its database tables are not provisioned in
Supabase yet. This endpoint reports requires_setup honestly and lists the
capabilities so the frontend never pretends bookings exist.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/tourism", tags=["tourism"])


@router.get("/status")
async def tourism_status():
    """Honest ecotourism module status."""
    return {
        "status": "requires_setup",
        "module": "ecotourism (بوم‌گردی)",
        "capabilities": [
            "ثبت راهنمای محلی و تأیید",
            "ایجاد تور طبیعت‌گردی",
            "رزرو و پرداخت با توکن (ECO)",
            "پایش آمار تور",
        ],
        "note": "سرویس بک‌اند آماده است؛ جداول دیتابیس هنوز در Supabase فراهم نشده‌اند — با migration بعدی فعال می‌شود.",
    }
