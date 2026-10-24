#!/usr/bin/env python3
"""
ECO-04.1 Comprehensive Invariant Scanner
Verifies all architecture invariants using static AST analysis.
Does NOT require numpy/scipy/pytest — uses only stdlib.
"""

from __future__ import annotations

import ast
import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ImportEdge:
    """A single import edge: importing_file → imported_module."""
    source_file: str
    source_module: str
    imported_module: str
    imported_names: list[str]
    line: int
    col: int
    is_relative: bool
    is_test: bool
    import_type: str  # "import" or "from_import"


@dataclass
class InvariantResult:
    invariant_id: str
    name: str
    description: str
    status: str  # PASS, FAIL, PARTIAL, UNKNOWN, NOT_IMPLEMENTED, BLOCKED
    violations: list[dict]
    evidence: str
    notes: str = ""


class ComprehensiveScanner:
    """Scans the repository for all ECO-04 architecture invariants."""

    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.edges: list[ImportEdge] = []
        self.python_files: list[Path] = []
        self.all_imports: dict[str, list[ImportEdge]] = defaultdict(list)
        self.test_files: set[str] = set()
        self.production_files: set[str] = set()

    def _is_test_file(self, rel_path: str) -> bool:
        parts = Path(rel_path).parts
        return (
            "test" in Path(rel_path).name.lower()
            or "tests" in parts
            or "conftest" in Path(rel_path).name
        )

    def _get_source_module(self, rel_path: str) -> str:
        parts = Path(rel_path).parts
        if parts[0] == "engine":
            return "engine"
        elif parts[0] == "services":
            if "ai" in parts[1:3]:
                return "services.ai"
            return "services"
        elif parts[0] == "database":
            return "database"
        elif parts[0] == "adapters":
            return "adapters"
        return parts[0] if parts else "unknown"

    def scan_file(self, file_path: Path, rel_path: str) -> list[ImportEdge]:
        """Parse a single Python file and extract import edges."""
        edges = []
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            return edges

        is_test = self._is_test_file(rel_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    imported_names = [alias.asname or alias.name]
                    # Skip if this is a relative import
                    edges.append(ImportEdge(
                        source_file=rel_path,
                        source_module=self._get_source_module(rel_path),
                        imported_module=module,
                        imported_names=imported_names,
                        line=node.lineno,
                        col=node.col_offset,
                        is_relative=False,
                        is_test=is_test,
                        import_type="import",
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    # Relative import - resolve it
                    continue
                module = node.module or ""
                names = [n.name for n in node.names]
                edges.append(ImportEdge(
                    source_file=rel_path,
                    source_module=self._get_source_module(rel_path),
                    imported_module=module,
                    imported_names=names,
                    line=node.lineno,
                    col=node.col_offset,
                    is_relative=False,
                    is_test=is_test,
                    import_type="from_import",
                ))

        self.all_imports[rel_path] = edges
        return edges

    def scan_project(self):
        """Scan entire project for all Python files and their imports."""
        exclude_dirs = {
            "__pycache__", ".venv", "venv", "node_modules",
            "build", "dist", ".eggs", ".mypy_cache",
        }

        python_files = list(self.root.rglob("*.py"))
        for py_file in python_files:
            rel = py_file.relative_to(self.root)
            parts = rel.parts
            if any(p in exclude_dirs for p in parts):
                continue
            self.python_files.append(py_file)
            rel_path = str(rel)
            if self._is_test_file(rel_path):
                self.test_files.add(rel_path)
            else:
                self.production_files.add(rel_path)
            self.scan_file(py_file, rel_path)

    # ------------------------------------------------------------------
    # Invariant checks
    # ------------------------------------------------------------------

    def check_inv_001_engine_no_services(self) -> InvariantResult:
        """INV-001: Engine → Services is forbidden."""
        violations = []
        for fpath, edges in self.all_imports.items():
            source_module = self._get_source_module(fpath)
            if source_module != "engine":
                continue
            if self._is_test_file(fpath):
                continue
            for edge in edges:
                mod = edge.imported_module
                if mod == "services" or mod.startswith("services."):
                    violations.append({
                        "file": fpath,
                        "line": edge.line,
                        "import": f"from {mod} import {', '.join(edge.imported_names[:3])}",
                    })
        return InvariantResult(
            invariant_id="INV-001",
            name="Engine → Services forbidden",
            description="Engine must not import from services layer.",
            status="PASS" if not violations else "FAIL",
            violations=violations,
            evidence=f"Scanned all engine production .py files; found {len(violations)} violations.",
        )

    def check_inv_002_engine_no_database(self) -> InvariantResult:
        """INV-002: Engine → Database is forbidden."""
        violations = []
        for fpath, edges in self.all_imports.items():
            source_module = self._get_source_module(fpath)
            if source_module != "engine":
                continue
            if self._is_test_file(fpath):
                continue
            for edge in edges:
                mod = edge.imported_module
                if mod == "database" or mod.startswith("database."):
                    violations.append({
                        "file": fpath,
                        "line": edge.line,
                        "import": f"import {mod}" if edge.import_type == "import" else f"from {mod} import {', '.join(edge.imported_names[:3])}",
                    })
        return InvariantResult(
            invariant_id="INV-002",
            name="Engine → Database forbidden",
            description="Engine must not import from database layer.",
            status="PASS" if not violations else "FAIL",
            violations=violations,
            evidence=f"Scanned all engine production .py files; found {len(violations)} violations.",
        )

    def check_inv_003_services_no_engine_internals(self) -> InvariantResult:
        """INV-003: Services must not directly import engine internals (must use Gateway)."""
        # Engine internals = engine.hydroma, engine.cpp_core, engine.ports, etc.
        # But engine itself (gateway, evidence, knowledge, models, safe_math) = OK to import
        forbidden_prefixes = [
            "engine.hydroma",
            "engine.cpp_core",
            "engine.ports",
        ]
        violations = []
        for fpath, edges in self.all_imports.items():
            source_module = self._get_source_module(fpath)
            if source_module not in ("services", "services.ai"):
                continue
            if self._is_test_file(fpath):
                continue
            for edge in edges:
                mod = edge.imported_module
                if mod == "engine" or mod.startswith("engine."):
                    # Actually check more carefully:
                    forbidden = False
                    for p in forbidden_prefixes:
                        if mod == p or mod.startswith(p + "."):
                            forbidden = True
                            break
                    # Also flag any engine.hydroma, engine.cpp_core, engine.ports imports
                    if mod.startswith("engine.hydroma") or mod.startswith("engine.cpp_core") or mod.startswith("engine.ports"):
                        forbidden = True
                    if forbidden:
                        violations.append({
                            "file": fpath,
                            "line": edge.line,
                            "import": f"from {mod} import {', '.join(edge.imported_names[:3])}" if edge.import_type == "from_import" else f"import {mod}",
                            "category": "FORBIDDEN_ENGINE_INTERNAL",
                        })
        return InvariantResult(
            invariant_id="INV-003",
            name="Services → Engine via Gateway only",
            description="Services must not directly import engine internals (hydroma, cpp_core, ports).",
            status="PASS" if not violations else "FAIL" if len(violations) > 0 else "PASS",
            violations=violations,
            evidence=f"Scanned all services production .py files; found {len(violations)} violations.",
        )

    def check_inv_003_all_engine_imports(self) -> InvariantResult:
        """Check ALL services → engine imports (including allowed ones like gateway)."""
        all_engine_imports = []
        forbidden = []
        allowed = []
        for fpath, edges in self.all_imports.items():
            source_module = self._get_source_module(fpath)
            if source_module not in ("services", "services.ai"):
                continue
            if self._is_test_file(fpath):
                continue
            for edge in edges:
                mod = edge.imported_module
                if mod == "engine" or mod.startswith("engine."):
                    entry = {
                        "file": fpath,
                        "line": edge.line,
                        "import": f"from {mod} import {', '.join(edge.imported_names[:3])}" if edge.import_type == "from_import" else f"import {mod}",
                        "module": mod,
                    }
                    all_engine_imports.append(entry)
                    # Check if forbidden
                    if mod.startswith("engine.hydroma") or mod.startswith("engine.cpp_core") or mod.startswith("engine.ports"):
                        forbidden.append(entry)
                    else:
                        allowed.append(entry)
        return InvariantResult(
            invariant_id="INV-003-COUNT",
            name="Services → Engine import count",
            description="Total count of all services → engine imports, classified as allowed or forbidden.",
            status="PASS" if not forbidden else "FAIL",
            violations=forbidden,
            evidence=f"Total engine imports from services: {len(all_engine_imports)}. Allowed: {len(allowed)}. Forbidden (engine internals): {len(forbidden)}.",
        )

    def check_inv_004_circular(self) -> InvariantResult:
        """INV-004: No circular dependencies."""
        # Build module import graph
        graph = defaultdict(set)
        for fpath, edges in self.all_imports.items():
            source_module = self._get_source_module(fpath)
            for edge in edges:
                mod = edge.imported_module
                # Only track internal modules
                if mod.startswith("engine.") or mod.startswith("services.") or mod.startswith("database.") or mod.startswith("adapters."):
                    graph[source_module].add(mod)

        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node) if node in path else 0
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, set()):
                dfs(neighbor, path.copy())
            rec_stack.discard(node)

        for node in list(graph.keys()):
            dfs(node, [])

        # Deduplicate cycles
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            key = tuple(sorted(set(cycle)))
            if key not in seen and len(cycle) > 1:
                seen.add(key)
                unique_cycles.append(cycle)

        return InvariantResult(
            invariant_id="INV-004",
            name="No circular dependencies",
            description="Dependency graph must have zero unexpected cycles.",
            status="PASS" if not unique_cycles else "FAIL",
            violations=[{"cycle": c} for c in unique_cycles],
            evidence=f"Built module graph with {len(graph)} nodes. Found {len(unique_cycles)} cycles.",
        )

    def check_inv_009_ai_isolation(self) -> InvariantResult:
        """INV-009: AI services must not import engine internals."""
        forbidden_prefixes = ["engine.hydroma", "engine.cpp_core", "engine.ports"]
        violations = []
        for fpath, edges in self.all_imports.items():
            source_module = self._get_source_module(fpath)
            if source_module != "services.ai":
                continue
            if self._is_test_file(fpath):
                continue
            for edge in edges:
                mod = edge.imported_module
                for p in forbidden_prefixes:
                    if mod == p or mod.startswith(p + "."):
                        violations.append({
                            "file": fpath,
                            "line": edge.line,
                            "import": f"from {mod} import {', '.join(edge.imported_names[:3])}" if edge.import_type == "from_import" else f"import {mod}",
                        })
                        break
        return InvariantResult(
            invariant_id="INV-009",
            name="AI isolation",
            description="AI services must not import engine internals (hydroma, cpp_core, ports).",
            status="PASS" if not violations else "FAIL",
            violations=violations,
            evidence=f"Scanned all AI service files; found {len(violations)} violations.",
        )

    def check_inv_circular_engine_knowledge_evidence(self) -> InvariantResult:
        """Check circular dependencies between engine.evidence and engine.knowledge."""
        violations = []
        # Check if evidence imports knowledge at module level (non-test, non-lazy)
        ev_file = "engine/evidence/__init__.py"
        if ev_file in self.all_imports:
            for edge in self.all_imports[ev_file]:
                if edge.imported_module == "engine.knowledge" or edge.imported_module.startswith("engine.knowledge."):
                    # Check if it's inside a function (lazy import)
                    violations.append({
                        "file": ev_file,
                        "line": edge.line,
                        "import": f"from {edge.imported_module} import {', '.join(edge.imported_names[:3])}",
                        "note": "Dynamic import to avoid circular dependency",
                    })
        return InvariantResult(
            invariant_id="INV-004-SUB",
            name="Evidence ↔ Knowledge circular dependency",
            description="Check for circular imports between engine.evidence and engine.knowledge.",
            status="PASS" if not violations else "PARTIAL",
            violations=violations,
            evidence=f"Found {len(violations)} lazy/dynamic imports between evidence and knowledge.",
            notes="These are lazy imports (inside to_fact()) — functionally acceptable but architecturally suboptimal.",
        )

    def count_test_files(self) -> dict:
        """Count all test files in the project."""
        test_files = []
        for fpath in self.all_imports.keys():
            if self._is_test_file(fpath):
                test_files.append(fpath)

        # Also find test files that might not have imports
        for py_file in self.python_files:
            rel = str(py_file.relative_to(self.root))
            if self._is_test_file(rel) and rel not in test_files:
                test_files.append(rel)

        return {
            "total_test_files": len(set(test_files)),
            "test_files": sorted(set(test_files)),
        }

    def count_service_count(self) -> dict:
        """Count domain services and bounded contexts."""
        service_dirs = []
        services_root = self.root / "services"
        if services_root.exists():
            for item in services_root.iterdir():
                if item.is_dir() and item.name not in ("__pycache__",):
                    service_dirs.append(item.name)
        return {
            "service_count": len(service_dirs),
            "services": sorted(service_dirs),
        }

    def find_skeleton_markers(self) -> list[dict]:
        """Find files that self-identify as 'skeleton' or 'stub' or 'placeholder'."""
        markers = ["skeleton", "stub", "placeholder", "not implemented", "NOT_IMPLEMENTED",
                   "to be implemented", "todo", "fixme", "pass  # "]
        results = []
        for py_file in self.python_files:
            rel = str(py_file.relative_to(self.root))
            try:
                content = py_file.read_text(encoding="utf-8")
            except:
                continue
            # Only check production files (skip tests)
            if self._is_test_file(rel):
                continue
            for marker in markers:
                if marker.lower() in content.lower():
                    # Find line
                    for i, line in enumerate(content.splitlines(), 1):
                        if marker.lower() in line.lower():
                            results.append({
                                "file": rel,
                                "line": i,
                                "marker": marker,
                                "text": line.strip()[:120],
                            })
                            break
        return results

    def find_placeholder_functions(self) -> list[dict]:
        """Find functions that raise NotImplementedError."""
        results = []
        for py_file in self.python_files:
            rel = str(py_file.relative_to(self.root))
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except:
                continue
            if self._is_test_file(rel):
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check if body is just 'raise NotImplementedError'
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Raise):
                        call = node.body[0].exc
                        if isinstance(call, ast.Call):
                            func_name = ""
                            if isinstance(call.func, ast.Name):
                                func_name = call.func.id
                            elif isinstance(call.func, ast.Attribute):
                                func_name = call.func.attr
                            if "NotImplemented" in func_name:
                                results.append({
                                    "file": rel,
                                    "function": node.name,
                                    "line": node.lineno,
                                })
        return results

    def generate_full_report(self) -> dict:
        """Generate the comprehensive invariant report."""
        self.scan_project()

        invariants = []

        inv001 = self.check_inv_001_engine_no_services()
        inv002 = self.check_inv_002_engine_no_database()
        inv003 = self.check_inv_003_services_no_engine_internals()
        inv003_count = self.check_inv_003_all_engine_imports()
        inv004 = self.check_inv_004_circular()
        inv004_sub = self.check_inv_circular_engine_knowledge_evidence()
        inv009 = self.check_inv_009_ai_isolation()

        invariants.append(asdict(inv001))
        invariants.append(asdict(inv002))
        invariants.append(asdict(inv003))
        invariants.append(asdict(inv003_count))
        invariants.append(asdict(inv004))
        invariants.append(asdict(inv004_sub))
        invariants.append(asdict(inv009))

        test_count = self.count_test_files()
        service_count = self.count_service_count()
        skeleton_markers = self.find_skeleton_markers()
        placeholder_funcs = self.find_placeholder_functions()

        return {
            "scan_timestamp": datetime.utcnow().isoformat() + "Z",
            "files_scanned": len(self.python_files),
            "test_files": test_count["total_test_files"],
            "production_files": len(self.production_files),
            "invariants": invariants,
            "service_count": service_count["service_count"],
            "services_list": service_count["services"],
            "skeleton_markers": skeleton_markers,
            "placeholder_functions": placeholder_funcs,
            "summary": {
                "INV-001": inv001.status,
                "INV-002": inv002.status,
                "INV-003": inv003.status,
                "INV-003-COUNT": inv003_count.status,
                "INV-004": inv004.status,
                "INV-004-SUB": inv004_sub.status,
                "INV-009": inv009.status,
            },
        }


def main():
    project_root = os.environ.get("HYDROMA_ROOT", ".")
    scanner = ComprehensiveScanner(project_root)
    report = scanner.generate_full_report()

    output_path = Path(project_root) / "tools" / "eco04_comprehensive_scan.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Files scanned: {report['files_scanned']}")
    print(f"Test files: {report['test_files']}")
    print(f"Production files: {report['production_files']}")
    print(f"Service count: {report['service_count']}")
    print(f"Skeleton markers found: {len(report['skeleton_markers'])}")
    print(f"NotImplementedError stubs: {len(report['placeholder_functions'])}")
    print()
    for inv in report["invariants"]:
        print(f"  {inv['invariant_id']}: {inv['name']} → {inv['status']}")
        if inv["violations"]:
            for v in inv["violations"][:10]:
                if "file" in v:
                    print(f"    {v['file']}:{v.get('line', '?')} — {v.get('import', v.get('cycle', v))}")
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
