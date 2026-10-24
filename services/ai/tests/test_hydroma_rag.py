"""Daneshyar scientific-corpus RAG + QUDT unit mapping (tasks 3 & 4).

Verifies the offline index is built from the project's *real* corpus and that
every search result carries a citation that points at a file which exists — the
index never fabricates a source — and that the QUDT mapping only emits
well-formed qudt.org URIs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import services.ai.hydroma_rag as rag
from services.ai.hydroma_rag import QUDT_BASE_URI, QUDT_UNITS

pytestmark = pytest.mark.heavy

_REPO_ROOT = Path(rag.__file__).resolve().parents[2]


def test_corpus_loads_real_sources():
    corpus = rag.load_corpus()
    assert len(corpus) >= 30, "corpus must contain many real references"
    kinds = {c["kind"] for c in corpus}
    # The model cards and the prose they are built from are always present.
    # The other kinds (engine references, catalog entries, research
    # definitions) depend on which source trees are present in this
    # environment, so they are asserted by kind, not by count.
    assert "model_card" in kinds
    assert "prose" in kinds
    assert kinds <= {
        "prose",
        "model_card",
        "engine_model_reference",
        "catalog",
        "research_definition",
        "model_reference_fa",
    }
    for chunk in corpus:
        assert chunk["reference"], "every chunk carries a reference string"
        src = chunk["source_file"]
        assert src and (_REPO_ROOT / src).exists(), f"real source expected: {src}"


def test_build_and_search_returns_citations_to_real_files():
    info = rag.build_index(force=True)
    assert info["chunks"] >= 30
    assert info["backend"] in {"qdrant-local-memory", "json-store"}
    results = rag.search("Penman Monteith reference evapotranspiration FAO-56", k=5)
    assert results, "a query over the scientific corpus must return hits"
    for hit in results:
        citation = hit["citation"]
        assert citation["reference"]
        src = citation["source_file"]
        assert src and (_REPO_ROOT / src).exists(), f"citation points at a real file: {src}"


def test_search_is_deterministic():
    a = rag.search("soil erosion RUSLE rainfall", k=5)
    b = rag.search("soil erosion RUSLE rainfall", k=5)
    assert [h["source_file"] + h["reference"] for h in a] == [
        h["source_file"] + h["reference"] for h in b
    ]


def test_to_qudt_known_examples():
    assert rag.to_qudt("mm") == f"{QUDT_BASE_URI}MilliM"
    assert rag.to_qudt("mm/day") == f"{QUDT_BASE_URI}MilliM-PER-DAY"
    assert rag.to_qudt("m3/day") == f"{QUDT_BASE_URI}CubicM-PER-DAY"
    assert rag.to_qudt("dS/m") == f"{QUDT_BASE_URI}DeciS-PER-M"
    assert rag.to_qudt("not-a-unit") is None


def test_qudt_table_all_valid_uris():
    assert QUDT_UNITS, "QUDT table must not be empty"
    for code, local in QUDT_UNITS.items():
        uri = rag.to_qudt(code)
        assert uri == QUDT_BASE_URI + local
        assert uri.startswith("http://qudt.org/vocab/unit/")


def test_units_in_text_maps_only_present_units():
    uris = rag.units_in_text("Discharge is 3 m3/day; no other unit here")
    assert f"{QUDT_BASE_URI}CubicM-PER-DAY" in uris
    # 'none' should be the exclusive vocabulary
    for uri in uris:
        assert uri.startswith("http://qudt.org/vocab/unit/")


def test_search_returns_empty_for_blank_query():
    assert rag.search("", k=5) == []
    assert rag.search("   ", k=3) == []


def test_json_store_fallback_when_qdrant_unavailable(monkeypatch):
    # qdrant-client is installed here, so force the documented no-qdrant path:
    # build_index must fall back to the JSON vector store and still answer with
    # real citations, never crash, never fabricate.
    class _Unavailable:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("qdrant unavailable (simulated)")

    monkeypatch.setattr(rag, "_QdrantStore", _Unavailable)
    info = rag.build_index(force=True)
    assert info["backend"] == "json-store"

    hits = rag.search("FAO-56 reference evapotranspiration", k=3)
    assert hits
    assert (rag._REPO_ROOT / hits[0]["source_file"]).exists()

    # Reset so later tests rebuild against the real qdrant backend.
    rag._INDEX = None
