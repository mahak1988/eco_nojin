"""Speech-to-Text provider interface with factory pattern.

Supports multiple backends via ``STT_PROVIDER`` env variable:
- ``mock`` (default) — simulated transcription
- ``whisper`` — OpenAI Whisper (see whisper_stt.py)
- ``google`` — Google Cloud STT (stub)
- ``vosk`` — Vosk offline (stub)

Usage:
    from services.business_modules.voice.stt_provider import get_stt_provider
    provider = get_stt_provider()
    result = provider.transcribe(audio_bytes, VoiceLanguage.EN)
"""

import logging
import os

from dataclasses import dataclass

from .tts_provider import VoiceLanguage

logger = logging.getLogger(__name__)


@dataclass
class STTResult:
    """Result from STT transcription."""
    text: str
    language: VoiceLanguage
    confidence: float = 0.0
    duration_seconds: float = 0.0
    alternatives: list | None = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class STTProvider:
    """Base STT provider interface."""

    @property
    def is_real_provider(self) -> bool:
        return False

    def get_model_info(self) -> dict:
        return {"provider": "mock", "model": "mock", "mode": "base"}

    def transcribe(self, audio_data: bytes, language: VoiceLanguage = VoiceLanguage.EN) -> STTResult:
        raise NotImplementedError

    def detect_language(self, audio_data: bytes) -> VoiceLanguage:
        raise NotImplementedError


# Lazy singletons
_stt_provider: STTProvider | None = None


def get_stt_provider() -> STTProvider:
    """Get STT provider based on STT_PROVIDER env variable."""
    global _stt_provider
    if _stt_provider is not None:
        return _stt_provider

    provider_name = os.environ.get("STT_PROVIDER", "mock").lower()

    if provider_name == "whisper":
        try:
            from services.business_modules.voice.whisper_stt import WhisperSTTProvider
            _stt_provider = WhisperSTTProvider()
            logger.info("STT provider: Whisper")
            return _stt_provider
        except Exception as exc:
            logger.warning("Whisper init failed, falling back to mock: %s", exc)

    if provider_name == "google":
        logger.warning("Google STT not yet implemented, using mock")

    if provider_name == "vosk":
        logger.warning("Vosk STT not yet implemented, using mock")

    from services.business_modules.voice.stt_provider import STTProvider as _MockSTT
    _stt_provider = _MockSTT()
    logger.info("STT provider: mock (set %STT_PROVIDER=whisper for real transcription)")
    return _stt_provider
