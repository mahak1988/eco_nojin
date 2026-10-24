"""Runtime environment diagnostic for the HYDROMA engine.

Reports the execution environment and the import resolution state of the
engine package hierarchy. Used during Stage 37/39 to diagnose the
import failures that the "filesystem visibility" reports described.

Usage:
    python tools/diagnostics/stage37_runtime_diagnostic.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path("D:/HyDroMA")


def _listdir(path: str) -> list[str]:
    try:
        return sorted(os.listdir(path))
    except OSError as exc:
        return [f"<unreadable: {exc}>"]


def main() -> int:
    print("=" * 68)
    print("HYDROMA runtime diagnostic")
    print("=" * 68)
    print(f"python : {sys.executable}")
    print(f"version: {sys.version.split()[0]}")
    print(f"cwd    : {os.getcwd()}")
    print()

    print("-- sys.path --")
    for i, p in enumerate(sys.path):
        print(f"  {i}: {p}")
    print()

    print("-- engine package directories --")
    for rel in (
        "engine",
        "engine/hydrama",
        "engine/hydroma/models",
        "engine/hydroma/simulation",
        "engine/hydroma/simulation/remote_sensing",
        "engine/hydroma/eval",
    ):
        path = str(ROOT / rel)
        exists = os.path.isdir(path)
        print(f"  {rel}: exists={exists}")
        if exists:
            names = _listdir(path)
            py = [n for n in names if n.endswith(".py")]
            print(f"      {len(names)} entries, {len(py)} .py")
    print()

    print("-- import resolution --")
    bootstrap_path = ROOT / "engine" / "hydroma" / "eval" / "runtime_bootstrap.py"
    if bootstrap_path.exists():
        spec = importlib.util.spec_from_file_location(
            "_rt_diag", str(bootstrap_path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["_rt_diag"] = module
        spec.loader.exec_module(module)
        module.ensure_engine_importable()
        for name in (
            "engine",
            "engine.hydroma",
            "engine.hydroma.models.hyrue",
            "engine.hydroma.simulation.weather_source",
            "engine.hydroma.simulation.par_pipeline",
            "engine.hydroma.simulation.radiation_units",
            "engine.hydroma.eval.seasonal_predictor",
        ):
            try:
                module.load_module(name)
                print(f"  OK   {name}")
            except Exception as exc:
                print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    else:
        print("  runtime_bootstrap.py not found")
    print()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
