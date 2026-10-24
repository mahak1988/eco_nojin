"""Hub module - provides database connection access.

This module provides the process-wide database access points:
- get_duckdb(name) -> DuckDB connection
- get_sqlite(name) -> SQLite connection
- get_duckdb_pooled(name) -> pooled DuckDB connection
- return_duckdb_pooled(conn, name) -> return connection to pool
- get_sqlalchemy_engine() -> shared SQLAlchemy Engine
- get_session() -> sync session bound to that engine
- get_async_session() -> async session bound to the async engine
"""

import asyncio
import logging
import sqlite3
import threading
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.base import Base

logger = logging.getLogger(__name__)

#: Named in-memory SQLite DB shared across all event loops *and* across
#: both engines. The "file:..." URI with cache=shared allows multiple
#: connections (including aiosqlite's background-thread connections) to
#: attach to the SAME in-memory database. A keepalive connection holds it
#: open for the process lifetime so data persists across loop churn.
#:
#: ``database.config`` (the sync engine) resolves the same URI, so a row
#: written through either driver is visible to the other â€” a second
#: ``:memory:`` database would give the two planes the same schema and
#: different rows.
#:
#: The ``&uri=true`` query parameter is load-bearing: the SQLite
#: dialect only re-attaches URL query parameters to the driver URI
#: (``?mode=memory&cache=shared``) when it also sees ``uri`` among
#: them, and only then passes ``uri=True`` to ``sqlite3.connect``.
#: Without it the dialect resolves ``url.database`` to a plain
#: filesystem path (``os.path.abspath("file:hydroma_async_mem")``)
#: and every "in-memory" engine silently writes a real file â€” on
#: Windows a stray ``file`` artifact next to an NTFS alternate data
#: stream â€” so ``create_all(checkfirst=True)`` then skips the models'
#: current schema as "existing" tables. See ``tests/test_sqlite_concurrency.py``.
SHARED_SQLITE_MEMORY_URI = "file:hydroma_async_mem?mode=memory&cache=shared"

#: Keepalive connection to prevent the shared memory DB from being
#: destroyed when the last active connection closes. Opened once on
#: first use and never closed.
_async_keepalive: sqlite3.Connection | None = None
_keepalive_lock = threading.Lock()

#: Process-wide async engine, recreated when the running event loop
#: changes (aiosqlite connections are bound to the loop that created them).
_async_engine: Any = None
_async_engine_loop: asyncio.AbstractEventLoop | None = None
_async_engine_lock = threading.Lock()


def _get_async_engine() -> Any:
    """Return the process-wide async engine, recreating it on loop change.

    All engines (one per loop) connect to the SAME named shared-cache
    in-memory database, so data written by one loop is visible to
    engines created on subsequent loops (e.g., per-request TestClient
    portals).
    """
    global _async_engine, _async_engine_loop, _async_keepalive
    with _async_engine_lock:
        # Ensure the keepalive connection exists (opens the shared DB).
        if _async_keepalive is None:
            _async_keepalive = sqlite3.connect(SHARED_SQLITE_MEMORY_URI, uri=True)
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        if _async_engine is None or _async_engine_loop is not current_loop:
            _async_engine = create_async_engine(
                "sqlite+aiosqlite:///" + SHARED_SQLITE_MEMORY_URI + "&uri=true",
                connect_args={
                    "uri": True,
                    "check_same_thread": False,
                    # A shared-cache database has no per-connection
                    # pragmas to install (``install_sqlite_pragmas``
                    # plans nothing for ``mode=memory``), so the busy
                    # wait the file-database pragma set would install is
                    # passed to the driver instead. Without it the
                    # default busy timeout is 0 and a second writer
                    # colliding with the sync plane fails instantly with
                    # "database table is locked".
                    "timeout": 30,
                },
                poolclass=StaticPool,
            )
            install_sqlite_pragmas(_async_engine)
            _async_engine_loop = current_loop
        return _async_engine


#: PRAGMAs installed on every *file-based* SQLite connection (see
#: https://www.sqlite.org/wal.html for the WAL model):
#:
#: - ``journal_mode=WAL``: readers do not block the writer and the writer
#:   does not block readers. SQLite still serializes writers (one writer
#:   at a time), so the two collide-and-wait case is what
#:   ``busy_timeout`` below absorbs.
#: - ``busy_timeout=30000``: two writers that collide wait up to 30 s for
#:   the lock instead of failing instantly with ``database is locked``;
#:   the loser ends at a clean SQLITE_BUSY (``OperationalError``) retry
#:   point.
#: - ``foreign_keys=ON``: SQLite does NOT enforce declared foreign keys
#:   unless told to, per connection.
#: - ``synchronous=NORMAL``: WAL commits are not fsynced â€” the
#:   documented durability trade-off: safe against application crash,
#:   only the tail of a power loss can be lost.
#:
#: In-memory SQLite (including this hub's shared-cache async plane) gets
#: none of them: WAL does not exist for ``:memory:`` and such a database
#: is process-private, so locking is a non-issue. A non-SQLite URL
#: (PostgreSQL) never reaches this table at all â€” :func:`sqlite_pragma_plan`
#: is where that decision is made and unit-tested.
SQLITE_FILE_PRAGMAS: tuple[tuple[str, str], ...] = (
    ("journal_mode", "WAL"),
    ("busy_timeout", "30000"),
    ("foreign_keys", "ON"),
    ("synchronous", "NORMAL"),
)

#: SQLite builds below this version are affected by the WAL-reset bug
#: (fixed in 3.51.3, backported as 3.44.6 / 3.50.7; affects 3.7.0â€“3.51.2).
#: A WAL deployment therefore REQUIRES upgrading SQLite first: deploying
#: on an affected build risks a corrupted WAL database.
_WAL_MIN_SQLITE_VERSION = (3, 51, 3)
_WAL_MIN_SQLITE_VERSION_TEXT = ".".join(str(part) for part in _WAL_MIN_SQLITE_VERSION)

_WAL_VERSION_MESSAGE = (
    "SQLite {version} is affected by the WAL-reset bug (fixed in 3.51.3, "
    "backports 3.44.6 / 3.50.7; affected 3.7.0-3.51.2). Upgrade SQLite "
    "before deploying a WAL database {url}: an affected build risks "
    "database corruption. See https://www.sqlite.org/wal.html"
)

#: A WAL file bigger than this is a *starvation* signal, not a busy one.
#: SQLite checkpoints automatically after 1000 committed pages, so a file past
#: that point means the checkpoint is not running â€” a long-lived reader is
#: pinning the tail (or ``wal_autocheckpoint`` was turned off) and every other
#: reader keeps paying for a file that only grows.
_WAL_STARVATION_PAGES = 1000

#: 1000 pages of the default 4096-byte page size is ~4 MB. The byte ceiling is
#: the same statement expressed for a WAL whose header cannot be read (a file
#: truncated mid-header), where the page count is unknowable.
_WAL_STARVATION_BYTES = 4 * 1024 * 1024

#: The WAL file header is 32 bytes: magic (4), format version (4), page size
#: (4), checkpoint sequence (4), salt-1 (4), salt-2 (4), checksum-1 (4) and
#: checksum-2 (4). ``struct.unpack(">I", data[8:12])`` is the page size.
_WAL_HEADER_BYTES = 32
_WAL_PAGE_SIZE_OFFSET = 8

#: Every frame after the header is a 24-byte frame header followed by exactly
#: one database page, which is what makes the page count derivable from the
#: file size alone.
_WAL_FRAME_HEADER_BYTES = 24


@dataclass(frozen=True)
class SQLiteEngineReport:
    """Which SQLite driver a deployment ends up using, and whether it is WAL-safe.

    The report is the artefact a release checklist reads: it names the module
    the process would talk to, the SQLite version behind it, whether that
    version is past the WAL-reset fix, and the reason for the choice. It never
    claims a build is safe because a *different* driver on the machine might
    have been new enough.
    """

    module: str
    version: str
    wal_deployment_safe: bool
    dropin_used: bool
    bundled_version: str
    dropin_version: str | None
    reason: str


@dataclass(frozen=True)
class WalSizeReport:
    """The state of one database's write-ahead log.

    ``wal_supported`` is False for a database that has no WAL at all by
    construction (an in-memory database is process-private, so the file cannot
    exist); the report then carries a zero size and never a starvation warning.
    ``starved`` is the actionable flag: the WAL is past the automatic-checkpoint
    ceiling, so a reader is pinning the tail and the file will keep growing.
    """

    db_path: str
    wal_path: str
    wal_supported: bool
    exists: bool
    size_bytes: int
    page_size: int | None
    page_count: int
    starvation_pages: int
    starvation_bytes: int
    starved: bool
    message: str


def _sqlite_version_info(version: str | None = None) -> tuple[int, ...]:
    """The runtime (or a given) SQLite version as a comparable integer tuple.

    A version string that cannot be parsed becomes ``(0, 0, 0)`` rather than
    an exception: a deployment check must never crash on an unexpected build
    string, and an unparseable version is by definition not a known-safe one.
    """
    raw = sqlite3.sqlite_version if version is None else version
    try:
        return tuple(int(part) for part in raw.split(".")[:3])
    except ValueError:
        return (0, 0, 0)


def sqlite_wal_deployment_safe() -> bool:
    """Whether the runtime SQLite is new enough to run a WAL deployment.

    False on an affected build (3.7.0â€“3.51.2). The version is read at
    call time, so a deployment check can run it at startup.
    """
    return _sqlite_version_info() >= _WAL_MIN_SQLITE_VERSION


def _pysqlite3_module() -> Any | None:
    """Import the ``pysqlite3`` drop-in, or return ``None`` when absent.

    ``pysqlite3`` bundles its own libsqlite3, so installing the wheel is a
    way out of a too-old *system* library where upgrading SQLite is not
    available. A missing wheel is an ordinary deployment fact, not an error,
    so every failure mode (not installed, unloadable, wrong Python) is
    swallowed here and reported as "unavailable" by
    :func:`sqlite_engine_in_use`.
    """
    try:
        import pysqlite3  # type: ignore[import-not-found]
    except Exception:
        return None
    return pysqlite3


def sqlite_engine_in_use() -> SQLiteEngineReport:
    """Report the SQLite driver a WAL deployment would actually use.

    Order of preference:

    1. the bundled ``sqlite3`` when it is already new enough (>= 3.51.3);
    2. otherwise the ``pysqlite3`` drop-in, **when it is installed and is
       itself new enough** â€” a drop-in that is also affected buys nothing;
    3. otherwise the bundled ``sqlite3`` again, which is what the deployment
       actually gets, and the report says so.

    This is a report, not a silent repair: nothing is switched here. The one
    caller that acts on it is :func:`wal_safe_sqlite_url`, and only when the
    drop-in is a genuine fix.
    """
    bundled = sqlite3.sqlite_version
    if sqlite_wal_deployment_safe():
        return SQLiteEngineReport(
            module="sqlite3",
            version=bundled,
            wal_deployment_safe=True,
            dropin_used=False,
            bundled_version=bundled,
            dropin_version=None,
            reason=(
                f"bundled sqlite3 {bundled} is at or above "
                f"{_WAL_MIN_SQLITE_VERSION_TEXT}; no drop-in is needed"
            ),
        )

    dropin = _pysqlite3_module()
    dropin_version = None if dropin is None else str(getattr(dropin, "sqlite_version", "unknown"))
    if dropin is not None and _sqlite_version_info(dropin_version) >= _WAL_MIN_SQLITE_VERSION:
        return SQLiteEngineReport(
            module="pysqlite3",
            version=dropin_version or "unknown",
            wal_deployment_safe=True,
            dropin_used=True,
            bundled_version=bundled,
            dropin_version=dropin_version,
            reason=(
                f"bundled sqlite3 {bundled} is affected by the WAL-reset bug; the "
                f"pysqlite3 drop-in is usable at {dropin_version} "
                f"(>= {_WAL_MIN_SQLITE_VERSION_TEXT})"
            ),
        )

    if dropin is not None:
        reason = (
            f"bundled sqlite3 {bundled} and pysqlite3 {dropin_version} are both "
            f"below {_WAL_MIN_SQLITE_VERSION_TEXT}; upgrade SQLite before a WAL "
            "deployment (the drop-in is no fix here)"
        )
    else:
        reason = (
            f"bundled sqlite3 {bundled} is affected by the WAL-reset bug "
            f"(fixed in {_WAL_MIN_SQLITE_VERSION_TEXT}) and the pysqlite3 drop-in "
            "is not installed; upgrade SQLite before a WAL deployment"
        )
    return SQLiteEngineReport(
        module="sqlite3",
        version=bundled,
        wal_deployment_safe=False,
        dropin_used=False,
        bundled_version=bundled,
        dropin_version=dropin_version,
        reason=reason,
    )


def wal_safe_sqlite_url(url: str) -> str:
    """Rewrite a SQLAlchemy SQLite URL onto the driver that is WAL-safe.

    Returns ``url`` unchanged unless **both** are true: the URL describes a
    file-based SQLite database (in-memory SQLite has no WAL to be safe about)
    and the bundled ``sqlite3`` is affected by the WAL-reset bug while the
    ``pysqlite3`` drop-in resolves to a WAL-safe build â€” see
    :func:`sqlite_engine_in_use`.

    The async plane (``sqlite+aiosqlite://``) is returned unchanged and
    documented as such: aiosqlite talks to the standard-library ``sqlite3``
    module and cannot ride the drop-in, so an affected build on the async
    plane must be fixed by upgrading, not by this rewrite.
    """
    if not url.startswith("sqlite://"):
        return url
    if not sqlite_pragma_plan(url):
        # Not a file-based SQLite database (in-memory, or another backend):
        # no WAL is in play, so no driver rewrite either.
        return url
    report = sqlite_engine_in_use()
    if not report.dropin_used:
        return url
    return "sqlite+" + report.module + "://" + url[len("sqlite://") :]


def _is_in_memory_database(raw: str) -> bool:
    """Whether ``raw`` names an in-memory database (no WAL file can exist)."""
    if not raw or raw == ":memory:":
        return True
    if ":memory:" in raw:
        return True
    return "mode=memory" in raw


def _wal_page_size(wal_path: Path) -> int | None:
    """The page size recorded in the WAL header, or ``None`` when unreadable."""
    try:
        with wal_path.open("rb") as handle:
            header = handle.read(_WAL_HEADER_BYTES)
    except OSError:
        return None
    if len(header) < _WAL_HEADER_BYTES:
        return None
    page_size = int.from_bytes(
        header[_WAL_PAGE_SIZE_OFFSET : _WAL_PAGE_SIZE_OFFSET + 4], "big"
    )
    # SQLite stores a page size of 1 to mean 65536; every other value is the
    # size itself. Anything else outside 512..65536 is not a real WAL header.
    if page_size == 1:
        return 65536
    if page_size < 512 or page_size > 65536 or page_size & (page_size - 1):
        return None
    return page_size


def wal_size_report(db_path: str | Path) -> WalSizeReport:
    """Report the write-ahead log size of the database at ``db_path``.

    ``db_path`` is the **database** file (``data/hydroma.db``); the WAL is the
    sibling SQLite always writes it to (``data/hydroma.db-wal``). A path that
    already ends in ``-wal`` is read as given, so a monitor that captured the
    WAL name can pass it straight in.

    The report is pure filesystem inspection: no connection is opened, so it
    is safe to call against a database another process is writing, and safe to
    call from a monitoring job while the writer runs.

    It is a **live** measurement, not an archive. Closing the *last*
    connection to a database checkpoints its log back into the file and
    unlinks it, so a quiescent database always reports ``exists=False``; the
    starvation warning only has meaning while a process is actually holding
    the database open.
    """
    raw = str(db_path)
    wal_path = Path(raw if raw.endswith("-wal") else raw + "-wal")

    if _is_in_memory_database(raw):
        return WalSizeReport(
            db_path=raw,
            wal_path=str(wal_path),
            wal_supported=False,
            exists=False,
            size_bytes=0,
            page_size=None,
            page_count=0,
            starvation_pages=_WAL_STARVATION_PAGES,
            starvation_bytes=_WAL_STARVATION_BYTES,
            starved=False,
            message=(
                f"{raw} is an in-memory database: WAL does not exist for it, so "
                "there is no log to starve"
            ),
        )

    try:
        size_bytes = wal_path.stat().st_size
        exists = True
    except OSError:
        size_bytes = 0
        exists = False

    page_size = _wal_page_size(wal_path) if exists else None
    page_count = (
        max(size_bytes - _WAL_HEADER_BYTES, 0) // (_WAL_FRAME_HEADER_BYTES + page_size)
        if page_size
        else 0
    )

    if not exists:
        message = f"no WAL file at {wal_path} (nothing committed outside a checkpoint)"
        starved = False
    elif page_count > _WAL_STARVATION_PAGES:
        message = (
            f"WAL {wal_path} is {page_count} pages / {size_bytes} bytes, above the "
            f"{_WAL_STARVATION_PAGES}-page automatic-checkpoint ceiling: a reader is "
            "pinning the tail, so checkpointing is not running and the file will "
            "keep growing"
        )
        starved = True
    elif page_size is None and size_bytes > _WAL_STARVATION_BYTES:
        message = (
            f"WAL {wal_path} is {size_bytes} bytes and its header is unreadable, so "
            f"its page count cannot be derived; above the {_WAL_STARVATION_BYTES}-byte "
            "starvation ceiling"
        )
        starved = True
    else:
        message = f"WAL {wal_path} is {page_count} pages / {size_bytes} bytes"
        starved = False

    return WalSizeReport(
        db_path=raw,
        wal_path=str(wal_path),
        wal_supported=True,
        exists=exists,
        size_bytes=size_bytes,
        page_size=page_size,
        page_count=page_count,
        starvation_pages=_WAL_STARVATION_PAGES,
        starvation_bytes=_WAL_STARVATION_BYTES,
        starved=starved,
        message=message,
    )


def sqlite_pragma_plan(url: str) -> tuple[tuple[str, str], ...]:
    """The PRAGMAs to apply for a SQLAlchemy database URL.

    Empty â€” meaning "install nothing" â€” for in-memory SQLite (WAL is
    unavailable for ``:memory:`` and the database is process-private)
    and for every non-SQLite URL (a PostgreSQL deployment must not run
    SQLite pragmas at all). File-based SQLite gets
    :data:`SQLITE_FILE_PRAGMAS`.
    """
    parsed = make_url(url)
    if not parsed.get_backend_name().startswith("sqlite"):
        return ()
    database = parsed.database or ""
    if database in ("", ":memory:"):
        return ()
    if ":memory:" in database or parsed.query.get("mode") == "memory":
        return ()
    return SQLITE_FILE_PRAGMAS


def install_sqlite_pragmas(engine: Any) -> None:
    """Install the file-SQLite PRAGMAs on every new connection of ``engine``.

    Accepts a sync or async engine (``AsyncEngine`` exposes its sync twin
    as ``.sync_engine``). A no-op whenever :func:`sqlite_pragma_plan` is
    empty for the engine's URL â€” in-memory SQLite and non-SQLite
    backends â€” so callers can wire every engine they create without
    branching.

    A file-based engine on an affected SQLite build logs an error naming
    the upgrade requirement, so a WAL deployment cannot ship silently on
    3.7.0â€“3.51.2 (WAL-reset bug, fixed 3.51.3). The same log line names the
    driver the deployment would actually use, including the case where the
    ``pysqlite3`` drop-in is the fix (see :func:`sqlite_engine_in_use`).
    """
    sync_engine = getattr(engine, "sync_engine", engine)
    plan = sqlite_pragma_plan(str(sync_engine.url))
    if not plan:
        return
    if not sqlite_wal_deployment_safe():
        logger.error(
            _WAL_VERSION_MESSAGE.format(
                version=sqlite3.sqlite_version, url=sync_engine.url
            )
        )
        logger.error(
            "WAL engine resolution: %s",
            sqlite_engine_in_use().reason,
        )
        # SEC-10: fail closed. Logging-only still shipped a WAL deployment the
        # runtime can corrupt (the WAL-reset bug, fixed in 3.51.3), so the
        # pragma is dropped from the plan and the engine falls back to
        # SQLite's default journal: slower, but not corrupting. The
        # expression below is a no-op for in-memory URLs (they have no
        # journal_mode in the plan) and for safe runtimes.
        plan = [item for item in plan if item[0] != "journal_mode"]
        # Dropping the pragma is NOT enough: ``journal_mode`` is persistent in
        # the database header, so a database created in WAL still *opens* in
        # WAL on this runtime (measured on 3.49.1) â€” exactly the deployment
        # this branch refuses. Fail the mitigation closed by forcing the
        # rollback journal back on every connection.
        # The conversion takes a write lock, so it is placed AFTER busy_timeout:
        # running it first executes with a 0 ms busy handler, and on an
        # existing WAL database with a concurrent open transaction the
        # conversion raises "database is locked" *inside the connect listener*
        # (measured) â€” refusing the very deployment this branch is meant to
        # open. Behind busy_timeout the conversion waits instead of failing.
        timeout_index = next(
            (i for i, item in enumerate(plan) if item[0] == "busy_timeout"),
            len(plan) - 1,
        )
        plan.insert(timeout_index + 1, ("journal_mode", "DELETE"))
        logger.error(
            "journal_mode=WAL refused on this runtime; forcing "
            "journal_mode=DELETE (upgrade SQLite to >= %s or install "
            "pysqlite3 to re-enable WAL)",
            _WAL_MIN_SQLITE_VERSION_TEXT,
        )

    def _apply_pragmas(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        try:
            for pragma, value in plan:
                cursor.execute(f"PRAGMA {pragma}={value}")
        finally:
            cursor.close()

    event.listen(sync_engine, "connect", _apply_pragmas)


#: ``id()`` of every async engine whose tables have been created. The flag
#: cannot live on the engine itself: SQLAlchemy's ``AsyncEngine`` rejects
#: arbitrary attribute assignment (``AttributeError``), so a module-level
#: registry keyed by identity is the only place to record "tables exist".
_async_tables_ready: set[int] = set()

#: One asyncio.Lock **per event loop**, keyed by the loop *object* in a
#: WeakKeyDictionary: a single global asyncio.Lock is bound to the first loop
#: that awaits it, and engines here live on several loops (one per TestClient
#: portal, one per worker). Keying by ``id(loop)`` is not safe either â€” ids are
#: reused after GC and the registry never evicted, so a new loop could inherit
#: a lock bound to a dead one and raise ``RuntimeError: ... bound to a
#: different event loop`` on first contention (which 500s every async route for
#: the process lifetime). Weak keys evict dead loops automatically.
_async_loop_locks: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
_async_loop_locks_guard = threading.Lock()
#: Fallback for the (impossible-in-practice) call outside a running loop:
#: ``None`` cannot be a weak-referenceable key.
_ASYNC_OUTSIDE_LOOP_LOCK = asyncio.Lock()


def _table_lock_for(engine: Any) -> asyncio.Lock:  # noqa: ARG001 - signature kept for callers
    """The asyncio.Lock of the running loop (a module lock outside any loop)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return _ASYNC_OUTSIDE_LOOP_LOCK
    with _async_loop_locks_guard:
        lock = _async_loop_locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            _async_loop_locks[loop] = lock
        return lock


async def _ensure_async_tables(engine: Any) -> None:
    """Create the model tables on the shared async database exactly once.

    Idempotent and safe under concurrent first use: callers on one loop
    serialize on that loop's lock, and the retry tolerates the two benign
    states a losing creator can observe on a shared-cache database â€”
    ``table ... already exists`` and ``database table is locked`` (both mean
    another connection's ``create_all`` is mid-flight; SQLite table-level
    locking makes the loser's ``checkfirst`` read of ``sqlite_master`` fail
    before the winner commits). Re-running ``create_all`` under ``checkfirst``
    converges instead of failing the request. Anything else raises.
    """
    key = id(engine)
    if key in _async_tables_ready:
        return
    async with _table_lock_for(engine):
        if key in _async_tables_ready:
            return
        for attempt in range(5):
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                break
            except OperationalError as exc:
                message = str(exc).lower()
                if "already exists" not in message and "locked" not in message:
                    raise
                if attempt == 4:
                    raise
                await asyncio.sleep(0.05 * (attempt + 1))
        _async_tables_ready.add(key)


def normalize_database_url(url: str) -> str:
    """Normalize a database URL to a SQLAlchemy-compatible form.

    Expands the shortcut ``sqlite:///./data/econojin.db`` into an absolute
    path so that the in-process engine and any worker agree on the file
    location regardless of the current working directory.
    """
    if not url or url == "sqlite:///:memory:":
        return url
    if url.startswith("sqlite:///./"):
        import os

        rel = url[len("sqlite:///./"):]
        return "sqlite:///" + os.path.abspath(rel)
    return url


class Hub:
    """Hub that provides database access on the shared engines."""

    #: Reference (DuckDB) store path — the single source of truth for
    #  reference tables (ref_rules, ref_units_reference, …).
    internal_duckdb: Path = Path(__file__).resolve().parent.parent / "data" / "master" / "eco_nojin_master.duckdb"

    def get_sqlalchemy_engine(self) -> Any:
        """Return the shared SQLAlchemy engine.

        Delegates to ``database.config.engine`` so the hub, the
        session factory and every caller observe one in-memory
        database (the seeded test data lives there).
        """
        from database.config import engine

        return engine

    def get_session(self) -> Any:
        """Return a SQLAlchemy session bound to the shared engine.

        The session supports the context-manager protocol so callers
        can use ``with hub.get_session() as session:``.
        """
        from database.config import SessionLocal

        return SessionLocal()

    def get_session_factory(self) -> Any:
        """Return the shared SQLAlchemy sessionmaker itself.

        Callers that open many sessions keep one factory
        (``SessionLocal = hub.get_session_factory()``) and call it per unit
        of work, instead of reaching through ``with hub.get_session()``.
        Bound to the same engine as :meth:`get_session`, so every session it
        produces observes the same rows.
        """
        from database.config import SessionLocal

        return SessionLocal

    @asynccontextmanager
    async def get_async_session(self):
        """Yield an async session bound to the process-wide async engine.

        The async plane mirrors the sync one: a process-level singleton
        engine with a single pooled connection, so every async session
        observes the same rows. Tables are created once per engine so
        the async plane always observes the schema the models declare.
        """
        engine = _get_async_engine()
        await _ensure_async_tables(engine)
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            yield session

    def get_duckdb(self, name: str, read_only: bool = False) -> Any:
        """Return a DuckDB connection to the reference store.

        Opens ``internal_duckdb`` (a file-backed SQLite-compatible DuckDB
        database).  Read-only by default so multiple concurrent readers can
        coexist with a single read/write writer (DuckDB forbids mixing
        read-only and read/write handles on one file in one process).
        """
        import duckdb

        return duckdb.connect(str(self.internal_duckdb), read_only=read_only)

    def release_duckdb(self, conn: Any) -> None:
        """Close a DuckDB connection returned by :meth:`get_duckdb`."""
        try:
            conn.close()
        except Exception:
            pass

    def get_sqlite(self, name: str) -> Any:
        raise NotImplementedError(
            "Database hub not configured. Install the database package or "
            "provide a hub instance to DataConnector."
        )

    def get_duckdb_pooled(self, database: str) -> Any:
        raise NotImplementedError(
            "Database hub not configured. Install the database package or "
            "provide a hub instance to DataConnector."
        )

    def return_duckdb_pooled(self, conn: Any, database: str) -> None:
        raise NotImplementedError(
            "Database hub not configured. Install the database package or "
            "provide a hub instance to DataConnector."
        )


hub = Hub()
