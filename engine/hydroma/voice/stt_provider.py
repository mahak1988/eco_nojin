"""Speech-to-Text provider interface.

Mock implementation for research mode.
Ready for integration with:
- Google Cloud Speech-to-Text
- Azure Cognitive Services
- OpenAI Whisper (open source)
- Vosk (offline)
"""

from dataclasses import dataclass

from .tts_provider import VoiceLanguage


@dataclass
class STTResult:
    """Result from STT transcription."""

    text: str
    language: VoiceLanguage
    confidence: float = 0.0
    duration_seconds: float = 0.0
    alternatives: list = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class STTProvider:
    """Mock STT provider for research mode.

    In production, replace with real provider:
    - GoogleSTTProvider
    - WhisperSTTProvider
    - VoskSTTProvider (offline)
    """

    def transcribe(
        self, audio_data: bytes, language: VoiceLanguage = VoiceLanguage.EN
    ) -> STTResult:
        """Convert speech to text.

        Mock implementation returns simulated transcription.
        Real implementation would call external API or local model.
        """
        # Mock: return a placeholder transcription
        # In production, this would be actual speech recognition
        mock_text = "how to make good compost"

        return STTResult(
            text=mock_text,
            language=language,
            confidence=0.95,
            duration_seconds=len(audio_data) / 16000 if audio_data else 0,
            alternatives=[
                {"text": "how to make compost", "confidence": 0.85},
                {"text": "compost making guide", "confidence": 0.70},
            ],
        )

    def detect_language(self, audio_data: bytes) -> VoiceLanguage:
        """Detect language of audio.

        Mock implementation returns English.
        """
        return VoiceLanguage.EN


# Singleton
_stt_provider: STTProvider | None = None


def get_stt_provider() -> STTProvider:
    """Get singleton STT provider."""
    global _stt_provider
    if _stt_provider is None:
        _stt_provider = STTProvider()
    return _stt_provider
