"""Real local semantic embeddings for the Daneshyar RAG, plus honest fallback.

Covers tasks 1–3 of the "upgrade the index embedder" work:

* (a) when the local sentence-transformers model can be downloaded, the index
  is built with it and a *paraphrase* query — one that shares no meaningful
  token with the target reference — retrieves the right model card with a
  citation pointing at a file that exists;
* (b) when it cannot (offline machine, blocked mirror) the tests skip with a
  documented reason, and a second test proves the hashing vectorizer still
  answers with real citations;
* (c) the ``embedder`` label is always present in search metadata and always
  states which vector space produced the ranking;
* (d) :class:`LocalSTEmbedder` raises a *typed* error naming the env var and
  the model id instead of silently degrading.

Honest limitation, asserted rather than hidden: the corpus chunk text is built
from the ``scientific_references`` cells of the model cards, which are English
bibliographic strings. A Persian query therefore *can* be embedded (the model is
multilingual) but cannot be asserted to reach a specific card, because the
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import services.ai.hydroma_rag as rag
from services.ai.embedding_service import (
    DEFAULT_LOCAL_EMBED_MODEL,
    LOCAL_EMBED_MODEL_ENV,
    LocalEmbeddingError,
    LocalSTEmbedder,
)
from services.ai.hydroma_rag import HASH_EMBED_LABEL

pytestmark = pytest.mark.heavy

_REPO_ROOT = Path(rag.__file__).resolve().parents[2]

#: Env vars introduced by the local-embedding work. They are always removed on
#: teardown so the module never leaks state into other test files.
_ENV_KEYS = ("HYDROMA_EMBED_MODE", "HYDROMA_EMBED_MODEL")


def _clear_env() -> None:
    for key in _ENV_KEYS:
        os.environ.pop(key, None)


def _reset_index() -> None:
    """Force the next build to re-resolve the backend (model is kept loaded)."""
    rag._INDEX = None
    rag.reset_embedding_backend()


def _full_reset() -> None:
    """Also drop the loaded model — used when a load failure is simulated."""
    rag._INDEX = None
    rag.reset_local_embedder()


_AVAILABILITY: tuple[bool, str] | None = None


def _local_model_available() -> tuple[bool, str]:
    """Try to load the default local model once; report ``(ok, detail)``.

    Loading triggers the one-off lazy download from huggingface.co, so a
    machine with no outbound access (and no warm cache) reports ``False``.
    The result and the loaded model are cached, so this is paid for once.
    """
    global _AVAILABILITY
    if _AVAILABILITY is None:
        try:
            embedder = rag.local_embedder()
            _AVAILABILITY = (True, f"{embedder.model_name} (dim={embedder.dim})")
        except Exception as exc:  # noqa: BLE001 - any failure means unavailable
            _AVAILABILITY = (False, f"{type(exc).__name__}: {exc}")
    return _AVAILABILITY


def _skip_reason(detail: str) -> str:
    return (
        f"local sentence-transformers model {DEFAULT_LOCAL_EMBED_MODEL!r} is not "
        "cached and huggingface.co is unreachable, so the semantic-embedding "
        f"tests cannot run here ({detail}). The hashing-fallback tests in this "
        "module still run and still assert real citations."
    )


# ---------------------------------------------------------------------------
# (b) the documented skip point
# ---------------------------------------------------------------------------
def test_semantic_tests_skip_when_local_model_cannot_be_downloaded():
    """Skip-guard: the semantic tests need the local model, offline they skip.

    On a machine that can reach huggingface.co this test passes (it is the
    documented reason the semantic tests below are allowed to run). On a
    machine that cannot, it skips with that reason, and the tests built on
    :func:`semantic_index` skip with it too — while the hashing-fallback tests
    keep running and keep asserting real citations.
    """
    available, detail = _local_model_available()
    if not available:
        pytest.skip(_skip_reason(detail))
    assert detail.startswith(DEFAULT_LOCAL_EMBED_MODEL)


@pytest.fixture(scope="module")
def semantic_index() -> dict:
    """Build the corpus index with the real local semantic model.

    Skips (with the documented reason) when the model cannot be obtained.
    Yields the build metadata; restores a clean module state on teardown.
    """
    _clear_env()
    available, detail = _local_model_available()
    if not available:
        pytest.skip(_skip_reason(detail))
    info = rag.build_index(force=True)
    label = info["embedder"]["label"]
    assert label.startswith("sentence-transformers:"), (
        f"semantic_index requires the semantic model, got {label!r} "
        f"({info['embedder'].get('reason', 'no reason')})"
    )
    yield info
    _reset_index()


@pytest.fixture()
def hashing_index() -> dict:
    """Build the corpus index with the documented hashing vectorizer."""
    _clear_env()
    os.environ["HYDROMA_EMBED_MODE"] = "hashing"
    _reset_index()
    info = rag.build_index(force=True)
    assert info["embedder"]["label"] == HASH_EMBED_LABEL
    yield info
    _reset_index()
    _clear_env()


# ---------------------------------------------------------------------------
# (a) semantic retrieval reaches the right card with its citation
# ---------------------------------------------------------------------------
def test_paraphrase_query_retrieves_right_card_with_citation(semantic_index):
    """A paraphrase with no token overlap must still reach the right card.

    ``CANON-006`` is van Genuchten's soil water-retention reference. The query
    below never uses "van Genuchten", "retention", "equation" or any word from
    that reference, so a hashing vectorizer (pure token matching) cannot rank
    it first while the semantic model does.
    """
    assert semantic_index["chunks"] >= 30

    hits = rag.search("water held in porous underground layers", k=5)
    assert hits, "a semantic query over the scientific corpus must return hits"

    top = hits[0]
    assert top["model_id"] == "CANON-006", (
        f"expected the van Genuchten card first, got {top['model_id']!r}"
    )
    citation = top["citation"]
    assert citation["reference"], "the top hit carries a reference string"
    src = citation["source_file"]
    assert src and (_REPO_ROOT / src).exists(), f"citation points at a real file: {src}"

    for hit in hits:
        assert hit["citation"]["reference"]
        assert (_REPO_ROOT / hit["citation"]["source_file"]).exists()


def test_penman_monteith_query_retrieves_fao56_card_with_citation(semantic_index):
    """The documented Penman-Monteith query reaches an FAO-56 / ET card."""
    hits = rag.search("penman monteith evapotranspiration", k=5)
    assert hits
    found = {h["model_id"] for h in hits}
    assert found & {"S-007", "CANON-001"}, (
        f"expected the Penman-Monteith ET0 card among the hits, got {found}"
    )
    for hit in hits:
        assert hit["citation"]["reference"]
        assert (_REPO_ROOT / hit["citation"]["source_file"]).exists()


def test_semantic_model_ranks_paraphrase_above_hashing(semantic_index):
    """The upgrade is real: hashing cannot rank the paraphrased card first.

    Both backends rank the *identical* query, so a silent regression to the
    lexical vector space fails this test.
    """
    query = "water held in porous underground layers"

    semantic_top = rag.search(query, k=5)[0]
    assert semantic_top["model_id"] == "CANON-006"
    assert semantic_top["embedder"].startswith("sentence-transformers:")

    try:
        os.environ["HYDROMA_EMBED_MODE"] = "hashing"
        _reset_index()
        rag.build_index(force=True)
        hashing_top = rag.search(query, k=5)[0]
    finally:
        _clear_env()
        _reset_index()  # drop the hashing backend so later tests re-resolve

    assert hashing_top["embedder"] == HASH_EMBED_LABEL
    assert hashing_top["model_id"] != "CANON-006", (
        "hashing unexpectedly matched the paraphrase first — the quality claim of "
        "the semantic upgrade needs re-checking"
    )


def test_persian_query_is_embedded_without_error(semantic_index):
    """The multilingual model accepts Persian queries and answers with citations.

    The indexed corpus text is English-only (bibliographic references), so the
    query is embedded but cannot be asserted to reach a specific card. What is
    asserted is that it still returns real citation-carrying passages instead of
    erroring or returning nothing.
    """
    hits = rag.search("تبخیر و تعرق", k=3)
    assert hits, "a Persian query must still return passages"
    for hit in hits:
        assert hit["citation"]["reference"]
        assert (_REPO_ROOT / hit["citation"]["source_file"]).exists()
        assert hit["embedder"].startswith("sentence-transformers:")


# ---------------------------------------------------------------------------
# (b) the hashing fallback still answers with real citations
# ---------------------------------------------------------------------------
def test_hashing_fallback_returns_real_citations_when_model_unavailable():
    """A real model-load failure degrades to the vectorizer, still citing sources.

    Simulates "the model cannot be downloaded" by pointing ``HYDROMA_EMBED_MODEL``
    at a repository that cannot be resolved — an actual failed fetch, not a mock.
    The index must still answer with citations that point at files which exist.
    """
    _clear_env()
    os.environ["HYDROMA_EMBED_MODEL"] = "sentence-transformers/__hydroma_missing__"
    try:
        _full_reset()
        info = rag.build_index(force=True)
        assert info["embedder"]["label"] == HASH_EMBED_LABEL
        assert info["embedder"]["backend"] == "hashing_vectorizer"
        assert info["embedder"]["reason"], "the fallback must record why it degraded"
        assert info["backend"] in {"qdrant-local-memory", "json-store"}

        hits = rag.search("FAO-56 reference evapotranspiration", k=5)
        assert hits, "the hashing fallback must still return hits"
        for hit in hits:
            assert hit["embedder"] == HASH_EMBED_LABEL
            assert hit["citation"]["reference"]
            assert (_REPO_ROOT / hit["citation"]["source_file"]).exists()
    finally:
        _full_reset()
        _clear_env()


def test_hashing_mode_env_forces_vectorizer(hashing_index):
    """``HYDROMA_EMBED_MODE=hashing`` forces the documented fallback."""
    expected = "hashing vectorizer forced by HYDROMA_EMBED_MODE=hashing"
    assert hashing_index["embedder"]["reason"] == expected
    hits = rag.search("soil erosion rainfall RUSLE", k=3)
    assert hits
    for hit in hits:
        assert hit["embedder"] == HASH_EMBED_LABEL


# ---------------------------------------------------------------------------
# (c) the embedder label is always present in search metadata
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("index_fixture", ["semantic_index", "hashing_index"])
def test_embedder_label_always_present_in_search_metadata(request, index_fixture):
    """Whatever the backend, every hit and every stats view names the embedder.

    This is the honesty contract: a caller can never mistake lexical hashing for
    semantic retrieval, because the label travels with the ranking.
    """
    request.getfixturevalue(index_fixture)

    hits = rag.search("evapotranspiration Penman Monteith reference", k=5)
    assert hits
    for hit in hits:
        assert hit["embedder"], "every search result must state its embedder"
        assert hit["embedder"].startswith("sentence-transformers:") or (
            hit["embedder"] == HASH_EMBED_LABEL
        )

    for view in (rag.build_index(), rag.index_stats()):
        assert view["embedder"]["label"], "index metadata must name the embedder"
        assert view["embedder"]["backend"] in {
            "sentence-transformers",
            "hashing_vectorizer",
        }


def test_index_stats_reports_resolved_backend(hashing_index):
    """``index_stats`` mirrors ``build_index`` and stays available."""
    stats = rag.index_stats()
    assert stats["available"] is True
    assert stats["chunks"] >= 30
    assert stats["backend"] in {"qdrant-local-memory", "json-store"}
    assert stats["embedder"]["label"] == HASH_EMBED_LABEL
    assert stats["corpus_sources"]["cards_dir"] is not None


# ---------------------------------------------------------------------------
# (d) LocalSTEmbedder error path is typed and actionable
# ---------------------------------------------------------------------------
def test_local_st_embedder_error_names_env_var_and_model():
    """A bad model id raises ``LocalEmbeddingError`` — never a silent swap.

    The message must name both ``HYDROMA_EMBED_MODEL`` and the model id, so the
    operator knows exactly what to change.
    """
    embedder = LocalSTEmbedder("sentence-transformers/__hydroma_no_such_model__")
    with pytest.raises(LocalEmbeddingError) as excinfo:
        _dim = embedder.dim  # triggers the lazy download
    message = str(excinfo.value)
    assert LOCAL_EMBED_MODEL_ENV in message
    assert "sentence-transformers/__hydroma_no_such_model__" in message


def test_local_st_embedder_env_override_selects_model():
    """``HYDROMA_EMBED_MODEL`` overrides the default model id."""
    _clear_env()
    try:
        os.environ[LOCAL_EMBED_MODEL_ENV] = "custom/override-model"
        assert LocalSTEmbedder().model_name == "custom/override-model"
        assert LocalSTEmbedder().label == "sentence-transformers:custom/override-model"
        # An explicit argument still wins over the environment.
        assert LocalSTEmbedder("explicit/model").model_name == "explicit/model"
    finally:
        _clear_env()


def test_local_st_embedder_embed_rejects_empty_batch_without_loading():
    """An empty batch short-circuits without triggering a model download."""
    embedder = LocalSTEmbedder()
    assert embedder.embed([]) == []
    assert embedder._model is None, "an empty batch must not load the model"
