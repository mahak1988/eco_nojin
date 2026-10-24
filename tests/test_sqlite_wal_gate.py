"""The SQLite WAL gate, made actionable (Phase 1 — backend integrity).

Pins the two halves of the gate that the release checklist actually needs,
plus the resolution order that decides which driver a deployment runs on:

1. **Which engine is in use.** ``sqlite_engine_in_use()`` reports the module
   and the SQLite version behind it, and whether that version is past the
   WAL-reset fix (3.51.3, backports 3.44.6 / 3.50.7; affected 3.7.0–3.51.2).
   When the bundled ``sqlite3`` is affected, the ``pysqlite3`` drop-in is
   attempted — it bundles its own libsqlite3, which is the only way out of a
   too-old *system* library — and it is only used when it is itself new enough.
   A drop-in that is also affected buys nothing, and a missing one is an
   ordinary deployment fact, not a crash.
2. **How big the log is.** ``wal_size_report()`` measures the sibling
   ``<db>-wal`` file and raises a starvation warning past the automatic
   checkpoint ceiling (1000 pages ≈ 4 MB), because a file past that point
   means a reader is pinning the tail and the log will only grow.

The runtime in this repository is **3.49.1 — affected** (see
``AGENTS.md``), so the drop-in and starvation paths below are the ones that
run here rather than the "already safe" path.

Every test writes inside ``tmp_path``. The repository's ``data/`` directory
is never touched, and no connection outlives its test.
"""

from __future__ import annotations

import sqlite3
import struct
from pathlib import Path
from types import SimpleNamespace

import pytest

import database.hub as hub

#: Rows the real-WAL test writes before it measures. Each row is a little
#: over 1 KB, so 6000 of them is comfortably past the 1000-page ceiling and
#: the assertion is not riding on a boundary value.
_WAL_GROW_ROWS = 6000
_WAL_ROW_PAD = "x" * 500


@pytest.fixture
def scratch_db(tmp_path: Path) -> Path:
    """Path of this test's scratch SQLite file under the system temp dir."""
    return tmp_path / "scratch.db"


# ── which engine is in use ─────────────────────────────────────────────────────


class TestSqliteEngineInUse:
    """The report names the module, the version, and whether it is WAL-safe."""

    def test_report_matches_the_runtime_build(self):
        bundled = sqlite3.sqlite_version
        bundled_version = tuple(int(part) for part in bundled.split(".")[:3])
        report = hub.sqlite_engine_in_use()

        assert report.version == bundled
        assert report.wal_deployment_safe == (bundled_version >= (3, 51, 3))
        assert report.wal_deployment_safe == hub.sqlite_wal_deployment_safe()

    def test_an_affected_bundled_build_never_reports_itself_as_safe(self):
        """3.49.1 must not be talked into being WAL-safe by this module."""
        if hub.sqlite_wal_deployment_safe():
            pytest.skip(
                f"SQLite {sqlite3.sqlite_version} is already past 3.51.3; the "
                "affected-build paths are only expected on 3.7.0-3.51.2"
            )
        report = hub.sqlite_engine_in_use()

        assert report.module == "sqlite3"
        assert report.wal_deployment_safe is False
        assert report.dropin_used is False
        # The reason is the upgrade instruction, not "watch out, maybe".
        assert "3.51.3" in report.reason
        assert "pysqlite3" in report.reason or "upgrade" in report.reason.lower()

    def test_a_missing_dropin_is_a_fact_not_a_crash(self, monkeypatch):
        monkeypatch.setattr(hub, "_pysqlite3_module", lambda: None)
        report = hub.sqlite_engine_in_use()

        assert report.dropin_version is None
        assert report.dropin_used is False
        assert "not installed" in report.reason

    def test_a_dropin_that_is_itself_new_enough_is_the_fix(self, monkeypatch):
        """A drop-in past 3.51.3 is used and named, version and all."""
        monkeypatch.setattr(
            hub,
            "_pysqlite3_module",
            lambda: SimpleNamespace(sqlite_version="3.51.3"),
        )
        report = hub.sqlite_engine_in_use()

        assert report.module == "pysqlite3"
        assert report.version == "3.51.3"
        assert report.dropin_used is True
        assert report.wal_deployment_safe is True
        assert report.dropin_version == "3.51.3"
        assert sqlite3.sqlite_version in report.reason

    def test_a_dropin_that_is_also_affected_is_not_used(self, monkeypatch):
        """A too-old drop-in buys nothing: the report says the build is affected."""
        monkeypatch.setattr(
            hub,
            "_pysqlite3_module",
            lambda: SimpleNamespace(sqlite_version="3.50.7"),
        )
        report = hub.sqlite_engine_in_use()

        assert report.module == "sqlite3"
        assert report.dropin_used is False
        assert report.wal_deployment_safe is False
        assert report.dropin_version == "3.50.7"

    def test_a_dropin_that_cannot_be_parsed_is_treated_as_affected(
        self, monkeypatch
    ):
        """An unreadable version string is not evidence of a fix."""
        monkeypatch.setattr(
            hub,
            "_pysqlite3_module",
            lambda: SimpleNamespace(sqlite_version="not-a-version"),
        )
        report = hub.sqlite_engine_in_use()

        assert report.dropin_used is False
        assert report.wal_deployment_safe is False

    def test_version_parsing_survives_a_short_build_string(self, monkeypatch):
        monkeypatch.setattr(sqlite3, "sqlite_version", "3")
        assert hub._sqlite_version_info() == (3,)
        assert not hub.sqlite_wal_deployment_safe()
        monkeypatch.setattr(sqlite3, "sqlite_version", "3.abc.1")
        assert hub._sqlite_version_info() == (0, 0, 0)


# ── the driver rewrite ────────────────────────────────────────────────────────


class TestWalSafeSqliteUrl:
    """``sqlite://`` is only rewritten when the drop-in is the actual fix."""

    def test_untouched_without_a_dropin(self, monkeypatch):
        monkeypatch.setattr(hub, "_pysqlite3_module", lambda: None)
        assert (
            hub.wal_safe_sqlite_url("sqlite:///./data/hydroma.db")
            == "sqlite:///./data/hydroma.db"
        )

    def test_rewritten_onto_the_dropin_when_it_is_the_fix(self, monkeypatch):
        monkeypatch.setattr(
            hub,
            "_pysqlite3_module",
            lambda: SimpleNamespace(sqlite_version="3.51.3"),
        )
        assert (
            hub.wal_safe_sqlite_url("sqlite:////data/hydroma.db")
            == "sqlite+pysqlite3:////data/hydroma.db"
        )

    def test_in_memory_urls_keep_their_driver(self, monkeypatch):
        """WAL does not exist for ``:memory:``, so there is nothing to fix."""
        monkeypatch.setattr(
            hub,
            "_pysqlite3_module",
            lambda: SimpleNamespace(sqlite_version="3.51.3"),
        )
        for url in (
            "sqlite:///:memory:",
            "sqlite://",
            "sqlite:///file:hydroma_async_mem?mode=memory&cache=shared",
        ):
            assert hub.wal_safe_sqlite_url(url) == url

    def test_the_async_plane_keeps_its_driver(self, monkeypatch):
        """aiosqlite talks to the stdlib module; it cannot ride the drop-in."""
        monkeypatch.setattr(
            hub,
            "_pysqlite3_module",
            lambda: SimpleNamespace(sqlite_version="3.51.3"),
        )
        url = "sqlite+aiosqlite:///file:hydroma_async_mem?mode=memory&cache=shared"
        assert hub.wal_safe_sqlite_url(url) == url

    def test_a_non_sqlite_url_is_returned_verbatim(self, monkeypatch):
        monkeypatch.setattr(hub, "_pysqlite3_module", lambda: None)
        url = "postgresql+psycopg://user@localhost/hydroma"
        assert hub.wal_safe_sqlite_url(url) == url


# ── how big the log is ────────────────────────────────────────────────────────


class TestWalSizeReport:
    """The WAL size, and the starvation warning past the checkpoint ceiling."""

    def test_an_in_memory_database_has_no_log_to_measure(self):
        report = hub.wal_size_report(":memory:")

        assert report.wal_supported is False
        assert report.exists is False
        assert report.size_bytes == 0
        assert report.page_count == 0
        assert report.starved is False
        assert "WAL does not exist" in report.message

    def test_a_database_with_no_wal_file_reports_nothing_committed(self, scratch_db):
        report = hub.wal_size_report(scratch_db)

        assert report.wal_supported is True
        assert report.exists is False
        assert report.wal_path == str(Path(str(scratch_db) + "-wal"))
        assert report.starved is False
        assert "no WAL file" in report.message

    def test_a_short_log_is_reported_without_a_starvation_warning(self, scratch_db):
        conn = sqlite3.connect(str(scratch_db))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA wal_autocheckpoint=0")
            conn.execute("CREATE TABLE t(a TEXT)")
            conn.commit()

            report = hub.wal_size_report(scratch_db)
        finally:
            conn.close()

        assert report.exists is True
        assert 0 < report.page_count <= hub._WAL_STARVATION_PAGES
        assert report.starved is False
        assert str(report.page_count) in report.message

    def test_a_clean_close_removes_the_log_entirely(self, scratch_db):
        """Why the report is a *live* measurement, not an archive.

        Closing the last connection is a checkpoint: SQLite folds the log back
        into the database and unlinks the file, so a database nobody is
        writing to always reports ``exists=False``. The starvation warning is
        therefore a statement about a *running* writer (or a reader pinning
        that writer), and a monitor must be sampling while the application is
        up — a report taken afterwards says nothing about what happened.
        """
        conn = sqlite3.connect(str(scratch_db))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE t(a TEXT)")
        conn.execute("INSERT INTO t VALUES ('a')")
        conn.commit()
        conn.close()

        report = hub.wal_size_report(scratch_db)

        assert report.wal_supported is True
        assert report.exists is False
        assert report.starved is False

    def test_a_log_past_the_checkpoint_ceiling_starves(self, scratch_db):
        """A real WAL that a pinned reader never let SQLite checkpoint.

        ``wal_autocheckpoint=0`` is the switch a monitoring job needs in order
        to see the state at all: with the default setting SQLite checkpoints
        at 1000 pages and the file collapses back, so the report would have
        nothing to say about a database that is actually failing.
        """
        conn = sqlite3.connect(str(scratch_db))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA wal_autocheckpoint=0")
            conn.execute("CREATE TABLE t(a TEXT, b TEXT)")
            conn.commit()
            conn.executemany(
                "INSERT INTO t VALUES (?, ?)",
                [(_WAL_ROW_PAD, "y" * 500) for _ in range(_WAL_GROW_ROWS)],
            )
            conn.commit()
            page_size = conn.execute("PRAGMA page_size").fetchone()[0]

            report = hub.wal_size_report(scratch_db)
        finally:
            conn.close()

        assert report.exists is True
        assert report.page_size == page_size
        assert report.page_count > hub._WAL_STARVATION_PAGES
        assert report.starved is True
        # 1000 pages of the default page size is ~4 MB, so the page ceiling
        # and the byte ceiling describe the same database.
        assert report.size_bytes > report.starvation_bytes
        assert "starv" in report.message.lower() or "ceiling" in report.message
        assert str(scratch_db) in report.message

    def test_the_page_count_comes_from_the_wal_header(self, scratch_db):
        """A synthetic log with a known header is measured, not estimated."""
        page_size = 4096
        frames = 12
        wal = Path(str(scratch_db) + "-wal")
        wal.write_bytes(
            struct.pack(">IIIIIII", 0x377F0682, 3007000, page_size, 7, 1, 2, 3)
            + struct.pack(">III", 0, 0, 0)
            + b"\x00" * (frames * (page_size + hub._WAL_FRAME_HEADER_BYTES))
        )

        report = hub.wal_size_report(scratch_db)

        assert report.exists is True
        assert report.page_size == page_size
        assert report.page_count == frames
        assert report.starved is False

    def test_a_truncated_header_falls_back_to_the_byte_ceiling(self, scratch_db):
        """A log too short to carry a header is judged by size alone."""
        wal = Path(str(scratch_db) + "-wal")
        wal.write_bytes(b"\x00" * (hub._WAL_STARVATION_BYTES + 1))

        report = hub.wal_size_report(scratch_db)

        assert report.exists is True
        assert report.page_size is None
        assert report.page_count == 0
        assert report.starved is True
        assert "byte" in report.message

    def test_a_non_power_of_two_header_is_rejected(self, scratch_db):
        """A garbage page size is not safe to divide by; size alone is the answer."""
        wal = Path(str(scratch_db) + "-wal")
        header = struct.pack(">IIIIIII", 0x377F0682, 3007000, 4000, 7, 1, 2, 3)
        wal.write_bytes(header + b"\x00" * 16)

        report = hub.wal_size_report(scratch_db)

        assert report.page_size is None
        assert report.page_count == 0
        assert report.starved is False

    def test_a_path_that_is_already_the_wal_is_read_as_given(self, scratch_db):
        wal = Path(str(scratch_db) + "-wal")
        wal.write_bytes(b"\x00" * 64)

        report = hub.wal_size_report(wal)

        assert report.db_path == str(wal)
        assert report.wal_path == str(wal)
        assert report.exists is True

    def test_the_report_is_pure_filesystem_inspection(self, scratch_db):
        """No connection is opened, so a live database is not disturbed."""
        conn = sqlite3.connect(str(scratch_db))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE t(a TEXT)")
            conn.commit()
            before = hub.wal_size_report(scratch_db)

            conn.execute("INSERT INTO t VALUES ('z')")
            conn.commit()
            after = hub.wal_size_report(scratch_db)
        finally:
            conn.close()

        # The log grew while the writer held its connection open: measuring
        # it neither checkpointed it nor interrupted the transaction.
        assert before.exists is True
        assert after.size_bytes > before.size_bytes
        assert after.starved is False


# ── the gate itself ───────────────────────────────────────────────────────────


class TestWalDeploymentGate:
    """The gate the release checklist refuses to pass without."""

    def test_the_gate_is_the_version_comparison(self):
        version = tuple(int(part) for part in sqlite3.sqlite_version.split(".")[:3])
        assert hub.sqlite_wal_deployment_safe() == (version >= (3, 51, 3))

    def test_an_affected_build_logs_the_upgrade_requirement_with_the_engine(
        self, scratch_db, caplog
    ):
        from sqlalchemy import create_engine, text

        if hub.sqlite_wal_deployment_safe():
            pytest.skip(
                f"SQLite {sqlite3.sqlite_version} is past the WAL-reset fix; the "
                "affected-build logging is only expected on 3.7.0-3.51.2"
            )

        engine = create_engine("sqlite:///" + scratch_db.as_posix())
        try:
            import logging

            with caplog.at_level(logging.ERROR, logger="database.hub"):
                hub.install_sqlite_pragmas(engine)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
        finally:
            engine.dispose()

        assert "3.51.3" in caplog.text
        assert "WAL-reset" in caplog.text
        # The new half: the log says which engine this deployment would use.
        assert "WAL engine resolution" in caplog.text
        assert "pysqlite3" in caplog.text

    def test_a_healthy_runtime_logs_nothing_new(self, scratch_db):
        """On a WAL-safe build the resolution line is not emitted at all."""
        from sqlalchemy import create_engine

        engine = create_engine("sqlite:///" + scratch_db.as_posix())
        try:
            if not hub.sqlite_wal_deployment_safe():
                pytest.skip(
                    f"SQLite {sqlite3.sqlite_version} is affected; only a healthy "
                    "runtime can prove the quiet path"
                )
            import logging

            import database.hub as hub_module

            records: list[str] = []
            logger = logging.getLogger(hub_module.__name__)

            class _Capture(logging.Handler):
                def emit(self, record):
                    records.append(record.getMessage())

            handler = _Capture()
            logger.addHandler(handler)
            try:
                hub_module.install_sqlite_pragmas(engine)
            finally:
                logger.removeHandler(handler)
            assert not records
        finally:
            engine.dispose()
