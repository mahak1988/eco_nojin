"""Voice AI / IVR module for Eco Nojin — Cloud-Native.

Provides voice-based access for low-literacy users via:
- IVR menu system
- Speech-to-Text (STT) — OpenAI Whisper API
- Text-to-Speech (TTS) — Cloud providers (removed local Coqui)
- Integration with AI Assistant (RAG)
- Twilio telephony integration
"""

from .ivr_engine import IVREngine, IVRResponse, IVRSession, IVRState, get_ivr_engine
from .stt_provider import STTProvider, STTResult, get_stt_provider
from .tts_provider import TTSProvider, TTSResult, VoiceLanguage, get_tts_provider
from .twilio_ivr import TwilioIVRIntegration, get_twilio_ivr
from .voice_assistant import VoiceAssistant, VoiceResponse, get_voice_assistant
from .whisper_stt import WhisperSTTProvider, get_whisper_stt_provider

__all__ = [
    # IVR
    "IVREngine",
    "IVRResponse",
    "IVRSession",
    "IVRState",
    # STT
    "STTProvider",
    "STTResult",
    # TTS
    "TTSProvider",
    "TTSResult",
    # Twilio
    "TwilioIVRIntegration",
    # Voice Assistant
    "VoiceAssistant",
    "VoiceLanguage",
    "VoiceResponse",
    "WhisperSTTProvider",
    "get_ivr_engine",
    "get_stt_provider",
    "get_tts_provider",
    "get_twilio_ivr",
    "get_voice_assistant",
    "get_whisper_stt_provider",
]