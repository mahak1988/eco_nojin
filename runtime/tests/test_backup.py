"""Backup/restore tests for the local SQLite storage tier (DP-2).

These tests prove the container-volume replacement: a WAL-checkpointed,
checksummed, prunable file snapshot. They use ``tmp_path`` only and never
touch a real database in the repository.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

_BACKUP_PATH = Path(__file__).resolve().parents[1] / "backup.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("runtime_backup_under_test", _BACKUP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_db(path: Path, rows: int = 24) -> Path:
    connection = sqlite3.connect(str(path))
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
    connection.executemany("INSERT INTO t (v) VALUES (?)", [(f"row-{i}",) for i in range(rows)])
    connection.commit()
    connection.close()
    return path


def _fake_active_wal(db_path: Path) -> Path:
    """A non-empty ``-wal`` file, written directly so no live handle is held."""
    wal = db_path.with_name(db_path.name + "-wal")
    wal.write_bytes(b"\x00" * 4096)
    return wal


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    return _make_db(tmp_path / "hydroma.sqlite3")


def test_snapshot_and_verify_round_trip(db: Path, tmp_path: Path) -> None:
    module = _load_module()
    backup_dir = tmp_path / "backups"
    manifest = module.snapshot(db, backup_dir, label="unit")
    snapshot_dir = backup_dir / manifest["snapshot"]

    assert snapshot_dir.is_dir()
    assert manifest["storage_tier"] == "local"
    assert manifest["files"], "manifest must list the copied files"
    assert (snapshot_dir / "manifest.json").is_file()
    assert module.verify(backup_dir) == [], "a fresh snapshot must verify clean"


def test_manifest_sha256_matches_the_file(db: Path, tmp_path: Path) -> None:
    module = _load_module()
    backup_dir = tmp_path / "backups"
    manifest = module.snapshot(db, backup_dir)
    snapshot_dir = backup_dir / manifest["snapshot"]
    for name, entry in manifest["files"].items():
        assert module._sha256(snapshot_dir / name) == entry["sha256"], name


def test_restore_refuses_active_wal_without_force(db: Path, tmp_path: Path) -> None:
    module = _load_module()
    backup_dir = tmp_path / "backups"
    manifest = module.snapshot(db, backup_dir)

    victim = tmp_path / "live.sqlite3"
    _make_db(victim, rows=3)
    _fake_active_wal(victim)
    with pytest.raises(RuntimeError, match="active write-ahead log"):
        module.restore(manifest["snapshot"], victim, backup_dir, force=False)

    restored = module.restore(manifest["snapshot"], victim, backup_dir, force=True)
    assert restored.is_file()
    connection = sqlite3.connect(str(restored))
    assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 24
    connection.close()


def test_prune_keeps_last_n(db: Path, tmp_path: Path) -> None:
    module = _load_module()
    backup_dir = tmp_path / "backups"
    for index in range(12):
        module.snapshot(db, backup_dir, label=f"p{index:02d}")
    module.retention(backup_dir, keep_last=5)
    manifests = [
        json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        for path in sorted(backup_dir.iterdir())
        if path.is_dir()
    ]
    assert len(manifests) == 5
    kept = sorted(m["snapshot"][-3:] for m in manifests)
    assert kept == ["p07", "p08", "p09", "p10", "p11"], kept


def test_cli_create_and_verify(db: Path, tmp_path: Path) -> None:
    module = _load_module()
    backup_dir = tmp_path / "backups"
    assert module.main(["create", "--db", str(db), "--dir", str(backup_dir), "--label", "cli"]) == 0
    assert module.main(["verify", "--dir", str(backup_dir)]) == 0


def test_corruption_is_detected(db: Path, tmp_path: Path) -> None:
    module = _load_module()
    backup_dir = tmp_path / "backups"
    manifest = module.snapshot(db, backup_dir)
    victim = backup_dir / manifest["snapshot"] / db.name
    with victim.open("r+b") as handle:
        handle.seek(0)
        original = handle.read(1)
        handle.seek(0)
        handle.write(bytes([original[0] ^ 0xFF]))
    assert module.main(["verify", "--dir", str(backup_dir)]) == 1
    with pytest.raises(RuntimeError, match="verification failed"):
        module.retention(backup_dir, keep_last=1)


def test_module_uses_stdlib_only() -> None:
    source = _BACKUP_PATH.read_text(encoding="utf-8")
    for forbidden in ("numpy", "requests", "sqlalchemy", "pydantic", "pandas"):
        assert f"import {forbidden}" not in source
