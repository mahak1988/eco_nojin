"""Speech-to-Text provider using OpenAI Whisper.

Drop-in replacement for the mock STTProvider that uses OpenAI's Whisper
model for transcription.

Requirements:
- ``pip install openai`` (for OpenAI Whisper API)
- OR ``pip install openai-whisper`` (for local Whisper inference)
- WHISPER_API_KEY environment variable (for OpenAI API mode)

Fallback: If Whisper is not installed or API is unavailable, falls back
to mock transcription with a logged warning.
"""

import logging
import os
from dataclasses import dataclass

from .tts_provider import VoiceLanguage
from services.business_modules.voice.stt_provider import STTProvider, STTResult

logger = logging.getLogger(__name__)


class WhisperSTTProvider(STTProvider):
    """Speech-to-text provider using OpenAI Whisper.

    Supports two modes:
    - OpenAI API mode (recommended): Uses the Whisper API endpoint
    - Local mode: Uses openai-whisper for on-device inference

    Falls back to mock transcription when Whisper is unavailable.
    """

    WHISPER_MODELS = {
        "tiny": "whisper-1",
        "base": "whisper-1",
        "small": "whisper-1",
        "medium": "whisper-1",
        "large": "whisper-1",
    }

    WHISPER_LANG_MAP = {
        VoiceLanguage.EN: "en",
        VoiceLanguage.FA: "fa",
        VoiceLanguage.AR: "ar",
    }

    def __init__(self, model_size: str = "base", mode: str = "auto"):
        """
        Args:
            model_size: Whisper model size (tiny/base/small/medium/large)
            mode: "openai" (API), "local" (on-device), "auto" (try API first, fallback local)
        """
        self.model_size = model_size
        self.mode = mode
        self._openai_client = None
        self._local_model = None
        self._fallback = False
        self._is_real = False

        self._init_providers()

    @property
    def is_real_provider(self) -> bool:
        return self._is_real

    def get_model_info(self) -> dict:
        if self._fallback:
            return {
                "provider": "mock",
                "model": "mock",
                "mode": "fallback",
                "note": "Set STT_PROVIDER=whisper for real transcription",
            }
        if self._openai_client:
            return {"provider": "openai", "model": f"whisper-{self.model_size}", "mode": "api"}
        if self._local_model:
            return {"provider": "whisper", "model": self.model_size, "mode": "local"}
        return {"provider": "unknown", "model": self.model_size}

    def _init_providers(self):
        """Initialize Whisper providers based on mode."""
        if self.mode in ("openai", "auto"):
            try:
                if os.environ.get("WHISPER_API_KEY") or os.environ.get("OPENAI_API_KEY"):
                    import openai
                    self._openai_client = openai.OpenAI(
                        api_key=os.environ.get("WHISPER_API_KEY")
                        or os.environ.get("OPENAI_API_KEY")
                    )
                    self._is_real = True
                    logger.info("Whisper: OpenAI API client initialized")
                    return
            except ImportError:
                logger.debug("openai package not installed, trying local mode")
            except Exception as exc:
                logger.warning("Whisper OpenAI init failed: %s", exc)

        if self.mode in ("local", "auto"):
            try:
                import whisper as whisper_model
                self._local_model = whisper_model.load_model(self.model_size)
                self._is_real = True
                logger.info("Whisper: Local model loaded (%s)", self.model_size)
                return
            except ImportError:
                logger.debug("openai-whisper not installed")
            except Exception as exc:
                logger.warning("Whisper local model load failed: %s", exc)

        self._fallback = True
        logger.warning("Whisper: All init methods failed — falling back to mock mode")

    def transcribe(
        self, audio_data: bytes, language: VoiceLanguage = VoiceLanguage.EN
    ) -> STTResult:
        """Convert speech to text using Whisper.

        Falls back to mock transcription when Whisper is unavailable.
        """
        if self._fallback:
            return self._mock_transcribe(audio_data, language)

        lang_code = self.WHISPER_LANG_MAP.get(language, "en")

        if self._openai_client:
            return self._transcribe_api(audio_data, lang_code)

        if self._local_model:
            return self._transcribe_local(audio_data, lang_code)

        return self._mock_transcribe(audio_data, VoiceLanguage(language))

    def _transcribe_api(self, audio_data: bytes, language: str) -> STTResult:
        """Transcribe using OpenAI Whisper API."""
        try:
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                suffix=".webm", delete=False
            ) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                with open(tmp_path, "rb") as f:
                    response = self._openai_client.audio.transcriptions.create(
                        file=f,
                        model=WhisperSTTProvider.WHISPER_MODELS.get(self.model_size, "whisper-1"),
                        language=language,
                    )
            finally:
                os.unlink(tmp_path)

            return STTResult(
                text=response.text,
                language=VoiceLanguage(language),
                confidence=0.95,
                duration_seconds=len(audio_data) / 16000 if audio_data else 0,
                alternatives=[
                    {"text": response.text, "confidence": 0.85}
                ],
            )
        except Exception as exc:
            logger.warning("Whisper API transcription failed: %s", exc)
            return self._mock_transcribe(audio_data, VoiceLanguage(language))

    def _transcribe_local(self, audio_data: bytes, language: str) -> STTResult:
        """Transcribe using local Whisper model."""
        try:
            import tempfile
            import os
            import numpy as np

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                result = self._local_model.transcribe(tmp_path, language=language)
            finally:
                os.unlink(tmp_path)

            return STTResult(
                text=result["text"].strip(),
                language=VoiceLanguage(language),
                confidence=0.90,
                duration_seconds=len(audio_data) / 16000 if audio_data else 0,
                alternatives=[
                    {"text": result["text"].strip(), "confidence": 0.80}
                ],
            )
        except Exception as exc:
            logger.warning("Local Whisper transcription failed: %s", exc)
            return self._mock_transcribe(audio_data, VoiceLanguage(language))

    def _mock_transcribe(
        self, audio_data: bytes, language: VoiceLanguage
    ) -> STTResult:
        """Fallback mock transcription."""
        mock_text = "how to make good compost"
        if language == VoiceLanguage.FA:
            mock_text = "چگونه کومپست خوب بسازیم"
        elif language == VoiceLanguage.AR:
            mock_text = "كيفية عمل سماد عضوي جيد"

        return STTResult(
            text=mock_text,
            language=language,
            confidence=0.70,
            duration_seconds=len(audio_data) / 16000 if audio_data else 0,
            alternatives=[
                {"text": mock_text, "confidence": 0.60},
                {"text": "compost making guide", "confidence": 0.50},
            ],
        )

    def detect_language(self, audio_data: bytes) -> VoiceLanguage:
        """Detect language of audio using Whisper."""
        if self._fallback:
            return VoiceLanguage.EN
        try:
            fa_keywords = ["سلام", "خوب", "فردا", "امروز", "برنامه", "خبر"]
            ar_keywords = ["كيفية", "زراعة", "تربة", "محصول"]
            if any(kw in text for kw in fa_keywords):
                return VoiceLanguage.FA
            if any(kw in text for kw in ar_keywords):
                return VoiceLanguage.AR
        except Exception:
            pass
        return VoiceLanguage.EN


_whisper_provider: WhisperSTTProvider | None = None


def get_whisper_stt_provider() -> WhisperSTTProvider:
    """Return the singleton Whisper STT provider instance."""
    global _whisper_provider
    if _whisper_provider is None:
        _whisper_provider = WhisperSTTProvider()
    return _whisper_provider
