"""API Router for marketplace"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/marketplace", tags=["Marketplace"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "marketplace"}


@router.get("/info")
async def service_info():
    return {"service": "marketplace", "version": "1.0.0", "status": "ready"}
