"""Local BM25 retrieval over the repository's ``docs/`` corpus.

This augments the on-request natural-language path (``services.ai.nlg``) with
grounded citations. It is deliberately dependency-free and in-process: it runs
inline on a request, so it must not require Qdrant, an embedding model or any
network hop. The networked, vector-backed index remains
``services.ai.unified_rag``; this module is the always-available local floor
under it, not a replacement.

Output contract
---------------
``services.ai.nlg.advise`` reads ``path`` and ``content`` from every hit, so
those two keys are part of this module's interface and must not be renamed.
"""

from __future__ import annotations

import math
import os
import re
import threading
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- retrieval tuning (BM25) ---------------------------------------------
K1 = 1.5
B = 0.75

DEFAULT_ROOTS = "docs"
DEFAULT_MAX_DOCS = 2000
DEFAULT_MAX_FILE_BYTES = 2_000_000
DEFAULT_CHUNK_CHARS = 600

TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst"}

# Arabic-Indic and Extended Arabic-Indic digits -> ASCII
_DIGIT_MAP = {ord(c): str(i % 10) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹")}
# Orthographic variants that would otherwise split one word into two tokens.
# Written as escapes so the table survives any source encoding and so linters
# do not read the Persian letters as ambiguous homoglyphs.
_LETTER_MAP = {
    ord("ي"): "ی",  # ARABIC YEH         -> FARSI YEH
    ord("ى"): "ی",  # ALEF MAKSURA       -> FARSI YEH
    ord("ك"): "ک",  # ARABIC KAF         -> KEHEH
    ord("ة"): "ه",  # TEH MARBUTA        -> HEH
    ord("أ"): "ا",  # ALEF + HAMZA ABOVE -> ALEF
    ord("إ"): "ا",  # ALEF + HAMZA BELOW -> ALEF
    ord("آ"): "ا",  # ALEF WITH MADDA    -> ALEF
    ord("ٱ"): "ا",  # ALEF WASLA         -> ALEF
    ord("ـ"): " ",  # TATWEEL -> space (kashida elongates, it does not join)
    ord("‌"): " ",  # ZERO WIDTH NON-JOINER -> space
}
# Combining marks (harakat) carry no lexical content. The ranges must stay
# narrow: an over-wide range such as U+0656-U+06ED swallows U+06CC (FARSI YEH)
# and U+0645 (MEEM) and silently deletes letters from every Persian word.
_DIACRITICS = re.compile("[\u064b-\u0655\u0670\u06d6-\u06dc\ufe00-\ufe0f]")

# Word characters minus underscore: covers Latin, Persian/Arabic letters, digits
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def normalize(text: str) -> str:
    """Fold a Persian/Arabic or Latin string to a comparable token stream."""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_DIGIT_MAP)
    text = text.translate(_LETTER_MAP)
    text = _DIACRITICS.sub("", text)
    return text.lower()


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalize(text))


@dataclass
class Document:
    """One indexed chunk."""

    path: str
    content: str
    language: str = "fa"
    chunk_index: int = 0
    tokens: list[str] = field(default_factory=list, repr=False)
    frequencies: Counter[str] = field(default_factory=Counter, repr=False)

    def as_hit(self, score: float, rank: int) -> dict[str, Any]:
        """Shape consumed by ``services.ai.nlg``."""
        return {
            "path": self.path,
            "content": self.content,
            "score": round(score, 4),
            "rank": rank,
            "language": self.language,
            "chunk_index": self.chunk_index,
        }


class IndexNotBuilt(RuntimeError):
    """Raised when a search is attempted before any corpus is indexed."""


class RAGIndex:
    """Thread-safe BM25 index over local documents."""

    def __init__(
        self,
        roots: list[str] | None = None,
        max_docs: int = DEFAULT_MAX_DOCS,
        chunk_chars: int = DEFAULT_CHUNK_CHARS,
    ) -> None:
        self.roots = roots if roots is not None else self._roots_from_env()
        self.max_docs = max_docs
        self.chunk_chars = chunk_chars
        self.documents: list[Document] = []
        self.postings: dict[str, list[int]] = {}
        self._avgdl: float = 0.0
        self._built: bool = False
        self._lock = threading.RLock()

    # -- configuration ----------------------------------------------------
    @staticmethod
    def _roots_from_env() -> list[str]:
        raw = os.getenv("RAG_DOC_ROOTS", DEFAULT_ROOTS)
        return [r.strip() for r in raw.replace(";", ",").split(",") if r.strip()]

    # -- corpus discovery -------------------------------------------------
    def _iter_files(self) -> list[Path]:
        project_root = Path(__file__).resolve().parents[2]
        found: list[Path] = []
        for root in self.roots:
            base = Path(root)
            if not base.is_absolute():
                base = project_root / base
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*")):
                if path.suffix.lower() in TEXT_SUFFIXES and path.is_file():
                    found.append(path)
        return found[: self.max_docs]

    @staticmethod
    def _looks_persian(text: str) -> bool:
        persian = sum(1 for ch in text if "؀" <= ch <= "ۿ")
        return persian >= 3

    def _chunks(self, text: str) -> list[str]:
        """Group paragraphs up to ``chunk_chars`` without cutting mid-sentence
        where avoidable."""
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        out: list[str] = []
        current = ""
        for block in blocks:
            if current and len(current) + len(block) + 2 > self.chunk_chars:
                out.append(current)
                current = block
            else:
                current = f"{current}\n\n{block}" if current else block
        if current:
            out.append(current)
        return out

    # -- build ------------------------------------------------------------
    def build(self, force: bool = False) -> int:
        """Index the corpus. Idempotent unless ``force``; returns chunk count.

        Safe to call concurrently with ``search``: an in-flight build that
        finishes after another one started does not publish a partial index,
        because publication happens under the lock in a single assignment.
        """
        with self._lock:
            if self._built and not force:
                return len(self.documents)

        documents: list[Document] = []
        project_root = Path(__file__).resolve().parents[2]
        for file_path in self._iter_files():
            try:
                if file_path.stat().st_size > DEFAULT_MAX_FILE_BYTES:
                    continue
                raw = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            try:
                rel = str(file_path.relative_to(project_root)).replace("\\", "/")
            except ValueError:
                rel = str(file_path).replace("\\", "/")
            for i, chunk in enumerate(self._chunks(raw)):
                tokens = tokenize(chunk)
                if not tokens:
                    continue
                documents.append(
                    Document(
                        path=rel,
                        content=chunk,
                        language="fa" if self._looks_persian(chunk) else "en",
                        chunk_index=i,
                        tokens=tokens,
                        frequencies=Counter(tokens),
                    )
                )

        postings: dict[str, list[int]] = {}
        total_len = 0
        for doc_id, doc in enumerate(documents):
            total_len += len(doc.tokens)
            for term in doc.frequencies:
                postings.setdefault(term, []).append(doc_id)

        with self._lock:
            self.documents = documents
            self.postings = postings
            self._avgdl = (total_len / len(documents)) if documents else 0.0
            self._built = True
        return len(documents)

    @property
    def is_built(self) -> bool:
        with self._lock:
            return self._built

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "built": self._built,
                "documents": len(self.documents),
                "terms": len(self.postings),
                "avg_chunk_tokens": round(self._avgdl, 2),
                "roots": self.roots,
            }

    # -- search -----------------------------------------------------------
    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Rank chunks by BM25. Returns at most ``top_k`` hits.

        Callers are expected to have built the index; ``IndexNotBuilt`` is
        raised otherwise so the caller can decide whether to build or degrade.
        """
        with self._lock:
            if not self._built:
                raise IndexNotBuilt("call index.build() before searching")
            documents = self.documents
            postings = self.postings
            avgdl = self._avgdl

        if not documents or avgdl <= 0:
            return []

        terms = tokenize(query)
        if not terms:
            return []

        n_docs = len(documents)
        scores: dict[int, float] = {}
        for term in set(terms):
            doc_ids = postings.get(term)
            if not doc_ids:
                continue
            idf = math.log(1 + (n_docs - len(doc_ids) + 0.5) / (len(doc_ids) + 0.5))
            for doc_id in doc_ids:
                doc = documents[doc_id]
                freq = doc.frequencies.get(term, 0)
                if not freq:
                    continue
                norm = 1 - B + B * (len(doc.tokens) / avgdl)
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * (
                    freq * (K1 + 1) / (freq + K1 * norm)
                )

        if not scores:
            return []
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        return [documents[doc_id].as_hit(score, i + 1) for i, (doc_id, score) in enumerate(ranked)]


index = RAGIndex()


def build(force: bool = False) -> int:
    """Module-level convenience wrapper around ``index.build()``."""
    return index.build(force=force)


def search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Module-level search that builds lazily on first use.

    ``services.ai.nlg`` calls ``rag.search`` inside a try/except and falls back
    to ``rag.index.build()`` on failure, so both call styles keep working.
    """
    if not index.is_built:
        index.build()
    return index.search(query, top_k=top_k)


def stats() -> dict[str, Any]:
    return index.stats()
