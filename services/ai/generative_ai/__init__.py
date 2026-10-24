"""
Generative AI Module — Compatibility Layer

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

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - for type checkers and IDEs only
    from services.ai.embedding_service import EmbeddingService as EmbeddingProvider
    from services.ai.llm_router import LLMProvider, LLMRouter
    from services.ai.unified_rag import RAGConfig as RAGConfig
    from services.ai.unified_rag import UnifiedRAG as RAGEngine

#: Public name -> (module under services.ai, attribute there).
_LAZY: dict[str, tuple[str, str]] = {
    "EmbeddingProvider": ("services.ai.embedding_service", "EmbeddingService"),
    "LLMProvider": ("services.ai.llm_router", "LLMProvider"),
    "LLMRouter": ("services.ai.llm_router", "LLMRouter"),
    "RAGEngine": ("services.ai.unified_rag", "UnifiedRAG"),
    "RAGConfig": ("services.ai.unified_rag", "RAGConfig"),
    "LocalEmbeddingProvider": ("services.ai.embedding_service", "EmbeddingService"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_path, attribute = target
    from importlib import import_module

    value = getattr(import_module(module_path), attribute)
    globals()[name] = value  # cache, so the lookup happens once
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY))


# Type aliases for compatibility
RAGQuery = dict  # Use dict with query, language, top_k, etc.
RAGResponse = dict  # Use dict with answer, sources, confidence, language
VectorStore = object  # Use Qdrant directly
FAISSVectorStore = object  # Not used in cloud-native
KnowledgeGraph = object  # Not used in cloud-native
CalibrationAssistant = object  # Use AdvisoryAgent
VoiceInterface = object  # Use VoiceAssistant
FarmerKnowledgeIngestion = object  # Use RAGEngine.add_documents

KnowledgeEntry = dict

__all__ = [
    "CalibrationAssistant",
    "EmbeddingProvider",
    "FAISSVectorStore",
    "FarmerKnowledgeIngestion",
    "KnowledgeEntry",
    "KnowledgeGraph",
    "LLMProvider",
    "LLMRouter",
    "LocalEmbeddingProvider",
    "RAGConfig",
    "RAGEngine",
    "RAGQuery",
    "RAGResponse",
    "VectorStore",
    "VoiceInterface",
]
