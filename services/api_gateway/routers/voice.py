"""Voice/IVR module — inclusive access for low-literacy users.

Endpoints
---------
- ``POST /api/v1/voice/ivr/start`` — start IVR session
- ``POST /api/v1/voice/ivr/dtmf`` — handle DTMF digit
- ``GET /api/v1/voice/ivr/menu/{language}`` — preview localized IVR menu
- ``POST /api/v1/voice/tts`` — text-to-speech
- ``POST /api/v1/voice/stt`` — speech-to-text
- ``POST /api/v1/voice/ask`` — ask expert via voice
- ``GET /api/v1/voice/health`` — module health
- ``GET /api/v1/voice/languages`` — supported languages
- ``GET /api/v1/voice/status`` — gateway status (requires telephony provider)
"""

import base64
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from services.business_modules.voice.ivr_engine import (
    IVRState,
    IVRSession,
    get_ivr_engine,
)
from services.business_modules.voice.stt_provider import get_stt_provider
from services.business_modules.voice.tts_provider import VoiceLanguage, get_tts_provider

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
    return {
        "status": "operational",
        "mode": "mock",
        "features": {
            "ivr_menu": True,
            "tts": True,
            "stt": True,
            "dtmf": True,
        },
    }


@router.get("/languages")
async def voice_languages() -> dict:
    """Return supported voice languages."""
    return {
        "languages": [
            {"code": "en", "name": "English", "voices": ["voice_en_male", "voice_en_female"]},
            {"code": "fa", "name": "Persian", "voices": ["voice_fa_male", "voice_fa_female"]},
            {"code": "ar", "name": "Arabic", "voices": ["voice_ar_male", "voice_ar_female"]},
        ]
    }


@router.get("/status")
async def voice_status() -> dict:
    """Honest voice/IVR status."""
    return {
        "status": "requires_gateway",
        "note": "دستیار صوتی (IVR) پس از اتصال خط تلفن/ترانک SIP فعال می‌شود؛ موتورهای STT/TTS داخلی آماده‌اند.",
    }
