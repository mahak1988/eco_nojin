"""Retrieval-Augmented Generation engine for agricultural knowledge."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .knowledge_base import KNOWLEDGE_BASE, KnowledgeDocument


class RAGEngine:
    """Simple but effective RAG using TF-IDF vectorization."""

    def __init__(self, documents: list[KnowledgeDocument] | None = None):
        self.documents = documents or KNOWLEDGE_BASE
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),  # Unigrams and bigrams
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


# Singleton instance for reuse
_engine: RAGEngine | None = None


def get_engine() -> RAGEngine:
    """Get or create the singleton RAG engine."""
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
