"""Stage 41 — print the repository audit classification summary."""

from __future__ import annotations

import json
from pathlib import Path

PATH = Path("D:/HyDroMA/engine/reports/data/stage41_repo_audit.json")

d = json.loads(PATH.read_text(encoding="utf-8"))
print(f"collected: {d['collected']}  passed: {d['passed']}  failed: {d['failed']}")
print("by class:")
for k, v in sorted(d["by_class"].items(), key=lambda kv: -kv[1]):
    print(f"  {v:4}  {k}")
print()
print("one example per class:")
seen: set[str] = set()
for f in d["failures"]:
    c = f["cause"]
    if c in seen:
        continue
    seen.add(c)
    print(f"  [{c}] {f['file']}::{f['test']}")
    print(f"      {f['excerpt'][:120]}")
