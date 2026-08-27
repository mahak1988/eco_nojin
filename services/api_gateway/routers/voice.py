"""Voice/IVR status — honest. Voice assistant needs a telephony provider
(IVR line / SIP trunk); until then reports requires_gateway.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.get("/status")
async def voice_status():
    """Honest voice/IVR status."""
    return {
        "status": "requires_gateway",
        "note": "دستیار صوتی (IVR) پس از اتصال خط تلفن/ترانک SIP فعال می‌شود؛ موتورهای STT/TTS داخلی آماده‌اند.",
    }
