"""ابزار خواندنی — شمارش فصل و جدول برای سه کتابچه.

این اسکریپت فقط می‌خواند. هیچ فایلی را تغییر نمی‌دهد.

معیارها عیناً از ``scripts/audit_booklets.py`` کپی شده‌اند تا خروجی این ابزار
با خروجی ممیز یکی باشد: همان ``_CHAPTER_LOOSE``، همان ``table_census`` و همان
منطق «اولین occurrence». اگر یکی از این دو تغییر کند، این ابزار باید هم‌زمان
تغییر کند.

کاربرد:
    python scripts/census_tool.py
    python scripts/census_tool.py --file HP-16
    python scripts/census_tool.py --file HP-16 --baseline
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BOOKS = ROOT / "کتابها"
BASELINE = HERE / "table_census_baseline.csv"

CHAPTER_FLOORS = {
    1: 320, 2: 350, 3: 400, 4: 200, 5: 250, 6: 280,
    7: 170, 8: 200, 9: 350, 10: 450, 11: 280, 12: 250,
}

TARGETS = [
    "HP-16 پایداری شیب.txt",
    "HP-22 صنایع تبدیل.txt",
    "HP-23 حکمرانی و اشتغال.txt",
]

_FA = "۰۱۲۳۴۵۶۷۸۹"
_MAP = str.maketrans(_FA, "0123456789")
_CHAPTER_LOOSE = re.compile(r"^(?:#{1,6}\s*)?فصل\s+([۰-۹]+)\s+—")
_TABLE_HEADER = re.compile(r"^\s*(?:جدول|شکل)\s+([۰-۹\d]+[٫٬.][۰-۹\d]+)\s*[-—:]")


def chapter_sizes(lines: list[str]) -> dict[int, tuple[int, int, str]]:
    """شمارهٔ فصل → (شمار سطر، شمارهٔ خط شروع، متن سرفصل)."""
    first: dict[int, tuple[int, str]] = {}
    for index, line in enumerate(lines, start=1):
        match = _CHAPTER_LOOSE.match(line)
        if not match:
            continue
        number = int(match.group(1).translate(_MAP))
        if number in CHAPTER_FLOORS and number not in first:
            first[number] = (index, line.strip()[:56])
    order = sorted((start, number) for number, (start, _) in first.items())
    out: dict[int, tuple[int, int, str]] = {}
    for position, (start, number) in enumerate(order):
        end = order[position + 1][0] - 1 if position + 1 < len(order) else len(lines)
        out[number] = (end - start + 1, start, first[number][1])
    return out


def table_census(text: str) -> dict[str, int]:
    census: dict[str, int] = {}
    current: str | None = None
    for line in text.split("\n"):
        match = _TABLE_HEADER.match(line)
        if match:
            current = match.group(1)
            census.setdefault(current, 0)
            continue
        if current and ("\t" in line or line.strip().startswith("|")):
            census[current] += 1
        elif current and not line.strip():
            continue
        elif current:
            current = None
    return census


def load_baseline() -> dict[tuple[str, str], int]:
    if not BASELINE.exists():
        return {}
    rows: dict[tuple[str, str], int] = {}
    with BASELINE.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[(row["file"], row["table"])] = int(row["rows"])
    return rows


def report(name: str, with_baseline: bool) -> None:
    text = (BOOKS / name).read_text(encoding="utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    sizes = chapter_sizes(lines)
    print(f"\n=== {name} · {len(lines)} سطر ===")
    short = 0
    for number, (count, start, title) in sorted(sizes.items()):
        floor = CHAPTER_FLOORS[number]
        flag = "" if count >= floor else f"   ✗ کسر {floor - count}"
        short += max(0, floor - count)
        print(f"  فصل {number:>2}  {count:>5} / {floor:<4}{flag:<18} L{start:<5} {title}")
    print(f"  جمع کسر: {short}   ·   تعداد جدول: {len(table_census(text))}")
    if not with_baseline:
        return
    baseline = load_baseline()
    census = table_census(text)
    drift = []
    for (file_name, table), base_rows in sorted(baseline.items()):
        if file_name != name:
            continue
        if table not in census:
            drift.append(f"{table}: {base_rows} → حذف")
        elif census[table] < base_rows:
            drift.append(f"{table}: {base_rows} → {census[table]}")
    print(f"  افت جدول نسبت به خط پایه: {drift if drift else 'هیچ'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="")
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    for name in TARGETS:
        if args.file and not name.startswith(args.file):
            continue
        report(name, args.baseline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
