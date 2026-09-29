"""شمار سطرهای جدول markdown (سطرهای آغازشونده با |) به تفکیک بلوک جدول.

اجرا: python scripts/_carbon_md_tables.py <backup> <file>
"""

from __future__ import annotations

import io
import sys


def blocks(path: str) -> dict[str, int]:
    out: dict[str, int] = {}
    label = "booting"
    prev_blank = True
    for line in io.open(path, encoding="utf-8").read().split("\n"):
        if line.startswith("|"):
            if prev_blank:
                label = line[:70]
                out.setdefault(label, 0)
            out[label] += 1
            prev_blank = False
        else:
            prev_blank = not line.strip()
    return out


def main() -> int:
    a, b = blocks(sys.argv[1]), blocks(sys.argv[2])
    print(f"backup table blocks: {len(a)}   current: {len(b)}")
    lost = 0
    for key, n in a.items():
        m = b.get(key)
        if m is None:
            print(f"  LOST block: {key[:60]}  (backup {n} rows)")
            lost += n
        elif m != n:
            print(f"  CHANGED: {key[:60]}  {n} -> {m}  ({m - n:+d})")
            if m < n:
                lost += n - m
    print(f"rows lost overall: {lost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
