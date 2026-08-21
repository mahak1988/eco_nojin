"""Tests for AI Assistant RAG engine."""

from engine.hydroma.ai_assistant.rag_engine import RAGEngine, get_engine


def test_rag_retrieves_compost_info():
    """Verify RAG retrieves compost-related docs for compost query."""
    engine = RAGEngine()
    results = engine.retrieve("How to make compost with correct C/N ratio?", top_k=2)

    assert len(results) > 0
    top_doc, score = results[0]
    assert "compost" in top_doc.content.lower() or "c/n" in top_doc.content.lower()
    assert score > 0.1


def test_rag_retrieves_water_info():
    """Verify RAG retrieves water/irrigation docs using specific ET0 terms."""
    engine = RAGEngine()
    # Use specific ET0-related terms to disambiguate from IPM doc
    results = engine.retrieve("Hargreaves-Samani ET0 evapotranspiration calculation", top_k=3)

    assert len(results) > 0
    # Check that at least one top result is about water/ET0
    found_water_doc = any(
        "et0" in doc.content.lower() or "evapotranspiration" in doc.content.lower()
        for doc, _ in results
    )
    assert found_water_doc, (
        f"Expected water/ET0 doc in results, got: {[d.title for d, _ in results]}"
    )


def test_rag_retrieves_biochar_info():
    """Verify RAG retrieves biochar docs."""
    engine = RAGEngine()
    results = engine.retrieve("biochar application rate for sandy soil", top_k=2)

    assert len(results) > 0
    top_doc, _ = results[0]
    assert "biochar" in top_doc.content.lower()


def test_rag_retrieves_erosion_info():
    """Verify RAG retrieves erosion/RUSLE docs."""
    engine = RAGEngine()
    results = engine.retrieve("RUSLE soil loss equation factors", top_k=2)

    assert len(results) > 0
    top_doc, _ = results[0]
    assert "rusle" in top_doc.content.lower() or "erosion" in top_doc.content.lower()


def test_rag_generates_response():
    """Verify response generation structure."""
    engine = RAGEngine()
    response = engine.generate_response("Tell me about biochar for sandy soils")

    assert "query" in response
    assert "answer" in response
    assert "sources" in response
    assert "confidence" in response
    assert len(response["sources"]) > 0
    assert response["confidence"] > 0


def test_rag_handles_unrelated_query():
    """Verify graceful handling of off-topic queries."""
    engine = RAGEngine()
    response = engine.generate_response("xyzabc nonsense query")

    assert "answer" in response
    assert isinstance(response["sources"], list)


def test_singleton_engine():
    """Verify singleton pattern works correctly."""
    engine1 = get_engine()
    engine2 = get_engine()
    assert engine1 is engine2
