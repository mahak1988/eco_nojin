#!/usr/bin/env python
"""Eco Nojin innovation backlog tracker.

Reads the machine-readable backlog in ``docs/innovation_backlog.csv`` and
reports status, dependencies and KPIs per wave. The ``validate`` subcommand
runs in the CI gate.

Deliberately dependency-free so it runs in any CI environment without an
install step (see ``docs/standards/S-STRUCT.md``).
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

BACKLOG_PATH = Path(__file__).resolve().parent.parent / "docs" / "innovation_backlog.csv"

VALID_STATUS = {"todo", "in_progress", "blocked", "done", "deferred"}
WAVE_ORDER = ("W0", "W1", "W2", "W3")
VALID_WAVES = set(WAVE_ORDER)
VALID_TYPES = {"evolutionary", "integration", "moonshot"}
VALID_HORIZONS = {"short", "mid", "long"}
VALID_GRADES = {"low", "medium", "high"}
VALID_CATEGORIES = set("ABCDEFGHIJKLMN")

WAVE_LABELS = {
    "W0": "W0 (0-2m) - base of trust",
    "W1": "W1 (2-6m) - trustworthy and sellable",
    "W2": "W2 (6-18m) - decentralized and nanoscale",
    "W3": "W3 (18m+) - new frontiers",
}

REQUIRED_COLUMNS = (
    "id",
    "title",
    "category",
    "type",
    "horizon",
    "impact",
    "effort",
    "trl",
    "wave",
    "depends_on",
    "owner",
    "status",
    "paths",
    "kpi",
)


@dataclass(frozen=True)
class Item:
    id: int
    title: str
    category: str
    type: str
    horizon: str
    impact: str
    effort: str
    trl: int
    wave: str
    depends_on: tuple[int, ...]
    owner: str
    status: str
    paths: str
    kpi: str

    @property
    def blocked_by(self) -> tuple[int, ...]:
        return self.depends_on


def _parse_dependencies(raw: str) -> tuple[int, ...]:
    if not raw.strip():
        return ()
    return tuple(int(part) for part in raw.replace(";", ",").split(",") if part.strip())


def load_items(path: Path) -> tuple[list[Item], list[str]]:
    """خواندن CSV. برگرداندن (اقلام، فهرست خطاها)."""
    errors: list[str] = []
    if not path.is_file():
        return [], [f"backlog file not found: {path}"]

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return [], [f"backlog has no header: {path}"]

        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            return [], [f"missing required columns: {', '.join(missing)}"]

        items: list[Item] = []
        seen_ids: set[int] = set()
        for line_number, row in enumerate(reader, start=2):
            raw_id = (row.get("id") or "").strip()
            if not raw_id:
                errors.append(f"line {line_number}: empty id")
                continue
            try:
                item_id = int(raw_id)
            except ValueError:
                errors.append(f"line {line_number}: id is not an integer: {raw_id!r}")
                continue

            if item_id in seen_ids:
                errors.append(f"line {line_number}: duplicate id {item_id}")
                continue
            seen_ids.add(item_id)

            category = (row.get("category") or "").strip().upper()
            if category not in VALID_CATEGORIES:
                errors.append(f"line {line_number}: unknown category {category!r}")

            item_type = (row.get("type") or "").strip().lower()
            if item_type not in VALID_TYPES:
                errors.append(f"line {line_number}: unknown type {item_type!r}")

            horizon = (row.get("horizon") or "").strip().lower()
            if horizon not in VALID_HORIZONS:
                errors.append(f"line {line_number}: unknown horizon {horizon!r}")

            for field in ("impact", "effort"):
                value = (row.get(field) or "").strip().lower()
                if value not in VALID_GRADES:
                    errors.append(f"line {line_number}: unknown {field} {value!r}")

            wave = (row.get("wave") or "").strip().upper()
            if wave not in VALID_WAVES:
                errors.append(f"line {line_number}: unknown wave {wave!r}")

            status = (row.get("status") or "").strip().lower()
            if status not in VALID_STATUS:
                errors.append(f"line {line_number}: unknown status {status!r}")

            try:
                trl = int((row.get("trl") or "").strip())
                if not 1 <= trl <= 9:
                    errors.append(f"line {line_number}: trl out of range 1-9: {trl}")
            except ValueError:
                errors.append(f"line {line_number}: trl is not an integer")
                trl = 0

            if not (row.get("kpi") or "").strip():
                errors.append(f"line {line_number}: item {item_id} has no KPI")

            if not (row.get("paths") or "").strip():
                errors.append(f"line {line_number}: item {item_id} has no target path")

            items.append(
                Item(
                    id=item_id,
                    title=(row.get("title") or "").strip(),
                    category=category,
                    type=item_type,
                    horizon=horizon,
                    impact=(row.get("impact") or "").strip().lower(),
                    effort=(row.get("effort") or "").strip().lower(),
                    trl=trl,
                    wave=wave,
                    depends_on=_parse_dependencies(row.get("depends_on") or ""),
                    owner=(row.get("owner") or "").strip(),
                    status=status,
                    paths=(row.get("paths") or "").strip(),
                    kpi=(row.get("kpi") or "").strip(),
                )
            )

    # شمارهٔ شناسه بر پایهٔ دسته‌بندی است نه ترتیب زمانی، پس شرط درست
    # «وابستگی در همان موج یا موج زودتر باشد» است، نه کوچک‌تر بودن شناسه.
    by_id = {item.id: item for item in items}
    for item in items:
        for dependency in item.depends_on:
            if dependency not in by_id:
                errors.append(f"item {item.id}: dependency {dependency} not in backlog")
                continue
            if dependency == item.id:
                errors.append(f"item {item.id}: depends on itself")
                continue
            other = by_id[dependency]
            if WAVE_ORDER.index(other.wave) > WAVE_ORDER.index(item.wave):
                errors.append(
                    f"item {item.id} ({item.wave}): depends on {dependency} "
                    f"which is in a later wave ({other.wave})"
                )

    return items, errors


def cmd_summary(items: list[Item], _args: argparse.Namespace) -> int:
    print(f"total items: {len(items)}")
    print()
    for label, wave in (("by wave", "wave"), ("by type", "type"), ("by status", "status")):
        counts = Counter(getattr(item, wave) for item in items)
        print(label + ":")
        for key in sorted(counts):
            print(f"  {key:<12} {counts[key]:>3}")
        print()
    counts = Counter(item.category for item in items)
    print("by category:")
    for key in sorted(counts):
        print(f"  {key:<12} {counts[key]:>3}")
    return 0


def cmd_status(items: list[Item], args: argparse.Namespace) -> int:
    selected = [item for item in items if item.wave == args.wave.upper()]
    if not selected:
        print(f"no items in wave {args.wave}")
        return 1
    print(WAVE_LABELS.get(args.wave.upper(), args.wave))
    print(f"items: {len(selected)}")
    print()
    for item in sorted(selected, key=lambda entry: entry.id):
        marker = {"done": "[x]", "in_progress": "[~]", "blocked": "[!]"}.get(item.status, "[ ]")
        print(f"  {marker} {item.id:>3}  {item.type:<12} {item.impact:<6} {item.title}")
    print()
    counts = Counter(item.status for item in selected)
    for status in ("done", "in_progress", "blocked", "todo", "deferred"):
        if counts.get(status):
            print(f"  {status:<12} {counts[status]:>3}")
    return 0


def cmd_ready(items: list[Item], _args: argparse.Namespace) -> int:
    done = {item.id for item in items if item.status == "done"}
    ready = [
        item
        for item in items
        if item.status == "todo" and all(dep in done for dep in item.depends_on)
    ]
    print(f"ready to start: {len(ready)}")
    for item in sorted(ready, key=lambda entry: entry.id):
        print(f"  {item.id:>3}  {item.wave}  {item.type:<12} {item.title}")
    return 0


def cmd_blocked(items: list[Item], _args: argparse.Namespace) -> int:
    done = {item.id for item in items if item.status == "done"}
    blocked = [
        item
        for item in items
        if item.status not in {"done", "deferred"}
        and any(dep not in done for dep in item.depends_on)
    ]
    print(f"blocked: {len(blocked)}")
    for item in sorted(blocked, key=lambda entry: entry.id):
        missing = [str(dep) for dep in item.depends_on if dep not in done]
        print(f"  {item.id:>3}  {item.wave}  waiting on {','.join(missing):<12} {item.title}")
    return 0


def cmd_kpi(items: list[Item], args: argparse.Namespace) -> int:
    selected = [item for item in items if args.wave is None or item.wave == args.wave.upper()]
    for item in sorted(selected, key=lambda entry: entry.id):
        if item.status != "done" and not args.all:
            continue
        print(f"  {item.id:>3}  [{item.status:<11}] {item.kpi}")
    return 0


def cmd_validate(_items: list[Item], _args: argparse.Namespace) -> int:
    items, errors = load_items(BACKLOG_PATH)
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"\n{len(errors)} validation error(s)")
        return 1
    print(f"OK {len(items)} items validated")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Eco Nojin innovation backlog tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", help="counts by wave, type, status and category")
    sub.add_parser("ready", help="items whose dependencies are all done")
    sub.add_parser("blocked", help="items waiting on a dependency")
    sub.add_parser("validate", help="schema validation for CI")

    status_parser = sub.add_parser("status", help="status of one wave")
    status_parser.add_argument("--wave", required=True, choices=sorted(VALID_WAVES))

    kpi_parser = sub.add_parser("kpi", help="KPIs of done items")
    kpi_parser.add_argument("--wave", choices=sorted(VALID_WAVES))
    kpi_parser.add_argument("--all", action="store_true", help="include unfinished items")

    return parser


COMMANDS = {
    "summary": cmd_summary,
    "status": cmd_status,
    "ready": cmd_ready,
    "blocked": cmd_blocked,
    "kpi": cmd_kpi,
    "validate": cmd_validate,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return COMMANDS[args.command]([], args)
    items, errors = load_items(BACKLOG_PATH)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    return COMMANDS[args.command](items, args)


if __name__ == "__main__":
    raise SystemExit(main())
