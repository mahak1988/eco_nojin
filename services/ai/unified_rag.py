"""Unified RAG Service — Qdrant Cloud + Jina Embeddings + LLM Router.

Single collection for all 14 languages with language detection.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
)

from services.ai.embedding_service import get_embedding_service, EmbeddingProvider
from services.ai.llm_router import get_router


@dataclass
class RAGConfig:
    collection_name: str = "econojin_knowledge"
    vector_size: int = 768
    distance: Distance = Distance.COSINE
    top_k: int = 5
    score_threshold: float = 0.3


@dataclass
class SearchResult:
    id: str
    content: str
    metadata: dict[str, Any]
    score: float


class UnifiedRAG:
    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()
        self.embedding_service = get_embedding_service()
        self.llm_router = get_router()
        self.client: AsyncQdrantClient | None = None

    async def _init_client(self):
        if self.client is None:
            qdrant_url = os.getenv("QDRANT_URL")
            qdrant_key = os.getenv("QDRANT_API_KEY")
            if not qdrant_url:
                raise RuntimeError("QDRANT_URL not configured")
            self.client = AsyncQdrantClient(
                url=qdrant_url,
                api_key=qdrant_key,
                timeout=30.0,
            )
            await self._ensure_collection()

    async def _ensure_collection(self):
        if not self.client:
            return
        collections = await self.client.get_collections()
        exists = any(c.name == self.config.collection_name for c in collections.collections)
        if not exists:
            await self.client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=self.config.distance,
                ),
            )

    def _detect_language(self, text: str) -> str:
        try:
            from langdetect import detect
            return detect(text)
        except Exception:
            return "fa"

    async def add_documents(
        self,
        documents: list[dict[str, Any]],
        language: str | None = None,
    ) -> list[str]:
        """Add documents to the knowledge base.
        
        Each document: {"content": str, "metadata": dict, "language": str (optional)}
        """
        await self._init_client()

        texts = [doc["content"] for doc in documents]
        embeddings = await self.embedding_service.embed(texts)

        points = []
        ids = []
        for i, (doc, emb) in enumerate(zip(documents, embeddings, strict=False)):
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            meta = doc.get("metadata", {}).copy()
            meta["content"] = doc["content"]
            meta["language"] = doc.get("language") or language or self._detect_language(doc["content"])
            meta["source"] = meta.get("source", "user")
            points.append(PointStruct(id=point_id, vector=emb, payload=meta))

        await self.client.upsert(
            collection_name=self.config.collection_name,
            points=points,
        )
        return ids

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        language: str | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for relevant documents."""
        await self._init_client()

        top_k = top_k or self.config.top_k
        query_lang = language or self._detect_language(query)
        query_emb = await self.embedding_service.embed_query(query)

        must_conditions = []
        if query_lang:
            must_conditions.append(FieldCondition(key="language", match=MatchValue(value=query_lang)))
        if filter_metadata:
            for k, v in filter_metadata.items():
                must_conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))

        search_filter = Filter(must=must_conditions) if must_conditions else None

        results = await self.client.search(
            collection_name=self.config.collection_name,
            query_vector=query_emb,
            limit=top_k,
            query_filter=search_filter,
            score_threshold=self.config.score_threshold,
        )

        return [
            SearchResult(
                id=str(r.id),
                content=r.payload.get("content", ""),
                metadata={k: v for k, v in r.payload.items() if k != "content"},
                score=r.score,
            )
            for r in results
        ]

    async def answer(
        self,
        question: str,
        top_k: int | None = None,
        language: str | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Full RAG pipeline: retrieve → generate."""
        lang = language or self._detect_language(question)

        # Retrieve
        results = await self.search(question, top_k, lang)

        if not results:
            return {
                "answer": "I don't have enough information to answer this question.",
                "sources": [],
                "confidence": 0.0,
                "language": lang,
            }

        # Build context
        context_parts = []
        sources = []
        for i, r in enumerate(results):
            context_parts.append(f"[Source {i+1}] {r.content}")
            sources.append({
                "id": r.id,
                "content": r.content[:200],
                "metadata": r.metadata,
                "score": r.score,
            })

        context = "\n\n".join(context_parts)

        # Default system prompt with anti-hallucination
        if system_prompt is None:
            system_prompt = """You are an expert agricultural advisor for Eco Nojin platform.
Answer ONLY based on the provided context. If the context doesn't contain enough information,
say so honestly. Cite sources using [Source N] format. Respond in the user's language."""

        # Generate answer
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]

        try:
            response = await self.llm_router.chat(messages, model_alias="default")
            answer = response.choices[0].message.content
        except Exception as e:
            # Fallback: return context directly
            answer = f"Based on available sources:\n{context}\n\n(LLM generation failed: {e})"

        # Confidence based on top score and number of sources
        confidence = min(1.0, results[0].score * 1.2) if results else 0.0
        if len(results) > 1:
            confidence = min(1.0, confidence + 0.1)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 2),
            "language": lang,
            "num_sources": len(results),
        }

    async def close(self):
        if self.client:
            await self.client.close()
        await self.embedding_service.close()


# Singleton
_rag: UnifiedRAG | None = None


def get_rag() -> UnifiedRAG:
    global _rag
    if _rag is None:
        _rag = UnifiedRAG()
    return _rag