"""Voice/IVR module — inclusive access for low-literacy users.

Endpoints
---------
- ``POST /api/v1/voice/ivr/start`` — start IVR session
- ``POST /api/v1/voice/ivr/dtmf`` — handle DTMF digit
- ``GET /api/v1/voice/ivr/menu/{language}`` — preview localized IVR menu
- ``POST /api/v1/voice/ivr/call`` — initiate call via Twilio
- ``POST /api/v1/voice/ivr/sms`` — send SMS via Twilio
- ``POST /api/v1/voice/tts`` — text-to-speech
- ``POST /api/v1/voice/stt`` — speech-to-text
- ``POST /api/v1/voice/ask`` — ask expert via voice
- ``GET /api/v1/voice/health`` — module health
- ``GET /api/v1/voice/languages`` — supported languages
- ``GET /api/v1/voice/status`` — gateway status (requires telephony provider)
- ``GET /api/v1/voice/providers`` — available providers and active configuration
- ``GET /api/v1/voice/diagnostics`` — provider status (mock/real, config, health)
"""

import base64
import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from services.business_modules.voice.ivr_engine import (
    IVRSession,
    IVRState,
    get_ivr_engine,
)
from services.business_modules.voice.stt_provider import get_stt_provider
from services.business_modules.voice.tts_provider import VoiceLanguage, get_tts_provider
from services.business_modules.voice.twilio_ivr import get_twilio_ivr

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


class IVRStartIn(BaseModel):
    session_id: str
    phone_number: str
    language: Literal["en", "fa", "ar"] = "en"


class IVRStartOut(BaseModel):
    session_id: str
    prompt_text: str
    state: str
    end_call: bool = False


class IVRDTMFIn(BaseModel):
    session_id: str
    digit: str


class IVRDTMFOut(BaseModel):
    state: str
    prompt_text: str
    end_call: bool


class TTSIn(BaseModel):
    text: str
    language: Literal["en", "fa", "ar"] = "en"


class TTSOut(BaseModel):
    text: str
    language: str
    duration_seconds: float


class STTIn(BaseModel):
    audio_base64: str
    language: Literal["en", "fa", "ar"] = "en"


class STTOut(BaseModel):
    text: str
    confidence: float
    alternatives: list[dict]


class AskIn(BaseModel):
    question: str
    language: Literal["en", "fa", "ar"] = "en"


class AskOut(BaseModel):
    answer: str


class IVRCallIn(BaseModel):
    phone_number: str
    twiml: str | None = None
    menu_language: Literal["en", "fa", "ar"] = "en"


class IVRCallOut(BaseModel):
    call_sid: str
    status: str


class IVRSMSIn(BaseModel):
    to: str
    body: str


class IVRSMSOut(BaseModel):
    message_sid: str
    status: str


class ProvidersOut(BaseModel):
    stt: dict
    tts: dict
    ivr: dict


class DiagnosticsOut(BaseModel):
    stt: dict
    tts: dict
    ivr: dict
    environment: dict


@router.post("/ivr/start", response_model=IVRStartOut)
async def ivr_start(payload: IVRStartIn) -> IVRStartOut:
    """Start a new IVR session."""
    engine = get_ivr_engine()
    session: IVRSession = engine.start_session(
        session_id=payload.session_id,
        phone_number=payload.phone_number,
        language=VoiceLanguage(payload.language),
    )
    resp = engine.get_prompt(session)
    return IVRStartOut(
        session_id=session.session_id,
        prompt_text=resp.prompt_text,
        state=resp.state.value,
        end_call=resp.end_call,
    )


@router.post("/ivr/dtmf", response_model=IVRDTMFOut)
async def ivr_dtmf(payload: IVRDTMFIn) -> IVRDTMFOut:
    """Handle DTMF digit input."""
    engine = get_ivr_engine()
    session = IVRSession(
        session_id=payload.session_id,
        phone_number="",
        language=VoiceLanguage.EN,
        state=IVRState.MAIN_MENU,
    )
    resp = engine.handle_dtmf(session, payload.digit)
    return IVRDTMFOut(
        state=resp.state.value,
        prompt_text=resp.prompt_text,
        end_call=resp.end_call,
    )


@router.get("/ivr/menu/{language}")
async def ivr_menu_preview(language: Literal["en", "fa", "ar"]) -> dict:
    """Preview localized IVR menu prompt."""
    engine = get_ivr_engine()
    session: IVRSession = engine.start_session(
        session_id="preview",
        phone_number="+000000000",
        language=VoiceLanguage(language),
    )
    resp = engine.get_prompt(session)
    return {"language": language, "menu_text": resp.prompt_text}


@router.post("/ivr/call", response_model=IVRCallOut)
async def ivr_call(payload: IVRCallIn) -> IVRCallOut:
    """Initiate an outbound call via Twilio with IVR menu.

    If twiml is not provided, generates a default IVR menu TwiML.
    """
    twilio = get_twilio_ivr()

    if payload.twiml:
        twiml = payload.twiml
    else:
        # Generate default IVR menu TwiML
        engine = get_ivr_engine()
        session = engine.start_session(
            session_id="twilio_call",
            phone_number=payload.phone_number,
            language=VoiceLanguage(payload.menu_language),
        )
        resp = engine.get_prompt(session)
        twiml = twilio.generate_twiml_ivr(
            menu_text=resp.prompt_text,
            gather_action=f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/api/v1/voice/ivr/twilio/dtmf",
            language=payload.menu_language,
        )

    call_sid = twilio.make_call(payload.phone_number, twiml)

    return IVRCallOut(
        call_sid=call_sid,
        status="initiated" if not call_sid.startswith("mock") else "mock",
    )


@router.post("/ivr/sms", response_model=IVRSMSOut)
async def ivr_sms(payload: IVRSMSIn) -> IVRSMSOut:
    """Send SMS via Twilio."""
    twilio = get_twilio_ivr()

    message_sid = twilio.send_sms(payload.to, payload.body)

    return IVRSMSOut(
        message_sid=message_sid,
        status="sent" if not message_sid.startswith("mock") else "mock",
    )


@router.post("/tts", response_model=TTSOut)
async def text_to_speech(payload: TTSIn) -> TTSOut:
    """Convert text to speech metadata."""
    tts = get_tts_provider()
    result = tts.synthesize(payload.text, VoiceLanguage(payload.language))
    return TTSOut(
        text=result.text,
        language=result.language.value,
        duration_seconds=result.duration_seconds,
    )


@router.post("/stt", response_model=STTOut)
async def speech_to_text(payload: STTIn) -> STTOut:
    """Convert speech to text."""
    stt = get_stt_provider()
    audio = base64.b64decode(payload.audio_base64)
    result = stt.transcribe(audio, VoiceLanguage(payload.language))
    return STTOut(
        text=result.text,
        confidence=result.confidence,
        alternatives=result.alternatives,
    )


@router.post("/ask", response_model=AskOut)
async def voice_ask(payload: AskIn) -> AskOut:
    """Ask expert question via voice interface."""
    return AskOut(answer="Please consult local extension officer.")


@router.get("/health")
async def voice_health() -> dict:
    """Health check for voice/IVR module."""
    stt = get_stt_provider()
    tts = get_tts_provider()
    twilio = get_twilio_ivr()

    return {
        "status": "operational",
        "mode": "mock"
        if not (stt.is_real_provider or tts.is_real_provider or twilio.is_real_provider)
        else "mixed",
        "features": {
            "ivr_menu": True,
            "tts": True,
            "stt": True,
            "dtmf": True,
            "twilio_calls": twilio.is_real_provider,
            "twilio_sms": twilio.is_real_provider,
        },
    }


@router.get("/languages")
async def voice_languages() -> dict:
    """Return supported voice languages."""
    tts = get_tts_provider()
    voices = tts.get_available_voices(VoiceLanguage.EN)  # Get sample voices

    return {
        "languages": [
            {
                "code": "en",
                "name": "English",
                "voices": [v["id"] for v in tts.get_available_voices(VoiceLanguage.EN)],
            },
            {
                "code": "fa",
                "name": "Persian",
                "voices": [v["id"] for v in tts.get_available_voices(VoiceLanguage.FA)],
            },
            {
                "code": "ar",
                "name": "Arabic",
                "voices": [v["id"] for v in tts.get_available_voices(VoiceLanguage.AR)],
            },
        ]
    }


@router.get("/status")
async def voice_status() -> dict:
    """Honest voice/IVR status."""
    return {
        "status": "requires_gateway",
        "note": "دستیار صوتی (IVR) پس از اتصال خط تلفن/ترانک SIP فعال می‌شود؛ موتورهای STT/TTS داخلی آماده‌اند.",
    }


@router.get("/providers", response_model=ProvidersOut)
async def voice_providers() -> ProvidersOut:
    """Return available providers and active configuration."""
    stt = get_stt_provider()
    tts = get_tts_provider()
    twilio = get_twilio_ivr()

    return ProvidersOut(
        stt={
            "active": stt.get_model_info(),
            "available": ["mock", "whisper", "google", "vosk"],
            "env_var": "STT_PROVIDER",
            "current": os.getenv("STT_PROVIDER", "mock"),
        },
        tts={
            "active": tts.get_model_info(),
            "available": ["mock", "coqui", "azure", "polly"],
            "env_var": "TTS_PROVIDER",
            "current": os.getenv("TTS_PROVIDER", "mock"),
        },
        ivr={
            "active": twilio.get_config_info(),
            "available": ["mock", "twilio"],
            "env_vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
        },
    )


@router.get("/diagnostics", response_model=DiagnosticsOut)
async def voice_diagnostics() -> DiagnosticsOut:
    """Return provider status (mock/real, config, health)."""
    stt = get_stt_provider()
    tts = get_tts_provider()
    twilio = get_twilio_ivr()

    # Determine overall health
    stt_healthy = stt.is_real_provider or os.getenv("STT_PROVIDER", "mock") == "mock"
    tts_healthy = tts.is_real_provider or os.getenv("TTS_PROVIDER", "mock") == "mock"
    twilio_healthy = twilio.is_real_provider or not twilio.config.is_configured()

    return DiagnosticsOut(
        stt={
            "provider": stt.get_model_info(),
            "is_real": stt.is_real_provider,
            "healthy": stt_healthy,
            "config": {
                "model_size": os.getenv("WHISPER_MODEL_SIZE", "base"),
            },
        },
        tts={
            "provider": tts.get_model_info(),
            "is_real": tts.is_real_provider,
            "healthy": tts_healthy,
            "config": {
                "model_name": os.getenv("COQUI_MODEL_NAME", "auto"),
            },
        },
        ivr={
            "provider": twilio.get_config_info(),
            "is_real": twilio.is_real_provider,
            "healthy": twilio_healthy,
            "config": {
                "phone_number": twilio.config.phone_number[:6] + "***"
                if twilio.config.phone_number
                else None,
            },
        },
        environment={
            "STT_PROVIDER": os.getenv("STT_PROVIDER", "mock"),
            "TTS_PROVIDER": os.getenv("TTS_PROVIDER", "mock"),
            "WHISPER_MODEL_SIZE": os.getenv("WHISPER_MODEL_SIZE", "base"),
            "COQUI_MODEL_NAME": os.getenv("COQUI_MODEL_NAME", "auto"),
            "TWILIO_CONFIGURED": twilio.config.is_configured(),
        },
    )


@router.post("/ivr/twilio/dtmf")
async def twilio_dtmf_webhook(payload: dict) -> dict:
    """Twilio webhook for DTMF input during IVR call.

    Expected to be called by Twilio when user presses a key.
    Returns TwiML for next step.
    """
    digits = payload.get("Digits", "")
    call_sid = payload.get("CallSid", "")

    twilio = get_twilio_ivr()
    engine = get_ivr_engine()

    # This is a simplified handler - in production you'd need session persistence
    session = IVRSession(
        session_id=call_sid,
        phone_number=payload.get("From", ""),
        language=VoiceLanguage.EN,
        state=IVRState.MAIN_MENU,
    )

    resp = engine.handle_dtmf(session, digits)
    twiml = twilio.generate_twiml_say(resp.prompt_text, language=session.language.value)

    if resp.end_call:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en">{resp.prompt_text}</Say>
    <Hangup/>
</Response>"""

    from fastapi.responses import Response

    return Response(content=twiml, media_type="application/xml")
