"""Tests for the local BM25 retrieval index (services.ai.rag).

Offline and deterministic: they build against the repository's own docs/
corpus, which is committed, so no network and no fixtures are required.
"""

from __future__ import annotations

import threading

import pytest

from services.ai import rag

MEEM = "م"
FARSI_YEH = "ی"  # FARSI YEH
ARABIC_YEH = "ي"  # ARABIC YEH
KEHEH = "ک"
ARABIC_KEHEH = "ك"
ZWNJ = "‌"  # ZERO WIDTH NON-JOINER
TASHKEEL = "ً"  # FATHTAN
SHAVAD = "شود"
MI = "می"


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------
def test_normalisation_preserves_persian_letters():
    """Regression: an over-wide diacritic range once covered U+0656-U+06ED,
    which contains FARSI YEH (U+06CC) and MEEM (U+0645) and silently deleted
    letters from every Persian word."""
    for word in (MI, SHAVAD, "کشاورزی", "فرسایش", "خیزداری", "رواناب"):
        assert word == rag.normalize(word), f"normalize mangled {word!r}"
        assert word in rag.tokenize(word)


def test_alef_with_madda_folds_to_plain_alef():
    """A -> A is a deliberate equivalence, not letter loss: the madda is an
    orthographic mark on the same letter."""
    assert rag.normalize("آبخیزداری") == "ابخیزداری"
    assert rag.tokenize("آبخیزداری") == ["ابخیزداری"]


def test_normalisation_strips_diacritics_but_keeps_the_letter():
    assert rag.normalize("بَ") == "ب"
    assert rag.normalize(MEEM + TASHKEEL) == MEEM


def test_arabic_and_farsi_letter_forms_are_equivalent():
    assert rag.tokenize(ARABIC_YEH) == rag.tokenize(FARSI_YEH)
    assert rag.tokenize(ARABIC_KEHEH) == rag.tokenize(KEHEH)


def test_zwnj_and_space_are_equivalent():
    assert rag.tokenize(MI + ZWNJ + SHAVAD) == rag.tokenize(MI + " " + SHAVAD)
    assert rag.tokenize(MEEM + ARABIC_YEH + ZWNJ + SHAVAD) == rag.tokenize(MI + " " + SHAVAD)


def test_tatweel_does_not_join_words():
    assert rag.normalize("کـــشاورزی").split() == ["ک", "شاورزی"]


def test_persian_digits_are_folded_to_ascii():
    assert rag.tokenize("۱۴۰۵") == ["1405"]
    assert rag.tokenize("٢٠٢٦") == ["2026"]


def test_tokenize_ignores_case_and_punctuation():
    assert rag.tokenize("Hello, WORLD!") == ["hello", "world"]


# --------------------------------------------------------------------------
# building
# --------------------------------------------------------------------------
def test_build_indexes_the_repository_corpus():
    idx = rag.RAGIndex()
    assert not idx.is_built
    count = idx.build()
    assert count > 0
    assert idx.is_built
    assert idx.stats()["terms"] > 0
    assert idx.stats()["avg_chunk_tokens"] > 0


def test_build_is_idempotent_unless_forced():
    idx = rag.RAGIndex()
    first = idx.build()
    assert idx.build() == first
    assert idx.build(force=True) == first


def test_search_raises_before_build():
    idx = rag.RAGIndex()
    with pytest.raises(rag.IndexNotBuilt):
        idx.search("offline")


def test_missing_corpus_root_degrades_to_empty():
    idx = rag.RAGIndex(roots=["no-such-directory-anywhere"])
    assert idx.build() == 0
    assert idx.search("offline") == []


# --------------------------------------------------------------------------
# searching
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built() -> rag.RAGIndex:
    idx = rag.RAGIndex()
    idx.build()
    return idx


def test_hits_satisfy_the_contract_nlg_consumes(built):
    """services.ai.nlg reads .get("path") and .get("content", "") on each hit."""
    hits = built.search("offline first architecture", top_k=3)
    assert hits
    for hit in hits:
        assert isinstance(hit["path"], str)
        assert hit["path"]
        assert isinstance(hit["content"], str)
        assert hit["content"]
        assert isinstance(hit["score"], float)
    assert [h["rank"] for h in hits] == list(range(1, len(hits) + 1))


def test_results_are_ranked_and_capped_at_top_k(built):
    hits = built.search("security rate limiting", top_k=2)
    assert len(hits) <= 2
    if len(hits) == 2:
        assert hits[0]["score"] >= hits[1]["score"]


def test_search_is_deterministic(built):
    a = built.search("cache invalidation", top_k=5)
    b = built.search("cache invalidation", top_k=5)
    assert [h["path"] for h in a] == [h["path"] for h in b]
    assert [h["score"] for h in a] == [h["score"] for h in b]


def test_relevant_persian_query_returns_persian_documents(built):
    hits = built.search("امنیت و احراز هویت", top_k=3)
    assert hits
    assert any(h["language"] == "fa" or "fa" in h["path"].lower() for h in hits)


def test_unrelated_query_returns_nothing_rather_than_everything(built):
    assert built.search("zzzqqqxyzzy nonexistentterm", top_k=3) == []


def test_empty_query_is_handled(built):
    assert built.search("", top_k=3) == []
    assert built.search("!!! ???", top_k=3) == []


def test_persian_variant_spelling_still_matches(built):
    """A query written with Arabic letter forms must reach Persian documents."""
    arabic_style = "توسعه"  # ARABIC KAF + TAH
    hits = built.search(arabic_style, top_k=3)
    assert hits, "Arabic-form query found nothing"


# --------------------------------------------------------------------------
# concurrency and module surface
# --------------------------------------------------------------------------
def test_concurrent_build_and_search_are_safe():
    idx = rag.RAGIndex()
    errors: list[Exception] = []
    barrier = threading.Barrier(4)

    def builder() -> None:
        try:
            barrier.wait()
            idx.build()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def searcher() -> None:
        try:
            barrier.wait()
            for _ in range(20):
                if idx.is_built:
                    idx.search("offline", top_k=2)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=builder) for _ in range(2)]
    threads += [threading.Thread(target=searcher) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    assert idx.is_built


def test_module_level_search_builds_lazily():
    hits = rag.search("PWA offline", top_k=3)
    assert hits
    assert rag.index.is_built
    assert rag.stats()["documents"] > 0


def test_nlg_advice_still_works_with_rag_present():
    """The NLG path must keep its provider and evidence contract now that the
    optional local index actually resolves."""
    from services.ai.nlg import advise

    out = advise("بندسار برای کاهش رواناب", {"spi": -0.812})
    assert out["provider"] == "local-nlg"
    assert "بندسار" in out["answer"]
    assert out["metrics"]["spi"] == -0.812
    assert len(out["evidence"]) >= 1
