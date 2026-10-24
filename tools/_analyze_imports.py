import json
from collections import Counter

data = json.load(open("D:/HyDroMA/temp_imports.json"))
violations = data.get("violations", [])
print(f"Total violations in JSON: {len(violations)}")

unique_files = {v["file"] for v in violations}
print(f"Unique files with violations: {len(unique_files)}")

dst_counter = Counter(v["module"] for v in violations)
print("\nTop destination modules:")
for mod, count in dst_counter.most_common(20):
    print(f"  {mod}: {count}")

src_counter = Counter(v["file"].split("\\")[0] for v in violations)
print("\nSource directories:")
for src, count in src_counter.most_common():
    print(f"  {src}: {count}")
