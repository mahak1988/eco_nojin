"""Text-to-Speech provider using Coqui TTS.

Drop-in replacement for the mock TTSProvider that uses Coqui TTS
for high-quality speech synthesis, including Persian and Arabic.

Requirements:
- ``pip install TTS`` (Coqui TTS)
- Requires downloading models on first run

Fallback: If Coqui TTS is not installed or model loading fails,
falls back to mock synthesis with a logged warning.
"""

import logging

from .tts_provider import TTSProvider, TTSResult, VoiceLanguage

logger = logging.getLogger(__name__)


class CoquiTTSProvider(TTSProvider):
    """Text-to-speech provider using Coqui TTS.

    Supports multiple languages including Persian (fa) and Arabic (ar).
    Falls back to mock synthesis when Coqui TTS is unavailable.
    """

    COQUI_VOICES = {
        VoiceLanguage.EN: {
            "male": {
                "id": "en_male",
                "name": "English Male",
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
            },
            "female": {
                "id": "en_female",
                "name": "English Female",
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
            },
        },
        VoiceLanguage.FA: {
            "male": {
                "id": "fa_male",
                "name": "Persian Male",
                "model": "tts_models/fa/balam/accelerate",
            },
            "female": {
                "id": "fa_female",
                "name": "Persian Female",
                "model": "tts_models/fa/balam/accelerate",
            },
        },
        VoiceLanguage.AR: {
            "male": {
                "id": "ar_male",
                "name": "Arabic Male",
                "model": "tts_models/ar/balam/accelerate",
            },
            "female": {
                "id": "ar_female",
                "name": "Arabic Female",
                "model": "tts_models/ar/balam/accelerate",
            },
        },
    }

    def __init__(self, model_name: str | None = None, voice: str = "auto"):
        """
        Args:
            model_name: Specific Coqui TTS model to use
            voice: "auto", "male", or "female"
        """
        self.model_name = model_name
        self.voice = voice
        self._tts_engine = None
        self._fallback = False
        self._is_real = False

        self._init_engine()

    @property
    def is_real_provider(self) -> bool:
        return self._is_real

    def get_model_info(self) -> dict:
        if self._fallback:
            return {
                "provider": "mock",
                "model": "mock",
                "mode": "fallback",
                "note": "Set TTS_PROVIDER=coqui for real synthesis",
            }
        if self._tts_engine:
            return {
                "provider": "coqui",
                "model": self.model_name or "tacotron2-DDC",
                "mode": "local",
            }
        return {"provider": "unknown", "model": self.model_name or "default"}

    def _init_engine(self):
        """Initialize Coqui TTS engine."""
        try:
            from TTS.api import TTS as CoquiTTS

            if self.model_name:
                self._tts_engine = CoquiTTS(model_name=self.model_name)
            else:
                self._tts_engine = CoquiTTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

            self._is_real = True
            logger.info("Coqui TTS engine initialized")
        except ImportError:
            logger.warning("TTS package not installed — falling back to mock mode")
            self._fallback = True
        except Exception as exc:
            logger.warning("Coqui TTS init failed: %s — falling back to mock", exc)
            self._fallback = True

    def synthesize(self, text: str, language: VoiceLanguage = VoiceLanguage.EN) -> TTSResult:
        """Convert text to speech using Coqui TTS.

        Falls back to mock synthesis when Coqui is unavailable.
        """
        if self._fallback or self._tts_engine is None:
            return self._mock_synthesize(text, language)

        try:
            voice_config = self.COQUI_VOICES.get(language, self.COQUI_VOICES[VoiceLanguage.EN])
            selected_voice = voice_config.get(
                self.voice if self.voice in voice_config else "female", voice_config["female"]
            )
            model_name = selected_voice["model"]

            try:
                self._tts_engine = __import__("TTS.api", fromlist=["TTS"]).TTS(
                    model_name=model_name
                )
            except Exception:
                pass

            wav = self._tts_engine.tts(text=text, speaker_name=selected_voice["id"])

            estimated_duration = len(text) / 15.0
            return TTSResult(
                text=text,
                language=language,
                audio_data=wav.tobytes() if hasattr(wav, "tobytes") else None,
                duration_seconds=estimated_duration,
                voice_id=selected_voice["id"],
            )
        except Exception as exc:
            logger.warning("Coqui synthesis failed: %s — using mock", exc)
            return self._mock_synthesize(text, language)

    def get_available_voices(self, language: VoiceLanguage) -> list:
        """Get available voices for a language."""
        voices = self.COQUI_VOICES.get(language, {})
        result = []
        for gender, config in voices.items():
            result.append(
                {
                    "id": config["id"],
                    "name": config["name"],
                    "model": config["model"],
                    "gender": gender,
                    "engine": "coqui",
                }
            )
        if not result:
            result = super().get_available_voices(language)
        return result

    def _mock_synthesize(self, text: str, language: VoiceLanguage) -> TTSResult:
        """Fallback mock synthesis."""
        estimated_duration = len(text) / 15.0
        return TTSResult(
            text=text,
            language=language,
            audio_data=None,
            duration_seconds=estimated_duration,
            voice_id=f"voice_{language.value}_default",
        )


_coqui_provider: CoquiTTSProvider | None = None


def get_coqui_tts_provider() -> CoquiTTSProvider:
    """Return the singleton Coqui TTS provider instance."""
    global _coqui_provider
    if _coqui_provider is None:
        _coqui_provider = CoquiTTSProvider()
    return _coqui_provider
