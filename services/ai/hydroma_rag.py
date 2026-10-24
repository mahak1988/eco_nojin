"""Daneshyar scientific-corpus RAG (offline, citation-carrying).

This module builds a vector index over the project's *real* scientific corpus
and answers free-text queries with passages that carry their source citation,
so Daneshyar (the knowledge assistant) can never present a claim without the
file and reference it came from.

Corpus (each chunk keeps ``{source_file, model_id, reference, doi, kind,
language}`` metadata):

* ``engine/models/cards/*.md`` — the model cards: the ``scientific_references``
  cell *and* the card's own prose (title plus every other field cell);
* ``engine/hydroma/models/*.py`` — the ``REFERENCES`` dicts of the index models
  (e.g. ``HYRUE.REFERENCES``, ``EPIA.REFERENCES``), read as *source text* via
  AST — this module never imports ``engine.*`` (INV-003 / AI isolation);
* ``reports/hydroma/HYDROMA_MODEL_CATALOG.md`` — the model-card catalog;
* the ``research_definition`` of every formula record in
  ``engine/hydroma/formulas/catalog.py``, read from the file and symbol that
  field names;
* ``engine/hydroma/models/MODEL_REFERENCE_FA.md`` — the Persian model reference,
  one chunk per model section.

Because the corpus is bilingual, every chunk carries the ``language`` its text
was labelled with by script detection (``"fa"`` for Arabic script, ``"en"``
otherwise). :func:`search` takes an optional ``lang`` so a Persian question
answers from Persian text rather than only from an embedding similarity, and
:func:`index_stats` reports the per-language chunk counts.

Vector store
------------
Primary backend is Qdrant in LOCAL in-memory mode (``qdrant-client``, no server,
free). If ``qdrant-client`` is unavailable, a plain JSON vector store under
``data/rag/`` is used instead. Neither backend ever raises out of the public
functions: a missing dependency or unreadable corpus degrades to an empty
result, never a fabricated source.

Embeddings
----------
The engine modules are read as text (not imported), so the embedder is a local
one. The primary backend is a small multilingual ``sentence-transformers``
model (default ``sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2``,
overridable with ``HYDROMA_EMBED_MODEL``) which gives real *semantic* vectors
over the mixed English/Persian corpus. That model is loaded lazily and needs a
one-off download, so when it cannot be obtained (offline machine, blocked
mirror) this module degrades to the deterministic hashing vectorizer.

The fallback is explicit, never silent: :func:`embedder_info` and every search
result carry an ``embedder`` label that is either
``sentence-transformers:<model-id>`` or ``hashing-fallback``, and the fallback
Info records the load failure verbatim. ``HYDROMA_EMBED_MODE=hashing`` forces
the vectorizer. ``llama-index`` is not used.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # typing only — no runtime import of the embedding service
    from services.ai.embedding_service import LocalSTEmbedder

# ---------------------------------------------------------------------------
# Locating the corpus. The repo root is two levels above this file
# (services/ai/hydroma_rag.py -> <root>). Overridable via env for tests.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = Path(os.getenv("HYDROMA_RAG_ENGINE", _REPO_ROOT / "engine"))
CARDS_DIR = ENGINE_DIR / "models" / "cards"
MODELS_DIR = ENGINE_DIR / "hydroma" / "models"
CATALOG_MD = Path(
    os.getenv(
        "HYDROMA_RAG_CATALOG",
        _REPO_ROOT / "reports" / "hydroma" / "HYDROMA_MODEL_CATALOG.md",
    )
)

#: JSON-fallback store location (only used when qdrant-client is missing).
_DATA_RAG_DIR = _REPO_ROOT / "data" / "rag"

COLLECTION = "hydroma_scientific_corpus"

_ID_PATTERN = re.compile(r"^(CANON-\d+|S-\d+|[A-Z]{2,}-\d+)$")


# ---------------------------------------------------------------------------
# QUDT unit mapping (task 4)
# ---------------------------------------------------------------------------
#: Base URI for the QUDT units vocabulary, per the task's examples and
#: https://www.qudt.org/doc/DOC_VOCAB-UNITS.html
QUDT_BASE_URI = "http://qudt.org/vocab/unit/"

#: Engine quantity/unit code -> QUDT vocabulary local name. Only well-established
#: QUDT units are listed; an unknown code maps to ``None`` rather than a guessed
#: URI. Each value is a real member of the QUDT ``unit`` vocabulary.
QUDT_UNITS: dict[str, str] = {
    # length
    "m": "M",
    "mm": "MilliM",
    "cm": "CentiM",
    "km": "KiloM",
    "um": "MicroM",
    # rate / velocity (depth per time)
    "m/s": "M-PER-SEC",
    "m/day": "M-PER-DAY",
    "km/day": "KiloM-PER-DAY",
    "mm/hr": "MilliM-PER-HR",
    "mm/day": "MilliM-PER-DAY",
    "mm/yr": "MilliM-PER-YR",
    # gradient
    "mm/m": "MilliM-PER-M",
    # volume and volumetric flow
    "m3": "CubicM",
    "m3/s": "CubicM-PER-SEC",
    "m3/day": "CubicM-PER-DAY",
    # electrical conductivity / salinity
    "S/m": "S-PER-M",
    "S/cm": "S-PER-CentiM",
    "dS/m": "DeciS-PER-M",
    "mS/cm": "MilliS-PER-CentiM",
    # time
    "day": "DAY",
    "yr": "YR",
    # area
    "m2": "M2",
}

#: Longest-first so multi-token codes (``mm/day``) win over single tokens (``mm``).
_UNIT_TOKENS = sorted(QUDT_UNITS, key=len, reverse=True)
_UNIT_SCAN = re.compile(
    r"(?<![A-Za-z0-9./-])(" + "|".join(re.escape(t) for t in _UNIT_TOKENS) + r")(?![A-Za-z0-9])"
)


def to_qudt(code: str) -> str | None:
    """Return the full QUDT URI for an engine unit ``code`` or ``None``.

    e.g. ``to_qudt("mm/day")`` -> ``http://qudt.org/vocab/unit/MilliM-PER-DAY``.
    """
    local = QUDT_UNITS.get(code.strip())
    return f"{QUDT_BASE_URI}{local}" if local else None


def units_in_text(text: str) -> list[str]:
    """Return the sorted QUDT URIs for every recognised unit token in ``text``.

    Only units literally present in the text are mapped, so the machine-readable
    units attached to an answer reflect what the source actually states.
    """
    found = {QUDT_UNITS[m.group(1)] for m in _UNIT_SCAN.finditer(text)}
    return sorted(f"{QUDT_BASE_URI}{u}" for u in found)


# ---------------------------------------------------------------------------
# Embedding backend: real local semantic model, honest hashing fallback
# ---------------------------------------------------------------------------
#: Label published when the deterministic feature-hashing vectorizer is in use.
#: It names a lexical (bag-of-tokens) vector space, not a semantic one, so a
#: caller can never mistake hashing retrieval for semantic retrieval.
HASH_EMBED_LABEL = "hashing-fallback"

#: Env switch: ``auto`` (default) prefers the local semantic model and degrades
#: to the hashing vectorizer with an explicit label; ``hashing`` forces it.
EMBED_MODE_ENV = "HYDROMA_EMBED_MODE"

#: Width of the hashing vectorizer, kept as the offline default and as the
#: fallback dimension whenever the semantic model is unavailable.
_EMBED_DIM = 384

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,;]+")


def _hash_embed(text: str) -> list[float]:
    """Feature-hashing embedding: deterministic, no model download, ~O(len).

    Tokens are Unicode word runs (letters and digits, underscore excluded),
    not ASCII-only runs: the corpus is bilingual and a Persian chunk must
    hash into the same vector space a Persian query is hashed into. For
    ASCII-only text the tokenisation is unchanged.
    """
    vec = [0.0] * _EMBED_DIM
    for token in re.findall(r"[^\W_]+", text.lower()):
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        as_int = int(digest, 16)
        idx = as_int % _EMBED_DIM
        vec[idx] += 1.0 if (as_int >> 40) & 1 else -1.0
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0.0:
        vec = [v / norm for v in vec]
    return vec


class _EmbeddingBackend:
    """Process-wide embedder with an explicit, labelled degradation path.

    The local ``sentence-transformers`` model is the primary backend — real
    semantic vectors over the English+Persian corpus. It is loaded lazily and
    needs a one-off download, so when it cannot be obtained the failure reason
    is recorded verbatim and the deterministic hashing vectorizer is used
    instead, published under :data:`HASH_EMBED_LABEL`. Search quality can
    therefore never degrade *silently*: the label is on every index build and
    every search result.

    ``HYDROMA_EMBED_MODE=hashing`` forces the vectorizer; ``auto`` (the
    default) tries the semantic model first.
    """

    def __init__(self) -> None:
        self._embedder: LocalSTEmbedder | None = None
        self._error: str | None = None
        self._resolved = False
        self._dim: int | None = None
        self.label: str = HASH_EMBED_LABEL

    # -- resolution -------------------------------------------------------
    def _resolve(self) -> None:
        if self._resolved:
            return
        self._resolved = True
        mode = os.getenv(EMBED_MODE_ENV, "auto").strip().lower() or "auto"
        if mode == "hashing":
            self._error = f"hashing vectorizer forced by {EMBED_MODE_ENV}=hashing"
            return
        try:
            from services.ai.embedding_service import (
                DEFAULT_LOCAL_EMBED_MODEL,
                LOCAL_EMBED_MODEL_ENV,
            )
        except Exception as exc:  # noqa: BLE001 - a broken import is a reason
            self._error = f"embedding_service unavailable: {type(exc).__name__}: {exc}"
            return
        try:
            embedder = local_embedder()
            self._dim = embedder.dim  # triggers the one-off lazy download
        except Exception as exc:  # noqa: BLE001 - recorded, never swallowed
            self._error = (
                f"{type(exc).__name__}: {exc} (model="
                f"{os.getenv(LOCAL_EMBED_MODEL_ENV, DEFAULT_LOCAL_EMBED_MODEL)!r}, "
                f"{LOCAL_EMBED_MODEL_ENV} overrides it)"
            )
            return
        self._embedder = embedder
        self.label = embedder.label

    @property
    def dim(self) -> int:
        """Vector width of the resolved backend (loads the model if needed)."""
        self._resolve()
        return self._dim if self._dim is not None else _EMBED_DIM

    # -- encoding ---------------------------------------------------------
    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch in one pass when the semantic model is available."""
        self._resolve()
        if self._embedder is not None:
            return self._embedder.embed(texts)
        return [_hash_embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        """Embed one query with the resolved backend."""
        self._resolve()
        if self._embedder is not None:
            return self._embedder.embed_query(text)
        return _hash_embed(text)

    # -- honesty surface --------------------------------------------------
    @property
    def semantic(self) -> bool:
        """True when the semantic model is in use (not the hash fallback)."""
        self._resolve()
        return self._embedder is not None

    def info(self) -> dict[str, Any]:
        """Report which backend is in use and why (never hides a fallback)."""
        self._resolve()
        if self._embedder is not None:
            return {
                "backend": "sentence-transformers",
                "label": self.label,
                "model": self._embedder.model_name,
                "dim": self._dim,
                "deterministic": False,
                "note": (
                    "Local multilingual sentence-transformers model giving real "
                    "semantic vectors over the English+Persian corpus. Loaded "
                    f"lazily; override with HYDROMA_EMBED_MODEL or force the "
                    f"hashing vectorizer with {EMBED_MODE_ENV}=hashing."
                ),
            }
        return {
            "backend": "hashing_vectorizer",
            "label": HASH_EMBED_LABEL,
            "dim": _EMBED_DIM,
            "deterministic": True,
            "reason": self._error or "unresolved",
            "note": (
                "OFFLINE FALLBACK — lexical feature hashing, not semantic "
                "embeddings: retrieval is keyword-based and weaker than the "
                f"sentence-transformers backend. Cause: {self._error}. Force it "
                f"with {EMBED_MODE_ENV}=hashing; pick a model with "
                "HYDROMA_EMBED_MODEL."
            ),
        }


#: Backend singleton (resolved once per process, lazily).
_BACKEND: _EmbeddingBackend | None = None

#: The loaded local model. Kept separate from :data:`_BACKEND` because the model
#: is ~470 MB: re-resolving the backend (e.g. after ``HYDROMA_EMBED_MODE``
#: changes) must reuse the loaded instance, not pay for a second load.
_ST_EMBEDDER: LocalSTEmbedder | None = None


def local_embedder() -> LocalSTEmbedder:
    """Return the process-cached local sentence-transformers embedder.

    Raises whatever the embedder raises (``LocalEmbeddingError``) when the
    model cannot be loaded — it never substitutes another vector space.
    """
    global _ST_EMBEDDER
    if _ST_EMBEDDER is None:
        from services.ai.embedding_service import LocalSTEmbedder

        _ST_EMBEDDER = LocalSTEmbedder()
    return _ST_EMBEDDER


def _backend() -> _EmbeddingBackend:
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = _EmbeddingBackend()
    return _BACKEND


def reset_embedding_backend() -> None:
    """Drop the cached backend decision; the loaded model is kept (tests)."""
    global _BACKEND
    _BACKEND = None


def reset_local_embedder() -> None:
    """Drop the loaded model too — a full reset (tests / env changes)."""
    global _ST_EMBEDDER, _BACKEND
    _ST_EMBEDDER = None
    _BACKEND = None


def embedder_info() -> dict[str, Any]:
    """Report which embedding backend is in use (honesty surface)."""
    return _backend().info()


def _extract_doi(text: str) -> str | None:
    match = _DOI_RE.search(text or "")
    return match.group(0) if match else None


def _rel(path: Path) -> str:
    """Path relative to the repo root when possible (stable, reviewable)."""
    try:
        return str(path.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Language labelling (bilingual corpus)
# ---------------------------------------------------------------------------
#: The corpus carries two languages. A chunk's ``language`` is decided from the
#: script its text actually uses, never from the file it came from, so a card
#: that grows a Persian paragraph later is labelled ``fa`` without a code
#: change here.
_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF]")
_LATIN_SCRIPT = re.compile(r"[A-Za-z]")


def _detect_language(text: str) -> str:
    """``"fa"`` when Arabic-script characters outnumber Latin ones, else ``"en"``.

    A mixed paragraph keeps the label of its dominant script, and a chunk with
    neither (symbols and digits only) is ``en``: that is the corpus's default
    language and matches what such a chunk can be retrieved by.
    """
    arabic = len(_ARABIC_SCRIPT.findall(text))
    latin = len(_LATIN_SCRIPT.findall(text))
    return "fa" if arabic > latin else "en"


# ---------------------------------------------------------------------------
# Corpus loaders
# ---------------------------------------------------------------------------
#: Card table fields that are not indexed as prose: ``model_id`` already labels
#: every chunk, ``scientific_references`` is indexed as its own chunk, and
#: ``field`` is the ``| Field | Value |`` markdown header row.
_CARD_NON_PROSE_LABELS = frozenset({"model_id", "scientific_references", "field"})

#: A markdown table rule row (``|---|---|``, ``|:---|---:|``).
_MARKDOWN_TABLE_RULE = re.compile(r"^:?-{2,}:?$")


def _prose_chunk(
    text: str, model_id: str, locator: str, source_file: str
) -> dict[str, Any]:
    """One prose chunk: the reference names the card field it was read from."""
    return {
        "text": text,
        "reference": f"{model_id} - {locator}",
        "source_file": source_file,
        "model_id": model_id,
        "doi": _extract_doi(text),
        "kind": "prose",
        "language": _detect_language(text),
        "qudt_units": units_in_text(text),
    }


def _load_model_cards() -> list[dict[str, Any]]:
    """Parse scientific_references and the card's own prose out of every card.

    Two chunk kinds come out of one card: the ``scientific_references`` cell
    (the bibliographic chunk this module has always carried) and one chunk per
    card section — the ``##`` heading plus the field cells under it. Section
    chunks keep each field labelled by name, so a query phrased in the card's
    own words (or in Persian, where a card carries Persian) reaches the card by
    text rather than only by embedding.
    """
    chunks: list[dict[str, Any]] = []
    if not CARDS_DIR.is_dir():
        return chunks

    for card in sorted(CARDS_DIR.glob("*.md")):
        if card.name.startswith("_"):
            continue
        try:
            text = card.read_text(encoding="utf-8")
        except OSError:
            continue

        model_id: str | None = None
        reference: str | None = None
        units_blurb = ""
        title = ""
        sections: list[tuple[str, list[tuple[str, str]]]] = []

        for line in text.splitlines():
            if line.startswith("# ") and not title:
                title = line[2:].strip()
                continue
            if line.startswith("## "):
                sections.append((line[3:].strip(), []))
                continue
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.split("|")]
            if len(cells) < 3:
                continue
            label = cells[1].strip("*").strip().lower()
            value = " | ".join(c for c in cells[2:] if c).strip()
            if not label or not value or _MARKDOWN_TABLE_RULE.match(label):
                continue  # header row, table rule, or empty cell
            if not sections:
                # The identification table sits above the first `##` heading.
                sections.append((title, []))
            if label == "model_id" and model_id is None:
                model_id = value.strip("`").strip()
            elif label == "scientific_references" and reference is None:
                reference = value
            elif label == "units":
                units_blurb = cells[2]
            if label not in _CARD_NON_PROSE_LABELS:
                sections[-1][1].append((label, value))

        if model_id is None:
            # filename prefix (CANON-001_..., S-001_...)
            prefix = card.stem.split("_", 1)[0]
            model_id = prefix if _ID_PATTERN.match(prefix) else card.stem

        source_file = _rel(card)

        if reference:
            body = f"{model_id}: {reference}"
            chunks.append(
                {
                    "text": body,
                    "reference": reference,
                    "source_file": source_file,
                    "model_id": model_id,
                    "doi": _extract_doi(reference),
                    "kind": "model_card",
                    "language": _detect_language(body),
                    "qudt_units": units_in_text(reference + " " + units_blurb),
                }
            )

        for heading, rows in sections:
            if not rows:
                continue
            prose = "\n".join(f"{label}: {value}" for label, value in rows)
            label = heading if heading else "identification"
            chunks.append(
                _prose_chunk(f"{model_id} {label}\n{prose}", model_id, label, source_file)
            )
    return chunks


def _load_engine_references() -> list[dict[str, Any]]:
    """Parse ``REFERENCES`` dicts out of engine model modules via AST.

    The modules are read as source and parsed — never imported — which keeps
    this service clear of the engine import boundary (INV-003 / AI isolation).
    """
    chunks: list[dict[str, Any]] = []
    if not MODELS_DIR.is_dir():
        return chunks

    for pyfile in sorted(MODELS_DIR.glob("*.py")):
        try:
            tree = ast.parse(pyfile.read_text(encoding="utf-8"), filename=str(pyfile))
        except (OSError, SyntaxError):
            continue

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            model_name = None
            refs: dict[str, str] = {}
            for stmt in node.body:
                target = None
                value = None
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    target, value = stmt.target.id, stmt.value
                elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    if isinstance(stmt.targets[0], ast.Name):
                        target, value = stmt.targets[0].id, stmt.value
                if target is None:
                    continue
                if target == "name" and isinstance(value, ast.Constant):
                    model_name = str(value.value)
                elif target == "REFERENCES" and isinstance(value, ast.Dict):
                    try:
                        refs = ast.literal_eval(value)
                    except (ValueError, SyntaxError):
                        refs = {}
            if not isinstance(refs, dict):
                continue
            model_id = model_name or node.name
            for key, citation in refs.items():
                if not isinstance(citation, str) or not citation.strip():
                    continue
                body = f"{model_id} {key}: {citation}"
                chunks.append(
                    {
                        "text": body,
                        "reference": citation,
                        "source_file": _rel(pyfile),
                        "model_id": model_id,
                        "doi": _extract_doi(citation),
                        "kind": "engine_model_reference",
                        "language": _detect_language(body),
                        "qudt_units": units_in_text(body),
                    }
                )
    return chunks


def _load_catalog() -> list[dict[str, Any]]:
    """Parse the model-card catalog markdown tables."""
    chunks: list[dict[str, Any]] = []
    if not CATALOG_MD.is_file():
        return chunks
    try:
        text = CATALOG_MD.read_text(encoding="utf-8")
    except OSError:
        return chunks

    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 6:
            continue
        model_id = cells[1]
        if not _ID_PATTERN.match(model_id):
            continue
        reference = cells[5]
        if not reference:
            continue
        body = f"{model_id} {cells[2]}: {reference}"
        chunks.append(
            {
                "text": body,
                "reference": reference,
                "source_file": _rel(CATALOG_MD),
                "model_id": model_id,
                "doi": _extract_doi(reference),
                "kind": "catalog",
                "language": _detect_language(body),
                "qudt_units": units_in_text(body),
            }
        )
    return chunks


#: The written research definitions the formula catalog points at, resolved
#: from ``catalog.py`` as ``<path>::<symbol>``.
_RESEARCH_DEFINITIONS_MODULE = "engine/hydroma/formulas/research/__init__.py"


def _resolve_repo_path(target: str) -> Path | None:
    """Resolve a repo-root-relative pointer to a file, or ``None``.

    The pointers inside ``catalog.py`` are relative to the repository root.
    When ``HYDROMA_RAG_ENGINE`` moves the engine elsewhere (tests), the engine
    root's parent is tried as well.
    """
    seen: set[Path] = set()
    for candidate in (_REPO_ROOT / target, ENGINE_DIR.parent / target):
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            return candidate
    return None


def _load_research_definitions() -> list[dict[str, Any]]:
    """Index each formula record's written research definition.

    ``engine/hydroma/formulas/catalog.py`` is read as source text -- never
    imported, so this module stays clear of the engine import boundary
    (INV-003). Every ``FormulaRecord`` whose ``research_definition`` names
    ``<path>::<symbol>`` contributes one chunk: that file is then read as source
    text too and its ``DEFINITIONS`` mapping supplies the definition, so the
    chunk cites the file the definition was actually read from.
    """
    catalog_path = ENGINE_DIR / "hydroma" / "formulas" / "catalog.py"
    if not catalog_path.is_file():
        return []
    try:
        tree = ast.parse(
            catalog_path.read_text(encoding="utf-8"), filename=str(catalog_path)
        )
    except (OSError, SyntaxError):
        return []

    # quantity -> research-definition pointer, as registered.
    definitions: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "id", None) != "FormulaRecord":
            continue
        quantity = None
        pointer = None
        for keyword in node.keywords:
            if keyword.arg == "quantity" and isinstance(keyword.value, ast.Constant):
                quantity = str(keyword.value.value)
            elif keyword.arg == "research_definition" and isinstance(
                keyword.value, ast.Constant
            ):
                pointer = str(keyword.value.value)
        if quantity and pointer:
            definitions[quantity] = pointer
    if not definitions:
        return []

    # One parse of the definitions module, shared by every pointer into it.
    texts: dict[Path, dict[str, str]] = {}
    chunks: list[dict[str, Any]] = []
    for quantity, pointer in definitions.items():
        target, _, symbol = pointer.partition("::")
        if not target or not symbol:
            continue
        path = _resolve_repo_path(target)
        if path is None:
            continue
        if path not in texts:
            texts[path] = _read_definitions_mapping(path)
        definition = texts[path].get(symbol)
        if not definition or not definition.strip():
            continue
        body = f"{quantity}: {definition}"
        chunks.append(
            {
                "text": body,
                "reference": f"{quantity} - research definition",
                "source_file": _rel(path),
                "model_id": quantity,
                "doi": _extract_doi(definition),
                "kind": "research_definition",
                "language": _detect_language(body),
                "qudt_units": units_in_text(definition),
            }
        )
    return chunks


def _read_definitions_mapping(path: Path) -> dict[str, str]:
    """The ``DEFINITIONS`` dict in a research-definition module, as source text."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return {}
    for node in tree.body:
        target = None
        value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name):
                target, value = node.targets[0].id, node.value
        if target != "DEFINITIONS" or not isinstance(value, ast.Dict):
            continue
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return {}
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    return {}


#: The Persian counterpart of the model cards: ``MODEL_REFERENCE_FA.md``
#: beside the index models. It is this corpus's Persian prose source.
_MODEL_REFERENCE_FA = ENGINE_DIR / "hydroma" / "models" / "MODEL_REFERENCE_FA.md"

#: A Latin token as it appears in a Persian section heading (``## ۱. ECSI — …``).
_HEADING_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def _fa_model_vocabulary() -> frozenset[str]:
    """Module names of the index models, lowercased (``hpheno`` for ``HPheno``).

    The Persian reference documents exactly those eight models, so its section
    headings are matched against this vocabulary rather than against a
    hard-coded list: a ninth model in the module directory is picked up without
    a change here, and a Latin word that is not a model is not mistaken for one.
    """
    if not MODELS_DIR.is_dir():
        return frozenset()
    return frozenset(path.stem.lower() for path in MODELS_DIR.glob("*.py"))


def _load_model_reference_fa() -> list[dict[str, Any]]:
    """Index the Persian model reference, one chunk per model section.

    Sections that name no model id (the document header, the one-page summary
    over all eight models and the closing notes) are skipped: every chunk
    carries a ``model_id``, and those sections' content is what the per-model
    sections already hold.
    """
    path = _MODEL_REFERENCE_FA
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    vocabulary = _fa_model_vocabulary()
    source_file = _rel(path)
    chunks: list[dict[str, Any]] = []
    heading = ""
    body: list[str] = []

    def flush() -> None:
        if not heading:
            return
        model_id = next(
            (
                token
                for token in _HEADING_TOKEN.findall(heading)
                if token.lower() in vocabulary
            ),
            None,
        )
        if model_id is None:
            return
        content = "\n".join(body).strip()
        if not content:
            return
        chunk_text = f"{model_id} {heading}\n{content}"
        chunks.append(
            {
                "text": chunk_text,
                "reference": f"{model_id} - {heading}",
                "source_file": source_file,
                "model_id": model_id,
                "doi": _extract_doi(chunk_text),
                "kind": "model_reference_fa",
                "language": "fa",
                "qudt_units": units_in_text(chunk_text),
            }
        )

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            heading, body = line[3:].strip(), []
        elif heading:
            body.append(line)
    flush()
    return chunks


def load_corpus() -> list[dict[str, Any]]:
    """Load the whole scientific corpus as citation-carrying chunks.

    Every chunk carries ``{source_file, model_id, reference, doi, kind,
    language}``. ``language`` is ``"fa"`` for Arabic-script text and ``"en"``
    otherwise, decided per chunk from the text itself.
    """
    corpus: list[dict[str, Any]] = []
    corpus.extend(_load_model_cards())
    corpus.extend(_load_engine_references())
    corpus.extend(_load_catalog())
    corpus.extend(_load_research_definitions())
    corpus.extend(_load_model_reference_fa())
    return corpus


# ---------------------------------------------------------------------------
# Vector store backends
# ---------------------------------------------------------------------------
def _citation_of(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "reference": chunk.get("reference", ""),
        "source_file": chunk.get("source_file", ""),
        "model_id": chunk.get("model_id"),
        "doi": chunk.get("doi"),
    }


def _result(chunk: dict[str, Any], score: float, label: str) -> dict[str, Any]:
    citation = _citation_of(chunk)
    return {
        "text": chunk.get("text", ""),
        "citation": citation,
        "reference": citation["reference"],
        "source_file": citation["source_file"],
        "model_id": citation["model_id"],
        "doi": citation["doi"],
        "language": chunk.get("language", "en"),
        "kind": chunk.get("kind", ""),
        "score": float(score),
        "qudt_units": chunk.get("qudt_units", []),
        "embedder": label,
    }


class _QdrantStore:
    """Qdrant local/in-memory backed index (no server)."""

    def __init__(self, backend: _EmbeddingBackend) -> None:
        from qdrant_client import QdrantClient  # local import; guarded by caller
        from qdrant_client.models import Distance, VectorParams

        self._backend = backend
        self._client = QdrantClient(location=":memory:")
        if self._client.collection_exists(COLLECTION):
            self._client.delete_collection(COLLECTION)
        self._client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=backend.dim, distance=Distance.COSINE),
        )

    def add(self, chunks: list[dict[str, Any]]) -> None:
        from qdrant_client.models import PointStruct

        texts = [chunk.get("text", "") for chunk in chunks]
        vectors = self._backend.embed_many(texts)
        points = []
        for i, chunk in enumerate(chunks):
            payload = {k: v for k, v in chunk.items() if k != "text"}
            payload["text"] = chunk.get("text", "")
            points.append(PointStruct(id=i, vector=vectors[i], payload=payload))
        self._client.upsert(collection_name=COLLECTION, points=points)

    def search(self, query: str, k: int, lang: str | None = None) -> list[dict[str, Any]]:
        if lang is None:
            query_filter = None
        else:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            query_filter = Filter(
                must=[
                    FieldCondition(key="language", match=MatchValue(value=lang))
                ]
            )
        hits = self._client.query_points(
            collection_name=COLLECTION,
            query=self._backend.embed_query(query),
            query_filter=query_filter,
            limit=k,
            with_payload=True,
        ).points
        label = self._backend.label
        return [_result(p.payload or {}, p.score, label) for p in hits]


class _JsonStore:
    """JSON vector store under ``data/rag/`` (qdrant-free fallback)."""

    def __init__(self, backend: _EmbeddingBackend) -> None:
        self._backend = backend
        self._rows: list[dict[str, Any]] = []
        self._path = _DATA_RAG_DIR / f"{COLLECTION}.json"

    def add(self, chunks: list[dict[str, Any]]) -> None:
        self._rows = []
        vectors = self._backend.embed_many([c.get("text", "") for c in chunks])
        for chunk, vector in zip(chunks, vectors, strict=False):
            self._rows.append(
                {
                    "text": chunk.get("text", ""),
                    "vector": vector,
                    "meta": {k: v for k, v in chunk.items() if k != "text"},
                }
            )
        try:
            _DATA_RAG_DIR.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps({"rows": self._rows}), encoding="utf-8")
        except OSError:
            pass  # persistence is best-effort; in-memory rows still answer

    def search(
        self, query: str, k: int, lang: str | None = None
    ) -> list[dict[str, Any]]:
        q = self._backend.embed_query(query)
        scored = []
        for row in self._rows:
            if lang is not None and row.get("meta", {}).get("language") != lang:
                continue
            v = row.get("vector", [])
            score = sum(a * b for a, b in zip(q, v, strict=False))
            merged = {"text": row.get("text", ""), **row.get("meta", {})}
            scored.append((score, merged))
        scored.sort(key=lambda t: t[0], reverse=True)
        label = self._backend.label
        return [_result(meta, score, label) for score, meta in scored[:k]]


# Module-level index singleton (built once per process, lazily).
_INDEX: _QdrantStore | _JsonStore | None = None
_INDEX_BACKEND: str | None = None
_INDEX_SIZE: int = 0
#: Chunk counts per language for the current index ({"en": n, "fa": m}).
_INDEX_LANGUAGES: dict[str, int] = {}


def _language_counts(chunks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for chunk in chunks:
        language = str(chunk.get("language") or "en")
        counts[language] = counts.get(language, 0) + 1
    return counts


def _build() -> tuple[_QdrantStore | _JsonStore | None, str, int]:
    backend = _backend()
    chunks = load_corpus()
    global _INDEX_LANGUAGES
    _INDEX_LANGUAGES = _language_counts(chunks)
    try:
        store: _QdrantStore | _JsonStore = _QdrantStore(backend)
        store_backend = "qdrant-local-memory"
    except Exception:  # noqa: BLE001 - qdrant missing or failed; use JSON store
        try:
            store = _JsonStore(backend)
            store_backend = "json-store"
        except Exception:  # noqa: BLE001 - an unusable store answers empty
            return None, store_backend, 0
    try:
        store.add(chunks)
    except Exception:  # noqa: BLE001 - an unusable store answers empty, never raises
        return None, store_backend, 0
    return store, store_backend, len(chunks)


def build_index(force: bool = False) -> dict[str, Any]:
    """Build (or reuse) the citation-carrying index and return build metadata.

    Idempotent per process unless ``force=True``. Returns a dict describing the
    backend, corpus size, per-language chunk counts and embedder — including
    which embedder actually won, so a lexical hashing fallback is never
    mistaken for semantic retrieval. Never raises.
    """
    global _INDEX, _INDEX_BACKEND, _INDEX_SIZE
    if _INDEX is not None and not force:
        return {
            "backend": _INDEX_BACKEND,
            "chunks": _INDEX_SIZE,
            "languages": dict(_INDEX_LANGUAGES),
            "embedder": embedder_info(),
        }
    _INDEX, _INDEX_BACKEND, _INDEX_SIZE = _build()
    return {
        "backend": _INDEX_BACKEND,
        "chunks": _INDEX_SIZE,
        "languages": dict(_INDEX_LANGUAGES),
        "embedder": embedder_info(),
    }


def search(query: str, k: int = 5, lang: str | None = None) -> list[dict[str, Any]]:
    """Return the ``k`` most relevant corpus passages, each with its citation.

    Every result carries ``{text, citation}`` where ``citation`` points at a real
    file (``source_file``), the ``reference`` string, ``model_id`` and ``doi``.

    ``lang`` restricts the candidates to chunks indexed in that language
    (``"en"`` or ``"fa"``) — a Persian question then answers from Persian text
    instead of only from an embedding similarity. ``None`` (the default)
    searches the whole bilingual corpus.
    Never raises: an unavailable backend or empty corpus returns ``[]``.
    """
    if not query or not query.strip() or k <= 0:
        return []
    if _INDEX is None or _INDEX_SIZE == 0:
        build_index()
    if _INDEX is None or _INDEX_SIZE == 0:
        return []
    try:
        return _INDEX.search(query, k, lang)
    except Exception:  # noqa: BLE001 - retrieval failure is not a fabricated answer
        return []


def index_stats() -> dict[str, Any]:
    """Non-mutating view of the current index (builds it if needed).

    Reports the same per-language chunk counts as :func:`build_index`, so a
    caller can see that the Persian half of the corpus is really indexed.
    """
    info = build_index()
    return {
        "backend": info["backend"],
        "chunks": info["chunks"],
        "languages": dict(info["languages"]),
        "available": _INDEX is not None and _INDEX_SIZE > 0,
        "embedder": info["embedder"],
        "corpus_sources": {
            "cards_dir": _rel(CARDS_DIR) if CARDS_DIR.exists() else None,
            "models_dir": _rel(MODELS_DIR) if MODELS_DIR.exists() else None,
            "catalog": _rel(CATALOG_MD) if CATALOG_MD.exists() else None,
        },
    }
