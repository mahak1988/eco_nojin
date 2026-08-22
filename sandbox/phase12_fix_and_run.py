"""Phase 12 Fix v2 - proper module registration for dataclasses"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 1. Path setup
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
print(f"Added to sys.path: {PROJECT_ROOT}")

# 2. Ensure __init__.py files
print("\nChecking package structure:")
for p in [
    PROJECT_ROOT / "engine",
    PROJECT_ROOT / "engine" / "hydroma",
    PROJECT_ROOT / "engine" / "hydroma" / "models",
    PROJECT_ROOT / "engine" / "hydroma" / "models" / "global_watchdog",
    PROJECT_ROOT / "engine" / "hydroma" / "models" / "validation",
]:
    init = p / "__init__.py"
    if p.exists() and not init.exists():
        init.write_text('"""Package init."""\n', encoding="utf-8")
        print(f"  Created: {init.relative_to(PROJECT_ROOT)}")
    else:
        print(f"  OK: {p.relative_to(PROJECT_ROOT)}")

# 3. Test imports
print("\nTesting imports:")
try:
    from engine.hydroma.models.global_watchdog import KGCv5, WBIv3
    print("  OK: Global Watchdog (KGCv5, WBIv3)")
    from engine.hydroma.models import EWSI, HYRUE, ECSI, HDVI, EPIA, HPheno, ESRI, HLHS
    print("  OK: 8 Hydroma models")
except ImportError as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# 4. Register sandbox as a package so dataclasses works
sandbox_pkg = PROJECT_ROOT / "sandbox" / "__init__.py"
if not sandbox_pkg.exists():
    sandbox_pkg.write_text('"""Sandbox package."""\n', encoding="utf-8")

# 5. Load orchestrator with PROPER registration
print("\nLoading orchestrator...")
import importlib.util
orchestrator_path = PROJECT_ROOT / "sandbox" / "phase12_unified_orchestrator.py"
spec = importlib.util.spec_from_file_location(
    "sandbox.phase12_unified_orchestrator", orchestrator_path
)
module = importlib.util.module_from_spec(spec)

# CRITICAL: Register in sys.modules BEFORE exec_module
sys.modules["sandbox.phase12_unified_orchestrator"] = module
module.PROJECT_ROOT = PROJECT_ROOT

spec.loader.exec_module(module)

# 6. Run demo
print("\n" + "=" * 70)
print("Running Unified Orchestrator Demo")
print("=" * 70)
results = module.demo()

print(f"\nResult: {len(results)} regions analyzed successfully")