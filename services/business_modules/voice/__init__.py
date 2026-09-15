"""Voice AI / IVR module for Eco Nojin.

Provides voice-based access for low-literacy users via:
- IVR menu system
- Speech-to-Text (STT)
- Text-to-Speech (TTS)
- Integration with AI Assistant (RAG)
- Twilio telephony integration
"""

from .stt_provider import STTProvider, STTResult, get_stt_provider
from .tts_provider import TTSProvider, TTSResult, VoiceLanguage, get_tts_provider
from .ivr_engine import IVREngine, IVRSession, IVRState, IVRResponse, get_ivr_engine
from .voice_assistant import VoiceAssistant, VoiceResponse, get_voice_assistant
from .whisper_stt import WhisperSTTProvider, get_whisper_stt_provider
from .coqui_tts import CoquiTTSProvider, get_coqui_tts_provider
from .twilio_ivr import TwilioIVRIntegration, get_twilio_ivr

__all__ = [
    # STT
    "STTProvider",
    "STTResult",
    "get_stt_provider",
    "WhisperSTTProvider",
    "get_whisper_stt_provider",
    # TTS
    "TTSProvider",
    "TTSResult",
    "VoiceLanguage",
    "get_tts_provider",
    "CoquiTTSProvider",
    "get_coqui_tts_provider",
    # IVR
    "IVREngine",
    "IVRSession",
    "IVRState",
    "IVRResponse",
    "get_ivr_engine",
    # Voice Assistant
    "VoiceAssistant",
    "VoiceResponse",
    "get_voice_assistant",
    # Twilio
    "TwilioIVRIntegration",
    "get_twilio_ivr",
]