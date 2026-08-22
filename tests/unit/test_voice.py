"""Tests for Voice AI / IVR module."""

from fastapi.testclient import TestClient

from services.business_modules.voice.ivr_engine import IVRState, get_ivr_engine
from services.business_modules.voice.stt_provider import get_stt_provider
from services.business_modules.voice.tts_provider import VoiceLanguage, get_tts_provider
from services.api_gateway.main import app

client = TestClient(app)


class TestTTSProvider:
    """Test Text-to-Speech provider."""

    def test_synthesize_returns_result(self):
        """Verify TTS synthesis returns valid result."""
        tts = get_tts_provider()
        result = tts.synthesize("Hello world", VoiceLanguage.EN)

        assert result.text == "Hello world"
        assert result.language == VoiceLanguage.EN
        assert result.duration_seconds > 0

    def test_synthesize_persian(self):
        """Verify TTS synthesis for Persian."""
        tts = get_tts_provider()
        result = tts.synthesize("سلام دنیا", VoiceLanguage.FA)

        assert result.language == VoiceLanguage.FA
        assert result.voice_id == "voice_fa_default"

    def test_get_available_voices(self):
        """Verify available voices list."""
        tts = get_tts_provider()
        voices = tts.get_available_voices(VoiceLanguage.EN)

        assert len(voices) >= 2
        assert any("male" in v["id"] for v in voices)
        assert any("female" in v["id"] for v in voices)


class TestSTTProvider:
    """Test Speech-to-Text provider."""

    def test_transcribe_returns_result(self):
        """Verify STT transcription returns valid result."""
        stt = get_stt_provider()
        result = stt.transcribe(b"mock_audio_data", VoiceLanguage.EN)

        assert result.text
        assert result.language == VoiceLanguage.EN
        assert 0 <= result.confidence <= 1

    def test_transcribe_has_alternatives(self):
        """Verify STT returns alternatives."""
        stt = get_stt_provider()
        result = stt.transcribe(b"mock_audio_data", VoiceLanguage.EN)

        assert len(result.alternatives) > 0

    def test_detect_language(self):
        """Verify language detection."""
        stt = get_stt_provider()
        lang = stt.detect_language(b"mock_audio_data")

        assert lang == VoiceLanguage.EN


class TestIVREngine:
    """Test IVR engine."""

    def test_start_session(self):
        """Verify IVR session creation."""
        engine = get_ivr_engine()
        session = engine.start_session("test-1", "+989123456789", VoiceLanguage.EN)

        assert session.session_id == "test-1"
        assert session.state == IVRState.MAIN_MENU

    def test_main_menu_prompt(self):
        """Verify main menu prompt."""
        engine = get_ivr_engine()
        session = engine.start_session("test-2", "+989123456789", VoiceLanguage.EN)
        response = engine.get_prompt(session)

        assert "Welcome to Eco Nojin" in response.prompt_text
        assert "Press 1" in response.prompt_text
        assert response.end_call is False

    def test_main_menu_persian(self):
        """Verify Persian main menu prompt."""
        engine = get_ivr_engine()
        session = engine.start_session("test-3", "+989123456789", VoiceLanguage.FA)
        response = engine.get_prompt(session)

        assert "اکو نوژین" in response.prompt_text

    def test_dtmf_navigation(self):
        """Verify DTMF menu navigation."""
        engine = get_ivr_engine()
        session = engine.start_session("test-4", "+989123456789", VoiceLanguage.EN)

        # Press 1 for soil analysis
        engine.handle_dtmf(session, "1")
        assert session.state == IVRState.SOIL_ANALYSIS

    def test_dtmf_exit(self):
        """Verify DTMF exit."""
        engine = get_ivr_engine()
        session = engine.start_session("test-5", "+989123456789", VoiceLanguage.EN)

        # Press 0 to exit
        response = engine.handle_dtmf(session, "0")
        assert session.state == IVRState.GOODBYE
        assert response.end_call is True


class TestVoiceAPIEndpoints:
    """Test voice API endpoints."""

    def test_ivr_start_endpoint(self):
        """Verify IVR start endpoint."""
        response = client.post(
            "/api/v1/voice/ivr/start",
            json={
                "session_id": "api-test-1",
                "phone_number": "+989123456789",
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "api-test-1"
        assert "Welcome" in data["prompt_text"]

    def test_ivr_dtmf_endpoint(self):
        """Verify IVR DTMF endpoint."""
        response = client.post(
            "/api/v1/voice/ivr/dtmf",
            json={
                "session_id": "api-test-2",
                "digit": "1",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "soil_analysis"

    def test_ivr_menu_preview_endpoint(self):
        """Verify IVR menu preview endpoint."""
        response = client.get("/api/v1/voice/ivr/menu/fa")

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "fa"
        assert "اکو نوژین" in data["menu_text"]

    def test_tts_endpoint(self):
        """Verify TTS endpoint."""
        response = client.post(
            "/api/v1/voice/tts",
            json={
                "text": "Hello world",
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hello world"
        assert data["duration_seconds"] > 0

    def test_stt_endpoint(self):
        """Verify STT endpoint."""
        import base64

        audio_b64 = base64.b64encode(b"mock_audio").decode()

        response = client.post(
            "/api/v1/voice/stt",
            json={
                "audio_base64": audio_b64,
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "confidence" in data

    def test_voice_ask_endpoint(self):
        """Verify voice ask endpoint."""
        response = client.post(
            "/api/v1/voice/ask",
            json={
                "question": "How to make good compost?",
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"]

    def test_voice_health_endpoint(self):
        """Verify voice health endpoint."""
        response = client.get("/api/v1/voice/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["mode"] == "mock"
        assert data["features"]["ivr_menu"] is True

    def test_voice_languages_endpoint(self):
        """Verify voice languages endpoint."""
        response = client.get("/api/v1/voice/languages")

        assert response.status_code == 200
        data = response.json()
        assert len(data["languages"]) == 3

    def test_health_reports_voice_module(self):
        """Verify main health endpoint reports voice module."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "voice_ivr" in data["modules"]
        assert data["inclusive_access"]["voice_ivr"] is True
