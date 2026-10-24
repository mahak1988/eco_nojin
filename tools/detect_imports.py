#!/usr/bin/env python3
"""
ECO-03.1: Architecture Import Guard

Detects forbidden import dependencies between architectural layers.

Usage:
    python tools/detect_imports.py
    python tools/detect_imports.py --json
    python tools/detect_imports.py --format=json --output=report.json

Rules are defined as data in get_rules().
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _embedded_policy() -> dict[str, Any]:
    """Fallback policy, used only when import_guard_policy.json is absent."""
    return {
        "rules": {
            "SERVICES_NO_ENGINE_INTERNALS": {
                "allowed_imports": [
                    {"module": "engine.hydroma.config.settings"},
                    {"module": "engine.hydroma.config.rules"},
                    {"module": "engine.hydroma.biofertilizer.models"},
                    {"module": "engine.hydroma.core.models"},
                    {"module": "engine.hydroma.carbon.calculator"},
                    {"module": "engine.hydroma.cpp_bridge"},
                ],
                "facade_files": [
                    {"path": "services/_gateway_facade.py"},
                    {"path": "services/api_gateway/routers/hydroma_common.py"},
                ],
            }
        }
    }


_POLICY_CACHE: dict[str, Any] | None = None


def load_import_policy() -> dict[str, Any]:
    """Load the import-guard exception policy from tools/import_guard_policy.json.

    The policy is data, not code: every sanctioned exception carries a
    rationale and is documented in ADR-014. Falls back to the embedded
    defaults when the file is missing or malformed, so the guard never
    fails to run because of a policy-file problem.
    """
    global _POLICY_CACHE
    if _POLICY_CACHE is None:
        policy_path = Path(__file__).resolve().parent / "import_guard_policy.json"
        try:
            _POLICY_CACHE = json.loads(policy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _POLICY_CACHE = _embedded_policy()
    return _POLICY_CACHE


def _policy_exception_modules() -> list[str]:
    """Sanctioned direct-import modules for SERVICES_NO_ENGINE_INTERNALS."""
    rule = load_import_policy()["rules"]["SERVICES_NO_ENGINE_INTERNALS"]
    return [entry["module"] for entry in rule["allowed_imports"]]


def _policy_facade_files() -> set[str]:
    """Service files whitelisted to import engine internals (the bridge)."""
    rule = load_import_policy()["rules"]["SERVICES_NO_ENGINE_INTERNALS"]
    return {entry["path"] for entry in rule["facade_files"]}


@dataclass
class Rule:
    id: str
    name: str
    description: str
    source_module: str
    forbidden_prefixes: list[str]
    mode: str  # FORBIDDEN_ALL, FORBIDDEN_PRODUCTION, WARNING
    rationale: str
    allowed_imports: list[str] = field(default_factory=list)


@dataclass
class Violation:
    rule_id: str
    rule_name: str
    file: str
    line: int
    column: int
    import_statement: str
    import_type: str
    severity: str
    module: str | None = None
    names: list[str] | None = None


@dataclass
class AuditResult:
    rules: list[Rule] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
    files_scanned: int = 0
    directories_scanned: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "PASS" if not self.violations else "FAIL",
            "files_scanned": self.files_scanned,
            "directories_scanned": self.directories_scanned,
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "source_module": r.source_module,
                    "forbidden_prefixes": r.forbidden_prefixes,
                    "allowed_imports": r.allowed_imports,
                    "mode": r.mode,
                    "rationale": r.rationale,
                }
                for r in self.rules
            ],
            "violations": [
                {
                    "rule": v.rule_id,
                    "rule_name": v.rule_name,
                    "file": v.file,
                    "line": v.line,
                    "column": v.column,
                    "import": v.import_statement,
                    "import_type": v.import_type,
                    "severity": v.severity,
                    "module": v.module,
                    "names": v.names,
                }
                for v in self.violations
            ],
        }


def get_rules() -> list[Rule]:
    """Architecture rules defined as data."""
    return [
        Rule(
            id="ENGINE_NO_SERVICES",
            name="Engine must not import from services",
            description="Scientific engine must not depend on services layer.",
            source_module="engine",
            forbidden_prefixes=["services"],
            mode="FORBIDDEN_PRODUCTION",
            rationale="INV-016: Engine may not import from services.",
        ),
        Rule(
            id="ENGINE_NO_DATABASE",
            name="Engine must not import from database",
            description="Engine must not depend directly on database layer.",
            source_module="engine",
            forbidden_prefixes=["database"],
            mode="FORBIDDEN_PRODUCTION",
            rationale=(
                "INV-002: Engine never depends on database. "
                "Exceptions: database.config (the session factory / "
                "engine binding) and database.base (the shared "
                "declarative Base registry). Both are the sanctioned "
                "persistence bridge — the production PersistencePort "
                "adapter imports the same session factory and Base, so "
                "reaching them directly is equivalent to the port "
                "contract and is not a computation dependency."
            ),
            allowed_imports=["database.config", "database.base"],
        ),
        Rule(
            id="ENGINE_NO_FRONTEND",
            name="Engine must not import from frontend",
            description="Engine is backend-only.",
            source_module="engine",
            forbidden_prefixes=["frontend", "ui", "dashboard", "web"],
            mode="FORBIDDEN_ALL",
            rationale="INV-003: Engine never depends on frontend.",
        ),
        Rule(
            id="ENGINE_NO_AUTH",
            name="Engine must not import from auth",
            description="Auth concerns belong in services layer.",
            source_module="engine",
            forbidden_prefixes=["auth", "authentication"],
            mode="FORBIDDEN_ALL",
            rationale="Security boundaries enforced at gateway.",
        ),
        Rule(
            id="ENGINE_NO_PAYMENT",
            name="Engine must not import from payment",
            description="Payment must not leak into engine.",
            source_module="engine",
            forbidden_prefixes=["payment", "stripe", "paypal"],
            mode="FORBIDDEN_ALL",
            rationale="Financial concerns belong in services.",
        ),
        Rule(
            id="ENGINE_NO_BLOCKCHAIN",
            name="Engine must not import from blockchain",
            description="Blockchain must not be in engine.",
            source_module="engine",
            forbidden_prefixes=["blockchain", "smart_contract", "web3", "ethereum"],
            mode="FORBIDDEN_ALL",
            rationale="Blockchain is a services-layer concern.",
        ),
        Rule(
            id="AI_NO_ENGINE_INTERNALS",
            name="AI services must not import engine internals",
            description="AI layer must not import deep engine implementation internals.",
            source_module="services.ai",
            forbidden_prefixes=["engine.hydroma", "engine.cpp_core", "engine.ports"],
            mode="FORBIDDEN_ALL",
            rationale="AI isolation: AI interprets results but must not influence computation.",
        ),
        Rule(
            id="SERVICES_NO_ENGINE_INTERNALS",
            name="Services must not import engine internals directly",
            description="All access to scientific computation must go through the Engine Gateway.",
            source_module="services",
            forbidden_prefixes=["engine.hydroma", "engine.cpp_core", "engine.ports"],
            allowed_imports=_policy_exception_modules(),
            mode="FORBIDDEN_ALL",
            rationale="INV-003: Services must use EngineGateway, not direct engine internals.",
        ),
    ]


def is_test_file(file_path: str) -> bool:
    """Check if file is a test file."""
    path = Path(file_path)
    parts = path.parts
    return (
        "test" in path.name.lower()
        or "tests" in parts
        or "conftest" in path.name
    )


def get_source_module(file_path: str) -> str | None:
    """Determine which architectural module a file belongs to."""
    path = Path(file_path)
    parts = path.parts

    if parts[0] == "engine":
        return "engine"
    elif parts[0] == "services":
        if "ai" in parts[1:3]:
            return "services.ai"
        return "services"
    return None


def check_module_against_rule(module: str, forbidden_prefixes: list[str]) -> str | None:
    """Check if a module import matches any forbidden prefix."""
    for prefix in forbidden_prefixes:
        if module == prefix or module.startswith(prefix + "."):
            return prefix
    return None


class ImportScanner(ast.NodeVisitor):
    """AST visitor that collects import statements and their context."""

    def __init__(self, rules: list[Rule], file_path: str, is_test: bool):
        self.rules = rules
        self.rel_path = file_path
        self.is_test = is_test
        self.violations: list[Violation] = []
        self.depth = 0
        self.type_checking = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    def visit_If(self, node: ast.If) -> None:
        old_tc = self.type_checking
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            self.type_checking = True
        self.generic_visit(node)
        self.type_checking = old_tc

    def _check_import(
        self,
        module: str,
        names: list[str],
        line: int,
        col: int,
        import_type: str,
        is_relative: bool = False,
    ) -> None:
        if self.is_test:
            return
        if self.type_checking:
            return
        # Relative imports (from .services) are local to the package
        if is_relative:
            return

        source_module = get_source_module(self.rel_path)
        if source_module is None:
            return

        for rule in self.rules:
            if source_module != rule.source_module and not source_module.startswith(rule.source_module + "."):
                continue

            forbidden = check_module_against_rule(module, rule.forbidden_prefixes)
            if forbidden:
                # Check allowlist - some modules are public interfaces
                # that services can access directly (e.g., config/settings)
                if module in rule.allowed_imports or any(
                    module.startswith(allowed + ".") for allowed in rule.allowed_imports
                ):
                    pass  # Allowed import, skip violation
                else:
                    is_lazy = self.depth > 0
                    severity = "WARNING" if rule.mode == "FORBIDDEN_PRODUCTION" and is_lazy else "ERROR"
                    stmt = f"from {module} import {', '.join(names[:3])}" if import_type == "from_import" else f"import {module}"
                    self.violations.append(Violation(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        file=self.rel_path,
                        line=line,
                        column=col,
                        import_statement=stmt,
                        import_type=import_type,
                        severity=severity,
                        module=module,
                        names=names,
                    ))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(
                module=alias.name,
                names=[alias.asname or alias.name],
                line=node.lineno,
                col=node.col_offset,
                import_type="import",
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        names = [n.name for n in node.names]
        is_relative = node.level > 0
        self._check_import(
            module=module,
            names=names,
            line=node.lineno,
            col=node.col_offset,
            import_type="from_import",
            is_relative=is_relative,
        )
        self.generic_visit(node)


def analyze_file(
    file_path: Path,
    rules: list[Rule],
    project_root: Path,
) -> list[Violation]:
    """Analyze a single Python file for import violations."""
    rel_path = str(file_path.relative_to(project_root))

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    is_test = is_test_file(rel_path)
    scanner = ImportScanner(rules, rel_path, is_test)
    scanner.visit(tree)
    return scanner.violations


def scan_project(project_root: Path) -> AuditResult:
    """Scan entire project for import violations."""
    rules = get_rules()
    result = AuditResult(rules=rules)

    exclude_dirs = {
        "__pycache__", ".venv", "venv", "node_modules",
        "build", "dist", ".eggs",
    }

    directories_scanned = set()
    python_files = list(project_root.rglob("*.py"))

    for py_file in python_files:
        rel = py_file.relative_to(project_root)
        parts = rel.parts

        if any(p in exclude_dirs for p in parts):
            continue
        
        # Whitelist the sanctioned bridge files. The list is policy data
        # (tools/import_guard_policy.json, documented in ADR-014), not
        # hard-coded here, so each exception is reviewable and versioned.
        if rel.as_posix() in _policy_facade_files():
            continue

        directories_scanned.add(str(rel.parent))
        result.files_scanned += 1
        violations = analyze_file(py_file, rules, project_root)
        result.violations.extend(violations)

    result.directories_scanned = sorted(directories_scanned)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ECO-03.1 Architecture Import Guard")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    result = scan_project(project_root)

    if args.json or args.format == "json":
        output = json.dumps(result.to_dict(), indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        print(output)
    else:
        print("Architecture Import Guard Report")
        print("=" * 60)
        print(f"Files scanned: {result.files_scanned}")
        print(f"Directories scanned: {len(result.directories_scanned)}")
        print(f"Rules checked: {len(result.rules)}")
        print(f"Violations found: {len(result.violations)}")
        print("=" * 60)

        if not result.violations:
            print("Status: PASS — No violations found")
        else:
            print("Status: FAIL — Violations found\n")
            for v in result.violations:
                print(f"[{v.severity}] {v.rule_id}: {v.file}:{v.line}")
                print(f"  Import: {v.import_statement}")
                print(f"  Rule: {v.rule_name}")
                print()

    return 0 if not result.violations else 1


if __name__ == "__main__":
    sys.exit(main())
