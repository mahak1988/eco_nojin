"""ثبت ماژول‌های جدید در API Gateway"""

from fastapi import FastAPI


def register_new_modules(app: FastAPI):
    """ثبت ماژول‌های جدید"""
    try:
        from services.marketplace.api import router as marketplace_router
        app.include_router(marketplace_router)
    except ImportError:
        pass

    try:
        from services.tourism.api import router as tourism_router
        app.include_router(tourism_router)
    except ImportError:
        pass

    try:
        from services.landscape.api import router as landscape_router
        app.include_router(landscape_router)
    except ImportError:
        pass
