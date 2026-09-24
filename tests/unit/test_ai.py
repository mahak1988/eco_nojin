"""Tests for AI Assistant Unified RAG engine."""

from services.ai.unified_rag import UnifiedRAG, RAGConfig


def test_rag_config_defaults():
    """Verify RAG config defaults."""
    config = RAGConfig()
    assert config.collection_name == "econojin_knowledge"
    assert config.vector_size == 768
    assert config.top_k == 5
    assert config.score_threshold == 0.3


def test_language_detection():
    """Verify language detection works."""
    rag = UnifiedRAG()
    assert rag._detect_language("این یک متن فارسی است") == "fa"
    assert rag._detect_language("This is English text") == "en"
    assert rag._detect_language("هذا نص عربي") == "ar"


def test_rag_singleton():
    """Verify singleton pattern works correctly."""
    from services.ai.unified_rag import get_rag
    engine1 = get_rag()
    engine2 = get_rag()
    assert engine1 is engine2


# Note: Integration tests with actual Qdrant require running infrastructure
# These tests verify the core logic without external dependencies