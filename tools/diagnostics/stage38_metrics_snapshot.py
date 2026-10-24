"""Compute metrics from the current Stage 39 benchmark results (snapshot)."""

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

_spec = importlib.util.spec_from_file_location(
    "_rt", "D:/HyDroMA/engine/hydroma/eval/runtime_bootstrap.py"
)
_rt = importlib.util.module_from_spec(_spec)
sys.modules["_rt"] = _rt
_spec.loader.exec_module(_rt)
_rt.ensure_engine_importable()

metrics = _rt.load_module("engine.hydroma.eval.stage39_benchmark")

results_path = Path(
    "D:/HyDroMA/engine/reports/data/stage39_benchmark/record_results.jsonl"
)
records = []
with open(results_path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

m = metrics.compute_benchmark_metrics(records, group="test_snapshot")
print("=== overall (snapshot) ===")
print("n       :", m.n)
print("RMSE    :", None if m.rmse is None else round(m.rmse, 4))
print("MAE     :", None if m.mae is None else round(m.mae, 4))
print("Bias    :", None if m.bias is None else round(m.bias, 4))
print("R2      :", None if m.r2 is None else round(m.r2, 4))
print("MAPE    :", None if m.mape is None else round(m.mape, 2))
print("mape excl:", m.mape_excluded)

print()
print("=== by district ===")
for k, v in metrics.compute_grouped_metrics(records, "district_id").items():
    print(
        f"  {k}: n={v.n} rmse={None if v.rmse is None else round(v.rmse,3)} "
        f"bias={None if v.bias is None else round(v.bias,3)} "
        f"r2={None if v.r2 is None else round(v.r2,3)}"
    )

print()
print("=== by season ===")
for k, v in metrics.compute_grouped_metrics(records, "season").items():
    print(f"  {k}: n={v.n} rmse={None if v.rmse is None else round(v.rmse,3)}")

print()
print("=== uncertainty ===")
b = metrics.cluster_bootstrap_uncertainty(records)
print("status      :", b.get("status"))
print("n_districts :", b.get("n_districts"))
print("n_records   :", b.get("n_records"))
if b.get("status") == "OK":
    print("rmse mean   :", round(b["rmse_mean"], 4))
    print("rmse 95% CI :", [round(x, 4) for x in b["rmse_ci"]])
