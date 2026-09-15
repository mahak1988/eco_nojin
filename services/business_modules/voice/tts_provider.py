"""Text-to-Speech provider interface with factory pattern.

Supports multiple backends via ``TTS_PROVIDER`` env variable:
- ``mock`` (default) — simulated synthesis
- ``coqui`` — Coqui TTS (see coqui_tts.py)
- ``azure`` — Azure Cognitive TTS (stub)
- ``polly`` — Amazon Polly (stub)

Usage:
    from services.business_modules.voice.tts_provider import get_tts_provider
    provider = get_tts_provider()
    result = provider.synthesize("Hello", VoiceLanguage.EN)
"""

import logging
import os

from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceLanguage(Enum):
    """Supported voice languages."""
    EN = "en"
    FA = "fa"
    AR = "ar"


@dataclass
class TTSResult:
    """Result from TTS synthesis."""
    text: str
    language: VoiceLanguage
    audio_data: bytes | None = None
    duration_seconds: float = 0.0
    voice_id: str = "default"


class TTSProvider:
    """Base TTS provider interface."""

    @property
    def is_real_provider(self) -> bool:
        return False

    def get_model_info(self) -> dict:
        return {"provider": "mock", "model": "mock", "mode": "base"}

    def synthesize(self, text: str, language: VoiceLanguage = VoiceLanguage.EN) -> TTSResult:
        raise NotImplementedError

    def get_available_voices(self, language: VoiceLanguage) -> list:
        raise NotImplementedError


# Lazy singletons
_tts_provider: TTSProvider | None = None


def get_tts_provider() -> TTSProvider:
    """Get TTS provider based on TTS_PROVIDER env variable."""
    global _tts_provider
    if _tts_provider is not None:
        return _tts_provider

    provider_name = os.environ.get("TTS_PROVIDER", "mock").lower()

    if provider_name == "coqui":
        try:
            from .coqui_tts import CoquiTTSProvider
            _tts_provider = CoquiTTSProvider()
            logger.info("TTS provider: Coqui")
            return _tts_provider
        except Exception as exc:
            logger.warning("Coqui init failed, falling back to mock: %s", exc)

    if provider_name == "azure":
        logger.warning("Azure TTS not yet implemented, using mock")

    if provider_name == "polly":
        logger.warning("Polly TTS not yet implemented, using mock")

    # Mock default
    _tts_provider = _MockTTS()
    logger.info("TTS provider: mock (set %TTS_PROVIDER=coqui for real synthesis)")
    return _tts_provider


class _MockTTS(TTSProvider):
    """Mock TTS provider (default)."""

    def synthesize(self, text: str, language: VoiceLanguage = VoiceLanguage.EN) -> TTSResult:
        estimated_duration = len(text) / 15.0
        return TTSResult(
            text=text,
            language=language,
            audio_data=None,
            duration_seconds=estimated_duration,
            voice_id=f"voice_{language.value}_default",
        )

    def get_available_voices(self, language: VoiceLanguage) -> list:
        return [
            {"id": f"voice_{language.value}_male", "name": f"Male ({language.value})", "engine": "mock"},
            {"id": f"voice_{language.value}_female", "name": f"Female ({language.value})", "engine": "mock"},
        ]
