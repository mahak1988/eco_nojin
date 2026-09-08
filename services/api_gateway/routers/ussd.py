"""USSD/SMS Gateway — feature-phone inclusive access layer.

Endpoints
---------
- ``POST /api/v1/ussd/ussd`` — USSD session handler
- ``POST /api/v1/ussd/sms`` — SMS command handler
- ``GET /api/v1/ussd/health`` — health/inclusive-access report
- ``GET /api/v1/ussd/menu/preview`` — preview localized USSD menu
- ``GET /api/v1/ussd/status`` — gateway status (requires telecom integration)
"""

from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.business_modules.ussd.engine import (
    Language,
    UssdRequest,
    UssdResponse,
    get_ussd_handler,
)
from services.business_modules.ussd.sms_parser import SmsParser, get_sms_parser

router = APIRouter(prefix="/api/v1/ussd", tags=["ussd"])


class UssdIn(BaseModel):
    session_id: str
    service_code: str
    phone_number: str
    text: str = ""
    language: Literal["en", "fa", "ar"] = "en"


class SmsIn(BaseModel):
    phone_number: str
    message: str


class UssdOut(BaseModel):
    text: str
    end_session: bool


class SmsOut(BaseModel):
    response: str
    char_count: int


@router.post("/ussd", response_model=UssdOut)
async def ussd_endpoint(payload: UssdIn) -> UssdOut:
    """Process a USSD session step."""
    handler = get_ussd_handler()
    req = UssdRequest(
        session_id=payload.session_id,
        service_code=payload.service_code,
        phone_number=payload.phone_number,
        text=payload.text,
        language=Language(payload.language),
    )
    resp: UssdResponse = handler.handle(req)
    return UssdOut(text=resp.text, end_session=resp.end_session)


@router.post("/sms", response_model=SmsOut)
async def sms_endpoint(payload: SmsIn) -> SmsOut:
    """Process an SMS command."""
    parser: SmsParser = get_sms_parser()
    text = parser.process(payload.phone_number, payload.message)
    return SmsOut(response=text, char_count=len(text))


@router.get("/health")
async def ussd_health() -> dict:
    """Health check for USSD/SMS module."""
    return {
        "status": "operational",
        "ussd_code": "*384*73#",
        "languages": ["en", "fa", "ar"],
        "inclusive_access": {
            "ussd_feature_phone": True,
            "sms_commands": True,
        },
    }


@router.get("/menu/preview")
async def menu_preview(language: Literal["en", "fa", "ar"] = Query("en")) -> dict:
    """Return the localized main menu text."""
    handler = get_ussd_handler()
    req = UssdRequest(
        session_id="preview",
        service_code="*384*73#",
        phone_number="+000000000",
        text="",
        language=Language(language),
    )
    resp: UssdResponse = handler.handle(req)
    return {"language": language, "menu_text": resp.text}


@router.get("/status")
async def ussd_status() -> dict:
    """Honest USSD/SMS status (no fake delivery)."""
    return {
        "status": "requires_gateway",
        "note": "اتصال USSD/SMS پس از فراهم‌شدن درگاه مخابراتی (GSM/modem یا سرویس ابری) فعال می‌شود؛ تا آن زمان هشدارها فقط در داشبورد نمایش داده می‌شوند.",
    }
