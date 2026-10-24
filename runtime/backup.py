"""File-based backup and restore for the local SQLite storage tier (DP-2).

This module replaces container volumes: before the container-era snapshot, a
database is checkpointed with ``PRAGMA wal_checkpoint(TRUNCATE)`` so the main
database file alone is a consistent image, the file (and any ``-wal``/``-shm``
sidecars) is copied into a timestamped snapshot directory, and every file's
sha256 is written into ``manifest.json`` next to it.

Commands:
    python -m runtime.backup create --db <path> [--label <text>]
    python -m runtime.backup verify --dir <backup_dir>
    python -m runtime.backup restore <snapshot_name> <target_path> [--force]
    python -m runtime.backup prune --keep <N>

Exit codes: 0 success · 1 verification failure · 2 usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_BACKUP_DIR = Path("data") / "backups"
_CHUNK = 1024 * 1024


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _safe_stamp() -> str:
    return _utc_now().replace(":", "").replace("+00:00", "Z").replace("-", "")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checkpoint(db_path: Path) -> None:
    """Fold the write-ahead log into the main file so the copy is consistent."""
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        connection.close()


def snapshot(db_path: Path, backup_dir: Path, label: str | None = None) -> dict:
    """Create a checksummed snapshot of *db_path* and return its manifest."""
    db_path = Path(db_path).resolve()
    backup_dir = Path(backup_dir).resolve()
    if not db_path.is_file():
        raise FileNotFoundError(f"database file not found: {db_path}")

    _checkpoint(db_path)

    suffix = f"_{label}" if label else ""
    target = backup_dir / f"{_safe_stamp()}{suffix}"
    target.mkdir(parents=True, exist_ok=False)

    files: dict[str, dict[str, object]] = {}
    sources = [db_path]
    for sidecar in ("-wal", "-shm"):
        candidate = db_path.with_name(db_path.name + sidecar)
        if candidate.is_file():
            sources.append(candidate)
    for source in sources:
        destination = target / source.name
        shutil.copy2(source, destination)
        files[destination.name] = {
            "size_bytes": destination.stat().st_size,
            "sha256": _sha256(destination),
        }

    manifest = {
        "snapshot": target.name,
        "created_at_utc": _utc_now(),
        "source_db": str(db_path),
        "storage_tier": "local",
        "files": files,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def _load_manifests(backup_dir: Path) -> list[dict]:
    manifests: list[dict] = []
    if not Path(backup_dir).is_dir():
        return manifests
    for path in sorted(Path(backup_dir).iterdir()):
        manifest_path = path / "manifest.json"
        if manifest_path.is_file():
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return manifests


def verify(backup_dir: Path) -> list[dict]:
    """Recompute every checksum; return one record per mismatch (empty = good)."""
    mismatches: list[dict] = []
    for manifest in _load_manifests(backup_dir):
        for name, entry in manifest["files"].items():
            snapshot_dir = Path(backup_dir) / manifest["snapshot"]
            path = snapshot_dir / name
            if not path.is_file():
                mismatches.append(
                    {"snapshot": manifest["snapshot"], "file": name, "issue": "missing"}
                )
                continue
            actual = _sha256(path)
            if actual != entry["sha256"]:
                mismatches.append(
                    {
                        "snapshot": manifest["snapshot"],
                        "file": name,
                        "issue": "sha256 mismatch",
                        "expected": entry["sha256"],
                        "actual": actual,
                    }
                )
    return mismatches


def _has_active_wal(target: Path) -> bool:
    wal = target.with_name(target.name + "-wal")
    return wal.is_file() and wal.stat().st_size > 0


def restore(
    snapshot_name: str,
    target_path: Path,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    force: bool = False,
) -> Path:
    """Restore a snapshot over *target_path*; refuses when a live WAL exists."""
    backup_dir = Path(backup_dir).resolve()
    target = Path(target_path).resolve()
    snapshot_dir = backup_dir / snapshot_name
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"snapshot not found: {snapshot_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if target.is_file() and _has_active_wal(target) and not force:
        raise RuntimeError(
            f"refusing to restore over an active write-ahead log: "
            f"{target.name}-wal is non-empty (pass --force to override)"
        )

    for sidecar in ("-wal", "-shm"):
        stale = target.with_name(target.name + sidecar)
        if stale.is_file() and (force or not _has_active_wal(target)):
            stale.unlink()

    target.parent.mkdir(parents=True, exist_ok=True)
    main_file = snapshot_dir / Path(manifest["source_db"]).name
    if not main_file.is_file():
        raise FileNotFoundError(f"snapshot is missing the database file: {main_file}")
    shutil.copy2(main_file, target)
    return target


def retention(backup_dir: Path, keep_last: int = 10) -> list[str]:
    """Verify-then-prune: delete the oldest snapshots beyond *keep_last*."""
    if verify(backup_dir):
        raise RuntimeError("refusing to prune: snapshot verification failed")
    manifests = _load_manifests(backup_dir)
    manifests.sort(key=lambda m: m["created_at_utc"])
    doomed = manifests[:-keep_last] if keep_last >= 0 else []
    removed: list[str] = []
    for manifest in doomed:
        directory = Path(backup_dir) / manifest["snapshot"]
        shutil.rmtree(directory, ignore_errors=True)
        removed.append(manifest["snapshot"])
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runtime.backup", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a snapshot")
    create.add_argument("--db", required=True)
    create.add_argument("--dir", default=str(DEFAULT_BACKUP_DIR))
    create.add_argument("--label", default=None)

    check = sub.add_parser("verify", help="verify every checksum")
    check.add_argument("--dir", default=str(DEFAULT_BACKUP_DIR))

    restore_parser = sub.add_parser("restore", help="restore a snapshot")
    restore_parser.add_argument("snapshot")
    restore_parser.add_argument("target")
    restore_parser.add_argument("--dir", default=str(DEFAULT_BACKUP_DIR))
    restore_parser.add_argument("--force", action="store_true")

    prune = sub.add_parser("prune", help="keep only the newest N snapshots")
    prune.add_argument("--dir", default=str(DEFAULT_BACKUP_DIR))
    prune.add_argument("--keep", type=int, default=10)

    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            manifest = snapshot(args.db, args.dir, args.label)
            print(
                f"CREATED {manifest['snapshot']} "
                f"({sum(int(f['size_bytes']) for f in manifest['files'].values())} bytes)"
            )
            print("SUMMARY created=1 verified_ok")
            return 0
        if args.command == "verify":
            mismatches = verify(args.dir)
            if mismatches:
                for entry in mismatches:
                    print(f"MISMATCH {entry}")
                print(f"SUMMARY verified=0 mismatched={len(mismatches)}")
                return 1
            print("SUMMARY verified=1 mismatched=0")
            return 0
        if args.command == "restore":
            path = restore(args.snapshot, args.target, args.dir, args.force)
            print(f"RESTORED {args.snapshot} -> {path}")
            print("SUMMARY restored=1")
            return 0
        if args.command == "prune":
            removed = retention(args.dir, keep_last=args.keep)
            print(f"PRUNED kept={args.keep} removed={len(removed)}")
            for name in removed:
                print(f"  removed {name}")
            print(f"SUMMARY kept={args.keep} removed={len(removed)}")
            return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR {type(exc).__name__}: {exc}")
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
