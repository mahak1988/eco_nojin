"""
Generative AI Module for Eco Nojin — Cloud-Native Compatibility Layer
======================================================================

This module provides backward compatibility imports for the old generative_ai API.
New code should use services.ai.* modules directly.

Exports (compatibility):
- RAGEngine -> services.ai.unified_rag.UnifiedRAG
- EmbeddingProvider -> services.ai.embedding_service.EmbeddingService
- KnowledgeGraph -> Not available in cloud-native (use Qdrant collections)
- CalibrationAssistant -> Not available (use AdvisoryAgent)
- VoiceInterface -> Not available (use VoiceAssistant)
- FarmerKnowledgeIngestion -> Not available (use UnifiedRAG.add_documents)
"""

# Re-export from new cloud-native services
from services.ai.unified_rag import UnifiedRAG as RAGEngine
from services.ai.unified_rag import RAGConfig as RAGConfig
from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
from services.ai.llm_router import LLMRouter, LLMProvider

# Type aliases for compatibility
RAGQuery = dict  # Use dict with query, language, top_k, etc.
RAGResponse = dict  # Use dict with answer, sources, confidence, language
VectorStore = object  # Use Qdrant directly
FAISSVectorStore = object  # Not used in cloud-native
KnowledgeGraph = object  # Not used in cloud-native
LocalEmbeddingProvider = EmbeddingProvider
CalibrationAssistant = object  # Use AdvisoryAgent
VoiceInterface = object  # Use VoiceAssistant
FarmerKnowledgeIngestion = object  # Use RAGEngine.add_documents

KnowledgeEntry = dict
RAGEngine = RAGEngine
RAGConfig = RAGConfig
EmbeddingProvider = EmbeddingProvider
LLMRouter = LLMRouter
LLMProvider = LLMProvider

__all__ = [
    "RAGEngine",
    "RAGConfig",
    "EmbeddingProvider",
    "LLMRouter",
    "LLMProvider",
    "RAGQuery",
    "RAGResponse",
    "VectorStore",
    "FAISSVectorStore",
    "KnowledgeGraph",
    "LocalEmbeddingProvider",
    "CalibrationAssistant",
    "VoiceInterface",
    "FarmerKnowledgeIngestion",
    "KnowledgeEntry",
]