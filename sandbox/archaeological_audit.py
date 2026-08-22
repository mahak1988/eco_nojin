"""
🏛️ ECONOJIN ARCHAEOLOGICAL AUDIT
================================

Comprehensive architectural audit based on 30-section questionnaire.

Output: reports/archaeological_audit.json (machine-readable)
        reports/archaeological_audit.md (human-readable)

Run:
    python sandbox/archaeological_audit.py

This script is the first step in the strategic consolidation.
It discovers what actually exists before any redesign is proposed.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(r"D:\eco_nojin")
JSON_REPORT = PROJECT_ROOT / "reports" / "archaeological_audit.json"
MD_REPORT = PROJECT_ROOT / "reports" / "archaeological_audit.md"

IGNORE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".satellite_cache", ".dvc", ".cache", ".vscode",
    "dist", "build", ".next", "out", ".turbo", "econojin.egg-info",
    "_backups_fix", "_trash", ".eggs", ".mypy_cache",
}


def should_ignore(path: Path) -> bool:
    """Check if path should be ignored during scanning."""
    return any(part in IGNORE_DIRS for part in path.parts)


def safe_read(path: Path) -> Optional[str]:
    """Safely read a file, returning None on failure."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def parse_python_ast(content: str) -> Dict[str, Any]:
    """Parse Python file AST and extract classes, functions, imports."""
    result = {
        "classes": [],
        "functions": [],
        "imports": [],
        "decorator_functions": [],
    }
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                result["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [b.id if isinstance(b, ast.Name) else str(b) 
                              for b in node.bases],
                    "methods": [n.name for n in node.body 
                               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = []
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    elif isinstance(dec, ast.Attribute):
                        decorators.append(dec.attr)
                    elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        decorators.append(dec.func.attr)
                
                entry = {
                    "name": node.name,
                    "line": node.lineno,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": decorators,
                }
                result["functions"].append(entry)
                if decorators:
                    result["decorator_functions"].append(entry)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append({"module": alias.name, "type": "import"})
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result["imports"].append({
                        "module": node.module,
                        "names": [a.name for a in node.names],
                        "type": "from_import",
                    })
    except SyntaxError as e:
        result["syntax_error"] = {"line": e.lineno, "msg": e.msg}
    return result


# ============================================================================
# 1. REPOSITORY STRUCTURE
# ============================================================================

def scan_structure() -> Dict[str, Any]:
    """Section 1: Overall system structure."""
    print("\n[1/30] Scanning repository structure...")
    
    result = {
        "top_level_directories": {},
        "top_level_files": {},
        "by_extension": defaultdict(lambda: {"count": 0, "size_bytes": 0, "lines": 0}),
        "largest_files": [],
        "total_files": 0,
        "total_lines": 0,
    }
    
    # Top-level scan
    for item in PROJECT_ROOT.iterdir():
        if item.name.startswith(".") and item.name not in {".github", ".env", ".env.example", ".gitignore"}:
            continue
        
        if item.is_dir():
            try:
                file_count = 0
                total_size = 0
                for f in item.rglob("*"):
                    if f.is_file() and not should_ignore(f):
                        file_count += 1
                        total_size += f.stat().st_size
                result["top_level_directories"][item.name] = {
                    "file_count": file_count,
                    "size_bytes": total_size,
                    "size_mb": round(total_size / 1024 / 1024, 2),
                }
            except Exception:
                pass
        else:
            try:
                result["top_level_files"][item.name] = item.stat().st_size
            except Exception:
                pass
    
    # Full recursive scan
    for file in PROJECT_ROOT.rglob("*"):
        if should_ignore(file) or not file.is_file():
            continue
        
        result["total_files"] += 1
        ext = file.suffix.lower() or "(no ext)"
        
        try:
            size = file.stat().st_size
            result["by_extension"][ext]["count"] += 1
            result["by_extension"][ext]["size_bytes"] += size
            
            if ext in {".py", ".js", ".ts", ".tsx", ".jsx", ".cpp", ".c", ".hpp", ".h",
                       ".md", ".json", ".yaml", ".yml", ".sql", ".html", ".css"}:
                content = safe_read(file)
                if content:
                    lines = len(content.split("\n"))
                    result["by_extension"][ext]["lines"] += lines
                    result["total_lines"] += lines
                    
                    result["largest_files"].append({
                        "path": str(file.relative_to(PROJECT_ROOT)),
                        "lines": lines,
                        "size_bytes": size,
                        "ext": ext,
                    })
        except Exception:
            continue
    
    # Sort largest files
    result["largest_files"] = sorted(
        result["largest_files"],
        key=lambda x: x["lines"],
        reverse=True,
    )[:30]
    
    # Convert defaultdict to dict
    result["by_extension"] = {
        ext: dict(stats) 
        for ext, stats in sorted(
            result["by_extension"].items(),
            key=lambda x: -x[1]["count"]
        )[:20]
    }
    
    return result


# ============================================================================
# 2. PYTHON ENGINE ANALYSIS
# ============================================================================

def analyze_python_engine() -> Dict[str, Any]:
    """Analyze the Python engine: models, services, scientific code."""
    print("\n[2/30] Analyzing Python engine...")
    
    result = {
        "engine_directory": {},
        "models": [],
        "services": {},
        "scientific_modules": [],
        "orchestrators": [],
        "equations_found": [],
        "syntax_errors": [],
    }
    
    # Scan engine/
    engine_dir = PROJECT_ROOT / "engine"
    if engine_dir.exists():
        for file in engine_dir.rglob("*.py"):
            if should_ignore(file):
                continue
            
            content = safe_read(file)
            if not content:
                continue
            
            rel = str(file.relative_to(PROJECT_ROOT))
            ast_data = parse_python_ast(content)
            
            if "syntax_error" in ast_data:
                result["syntax_errors"].append({
                    "file": rel,
                    "line": ast_data["syntax_error"]["line"],
                    "msg": ast_data["syntax_error"]["msg"],
                })
                continue
            
            # Detect model classes
            for cls in ast_data["classes"]:
                cls_lower = cls["name"].lower()
                if any(kw in cls_lower for kw in ["model", "engine", "simulator", "calculator", "analyzer", "index", "watchdog"]):
                    result["models"].append({
                        "class": cls["name"],
                        "file": rel,
                        "line": cls["line"],
                        "bases": cls["bases"],
                        "methods": cls["methods"][:10],
                    })
            
            # Detect scientific keywords
            sci_keywords = ["equation", "formula", "integral", "derivative", "differential",
                           "penman", "monteith", "hargreaves", "richards", "saint_venant",
                           "darcy", "manning", "thornthwaite", "blaney_criddle",
                           "rational_method", "scs_cn", "green_ampt"]
            
            content_lower = content.lower()
            found_keywords = [kw for kw in sci_keywords if kw in content_lower]
            if found_keywords:
                result["scientific_modules"].append({
                    "file": rel,
                    "keywords": found_keywords,
                    "classes": [c["name"] for c in ast_data["classes"]],
                    "functions": [f["name"] for f in ast_data["functions"][:20]],
                })
            
            # Detect orchestrator patterns
            if "orchestrat" in content_lower or "coordinator" in content_lower:
                result["orchestrators"].append({
                    "file": rel,
                    "classes": [c["name"] for c in ast_data["classes"]],
                    "functions": [f["name"] for f in ast_data["functions"]],
                })
    
    # Scan services/
    services_dir = PROJECT_ROOT / "services"
    if services_dir.exists():
        for subdir in services_dir.iterdir():
            if not subdir.is_dir() or subdir.name.startswith("_"):
                continue
            
            svc_info = {
                "path": str(subdir.relative_to(PROJECT_ROOT)),
                "files": [],
                "classes": [],
                "functions": [],
                "imports_external": set(),
                "database_usage": False,
                "has_router": False,
            }
            
            for file in subdir.rglob("*.py"):
                if should_ignore(file):
                    continue
                
                rel = str(file.relative_to(PROJECT_ROOT))
                svc_info["files"].append(rel)
                
                content = safe_read(file)
                if not content:
                    continue
                
                ast_data = parse_python_ast(content)
                svc_info["classes"].extend([c["name"] for c in ast_data["classes"]])
                svc_info["functions"].extend([f["name"] for f in ast_data["functions"]])
                
                for imp in ast_data["imports"]:
                    module = imp.get("module", "")
                    if module and not module.startswith("."):
                        top = module.split(".")[0]
                        if top not in {"typing", "os", "sys", "json", "datetime", "pathlib",
                                       "dataclasses", "collections", "itertools", "functools",
                                       "abc", "enum", "re", "math", "random", "hashlib",
                                       "time", "logging", "uuid", "copy"}:
                            svc_info["imports_external"].add(top)
                
                content_lower = content.lower()
                if any(kw in content_lower for kw in ["sqlalchemy", "session", "asyncpg", "psycopg", "database"]):
                    svc_info["database_usage"] = True
                if "router" in rel.lower() or "@router" in content or "@app" in content:
                    svc_info["has_router"] = True
            
            svc_info["imports_external"] = list(svc_info["imports_external"])
            result["services"][subdir.name] = svc_info
    
    return result


# ============================================================================
# 3. C++ ENGINE ANALYSIS
# ============================================================================

def analyze_cpp_engine() -> Dict[str, Any]:
    """Analyze the C++ engine: files, bindings, integration."""
    print("\n[3/30] Analyzing C++ engine...")
    
    result = {
        "cpp_files": [],
        "header_files": [],
        "built_modules": [],
        "binding_method": None,
        "python_imports": [],
        "functions_exported": [],
        "namespaces": [],
    }
    
    # Scan C++ sources
    cpp_patterns = ["*.cpp", "*.cc", "*.cxx", "*.c"]
    h_patterns = ["*.hpp", "*.h", "*.hh"]
    
    for pattern in cpp_patterns:
        for file in PROJECT_ROOT.rglob(pattern):
            if should_ignore(file):
                continue
            content = safe_read(file)
            if not content:
                continue
            
            rel = str(file.relative_to(PROJECT_ROOT))
            lines = len(content.split("\n"))
            
            # Detect binding methods
            binding = None
            if "pybind11" in content or "PYBIND11" in content:
                binding = "pybind11"
            elif "extern \"C\"" in content:
                binding = "C API"
            
            # Detect namespaces
            namespaces = re.findall(r'namespace\s+(\w+)', content)
            
            # Detect functions
            func_pattern = r'\b(?:[\w:]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const)?\s*\{'
            funcs = re.findall(func_pattern, content)
            
            result["cpp_files"].append({
                "file": rel,
                "lines": lines,
                "binding": binding,
                "namespaces": list(set(namespaces)),
                "function_count": len(funcs),
            })
            
            if binding:
                result["binding_method"] = binding
    
    for pattern in h_patterns:
        for file in PROJECT_ROOT.rglob(pattern):
            if should_ignore(file):
                continue
            content = safe_read(file)
            if not content:
                continue
            rel = str(file.relative_to(PROJECT_ROOT))
            result["header_files"].append({
                "file": rel,
                "lines": len(content.split("\n")),
            })
    
    # Find built .pyd/.so modules
    for ext in ["*.pyd", "*.so", "*.dll"]:
        for file in PROJECT_ROOT.rglob(ext):
            if should_ignore(file):
                continue
            result["built_modules"].append({
                "file": str(file.relative_to(PROJECT_ROOT)),
                "size_bytes": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
            })
    
    # Find Python files that import C++ modules
    cpp_import_patterns = [
        r"import\s+hydroma_core",
        r"from\s+hydroma_core",
        r"import\s+cpp_bridge",
        r"from\s+cpp_bridge",
        r"import\s+cpp_core",
        r"from\s+cpp_core",
        r"import\s+hydroma_models",
        r"from\s+hydroma_models",
        r"ctypes\.CDLL",
        r"ctypes\.WinDLL",
        r"cffi",
    ]
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        content = safe_read(py_file)
        if not content:
            continue
        
        for pattern in cpp_import_patterns:
            if re.search(pattern, content):
                result["python_imports"].append({
                    "file": str(py_file.relative_to(PROJECT_ROOT)),
                    "pattern": pattern,
                })
                break
    
    # Unique Python imports
    seen = set()
    unique = []
    for imp in result["python_imports"]:
        if imp["file"] not in seen:
            seen.add(imp["file"])
            unique.append(imp)
    result["python_imports"] = unique
    
    return result


# ============================================================================
# 4. FRONTEND ANALYSIS
# ============================================================================

def analyze_frontend() -> Dict[str, Any]:
    """Analyze the frontend (Next.js)."""
    print("\n[4/30] Analyzing frontend...")
    
    result = {
        "exists": False,
        "framework": None,
        "pages": [],
        "components": [],
        "api_calls": [],
        "routes": [],
        "state_management": None,
        "package_json": None,
    }
    
    frontend_dir = PROJECT_ROOT / "frontend"
    if not frontend_dir.exists():
        return result
    
    result["exists"] = True
    
    # Read package.json
    pkg_file = frontend_dir / "package.json"
    if pkg_file.exists():
        try:
            pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
            result["package_json"] = {
                "name": pkg.get("name"),
                "version": pkg.get("version"),
                "dependencies": list(pkg.get("dependencies", {}).keys()),
                "devDependencies": list(pkg.get("devDependencies", {}).keys()),
                "scripts": pkg.get("scripts", {}),
            }
            
            # Detect framework
            all_deps = set(pkg.get("dependencies", {}).keys()) | set(pkg.get("devDependencies", {}).keys())
            if "next" in all_deps:
                result["framework"] = "Next.js"
            elif "react" in all_deps:
                result["framework"] = "React"
            
            # Detect state management
            for dep in all_deps:
                if dep in ["zustand", "redux", "mobx", "recoil", "jotai", "valtio"]:
                    result["state_management"] = dep
        except Exception:
            pass
    
    # Scan pages (app/ or pages/)
    for dir_name in ["app", "pages", "src/app", "src/pages"]:
        pages_dir = frontend_dir / dir_name
        if pages_dir.exists():
            for file in pages_dir.rglob("*"):
                if file.suffix in {".tsx", ".jsx", ".ts", ".js"} and file.is_file():
                    if should_ignore(file):
                        continue
                    rel = str(file.relative_to(frontend_dir))
                    result["pages"].append({
                        "path": rel,
                        "name": file.name,
                        "size_bytes": file.stat().st_size,
                    })
    
    # Scan components
    for dir_name in ["components", "src/components"]:
        comp_dir = frontend_dir / dir_name
        if comp_dir.exists():
            for file in comp_dir.rglob("*"):
                if file.suffix in {".tsx", ".jsx", ".ts", ".js"} and file.is_file():
                    if should_ignore(file):
                        continue
                    rel = str(file.relative_to(frontend_dir))
                    result["components"].append({
                        "path": rel,
                        "name": file.name,
                        "size_bytes": file.stat().st_size,
                    })
    
    # Scan for API calls
    api_patterns = [
        r"fetch\s*\(\s*['\"]([^'\"]+)['\"]",
        r"axios\.(get|post|put|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
        r"useSWR\s*\(\s*['\"]([^'\"]+)['\"]",
        r"useQuery\s*\(.*?['\"]([^'\"]+)['\"]",
    ]
    
    for ts_file in frontend_dir.rglob("*"):
        if ts_file.suffix not in {".ts", ".tsx", ".js", ".jsx"} or not ts_file.is_file():
            continue
        if should_ignore(ts_file):
            continue
        
        content = safe_read(ts_file)
        if not content:
            continue
        
        for pattern in api_patterns:
            for match in re.finditer(pattern, content):
                url = match.group(match.lastindex)
                if url.startswith("/") or url.startswith("http"):
                    result["api_calls"].append({
                        "file": str(ts_file.relative_to(frontend_dir)),
                        "url": url,
                        "pattern": pattern,
                    })
    
    return result


# ============================================================================
# 5. DATABASE ANALYSIS
# ============================================================================

def analyze_database() -> Dict[str, Any]:
    """Analyze database: models, migrations, schema."""
    print("\n[5/30] Analyzing database...")
    
    result = {
        "databases_found": [],
        "alembic": {
            "exists": False,
            "migrations": [],
            "env_file": None,
        },
        "orm_models": [],
        "sql_files": [],
        "db_config_files": [],
    }
    
    # Check for database files
    for db_file in PROJECT_ROOT.rglob("*.db"):
        if should_ignore(db_file):
            continue
        result["databases_found"].append({
            "file": str(db_file.relative_to(PROJECT_ROOT)),
            "type": "SQLite",
            "size_bytes": db_file.stat().st_size,
            "modified": datetime.fromtimestamp(db_file.stat().st_mtime).isoformat(),
        })
    
    # Check alembic
    alembic_dir = PROJECT_ROOT / "alembic"
    alembic_ini = PROJECT_ROOT / "alembic.ini"
    
    if alembic_ini.exists():
        result["alembic"]["exists"] = True
        result["alembic"]["ini_file"] = str(alembic_ini.relative_to(PROJECT_ROOT))
    
    if alembic_dir.exists():
        versions_dir = alembic_dir / "versions"
        if versions_dir.exists():
            for file in versions_dir.rglob("*.py"):
                if should_ignore(file):
                    continue
                content = safe_read(file)
                if not content:
                    continue
                
                # Extract revision info
                revision = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
                down_revision = re.search(r"down_revision\s*=\s*['\"]?([^'\"\n]+)['\"]?", content)
                branch_labels = re.search(r"branch_labels\s*=\s*(.+)", content)
                revision_msg = re.search(r"#\s*(?:revision|message):\s*(.+)", content, re.IGNORECASE)
                
                result["alembic"]["migrations"].append({
                    "file": str(file.relative_to(PROJECT_ROOT)),
                    "revision": revision.group(1) if revision else None,
                    "down_revision": down_revision.group(1) if down_revision else None,
                    "message": revision_msg.group(1).strip() if revision_msg else file.stem,
                })
    
    # Scan for ORM models (SQLAlchemy)
    sqla_patterns = [
        r"class\s+(\w+)\s*\(\s*(?:Base|DeclarativeBase|Model)",
        r"__tablename__\s*=\s*['\"]([^'\"]+)['\"]",
        r"Column\s*\(",
        r"mapped_column",
    ]
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        content = safe_read(py_file)
        if not content:
            continue
        
        if "sqlalchemy" in content.lower() or "__tablename__" in content:
            rel = str(py_file.relative_to(PROJECT_ROOT))
            
            # Find table names
            tables = re.findall(r"__tablename__\s*=\s*['\"]([^'\"]+)['\"]", content)
            
            # Find model classes
            classes = re.findall(r"class\s+(\w+)\s*\([^)]*Base[^)]*\):", content)
            classes += re.findall(r"class\s+(\w+)\s*\(\s*DeclarativeBase\s*\):", content)
            classes += re.findall(r"class\s+(\w+)\s*\(\s*Model\s*\):", content)
            
            if tables or classes:
                result["orm_models"].append({
                    "file": rel,
                    "tables": tables,
                    "classes": list(set(classes)),
                })
    
    # Scan SQL files
    for sql_file in PROJECT_ROOT.rglob("*.sql"):
        if should_ignore(sql_file):
            continue
        content = safe_read(sql_file)
        if not content:
            continue
        
        # Find CREATE TABLE statements
        tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", content, re.IGNORECASE)
        
        result["sql_files"].append({
            "file": str(sql_file.relative_to(PROJECT_ROOT)),
            "tables_defined": tables,
            "size_bytes": sql_file.stat().st_size,
        })
    
    # Find database config files
    for name in ["database.py", "config.py", "db.py", "database_config.py"]:
        for file in PROJECT_ROOT.rglob(name):
            if should_ignore(file):
                continue
            if "database" in str(file).lower() or "config" in str(file).lower():
                result["db_config_files"].append(str(file.relative_to(PROJECT_ROOT)))
    
    return result


# ============================================================================
# 6. TESTS ANALYSIS
# ============================================================================

def analyze_tests() -> Dict[str, Any]:
    """Analyze test suite."""
    print("\n[6/30] Analyzing test suite...")
    
    result = {
        "test_files": [],
        "test_classes": [],
        "test_functions": [],
        "pytest_config": {},
        "coverage_files": [],
        "total_test_functions": 0,
    }
    
    # Read pytest configs
    pytest_ini = PROJECT_ROOT / "pytest.ini"
    if pytest_ini.exists():
        result["pytest_config"]["pytest.ini"] = safe_read(pytest_ini)
    
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        content = safe_read(pyproject)
        if content and "tool.pytest" in content:
            result["pytest_config"]["pyproject.toml_has_pytest"] = True
    
    setup_cfg = PROJECT_ROOT / "setup.cfg"
    if setup_cfg.exists():
        content = safe_read(setup_cfg)
        if content and "[tool:pytest]" in content:
            result["pytest_config"]["setup.cfg_has_pytest"] = True
    
    # Scan test files
    for file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(file):
            continue
        if not (file.name.startswith("test_") or file.name.endswith("_test.py")):
            continue
        
        content = safe_read(file)
        if not content:
            continue
        
        rel = str(file.relative_to(PROJECT_ROOT))
        ast_data = parse_python_ast(content)
        
        test_classes = [c for c in ast_data["classes"] if c["name"].startswith("Test")]
        test_functions = [f for f in ast_data["functions"] if f["name"].startswith("test_")]
        
        result["test_files"].append({
            "file": rel,
            "classes": len(test_classes),
            "functions": len(test_functions),
            "has_syntax_error": "syntax_error" in ast_data,
        })
        
        result["test_classes"].extend([
            {"name": c["name"], "file": rel} for c in test_classes
        ])
        result["test_functions"].extend([
            {"name": f["name"], "file": rel, "line": f["line"]} for f in test_functions
        ])
    
    result["total_test_functions"] = len(result["test_functions"])
    
    # Coverage files
    for name in [".coverage", "coverage.xml", "htmlcov"]:
        item = PROJECT_ROOT / name
        if item.exists():
            result["coverage_files"].append(str(item.relative_to(PROJECT_ROOT)))
    
    return result


# ============================================================================
# 7. SCIENTIFIC MODEL INVENTORY
# ============================================================================

def inventory_scientific_models() -> Dict[str, Any]:
    """Deep inventory of all scientific models."""
    print("\n[7/30] Inventorying scientific models...")
    
    result = {
        "models_by_domain": defaultdict(list),
        "equations_found": [],
        "references": [],
        "validated_models": [],
        "uncalibrated_models": [],
    }
    
    # Domain keywords
    domains = {
        "Hydrology": ["hydrology", "runoff", "infiltration", "darcy", "richards", "green_ampt"],
        "Hydraulics": ["hydraulic", "manning", "saint_venant", "open_channel", "weir"],
        "Climate": ["climate", "koppen", "geiger", "temperature", "precipitation"],
        "Evapotranspiration": ["evapotranspiration", "et0", "penman", "monteith", "hargreaves", "thornthwaite"],
        "Soil": ["soil", "pedology", "texture", "bulk_density", "ph", "cec"],
        "Crop": ["crop", "aquacrop", "rue", "phenology", "lai", "biomass", "yield"],
        "Irrigation": ["irrigation", "water_requirement", "crop_coefficient", "kc"],
        "WaterBalance": ["water_balance", "water_budget", "storage"],
        "Groundwater": ["groundwater", "aquifer", "water_table"],
        "Watershed": ["watershed", "catchment", "drainage", "basin"],
        "Economics": ["economics", "finance", "cost", "revenue", "profit", "npv", "irr"],
        "Carbon": ["carbon", "rothc", "soc", "sequestration"],
        "Biofertilizer": ["biofertilizer", "microorganism", "strain", "cfu"],
    }
    
    # Scan all Python files
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        
        content = safe_read(py_file)
        if not content:
            continue
        
        content_lower = content.lower()
        rel = str(py_file.relative_to(PROJECT_ROOT))
        
        # Find which domain(s) this file belongs to
        matched_domains = []
        for domain, keywords in domains.items():
            if any(kw in content_lower for kw in keywords):
                matched_domains.append(domain)
        
        if not matched_domains:
            continue
        
        # Extract model classes
        ast_data = parse_python_ast(content)
        
        for cls in ast_data["classes"]:
            cls_lower = cls["name"].lower()
            for domain in matched_domains:
                if any(kw in cls_lower for kw in domains[domain]):
                    result["models_by_domain"][domain].append({
                        "class": cls["name"],
                        "file": rel,
                        "methods": cls["methods"][:15],
                    })
        
        # Find equations
        eq_patterns = [
            r"def\s+compute_([\w_]+)\s*\(",
            r"def\s+calculate_([\w_]+)\s*\(",
            r"#\s*equation:\s*(.+)",
            r"#\s*formula:\s*(.+)",
        ]
        for pattern in eq_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                result["equations_found"].append({
                    "file": rel,
                    "name": match.group(1) if match.lastindex else None,
                    "pattern": pattern,
                })
        
        # Find scientific references
        ref_patterns = [
            r"(?:FAO[- ]\d+)",
            r"(?:Penman[- ]Monteith)",
            r"(?:Hargreaves)",
            r"(?:Thornthwaite)",
            r"(?:RothC)",
            r"(?:DSSAT)",
            r"(?:AquaCrop)",
            r"(?:SWAT)",
            r"(?:USLE|RUSLE)",
            r"(?:SCS[- ]CN)",
        ]
        for pattern in ref_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                result["references"].append({
                    "file": rel,
                    "reference": list(set(matches)),
                })
    
    # Convert defaultdict to dict
    result["models_by_domain"] = {
        domain: models
        for domain, models in result["models_by_domain"].items()
    }
    
    return result


# ============================================================================
# 8. API ANALYSIS
# ============================================================================

def analyze_apis() -> Dict[str, Any]:
    """Analyze all API endpoints."""
    print("\n[8/30] Analyzing APIs...")
    
    result = {
        "api_implementations": [],
        "endpoints_by_path": defaultdict(list),
        "frameworks_used": set(),
        "routers": [],
        "authentication_methods": set(),
    }
    
    # Find FastAPI apps and routers
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        
        content = safe_read(py_file)
        if not content:
            continue
        
        # Detect FastAPI
        if "FastAPI(" in content:
            result["frameworks_used"].add("FastAPI")
            result["api_implementations"].append({
                "file": str(py_file.relative_to(PROJECT_ROOT)),
                "type": "FastAPI app",
                "framework": "FastAPI",
            })
        
        if "Flask(" in content:
            result["frameworks_used"].add("Flask")
            result["api_implementations"].append({
                "file": str(py_file.relative_to(PROJECT_ROOT)),
                "type": "Flask app",
                "framework": "Flask",
            })
        
        # Detect routers
        if "APIRouter(" in content:
            result["frameworks_used"].add("FastAPI")
            result["routers"].append(str(py_file.relative_to(PROJECT_ROOT)))
        
        # Detect endpoints
        endpoint_patterns = [
            (r'@app\.get\(["\']([^"\']+)["\']', "GET"),
            (r'@app\.post\(["\']([^"\']+)["\']', "POST"),
            (r'@app\.put\(["\']([^"\']+)["\']', "PUT"),
            (r'@app\.delete\(["\']([^"\']+)["\']', "DELETE"),
            (r'@app\.patch\(["\']([^"\']+)["\']', "PATCH"),
            (r'@router\.get\(["\']([^"\']+)["\']', "GET"),
            (r'@router\.post\(["\']([^"\']+)["\']', "POST"),
            (r'@router\.put\(["\']([^"\']+)["\']', "PUT"),
            (r'@router\.delete\(["\']([^"\']+)["\']', "DELETE"),
            (r'@router\.patch\(["\']([^"\']+)["\']', "PATCH"),
        ]
        
        rel = str(py_file.relative_to(PROJECT_ROOT))
        for pattern, method in endpoint_patterns:
            for match in re.finditer(pattern, content):
                path = match.group(1)
                result["endpoints_by_path"][path].append({
                    "file": rel,
                    "method": method,
                })
        
        # Detect authentication
        auth_keywords = ["oauth", "jwt", "bearer", "api_key", "apikey", "auth0", "supabase"]
        for kw in auth_keywords:
            if kw in content.lower():
                result["authentication_methods"].add(kw)
    
    result["frameworks_used"] = list(result["frameworks_used"])
    result["authentication_methods"] = list(result["authentication_methods"])
    result["endpoints_by_path"] = dict(result["endpoints_by_path"])
    
    return result


# ============================================================================
# 9. SANDBOX ANALYSIS
# ============================================================================

def analyze_sandbox() -> Dict[str, Any]:
    """Analyze the sandbox directory (experimental code)."""
    print("\n[9/30] Analyzing sandbox...")
    
    result = {
        "total_files": 0,
        "scripts": [],
        "categories": defaultdict(list),
    }
    
    sandbox_dir = PROJECT_ROOT / "sandbox"
    if not sandbox_dir.exists():
        return result
    
    for file in sandbox_dir.iterdir():
        if not file.is_file():
            continue
        if file.suffix != ".py":
            continue
        
        content = safe_read(file)
        if not content:
            continue
        
        # Categorize by phase/purpose
        name_lower = file.stem.lower()
        category = "other"
        if "phase" in name_lower:
            # Extract phase number
            match = re.search(r'phase(\d+)', name_lower)
            if match:
                category = f"phase_{match.group(1)}"
            else:
                category = "phase_misc"
        elif "fix" in name_lower or "patch" in name_lower:
            category = "fixes"
        elif "test" in name_lower:
            category = "tests"
        elif "demo" in name_lower or "audit" in name_lower:
            category = "demos"
        elif "integration" in name_lower:
            category = "integration"
        
        # Extract docstring
        docstring = ""
        try:
            tree = ast.parse(content)
            if ast.get_docstring(tree):
                docstring = ast.get_docstring(tree)[:300]
        except:
            pass
        
        result["scripts"].append({
            "file": str(file.relative_to(PROJECT_ROOT)),
            "name": file.stem,
            "category": category,
            "size_bytes": file.stat().st_size,
            "docstring": docstring,
            "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
        })
        
        result["categories"][category].append(file.stem)
        result["total_files"] += 1
    
    result["categories"] = dict(result["categories"])
    return result


# ============================================================================
# 10. NOUZHIN BIOFERTILIZER ANALYSIS
# ============================================================================

def analyze_nouzhin() -> Dict[str, Any]:
    """Analyze Nouzhin biofertilizer specific code."""
    print("\n[10/30] Analyzing Nouzhin biofertilizer...")
    
    result = {
        "files_found": [],
        "keywords_found": defaultdict(list),
        "models": [],
        "database_tables": [],
    }
    
    keywords = ["nouzhin", "نوژین", "biofertilizer", "bio_fertilizer", "biological_fertilizer",
                "strain", "formulation", "cfu", "colony_forming", "microorganism"]
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        
        content = safe_read(py_file)
        if not content:
            continue
        
        content_lower = content.lower()
        rel = str(py_file.relative_to(PROJECT_ROOT))
        
        found = []
        for kw in keywords:
            if kw in content_lower:
                found.append(kw)
        
        if found:
            result["files_found"].append(rel)
            for kw in found:
                result["keywords_found"][kw].append(rel)
            
            # Find classes related to biofertilizer
            ast_data = parse_python_ast(content)
            for cls in ast_data["classes"]:
                if any(kw in cls["name"].lower() for kw in ["biofertilizer", "strain", "formulation"]):
                    result["models"].append({
                        "class": cls["name"],
                        "file": rel,
                    })
    
    # Search SQL files
    for sql_file in PROJECT_ROOT.rglob("*.sql"):
        if should_ignore(sql_file):
            continue
        content = safe_read(sql_file)
        if not content:
            continue
        
        content_lower = content.lower()
        if any(kw in content_lower for kw in ["biofertilizer", "strain", "formulation"]):
            tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", content, re.IGNORECASE)
            result["database_tables"].extend(tables)
    
    result["keywords_found"] = {k: list(set(v)) for k, v in result["keywords_found"].items()}
    return result


# ============================================================================
# 11. FINANCIAL MODULE ANALYSIS
# ============================================================================

def analyze_financial() -> Dict[str, Any]:
    """Analyze financial/accounting modules."""
    print("\n[11/30] Analyzing financial modules...")
    
    result = {
        "files_found": [],
        "keywords": defaultdict(list),
        "double_entry": False,
        "accounts_chart": False,
    }
    
    keywords = ["accounting", "ledger", "journal_entry", "double_entry",
                "debit", "credit", "balance_sheet", "profit_loss",
                "cash_flow", "npv", "irr", "roi", "cost_accounting"]
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        
        content = safe_read(py_file)
        if not content:
            continue
        
        content_lower = content.lower()
        rel = str(py_file.relative_to(PROJECT_ROOT))
        
        found = []
        for kw in keywords:
            if kw in content_lower:
                found.append(kw)
        
        if found:
            result["files_found"].append(rel)
            for kw in found:
                result["keywords"][kw].append(rel)
            if "double_entry" in content_lower or ("debit" in content_lower and "credit" in content_lower):
                result["double_entry"] = True
            if "chart_of_accounts" in content_lower or "account_code" in content_lower:
                result["accounts_chart"] = True
    
    result["keywords"] = {k: list(set(v)) for k, v in result["keywords"].items()}
    return result


# ============================================================================
# 12. GIS / MAPPING ANALYSIS
# ============================================================================

def analyze_gis() -> Dict[str, Any]:
    """Analyze GIS and mapping modules."""
    print("\n[12/30] Analyzing GIS/mapping...")
    
    result = {
        "libraries_used": set(),
        "files_using_gis": [],
        "spatial_tables": [],
        "map_viewers": [],
    }
    
    gis_libraries = ["geopandas", "shapely", "fiona", "rasterio", "gdal", "osgeo",
                     "pyproj", "cartopy", "folium", "mapbox", "leaflet",
                     "postgis", "geodjango", "geoalchemy", "sentinelhub",
                     "xarray", "rioxarray"]
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        
        content = safe_read(py_file)
        if not content:
            continue
        
        rel = str(py_file.relative_to(PROJECT_ROOT))
        found = []
        
        for lib in gis_libraries:
            if f"import {lib}" in content or f"from {lib}" in content:
                found.append(lib)
                result["libraries_used"].add(lib)
        
        if found:
            result["files_using_gis"].append({
                "file": rel,
                "libraries": found,
            })
    
    # Search for spatial SQL
    for sql_file in PROJECT_ROOT.rglob("*.sql"):
        if should_ignore(sql_file):
            continue
        content = safe_read(sql_file)
        if not content:
            continue
        
        if "GEOGRAPHY" in content or "GEOMETRY" in content or "PostGIS" in content:
            tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", content, re.IGNORECASE)
            result["spatial_tables"].extend(tables)
    
    # Search frontend for map viewers
    frontend_dir = PROJECT_ROOT / "frontend"
    if frontend_dir.exists():
        for file in frontend_dir.rglob("*"):
            if file.suffix not in {".tsx", ".jsx", ".ts", ".js"}:
                continue
            if should_ignore(file):
                continue
            content = safe_read(file)
            if not content:
                continue
            
            if any(lib in content for lib in ["Leaflet", "Mapbox", "MapLibre", "OpenLayers", "Cesium", "@react-google-maps"]):
                result["map_viewers"].append({
                    "file": str(file.relative_to(frontend_dir)),
                    "library": next((lib for lib in ["Leaflet", "Mapbox", "MapLibre", "OpenLayers", "Cesium"] if lib in content), "unknown"),
                })
    
    result["libraries_used"] = list(result["libraries_used"])
    return result


# ============================================================================
# 13. CONFIGURATION & INFRASTRUCTURE
# ============================================================================

def analyze_infrastructure() -> Dict[str, Any]:
    """Analyze configuration and infrastructure."""
    print("\n[13/30] Analyzing infrastructure...")
    
    result = {
        "dockerfiles": [],
        "docker_compose": [],
        "env_files": [],
        "requirements": {},
        "package_managers": [],
        "ci_cd": [],
    }
    
    # Dockerfiles
    for file in PROJECT_ROOT.rglob("Dockerfile*"):
        if should_ignore(file):
            continue
        result["dockerfiles"].append(str(file.relative_to(PROJECT_ROOT)))
    
    # Docker compose
    for name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
        file = PROJECT_ROOT / name
        if file.exists():
            result["docker_compose"].append(name)
    
    # Env files
    for file in PROJECT_ROOT.glob(".env*"):
        result["env_files"].append(file.name)
    
    # Requirements files
    for file in PROJECT_ROOT.glob("requirements*.txt"):
        content = safe_read(file)
        if content:
            lines = [l.strip() for l in content.split("\n") 
                    if l.strip() and not l.startswith("#")]
            result["requirements"][file.name] = lines[:30]
    
    # pyproject.toml
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        content = safe_read(pyproject)
        if content:
            result["requirements"]["pyproject.toml"] = {
                "has_deps": "dependencies" in content or "tool.poetry" in content,
                "size": pyproject.stat().st_size,
            }
    
    # Package managers
    for name in ["pnpm-lock.yaml", "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"]:
        file = PROJECT_ROOT / name
        if file.exists():
            manager = name.split("-")[0] if "-" in name else name.split(".")[0]
            result["package_managers"].append(manager)
    
    # CI/CD
    github_workflows = PROJECT_ROOT / ".github" / "workflows"
    if github_workflows.exists():
        for file in github_workflows.glob("*.yml"):
            result["ci_cd"].append({
                "type": "GitHub Actions",
                "file": f".github/workflows/{file.name}",
            })
    
    return result


# ============================================================================
# MAIN: ORCHESTRATE FULL AUDIT
# ============================================================================

def run_full_audit() -> Dict[str, Any]:
    """Run the complete archaeological audit."""
    print("=" * 80)
    print("🏛️ ECONOJIN ARCHAEOLOGICAL AUDIT")
    print("=" * 80)
    print(f"Repository: {PROJECT_ROOT}")
    print()
    
    audit = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository_path": str(PROJECT_ROOT),
            "auditor_version": "1.0",
        },
    }
    
    # Run all sections
    audit["structure"] = scan_structure()
    audit["python_engine"] = analyze_python_engine()
    audit["cpp_engine"] = analyze_cpp_engine()
    audit["frontend"] = analyze_frontend()
    audit["database"] = analyze_database()
    audit["tests"] = analyze_tests()
    audit["scientific_models"] = inventory_scientific_models()
    audit["apis"] = analyze_apis()
    audit["sandbox"] = analyze_sandbox()
    audit["nouzhin"] = analyze_nouzhin()
    audit["financial"] = analyze_financial()
    audit["gis"] = analyze_gis()
    audit["infrastructure"] = analyze_infrastructure()
    
    return audit


def generate_human_report(audit: Dict[str, Any]) -> str:
    """Generate a human-readable markdown report."""
    lines = []
    lines.append("# 🏛️ EcoNojin Archaeological Audit Report")
    lines.append(f"\n*Generated: {audit['metadata']['generated_at']}*")
    lines.append(f"*Repository: `{audit['metadata']['repository_path']}`*")
    lines.append("")
    
    # Summary
    lines.append("## 📊 Executive Summary")
    lines.append("")
    s = audit["structure"]
    lines.append(f"- **Total Files**: {s['total_files']:,}")
    lines.append(f"- **Total Lines**: {s['total_lines']:,}")
    lines.append(f"- **Top-Level Directories**: {len(s['top_level_directories'])}")
    lines.append("")
    
    pe = audit["python_engine"]
    lines.append(f"### Python Engine")
    lines.append(f"- **Services**: {len(pe['services'])}")
    lines.append(f"- **Models Detected**: {len(pe['models'])}")
    lines.append(f"- **Scientific Modules**: {len(pe['scientific_modules'])}")
    lines.append(f"- **Orchestrators**: {len(pe['orchestrators'])}")
    lines.append(f"- **Syntax Errors**: {len(pe['syntax_errors'])}")
    lines.append("")
    
    ce = audit["cpp_engine"]
    lines.append(f"### C++ Engine")
    lines.append(f"- **Source Files**: {len(ce['cpp_files'])}")
    lines.append(f"- **Header Files**: {len(ce['header_files'])}")
    lines.append(f"- **Built Modules (.pyd/.so)**: {len(ce['built_modules'])}")
    lines.append(f"- **Binding Method**: {ce['binding_method'] or 'Unknown'}")
    lines.append(f"- **Python Files Importing C++**: {len(ce['python_imports'])}")
    lines.append("")
    
    fe = audit["frontend"]
    lines.append(f"### Frontend")
    lines.append(f"- **Exists**: {'✅' if fe['exists'] else '❌'}")
    if fe['exists']:
        lines.append(f"- **Framework**: {fe['framework'] or 'Unknown'}")
        lines.append(f"- **Pages**: {len(fe['pages'])}")
        lines.append(f"- **Components**: {len(fe['components'])}")
        lines.append(f"- **API Calls Found**: {len(fe['api_calls'])}")
    lines.append("")
    
    db = audit["database"]
    lines.append(f"### Database")
    lines.append(f"- **Database Files**: {len(db['databases_found'])}")
    lines.append(f"- **Alembic Migrations**: {len(db['alembic']['migrations'])}")
    lines.append(f"- **ORM Models (tables)**: {sum(len(m['tables']) for m in db['orm_models'])}")
    lines.append(f"- **SQL Files**: {len(db['sql_files'])}")
    lines.append("")
    
    tests = audit["tests"]
    lines.append(f"### Tests")
    lines.append(f"- **Test Files**: {len(tests['test_files'])}")
    lines.append(f"- **Test Functions**: {tests['total_test_functions']}")
    lines.append(f"- **Test Classes**: {len(tests['test_classes'])}")
    lines.append("")
    
    sci = audit["scientific_models"]
    lines.append(f"### Scientific Models by Domain")
    lines.append("")
    for domain, models in sci["models_by_domain"].items():
        lines.append(f"- **{domain}**: {len(models)} model classes")
    lines.append("")
    
    apis = audit["apis"]
    lines.append(f"### APIs")
    lines.append(f"- **Frameworks**: {', '.join(apis['frameworks_used']) or 'None'}")
    lines.append(f"- **Unique Endpoint Paths**: {len(apis['endpoints_by_path'])}")
    lines.append(f"- **Routers**: {len(apis['routers'])}")
    lines.append(f"- **Authentication**: {', '.join(apis['authentication_methods']) or 'None detected'}")
    lines.append("")
    
    sandbox = audit["sandbox"]
    lines.append(f"### Sandbox")
    lines.append(f"- **Total Scripts**: {sandbox['total_files']}")
    lines.append(f"- **Categories**: {', '.join(sandbox['categories'].keys())}")
    lines.append("")
    
    nouzhin = audit["nouzhin"]
    lines.append(f"### Nouzhin Biofertilizer")
    lines.append(f"- **Files Found**: {len(nouzhin['files_found'])}")
    lines.append(f"- **Models**: {len(nouzhin['models'])}")
    lines.append(f"- **Database Tables**: {len(nouzhin['database_tables'])}")
    lines.append("")
    
    fin = audit["financial"]
    lines.append(f"### Financial Module")
    lines.append(f"- **Files Found**: {len(fin['files_found'])}")
    lines.append(f"- **Double-Entry**: {'✅' if fin['double_entry'] else '❌'}")
    lines.append(f"- **Chart of Accounts**: {'✅' if fin['accounts_chart'] else '❌'}")
    lines.append("")
    
    gis = audit["gis"]
    lines.append(f"### GIS/Mapping")
    lines.append(f"- **Libraries Used**: {', '.join(gis['libraries_used']) or 'None'}")
    lines.append(f"- **Files Using GIS**: {len(gis['files_using_gis'])}")
    lines.append(f"- **Map Viewers (Frontend)**: {len(gis['map_viewers'])}")
    lines.append(f"- **Spatial Tables**: {len(gis['spatial_tables'])}")
    lines.append("")
    
    infra = audit["infrastructure"]
    lines.append(f"### Infrastructure")
    lines.append(f"- **Dockerfiles**: {len(infra['dockerfiles'])}")
    lines.append(f"- **Docker Compose**: {len(infra['docker_compose'])}")
    lines.append(f"- **Env Files**: {len(infra['env_files'])}")
    lines.append(f"- **Package Managers**: {', '.join(infra['package_managers']) or 'None'}")
    lines.append(f"- **CI/CD**: {len(infra['ci_cd'])}")
    lines.append("")
    
    # Detailed sections
    lines.append("---")
    lines.append("")
    lines.append("## 📂 Detailed Structure")
    lines.append("")
    lines.append("### Top-Level Directories")
    lines.append("")
    lines.append("| Directory | Files | Size (MB) |")
    lines.append("|-----------|-------|-----------|")
    for name, info in sorted(s["top_level_directories"].items(), key=lambda x: -x[1]["size_bytes"])[:20]:
        lines.append(f"| `{name}` | {info['file_count']:,} | {info['size_mb']:.2f} |")
    lines.append("")
    
    # Services detail
    lines.append("## 🏢 Services Inventory")
    lines.append("")
    if pe["services"]:
        lines.append("| Service | Files | Classes | Functions | Database? | Router? | External Dependencies |")
        lines.append("|---------|-------|---------|-----------|-----------|---------|----------------------|")
        for name, info in pe["services"].items():
            db_icon = "✅" if info["database_usage"] else "—"
            router_icon = "✅" if info["has_router"] else "—"
            ext_deps = ", ".join(info["imports_external"][:5]) if info["imports_external"] else "—"
            lines.append(f"| `{name}` | {len(info['files'])} | {len(info['classes'])} | {len(info['functions'])} | {db_icon} | {router_icon} | {ext_deps} |")
    else:
        lines.append("No services found.")
    lines.append("")
    
    # C++ detail
    lines.append("## ⚙️ C++ Engine Detail")
    lines.append("")
    if ce["cpp_files"]:
        lines.append("### Source Files")
        lines.append("")
        for f in ce["cpp_files"][:20]:
            lines.append(f"- `{f['file']}` ({f['lines']} lines)")
        if len(ce["cpp_files"]) > 20:
            lines.append(f"- ... and {len(ce['cpp_files']) - 20} more")
    lines.append("")
    
    if ce["built_modules"]:
        lines.append("### Built Modules")
        lines.append("")
        for m in ce["built_modules"]:
            lines.append(f"- `{m['file']}` ({m['size_bytes']:,} bytes)")
    lines.append("")
    
    # Frontend detail
    lines.append("## 🎨 Frontend Detail")
    lines.append("")
    if fe["exists"]:
        if fe["package_json"]:
            lines.append("### Package Dependencies")
            lines.append("")
            lines.append("**Production:**")
            for dep in fe["package_json"]["dependencies"][:20]:
                lines.append(f"- {dep}")
            lines.append("")
            lines.append("**Development:**")
            for dep in fe["package_json"]["devDependencies"][:20]:
                lines.append(f"- {dep}")
            lines.append("")
        
        if fe["pages"]:
            lines.append(f"### Pages ({len(fe['pages'])})")
            lines.append("")
            for p in fe["pages"][:20]:
                lines.append(f"- `{p['path']}`")
            if len(fe["pages"]) > 20:
                lines.append(f"- ... and {len(fe['pages']) - 20} more")
            lines.append("")
    
    # Database detail
    lines.append("## 🗄️ Database Detail")
    lines.append("")
    if db["databases_found"]:
        lines.append("### Database Files")
        lines.append("")
        for d in db["databases_found"]:
            lines.append(f"- `{d['file']}` ({d['type']}, {d['size_bytes']:,} bytes)")
    lines.append("")
    
    if db["alembic"]["migrations"]:
        lines.append(f"### Alembic Migrations ({len(db['alembic']['migrations'])})")
        lines.append("")
        for m in db["alembic"]["migrations"][:10]:
            lines.append(f"- `{m['file']}` — {m['message']}")
        if len(db["alembic"]["migrations"]) > 10:
            lines.append(f"- ... and {len(db['alembic']['migrations']) - 10} more")
    lines.append("")
    
    if db["orm_models"]:
        lines.append("### ORM Models (SQLAlchemy Tables)")
        lines.append("")
        for m in db["orm_models"][:30]:
            tables = ", ".join(m["tables"])
            lines.append(f"- `{m['file']}`: {tables}")
    lines.append("")
    
    # Syntax errors
    lines.append("## ⚠️ Syntax Errors")
    lines.append("")
    if pe["syntax_errors"]:
        for err in pe["syntax_errors"]:
            lines.append(f"- `{err['file']}` line {err['line']}: {err['msg']}")
    else:
        lines.append("No syntax errors found.")
    lines.append("")
    
    # Scientific Models by domain
    lines.append("## 🔬 Scientific Models by Domain")
    lines.append("")
    for domain, models in sci["models_by_domain"].items():
        lines.append(f"### {domain} ({len(models)} models)")
        lines.append("")
        for m in models[:10]:
            lines.append(f"- **{m['class']}** in `{m['file']}`")
            if m["methods"]:
                lines.append(f"  - Methods: {', '.join(m['methods'][:5])}")
        if len(models) > 10:
            lines.append(f"- ... and {len(models) - 10} more")
        lines.append("")
    
    # APIs detail
    lines.append("## 🔌 API Endpoints")
    lines.append("")
    if apis["endpoints_by_path"]:
        lines.append(f"**{len(apis['endpoints_by_path'])} unique endpoint paths**")
        lines.append("")
        for path, impls in sorted(apis["endpoints_by_path"].items())[:30]:
            methods = ", ".join(set(i["method"] for i in impls))
            files = ", ".join(set(i["file"] for i in impls))
            lines.append(f"- `{path}` ({methods}) in `{files}`")
        if len(apis["endpoints_by_path"]) > 30:
            lines.append(f"- ... and {len(apis['endpoints_by_path']) - 30} more")
    lines.append("")
    
    # Sandbox detail
    lines.append("## 🧪 Sandbox Scripts")
    lines.append("")
    if sandbox["scripts"]:
        lines.append(f"### By Category")
        lines.append("")
        for cat, scripts in sandbox["categories"].items():
            lines.append(f"**{cat}** ({len(scripts)} scripts):")
            for s in scripts[:5]:
                lines.append(f"- {s}")
            if len(scripts) > 5:
                lines.append(f"- ... and {len(scripts) - 5} more")
            lines.append("")
    
    # Nouzhin detail
    lines.append("## 🌱 Nouzhin Biofertilizer")
    lines.append("")
    if nouzhin["files_found"]:
        lines.append(f"**{len(nouzhin['files_found'])} files** mention Nouzhin/biofertilizer:")
        lines.append("")
        for f in nouzhin["files_found"][:20]:
            lines.append(f"- `{f}`")
    else:
        lines.append("**❌ No Nouzhin-specific code found in repository**")
    lines.append("")
    
    # Financial detail
    lines.append("## 💰 Financial Module")
    lines.append("")
    if fin["files_found"]:
        lines.append(f"**{len(fin['files_found'])} files** with financial content:")
        lines.append("")
        for f in fin["files_found"][:20]:
            lines.append(f"- `{f}`")
        lines.append("")
        lines.append(f"**Keywords found:**")
        for kw, files in fin["keywords"].items():
            lines.append(f"- `{kw}`: {len(files)} files")
    else:
        lines.append("**❌ No financial module code found**")
    lines.append("")
    
    # GIS detail
    lines.append("## 🗺️ GIS/Mapping")
    lines.append("")
    if gis["files_using_gis"]:
        lines.append(f"**{len(gis['files_using_gis'])} files** use GIS libraries:")
        lines.append("")
        for f in gis["files_using_gis"][:20]:
            libs = ", ".join(f["libraries"])
            lines.append(f"- `{f['file']}`: {libs}")
    else:
        lines.append("No Python GIS code found.")
    lines.append("")
    
    if gis["map_viewers"]:
        lines.append("### Map Viewers (Frontend)")
        lines.append("")
        for v in gis["map_viewers"]:
            lines.append(f"- `{v['file']}` ({v['library']})")
    lines.append("")
    
    # Infrastructure detail
    lines.append("## 🏗️ Infrastructure")
    lines.append("")
    if infra["dockerfiles"]:
        lines.append("### Dockerfiles")
        for d in infra["dockerfiles"]:
            lines.append(f"- `{d}`")
        lines.append("")
    
    if infra["docker_compose"]:
        lines.append("### Docker Compose")
        for d in infra["docker_compose"]:
            lines.append(f"- `{d}`")
        lines.append("")
    
    if infra["requirements"]:
        lines.append("### Requirements Files")
        lines.append("")
        for name, content in infra["requirements"].items():
            if isinstance(content, list):
                lines.append(f"**{name}** ({len(content)} deps):")
                for dep in content[:10]:
                    lines.append(f"- {dep}")
                if len(content) > 10:
                    lines.append(f"- ... and {len(content) - 10} more")
            else:
                lines.append(f"**{name}**: {content}")
            lines.append("")
    
    # Key findings
    lines.append("---")
    lines.append("")
    lines.append("## 🎯 Key Findings & Observations")
    lines.append("")
    
    findings = []
    
    if pe["services"] and len(pe["services"]) >= 5:
        findings.append(f"✅ **Production microservices**: {len(pe['services'])} services detected")
    else:
        findings.append(f"⚠️ **Limited microservices**: only {len(pe['services'])} detected")
    
    if ce["built_modules"] and ce["python_imports"]:
        findings.append(f"✅ **C++ integrated**: {len(ce['built_modules'])} modules built, {len(ce['python_imports'])} Python imports")
    elif ce["built_modules"]:
        findings.append(f"⚠️ **C++ built but unused**: {len(ce['built_modules'])} modules, no Python imports")
    elif ce["cpp_files"]:
        findings.append(f"⚠️ **C++ exists but not built**: {len(ce['cpp_files'])} source files, no .pyd/.so")
    else:
        findings.append(f"❌ **No C++ engine found**")
    
    if fe["exists"] and fe["pages"] and len(fe["pages"]) > 20:
        findings.append(f"✅ **Mature frontend**: {len(fe['pages'])} pages, {len(fe['components'])} components")
    elif fe["exists"]:
        findings.append(f"⚠️ **Frontend exists but limited**: {len(fe['pages'])} pages")
    else:
        findings.append(f"❌ **No frontend found**")
    
    if db["alembic"]["migrations"] and len(db["alembic"]["migrations"]) > 3:
        findings.append(f"✅ **Active database migrations**: {len(db['alembic']['migrations'])} migrations")
    elif db["alembic"]["exists"]:
        findings.append(f"⚠️ **Alembic exists but few migrations**")
    else:
        findings.append(f"❌ **No migrations found**")
    
    if nouzhin["files_found"]:
        findings.append(f"✅ **Nouzhin IP present**: {len(nouzhin['files_found'])} files")
    else:
        findings.append(f"❌ **No Nouzhin biofertilizer code**")
    
    if fin["files_found"] and fin["double_entry"]:
        findings.append(f"✅ **Financial module with double-entry**: {len(fin['files_found'])} files")
    elif fin["files_found"]:
        findings.append(f"⚠️ **Financial module exists**: {len(fin['files_found'])} files (no double-entry)")
    else:
        findings.append(f"❌ **No financial module found**")
    
    if sandbox["total_files"] > 30:
        findings.append(f"⚠️ **Large sandbox**: {sandbox['total_files']} scripts (needs consolidation)")
    elif sandbox["total_files"] > 0:
        findings.append(f"ℹ️ **Sandbox**: {sandbox['total_files']} scripts")
    else:
        findings.append(f"ℹ️ **No sandbox**")
    
    if pe["syntax_errors"]:
        findings.append(f"❌ **{len(pe['syntax_errors'])} syntax errors** in production code")
    else:
        findings.append(f"✅ **No syntax errors** in Python code")
    
    for f in findings:
        lines.append(f"- {f}")
    lines.append("")
    
    # Critical gaps
    lines.append("---")
    lines.append("")
    lines.append("## 🚨 Critical Gaps (vs. Vision)")
    lines.append("")
    lines.append("Compared to the vision of an Integrated Land & Agriculture Platform:")
    lines.append("")
    
    gaps = []
    
    if not nouzhin["files_found"]:
        gaps.append("❌ **Nouzhin Biofertilizer Module**: MISSING (core IP)")
    else:
        gaps.append(f"✅ **Nouzhin Biofertilizer**: PARTIAL ({len(nouzhin['files_found'])} files, needs verification)")
    
    if not fin["double_entry"]:
        gaps.append("❌ **Double-Entry Accounting**: MISSING or INCOMPLETE")
    else:
        gaps.append("✅ **Double-Entry Accounting**: EXISTS")
    
    if not gis["libraries_used"]:
        gaps.append("❌ **GIS/Mapping Engine**: MISSING")
    elif len(gis["files_using_gis"]) < 5:
        gaps.append(f"⚠️ **GIS/Mapping**: PARTIAL ({len(gis['files_using_gis'])} files)")
    else:
        gaps.append(f"✅ **GIS/Mapping**: EXISTS ({len(gis['files_using_gis'])} files)")
    
    if "Optimization" not in sci["models_by_domain"]:
        gaps.append("❌ **Optimization Engine**: MISSING")
    else:
        gaps.append(f"✅ **Optimization**: EXISTS ({len(sci['models_by_domain']['Optimization'])} models)")
    
    if not any("Watershed" in d for d in sci["models_by_domain"]):
        gaps.append("❌ **Watershed Management**: MISSING")
    else:
        gaps.append(f"✅ **Watershed**: EXISTS")
    
    if not any("Economics" in d for d in sci["models_by_domain"]):
        gaps.append("❌ **Economics/Finance Model**: MISSING")
    else:
        gaps.append(f"✅ **Economics Model**: EXISTS")
    
    for g in gaps:
        lines.append(f"- {g}")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*Full machine-readable data available in `reports/archaeological_audit.json`*")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    audit = run_full_audit()
    
    # Save JSON report
    JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8"
    )
    
    # Generate and save markdown report
    md_report = generate_human_report(audit)
    MD_REPORT.write_text(md_report, encoding="utf-8")
    
    print()
    print("=" * 80)
    print("✅ ARCHAEOLOGICAL AUDIT COMPLETE")
    print("=" * 80)
    print()
    print(f"📄 JSON Report: {JSON_REPORT.relative_to(PROJECT_ROOT)}")
    print(f"   Size: {JSON_REPORT.stat().st_size / 1024:.1f} KB")
    print()
    print(f"📖 Markdown Report: {MD_REPORT.relative_to(PROJECT_ROOT)}")
    print(f"   Size: {MD_REPORT.stat().st_size / 1024:.1f} KB")
    print()
    print("🔍 Next steps:")
    print("   1. Review reports/archaeological_audit.md")
    print("   2. Send reports/archaeological_audit.json to your AI assistant")
    print("   3. Get back: 8 deliverables (Current Architecture, Inventories, Gap Matrix, Migration Roadmap)")
    print()
    
    # Print quick summary
    print("=" * 80)
    print("📊 QUICK SUMMARY")
    print("=" * 80)
    print(f"   Total files: {audit['structure']['total_files']:,}")
    print(f"   Total lines: {audit['structure']['total_lines']:,}")
    print(f"   Services: {len(audit['python_engine']['services'])}")
    print(f"   Scientific models: {sum(len(m) for m in audit['scientific_models']['models_by_domain'].values())}")
    print(f"   C++ files: {len(audit['cpp_engine']['cpp_files'])}")
    print(f"   C++ modules built: {len(audit['cpp_engine']['built_modules'])}")
    print(f"   Frontend exists: {'YES' if audit['frontend']['exists'] else 'NO'}")
    print(f"   Frontend pages: {len(audit['frontend']['pages']) if audit['frontend']['exists'] else 0}")
    print(f"   Database files: {len(audit['database']['databases_found'])}")
    print(f"   Alembic migrations: {len(audit['database']['alembic']['migrations'])}")
    print(f"   Test functions: {audit['tests']['total_test_functions']}")
    print(f"   API endpoint paths: {len(audit['apis']['endpoints_by_path'])}")
    print(f"   Sandbox scripts: {audit['sandbox']['total_files']}")
    print(f"   Nouzhin files: {len(audit['nouzhin']['files_found'])}")
    print(f"   Financial files: {len(audit['financial']['files_found'])}")
    print(f"   GIS files: {len(audit['gis']['files_using_gis'])}")


if __name__ == "__main__":
    main()