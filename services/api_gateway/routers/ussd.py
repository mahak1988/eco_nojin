"""USSD gateway status — honest. Real SMS/USSD delivery needs a telecom
gateway; until then this module reports requires_gateway instead of faking it.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/ussd", tags=["ussd"])


@router.get("/status")
async def ussd_status():
    """Honest USSD/SMS status (no fake delivery)."""
    return {
        "status": "requires_gateway",
        "note": "اتصال USSD/SMS پس از فراهم‌شدن درگاه مخابراتی (GSM/modem یا سرویس ابری) فعال می‌شود؛ تا آن زمان هشدارها فقط در داشبورد نمایش داده می‌شوند.",
    }
