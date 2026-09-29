"""Honesty-contract tests for the backup service.

Before Phase 1, ``_run_logical_backup`` wrote three lines of SQL comment to
disk and returned ``verification_status="passed"``; both restore methods were
``pass`` while ``run_restore`` still set ``COMPLETED`` and
``restored_objects=1``. These tests pin the replacement: a backup either
produces a real artifact or the job fails with a reason.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from services.backup.service import (
    BackupNotImplementedError,
    BackupService,
    _sqlite_source,
)


@pytest.fixture
def sqlite_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A small SQLite database that looks like the app's.

    Rows are inserted with explicit ``execute`` calls rather than
    ``executemany``: the ``typeguard`` plugin instruments pytest fixture
    generators, and parameterised ``executemany`` raises
    ``ProgrammingError: parameters are of unsupported type`` inside a fixture
    while working fine in a test body.
    """
    path = tmp_path / "source.sqlite"
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance REAL)")
    conn.execute("CREATE TABLE entries (id INTEGER PRIMARY KEY, memo TEXT)")
    conn.execute("INSERT INTO accounts (balance) VALUES (10.0)")
    conn.execute("INSERT INTO accounts (balance) VALUES (20.0)")
    conn.execute("INSERT INTO entries (memo) VALUES ('a')")
    conn.execute("INSERT INTO entries (memo) VALUES ('b')")
    conn.commit()
    conn.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path.as_posix()}")
    return path


class _StubConfig:
    def __init__(self, storage_path: Path, **kw):
        self.id = "cfg-1"
        self.name = "test"
        self.storage_path = str(storage_path)
        self.compression = "gzip"
        self.encryption_enabled = False
        self.verify_checksum = True
        self.backup_type = "logical"
        self.__dict__.update(kw)


class _StubJob:
    def __init__(self, backup_type: str = "logical"):
        self.id = "job-1"
        self.config_id = "cfg-1"
        self.backup_type = backup_type
        self.started_at = None
        self.status = "pending"
        self.databases = ["main"]
        self.file_path = None
        self.restored_objects = 0
        self.confirm = True


def _service() -> BackupService:
    return BackupService(db=None)  # type: ignore[arg-type]


class TestLogicalBackupIsReal:
    @pytest.mark.asyncio
    async def test_artifact_contains_the_source_data(self, sqlite_db: Path, tmp_path: Path):
        svc = _service()
        result = await svc._run_logical_backup(_StubJob(), _StubConfig(tmp_path / "out"))

        produced = Path(result["file_path"])
        assert produced.exists()
        assert result["size_bytes"] > 0
        assert result["verification_status"] == "passed"

        # The artifact must round-trip back to the same rows.
        restored = tmp_path / "restored.sqlite"
        restored.write_bytes(svc._read_artifact(produced))
        raw = sqlite3.connect(str(restored))
        rows = raw.execute("SELECT balance FROM accounts ORDER BY id").fetchall()
        raw.close()
        assert rows == [(10.0,), (20.0,)]

    @pytest.mark.asyncio
    async def test_verification_reports_the_table_count(self, sqlite_db: Path, tmp_path: Path):
        svc = _service()
        result = await svc._run_logical_backup(_StubJob(), _StubConfig(tmp_path / "out"))
        details = result["verification_details"]
        assert details["integrity_check"].lower() == "ok"
        assert details["snapshot_table_count"] >= 2
        assert details["source_table_count"] == details["snapshot_table_count"]

    @pytest.mark.asyncio
    async def test_uncompressed_path_also_produces_a_usable_artifact(
        self, sqlite_db: Path, tmp_path: Path
    ):
        svc = _service()
        result = await svc._run_logical_backup(
            _StubJob(), _StubConfig(tmp_path / "out", compression="none")
        )
        produced = Path(result["file_path"])
        assert not produced.name.endswith(".gz")
        conn = sqlite3.connect(str(produced))
        assert conn.execute("PRAGMA integrity_check").fetchone()[0].lower() == "ok"
        conn.close()

    @pytest.mark.asyncio
    async def test_refuses_to_mislabel_a_plaintext_dump_as_encrypted(
        self, sqlite_db: Path, tmp_path: Path
    ):
        svc = _service()
        with pytest.raises(BackupNotImplementedError, match="encryption_enabled"):
            await svc._run_logical_backup(
                _StubJob(), _StubConfig(tmp_path / "out", encryption_enabled=True)
            )


class TestUnimplementedModesFailLoudly:
    @pytest.mark.asyncio
    async def test_physical_backup_raises(self, sqlite_db: Path, tmp_path: Path):
        svc = _service()
        with pytest.raises(BackupNotImplementedError, match="Physical backup"):
            await svc._run_physical_backup(_StubJob("physical"), _StubConfig(tmp_path / "out"))

    @pytest.mark.asyncio
    async def test_physical_restore_raises(self, sqlite_db: Path):
        svc = _service()
        with pytest.raises(BackupNotImplementedError, match="Physical restore"):
            await svc._run_physical_restore(_StubJob("physical"), _StubJob())

    @pytest.mark.asyncio
    async def test_pg_dump_absent_is_an_error_not_a_placeholder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
        monkeypatch.setattr("services.backup.service.shutil.which", lambda _name: None)
        svc = _service()
        with pytest.raises(BackupNotImplementedError, match="pg_dump"):
            await svc._run_logical_backup(_StubJob(), _StubConfig(tmp_path / "out"))


class TestRestoreIsReal:
    @pytest.mark.asyncio
    async def test_round_trip_restores_previous_contents(self, sqlite_db: Path, tmp_path: Path):
        svc = _service()
        result = await svc._run_logical_backup(_StubJob(), _StubConfig(tmp_path / "out"))

        # Mutate the live database after the snapshot.
        conn = sqlite3.connect(str(sqlite_db))
        conn.execute("DELETE FROM accounts")
        conn.commit()
        conn.close()

        backup_job = _StubJob()
        backup_job.file_path = result["file_path"]
        restore = _StubJob()
        await svc._run_logical_restore(restore, backup_job)

        assert restore.restored_objects >= 2
        conn = sqlite3.connect(str(sqlite_db))
        rows = conn.execute("SELECT balance FROM accounts ORDER BY id").fetchall()
        conn.close()
        assert rows == [(10.0,), (20.0,)]

    @pytest.mark.asyncio
    async def test_restore_requires_confirmation(self, sqlite_db: Path, tmp_path: Path):
        svc = _service()
        result = await svc._run_logical_backup(_StubJob(), _StubConfig(tmp_path / "out"))
        backup_job = _StubJob()
        backup_job.file_path = result["file_path"]
        restore = _StubJob()
        restore.confirm = False
        with pytest.raises(BackupNotImplementedError, match="confirm"):
            await svc._run_logical_restore(restore, backup_job)

    @pytest.mark.asyncio
    async def test_restore_refuses_a_missing_artifact(self, sqlite_db: Path, tmp_path: Path):
        svc = _service()
        backup_job = _StubJob()
        backup_job.file_path = str(tmp_path / "nope.sql")
        with pytest.raises(FileNotFoundError):
            await svc._run_logical_restore(_StubJob(), backup_job)


class TestSourceResolution:
    def test_sqlite_source_is_none_for_postgres(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
        assert _sqlite_source() is None

    def test_sqlite_source_is_none_for_memory(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DATABASE_URL", "sqlite://")
        assert _sqlite_source() is None

    def test_sqlite_source_resolves_the_file(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/x.db")
        assert _sqlite_source() == Path("./data/x.db").resolve()
