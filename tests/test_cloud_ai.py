"""Tests for Cloud-Native AI Services."""

import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLLMRouter:
    """Test LLM Router fallback logic."""

    def test_provider_chain_order(self):
        from services.ai.llm_router import PROVIDER_CHAIN, LLMProvider
        providers = [p.name for p in PROVIDER_CHAIN]
        assert providers == [
            LLMProvider.GROQ,
            LLMProvider.OPENROUTER,
            LLMProvider.GOOGLE,
            LLMProvider.MISTRAL,
            LLMProvider.DEEPSEEK,
        ]

    def test_model_resolution(self):
        from services.ai.llm_router import LLMRouter, LLMProvider
        router = LLMRouter()
        # Test default model
        assert router._resolve_model(LLMProvider.GROQ, "default") == "llama-3.3-70b-versatile"
        # Test fast model
        assert router._resolve_model(LLMProvider.GROQ, "fast") == "llama-3.1-8b-instant"
        # Test tools model
        assert router._resolve_model(LLMProvider.GROQ, "tools") == "qwen/qwen3-32b"

    @pytest.mark.asyncio
    async def test_fallback_on_429(self):
        from services.ai.llm_router import LLMRouter
        router = LLMRouter()
        
        # Mock clients with at least 2 providers
        from unittest.mock import AsyncMock, MagicMock
        mock_client1 = AsyncMock()
        mock_client1.chat.completions.create.side_effect = [
            Exception("429 Rate Limit"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="fallback response"))]),
        ]
        mock_client2 = AsyncMock()
        mock_client2.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="success"))]
        )
        
        # Need to have at least 2 clients in the router
        providers = list(router._clients.keys())
        if len(providers) < 2:
            pytest.skip("Need at least 2 providers configured for fallback test")
        
        router._clients[providers[0]] = mock_client1
        router._clients[providers[1]] = mock_client2
        
        # Should fall through to second provider on 429
        with patch.object(router, '_get_client', side_effect=[mock_client1, mock_client2]):
            with patch.object(router.quota, 'can_use', return_value=True):
                result = await router.chat([{"role": "user", "content": "test"}])
                assert result is not None


class TestEmbeddingService:
    """Test Embedding Service fallback."""

    def test_embedding_chain_order(self):
        from services.ai.embedding_service import EMBEDDING_CHAIN, EmbeddingProvider
        providers = [c.name for c in EMBEDDING_CHAIN]
        assert providers == [
            EmbeddingProvider.JINA,
            EmbeddingProvider.CLOUDFLARE,
            EmbeddingProvider.COHERE,
        ]

    def test_jina_dimensions(self):
        from services.ai.embedding_service import EMBEDDING_CHAIN
        jina_config = next(c for c in EMBEDDING_CHAIN if c.name.value == "jina")
        assert jina_config.dimensions == 768
        assert jina_config.model == "jina-embeddings-v3"


class TestUnifiedRAG:
    """Test Unified RAG pipeline."""

    def test_rag_config_defaults(self):
        from services.ai.unified_rag import RAGConfig
        config = RAGConfig()
        assert config.collection_name == "econojin_knowledge"
        assert config.vector_size == 768
        assert config.top_k == 5

    def test_language_detection(self):
        from services.ai.unified_rag import UnifiedRAG
        rag = UnifiedRAG()
        # Persian
        assert rag._detect_language("این یک متن فارسی است") == "fa"
        # English
        assert rag._detect_language("This is English text") == "en"
        # Arabic
        assert rag._detect_language("هذا نص عربي") == "ar"


class TestDroughtAgent:
    """Test Drought Analysis Agent."""

    def test_spi_interpretation(self):
        from services.analysis.drought_agent import DroughtAgent
        agent = DroughtAgent()
        assert "خشک" in agent._interpret_spi(-1.5)
        assert "مرطوب" in agent._interpret_spi(1.5)
        assert "طبیعی" in agent._interpret_spi(0.5)

    def test_spei_interpretation(self):
        from services.analysis.drought_agent import DroughtAgent
        agent = DroughtAgent()
        # SPEI uses same thresholds
        assert agent._interpret_spei(-2.0) == "بسیار خشک (Extremely Dry)"


class TestScenarioAgent:
    """Test Scenario Agent."""

    def test_scenario_config(self):
        from services.analysis.scenario_agent import ScenarioConfig
        config = ScenarioConfig(base_lat=35.7, base_lon=51.4)
        assert config.base_lat == 35.7
        assert config.base_lon == 51.4
        assert config.precip_change_pct == 0.0


class TestAdvisoryAgent:
    """Test Advisory Agent intent detection."""

    def test_intent_detection_drought(self):
        from services.analysis.advisory_agent import AdvisoryAgent
        agent = AdvisoryAgent()
        assert agent._detect_intent("خشکسالی اصفهان چطوره؟") == "drought"
        assert agent._detect_intent("SPI index for my farm") == "drought"
        assert agent._detect_intent("بارش کم بوده") == "drought"

    def test_intent_detection_scenario(self):
        from services.analysis.advisory_agent import AdvisoryAgent
        agent = AdvisoryAgent()
        assert agent._detect_intent("اگر بارش 20% کم شود چه می‌شود؟") == "scenario"
        assert agent._detect_intent("سناریوی تغییر اقلیم") == "scenario"

    def test_intent_detection_general(self):
        from services.analysis.advisory_agent import AdvisoryAgent
        agent = AdvisoryAgent()
        assert agent._detect_intent("چگونه کومپست بسازم؟") == "general"
        assert agent._detect_intent("بهترین کود برای گندم؟") == "general"


class TestAIAnalysisRouter:
    """Test API Router models."""

    def test_drought_request_validation(self):
        from services.api_gateway.routers.ai_analysis import DroughtRequest
        req = DroughtRequest(lat=35.7, lon=51.4, months=6)
        assert req.lat == 35.7
        assert req.lon == 51.4

    def test_scenario_request_validation(self):
        from services.api_gateway.routers.ai_analysis import ScenarioRequest
        req = ScenarioRequest(
            lat=35.7, lon=51.4,
            precip_change_pct=-20,
            temp_change_c=2.0
        )
        assert req.precip_change_pct == -20
        assert req.temp_change_c == 2.0

    def test_advisory_request_language_validation(self):
        from services.api_gateway.routers.ai_analysis import AdvisoryRequest
        # Valid language
        req = AdvisoryRequest(question="test", language="fa")
        assert req.language == "fa"
        # Invalid language should fail
        with pytest.raises(Exception):
            AdvisoryRequest(question="test", language="xx")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])