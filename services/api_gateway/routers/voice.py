"""API endpoints for Voice AI / IVR."""

import base64

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.hydroma.voice.ivr_engine import get_ivr_engine
from engine.hydroma.voice.stt_provider import get_stt_provider
from engine.hydroma.voice.tts_provider import VoiceLanguage, get_tts_provider
from engine.hydroma.voice.voice_assistant import get_voice_assistant

router = APIRouter(prefix="/api/v1/voice", tags=["Voice AI / IVR"])


@router.get("/health", tags=["voice"])
async def voice_health():
    """Voice module health check."""
    return {
        "status": "operational",
        "module": "voice",
        "version": "1.0.0",
        "mode": "mock",
        "features": {
            "ivr_menu": True,
            "tts": True,
            "stt": True,
            "voice_ask": True,
        },
        "voice_ivr": {
            "enabled": True,
            "languages": ["fa", "en", "ar"],
            "tts_provider": "mock",
            "stt_provider": "mock",
        },
    }



# ============================================================================
# Pydantic Models
# ============================================================================


class IVRStartRequest(BaseModel):
    """Request to start IVR session."""

    session_id: str = Field(..., description="Unique session ID")
    phone_number: str = Field(..., description="Caller phone number")
    language: str = Field("en", description="Language: en, fa, ar")


class IVRDTMFRequest(BaseModel):
    """Request with DTMF input."""

    session_id: str
    digit: str = Field(..., pattern="^[0-9*#]$")


class IVRVoiceRequest(BaseModel):
    """Request with voice input."""

    session_id: str
    audio_base64: str = Field(..., description="Base64 encoded audio")
    language: str = Field("en")


class TTSRequest(BaseModel):
    """Text-to-Speech request."""

    text: str = Field(..., min_length=1, max_length=1000)
    language: str = Field("en")


class STTRequest(BaseModel):
    """Speech-to-Text request."""

    audio_base64: str = Field(..., description="Base64 encoded audio")
    language: str = Field("en")


class VoiceQuestionRequest(BaseModel):
    """Voice question request."""

    question: str = Field(..., min_length=3, max_length=500)
    language: str = Field("en")


# ============================================================================
# IVR Endpoints
# ============================================================================


@router.post("/ivr/start")
def ivr_start(payload: IVRStartRequest):
    """Start a new IVR session."""
    engine = get_ivr_engine()

    try:
        lang = VoiceLanguage(payload.language)
    except ValueError:
        lang = VoiceLanguage.EN

    session = engine.start_session(
        session_id=payload.session_id,
        phone_number=payload.phone_number,
        language=lang,
    )

    response = engine.get_prompt(session)

    return {
        "session_id": payload.session_id,
        "prompt_text": response.prompt_text,
        "state": response.state.value,
        "end_call": response.end_call,
        "language": payload.language,
    }


@router.post("/ivr/dtmf")
def ivr_dtmf(payload: IVRDTMFRequest):
    """Handle DTMF input in IVR session."""
    engine = get_ivr_engine()

    # Note: In production, sessions would be stored in Redis/DB
    # For research mode, we create a mock session
    session = engine.start_session(
        session_id=payload.session_id,
        phone_number="+0000000000",
        language=VoiceLanguage.EN,
    )

    response = engine.handle_dtmf(session, payload.digit)

    return {
        "session_id": payload.session_id,
        "prompt_text": response.prompt_text,
        "state": response.state.value,
        "end_call": response.end_call,
    }


@router.get("/ivr/menu/{language}")
def ivr_menu_preview(language: str):
    """Preview IVR menu in given language."""
    try:
        lang = VoiceLanguage(language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid language: {language}")

    engine = get_ivr_engine()
    session = engine.start_session("preview", "+0000000000", lang)
    response = engine.get_prompt(session)

    return {
        "language": language,
        "menu_text": response.prompt_text,
    }


# ============================================================================
# TTS/STT Endpoints
# ============================================================================


@router.post("/tts")
def text_to_speech(payload: TTSRequest):
    """Convert text to speech."""
    try:
        lang = VoiceLanguage(payload.language)
    except ValueError:
        lang = VoiceLanguage.EN

    tts = get_tts_provider()
    result = tts.synthesize(payload.text, lang)

    return {
        "text": result.text,
        "language": payload.language,
        "duration_seconds": result.duration_seconds,
        "voice_id": result.voice_id,
        "audio_base64": None,  # Would be actual audio in production
    }


@router.post("/stt")
def speech_to_text(payload: STTRequest):
    """Convert speech to text."""
    try:
        lang = VoiceLanguage(payload.language)
    except ValueError:
        lang = VoiceLanguage.EN

    stt = get_stt_provider()
    audio_data = base64.b64decode(payload.audio_base64) if payload.audio_base64 else b""
    result = stt.transcribe(audio_data, lang)

    return {
        "text": result.text,
        "language": payload.language,
        "confidence": result.confidence,
        "duration_seconds": result.duration_seconds,
        "alternatives": result.alternatives,
    }


# ============================================================================
# Voice Assistant Endpoints
# ============================================================================


@router.post("/ask")
def voice_ask(payload: VoiceQuestionRequest):
    """Ask a question and get voice response."""
    try:
        lang = VoiceLanguage(payload.language)
    except ValueError:
        lang = VoiceLanguage.EN

    assistant = get_voice_assistant()
    response = assistant.answer_question(payload.question, lang)

    return {
        "question": payload.question,
        "answer": response.text,
        "language": payload.language,
        "confidence": response.confidence,
        "sources": response.sources,
        "audio_base64": None,
    }


# ============================================================================
# Health & Info Endpoints
# ============================================================================


@router.get("/health")
def voice_health():
    """Check voice service status."""
    return {
        "status": "operational",
        "service": "Voice AI / IVR",
        "mode": "mock",  # Research mode uses mock STT/TTS
        "supported_languages": ["en", "fa", "ar"],
        "features": {
            "ivr_menu": True,
            "speech_to_text": True,
            "text_to_speech": True,
            "voice_qa": True,
            "dtmf_input": True,
        },
        "production_ready": False,
        "note": "Mock providers for research. Integrate real STT/TTS for production.",
    }


@router.get("/languages")
def voice_languages():
    """List supported voice languages."""
    return {
        "languages": [
            {"code": "en", "name": "English", "direction": "ltr"},
            {"code": "fa", "name": "Persian", "direction": "rtl"},
            {"code": "ar", "name": "Arabic", "direction": "rtl"},
        ],
    }
