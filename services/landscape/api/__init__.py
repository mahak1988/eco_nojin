"""API Router for landscape"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/landscape", tags=["Landscape"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "landscape"}


@router.get("/info")
async def service_info():
    return {"service": "landscape", "version": "1.0.0", "status": "ready"}
