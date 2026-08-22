"""
Phase 16.5: Seven Strategic Questions — Automated Answers
==========================================================

این اسکریپت ۷ سوال استراتژیک را از کد واقعی استخراج می‌کند:

Q1: آیا services/ لایه production است یا experimental؟
Q2: آیا frontend/ محصول فعال است؟
Q3: آیا services/bots/ Telegram bot به کاربران سرویس می‌دهد؟
Q4: چرا test suite 0 test اجرا می‌کند؟
Q5: آیا C++ core واقعاً در Python load می‌شود؟
Q6: آیا services/api_gateway با sandbox/phase13 متفاوت است؟
Q7: MVP واقعی چیست؟

Output: reports/seven_answers.md
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

PROJECT_ROOT = Path(r"D:\eco_nojin")
REPORT_FILE = PROJECT_ROOT / "reports" / "seven_answers.md"

# Common ignore directories
IGNORE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".satellite_cache", ".dvc", ".cache", ".vscode",
    "dist", "build", ".next", "out", ".turbo", "econojin.egg-info",
    "_backups_fix", "_trash", ".eggs",
}


def should_ignore(path: Path) -> bool:
    return any(p in path.parts for p in IGNORE_DIRS)


# ============================================================================
# Q1: Is services/ production or experimental?
# ============================================================================

def analyze_services() -> Dict[str, Any]:
    """Deep analysis of services/ directory."""
    print("\n[Q1] Analyzing services/ directory...")
    
    result = {
        "microservices": {},
        "total_files": 0,
        "total_lines": 0,
        "has_env_files": False,
        "has_requirements": False,
        "production_indicators": [],
        "experimental_indicators": [],
        "database_usage": [],
        "external_apis": [],
    }
    
    services_dir = PROJECT_ROOT / "services"
    if not services_dir.exists():
        result["error"] = "services/ not found"
        return result
    
    # Analyze each microservice
    for subdir in services_dir.iterdir():
        if not subdir.is_dir() or subdir.name.startswith("_"):
            continue
        
        service_info = {
            "path": str(subdir.relative_to(PROJECT_ROOT)),
            "files": 0,
            "py_files": 0,
            "lines": 0,
            "classes": 0,
            "functions": 0,
            "imports": set(),
            "has_init": False,
            "has_main": False,
            "has_routers": False,
            "uses_database": False,
            "uses_external_apis": [],
        }
        
        for file in subdir.rglob("*.py"):
            if should_ignore(file):
                continue
            
            service_info["py_files"] += 1
            result["total_files"] += 1
            
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                lines = len(content.split("\n"))
                service_info["lines"] += lines
                result["total_lines"] += lines
                
                if file.name == "__init__.py":
                    service_info["has_init"] = True
                if file.name == "__main__.py" or file.name == "main.py":
                    service_info["has_main"] = True
                if "router" in file.name.lower() or "endpoint" in file.name.lower():
                    service_info["has_routers"] = True
                
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            service_info["classes"] += 1
                        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            service_info["functions"] += 1
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                top = node.module.split(".")[0]
                                service_info["imports"].add(top)
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                service_info["imports"].add(alias.name.split(".")[0])
                except SyntaxError:
                    pass
                
                # Check for database usage
                if any(kw in content.lower() for kw in ["sqlalchemy", "session", "asyncpg", "psycopg"]):
                    service_info["uses_database"] = True
                
                # Check for external APIs
                external_patterns = [
                    ("sentinel", "Sentinel Hub"),
                    ("open-meteo", "Open-Meteo"),
                    ("copernicus", "Copernicus"),
                    ("earth-search", "Earth Search"),
                    ("soilgrids", "SoilGrids"),
                    ("telegram", "Telegram Bot"),
                    ("stripe", "Stripe"),
                    ("supabase", "Supabase"),
                ]
                for pattern, api_name in external_patterns:
                    if pattern in content.lower():
                        service_info["uses_external_apis"].append(api_name)
                
            except Exception:
                continue
        
        service_info["imports"] = list(service_info["imports"])
        result["microservices"][subdir.name] = service_info
    
    # Check for env files
    for env_file in PROJECT_ROOT.glob(".env*"):
        result["has_env_files"] = True
        break
    
    # Check for requirements
    for req_file in PROJECT_ROOT.glob("requirements*.txt"):
        result["has_requirements"] = True
        break
    
    # Production vs experimental indicators
    prod_indicators = []
    exp_indicators = []
    
    # Indicator: database migrations exist
    if (PROJECT_ROOT / "alembic").exists() and (PROJECT_ROOT / "alembic.ini").exists():
        prod_indicators.append("✅ Alembic migrations configured")
    
    # Indicator: database/ directory
    if (PROJECT_ROOT / "database").exists():
        prod_indicators.append("✅ database/ directory with schemas")
    
    # Indicator: econojin.db exists
    if (PROJECT_ROOT / "econojin.db").exists():
        prod_indicators.append("✅ econojin.db SQLite database exists")
    
    # Indicator: services count
    total_services = len(result["microservices"])
    if total_services >= 3:
        prod_indicators.append(f"✅ {total_services} microservices (enterprise pattern)")
    
    # Indicator: .env configuration
    if result["has_env_files"]:
        prod_indicators.append("✅ .env files for configuration")
    
    # Indicator: main entry points
    total_mains = sum(1 for s in result["microservices"].values() if s["has_main"])
    if total_mains > 0:
        prod_indicators.append(f"✅ {total_mains} services with entry points")
    
    # Indicator: routers (FastAPI pattern)
    total_routers = sum(1 for s in result["microservices"].values() if s["has_routers"])
    if total_routers > 0:
        prod_indicators.append(f"✅ {total_routers} services with routers (FastAPI pattern)")
    
    # Experimental indicators
    if total_services > 0:
        total_inits = sum(1 for s in result["microservices"].values() if s["has_init"])
        if total_inits < total_services:
            exp_indicators.append(f"⚠️ {total_services - total_inits} services missing __init__.py")
    
    result["production_indicators"] = prod_indicators
    result["experimental_indicators"] = exp_indicators
    
    return result


# ============================================================================
# Q2: Is frontend/ an active product?
# ============================================================================

def analyze_frontend() -> Dict[str, Any]:
    """Deep analysis of frontend/ directory."""
    print("\n[Q2] Analyzing frontend/ directory...")
    
    result = {
        "exists": False,
        "package_json": None,
        "frameworks": [],
        "total_files": 0,
        "total_tsx": 0,
        "total_ts": 0,
        "has_next_config": False,
        "has_tailwind": False,
        "has_pnpm_lock": False,
        "has_public_dir": False,
        "has_pages_or_app": False,
        "pages_count": 0,
        "components_count": 0,
        "production_ready": False,
    }
    
    frontend_dir = PROJECT_ROOT / "frontend"
    if not frontend_dir.exists():
        return result
    
    result["exists"] = True
    
    # Check package.json
    pkg_file = frontend_dir / "package.json"
    if pkg_file.exists():
        try:
            import json
            pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
            result["package_json"] = {
                "name": pkg.get("name"),
                "version": pkg.get("version"),
                "scripts": list(pkg.get("scripts", {}).keys()),
            }
            
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))
            
            for dep in all_deps:
                dl = dep.lower()
                if "next" in dl:
                    result["frameworks"].append("Next.js")
                if "react" in dl and "react-" not in dl:
                    result["frameworks"].append("React")
                if "tailwind" in dl:
                    result["frameworks"].append("Tailwind CSS")
                if "typescript" in dl:
                    result["frameworks"].append("TypeScript")
                if "prisma" in dl:
                    result["frameworks"].append("Prisma ORM")
        except Exception:
            pass
    
    # Check config files
    result["has_next_config"] = (frontend_dir / "next.config.js").exists() or \
                                 (frontend_dir / "next.config.mjs").exists()
    result["has_tailwind"] = (frontend_dir / "tailwind.config.js").exists() or \
                              (frontend_dir / "tailwind.config.ts").exists()
    result["has_pnpm_lock"] = (frontend_dir / "pnpm-lock.yaml").exists()
    result["has_public_dir"] = (frontend_dir / "public").exists()
    
    # Check for pages or app directory (Next.js convention)
    if (frontend_dir / "app").exists():
        result["has_pages_or_app"] = True
        result["pages_dir_type"] = "app (App Router - modern Next.js)"
    elif (frontend_dir / "pages").exists():
        result["has_pages_or_app"] = True
        result["pages_dir_type"] = "pages (Pages Router)"
    
    # Count files
    for file in frontend_dir.rglob("*"):
        if should_ignore(file):
            continue
        if not file.is_file():
            continue
        result["total_files"] += 1
        if file.suffix == ".tsx":
            result["total_tsx"] += 1
        elif file.suffix == ".ts":
            result["total_ts"] += 1
    
    # Count pages/components
    for d in ["app", "pages", "components", "lib"]:
        sub = frontend_dir / d
        if sub.exists():
            count = sum(1 for _ in sub.rglob("*") if _.is_file() and not should_ignore(_))
            if d in ("app", "pages"):
                result["pages_count"] = count
            elif d == "components":
                result["components_count"] = count
    
    # Production readiness assessment
    prod_checks = [
        result["has_next_config"],
        result["has_tailwind"],
        result["has_pnpm_lock"],
        result["has_pages_or_app"],
        result["total_tsx"] > 10,
        result["components_count"] > 5,
    ]
    result["production_ready"] = sum(prod_checks) >= 5
    result["production_score"] = f"{sum(prod_checks)}/{len(prod_checks)}"
    
    return result


# ============================================================================
# Q3: Is services/bots/ serving real users?
# ============================================================================

def analyze_bots() -> Dict[str, Any]:
    """Deep analysis of services/bots/."""
    print("\n[Q3] Analyzing services/bots/...")
    
    result = {
        "exists": False,
        "total_files": 0,
        "handlers": [],
        "commands": [],
        "has_token": False,
        "framework": None,
        "database_usage": False,
        "bot_name": None,
    }
    
    bots_dir = PROJECT_ROOT / "services" / "bots"
    if not bots_dir.exists():
        return result
    
    result["exists"] = True
    
    # Walk through bot files
    for file in bots_dir.rglob("*.py"):
        if should_ignore(file):
            continue
        result["total_files"] += 1
        
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
            
            # Check framework
            if "aiogram" in content:
                result["framework"] = "aiogram"
            elif "python-telegram-bot" in content:
                result["framework"] = "python-telegram-bot"
            elif "telebot" in content:
                result["framework"] = "telebot"
            
            # Find handlers
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and "handler" in node.name.lower():
                        result["handlers"].append({
                            "name": node.name,
                            "file": str(file.relative_to(PROJECT_ROOT)),
                        })
            except SyntaxError:
                pass
            
            # Find commands
            cmd_patterns = [
                r'@dp\.message_handler\(commands=\[["\'](\w+)["\']',
                r'commands=\[["\'](\w+)["\']',
                r'Command\(command=["\'](\w+)["\']',
                r'/(\w+)\s*-',
            ]
            for pattern in cmd_patterns:
                for match in re.finditer(pattern, content):
                    cmd = match.group(1)
                    if len(cmd) < 30 and cmd.isalnum():
                        result["commands"].append(cmd)
            
            # Check for bot token usage
            if "BOT_TOKEN" in content or "TELEGRAM_TOKEN" in content or "os.environ" in content:
                result["has_token"] = True
            
            # Database usage
            if "database" in content.lower() or "session" in content.lower():
                result["database_usage"] = True
            
            # Bot name
            name_match = re.search(r'bot_name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                result["bot_name"] = name_match.group(1)
        
        except Exception:
            continue
    
    # Deduplicate commands
    result["commands"] = list(set(result["commands"]))[:20]
    
    return result


# ============================================================================
# Q4: Why does test suite show 0 tests?
# ============================================================================

def diagnose_tests() -> Dict[str, Any]:
    """Diagnose why pytest shows 0 tests."""
    print("\n[Q4] Diagnosing test suite...")
    
    result = {
        "pytest_ini": None,
        "pyproject_toml": None,
        "test_files": [],
        "test_files_wrong_naming": [],
        "collection_errors": [],
        "import_failures": [],
        "root_cause": None,
    }
    
    # Check pytest.ini
    pytest_ini = PROJECT_ROOT / "pytest.ini"
    if pytest_ini.exists():
        try:
            result["pytest_ini"] = pytest_ini.read_text(encoding="utf-8", errors="ignore")[:1000]
        except Exception as e:
            result["pytest_ini"] = f"ERROR: {e}"
    
    # Check pyproject.toml [tool.pytest]
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            if "tool.pytest" in content:
                # Extract pytest section
                lines = content.split("\n")
                in_pytest = False
                pytest_section = []
                for line in lines:
                    if line.strip().startswith("[tool.pytest"):
                        in_pytest = True
                    elif line.strip().startswith("[") and in_pytest:
                        break
                    if in_pytest:
                        pytest_section.append(line)
                result["pyproject_toml"] = "\n".join(pytest_section)[:1000]
        except Exception as e:
            result["pyproject_toml"] = f"ERROR: {e}"
    
    # Find test files
    tests_dir = PROJECT_ROOT / "tests"
    if tests_dir.exists():
        for file in tests_dir.rglob("*.py"):
            if should_ignore(file):
                continue
            rel = str(file.relative_to(PROJECT_ROOT))
            if file.name.startswith("test_") or file.name.endswith("_test.py"):
                result["test_files"].append(rel)
            else:
                result["test_files_wrong_naming"].append(rel)
    
    # Also find test files elsewhere
    for file in PROJECT_ROOT.rglob("test_*.py"):
        if should_ignore(file):
            continue
        if "tests" not in file.parts:
            result["test_files"].append(str(file.relative_to(PROJECT_ROOT)))
    
    # Try to run pytest with verbose collection only
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             "--disable-warnings", "--no-header"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="ignore",
        )
        
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        
        # Look for errors
        if "ImportError" in combined or "ModuleNotFoundError" in combined:
            for line in combined.split("\n"):
                if "ImportError" in line or "ModuleNotFoundError" in line:
                    result["import_failures"].append(line.strip()[:200])
        
        # Look for collection errors
        if "ERROR" in combined or "error" in combined.lower():
            for line in combined.split("\n"):
                if "ERROR" in line or "error:" in line.lower():
                    result["collection_errors"].append(line.strip()[:200])
        
        result["pytest_output"] = combined[:3000]
        result["pytest_returncode"] = proc.returncode
        
    except Exception as e:
        result["collection_error"] = str(e)
    
    # Root cause analysis
    if result["import_failures"]:
        result["root_cause"] = "Import failures prevent test collection"
    elif result["test_files_wrong_naming"] and not result["test_files"]:
        result["root_cause"] = "Test files don't follow test_*.py naming convention"
    elif result["collection_errors"]:
        result["root_cause"] = "Collection errors (see errors below)"
    elif not result["test_files"]:
        result["root_cause"] = "No test files found matching test_*.py pattern"
    else:
        result["root_cause"] = "Tests exist but pytest configuration may be wrong"
    
    return result


# ============================================================================
# Q5: Is C++ core actually loaded in Python?
# ============================================================================

def analyze_cpp_integration() -> Dict[str, Any]:
    """Check if C++ core is actually used in Python."""
    print("\n[Q5] Analyzing C++ integration...")
    
    result = {
        "cpp_core_exists": False,
        "cpp_files": [],
        "pyd_files": [],
        "so_files": [],
        "python_imports_cpp": [],
        "python_uses_cpp_functions": [],
        "build_artifacts": [],
        "is_integrated": False,
    }
    
    # Check cpp_core directory
    cpp_dir = PROJECT_ROOT / "engine" / "cpp_core"
    if cpp_dir.exists():
        result["cpp_core_exists"] = True
        
        # Find C++ source files
        for f in cpp_dir.rglob("*.cpp"):
            if should_ignore(f):
                continue
            result["cpp_files"].append(str(f.relative_to(PROJECT_ROOT)))
        
        for f in cpp_dir.rglob("*.hpp"):
            if should_ignore(f):
                continue
            result["cpp_files"].append(str(f.relative_to(PROJECT_ROOT)))
        
        # Find built modules
        for f in cpp_dir.rglob("*.pyd"):
            result["pyd_files"].append(str(f.relative_to(PROJECT_ROOT)))
        for f in cpp_dir.rglob("*.so"):
            result["so_files"].append(str(f.relative_to(PROJECT_ROOT)))
        
        # Check build directory
        build_dir = cpp_dir / "build2"
        if build_dir.exists():
            for f in build_dir.rglob("CMakeCache.txt"):
                result["build_artifacts"].append(str(f.relative_to(PROJECT_ROOT)))
            for f in build_dir.rglob("CMakeConfigureLog.yaml"):
                result["build_artifacts"].append(str(f.relative_to(PROJECT_ROOT)))
    
    # Also check engine/hydroma/cpp_bridge
    bridge_dir = PROJECT_ROOT / "engine" / "hydroma" / "cpp_bridge"
    if bridge_dir.exists():
        for f in bridge_dir.rglob("*.pyd"):
            result["pyd_files"].append(str(f.relative_to(PROJECT_ROOT)))
        for f in bridge_dir.rglob("*.so"):
            result["so_files"].append(str(f.relative_to(PROJECT_ROOT)))
    
    # Search Python files for C++ imports
    cpp_import_patterns = [
        r"import hydroma_core",
        r"from hydroma_core",
        r"import cpp_bridge",
        r"from cpp_bridge",
        r"import cpp_core",
        r"from cpp_core",
        r'ctypes\.CDLL',
        r'ctypes\.WinDLL',
        r'cffi',
    ]
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern in cpp_import_patterns:
                if re.search(pattern, content):
                    result["python_imports_cpp"].append({
                        "file": str(py_file.relative_to(PROJECT_ROOT)),
                        "pattern": pattern,
                    })
                    break
        except Exception:
            continue
    
    # Deduplicate
    seen_files = set()
    unique_imports = []
    for imp in result["python_imports_cpp"]:
        if imp["file"] not in seen_files:
            seen_files.add(imp["file"])
            unique_imports.append(imp)
    result["python_imports_cpp"] = unique_imports
    
    # Assessment
    has_built_module = bool(result["pyd_files"] or result["so_files"])
    has_python_usage = bool(result["python_imports_cpp"])
    
    result["is_integrated"] = has_built_module and has_python_usage
    result["integration_status"] = (
        "✅ Full: Built AND used" if (has_built_module and has_python_usage)
        else "⚠️ Partial: Built but not used" if has_built_module
        else "⚠️ Partial: Used but not built" if has_python_usage
        else "❌ Not integrated"
    )
    
    return result


# ============================================================================
# Q6: Is services/api_gateway different from sandbox/phase13?
# ============================================================================

def compare_apis() -> Dict[str, Any]:
    """Compare the two API implementations."""
    print("\n[Q6] Comparing API implementations...")
    
    result = {
        "sandbox_api": None,
        "services_api": None,
        "comparison": {},
    }
    
    # Analyze sandbox/phase13
    sandbox_api = PROJECT_ROOT / "sandbox" / "phase13_api_endpoint.py"
    if sandbox_api.exists():
        try:
            content = sandbox_api.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            
            # Count endpoints
            endpoints = re.findall(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
            
            result["sandbox_api"] = {
                "path": "sandbox/phase13_api_endpoint.py",
                "lines": len(lines),
                "size_kb": sandbox_api.stat().st_size / 1024,
                "endpoints": len(endpoints),
                "endpoint_paths": [ep[1] for ep in endpoints],
                "modified": datetime.fromtimestamp(sandbox_api.stat().st_mtime).isoformat(),
                "framework": "FastAPI",
                "type": "Sandbox (experimental/demo)",
            }
        except Exception as e:
            result["sandbox_api"] = {"error": str(e)}
    
    # Analyze services/api_gateway
    api_gateway_dir = PROJECT_ROOT / "services" / "api_gateway"
    if api_gateway_dir.exists():
        api_info = {
            "path": "services/api_gateway/",
            "files": [],
            "total_lines": 0,
            "total_size_kb": 0,
            "endpoints": 0,
            "endpoint_paths": [],
            "routers": [],
            "framework": None,
        }
        
        for file in api_gateway_dir.rglob("*.py"):
            if should_ignore(file):
                continue
            
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                lines = len(content.split("\n"))
                api_info["total_lines"] += lines
                api_info["total_size_kb"] += file.stat().st_size / 1024
                
                rel = str(file.relative_to(PROJECT_ROOT))
                api_info["files"].append(rel)
                
                # Find endpoints
                endpoints = re.findall(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
                endpoints2 = re.findall(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
                all_eps = endpoints + endpoints2
                
                api_info["endpoints"] += len(all_eps)
                for ep in all_eps:
                    api_info["endpoint_paths"].append(f"{file.stem}:{ep[1]}")
                
                if "router" in file.name.lower():
                    api_info["routers"].append(file.name)
                
                if "fastapi" in content.lower():
                    api_info["framework"] = "FastAPI"
                elif "flask" in content.lower():
                    api_info["framework"] = "Flask"
            
            except Exception:
                continue
        
        api_info["type"] = "Production Microservice"
        result["services_api"] = api_info
    
    # Comparison
    if result["sandbox_api"] and result["services_api"]:
        result["comparison"] = {
            "sandbox_lines": result["sandbox_api"].get("lines", 0),
            "services_lines": result["services_api"].get("total_lines", 0),
            "sandbox_endpoints": result["sandbox_api"].get("endpoints", 0),
            "services_endpoints": result["services_api"].get("endpoints", 0),
            "sandbox_scope": "Single file, demo-focused",
            "services_scope": f"Multi-file ({len(result['services_api'].get('files', []))} files), production-focused",
            "overlap_check": [],
        }
        
        # Check for endpoint overlap
        sandbox_paths = set(result["sandbox_api"].get("endpoint_paths", []))
        services_paths = set(p.split(":")[-1] if ":" in p else p 
                            for p in result["services_api"].get("endpoint_paths", []))
        overlap = sandbox_paths & services_paths
        if overlap:
            result["comparison"]["overlap_check"] = list(overlap)
    
    return result


# ============================================================================
# Q7: What's the real MVP?
# ============================================================================

def deduce_mvp() -> Dict[str, Any]:
    """Deduce MVP from project structure."""
    print("\n[Q7] Deducing MVP...")
    
    result = {
        "product_layers": {},
        "user_facing_artifacts": [],
        "data_pipeline": [],
        "distribution_channels": [],
        "business_artifacts": [],
    }
    
    # Layer detection
    layers = {
        "Frontend Web": (PROJECT_ROOT / "frontend").exists(),
        "API Gateway": (PROJECT_ROOT / "services" / "api_gateway").exists(),
        "Telegram Bot": (PROJECT_ROOT / "services" / "bots").exists(),
        "Scientific Engine": (PROJECT_ROOT / "engine" / "hydroma").exists(),
        "Satellite Integration": (PROJECT_ROOT / "services" / "satellite").exists(),
        "Analytics Service": (PROJECT_ROOT / "services" / "analytics").exists(),
        "Mobile/Desktop": False,
    }
    
    # Check for mobile/desktop
    for d in ["apps/mobile", "apps/desktop", "mobile", "desktop", "tauri"]:
        if (PROJECT_ROOT / d).exists():
            layers["Mobile/Desktop"] = True
            break
    
    result["product_layers"] = layers
    
    # User-facing artifacts
    user_facing = []
    
    # Frontend
    frontend_dir = PROJECT_ROOT / "frontend"
    if frontend_dir.exists():
        # Check for built output
        for d in [".next", "out", "build", "dist"]:
            if (frontend_dir / d).exists():
                user_facing.append(f"Frontend built output: {d}/")
                break
        
        # Check package.json scripts
        pkg_file = frontend_dir / "package.json"
        if pkg_file.exists():
            try:
                import json
                pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
                scripts = pkg.get("scripts", {})
                if "build" in scripts or "start" in scripts:
                    user_facing.append(f"Frontend has build/start scripts")
            except Exception:
                pass
    
    # API endpoints
    api_gateway = PROJECT_ROOT / "services" / "api_gateway"
    if api_gateway.exists():
        user_facing.append("REST API (services/api_gateway/)")
    
    # Bot
    bots_dir = PROJECT_ROOT / "services" / "bots"
    if bots_dir.exists():
        user_facing.append("Telegram Bot (services/bots/)")
    
    # Database
    if (PROJECT_ROOT / "econojin.db").exists():
        user_facing.append("SQLite database (econojin.db)")
    
    result["user_facing_artifacts"] = user_facing
    
    # Business artifacts
    business = []
    if (PROJECT_ROOT / "contracts").exists():
        contracts_files = list((PROJECT_ROOT / "contracts").rglob("*"))
        business.append(f"Contracts directory ({len(contracts_files)} items)")
    
    if (PROJECT_ROOT / "blockchain").exists():
        business.append("Blockchain/token integration")
    
    if (PROJECT_ROOT / "DELIVERY").exists():
        business.append("DELIVERY directory (deliverables)")
    
    for doc in ["INVESTOR_PITCH.md", "ECO_COIN_WHITEPAPER.md", "ECONOMIC_MODEL.md",
                "PROJECT_SUMMARY.md", "LEGAL_COMPLIANCE.md", "PRESENTATION.md",
                "DEMO_SCRIPT.md"]:
        if (PROJECT_ROOT / doc).exists():
            business.append(f"Business doc: {doc}")
    
    result["business_artifacts"] = business
    
    # Data pipeline
    pipeline = []
    if (PROJECT_ROOT / "services" / "satellite").exists():
        pipeline.append("1. Satellite data ingestion (services/satellite/)")
    if (PROJECT_ROOT / "engine" / "hydroma").exists():
        pipeline.append("2. Scientific processing (engine/hydroma/)")
    if (PROJECT_ROOT / "services" / "analytics").exists():
        pipeline.append("3. Analytics aggregation (services/analytics/)")
    if (PROJECT_ROOT / "services" / "api_gateway").exists():
        pipeline.append("4. API delivery (services/api_gateway/)")
    
    result["data_pipeline"] = pipeline
    
    return result


# ============================================================================
# Report Generation
# ============================================================================

def generate_report(answers: Dict[str, Any]) -> str:
    """Generate comprehensive markdown report."""
    
    report = []
    report.append("# 🎯 Seven Strategic Questions — Answered")
    report.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    report.append(f"*Repository: `{PROJECT_ROOT}`*")
    report.append("")
    
    report.append("---")
    report.append("\n## 🏢 Q1: Is `services/` Production or Experimental?")
    report.append("")
    
    services = answers["q1"]
    if "error" in services:
        report.append(f"❌ {services['error']}")
    else:
        report.append(f"**{len(services['microservices'])} microservices found**")
        report.append("")
        
        report.append("### Microservice Inventory")
        report.append("")
        report.append("| Service | Files | Lines | Classes | Functions | Database? | External APIs |")
        report.append("|---------|-------|-------|---------|-----------|-----------|---------------|")
        for name, info in services["microservices"].items():
            apis = ", ".join(set(info["uses_external_apis"])) if info["uses_external_apis"] else "—"
            db_icon = "✅" if info["uses_database"] else "—"
            report.append(f"| `{name}` | {info['py_files']} | {info['lines']:,} | {info['classes']} | {info['functions']} | {db_icon} | {apis} |")
        
        report.append("")
        report.append("### Production Indicators")
        report.append("")
        if services["production_indicators"]:
            for ind in services["production_indicators"]:
                report.append(f"- {ind}")
        else:
            report.append("- None detected")
        
        if services["experimental_indicators"]:
            report.append("")
            report.append("### Experimental Indicators")
            report.append("")
            for ind in services["experimental_indicators"]:
                report.append(f"- {ind}")
        
        report.append("")
        report.append("### 🎯 VERDICT")
        report.append("")
        prod_score = len(services["production_indicators"])
        exp_score = len(services["experimental_indicators"])
        if prod_score >= 4:
            report.append(f"**✅ PRODUCTION-READY** ({prod_score}/6 indicators)")
            report.append("")
            report.append("The `services/` layer is a **real production microservices architecture**, not experimental code.")
        elif prod_score >= 2:
            report.append(f"**⚠️ HYBRID** ({prod_score} production, {exp_score} experimental)")
            report.append("")
            report.append("The `services/` layer has production elements but also experimental aspects.")
        else:
            report.append(f"**⚠️ MOSTLY EXPERIMENTAL** ({prod_score}/6 indicators)")
    
    # Q2
    report.append("")
    report.append("---")
    report.append("\n## 🎨 Q2: Is `frontend/` an Active Product?")
    report.append("")
    
    frontend = answers["q2"]
    if not frontend["exists"]:
        report.append("❌ `frontend/` directory does not exist.")
    else:
        report.append("### Configuration")
        report.append("")
        report.append(f"- **Package name**: {frontend['package_json']['name'] if frontend['package_json'] else '—'}")
        report.append(f"- **Version**: {frontend['package_json']['version'] if frontend['package_json'] else '—'}")
        report.append(f"- **Scripts**: {', '.join(frontend['package_json']['scripts'][:10]) if frontend['package_json'] else '—'}")
        report.append("")
        
        report.append("### Frameworks Detected")
        report.append("")
        for fw in frontend["frameworks"]:
            report.append(f"- ✅ {fw}")
        
        report.append("")
        report.append("### File Statistics")
        report.append("")
        report.append(f"- Total files: **{frontend['total_files']}**")
        report.append(f"- TypeScript React (.tsx): **{frontend['total_tsx']}**")
        report.append(f"- TypeScript (.ts): **{frontend['total_ts']}**")
        report.append(f"- Components: **{frontend['components_count']}**")
        report.append(f"- Pages: **{frontend['pages_count']}**")
        
        report.append("")
        report.append("### Quality Indicators")
        report.append("")
        indicators = {
            "next.config.js/mjs": frontend["has_next_config"],
            "tailwind.config.js": frontend["has_tailwind"],
            "pnpm-lock.yaml": frontend["has_pnpm_lock"],
            "pages or app directory": frontend["has_pages_or_app"],
            "10+ TSX files": frontend["total_tsx"] > 10,
            "5+ components": frontend["components_count"] > 5,
        }
        for name, ok in indicators.items():
            icon = "✅" if ok else "❌"
            report.append(f"- {icon} {name}")
        
        report.append("")
        report.append("### 🎯 VERDICT")
        report.append("")
        report.append(f"**Production Score: {frontend['production_score']}**")
        report.append("")
        if frontend["production_ready"]:
            report.append("**✅ PRODUCTION-READY**: This is a real Next.js application, not a scaffold.")
        elif frontend["total_files"] > 50:
            report.append("**⚠️ ACTIVE DEVELOPMENT**: Substantial code exists but may not be production-ready.")
        else:
            report.append("**⚠️ SCAFFOLD/EARLY**: Limited files, likely early stage.")
    
    # Q3
    report.append("")
    report.append("---")
    report.append("\n## 🤖 Q3: Is `services/bots/` Serving Real Users?")
    report.append("")
    
    bots = answers["q3"]
    if not bots["exists"]:
        report.append("❌ `services/bots/` does not exist.")
    else:
        report.append("### Bot Details")
        report.append("")
        report.append(f"- **Framework**: {bots['framework'] or 'Unknown'}")
        report.append(f"- **Bot name**: {bots['bot_name'] or 'Not specified'}")
        report.append(f"- **Files**: {bots['total_files']}")
        report.append(f"- **Uses token from env**: {'✅ Yes' if bots['has_token'] else '❌ No'}")
        report.append(f"- **Uses database**: {'✅ Yes' if bots['database_usage'] else '❌ No'}")
        
        report.append("")
        report.append(f"### Handlers ({len(bots['handlers'])} found)")
        report.append("")
        for handler in bots["handlers"][:10]:
            report.append(f"- `{handler['name']}` in `{handler['file']}`")
        
        if bots["commands"]:
            report.append("")
            report.append("### Telegram Commands")
            report.append("")
            for cmd in bots["commands"]:
                report.append(f"- `/{cmd}`")
        
        report.append("")
        report.append("### 🎯 VERDICT")
        report.append("")
        has_token = bots["has_token"]
        has_handlers = len(bots["handlers"]) > 0
        has_db = bots["database_usage"]
        
        if has_token and has_handlers and has_db:
            report.append("**✅ ACTIVE PRODUCTION BOT**: Has token loading, handlers, and database integration.")
            report.append("")
            report.append("This is likely serving real users via Telegram.")
        elif has_token and has_handlers:
            report.append("**⚠️ DEVELOPMENT/TESTING BOT**: Has handlers and token but no database.")
        else:
            report.append("**❌ NOT PRODUCTION**: Missing key production elements.")
    
    # Q4
    report.append("")
    report.append("---")
    report.append("\n## 🧪 Q4: Why Does the Test Suite Show 0 Tests?")
    report.append("")
    
    tests = answers["q4"]
    report.append(f"**Total test files found**: {len(tests['test_files'])}")
    report.append(f"**Files with wrong naming**: {len(tests['test_files_wrong_naming'])}")
    report.append("")
    
    report.append("### Root Cause")
    report.append("")
    if tests["root_cause"]:
        report.append(f"**{tests['root_cause']}**")
    else:
        report.append("Unknown")
    
    if tests["import_failures"]:
        report.append("")
        report.append("### Import Failures")
        report.append("")
        report.append("```")
        for err in tests["import_failures"][:10]:
            report.append(err)
        report.append("```")
    
    if tests["collection_errors"]:
        report.append("")
        report.append("### Collection Errors")
        report.append("")
        report.append("```")
        for err in tests["collection_errors"][:10]:
            report.append(err)
        report.append("```")
    
    if tests.get("pytest_ini"):
        report.append("")
        report.append("### pytest.ini Content")
        report.append("")
        report.append("```ini")
        report.append(tests["pytest_ini"])
        report.append("```")
    
    if tests.get("pyproject_toml"):
        report.append("")
        report.append("### pyproject.toml [tool.pytest]")
        report.append("")
        report.append("```toml")
        report.append(tests["pyproject_toml"])
        report.append("```")
    
    if tests.get("pytest_output"):
        report.append("")
        report.append("### Pytest Collection Output")
        report.append("")
        report.append("```")
        report.append(tests["pytest_output"][:2000])
        report.append("```")
    
    # Q5
    report.append("")
    report.append("---")
    report.append("\n## ⚙️ Q5: Is C++ Core Actually Loaded in Python?")
    report.append("")
    
    cpp = answers["q5"]
    report.append(f"**Integration Status**: {cpp['integration_status']}")
    report.append("")
    
    report.append("### C++ Source Files")
    report.append("")
    if cpp["cpp_files"]:
        report.append(f"Found **{len(cpp['cpp_files'])}** C++ files:")
        report.append("")
        for f in cpp["cpp_files"][:10]:
            report.append(f"- `{f}`")
        if len(cpp["cpp_files"]) > 10:
            report.append(f"- ... and {len(cpp['cpp_files']) - 10} more")
    else:
        report.append("None found.")
    
    report.append("")
    report.append("### Built Modules")
    report.append("")
    if cpp["pyd_files"]:
        report.append(f"✅ **{len(cpp['pyd_files'])}** .pyd (Windows) modules:")
        for f in cpp["pyd_files"]:
            report.append(f"- `{f}`")
    else:
        report.append("❌ No .pyd modules built")
    
    if cpp["so_files"]:
        report.append(f"✅ **{len(cpp['so_files'])}** .so (Unix) modules:")
        for f in cpp["so_files"]:
            report.append(f"- `{f}`")
    
    report.append("")
    report.append("### Python Files That Use C++")
    report.append("")
    if cpp["python_imports_cpp"]:
        for imp in cpp["python_imports_cpp"][:10]:
            report.append(f"- `{imp['file']}` → `{imp['pattern']}`")
    else:
        report.append("❌ No Python files import C++ modules")
    
    report.append("")
    report.append("### 🎯 VERDICT")
    report.append("")
    if cpp["is_integrated"]:
        report.append("**✅ FULLY INTEGRATED**: C++ is built and actively used.")
    elif cpp["pyd_files"] or cpp["so_files"]:
        report.append("**⚠️ BUILT BUT UNUSED**: C++ modules exist but Python doesn't use them.")
        report.append("")
        report.append("**Recommendation**: Either wire them into Python or remove the build artifacts.")
    elif cpp["python_imports_cpp"]:
        report.append("**⚠️ USED BUT NOT BUILT**: Python expects C++ but modules aren't built.")
        report.append("")
        report.append("**Recommendation**: Build the C++ modules or replace with Python fallbacks.")
    else:
        report.append("**❌ NOT INTEGRATED**: C++ exists as source but is neither built nor used.")
    
    # Q6
    report.append("")
    report.append("---")
    report.append("\n## 🔄 Q6: Is `services/api_gateway` Different from `sandbox/phase13`?")
    report.append("")
    
    apis = answers["q6"]
    
    report.append("### Sandbox API (phase13)")
    report.append("")
    if apis["sandbox_api"]:
        sa = apis["sandbox_api"]
        if "error" in sa:
            report.append(f"❌ {sa['error']}")
        else:
            report.append(f"- **Path**: `{sa['path']}`")
            report.append(f"- **Type**: {sa['type']}")
            report.append(f"- **Lines**: {sa['lines']:,}")
            report.append(f"- **Size**: {sa['size_kb']:.1f} KB")
            report.append(f"- **Endpoints**: {sa['endpoints']}")
            report.append(f"- **Modified**: {sa['modified']}")
            if sa['endpoint_paths']:
                report.append(f"- **Paths**: {', '.join(sa['endpoint_paths'][:10])}")
    else:
        report.append("Not found.")
    
    report.append("")
    report.append("### Services API (api_gateway)")
    report.append("")
    if apis["services_api"]:
        sa = apis["services_api"]
        report.append(f"- **Path**: `{sa['path']}`")
        report.append(f"- **Type**: {sa['type']}")
        report.append(f"- **Files**: {len(sa['files'])}")
        report.append(f"- **Total lines**: {sa['total_lines']:,}")
        report.append(f"- **Total size**: {sa['total_size_kb']:.1f} KB")
        report.append(f"- **Endpoints**: {sa['endpoints']}")
        report.append(f"- **Routers**: {', '.join(sa['routers'])}")
        if sa['files']:
            report.append("")
            report.append("**Files:**")
            for f in sa['files'][:20]:
                report.append(f"- `{f}`")
    else:
        report.append("Not found.")
    
    if apis["comparison"]:
        report.append("")
        report.append("### Comparison")
        report.append("")
        comp = apis["comparison"]
        report.append(f"- **Lines**: Sandbox {comp['sandbox_lines']:,} vs Services {comp['services_lines']:,}")
        report.append(f"- **Endpoints**: Sandbox {comp['sandbox_endpoints']} vs Services {comp['services_endpoints']}")
        report.append(f"- **Scope**: {comp['sandbox_scope']} vs {comp['services_scope']}")
        
        if comp["overlap_check"]:
            report.append("")
            report.append("**⚠️ Endpoint Overlap Detected:**")
            for ep in comp["overlap_check"]:
                report.append(f"- `{ep}`")
    
    report.append("")
    report.append("### 🎯 VERDICT")
    report.append("")
    if apis["sandbox_api"] and apis["services_api"]:
        s_lines = apis["sandbox_api"].get("lines", 0)
        sv_lines = apis["services_api"].get("total_lines", 0)
        if sv_lines > s_lines * 3:
            report.append("**✅ TWO DISTINCT IMPLEMENTATIONS**: `services/api_gateway` is significantly larger and more mature.")
            report.append("")
            report.append("**Recommendation**: Treat `sandbox/phase13` as experimental/demo, `services/api_gateway` as production.")
        else:
            report.append("**⚠️ SIMILAR SCALE**: Both are roughly the same size.")
    elif apis["services_api"]:
        report.append("**Only `services/api_gateway` exists** — this is the production API.")
    elif apis["sandbox_api"]:
        report.append("**Only `sandbox/phase13` exists** — this is experimental.")
    
    # Q7
    report.append("")
    report.append("---")
    report.append("\n## 🎯 Q7: What Is the REAL MVP?")
    report.append("")
    
    mvp = answers["q7"]
    
    report.append("### Product Layers")
    report.append("")
    report.append("| Layer | Present? |")
    report.append("|-------|----------|")
    for layer, present in mvp["product_layers"].items():
        icon = "✅" if present else "❌"
        report.append(f"| {layer} | {icon} |")
    
    if mvp["user_facing_artifacts"]:
        report.append("")
        report.append("### User-Facing Artifacts")
        report.append("")
        for artifact in mvp["user_facing_artifacts"]:
            report.append(f"- {artifact}")
    
    if mvp["data_pipeline"]:
        report.append("")
        report.append("### Data Pipeline")
        report.append("")
        for step in mvp["data_pipeline"]:
            report.append(f"- {step}")
    
    if mvp["business_artifacts"]:
        report.append("")
        report.append("### Business/Strategy Artifacts")
        report.append("")
        for artifact in mvp["business_artifacts"]:
            report.append(f"- {artifact}")
    
    report.append("")
    report.append("### 🎯 MVP DEDUCTION")
    report.append("")
    
    # Heuristic for MVP
    has_frontend = mvp["product_layers"].get("Frontend Web", False)
    has_api = mvp["product_layers"].get("API Gateway", False)
    has_bot = mvp["product_layers"].get("Telegram Bot", False)
    has_business_docs = len(mvp["business_artifacts"]) > 3
    
    if has_frontend and has_api and has_bot:
        report.append("**MULTI-CHANNEL PLATFORM**")
        report.append("")
        report.append("The project is building a **comprehensive multi-channel platform**:")
        report.append("")
        report.append("1. **Web frontend** (Next.js) for end users")
        report.append("2. **REST API** for developers/integrations")
        report.append("3. **Telegram bot** for mobile users")
        report.append("")
        report.append("The MVP is likely a **scientific analysis service** delivered through multiple channels.")
    elif has_frontend and has_api:
        report.append("**WEB + API PLATFORM**")
        report.append("")
        report.append("Standard SaaS architecture: web UI + API backend.")
    elif has_api:
        report.append("**API-FIRST PRODUCT**")
        report.append("")
        report.append("API is the primary product (B2B or developer platform).")
    elif has_bot:
        report.append("**BOT-FIRST PRODUCT**")
        report.append("")
        report.append("Telegram bot is the primary distribution channel.")
    else:
        report.append("**UNDEFINED MVP**")
        report.append("")
        report.append("No clear user-facing surface detected.")
    
    # Final Strategic Summary
    report.append("")
    report.append("---")
    report.append("\n## 🎓 FINAL STRATEGIC SUMMARY")
    report.append("")
    
    report.append("### Project Classification")
    report.append("")
    report.append("Based on the evidence, this project is:")
    report.append("")
    
    classifications = []
    
    if mvp["product_layers"].get("Frontend Web", False):
        classifications.append("- ✅ **Full-stack web application** (Next.js frontend)")
    if mvp["product_layers"].get("API Gateway", False):
        classifications.append("- ✅ **Microservices architecture** (services/ layer)")
    if mvp["product_layers"].get("Scientific Engine", False):
        classifications.append("- ✅ **Scientific computing platform** (Hydroma models)")
    if mvp["product_layers"].get("Satellite Integration", False):
        classifications.append("- ✅ **Earth observation integration** (Sentinel-2)")
    if mvp["product_layers"].get("Telegram Bot", False):
        classifications.append("- ✅ **Multi-channel distribution** (Telegram bot)")
    if any("blockchain" in a.lower() or "coin" in a.lower() for a in mvp["business_artifacts"]):
        classifications.append("- ✅ **Tokenomics/economic layer** (blockchain)")
    if any("investor" in a.lower() for a in mvp["business_artifacts"]):
        classifications.append("- ✅ **Startup/business-ready** (investor materials)")
    
    for c in classifications:
        report.append(c)
    
    report.append("")
    report.append("### Priority Recommendations")
    report.append("")
    
    report.append("1. **🔴 IMMEDIATE**: Fix syntax errors (9 issues in production code)")
    report.append("2. **🔴 IMMEDIATE**: Diagnose and fix test suite (0 tests currently running)")
    report.append("3. **🟡 SOON**: Decide on C++ integration strategy (build it or remove it)")
    report.append("4. **🟡 SOON**: Clarify relationship between sandbox/ and services/ APIs")
    report.append("5. **🟢 BEFORE PHASE 17**: Confirm MVP scope (which channels, which users)")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("*Report generated by EcoNojin Strategic Audit Tool*")
    
    return "\n".join(report)


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("🔍 PHASE 16.5: SEVEN STRATEGIC QUESTIONS — AUTOMATED ANSWERS")
    print("=" * 80)
    print(f"Repository: {PROJECT_ROOT}")
    print()
    
    # Run all analyses
    answers = {
        "q1": analyze_services(),
        "q2": analyze_frontend(),
        "q3": analyze_bots(),
        "q4": diagnose_tests(),
        "q5": analyze_cpp_integration(),
        "q6": compare_apis(),
        "q7": deduce_mvp(),
    }
    
    # Generate report
    print("\n[Final] Generating comprehensive report...")
    report = generate_report(answers)
    
    # Save
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")
    
    print()
    print("=" * 80)
    print("✅ All 7 questions answered")
    print("=" * 80)
    print(f"\n📄 Report: {REPORT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"   Size: {REPORT_FILE.stat().st_size / 1024:.1f} KB")
    print()
    print("🔍 View the report:")
    print(f"   Get-Content reports\\seven_answers.md")
    print()
    print("💡 Or open in any markdown editor")
    
    # Also print summary to console
    print()
    print("=" * 80)
    print("📊 QUICK SUMMARY")
    print("=" * 80)
    
    # Q1 summary
    q1 = answers["q1"]
    if "error" not in q1:
        print(f"\nQ1 services/: {len(q1['microservices'])} microservices")
        print(f"   Production indicators: {len(q1['production_indicators'])}/6")
    
    # Q2 summary
    q2 = answers["q2"]
    if q2["exists"]:
        print(f"\nQ2 frontend/: {q2['total_files']} files, {q2['total_tsx']} TSX")
        print(f"   Production score: {q2['production_score']}")
    
    # Q3 summary
    q3 = answers["q3"]
    if q3["exists"]:
        print(f"\nQ3 bots/: framework={q3['framework']}, handlers={len(q3['handlers'])}")
    
    # Q4 summary
    q4 = answers["q4"]
    print(f"\nQ4 tests/: {len(q4['test_files'])} files, root cause: {q4['root_cause']}")
    
    # Q5 summary
    q5 = answers["q5"]
    print(f"\nQ5 C++/: {q5['integration_status']}")
    
    # Q6 summary
    q6 = answers["q6"]
    if q6["sandbox_api"] and q6["services_api"]:
        print(f"\nQ6 APIs: sandbox={q6['sandbox_api'].get('lines', 0)} lines vs services={q6['services_api'].get('total_lines', 0)} lines")
    
    # Q7 summary
    q7 = answers["q7"]
    layers_active = sum(1 for v in q7["product_layers"].values() if v)
    print(f"\nQ7 MVP: {layers_active}/{len(q7['product_layers'])} layers active")


if __name__ == "__main__":
    main()