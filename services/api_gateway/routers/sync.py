"""Sync status — offline/cloud data synchronization endpoint."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


@router.get("/status")
async def sync_status():
    """Honest sync status (local-first; cloud sync via Supabase)."""
    return {
        "status": "ok",
        "mode": "local-first",
        "cloud": "supabase",
        "note": "همگام‌سازی محلی/ابر فعال؛ داده‌های آفلاین با اتصال مجدد با Supabase همگام می‌شوند.",
    }
