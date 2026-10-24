"""Ecotourism (بوم‌گردی) — capability/status surface.

The domain is implemented and live. ``services.tourism.service`` carries the
whole lifecycle — guide registration and verification, tour creation and
landscape-manager approval, booking with ecological-capacity enforcement,
payment confirmation and regenerative completion, and the 800/200/200 bps fee
split — and ``services.tourism.api.router`` serves it over ``/api/v1/tourism``
(guides / tours / bookings), mounted beside this route by
``services.api_gateway.main.py``. This router therefore lists capabilities that
now have a live HTTP surface, not ones that are still pending.

The tables are not "awaiting provisioning" either: ``services.tourism.models``
declares ``TourismGuide``/``TourismTour``/``TourismBooking`` on the shared
``database.base.Base``, so ``services.api_gateway.main.init_db``
(``Base.metadata.create_all``) creates them, and the alembic delta
``20261010_180000_waves_2_6_schema_delta`` creates the same tables for a
database built by ``alembic upgrade`` alone.

P1 (2026-10-11, KN-01): the two pre-mount literals this route used to return —
``status: "requires_setup"`` and the "tables not provisioned in Supabase"
note — were rewritten to describe the live surface, and a
``not_yet_available`` list was added so a reader cannot mistake a roadmap
item for a live feature (eco.md P-01/P-15). The route now claims exactly
what ``services.tourism.api.router`` serves; ``test_tourism_status_honesty``
pins that claim to the mounted routes, so deleting the lifecycle mount fails
the test instead of silently falsifying this payload.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/tourism", tags=["tourism"])


@router.get("/status")
async def tourism_status():
    """Honest capability/status payload for the ecotourism surface.

    ``status`` is ``live`` because the guide/tour/booking lifecycle is served
    over this same prefix by ``services.tourism.api.router``. ``endpoints``
    names that live surface, and ``not_yet_available`` names what eco.md's
    Phase 8 still lacks (event registry, refund/complaint endpoints, the
    9-entity model question, GSTC as design reference only) — the payload is
    only allowed to advertise what is mounted.
    """
    return {
        "status": "live",
        "module": "ecotourism (بوم‌گردی)",
        "capabilities": [
            "ثبت راهنمای محلی و تأیید",
            "ایجاد تور طبیعت‌گردی و تأیید مدیر منظر",
            "رزرو با کنترل ظرفیت محیط‌زیستی",
            "تأیید پرداخت و تکمیل تور با تقسیم کارمزد ۸۰۰/۲۰۰/۲۰۰ bps",
        ],
        "endpoints": {
            "guides": "/api/v1/tourism/guides",
            "tours": "/api/v1/tourism/tours",
            "bookings": "/api/v1/tourism/bookings",
        },
        "tables": (
            "TourismGuide/TourismTour/TourismBooking are declared on "
            "database.base.Base and created by init_db (create_all) and "
            "alembic 20261010_180000_waves_2_6_schema_delta"
        ),
        "not_yet_available": [
            "رجیستری رویدادها (جشنواره/نمایشگاه/مسابقه) — فاز ۸",
            "مسیرهای بازپرداخت و شکایت تور — فاز ۸",
            "مدل ۹-موجودی‌ای eco.md "
            "(پیشنهاد/مجری/تأیید/اجرا/شرکت‌کننده/حادثه/بازپرداخت) — تصمیم باز فاز ۸",
            "معیارهای GSTC — تنها مرجع طراحی، بدون ادعای گواهی",
        ],
        "note": (
            "چرخهٔ زندگی تور (راهنما، تور، رزرو، تأیید پرداخت) روی "
            "/api/v1/tourism فعال است؛ موارد فهرست‌شده در not_yet_available "
            "هنوز ارائه نشده‌اند."
        ),
    }
