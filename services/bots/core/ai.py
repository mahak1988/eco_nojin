"""AI layer for the bot: local Ollama client + citation-grounded advice.

Design (Phase 1):
- ``OllamaClient`` talks to a local Ollama server (offline-safe: every call
  is wrapped, and ``available()`` is cached for a short time).
- ``AdviceService`` retrieves evidence from the existing RAG engine
  (``engine.hydroma.ai_assistant``), then optionally synthesizes a response
  in the user's language with the model. If Ollama is offline, the raw
  English evidence is returned with an honest note — never fabricated
  content.
"""

from __future__ import annotations

import logging

import httpx

from .. import i18n
from ..config import BotConfig

logger = logging.getLogger(__name__)


class OllamaClient:
    """Thin async client for a local Ollama server."""

    def __init__(self, config: BotConfig) -> None:
        self._base = config.ollama_base_url.rstrip("/")
        self._model = config.ollama_model
        self._timeout = config.ollama_timeout
        self._available: bool | None = None

    async def available(self) -> bool:
        """Whether the Ollama server responds (checked once, cached)."""
        if self._available is not None:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base}/api/tags")
                self._available = resp.status_code == 200
        except Exception:
            logger.info("Ollama not reachable at %s", self._base)
            self._available = False
        return self._available

    async def chat(self, system: str, user: str, temperature: float = 0.2) -> str | None:
        """Chat completion; returns None on any failure (never raises)."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout + 15.0) as client:
                resp = await client.post(
                    f"{self._base}/api/chat",
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "stream": False,
                        "options": {"temperature": temperature},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content")
        except Exception:
            logger.exception("Ollama chat failed")
            return None


class AdviceService:
    """Combines RAG retrieval with optional local-LLM synthesis."""

    def __init__(self, config: BotConfig, rag=None, ollama: OllamaClient | None = None) -> None:
        from engine.hydroma.ai_assistant.rag_engine import RAGEngine

        self._config = config
        self._rag = rag if rag is not None else RAGEngine()
        self._ollama = ollama if ollama is not None else OllamaClient(config)

    async def advise(self, query: str, language: str) -> dict:
        """Answer a user question with citations.

        Returns: {"answer": str, "sources": [...], "language": str,
        "translated": bool}
        """
        retrieved = self._rag.retrieve(query, top_k=3)
        if not retrieved:
            return {
                "answer": i18n.t(language, "no_answer"),
                "sources": [],
                "language": language,
                "translated": False,
            }

        source_lines = [
            f"[{i + 1}] {doc.title} ({doc.source})" for i, (doc, _s) in enumerate(retrieved)
        ]
        context = "\n\n".join(
            f"[{i + 1}] {doc.content}" for i, (doc, _s) in enumerate(retrieved)
        )

        if await self._ollama.available():
            translated = await self._ollama.chat(
                system=(
                    "You are an agricultural advisor for the Eco Nojin platform. "
                    "Answer ONLY from the provided context. Cite sources inline as [1], [2], ... "
                    f"Respond in the language code '{language}'. "
                    "If the context does not answer the question, say so clearly."
                ),
                user=f"Context:\n{context}\n\nQuestion: {query}",
            )
            if translated:
                answer = (
                    f"{translated.strip()}\n\n📚 منابع:\n" + "\n".join(source_lines)
                )
                return {
                    "answer": answer,
                    "sources": [d.id for d, _s in retrieved],
                    "language": language,
                    "translated": True,
                }

        # Offline fallback: honest English evidence + note.
        top_doc, _score = retrieved[0]
        answer = (
            f"📚 {top_doc.source}: {top_doc.title}\n\n{top_doc.content}"
            + i18n.t(language, "ollama_offline_note")
        )
        return {
            "answer": answer,
            "sources": [d.id for d, _s in retrieved],
            "language": language,
            "translated": False,
        }
