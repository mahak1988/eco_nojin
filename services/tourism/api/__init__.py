"""API Router for tourism"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/tourism", tags=["Tourism"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tourism"}


@router.get("/info")
async def service_info():
    return {"service": "tourism", "version": "1.0.0", "status": "ready"}
