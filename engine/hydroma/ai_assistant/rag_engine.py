"""Retrieval-Augmented Generation engine for agricultural knowledge."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .knowledge_base import (
    KNOWLEDGE_BASE,
    KNOWLEDGE_BASE_FA,
    KNOWLEDGE_BASE_AR,
    KnowledgeDocument,
)

# Per-language stop words and corpora
_LANG_CORPUS: dict[str, tuple[list[KnowledgeDocument], str]] = {
    "en": (KNOWLEDGE_BASE, "english"),
    "fa": (KNOWLEDGE_BASE_FA, "english"),  # Farsi; sklearn has no Farsi stop words yet
    "ar": (KNOWLEDGE_BASE_AR, "english"),  # Arabic; sklearn has no Arabic stop words yet
}

VALID_LANGS = frozenset(_LANG_CORPUS.keys())


class RAGEngine:
    """Multilingual RAG using TF-IDF vectorization.

    Supports English (en), Persian (fa), and Arabic (ar) corpora.
    """

    def __init__(
        self,
        documents: list[KnowledgeDocument] | None = None,
        lang: str = "en",
    ):
        if documents is not None:
            self.documents = documents
            self.lang = "en"
            stop = "english"
        else:
            if lang not in _LANG_CORPUS:
                raise ValueError(f"Unsupported language: {lang}. Valid: {sorted(_LANG_CORPUS)}")
            self.documents, stop = _LANG_CORPUS[lang]
            self.lang = lang

        self.vectorizer = TfidfVectorizer(
            stop_words=stop,
            max_features=5000,
            ngram_range=(1, 2),
        )
        self._fit()

    def _fit(self) -> None:
        """Build the TF-IDF matrix from knowledge documents."""
        corpus = [doc.content for doc in self.documents]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3) -> list[tuple[KnowledgeDocument, float]]:
        """Retrieve top-k most relevant documents for a query.

        Returns list of (document, similarity_score) tuples.
        """
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.05:  # Minimum relevance threshold
                results.append((self.documents[idx], float(similarities[idx])))

        return results

    def generate_response(self, query: str) -> dict:
        """Generate a complete response with retrieved context.

        Returns dict with: query, answer, sources, confidence
        """
        retrieved = self.retrieve(query, top_k=3)

        if not retrieved:
            return {
                "query": query,
                "answer": "I don't have specific guidance on this topic yet. "
                "Please consult a local agricultural extension officer.",
                "sources": [],
                "confidence": 0.0,
            }

        # Build answer from top document + summaries of others
        top_doc, top_score = retrieved[0]

        # Format response
        answer_parts = [f"**Based on {top_doc.source}:**", "", top_doc.content]

        if len(retrieved) > 1:
            answer_parts.append("")
            answer_parts.append("**Additional relevant guidance:**")
            for doc, _score in retrieved[1:]:
                answer_parts.append(f"• {doc.title} ({doc.source})")

        return {
            "query": query,
            "answer": "\n".join(answer_parts),
            "sources": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "category": doc.category,
                    "relevance": round(score, 3),
                }
                for doc, score in retrieved
            ],
            "confidence": round(top_score, 3),
        }


# Singleton instances for reuse, one per language
_engines: dict[str, RAGEngine] = {}


def get_engine(lang: str = "en") -> RAGEngine:
    """Get or create a singleton RAG engine for the given language."""
    if lang not in _engines:
        _engines[lang] = RAGEngine(lang=lang)
    return _engines[lang]


def supported_languages() -> list[str]:
    """Return list of supported RAG languages."""
    return sorted(_LANG_CORPUS.keys())
