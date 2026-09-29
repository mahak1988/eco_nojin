"""مقایسهٔ سطر و سطر-جدول یک فایل با نسخهٔ پشتیبان تاریخ‌دار.

اجرا:
  python scripts/_carbon_drift.py <file> <backup>
خروجی: تعداد سطر، سطرهای جدید، سطرهای حذف‌شده، و شمار سطر هر جدول در هر دو نسخه.
"""

from __future__ import annotations

import io
import re
import sys
from collections import Counter

HEADER = re.compile(r"^\s*(?:جدول|شکل)\s+([۰-۹\d]+[٫٬.][۰-۹\d]+)\s*(?:[-—:،]|\t|$)")


def census(lines: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    current: str | None = None
    for line in lines:
        m = HEADER.match(line)
        if m:
            current = m.group(1)
            out.setdefault(current, 0)
            continue
        if current and ("\t" in line or line.strip().startswith("|")):
            out[current] += 1
        elif current and not line.strip():
            continue
        elif current:
            current = None
    return out


def main() -> int:
    new_path, bak_path = sys.argv[1], sys.argv[2]
    new = io.open(new_path, encoding="utf-8").read().split("\n")
    bak = io.open(bak_path, encoding="utf-8").read().split("\n")

    print(f"file    : {new_path}")
    print(f"lines   : backup {len(bak)} -> now {len(new)}  (delta {len(new) - len(bak):+d})")

    cn, cb = census(new), census(bak)
    keys = sorted(set(cn) | set(cb), key=lambda k: (len(k), k))
    for k in keys:
        a, b = cb.get(k), cn.get(k)
        flag = "  " if a == b else ("DROP" if (a or 0) > (b or 0) else "ADD ")
        print(f"  {flag} table {k}: {a} -> {b}")

    removed = Counter(bak) - Counter(new)
    added = Counter(new) - Counter(bak)
    print(f"\nremoved distinct lines: {len(removed)} (total {sum(removed.values())})")
    for line, n in list(removed.items())[:40]:
        print(f"  -{n}  {line[:110]}")
    print(f"\nadded distinct lines: {len(added)} (total {sum(added.values())})")
    for line, n in list(added.items())[:40]:
        print(f"  +{n}  {line[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
