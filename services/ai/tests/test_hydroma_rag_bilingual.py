"""Bilingual corpus for the Daneshyar RAG: language labels, filter, citations.

The corpus is English *and* Persian, so a Persian question must be answerable
from Persian text rather than only from an embedding similarity. These tests
pin that down:

* (a) the per-language chunk counts are non-zero for both ``en`` and ``fa``,
  reported by :func:`load_corpus` and by :func:`index_stats`;
* (b) the Persian query ``طھط¨ط®غŒط± ظˆ طھط¹ط±ظ‚`` ("evaporation and transpiration")
  returns a passage with a real citation, and the Persian text that carries
  that term is really part of the index;
* (c) ``search(..., lang=...)`` restricts the candidates to one language;
* (d) every citation path still exists on disk — the invariant the whole
  module rests on;
* (e) the hashing fallback (no model download) still answers.

The tests are backend-agnostic where they can be: the assertions hold whether
the index resolves to the local semantic model or to the hashing vectorizer,
so they exercise the corpus contract and not one embedder.
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import pytest

import services.ai.hydroma_rag as rag
from services.ai.hydroma_rag import HASH_EMBED_LABEL

pytestmark = pytest.mark.heavy

_REPO_ROOT = Path(rag.__file__).resolve().parents[2]

#: The Persian query under test: evaporation and transpiration.
PERSIAN_QUERY = "تبخیر و تعرق"

#: The Persian evaporation term the query names, as it appears in the corpus.
PERSIAN_EVAPORATION_TERM = "تبخیر"

_ENV_KEYS = ("HYDROMA_EMBED_MODE", "HYDROMA_EMBED_MODEL")


def _clear_env() -> None:
    for key in _ENV_KEYS:
        os.environ.pop(key, None)


def _reset_index() -> None:
    """Force the next build to re-resolve the backend (model is kept loaded)."""
    rag._INDEX = None
    rag.reset_embedding_backend()


def _assert_real_citation(hit: dict) -> None:
    citation = hit["citation"]
    assert citation["reference"], "every chunk carries a reference string"
    src = citation["source_file"]
    assert src, "every chunk names its source file"
    assert (_REPO_ROOT / src).exists(), f"citation points at a real file: {src}"


@pytest.fixture()
def default_index() -> dict:
    """Build the index with whatever backend resolves here; restore after."""
    _clear_env()
    _reset_index()
    info = rag.build_index(force=True)
    assert info["chunks"] > 0
    yield info
    _reset_index()
    _clear_env()


@pytest.fixture()
def hashing_index() -> None:
    """Build the index with the documented hashing vectorizer."""
    _clear_env()
    os.environ["HYDROMA_EMBED_MODE"] = "hashing"
    _reset_index()
    info = rag.build_index(force=True)
    assert info["embedder"]["label"] == HASH_EMBED_LABEL
    yield info
    _reset_index()
    _clear_env()


# ---------------------------------------------------------------------------
# (a) and (d) the corpus really is bilingual, and every chunk is citable
# ---------------------------------------------------------------------------
def test_corpus_reports_both_languages_with_nonzero_counts():
    corpus = rag.load_corpus()
    counts = Counter(chunk["language"] for chunk in corpus)

    assert counts["en"] > 0, f"English chunks expected, got {dict(counts)}"
    assert counts["fa"] > 0, f"Persian chunks expected, got {dict(counts)}"
    for chunk in corpus:
        assert chunk["language"] in {"en", "fa"}, (
            f"unknown language label {chunk['language']!r}"
        )
        assert chunk["model_id"], "every chunk carries a model_id"
        assert chunk["reference"], "every chunk carries a reference string"
        assert chunk["source_file"], "every chunk names its source file"
        assert (_REPO_ROOT / chunk["source_file"]).exists(), (
            f"citation points at a real file: {chunk['source_file']}"
        )


def test_index_stats_reports_per_language_counts(default_index):
    stats = rag.index_stats()
    counts = stats["languages"]

    assert counts.get("en", 0) > 0, f"English chunks expected, got {counts}"
    assert counts.get("fa", 0) > 0, f"Persian chunks expected, got {counts}"
    assert sum(counts.values()) == stats["chunks"], (
        "the per-language counts must account for every indexed chunk"
    )
    assert counts == default_index["languages"], (
        "index_stats must mirror the build metadata"
    )
    assert stats["available"] is True


def test_persian_prose_carrying_the_query_term_is_indexed():
    """The Persian text the query names is in the corpus, not just the model.

    This is the text-level half of the bilingual claim: before the Persian
    model reference was indexed, a Persian query could only be embedded — no
    indexed passage shared a word with it.
    """
    corpus = rag.load_corpus()
    hits = [
        chunk
        for chunk in corpus
        if chunk["language"] == "fa" and PERSIAN_EVAPORATION_TERM in chunk["text"]
    ]
    assert hits, (
        "the corpus must index Persian prose that names evaporation, the "
        f"subject of the query {PERSIAN_QUERY!r}"
    )
    for chunk in hits:
        _assert_real_citation(
            {
                "citation": {
                    "reference": chunk["reference"],
                    "source_file": chunk["source_file"],
                }
            }
        )


# ---------------------------------------------------------------------------
# (b) a Persian query answers with a real citation
# ---------------------------------------------------------------------------
def test_persian_query_returns_a_real_citation(default_index):
    hits = rag.search(PERSIAN_QUERY, k=5)
    assert hits, "a Persian query must return passages"
    for hit in hits:
        _assert_real_citation(hit)
        assert hit["embedder"], "every hit must state its embedder"

    # Restricted to Persian, the same query answers from Persian text: the
    # corpus's Persian reference is what is being searched.
    fa_hits = rag.search(PERSIAN_QUERY, k=5, lang="fa")
    assert fa_hits, "the Persian half of the corpus must answer a Persian query"
    for hit in fa_hits:
        assert hit["language"] == "fa"
        _assert_real_citation(hit)
    assert {hit["source_file"] for hit in fa_hits} <= {
        rag._rel(rag._MODEL_REFERENCE_FA)
    }, "the fa filter searches the Persian model reference"


# ---------------------------------------------------------------------------
# (c) the language filter works
# ---------------------------------------------------------------------------
def test_lang_filter_restricts_results_to_one_language(default_index):
    english_hits = rag.search("penman monteith reference evapotranspiration", k=5,
                              lang="en")
    persian_hits = rag.search(PERSIAN_QUERY, k=5, lang="fa")

    assert english_hits, "an English query must answer from English chunks"
    assert persian_hits, "a Persian query must answer from Persian chunks"
    for hit in english_hits:
        assert hit["language"] == "en"
        _assert_real_citation(hit)
    for hit in persian_hits:
        assert hit["language"] == "fa"
        _assert_real_citation(hit)

    # The two halves of the corpus are not the same passages.
    assert {hit["model_id"] for hit in english_hits} != {
        hit["model_id"] for hit in persian_hits
    }


def test_lang_filter_with_no_such_language_returns_nothing(default_index):
    assert rag.search(PERSIAN_QUERY, k=5, lang="de") == []


def test_unindexed_language_returns_nothing_not_other_languages(hashing_index):
    """A language filter must not fall back to the other language's chunks."""
    hits = rag.search("evapotranspiration", k=5, lang="fa")
    for hit in hits:
        assert hit["language"] == "fa", "the fa filter must not return en chunks"


# ---------------------------------------------------------------------------
# (e) the hashing fallback still answers, bilingual corpus and all
# ---------------------------------------------------------------------------
def test_hashing_fallback_answers_persian_and_english_queries(hashing_index):
    for query in (PERSIAN_QUERY, "FAO-56 reference evapotranspiration",
                  "soil erosion rainfall RUSLE"):
        hits = rag.search(query, k=5)
        assert hits, f"the hashing fallback must still answer {query!r}"
        for hit in hits:
            assert hit["embedder"] == HASH_EMBED_LABEL
            _assert_real_citation(hit)


def test_hashing_vectorizer_hashes_unicode_words():
    """A Persian query hashes into the vector space, not into the zero vector.

    The fallback is lexical, so its tokeniser must read Persian words as words:
    with an ASCII-only token regex a Persian query would hash to the zero
    vector and could never match any Persian passage.
    """
    vector = rag._hash_embed(PERSIAN_QUERY)
    assert any(vector), "a Persian query must hash to a non-zero vector"

    norm = sum(value * value for value in vector) ** 0.5
    assert norm == pytest.approx(1.0), "the embedding is unit length"
