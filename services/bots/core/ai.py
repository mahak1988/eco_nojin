"""AI layer for the bot: cloud LLM + citation-grounded advice.

Design (Phase 1):
- ``LLMRouter`` talks to cloud LLM providers (Groq, OpenRouter, etc.)
- ``AdviceService`` retrieves evidence from the unified RAG,
  then optionally synthesizes a response with the cloud LLM.
  If LLM is offline, the raw evidence is returned with an honest note.
"""

from __future__ import annotations

import logging

import httpx

from .. import i18n
from ..config import BotConfig

from services.ai.unified_rag import get_rag
from services.ai.llm_router import get_router

logger = logging.getLogger(__name__)


class AdviceService:
    """Combines RAG retrieval with cloud-LLM synthesis."""

    def __init__(
        self,
        config: BotConfig,
        rag=None,
        llm_router=None,
    ) -> None:
        self._config = config
        self._rag = rag if rag is not None else get_rag()
        self._llm_router = llm_router if llm_router is not None else get_router()

    async def advise(self, query: str, language: str) -> dict:
        """Answer a user question with citations.

        Returns: {"answer": str, "sources": [...], "language": str,
        "translated": bool}
        """
        rag_result = await self._rag.answer(query, language=language)

        if not rag_result.get("sources"):
            return {
                "answer": i18n.t(language, "no_answer"),
                "sources": [],
                "language": language,
                "translated": False,
            }

        sources = rag_result.get("sources", [])
        source_lines = [
            f"[{i + 1}] {s['metadata'].get('title', 'Unknown')} ({s['metadata'].get('source', 'Unknown')})"
            for i, s in enumerate(sources)
        ]
        context = "\n\n".join(
            f"[{i + 1}] {s['content']}" for i, s in enumerate(sources)
        )

        # Try cloud LLM
        try:
            response = await self._llm_router.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an agricultural advisor for the Eco Nojin platform. "
                            "Answer ONLY from the provided context. Cite sources inline as [1], [2], ... "
                            f"Respond in the language code '{language}'. "
                            "If the context does not answer the question, say so clearly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}",
                    },
                ],
                model_alias="default",
            )
            translated = response.choices[0].message.content
            if translated:
                answer = f"{translated.strip()}\n\n📚 منابع:\n" + "\n".join(source_lines)
                return {
                    "answer": answer,
                    "sources": [s["id"] for s in sources],
                    "language": language,
                    "translated": True,
                }
        except Exception as e:
            logger.info("Cloud LLM not reachable: %s", e)

        # Offline fallback: honest evidence + note.
        top_source = sources[0] if sources else None
        if top_source:
            answer = f"📚 {top_source['metadata'].get('source', 'Source')}: {top_source['metadata'].get('title', 'Document')}\n\n{top_source['content']}" + i18n.t(
                language, "ollama_offline_note"
            )
        else:
            answer = i18n.t(language, "no_answer")
        return {
            "answer": answer,
            "sources": [s["id"] for s in sources],
            "language": language,
            "translated": False,
        }