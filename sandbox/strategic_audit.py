"""
Strategic Audit: Comprehensive Repository Analysis
===================================================

Before transforming the architecture, we must understand the current state.

This script analyzes:
1. Repository structure (directories, files, sizes)
2. Git history (commits, contributors, evolution)
3. Code quality (lines, complexity, dependencies)
4. Test coverage (passed/failed, coverage %)
5. Execution balance (what was planned vs what shipped)
6. Technology inventory (what we actually have)

Output: Comprehensive report for strategic decision-making.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

PROJECT_ROOT = Path(r"D:\eco_nojin")
REPORT_FILE = PROJECT_ROOT / "reports" / "strategic_audit.md"


# ============================================================================
# 1. Repository Structure Analysis
# ============================================================================

def scan_structure() -> Dict[str, Any]:
    """Scan the repository structure with detailed metrics."""
    print("\n[1/6] Scanning repository structure...")
    
    stats = {
        "total_files": 0,
        "total_lines": 0,
        "by_extension": defaultdict(lambda: {"count": 0, "lines": 0, "bytes": 0}),
        "by_directory": defaultdict(lambda: {"count": 0, "lines": 0, "bytes": 0}),
        "large_files": [],  # >1000 lines
        "empty_files": [],
        "key_files": {},
    }
    
    # Ignore patterns
    ignore_dirs = {
        ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
        ".ruff_cache", ".satellite_cache", ".dvc", ".cache", ".vscode",
        "dist", "build", ".next", "out", ".turbo", "econojin.egg-info",
        "_backups_fix", "_trash",
    }
    
    key_file_names = {
        "pyproject.toml", "package.json", "README.md", "requirements.txt",
        "docker-compose.yml", "Dockerfile", "turbo.json", "alembic.ini",
    }
    
    # Walk directory
    for path in PROJECT_ROOT.rglob("*"):
        # Skip ignored dirs
        parts = set(path.parts)
        if parts & ignore_dirs:
            continue
        
        if path.is_file():
            try:
                size = path.stat().st_size
                ext = path.suffix.lower() or "(no ext)"
                rel_path = path.relative_to(PROJECT_ROOT)
                
                stats["total_files"] += 1
                stats["by_extension"][ext]["count"] += 1
                stats["by_extension"][ext]["bytes"] += size
                
                # Count lines for text files
                if ext in {".py", ".js", ".ts", ".tsx", ".jsx", ".sql", ".md", 
                           ".json", ".yaml", ".yml", ".toml", ".txt", ".html", 
                           ".css", ".sh", ".ps1", ".rs", ".cpp", ".hpp", ".c"}:
                    try:
                        lines = len(path.read_text(encoding="utf-8", errors="ignore").split("\n"))
                        stats["total_lines"] += lines
                        stats["by_extension"][ext]["lines"] += lines
                        
                        # Track large files
                        if lines > 1000:
                            stats["large_files"].append({
                                "path": str(rel_path),
                                "lines": lines,
                                "ext": ext,
                            })
                        
                        if lines == 0:
                            stats["empty_files"].append(str(rel_path))
                    except Exception:
                        pass
                
                # Directory stats
                parent = rel_path.parent
                if parent != Path("."):
                    dir_name = parent.parts[0] if parent.parts else "root"
                    stats["by_directory"][dir_name]["count"] += 1
                    stats["by_directory"][dir_name]["bytes"] += size
                
                # Key files
                if path.name in key_file_names:
                    stats["key_files"][str(rel_path)] = {
                        "size": size,
                        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                    }
            
            except Exception as e:
                continue
    
    # Sort by size
    stats["large_files"].sort(key=lambda x: x["lines"], reverse=True)
    
    return stats


# ============================================================================
# 2. Git History Analysis
# ============================================================================

def analyze_git_history() -> Dict[str, Any]:
    """Analyze git commit history."""
    print("[2/6] Analyzing git history...")
    
    result = {
        "total_commits": 0,
        "first_commit": None,
        "last_commit": None,
        "days_active": 0,
        "commit_frequency": {},
        "branches": [],
        "top_messages": [],
        "recent_commits": [],
        "phase_commits": defaultdict(int),
    }
    
    try:
        # Total commits
        output = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if output.returncode == 0:
            result["total_commits"] = int(output.stdout.strip())
        
        # First commit date
        output = subprocess.run(
            ["git", "log", "--reverse", "--format=%ci", "--max-count=1"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if output.returncode == 0:
            result["first_commit"] = output.stdout.strip()
        
        # Last commit
        output = subprocess.run(
            ["git", "log", "--format=%ci|%s", "--max-count=1"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if output.returncode == 0 and "|" in output.stdout:
            date_str, msg = output.stdout.strip().split("|", 1)
            result["last_commit"] = {"date": date_str, "message": msg}
        
        # Branches
        output = subprocess.run(
            ["git", "branch", "-a"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if output.returncode == 0:
            result["branches"] = [b.strip() for b in output.stdout.split("\n") if b.strip()]
        
        # Recent commits (last 50)
        output = subprocess.run(
            ["git", "log", "--format=%h|%ci|%s", "--max-count=50"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if output.returncode == 0:
            for line in output.stdout.split("\n"):
                if "|" in line:
                    parts = line.split("|", 2)
                    if len(parts) == 3:
                        hash_, date, msg = parts
                        result["recent_commits"].append({
                            "hash": hash_,
                            "date": date,
                            "message": msg,
                        })
                        
                        # Categorize by phase keywords
                        msg_lower = msg.lower()
                        for keyword in ["phase", "feat", "fix", "refactor", "docs", "test", "wip"]:
                            if keyword in msg_lower:
                                result["phase_commits"][keyword] += 1
                                break
                        else:
                            result["phase_commits"]["other"] += 1
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================================
# 3. Code Quality Analysis (Python)
# ============================================================================

def analyze_python_code() -> Dict[str, Any]:
    """Analyze Python code quality metrics."""
    print("[3/6] Analyzing Python code quality...")
    
    result = {
        "total_py_files": 0,
        "total_py_lines": 0,
        "total_classes": 0,
        "total_functions": 0,
        "total_imports": 0,
        "syntax_errors": [],
        "largest_files": [],
        "import_dependencies": defaultdict(int),
        "modules_by_purpose": {
            "science_models": [],
            "api_endpoints": [],
            "tests": [],
            "sandbox_scripts": [],
            "config": [],
            "other": [],
        },
    }
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        # Skip ignored
        parts = py_file.parts
        if any(p in parts for p in {".venv", "node_modules", "__pycache__", 
                                     ".pytest_cache", "_trash", "_backups_fix"}):
            continue
        
        rel_path = py_file.relative_to(PROJECT_ROOT)
        
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = len(content.split("\n"))
            
            result["total_py_files"] += 1
            result["total_py_lines"] += lines
            
            # Categorize
            path_str = str(rel_path)
            if "test" in path_str or path_str.startswith("tests/"):
                result["modules_by_purpose"]["tests"].append(path_str)
            elif path_str.startswith("sandbox/"):
                result["modules_by_purpose"]["sandbox_scripts"].append(path_str)
            elif path_str.startswith("engine/hydroma/models"):
                result["modules_by_purpose"]["science_models"].append(path_str)
            elif "api" in path_str or "endpoint" in path_str or "service" in path_str:
                result["modules_by_purpose"]["api_endpoints"].append(path_str)
            elif any(name in path_str for name in ["config", "settings", "pyproject"]):
                result["modules_by_purpose"]["config"].append(path_str)
            else:
                result["modules_by_purpose"]["other"].append(path_str)
            
            # Parse AST
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        result["total_classes"] += 1
                    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                        result["total_functions"] += 1
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        result["total_imports"] += 1
                        if isinstance(node, ast.ImportFrom) and node.module:
                            # Top-level module
                            top_module = node.module.split(".")[0]
                            result["import_dependencies"][top_module] += 1
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                top_module = alias.name.split(".")[0]
                                result["import_dependencies"][top_module] += 1
            except SyntaxError as e:
                result["syntax_errors"].append({
                    "file": str(rel_path),
                    "line": e.lineno,
                    "msg": e.msg,
                })
            
            # Track largest files
            result["largest_files"].append({
                "path": str(rel_path),
                "lines": lines,
            })
            
        except Exception as e:
            continue
    
    result["largest_files"].sort(key=lambda x: x["lines"], reverse=True)
    result["largest_files"] = result["largest_files"][:20]
    
    # Top 20 imports
    top_imports = sorted(
        result["import_dependencies"].items(),
        key=lambda x: x[1],
        reverse=True,
    )[:20]
    result["top_imports"] = top_imports
    
    return result


# ============================================================================
# 4. Test Analysis
# ============================================================================

def run_tests() -> Dict[str, Any]:
    """Run pytest and collect results."""
    print("[4/6] Running test suite...")
    
    result = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "failed_tests": [],
        "duration_seconds": 0,
        "test_files": 0,
    }
    
    try:
        t0 = time.time()
        output = subprocess.run(
            [sys.executable, "-m", "pytest", 
             "--tb=no", "-q", 
             "--disable-warnings",
             "tests/"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        result["duration_seconds"] = time.time() - t0
        
        # Parse output
        stdout = output.stdout
        stderr = output.stderr
        combined = stdout + "\n" + stderr
        
        # Look for summary line like "X passed, Y failed, Z skipped"
        for line in combined.split("\n"):
            line = line.strip()
            if "passed" in line and any(c.isdigit() for c in line):
                # Parse numbers
                import re
                passed_match = re.search(r"(\d+) passed", line)
                failed_match = re.search(r"(\d+) failed", line)
                skipped_match = re.search(r"(\d+) skipped", line)
                error_match = re.search(r"(\d+) error", line)
                
                if passed_match:
                    result["passed"] = int(passed_match.group(1))
                if failed_match:
                    result["failed"] = int(failed_match.group(1))
                if skipped_match:
                    result["skipped"] = int(skipped_match.group(1))
                if error_match:
                    result["errors"] = int(error_match.group(1))
                
                result["total_tests"] = (
                    result["passed"] + result["failed"] + 
                    result["skipped"] + result["errors"]
                )
                break
        
        # Count test files
        test_dir = PROJECT_ROOT / "tests"
        if test_dir.exists():
            result["test_files"] = sum(
                1 for f in test_dir.rglob("test_*.py")
            )
        
        # Capture failure details
        if result["failed"] > 0:
            for line in combined.split("\n"):
                if "FAILED" in line and "::" in line:
                    result["failed_tests"].append(line.strip()[:150])
                    if len(result["failed_tests"]) >= 10:
                        break
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================================
# 5. Execution Balance: Planned vs Delivered
# ============================================================================

def analyze_execution_balance() -> Dict[str, Any]:
    """Compare planned phases vs what's actually delivered."""
    print("[5/6] Analyzing execution balance...")
    
    result = {
        "planned_phases": {},
        "delivered_components": {},
        "gaps": [],
        "overdelivery": [],
    }
    
    # Scan for evidence of each planned phase
    phases = {
        "1-C++ Core": {
            "evidence": ["engine/hydroma/cpp_bridge", "hydroma_core.pyd", "hydroma_core.so"],
            "files_found": [],
            "status": "not_found",
        },
        "2-Hydroma Models": {
            "evidence": [
                "engine/hydroma/models/ewsi.py",
                "engine/hydroma/models/hyrue.py",
                "engine/hydroma/models/ecsi.py",
                "engine/hydroma/models/hdvi.py",
                "engine/hydroma/models/epia.py",
                "engine/hydroma/models/hpheno.py",
                "engine/hydroma/models/esri.py",
                "engine/hydroma/models/hlhs.py",
            ],
            "files_found": [],
            "status": "not_found",
        },
        "3-Global Watchdog": {
            "evidence": [
                "engine/hydroma/models/global_watchdog/koppen.py",
                "engine/hydroma/models/global_watchdog/wbi.py",
                "engine/hydroma/models/global_watchdog/watchdog.py",
            ],
            "files_found": [],
            "status": "not_found",
        },
        "4-Unified Orchestrator": {
            "evidence": ["sandbox/phase12_unified_orchestrator.py"],
            "files_found": [],
            "status": "not_found",
        },
        "5-FastAPI Endpoint": {
            "evidence": ["sandbox/phase13_api_endpoint.py"],
            "files_found": [],
            "status": "not_found",
        },
        "6-Real Data Integration": {
            "evidence": ["sandbox/phase14_real_data_integration.py"],
            "files_found": [],
            "status": "not_found",
        },
        "7-Local-First Design": {
            "evidence": ["docs/architecture/local_first/README.md"],
            "files_found": [],
            "status": "not_found",
        },
        "8-Hybrid PWA (Phase 17)": {
            "evidence": ["apps/web/package.json", "packages/core/package.json"],
            "files_found": [],
            "status": "not_found",
        },
    }
    
    # Check each phase
    for phase_name, phase_data in phases.items():
        for evidence_path in phase_data["evidence"]:
            full_path = PROJECT_ROOT / evidence_path
            if full_path.exists():
                phase_data["files_found"].append(evidence_path)
        
        if len(phase_data["files_found"]) == len(phase_data["evidence"]):
            phase_data["status"] = "complete"
        elif len(phase_data["files_found"]) > 0:
            phase_data["status"] = "partial"
        else:
            phase_data["status"] = "not_found"
    
    result["planned_phases"] = phases
    
    # Scan for additional artifacts (over-delivery)
    extra_dirs = ["sandbox", "reports", "benchmarks", "blockchain", "frontend", "ml"]
    for dir_name in extra_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            try:
                file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
                result["delivered_components"][dir_name] = file_count
            except Exception:
                pass
    
    return result


# ============================================================================
# 6. Technology Inventory
# ============================================================================

def inventory_technologies() -> Dict[str, Any]:
    """Inventory all technologies in use."""
    print("[6/6] Building technology inventory...")
    
    result = {
        "languages": {},
        "frameworks": {},
        "databases": [],
        "deployment": [],
        "tools": [],
        "package_managers": [],
    }
    
    # Check file types
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".jsx": "JavaScript (React)",
        ".cpp": "C++",
        ".c": "C",
        ".hpp": "C++ Header",
        ".rs": "Rust",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".md": "Markdown",
    }
    
    for path in PROJECT_ROOT.rglob("*"):
        if any(p in path.parts for p in {".venv", "node_modules", "__pycache__"}):
            continue
        if path.is_file():
            ext = path.suffix.lower()
            if ext in ext_map:
                lang = ext_map[ext]
                result["languages"][lang] = result["languages"].get(lang, 0) + 1
    
    # Check package.json files
    for pkg_file in PROJECT_ROOT.rglob("package.json"):
        if "node_modules" in str(pkg_file):
            continue
        try:
            data = json.loads(pkg_file.read_text(encoding="utf-8"))
            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))
            
            for dep in all_deps:
                dep_lower = dep.lower()
                if "next" in dep_lower:
                    result["frameworks"]["Next.js"] = True
                if "react" in dep_lower:
                    result["frameworks"]["React"] = True
                if "fastapi" in dep_lower:
                    result["frameworks"]["FastAPI"] = True
                if "tailwind" in dep_lower:
                    result["frameworks"]["Tailwind"] = True
                if "turbo" in dep_lower:
                    result["tools"].append("Turborepo")
        except Exception:
            continue
    
    # Check pyproject.toml
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        for fw in ["fastapi", "sqlalchemy", "pydantic", "pytest", "numpy", "scipy"]:
            if fw in content.lower():
                result["frameworks"][fw] = True
    
    # Check for Docker
    if (PROJECT_ROOT / "Dockerfile").exists():
        result["deployment"].append("Docker")
    if (PROJECT_ROOT / "docker-compose.yml").exists():
        result["deployment"].append("docker-compose")
    
    # Check for pnpm
    if (PROJECT_ROOT / "pnpm-workspace.yaml").exists():
        result["package_managers"].append("pnpm")
    if (PROJECT_ROOT / "package-lock.json").exists():
        result["package_managers"].append("npm")
    
    # Database detection
    if (PROJECT_ROOT / "econojin.db").exists():
        result["databases"].append("SQLite (econojin.db)")
    if (PROJECT_ROOT / "alembic.ini").exists():
        result["databases"].append("Alembic migrations")
    
    return result


# ============================================================================
# Report Generation
# ============================================================================

def generate_report(audit: Dict[str, Any]) -> str:
    """Generate comprehensive markdown report."""
    
    structure = audit["structure"]
    git = audit["git"]
    python = audit["python"]
    tests = audit["tests"]
    balance = audit["balance"]
    tech = audit["tech"]
    
    # Calculate key metrics
    py_total = python["total_py_lines"]
    py_files = python["total_py_files"]
    classes = python["total_classes"]
    functions = python["total_functions"]
    
    tests_total = tests["total_tests"]
    tests_passed = tests["passed"]
    tests_failed = tests["failed"]
    tests_pass_rate = (tests_passed / tests_total * 100) if tests_total > 0 else 0
    
    # Phase status summary
    phases_status = balance["planned_phases"]
    complete_count = sum(1 for p in phases_status.values() if p["status"] == "complete")
    partial_count = sum(1 for p in phases_status.values() if p["status"] == "partial")
    missing_count = sum(1 for p in phases_status.values() if p["status"] == "not_found")
    
    report = []
    report.append("# 📊 Strategic Audit Report — EcoNojin Platform")
    report.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    report.append(f"*Repository: `{PROJECT_ROOT}`*")
    report.append("")
    
    report.append("---")
    report.append("\n## 🎯 Executive Summary")
    report.append("")
    report.append("| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| **Total Files** | {structure['total_files']:,} |")
    report.append(f"| **Total Lines** | {structure['total_lines']:,} |")
    report.append(f"| **Python Lines** | {py_total:,} |")
    report.append(f"| **Python Classes** | {classes} |")
    report.append(f"| **Python Functions** | {functions} |")
    report.append(f"| **Total Commits** | {git['total_commits']} |")
    report.append(f"| **Test Files** | {tests['test_files']} |")
    report.append(f"| **Tests Total** | {tests_total} |")
    report.append(f"| **Tests Pass Rate** | {tests_pass_rate:.1f}% |")
    report.append(f"| **Phases Complete** | {complete_count}/{len(phases_status)} |")
    report.append("")
    
    # 1. Repository Structure
    report.append("---")
    report.append("\n## 📁 1. Repository Structure")
    report.append("")
    report.append("### By Extension (Top 15)")
    report.append("")
    report.append("| Extension | Files | Lines | Size (MB) |")
    report.append("|-----------|-------|-------|-----------|")
    sorted_exts = sorted(
        structure["by_extension"].items(),
        key=lambda x: x[1]["count"],
        reverse=True,
    )[:15]
    for ext, data in sorted_exts:
        report.append(f"| `{ext}` | {data['count']} | {data['lines']:,} | {data['bytes']/1024/1024:.2f} |")
    
    report.append("")
    report.append("### By Top-Level Directory")
    report.append("")
    report.append("| Directory | Files | Size (MB) |")
    report.append("|-----------|-------|-----------|")
    sorted_dirs = sorted(
        structure["by_directory"].items(),
        key=lambda x: x[1]["bytes"],
        reverse=True,
    )[:15]
    for dir_name, data in sorted_dirs:
        report.append(f"| `{dir_name}` | {data['count']} | {data['bytes']/1024/1024:.2f} |")
    
    if structure["large_files"]:
        report.append("")
        report.append("### Large Files (>1000 lines)")
        report.append("")
        report.append("| File | Lines |")
        report.append("|------|-------|")
        for f in structure["large_files"][:15]:
            report.append(f"| `{f['path']}` | {f['lines']:,} |")
    
    # 2. Git History
    report.append("")
    report.append("---")
    report.append("\n## 📜 2. Git History")
    report.append("")
    report.append(f"- **Total commits**: {git['total_commits']}")
    report.append(f"- **First commit**: {git['first_commit']}")
    report.append(f"- **Last commit**: {git['last_commit']}")
    report.append(f"- **Branches**: {', '.join(git['branches'][:5])}")
    report.append("")
    
    report.append("### Commit Categories")
    report.append("")
    report.append("| Type | Count |")
    report.append("|------|-------|")
    for type_, count in sorted(git["phase_commits"].items(), key=lambda x: x[1], reverse=True):
        report.append(f"| {type_} | {count} |")
    
    report.append("")
    report.append("### Recent Commits (last 10)")
    report.append("")
    for commit in git["recent_commits"][:10]:
        report.append(f"- `{commit['hash']}` — {commit['message'][:80]}")
    
    # 3. Code Quality
    report.append("")
    report.append("---")
    report.append("\n## 🧪 3. Python Code Quality")
    report.append("")
    report.append(f"- **Files**: {py_files}")
    report.append(f"- **Total lines**: {py_total:,}")
    report.append(f"- **Classes**: {classes}")
    report.append(f"- **Functions**: {functions}")
    report.append(f"- **Imports**: {python['total_imports']}")
    report.append(f"- **Syntax errors**: {len(python['syntax_errors'])}")
    report.append("")
    
    report.append("### Code by Purpose")
    report.append("")
    report.append("| Category | Files |")
    report.append("|----------|-------|")
    for category, files in python["modules_by_purpose"].items():
        report.append(f"| {category} | {len(files)} |")
    
    report.append("")
    report.append("### Top Dependencies (from imports)")
    report.append("")
    report.append("| Module | Usage Count |")
    report.append("|--------|-------------|")
    for module, count in python.get("top_imports", []):
        report.append(f"| `{module}` | {count} |")
    
    report.append("")
    report.append("### Largest Python Files")
    report.append("")
    report.append("| File | Lines |")
    report.append("|------|-------|")
    for f in python["largest_files"][:15]:
        report.append(f"| `{f['path']}` | {f['lines']:,} |")
    
    if python["syntax_errors"]:
        report.append("")
        report.append("### ⚠️ Syntax Errors")
        report.append("")
        for err in python["syntax_errors"][:10]:
            report.append(f"- `{err['file']}` line {err['line']}: {err['msg']}")
    
    # 4. Tests
    report.append("")
    report.append("---")
    report.append("\n## ✅ 4. Test Suite")
    report.append("")
    report.append("| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| Test files | {tests['test_files']} |")
    report.append(f"| Total tests | {tests_total} |")
    report.append(f"| Passed | {tests_passed} |")
    report.append(f"| Failed | {tests_failed} |")
    report.append(f"| Skipped | {tests['skipped']} |")
    report.append(f"| Errors | {tests['errors']} |")
    report.append(f"| Pass rate | **{tests_pass_rate:.1f}%** |")
    report.append(f"| Duration | {tests['duration_seconds']:.1f}s |")
    
    if tests["failed_tests"]:
        report.append("")
        report.append("### Failed Tests")
        report.append("")
        for t in tests["failed_tests"]:
            report.append(f"- {t}")
    
    # 5. Execution Balance
    report.append("")
    report.append("---")
    report.append("\n## 📈 5. Execution Balance (Planned vs Delivered)")
    report.append("")
    report.append("### Phase Status")
    report.append("")
    report.append("| Phase | Status | Evidence |")
    report.append("|-------|--------|----------|")
    status_emoji = {"complete": "✅", "partial": "⚠️", "not_found": "❌"}
    for phase_name, phase_data in phases_status.items():
        status = phase_data["status"]
        emoji = status_emoji.get(status, "❓")
        found = len(phase_data["files_found"])
        total = len(phase_data["evidence"])
        report.append(f"| {phase_name} | {emoji} {status} | {found}/{total} files |")
    
    report.append("")
    report.append(f"**Summary**: ✅ {complete_count} complete, ⚠️ {partial_count} partial, ❌ {missing_count} missing")
    
    if balance["delivered_components"]:
        report.append("")
        report.append("### Extra Deliverables (Sandbox/Extras)")
        report.append("")
        report.append("| Component | Files |")
        report.append("|-----------|-------|")
        for name, count in sorted(balance["delivered_components"].items(), key=lambda x: x[1], reverse=True):
            report.append(f"| `{name}` | {count} |")
    
    # 6. Technology Inventory
    report.append("")
    report.append("---")
    report.append("\n## 🛠️ 6. Technology Inventory")
    report.append("")
    report.append("### Languages")
    report.append("")
    report.append("| Language | Files |")
    report.append("|----------|-------|")
    for lang, count in sorted(tech["languages"].items(), key=lambda x: x[1], reverse=True):
        report.append(f"| {lang} | {count} |")
    
    report.append("")
    report.append("### Frameworks & Libraries")
    report.append("")
    for fw in sorted(tech["frameworks"].keys()):
        report.append(f"- ✅ {fw}")
    
    if tech["databases"]:
        report.append("")
        report.append("### Databases")
        report.append("")
        for db in tech["databases"]:
            report.append(f"- {db}")
    
    if tech["deployment"]:
        report.append("")
        report.append("### Deployment")
        report.append("")
        for d in tech["deployment"]:
            report.append(f"- {d}")
    
    if tech["package_managers"]:
        report.append("")
        report.append("### Package Managers")
        report.append("")
        for pm in tech["package_managers"]:
            report.append(f"- {pm}")
    
    # 7. Critical Findings
    report.append("")
    report.append("---")
    report.append("\n## 🚨 7. Critical Findings & Recommendations")
    report.append("")
    
    findings = []
    
    # Finding 1: Test coverage
    if tests_pass_rate < 80:
        findings.append(f"❌ **Low test pass rate**: {tests_pass_rate:.1f}% (target: ≥80%)")
    elif tests_pass_rate >= 90:
        findings.append(f"✅ **Strong test coverage**: {tests_pass_rate:.1f}%")
    else:
        findings.append(f"⚠️ **Acceptable test coverage**: {tests_pass_rate:.1f}%")
    
    # Finding 2: Phase completion
    if complete_count < len(phases_status) * 0.5:
        findings.append(f"❌ **Phase delivery**: Only {complete_count}/{len(phases_status)} phases complete")
    elif complete_count == len(phases_status):
        findings.append(f"✅ **All planned phases delivered**")
    else:
        findings.append(f"⚠️ **Phase delivery**: {complete_count}/{len(phases_status)} phases complete")
    
    # Finding 3: Silos
    if python["modules_by_purpose"]["sandbox_scripts"] and len(python["modules_by_purpose"]["sandbox_scripts"]) > 20:
        findings.append(f"⚠️ **Sandbox sprawl**: {len(python['modules_by_purpose']['sandbox_scripts'])} scripts in sandbox/ — risk of silos")
    
    # Finding 4: Large files
    if len(structure["large_files"]) > 5:
        findings.append(f"⚠️ **Monolithic files**: {len(structure['large_files'])} files with >1000 lines")
    
    # Finding 5: Syntax errors
    if python["syntax_errors"]:
        findings.append(f"❌ **{len(python['syntax_errors'])} syntax errors** — will break deployment")
    else:
        findings.append(f"✅ **Zero syntax errors** in Python codebase")
    
    # Finding 6: Hybrid scaffold not yet
    if phases_status["8-Hybrid PWA (Phase 17)"]["status"] == "not_found":
        findings.append(f"ℹ️ **Hybrid PWA (Phase 17)**: Not yet scaffolded — next step")
    
    for finding in findings:
        report.append(f"- {finding}")
    
    # 8. Strategic Questions
    report.append("")
    report.append("---")
    report.append("\n## 🤔 8. Strategic Questions for Decision")
    report.append("")
    report.append("Before proceeding to Phase 17, we need answers:")
    report.append("")
    report.append("1. **What is the REAL MVP?** Is it the Python API server, the upcoming PWA, or something else?")
    report.append("2. **Are the 8 Hydroma models production-validated?** Or are they research prototypes?")
    report.append("3. **Is the current API (phase13) stable enough** to be the backend for the PWA?")
    report.append("4. **Should we consolidate the sandbox scripts** into proper modules?")
    report.append("5. **What's the user-facing product?** Web app, mobile app, desktop, API, or all?")
    report.append("6. **What's the timeline?** 1 month MVP, 6 month production, 1 year platform?")
    report.append("7. **Team size?** Solo dev vs team affects architecture choices")
    report.append("")
    
    return "\n".join(report)


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("🔍 STRATEGIC AUDIT — EcoNojin Platform")
    print("=" * 80)
    print(f"Repository: {PROJECT_ROOT}")
    print()
    
    t0 = time.time()
    
    # Run all analyses
    audit = {
        "structure": scan_structure(),
        "git": analyze_git_history(),
        "python": analyze_python_code(),
        "tests": run_tests(),
        "balance": analyze_execution_balance(),
        "tech": inventory_technologies(),
    }
    
    duration = time.time() - t0
    
    # Generate report
    print(f"\n[Final] Generating report ({duration:.1f}s elapsed)...")
    report = generate_report(audit)
    
    # Save
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")
    
    print()
    print("=" * 80)
    print(f"✅ Audit complete in {duration:.1f} seconds")
    print("=" * 80)
    print(f"\n📄 Report saved: {REPORT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"   Size: {REPORT_FILE.stat().st_size / 1024:.1f} KB")
    print()
    print("🔍 View the report:")
    print(f"   Get-Content reports\\strategic_audit.md")
    print()
    print("💡 Next: Review the report, then we discuss transformation strategy")


if __name__ == "__main__":
    main()