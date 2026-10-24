"""Stage 41 — diagnose shard overlap in the benchmark results."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

SHARDS = Path(
    "D:/HyDroMA/engine/reports/data/stage41_test_benchmark/shards"
)

where: dict[str, list[str]] = defaultdict(list)
per_shard: dict[str, set[str]] = {}

for shard_dir in sorted(SHARDS.glob("shard_*")):
    path = shard_dir / "record_results.jsonl"
    ids: set[str] = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rid = str(json.loads(line)["record_id"])
                    ids.add(rid)
                    where[rid].append(shard_dir.name)
    per_shard[shard_dir.name] = ids

total = sum(len(v) for v in per_shard.values())
unique = len(where)
print(f"shards        : {len(per_shard)}")
print(f"total lines   : {total}")
print(f"unique records: {unique}")
print()
overlap = {k: v for k, v in where.items() if len(v) > 1}
print(f"records in more than one shard: {len(overlap)}")
for rid, shards in list(overlap.items())[:5]:
    print(f"  {rid}: {shards}")
print()
# Do the shard id sets actually partition the frame?
allsets = list(per_shard.values())
print(f"shard id-set sizes: {[len(s) for s in allsets]}")
if len(allsets) > 1:
    a, b = allsets[0], allsets[1]
    print(f"shard00 ∩ shard01 = {len(a & b)}")
    print(f"shard00 ∪ shard01 = {len(a | b)}")
