"""Offline, dependency-free full-text search over marketplace products.

The marketplace's public API only pages and filters products (seller,
village, category, price). A buyer who knows the *name* of a product —
especially in Persian — has no way to find it: there is no text search at
all. This module closes that gap with an inverted full-text index built on
SQLite's FTS5 extension, reached through the standard library's
``sqlite3`` module. No new dependency is installed and no network access is
required, so the index works in the offline village deployments this
platform targets.

Engine: SQLite FTS5
-------------------
The service owns one SQLite database (in-memory by default, see
``path=``) holding a single virtual table::

    CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
        product_id UNINDEXED,   -- MarketplaceProduct primary key
        title,                  -- indexed; bm25 weight 10.0
        body,                   -- indexed description; bm25 weight 1.0
        village_id UNINDEXED,   -- filter predicate
        category   UNINDEXED,   -- filter predicate
        price      UNINDEXED,   -- filter predicate (REAL)
        status     UNINDEXED,   -- surfaced to the caller, never filtered here
        title_raw  UNINDEXED,   -- original casing, kept for display
        tokenize = 'unicode61'
    );

``UNINDEXED`` columns are stored on the row but never tokenised, so they add
nothing to the inverted index while remaining available as ordinary SQL
predicates. That is exactly how the filters are applied: ``village_id``,
``category`` and ``price`` are bound into the same ``WHERE`` clause as the
``MATCH`` constraint (see :meth:`MarketplaceSearchService.search`), so
filtering and ranking share one index scan instead of a Python-side filter
over an unbounded result set. ``title``/``body`` hold normalised text;
``title_raw`` keeps the original spelling for display.

Tokenizer: unicode61 (the FTS5 default)
--------------------------------------
``unicode61`` is the only tokenizer that ships inside stock SQLite, which
makes it the only honest choice for an offline, dependency-free index. It
splits text on Unicode non-alphanumeric boundaries and case-folds, which
covers the Persian (Arabic-script) alphabet used by product names without
extra machinery: Persian words are whitespace-delimited, so no word
segmentation or compounding rules are needed, and punctuation as well as
the zero-width non-joiner (U+200C) used inside Persian compounds simply
fall outside the alphanumeric class and act as token separators.

Persian-aware normalisation (index side *and* query side)
--------------------------------------------------------
``unicode61`` does not fold the Arabic-script spelling variants found in
real Persian input — Arabic yeh ``ي`` (U+064A) vs Persian yeh ``ی``
(U+06CC), Arabic kaf ``ك`` (U+0643) vs Persian keheh ``ک`` (U+06A9), teh
marbuta ``ة`` (U+0629) vs heh ``ه`` (U+0647), harakat and tatweel — and it
leaves the ZWNJ glued to a token. :func:`normalize_text` therefore maps
those variants onto their Persian forms and turns ZWNJ/ZWJ into spaces for
*every* write and *every* query, so a query typed with Arabic yeh finds a
product stored with Persian yeh (and vice versa) and a ZWNJ compound
matches its spaced spelling.

No stemmer — the honest limitation
----------------------------------
No Persian stemmer is available offline in this project. SQLite ships no
stemmer tokenizer, and the usual offline libraries (NLTK, Snowball, Hazm)
are neither installed nor installable in a village deployment. Stemming is
therefore **not** applied, and the consequences are stated plainly:
``کود`` does not match the plural ``کودها``, and ``زیستی`` does not match
``زیست``. Prefix matching on every term (each term becomes the FTS5 prefix
query ``"term"*``) recovers the common *prefix* cases — ``زیست`` finds
``زیستی``, ``whea`` finds ``Wheat`` — but no suffix, infix or
morphological folding is attempted.

Ranking: bm25 (the FTS5 default)
--------------------------------
Rows are ordered by ``bm25(products_fts, 0.0, 10.0, 1.0)``: FTS5's own
BM25 implementation with the title column weighted ten times the body
column (the leading 0.0 is the ``product_id`` column, which has no
postings). BM25 returns a *negative* score where more negative means more
relevant, so results are ordered ascending by that score and the ``rank``
field is the raw BM25 value — lower is better. A product whose *title*
matches outranks a product that matches only in its description, which is
the expected marketplace behaviour. The bm25 weights are positional over
*all* columns of the table, which is why the UNINDEXED leading column gets
its own (zero) weight instead of being skipped.

Capability check
----------------
FTS5 is a compile-time option of SQLite. It ships with the interpreter
this project runs on (see :func:`fts5_available`), but a build without it
must fail loudly rather than silently degrade into "no results ever", so
the service probes the capability at construction time and raises
:class:`FTS5UnavailableError` when it is missing. Pass a monkeypatched
``fts5_available`` to exercise that path in tests.

Wiring
------
This module is imported lazily by its caller. Nothing in ``service.py``,
the routers or ``main.py`` imports it, so the search surface can be
reviewed and switched on independently of the rest of the marketplace.
Use :func:`get_search_service` for the process-wide singleton (in-memory
index by default, ``path=`` for a persistent on-disk index).
"""

from __future__ import annotations

import inspect
import sqlite3
import threading
import unicodedata
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from typing import Any

__all__ = [
    "FTS5UnavailableError",
    "FTS_SCHEMA",
    "FTS_TABLE",
    "MarketplaceSearchError",
    "MarketplaceSearchService",
    "fts5_available",
    "get_search_service",
    "normalize_text",
    "reset_search_service",
]


FTS_TABLE = "products_fts"

#: DDL for the one virtual table the index needs. Kept importable so the
#: schema can be asserted in tests without touching a live service.
FTS_SCHEMA = f"""CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE} USING fts5(
    product_id UNINDEXED,
    title,
    body,
    village_id UNINDEXED,
    category UNINDEXED,
    price UNINDEXED,
    status UNINDEXED,
    title_raw UNINDEXED,
    tokenize = 'unicode61'
)"""

_INSERT_SQL = (
    f"INSERT INTO {FTS_TABLE} "
    "(product_id, title, body, village_id, category, price, status, title_raw) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)

_SNIPPET_OPEN = "<mark>"
_SNIPPET_CLOSE = "</mark>"
_SNIPPET_ELLIPSIS = " ... "
_SNIPPET_TOKENS = 12

# Positional over *every* column of products_fts (bm25's contract):
# product_id=0.0, title=10.0, body=1.0 -> a title hit outranks a body hit.
_TITLE_WEIGHT = 10.0
_BODY_WEIGHT = 1.0
_PRODUCT_ID_WEIGHT = 0.0

_ZWNJ = "\u200c"
_ZWJ = "\u200d"

# Arabic-script spelling variants folded onto their Persian forms.
_ARABIC_TO_PERSIAN = {
    ord("\u064a"): "\u06cc",  # ي  ARABIC YEH        -> ی  PERSIAN YEH
    ord("\u0649"): "\u06cc",  # ى  ALEF MAKSURA      -> ی
    ord("\u0643"): "\u06a9",  # ك  ARABIC KAF        -> ک  PERSIAN KEHEH
    ord("\u0629"): "\u0647",  # ة  TEH MARBUTA       -> ه  PERSIAN HEH
    ord("\u0640"): "",  # ـ  TATWEEL (kashida) dropped
}


class MarketplaceSearchError(RuntimeError):
    """Base class for marketplace search-index failures."""


class FTS5UnavailableError(MarketplaceSearchError):
    """The running SQLite build has no FTS5 module.

    Raised (never logged-and-forgotten) so a deployment without FTS5 fails
    at construction time instead of answering every query with an empty
    result set.
    """


def fts5_available() -> bool:
    """Report whether the loaded SQLite library can create an FTS5 table.

    FTS5 is a compile-time option, so this is a runtime capability probe:
    it tries the exact statement the index needs on a throwaway in-memory
    database and lets the failure speak for itself.
    """
    try:
        conn = sqlite3.connect(":memory:")
    except sqlite3.Error:  # pragma: no cover - no SQLite at all
        return False
    try:
        conn.execute("CREATE VIRTUAL TABLE _fts5_capability_probe USING fts5(x)")
    except sqlite3.Error:
        return False
    finally:
        conn.close()
    return True


def normalize_text(text: object) -> str:
    """Return the canonical form used on the index side and the query side.

    NFKC-normalises, folds Arabic-script spellings onto their Persian forms,
    turns ZWNJ/ZWJ into spaces, strips combining marks (Persian harakat,
    Latin accents) and case-folds. Both ``index_product`` and ``search``
    pass every string through this function, which is what makes
    Arabic/Persian spelling variants match each other.
    """
    if text is None:
        return ""
    value = unicodedata.normalize("NFKC", str(text))
    value = value.replace(_ZWNJ, " ").replace(_ZWJ, " ")
    value = value.translate(_ARABIC_TO_PERSIAN)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return value.casefold()


def _as_text(value: object) -> str | None:
    """Coerce an enum/str/None field into plain text (or ``None``)."""
    if value is None:
        return None
    value = getattr(value, "value", value)  # enum members carry .value
    text = str(value)
    return text or None


def _as_float(value: object) -> float | None:
    """Coerce a price into a REAL-compatible float, or ``None``."""
    if isinstance(value, str | int | float | Decimal):
        try:
            return float(value)
        except ValueError:  # a non-numeric price string is stored as NULL
            return None
    return None


def _quote_prefix(token: str) -> str:
    """Escape one term into an FTS5 prefix query: ``"term"*``.

    Wrapping the term in double quotes neutralises FTS5 keywords and bare
    operators in user input, and doubling embedded quotes keeps quoting
    balanced, so arbitrary search text can never raise
    ``sqlite3.OperationalError``.
    """
    return '"' + token.replace('"', '""') + '"*'


def _match_expression(query: str) -> str | None:
    """Translate free text into an FTS5 ``MATCH`` expression.

    Terms are AND-ed (each must match somewhere) and each is matched as a
    prefix so partially typed words still hit. ``None`` is returned for a
    query that carries no terms at all.
    """
    tokens = [token for token in normalize_text(query).split() if token]
    if not tokens:
        return None
    return " AND ".join(_quote_prefix(token) for token in tokens)


def _pick_snippet(body_snippet: Any, title_snippet: Any) -> str:
    """Choose the snippet worth showing, preferring the marked one.

    ``snippet()`` returns the whole column when the phrase does not occur
    in it, so the column that actually contains the match is the one with
    highlight markers; that is the informative one.
    """
    for candidate in (body_snippet, title_snippet):
        if candidate and _SNIPPET_OPEN in candidate:
            return str(candidate)
    return str(body_snippet or title_snippet or "")


class MarketplaceSearchService:
    """A rebuildable inverted full-text index over marketplace products.

    All public methods are synchronous: the index lives in its own SQLite
    database and never touches the ORM session that produced the rows.

    Parameters
    ----------
    path:
        ``None`` (default) keeps the index in memory — a fresh process
        starts empty. Pass a filesystem path to persist the index and let
        the FTS table (created with ``IF NOT EXISTS``) be reopened.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        if not fts5_available():
            msg = (
                "this SQLite build has no FTS5 module: "
                f"sqlite {sqlite3.sqlite_version} rejected "
                "CREATE VIRTUAL TABLE ... USING fts5, so the marketplace "
                "product index cannot be built"
            )
            raise FTS5UnavailableError(msg)

        self.path: str = ":memory:" if path is None else str(path)
        if path is not None:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False plus the RLock below: the index is a
        # process-wide singleton reached from request threads and from
        # asyncio tasks, and a bare sqlite3 connection is not thread-safe.
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._lock = threading.RLock()
        with self._lock:
            self._conn.execute(FTS_SCHEMA)
            self._conn.commit()

    # -- index maintenance -------------------------------------------------

    def index_product(self, product: Any) -> None:
        """Index one product, replacing any earlier row for the same id.

        ``product`` is duck-typed so the ``MarketplaceProduct`` ORM row,
        the legacy ``Product`` dataclass or a plain namespace all work:
        the fields read are ``id``, ``name``, ``description``,
        ``village_id``, ``category``, ``price`` and ``status``, each
        optional except ``id``. Text is normalised before it is tokenised.
        """
        row = self._row(product)
        with self._lock:
            self._conn.execute(f"DELETE FROM {FTS_TABLE} WHERE product_id = ?", (row[0],))
            self._conn.execute(_INSERT_SQL, row)
            self._conn.commit()

    def remove_product(self, product_id: str) -> None:
        """Drop one product from the index (idempotent)."""
        with self._lock:
            self._conn.execute(f"DELETE FROM {FTS_TABLE} WHERE product_id = ?", (str(product_id),))
            self._conn.commit()

    def rebuild(self, products: Iterable[Any]) -> int:
        """Replace the whole index with ``products``; return the row count.

        The previous contents are dropped first, so this is also the way to
        drop rows for products that no longer exist.
        """
        rows = [self._row(product) for product in products]
        with self._lock:
            self._conn.execute(f"DELETE FROM {FTS_TABLE}")
            self._conn.executemany(_INSERT_SQL, rows)
            self._conn.commit()
        return len(rows)

    async def rebuild_from_session(self, db_session: Any) -> int:
        """Cold-start the index from the ORM table of an existing database.

        ``MarketplaceService`` stores products in ``MarketplaceProduct``, so
        a fresh process can rebuild the search index from those rows with no
        separate export. Works with both an ``AsyncSession`` (the project's
        own session type) and a plain synchronous ``Session``.
        """
        from sqlalchemy import select

        from services.marketplace.models import MarketplaceProduct

        result = db_session.execute(select(MarketplaceProduct))
        if inspect.isawaitable(result):
            result = await result
        rows = list(result.scalars().all())
        return self.rebuild(rows)

    # -- querying ----------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        village_id: str | None = None,
        category: str | None = None,
        max_price: float | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Rank products matching ``query``, optionally filtered.

        Terms are AND-ed prefix matches; results come back ordered by BM25
        (best first, more negative ``rank`` = more relevant) and bounded by
        ``limit``. Each result is a dict with the keys ``product_id``,
        ``title``, ``rank``, ``snippet``, plus the filter fields
        (``village_id``, ``category``, ``price``, ``status``) so the caller
        can display or group hits without a second lookup.

        The filters are SQL predicates on the UNINDEXED columns of the same
        FTS table, applied in the one statement that does the matching —
        never as a Python-side filter over the result set. ``max_price``
        uses ``price <= ?``, so a row with a NULL price never satisfies it.
        An empty (or punctuation-only) query matches nothing and returns
        ``[]`` instead of raising.

        ``snippet`` is FTS5's own ``snippet()`` output, wrapping matched
        terms of the normalised text in ``<mark>``/``</mark>``; the column
        that actually matched (title or description) is the one that keeps
        the markers, while ``title`` keeps the original spelling.
        """
        match_expression = _match_expression(query)
        if match_expression is None:
            return []

        sql, params = self._build_sql(
            match_expression,
            village_id=village_id,
            category=category,
            max_price=max_price,
            limit=limit,
        )
        with self._lock:
            cursor = self._conn.execute(sql, params)
            return [self._hit(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """Number of indexed products (index health / test helper)."""
        with self._lock:
            cursor = self._conn.execute(f"SELECT count(*) FROM {FTS_TABLE}")
            return int(cursor.fetchone()[0])

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with self._lock:
            self._conn.close()

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _row(product: Any) -> tuple[Any, ...]:
        """Project one product onto the FTS table's column order."""
        product_id = getattr(product, "id", None)
        if product_id is None or str(product_id) == "":
            msg = "cannot index a product without an id"
            raise ValueError(msg)
        title_raw = str(getattr(product, "name", "") or "")
        return (
            str(product_id),
            normalize_text(title_raw),
            normalize_text(getattr(product, "description", "") or ""),
            _as_text(getattr(product, "village_id", None)),
            _as_text(getattr(product, "category", None)),
            _as_float(getattr(product, "price", None)),
            _as_text(getattr(product, "status", None)),
            title_raw,
        )

    @staticmethod
    def _build_sql(
        match_expression: str,
        *,
        village_id: str | None,
        category: str | None,
        max_price: float | None,
        limit: int,
    ) -> tuple[str, list[Any]]:
        """Build the search statement: one MATCH plus the filter predicates.

        Returns ``(sql, params)``; the SQL text is what proves the filters
        are index predicates rather than post-processing, and it is kept
        free of interpolated user input (every value is a bound parameter).
        """
        snippet_params = [_SNIPPET_OPEN, _SNIPPET_CLOSE, _SNIPPET_ELLIPSIS]
        params: list[Any] = [
            *snippet_params,
            *snippet_params,
            match_expression,
        ]
        predicates: list[str] = []
        if village_id is not None:
            predicates.append("village_id = ?")
            params.append(village_id)
        if category is not None:
            predicates.append("category = ?")
            params.append(category)
        if max_price is not None:
            predicates.append("price <= ?")
            params.append(float(max_price))

        weights = f"{_PRODUCT_ID_WEIGHT}, {_TITLE_WEIGHT}, {_BODY_WEIGHT}"
        sql = f"""
            SELECT product_id,
                   title_raw,
                   bm25({FTS_TABLE}, {weights}) AS rank,
                   snippet({FTS_TABLE}, 1, ?, ?, ?, {_SNIPPET_TOKENS}) AS title_snippet,
                   snippet({FTS_TABLE}, 2, ?, ?, ?, {_SNIPPET_TOKENS}) AS body_snippet,
                   village_id,
                   category,
                   price,
                   status
              FROM {FTS_TABLE}
             WHERE {FTS_TABLE} MATCH ?
        """
        if predicates:
            sql += "   AND " + "\n   AND ".join(predicates) + "\n"
        sql += " ORDER BY rank\n LIMIT ?"
        params.append(max(0, int(limit)))
        return sql, params

    @staticmethod
    def _hit(row: Any) -> dict[str, Any]:
        """Shape one result row into the documented dict."""
        return {
            "product_id": row[0],
            "title": row[1],
            "rank": row[2],
            "snippet": _pick_snippet(row[4], row[3]),
            "village_id": row[5],
            "category": row[6],
            "price": row[7],
            "status": row[8],
        }


# -- process-wide singleton -------------------------------------------------

_search_service: MarketplaceSearchService | None = None
_search_service_lock = threading.Lock()


def get_search_service(path: str | Path | None = None) -> MarketplaceSearchService:
    """Return the process-wide search index, building it on first use.

    The default index is in-memory; pass ``path=`` for a persistent file.
    The first call decides the backing store, so a ``path=`` supplied after
    the singleton already exists is ignored — reset it first with
    :func:`reset_search_service` if the backing store must change.
    """
    global _search_service
    with _search_service_lock:
        if _search_service is None:
            _search_service = MarketplaceSearchService(path=path)
        return _search_service


def reset_search_service() -> None:
    """Drop the cached singleton (test isolation / shutdown helper)."""
    global _search_service
    with _search_service_lock:
        _search_service = None
