"""Voice Assistant: Integration of IVR + AI Assistant (RAG).

Provides voice-based Q&A using the existing RAG engine.
"""

from dataclasses import dataclass

from engine.hydroma.ai_assistant.rag_engine import get_engine

from .stt_provider import get_stt_provider
from .tts_provider import VoiceLanguage, get_tts_provider


@dataclass
class VoiceResponse:
    """Response from voice assistant."""

    text: str
    audio_data: bytes | None = None
    language: VoiceLanguage = VoiceLanguage.EN
    confidence: float = 0.0
    sources: list = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []


class VoiceAssistant:
    """Voice assistant with RAG integration."""

    def __init__(self):
        self.tts = get_tts_provider()
        self.stt = get_stt_provider()
        self.rag = get_engine()

    def answer_question(
        self, question: str, language: VoiceLanguage = VoiceLanguage.EN
    ) -> VoiceResponse:
        """Answer a question using RAG and return voice response."""
        # Get answer from RAG
        rag_result = self.rag.generate_response(question)

        # Generate TTS audio
        tts_result = self.tts.synthesize(rag_result["answer"], language)

        return VoiceResponse(
            text=rag_result["answer"],
            audio_data=tts_result.audio_data,
            language=language,
            confidence=rag_result.get("confidence", 0.0),
            sources=rag_result.get("sources", []),
        )

    def process_voice_input(
        self, audio_data: bytes, language: VoiceLanguage = VoiceLanguage.EN
    ) -> VoiceResponse:
        """Process voice input: STT -> RAG -> TTS."""
        # Step 1: Speech-to-Text
        stt_result = self.stt.transcribe(audio_data, language)

        # Step 2: Get answer from RAG
        rag_result = self.rag.generate_response(stt_result.text)

        # Step 3: Text-to-Speech
        tts_result = self.tts.synthesize(rag_result["answer"], language)

        return VoiceResponse(
            text=rag_result["answer"],
            audio_data=tts_result.audio_data,
            language=language,
            confidence=rag_result.get("confidence", 0.0),
            sources=rag_result.get("sources", []),
        )


# Singleton
_voice_assistant: VoiceAssistant | None = None


def get_voice_assistant() -> VoiceAssistant:
    """Get singleton voice assistant."""
    global _voice_assistant
    if _voice_assistant is None:
        _voice_assistant = VoiceAssistant()
    return _voice_assistant
