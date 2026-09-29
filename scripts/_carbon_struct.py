"""شمار سطرهای جدولی و سرفصل‌ها در یک فایل و در نسخهٔ پشتیبان.

اجرا:
  python scripts/_carbon_struct.py <file> <backup>
"""

from __future__ import annotations

import io
import re
import sys

CHAPTER = re.compile(r"^(?:#{1,6}\s*)?(بخش|فصل|۱۳-۲-|۹-۹|۱۵-|۱۶-|۱-۷|۱-۸|۱-۴|۱-۵)")


def profile(path: str) -> dict[str, int]:
    lines = io.open(path, encoding="utf-8").read().split("\n")
    heads = {}
    for line in lines:
        if CHAPTER.match(line.strip()) or line.startswith("بخش ") or line.startswith("فصل "):
            key = line.strip()[:40]
            heads[key] = heads.get(key, 0) + 1
    return {
        "lines": len(lines),
        "tab_rows": sum(1 for line in lines if "\t" in line),
        "nonempty": sum(1 for line in lines if line.strip()),
        "chars": sum(len(line) for line in lines),
        "headings": len(heads),
    }


def main() -> int:
    a, b = profile(sys.argv[1]), profile(sys.argv[2])
    for key in ("lines", "tab_rows", "nonempty", "chars", "headings"):
        print(f"{key:>10}: backup {a[key]:>8} -> now {b[key]:>8}  ({b[key] - a[key]:+d})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
