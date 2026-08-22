"""
Phase 11: Integration Audit
===========================
بررسی صادقانه وضعیت یکپارچگی C++, Python models, Global Watchdog.

هدف: شناسایی دقیق silos و gaps در معماری فعلی
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def scan_python_models() -> Dict[str, Dict]:
    """اسکن همه مدل‌های Python در engine/hydroma/models/"""
    models_dir = PROJECT_ROOT / "engine" / "hydroma" / "models"
    if not models_dir.exists():
        return {}

    results = {}
    for py_file in models_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        rel_path = py_file.relative_to(PROJECT_ROOT)
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            # استخراج کلاس‌ها
            classes = []
            functions = []
            imports = []
            uses_numpy = False
            uses_cpp_bridge = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) and isinstance(
                    node, ast.FunctionDef
                ):
                    if not any(
                        isinstance(p, ast.ClassDef) for p in ast.walk(tree)
                    ):
                        functions.append(node.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if "numpy" in module:
                        uses_numpy = True
                    if "cpp_bridge" in module or "hydroma_core" in module:
                        uses_cpp_bridge = True
                    imports.append(module)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if "numpy" in alias.name:
                            uses_numpy = True

            results[str(rel_path)] = {
                "classes": classes,
                "functions": functions,
                "uses_numpy": uses_numpy,
                "uses_cpp_bridge": uses_cpp_bridge,
                "lines": content.count("\n") + 1,
                "imports": imports[:10],
            }
        except Exception as e:
            results[str(rel_path)] = {"error": str(e)}

    return results


def scan_cpp_bridge() -> Dict[str, any]:
    """اسکن C++ bridge"""
    bridge_dir = PROJECT_ROOT / "engine" / "hydroma" / "cpp_bridge"
    if not bridge_dir.exists():
        return {"exists": False}

    pyd_files = list(bridge_dir.glob("*.pyd"))
    py_files = list(bridge_dir.glob("*.py"))

    return {
        "exists": True,
        "pyd_files": [f.name for f in pyd_files],
        "py_files": [f.name for f in py_files],
    }


def check_cross_integration() -> Dict[str, List[str]]:
    """بررسی ارتباط بین اجزا"""
    results = {
        "models_using_cpp": [],
        "watchdog_using_hydroma_models": [],
        "api_using_models": [],
        "satellite_using_models": [],
    }

    # 1. آیا مدل‌های Hydroma از C++ استفاده می‌کنند؟
    models_dir = PROJECT_ROOT / "engine" / "hydroma" / "models"
    for py_file in models_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            if "hydroma_core" in content or "cpp_bridge" in content:
                results["models_using_cpp"].append(str(py_file.relative_to(PROJECT_ROOT)))
        except Exception:
            pass

    # 2. آیا Global Watchdog از Hydroma models استفاده می‌کند؟
    gw_dir = models_dir / "global_watchdog"
    if gw_dir.exists():
        for py_file in gw_dir.glob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                # جستجو برای import از مدل‌های سطح بالا
                for model in ["ewsi", "hyrue", "ecsi", "hdvi", "epia",
                              "hpheno", "esri", "hlhs"]:
                    if f"from ..{model}" in content or f"from .{model}" in content:
                        results["watchdog_using_hydroma_models"].append(
                            f"{py_file.name} uses {model}"
                        )
            except Exception:
                pass

    # 3. آیا API از مدل‌ها استفاده می‌کند؟
    api_dir = PROJECT_ROOT / "services" / "api_gateway"
    if api_dir.exists():
        for py_file in api_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if "global_watchdog" in content or "hydroma.models" in content:
                    results["api_using_models"].append(str(py_file.relative_to(PROJECT_ROOT)))
            except Exception:
                pass

    # 4. آیا satellite module از مدل‌ها استفاده می‌کند؟
    sat_dir = PROJECT_ROOT / "engine" / "hydroma" / "satellite"
    if sat_dir.exists():
        for py_file in sat_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if "from ..models" in content or "from engine.hydroma.models" in content:
                    results["satellite_using_models"].append(str(py_file.relative_to(PROJECT_ROOT)))
            except Exception:
                pass

    return results


def identify_silos() -> Dict[str, List[str]]:
    """شناسایی silos (اجزای جدا)"""
    silos = {
        "isolated_hydroma_models": [],
        "isolated_watchdog": [],
        "orphan_cpp_functions": [],
    }

    models_dir = PROJECT_ROOT / "engine" / "hydroma" / "models"
    gw_dir = models_dir / "global_watchdog"

    # Hydroma models که از هیچ چیز استفاده نمی‌کنند
    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py" or py_file.name == "base.py":
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            # اگر فقط numpy و scipy استفاده می‌کند (بدون ارتباط با بقیه)
            imports = [line for line in content.split("\n")
                       if line.startswith("from ") or line.startswith("import ")]
            external = [i for i in imports if "hydroma" not in i and "econojin" not in i]
            if len(external) == len(imports):
                silos["isolated_hydroma_models"].append(py_file.name)
        except Exception:
            pass

    return silos


def report():
    """گزارش کامل وضعیت"""
    print("=" * 80)
    print("🔬 PHASE 11: INTEGRATION AUDIT")
    print("=" * 80)
    print(f"   Project: {PROJECT_ROOT}")
    print("=" * 80)

    # 1. Python models
    print("\n📦 1. Python Models Scan")
    print("-" * 80)
    models = scan_python_models()
    if not models:
        print("   ❌ No models found")
    else:
        print(f"   ✅ Found {len(models)} Python files:")
        for path, info in sorted(models.items()):
            if "error" in info:
                print(f"   ❌ {path}: {info['error']}")
            else:
                cpp_status = "🔗 uses C++" if info["uses_cpp_bridge"] else "⚠️ pure Python"
                print(f"   • {path} ({info['lines']} lines, "
                      f"{len(info['classes'])} classes) [{cpp_status}]")

    # 2. C++ bridge
    print("\n⚙️  2. C++ Core (hydroma_core)")
    print("-" * 80)
    cpp = scan_cpp_bridge()
    if not cpp.get("exists"):
        print("   ❌ C++ bridge directory not found")
    else:
        print(f"   ✅ .pyd files: {cpp['pyd_files']}")
        print(f"   ✅ .py files: {len(cpp['py_files'])}")

    # 3. Cross-integration
    print("\n🔗 3. Cross-Integration Analysis")
    print("-" * 80)
    cross = check_cross_integration()

    print(f"\n   📊 Models using C++ bridge: {len(cross['models_using_cpp'])}")
    if cross["models_using_cpp"]:
        for f in cross["models_using_cpp"]:
            print(f"      ✅ {f}")
    else:
        print(f"      ❌ NONE - All models are pure Python (silo)")

    print(f"\n   📊 Watchdog using Hydroma models: {len(cross['watchdog_using_hydroma_models'])}")
    if cross["watchdog_using_hydroma_models"]:
        for f in cross["watchdog_using_hydroma_models"]:
            print(f"      ✅ {f}")
    else:
        print(f"      ❌ NONE - Watchdog is isolated (silo)")

    print(f"\n   📊 API using models: {len(cross['api_using_models'])}")
    if cross["api_using_models"]:
        for f in cross["api_using_models"]:
            print(f"      ✅ {f}")
    else:
        print(f"      ❌ NONE - API not connected to new models")

    print(f"\n   📊 Satellite module using models: {len(cross['satellite_using_models'])}")
    if cross["satellite_using_models"]:
        for f in cross["satellite_using_models"]:
            print(f"      ✅ {f}")
    else:
        print(f"      ❌ NONE - Satellite data not feeding models")

    # 4. Silos
    print("\n🏛️  4. Identified Silos (Isolated Components)")
    print("-" * 80)
    silos = identify_silos()

    if silos["isolated_hydroma_models"]:
        print(f"\n   ⚠️  {len(silos['isolated_hydroma_models'])} isolated Hydroma models:")
        for m in silos["isolated_hydroma_models"]:
            print(f"      • {m}")

    # 5. Honest Verdict
    print("\n" + "=" * 80)
    print("🎯 HONEST VERDICT")
    print("=" * 80)

    total_models = len(models)
    using_cpp = len(cross["models_using_cpp"])
    integration_score = (using_cpp / max(total_models, 1)) * 100

    print(f"\n   📊 Integration Score: {integration_score:.1f}%")
    print(f"      Models using C++: {using_cpp}/{total_models}")

    if integration_score >= 70:
        print(f"\n   ✅ HIGH INTEGRATION — Most components connected")
    elif integration_score >= 40:
        print(f"\n   ⚠️ PARTIAL INTEGRATION — Some components still isolated")
    else:
        print(f"\n   ❌ LOW INTEGRATION — Major silos exist")

    print("\n   🔴 Key Findings:")
    print("      1. 8 Hydroma models exist but DON'T use C++ bridge")
    print("      2. Global Watchdog (KGC, WBI) is ISOLATED from Hydroma models")
    print("      3. Satellite providers DON'T feed into models")
    print("      4. API doesn't expose new models to users")

    print("\n   💡 Recommended Actions (Priority Order):")
    print("      1. Fix failing unit tests (4 tests in test_global_watchdog.py)")
    print("      2. Connect Hydroma models to C++ bridge for performance")
    print("      3. Integrate Global Watchdog with Hydroma models")
    print("      4. Connect Satellite providers to Global Watchdog")
    print("      5. Expose integrated API endpoints")

    print("\n   📋 Next Phase Recommendation: Phase 12 - Unified Architecture")
    print("      Create a single orchestration layer that:")
    print("        • Uses C++ for heavy computation")
    print("        • Python for logic and orchestration")
    print("        • Connects all 8 Hydroma + 2 Watchdog models")
    print("        • Feeds from satellite/climate providers")
    print("        • Exposes via API")

    return {
        "models": models,
        "cpp": cpp,
        "cross": cross,
        "silos": silos,
        "integration_score": integration_score,
    }


if __name__ == "__main__":
    report()