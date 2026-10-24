"""Concurrency regression tests for the SQLite durability foundation.

Pins the guarantees the SQLite plane can actually make, and the two
defects that made them meaningless until now (``database/hub.py``):

1. **The hub async engine is genuinely in-memory.** Its URL must carry
   ``&uri=true`` next to ``mode=memory&cache=shared``: without it the
   SQLite dialect resolves ``file:hydroma_async_mem?...`` through
   ``os.path.abspath`` and every "in-memory" engine silently opens a
   real file (on Windows a stray ``file`` artifact backed by an NTFS
   alternate data stream), whose stale schema ``create_all(checkfirst=True)``
   then trusts as existing tables — the ``no such column`` class of
   failures a previous wave documented. ``PRAGMA database_list`` must
   report an empty path and ``journal_mode`` must be ``memory``, and no
   stray artifact may appear next to the repository.
2. **The first-touch race resolves through the UNIQUE constraint.**
   ``FOR UPDATE`` is a no-op on SQLite (SQLAlchemy drops the locking
   clause), so ``StockService.get_or_create_balance``'s anti-fork
   guarantee rests on ``uq_inv_balance_sku_wh_loc_lot``: two connections
   inserting the same (sku, warehouse, location, lot) row leave exactly
   one row, and the loser's transaction rolls back cleanly
   (``IntegrityError``).
3. **WAL + busy_timeout on file databases.** The hub installs
   ``journal_mode=WAL`` / ``busy_timeout`` / ``foreign_keys=ON`` /
   ``synchronous=NORMAL``: a writer commits while a reader holds a read
   transaction (no ``database is locked``), and a colliding second writer
   waits for the lock and then surfaces a clean ``OperationalError``
   (SQLITE_BUSY) instead of failing instantly.
4. **The SQLite version gate.** The WAL-reset bug (fixed in 3.51.3;
   backports 3.44.6 / 3.50.7; affects 3.7.0–3.51.2) means a WAL
   deployment must upgrade SQLite first. ``sqlite_wal_deployment_safe()``
   is the startup check, and the pragma path installs nothing for
   in-memory SQLite (WAL does not exist for ``:memory:``) or for a
   non-SQLite URL such as PostgreSQL.

Every test uses a scratch database under the system temp directory and
closes its connections, so cleanup never races an open handle — the
repository's ``data/`` directory is never touched.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError

import database.hub as hub

#: Imported for its side effect: registers every model class on
#: ``Base.metadata``, without which ``create_all`` creates nothing.
import database.models  # noqa: F401
from database.base import Base

#: The P2-18 first-touch insert: the exact key
#: ``uq_inv_balance_sku_wh_loc_lot`` guards. The parent ids (1, 1) are
#: seeded into ``inv_skus`` / ``inv_warehouses`` first because the hub's
#: pragma set turns foreign-key enforcement ON for file databases. Raw
#: ``text()`` SQL bypasses the ORM's column defaults, so every NOT NULL
#: column is spelled out.
FIRST_TOUCH_SQL = (
    "INSERT INTO inv_inventory_balances "
    "(sku_id, warehouse_id, location_id, lot_id, on_hand, reserved, blocked, in_transit) "
    "VALUES (1, 1, 0, 0, 10, 0, 0, 0)"
)


@pytest.fixture
def scratch_db(tmp_path: Path) -> Path:
    """Path of this test's scratch SQLite file under the system temp dir."""
    return tmp_path / "scratch.db"


@pytest.fixture
def scratch_engine(scratch_db: Path, safe_sqlite: bool):
    """A file-based engine wired through the hub's pragma installer."""
    engine = create_engine("sqlite:///" + scratch_db.as_posix())
    hub.install_sqlite_pragmas(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def safe_sqlite() -> bool:
    """Whether the runtime SQLite is new enough to run a WAL deployment.

    SEC-10: the hub refuses ``journal_mode=WAL`` below 3.51.3 (the WAL-reset
    bug), so the WAL-specific assertions in this module are conditional on the
    runtime rather than hard-failing on an affected build.
    """
    return hub.sqlite_wal_deployment_safe()


def _create_inventory_tables(engine) -> None:
    """Create the full model schema on the scratch database.

    The whole ``Base.metadata`` is created (not just the inventory
    tables) so the scratch database matches what production's
    ``_ensure_async_tables`` builds — including the parents the
    balance rows' foreign keys point at, which ``foreign_keys=ON``
    on a file database now actually enforces.
    """
    Base.metadata.create_all(engine)


# ── the hub async engine is genuinely in-memory ──────────────────────────────


def test_hub_async_engine_is_genuinely_in_memory():
    """The shared-cache engine must resolve to an in-memory database.

    Before the fix the dialect stripped ``mode=memory``/``cache=shared``
    off the URL (``uri`` only arrived through ``connect_args``, which
    ``create_connect_args`` never sees) and opened a real file at
    ``<repo>/file:hydroma_async_mem`` instead — with a stale schema the
    process then trusted.
    """
    repo_root = Path.cwd()
    before = set(os.listdir(repo_root))

    async def _probe() -> tuple[list[tuple], str]:
        engine = hub._get_async_engine()
        async with engine.connect() as conn:
            databases = (await conn.exec_driver_sql("PRAGMA database_list")).fetchall()
            journal_mode = (await conn.exec_driver_sql("PRAGMA journal_mode")).scalar()
        return list(databases), journal_mode

    databases, journal_mode = asyncio.run(_probe())

    # (0, 'main', '') — an in-memory database has no file path at all.
    assert databases == [(0, "main", "")]
    assert journal_mode == "memory"

    strays = {
        name
        for name in set(os.listdir(repo_root)) - before
        if name == "file" or "hydroma_async_mem" in name
    }
    assert not strays, f"the async engine created on-disk artifacts: {strays}"


# ── pragma selection: file vs memory vs non-SQLite ───────────────────────────


class TestPragmaPlanSelection:
    """``sqlite_pragma_plan`` decides where the pragma path runs."""

    def test_file_sqlite_gets_the_full_plan(self):
        assert dict(hub.sqlite_pragma_plan("sqlite:////srv/data/econojin.db")) == {
            "journal_mode": "WAL",
            "busy_timeout": "30000",
            "foreign_keys": "ON",
            "synchronous": "NORMAL",
        }

    def test_relative_file_sqlite_gets_the_full_plan(self):
        # The backup service's default shape (normalize_database_url
        # expands it to an absolute path, but the plan must not depend on
        # that normalisation having happened).
        assert hub.sqlite_pragma_plan("sqlite:///./data/econojin.db") == (
            hub.SQLITE_FILE_PRAGMAS
        )

    def test_plain_memory_sqlite_gets_nothing(self):
        assert hub.sqlite_pragma_plan("sqlite:///:memory:") == ()
        assert hub.sqlite_pragma_plan("sqlite://") == ()

    def test_shared_cache_memory_uri_gets_nothing(self):
        # The hub's own async URL: mode=memory, so WAL and locking
        # pragmas are both meaningless (and WAL is unavailable).
        assert (
            hub.sqlite_pragma_plan(
                "sqlite+aiosqlite:///file:hydroma_async_mem"
                "?mode=memory&cache=shared&uri=true"
            )
            == ()
        )
        assert (
            hub.sqlite_pragma_plan(
                "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"
            )
            == ()
        )

    def test_non_sqlite_url_gets_nothing(self):
        """A PostgreSQL deployment must never run the SQLite pragma path."""
        assert hub.sqlite_pragma_plan("postgresql://u:p@db:5432/hydroma") == ()
        assert hub.sqlite_pragma_plan("postgresql+psycopg://u:p@db:5432/hydroma") == ()

    def test_install_registers_nothing_for_memory_or_postgres(self, monkeypatch):
        """The pragma path itself is skipped for those URLs, not just planned away."""
        # The engines are built before the spy is installed: SQLAlchemy
        # itself registers a pool-level "connect" listener inside
        # create_engine, which the spy must not intercept.
        memory_engine = create_engine("sqlite:///:memory:")
        postgres_engine = create_engine("postgresql+psycopg://u:p@localhost:5432/hydroma")

        registered: list[str] = []
        real_listen = hub.event.listen

        def _spy(target, identifier, fn, **kw):
            if target in (memory_engine, postgres_engine):
                registered.append(identifier)
                return None
            return real_listen(target, identifier, fn, **kw)

        monkeypatch.setattr(hub.event, "listen", _spy)
        try:
            hub.install_sqlite_pragmas(memory_engine)
            assert registered == []

            hub.install_sqlite_pragmas(postgres_engine)
            assert registered == []
        finally:
            memory_engine.dispose()

    def test_install_registers_one_connect_listener_for_file_sqlite(self, monkeypatch):
        # The engine is built before the spy is installed (see the test
        # above): only the hub's own listener must be counted.
        engine = create_engine("sqlite:///./data/econojin.db")

        registered: list[str] = []
        real_listen = hub.event.listen

        def _spy(target, identifier, fn, **kw):
            if target is engine:
                registered.append(identifier)
                return None
            return real_listen(target, identifier, fn, **kw)

        monkeypatch.setattr(hub.event, "listen", _spy)
        try:
            hub.install_sqlite_pragmas(engine)
            assert registered == ["connect"]
        finally:
            engine.dispose()

    def test_memory_engine_keeps_default_pragmas(self):
        """Even when installed, an in-memory engine keeps SQLite defaults."""
        engine = create_engine("sqlite:///:memory:")
        hub.install_sqlite_pragmas(engine)
        with engine.connect() as conn:
            assert conn.execute(text("PRAGMA journal_mode")).scalar() == "memory"
            assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 0
        engine.dispose()


# ── file databases get the pragma set ────────────────────────────────────────


class TestFileEnginePragmas:
    def test_file_engine_gets_wal_busy_timeout_and_fk(self, scratch_engine, safe_sqlite):
        """WAL + busy_timeout + FK pragmas on a **safe** runtime.

        SEC-10: on a runtime below the WAL-safe SQLite (3.51.3) the installer
        refuses ``journal_mode=WAL`` (the WAL-reset bug corrupts data), so the
        journal assertions only hold when ``safe_sqlite`` provided a safe
        runtime. busy_timeout / foreign_keys / synchronous are applied either
        way.
        """
        with scratch_engine.connect() as conn:
            if safe_sqlite:
                assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
                # NORMAL == 1 once the database is in WAL mode.
                assert conn.execute(text("PRAGMA synchronous")).scalar() == 1
            else:
                assert conn.execute(text("PRAGMA journal_mode")).scalar() != "wal"
            assert conn.execute(text("PRAGMA busy_timeout")).scalar() == 30000
            assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1

    def test_writer_commits_while_a_reader_holds_a_read_transaction(
        self, scratch_db: Path, scratch_engine, safe_sqlite
    ):
        """WAL: a reader's open transaction does not block the writer.

        Only meaningful on a WAL runtime: on an unsafe SQLite the installer
        refuses WAL and the default journal serializes readers and writers, so
        the test is skipped there rather than asserted to fail (SEC-10).
        """
        if not safe_sqlite:
            pytest.skip("WAL is refused on this SQLite runtime (SEC-10)")
        with scratch_engine.begin() as conn:
            conn.execute(text("CREATE TABLE demo (id INTEGER PRIMARY KEY, note TEXT)"))
            conn.execute(text("INSERT INTO demo (id, note) VALUES (1, 'seed')"))

        reader = sqlite3.connect(scratch_db)
        writer = sqlite3.connect(scratch_db)
        try:
            # A plain SELECT does not hold a transaction in the sqlite3
            # module's legacy isolation mode; BEGIN makes the read
            # snapshot (and the shared lock) explicit.
            reader.execute("BEGIN")
            assert reader.execute("SELECT count(*) FROM demo").fetchone()[0] == 1

            writer.execute("INSERT INTO demo (id, note) VALUES (2, 'during read')")
            writer.commit()

            # The reader keeps its snapshot (WAL isolation) ...
            assert reader.execute("SELECT count(*) FROM demo").fetchone()[0] == 1
            reader.rollback()
            # ... and both writers' rows are there once it ends.
            assert reader.execute("SELECT count(*) FROM demo").fetchone()[0] == 2
        finally:
            reader.close()
            writer.close()

    async def test_async_file_engine_gets_the_pragmas(
        self, tmp_path: Path, safe_sqlite: bool
    ):
        """The installer unwraps AsyncEngine (``.sync_engine``) for file DBs."""
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(
            "sqlite+aiosqlite:///" + (tmp_path / "async.db").as_posix()
        )
        hub.install_sqlite_pragmas(engine)
        try:
            async with engine.connect() as conn:
                journal_mode = (
                    await conn.exec_driver_sql("PRAGMA journal_mode")
                ).scalar()
                busy_timeout = (
                    await conn.exec_driver_sql("PRAGMA busy_timeout")
                ).scalar()
        finally:
            await engine.dispose()

        # SEC-10: WAL only on a safe runtime; busy_timeout always applies.
        assert (journal_mode == "wal") == safe_sqlite
        assert busy_timeout == 30000

    def test_colliding_writer_waits_then_fails_cleanly(
        self, scratch_db: Path, scratch_engine
    ):
        """busy_timeout turns a lock collision into a bounded, clean SQLITE_BUSY."""
        with scratch_engine.begin() as conn:
            conn.execute(text("CREATE TABLE demo (id INTEGER PRIMARY KEY, note TEXT)"))
            conn.execute(text("INSERT INTO demo (id, note) VALUES (1, 'seed')"))

        holder = scratch_engine.connect()
        waiter = scratch_engine.connect()
        try:
            # Hold a write transaction open: the second writer must wait.
            holder.execute(text("INSERT INTO demo (id, note) VALUES (2, 'held')"))

            # Shorten only the waiter's wait so the test stays fast; the
            # wait itself is what busy_timeout buys.
            waiter.exec_driver_sql("PRAGMA busy_timeout=200")
            started = time.monotonic()
            with pytest.raises(OperationalError) as excinfo:
                waiter.execute(text("INSERT INTO demo (id, note) VALUES (3, 'waiting')"))
            waited = time.monotonic() - started

            assert "database is locked" in str(excinfo.value)
            assert waited >= 0.15, "the second writer failed before busy_timeout elapsed"

            # The holder can still commit and the waiter's transaction
            # rolls back cleanly, leaving the database usable.
            holder.commit()
            waiter.rollback()
            with scratch_engine.begin() as conn:
                assert conn.execute(text("SELECT count(*) FROM demo")).scalar() == 2
        finally:
            holder.close()
            waiter.close()


# ── the P2-18 first-touch race ───────────────────────────────────────────────


class TestFirstTouchRace:
    """Two connections reserving the same balance row, at engine level.

    ``FOR UPDATE`` cannot be exercised on SQLite (SQLAlchemy no-ops it),
    so this pins the constraint the guarantee actually degrades to: the
    UNIQUE index on (sku_id, warehouse_id, location_id, lot_id) that
    ``StockService.get_or_create_balance`` relies on.
    """

    def test_duplicate_first_touch_insert_has_one_winner_and_clean_rollback(
        self, scratch_db: Path, scratch_engine
    ):
        _create_inventory_tables(scratch_engine)
        with scratch_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO inv_skus (id, sku_code, name, uom) "
                    "VALUES (1, 'P218', 'sku', 'kg')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO inv_warehouses (id, code, name, is_active) "
                    "VALUES (1, 'P218', 'wh', 1)"
                )
            )

        outcomes: dict[str, str] = {}
        barrier = threading.Barrier(2)

        def _first_touch(name: str) -> None:
            try:
                with scratch_engine.begin() as conn:
                    barrier.wait(timeout=30)
                    conn.execute(text(FIRST_TOUCH_SQL))
                outcomes[name] = "committed"
            except IntegrityError as exc:
                outcomes[name] = f"integrity-error: {exc}"

        threads = [threading.Thread(target=_first_touch, args=(name,)) for name in ("a", "b")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert sorted(value.split(":")[0] for value in outcomes.values()) == [
            "committed",
            "integrity-error",
        ]
        loser_error = next(value for value in outcomes.values() if value != "committed")
        assert "UNIQUE constraint failed" in loser_error
        assert "inv_inventory_balances" in loser_error

        with scratch_engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT count(*) FROM inv_inventory_balances "
                    "WHERE sku_id = 1 AND warehouse_id = 1 "
                    "AND location_id = 0 AND lot_id = 0"
                )
            ).scalar()
        assert rows == 1

        # The loser's rollback left the database usable: a different key
        # still inserts and both rows are readable afterwards.
        with scratch_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO inv_inventory_balances "
                    "(sku_id, warehouse_id, location_id, lot_id, on_hand, reserved,"
                    " blocked, in_transit) VALUES (1, 1, 1, 0, 1, 0, 0, 0)"
                )
            )
        with scratch_engine.connect() as conn:
            total = conn.execute(
                text("SELECT count(*) FROM inv_inventory_balances")
            ).scalar()
        assert total == 2


# ── the WAL version gate ─────────────────────────────────────────────────────


class TestWalVersionGate:
    """A WAL deployment requires SQLite >= 3.51.3 (WAL-reset bug)."""

    def test_gate_matches_the_runtime_version(self):
        version = tuple(int(part) for part in sqlite3.sqlite_version.split(".")[:3])
        assert hub.sqlite_wal_deployment_safe() == (version >= (3, 51, 3))

    def test_affected_runtime_logs_the_upgrade_requirement(
        self, scratch_db: Path, caplog: pytest.LogCaptureFixture
    ):
        """On an affected build the pragma path says so, loudly.

        The WAL-reset bug affects SQLite 3.7.0–3.51.2 and is fixed in
        3.51.3 (backports 3.44.6 / 3.50.7); a WAL database deployed on an
        affected build risks corruption, so the requirement is recorded
        on the error channel instead of shipping silently. The engine is
        built here — inside the capture window — because the hub logs
        when it installs the pragmas.
        """
        if hub.sqlite_wal_deployment_safe():
            pytest.skip(
                f"SQLite {sqlite3.sqlite_version} is not affected by the WAL-reset "
                "bug (fixed 3.51.3); the upgrade-requirement warning is only "
                "expected on 3.7.0-3.51.2 builds"
            )

        engine = create_engine("sqlite:///" + scratch_db.as_posix())
        with caplog.at_level(logging.ERROR, logger="database.hub"):
            hub.install_sqlite_pragmas(engine)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        finally:
            engine.dispose()

        assert "3.51.3" in caplog.text
        assert "WAL-reset" in caplog.text
