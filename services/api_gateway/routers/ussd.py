"""API endpoints for USSD/SMS Gateway.

Supports multiple telco integrations:
- Africa's Talking (African telcos)
- Twilio (global)
- Kavehnegar (Iran)
- Generic webhook format
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, ConfigDict

from engine.hydroma.ussd.engine import GatewayType, Language, UssdRequest, get_ussd_handler
from engine.hydroma.ussd.sms_parser import get_sms_parser

router = APIRouter(prefix="/api/v1/ussd", tags=["USSD/SMS Gateway"])


@router.get("/health", tags=["ussd"])
async def ussd_health():
    """USSD module health check."""
    return {
        "status": "operational",
        "module": "ussd",
        "version": "1.0.0",
        "ussd_code": "*384*73#",
        "sms_commands": True,
        "menu_text": "Welcome to Eco Nojin USSD",
        "inclusive_access": {
            "ussd_feature_phone": True,
            "sms_enabled": True,
            "multilanguage": True,
            "offline_mode": True,
        },
    }



# ============================================================================
# Pydantic Models
# ============================================================================


class UssdApiRequest(BaseModel):
    """Generic USSD request."""

    session_id: str = Field(..., description="Unique session identifier")
    service_code: str = Field(..., description="USSD service code (e.g. *384*73#)")
    phone_number: str = Field(..., description="User's phone number")
    text: str = Field("", description="USSD input so far")
    language: str = Field("en", description="Language code: en, fa, ar")


class SmsApiRequest(BaseModel):
    """Generic SMS request."""

    phone_number: str = Field(..., description="Sender's phone number")
    message: str = Field(..., description="SMS message text")
    language: str | None = Field(None, description="Optional language override")


class AfricasTalkingUssdRequest(BaseModel):
    """Africa's Talking USSD webhook format."""

    sessionId: str
    serviceCode: str
    phoneNumber: str
    text: str


class SmsWebhookRequest(BaseModel):
    """Generic SMS webhook request."""

    from_number: str = Field(..., alias="from")
    to_number: str = Field(..., alias="to")
    message: str
    timestamp: str | None = None

    class Config:
        populate_by_name = True


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/ussd")
def handle_ussd(payload: UssdApiRequest):
    """Process USSD request and return response."""
    try:
        lang = Language(payload.language)
    except ValueError:
        lang = Language.EN

    request = UssdRequest(
        session_id=payload.session_id,
        service_code=payload.service_code,
        phone_number=payload.phone_number,
        text=payload.text,
        gateway=GatewayType.USSD,
        language=lang,
    )

    handler = get_ussd_handler()
    response = handler.handle(request)

    return {
        "text": response.text,
        "end_session": response.end_session,
        "africastalking_format": response.to_africastalking_format(),
    }


@router.post("/ussd/africastalking")
async def handle_africastalking_ussd(request: Request):
    """Handle Africa's Talking USSD webhook (form-encoded).

    Africa's Talking expects plain text response starting with CON or END.
    """
    form = await request.form()
    session_id = form.get("sessionId", "")
    service_code = form.get("serviceCode", "")
    phone_number = form.get("phoneNumber", "")
    text = form.get("text", "")

    # Detect language from phone number prefix (simplified)
    lang = Language.EN  # Default
    if phone_number.startswith("+98"):
        lang = Language.FA
    elif phone_number.startswith("+966") or phone_number.startswith("+971"):
        lang = Language.AR

    ussd_request = UssdRequest(
        session_id=session_id,
        service_code=service_code,
        phone_number=phone_number,
        text=text,
        gateway=GatewayType.USSD,
        language=lang,
    )

    handler = get_ussd_handler()
    response = handler.handle(ussd_request)

    # Africa's Talking requires plain text response
    return PlainTextResponse(content=response.to_africastalking_format())


@router.post("/sms")
def handle_sms(payload: SmsApiRequest):
    """Process SMS command and return response."""
    try:
        lang = Language(payload.language) if payload.language else None
    except ValueError:
        lang = None

    parser = get_sms_parser()

    if lang:
        parser.set_user_language(payload.phone_number, lang)

    response_text = parser.process(payload.phone_number, payload.message)

    return {
        "phone_number": payload.phone_number,
        "response": response_text,
        "char_count": len(response_text),
        "sms_segments": (len(response_text) + 159) // 160,  # 160 chars per SMS
    }


@router.post("/sms/webhook")
async def handle_sms_webhook(request: Request):
    """Handle generic SMS webhook (form-encoded)."""
    form = await request.form()
    from_number = form.get("from", "") or form.get("from_number", "")
    message = form.get("message", "") or form.get("body", "")

    if not from_number or not message:
        raise HTTPException(status_code=400, detail="Missing from or message")

    parser = get_sms_parser()
    response_text = parser.process(from_number, message)

    # In production, would call SMS provider API to send response
    # For research mode, we just log it
    return {
        "to": from_number,
        "message": response_text,
        "status": "operational",
    }


@router.get("/health")
def ussd_health():
    """Check USSD/SMS gateway status."""
    return {
        "inclusive_access": True,
        "languages": ["fa", "en", "ar"],
        "status": "operational",
        "gateway_type": "USSD/SMS",
        "supported_languages": ["en", "fa", "ar"],
        "supported_providers": [
            "africastalking",
            "twilio",
            "kavehnegar",
            "generic",
        ],
        "ussd_code": "*384*73#",
        "sms_commands": [
            "SOIL <lat> <lon>",
            "CROP <region>",
            "PRICE <product>",
            "WEATHER <city>",
            "ASK <question>",
            "HELP",
            "LANG en|fa|ar",
        ],
    }


@router.get("/menu/preview")
def preview_menu(language: str = "en"):
    """Preview USSD menu in given language (for testing)."""
    try:
        lang = Language(language)
    except ValueError:
        lang = Language.EN

    handler = get_ussd_handler()
    request = UssdRequest(
        session_id="preview",
        service_code="*384*73#",
        phone_number="+0000000000",
        text="",
        gateway=GatewayType.USSD,
        language=lang,
    )

    response = handler.handle(request)

    return {
        "language": language,
        "menu_text": response.text,
    }
