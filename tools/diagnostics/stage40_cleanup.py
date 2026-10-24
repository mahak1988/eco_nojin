import os
import shutil

print("=== listing health check ===", flush=True)
for d in (
    "D:/HyDroMA/engine/hydroma",
    "D:/HyDroMA/engine/hydroma/eval",
    "D:/HyDroMA/engine/hydroma/simulation",
    "D:/HyDroMA/engine/hydroma/models",
    "D:/HyDroMA/engine/hydroma/simulation/remote_sensing",
):
    try:
        n = len(os.listdir(d))
        print(f"  OK   {d} -> {n} entries", flush=True)
    except Exception as exc:
        print(f"  FAIL {d} -> {type(exc).__name__}", flush=True)

print()
print("=== hydrama_wrong contents ===", flush=True)
wrong = "D:/HyDroMA/engine/hydrama_wrong"
try:
    for dirpath, dirnames, filenames in os.walk(wrong):
        print("  ", dirpath, "dirs:", dirnames, "files:", filenames, flush=True)
except Exception as exc:
    print("  ERROR", exc, flush=True)

# Remove the empty leftover
try:
    total = sum(len(files) for _, _, files in os.walk(wrong))
    if total == 0:
        shutil.rmtree(wrong, ignore_errors=True)
        print()
        print("removed empty hydrama_wrong:", not os.path.exists(wrong), flush=True)
    else:
        print(f"\nhydrama_wrong NOT empty ({total} files) - left in place", flush=True)
except Exception as exc:
    print("  cleanup error:", exc, flush=True)

print()
print("=== engine/ after cleanup ===", flush=True)
for n in sorted(os.listdir("D:/HyDroMA/engine")):
    if "hydr" in n.lower():
        print("  ", repr(n), flush=True)
