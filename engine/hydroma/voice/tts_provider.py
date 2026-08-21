"""Text-to-Speech provider interface.

Mock implementation for research mode.
Ready for integration with:
- Google Cloud Text-to-Speech
- Azure Cognitive Services
- Amazon Polly
- Coqui TTS (open source)
"""

from dataclasses import dataclass
from enum import Enum


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
    """Mock TTS provider for research mode.

    In production, replace with real provider:
    - GoogleTTSProvider
    - AzureTTSProvider
    - CoquiTTSProvider
    """

    def synthesize(self, text: str, language: VoiceLanguage = VoiceLanguage.EN) -> TTSResult:
        """Convert text to speech.

        Mock implementation returns metadata without actual audio.
        Real implementation would call external API or local model.
        """
        # Mock: estimate duration based on text length
        estimated_duration = len(text) / 15.0  # ~15 chars per second

        return TTSResult(
            text=text,
            language=language,
            audio_data=None,  # Would be actual audio bytes in production
            duration_seconds=estimated_duration,
            voice_id=f"voice_{language.value}_default",
        )

    def get_available_voices(self, language: VoiceLanguage) -> list:
        """Get available voices for a language."""
        return [
            {"id": f"voice_{language.value}_male", "name": f"Male ({language.value})"},
            {"id": f"voice_{language.value}_female", "name": f"Female ({language.value})"},
        ]


# Singleton
_tts_provider: TTSProvider | None = None


def get_tts_provider() -> TTSProvider:
    """Get singleton TTS provider."""
    global _tts_provider
    if _tts_provider is None:
        _tts_provider = TTSProvider()
    return _tts_provider
