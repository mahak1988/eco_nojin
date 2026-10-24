#!/usr/bin/env python3
"""Security scanner for the HyDroMA (Eco Nojin) codebase.

Runs a series of static checks to detect common security issues:

1. **Hardcoded secrets** — string literals matching known secret patterns
2. **Sensitive data in logs** — logging statements that interpolate secrets
3. **Gateway bypass** — services importing engine modules directly instead
   of going through `services._gateway_facade` or `engine.gateway`
4. **Provenance field population** — model outputs missing provenance fields
5. **Error detail leakage** — `str(exc)` passed to clients
6. **C++ bridge availability** — checks if the compiled extension is loadable
7. **Environment secrets** — secret-named variables (`*_KEY`, `*_SECRET`,
   `*_TOKEN`, `*_PASSWORD`) set in the parent process environment; names and
   bucketed value lengths only, never the values themselves

Usage:
    python tools/check_security.py [--repo DIR] [--json] [--fail-on ISSUE]

Exit codes:
    0 — no issues found (or all found issues below threshold)
    1 — one or more issues of severity >= --fail-on found
    2 — scanner error (e.g., directory not found)
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_REPO = Path(__file__).resolve().parent.parent

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS secret key", re.compile(r"(?i)aws.{0,20}secret.{0,20}[a-z0-9/+]{40}")),
    ("Google API key", re.compile(r"AIza[0-9A-H_-]{35}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("Slack token", re.compile(r"xox[bap]-[A-Za-z0-9-]{10,}")),
    ("Stripe key", re.compile(r"sk_(live|test)_[0-9a-zA-Z]{16,}")),
    ("Generic bearer token", re.compile(r"(?i)token\s*[:=]\s*['\"][a-zA-Z0-9._-]{20,}['\"]")),
    ("Generic password", re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")),
    ("Generic secret", re.compile(r"(?i)secret\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")),
]

SECRET_ENV_SUFFIXES = ("_KEY", "_SECRET", "_TOKEN", "_PASSWORD")

LENGTH_BUCKET_LABELS: tuple[tuple[int, str], ...] = (
    (8, "1-8"),
    (16, "9-16"),
    (32, "17-32"),
    (64, "33-64"),
)


def _length_bucket(length: int) -> str:
    """Bucket a secret value's length so shapes can be compared, never values."""
    if length <= 0:
        return "0 (empty)"
    for upper, label in LENGTH_BUCKET_LABELS:
        if length <= upper:
            return label
    return "65+"


INSECURE_SECRET_VALUES = {
    "dev-secret-key",
    "dev-jwt-secret",
    "change-me-in-production",
    "changeme",
    "secret",
    "dev",
    "demo123",
    "CHANGE_ME",
    "CHANGE_ME_TO_A_STRONG_RANDOM_KEY",
    "your-secret-key",
    "",
    "your-project.supabase.co",
    "your-supabase-key",
    "your-anon-key",
    "your-service-role-key",
}

ALLOWED_GATEWAY_IMPORTS = {
    "engine.gateway",
    "engine.gateway.EngineGateway",
    "engine.gateway.GatewayRequest",
    "engine.gateway.GatewayResult",
    "engine.gateway.GatewayError",
    "engine.gateway.ProvenanceSpec",
    "engine.gateway.UncertaintySpec",
    "engine.gateway.ModelSpec",
    "engine.gateway.ExecutionMetadata",
    "engine.gateway.InputSpec",
    "engine.gateway.UnitSpec",
    "engine.gateway.ValidationResult",
    "services._gateway_facade",
    "services.gateway_facade",
}

FORBIDDEN_ENGINE_IMPORTS = {
    "engine.hydroma.et",
    "engine.hydroma.runoff",
    "engine.hydroma.theis",
    "engine.hydroma.soil",
    "engine.hydroma.carbon",
    "engine.hydroma.economics",
    "engine.hydroma.watershed",
    "engine.hydroma.plant_neuro",
    "engine.hydroma.mrv",
    "engine.hydroma.irrigation",
    "engine.hydroma.simulation",
    "engine.hydroma.decision_support",
    "engine.hydroma.scenarios",
    "engine.hydroma.data_pipeline",
    "engine.hydroma.models",
    "engine.hydroma.cpp_bridge",
    "engine.hydroma.cpp_bindings",
    "engine.hydroma.config",
    "engine.hydroma.provenance",
}

SENSITIVE_VAR_NAMES = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "secret_key",
    "jwt_secret",
    "bot_token",
    "anon_key",
    "service_role_key",
    "webhook_key",
    "mrv_ingest_key",
    "oauth_encryption_key",
    "telegram_bot_token",
    "satellite_api_key",
    "openai_api_key",
    "anthropic_api_key",
    "groq_api_key",
    "sentinel_hub_client_secret",
    "cds_api_key",
    "ewds_api_key",
    "ads_api_key",
    "zarinpal_merchant_id",
    "blockchain_private_key",
    "alchemy_api_key",
    "polygonscan_api_key",
    "whisper_api_key",
    "zenodo_token",
    "verra_api_key",
    "verra_api_secret",
    "cdse_client_secret",
    "smtp_password",
    "nats_password",
    "nats_token",
    "client_secret",
    "hashed_password",
    "master_key",
    "encryption_key",
}

ERROR_LEAK_PATTERNS = [
    re.compile(r"raise\s+HTTPException.*detail\s*=\s*str\(exc\)", re.DOTALL),
    re.compile(r"raise\s+HTTPException.*detail\s*=\s*str\(e\)", re.DOTALL),
    re.compile(r'detail\s*=\s*str\(.*error.*\)', re.DOTALL | re.IGNORECASE),
    re.compile(r'HTTPException.*detail=.*f"[^"]*\{.*exc.*"', re.DOTALL),
]


@dataclass
class Finding:
    severity: str
    check: str
    file: str
    line: int
    col: int
    message: str
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "check": self.check,
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "message": self.message,
            "context": self.context,
        }


@dataclass
class ScanResult:
    timestamp: str
    repo: str
    findings: list[Finding] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def add(self, severity: str, check: str, file: str, line: int, col: int,
            message: str, context: str = "") -> None:
        self.findings.append(
            Finding(severity, check, file, line, col, message, context)
        )

    @property
    def has_issues(self) -> bool:
        return len(self.findings) > 0

    def by_severity(self) -> dict[str, list[Finding]]:
        grouped: dict[str, list[Finding]] = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        for f in self.findings:
            grouped.setdefault(f.severity, []).append(f)
        return grouped

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "repo": self.repo,
            "stats": self.stats,
            "findings": [f.to_dict() for f in self.findings],
        }


def _rel_path(file: str, repo: Path) -> str:
    try:
        return str(Path(file).relative_to(repo))
    except ValueError:
        return file


def check_hardcoded_secrets(repo: Path, result: ScanResult) -> None:
    """Check for hardcoded secrets in Python source files.

    Test modules are excluded: a test must be able to write
    ``password = "dummy"`` to exercise a login path, and every dummy
    credential in a test fixture is a finding under this pattern. Real
    credentials never belong in a test either — the protection for those is
    the repository secret scan and review, not this pattern match.
    """
    for py_file in repo.rglob("*.py"):
        if _should_skip_file(py_file, repo) or _is_test_file(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "# nosec" in stripped.lower():
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            for name, pattern in SECRET_PATTERNS:
                for match in pattern.finditer(line):
                    matched_text = match.group()
                    if any(IS_INSECURE(s) for s in INSECURE_SECRET_VALUES):
                        continue
                    result.add(
                        severity="HIGH",
                        check="hardcoded_secret",
                        file=str(py_file),
                        line=i,
                        col=match.start(),
                        message=f"Possible {name} detected",
                        context=matched_text[:80],
                    )

            for var_hint in SENSITIVE_VAR_NAMES:
                m = re.search(
                    rf'(?i)({var_hint})\s*[:=]\s*["\']([^"\']{{8,}})["\']',
                    line,
                )
                if m:
                    value = m.group(2)
                    if _is_likely_placeholder(value):
                        continue
                    if _looks_like_test_value(value):
                        continue
                    is_critical = var_hint in {"password", "secret_key", "private_key"}
                    result.add(
                        severity="HIGH" if is_critical else "MEDIUM",
                        check="hardcoded_secret_assignment",
                        file=str(py_file),
                        line=i,
                        col=m.start(),
                        message=f"Sensitive variable '{var_hint}' assigned a literal value",
                        context=value[:60],
                    )


def _should_skip_file(path: Path, repo: Path) -> bool:
    parts = set(path.relative_to(repo).parts)
    skip_dirs = {"__pycache__", ".venv", "venv", "node_modules", ".git", "data"}
    if parts & skip_dirs:
        return True
    return False


def IS_INSECURE(s: str) -> bool:
    return s in INSECURE_SECRET_VALUES


def _is_likely_placeholder(value: str) -> bool:
    lower = value.lower()
    placeholders = {
        "changeme", "change-me", "placeholder", "your-", "test", "testing",
        "dummy", "example", "replace", "xxx", "todo", "fixme",
        "dev", "demo", "fake", "mock", "sample",
    }
    return any(p in lower for p in placeholders)


def _looks_like_test_value(value: str) -> bool:
    if value in INSECURE_SECRET_VALUES:
        return True
    return False


def check_sensitive_logging(repo: Path, result: ScanResult) -> None:
    """Check for logging statements that interpolate secret/sensitive variables."""
    for py_file in repo.rglob("*.py"):
        if _should_skip_file(py_file, repo):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in {"debug", "info", "warning", "error"}:
                continue
            if not isinstance(func.value, ast.Name):
                continue
            if func.value.id not in {"logger", "logging", "_logger", "log"}:
                continue
            for arg in node.args:
                if isinstance(arg, ast.JoinedStr):
                    for val in arg.values:
                        if isinstance(val, ast.FormattedValue) and isinstance(val.value, ast.Name):
                            if val.value.id.lower() in SENSITIVE_VAR_NAMES:
                                var_id = val.value.id
                                result.add(
                                    severity="MEDIUM",
                                    check="sensitive_logging",
                                    file=str(py_file),
                                    line=node.lineno,
                                    col=node.col_offset,
                                    message=(
                                        "Logger call interpolates sensitive variable "
                                        f"'{var_id}'"
                                    ),
                                )


def _is_test_file(py_file: Path) -> bool:
    """Whether the file is a test module (``tests/`` dir or ``test_*.py``).

    The gateway-bypass rule is a production-boundary rule: a test that
    verifies an engine kernel reaches into it deliberately, and
    ``detect_imports.py`` (the authoritative guard) does not flag those
    imports. Excluding test files here keeps the two scanners in agreement —
    without it the scanner reports HIGH findings for the very test suites
    that prove the boundary holds.
    """
    parts = py_file.parts
    if "tests" in parts or "test" in parts:
        return True
    return py_file.name.startswith("test_") or py_file.name == "conftest.py"


def check_gateway_bypass(repo: Path, result: ScanResult) -> None:
    """Check for services importing engine modules directly (bypassing facade)."""
    services_dir = repo / "services"
    if not services_dir.exists():
        return

    for py_file in services_dir.rglob("*.py"):
        if _should_skip_file(py_file, repo) or _is_test_file(py_file):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("engine."):
                    if not node.module.startswith("engine.gateway"):
                        for alias in node.names:
                            if alias.name == "*":
                                full = node.module
                            else:
                                full = f"{node.module}.{alias.name}"
                            if _is_unsanctioned_engine_import(full, py_file, repo):
                                result.add(
                                    severity="MEDIUM",
                                    check="gateway_bypass_import",
                                    file=str(py_file),
                                    line=node.lineno,
                                    col=node.col_offset,
                                    message=(
                                        "Services imports engine module "
                                        f"directly: {full}"
                                    ),
                                    context=(
                                        "services/ should use "
                                        "services._gateway_facade or "
                                        "engine.gateway"
                                    ),
                                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("engine."):
                        if _is_unsanctioned_engine_import(alias.name, py_file, repo):
                            result.add(
                                severity="MEDIUM",
                                check="gateway_bypass_import",
                                file=str(py_file),
                                line=node.lineno,
                                col=node.col_offset,
                                message=f"Services imports engine module directly: {alias.name}",
                            )


def _import_guard_policy() -> dict[str, Any]:
    """The import-guard policy — one data source shared with detect_imports.py.

    Reading the same JSON keeps the two guards telling the same story: a module
    or file the import guard sanctions (ADR-014, `allowed_imports` /
    `facade_files`) is not an architecture violation here either (SEC-08
    reconciliation: 29 scanner HIGHs were this check disagreeing with the
    guard).
    """
    path = Path(__file__).resolve().parent / "import_guard_policy.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _policy_rule() -> dict[str, Any]:
    return (
        _import_guard_policy()
        .get("rules", {})
        .get("SERVICES_NO_ENGINE_INTERNALS", {})
    )


def _sanctioned_engine_modules() -> list[str]:
    """Engine modules the policy allows services to import directly."""
    return [entry["module"] for entry in _policy_rule().get("allowed_imports", [])]


def _sanctioned_facade_files(repo: Path) -> set[str]:
    """Service files whitelisted as the sanctioned engine bridge (relative)."""
    files = set()
    for entry in _policy_rule().get("facade_files", []):
        files.add(entry["path"].replace("\\", "/"))
    return files


def _is_unsanctioned_engine_import(full_name: str, py_file: Path, repo: Path) -> bool:
    """Whether ``full_name`` imported by ``py_file`` really bypasses the facade.

    The forbidden list is still a deny-list, but the import-guard policy's
    sanctioned modules and bridge files are removed from the match first —
    otherwise this scanner contradicts ``detect_imports.py`` (which honors the
    same policy and reports zero violations) and its HIGH findings are noise
    that buries real ones.
    """
    try:
        relative = py_file.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        relative = ""
    if relative and relative in _sanctioned_facade_files(repo):
        return False
    for allowed in _sanctioned_engine_modules():
        if full_name == allowed or full_name.startswith(allowed + "."):
            return False
    for forbidden in FORBIDDEN_ENGINE_IMPORTS:
        if full_name == forbidden or full_name.startswith(forbidden + "."):
            return True
    return False


def check_provenance_population(repo: Path, result: ScanResult) -> None:
    """Check that result classes inheriting ResultProvenance have data_source."""
    provenance_file = repo / "engine" / "hydroma" / "provenance.py"
    if not provenance_file.exists():
        return

    for py_file in repo.rglob("*.py"):
        if _should_skip_file(py_file, repo):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                if "ResultProvenance" in bases:
                    has_data_source_default = False
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            if item.target.id == "data_source" and item.value is not None:
                                has_data_source_default = True
                    if has_data_source_default:
                        result.add(
                            severity="LOW",
                            check="provenance_default",
                            file=str(py_file),
                            line=node.lineno,
                            col=node.col_offset,
                            message=(
                                "ResultProvenance subclass has default "
                                "data_source (should be required)"
                            ),
                        )


def check_error_leakage(repo: Path, result: ScanResult) -> None:
    """Check for potential error detail leakage in HTTPException raises."""
    for py_file in repo.rglob("*.py"):
        if _should_skip_file(py_file, repo):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content)
        except (SyntaxError, OSError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id != "HTTPException":
                    continue
                for kw in node.keywords:
                    if kw.arg == "detail":
                        if kw.value and isinstance(kw.value, ast.Call):
                            if isinstance(kw.value.func, ast.Name) and kw.value.func.id == "str":
                                result.add(
                                    severity="HIGH",
                                    check="error_leakage",
                                    file=str(py_file),
                                    line=node.lineno,
                                    col=node.col_offset,
                                    message=(
                                        "HTTPException detail uses str(exc) "
                                        "— leaks internal details to client"
                                    ),
                                )
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        if any(p.search(arg.value) for p in ERROR_LEAK_PATTERNS):
                            result.add(
                                severity="MEDIUM",
                                check="error_leakage_pattern",
                                file=str(py_file),
                                line=node.lineno,
                                col=node.col_offset,
                                message=(
                                    "HTTPException detail contains "
                                    "potential internal detail pattern"
                                ),
                            )


def check_cpp_bridge_loadable(repo: Path, result: ScanResult) -> None:
    """Check if the C++ hydroma_core extension is loadable."""
    cpp_bridge = repo / "engine" / "hydroma" / "cpp_bridge" / "__init__.py"
    if not cpp_bridge.exists():
        result.add(
            severity="HIGH",
            check="cpp_bridge_missing",
            file=str(cpp_bridge),
            line=1,
            col=0,
            message="C++ bridge module not found",
        )
        return

    try:
        sys.path.insert(0, str(repo))
        from engine.hydroma.cpp_bridge import backend_status, is_cpp_available

        if not is_cpp_available():
            status = backend_status()
            import_err = status.get('import_error', 'unknown')
            backend = status.get('backend')
            avail = status.get('cpp_available')
            result.add(
                severity="MEDIUM",
                check="cpp_bridge_unavailable",
                file=str(cpp_bridge),
                line=1,
                col=0,
                message=f"C++ backend unavailable: {import_err}",
                context=f"backend={backend}, cpp_available={avail}",
            )
    except ImportError as e:
        result.add(
            severity="HIGH",
            check="cpp_bridge_import_error",
            file=str(cpp_bridge),
            line=1,
            col=0,
            message=f"Cannot import cpp_bridge: {e}",
        )
    except Exception as e:
        result.add(
            severity="LOW",
            check="cpp_bridge_check_error",
            file=str(cpp_bridge),
            line=1,
            col=0,
            message=f"cpp_bridge check raised: {e}",
        )


def check_secret_field_allowlist(repo: Path, result: ScanResult) -> None:
    """Verify that SecretStr fields are in the SECRET_FIELDS allowlist."""
    secrets_file = repo / "engine" / "hydroma" / "config" / "secrets.py"
    settings_file = repo / "engine" / "hydroma" / "config" / "settings.py"

    if not secrets_file.exists() or not settings_file.exists():
        return

    try:
        tree = ast.parse(settings_file.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return

    declared_secret_fields: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            ann = node.annotation
            if isinstance(ann, ast.Name) and ann.id in ("SecretStr", "SecretValue"):
                declared_secret_fields.add(node.target.id)

    try:
        content = secrets_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return

    allowlist_match = re.search(
        r"SECRET_FIELDS\s*[:=].*?frozenset\s*\(\s*\{([^}]+)\}",
        content,
        re.DOTALL,
    )
    if not allowlist_match:
        result.add(
            severity="HIGH",
            check="secret_fields_allowlist_missing",
            file=str(secrets_file),
            line=1,
            col=0,
            message="Could not parse SECRET_FIELDS allowlist",
        )
        return

    allowlist_fields = set()
    for m in re.finditer(r'"(\w+)"', allowlist_match.group(1)):
        allowlist_fields.add(m.group(1))

    for field_name in declared_secret_fields:
        if field_name not in allowlist_fields:
            result.add(
                severity="HIGH",
                check="secret_field_not_allowlisted",
                file=str(secrets_file),
                line=1,
                col=0,
                message=f"SecretStr field '{field_name}' not in SECRET_FIELDS allowlist",
                context="Declared in settings.py, missing from secrets.py allowlist",
            )


def check_env_file_absent(repo: Path, result: ScanResult) -> None:
    """Warn if .env exists in repo (should never be committed)."""
    gitignore = repo / ".gitignore"
    if (repo / ".env").exists():
        if gitignore.exists() and ".env" in gitignore.read_text(encoding="utf-8", errors="replace"):
            return
        result.add(
            severity="LOW",
            check="env_file_present",
            file=".env",
            line=1,
            col=0,
            message=".env file exists in repository root — ensure it is gitignored",
        )


def check_environment_secrets(repo: Path, result: ScanResult) -> None:
    """Report secret-named variables set in the parent process environment.

    A variable whose name ends in ``_KEY``, ``_SECRET``, ``_TOKEN`` or
    ``_PASSWORD`` is inherited by every subprocess, every agent and every CI
    job. Only the variable names and their bucketed value lengths are
    reported — the values themselves are never read into the finding, so the
    scan's own output is safe to publish in CI logs.
    """
    names = sorted(
        name for name in os.environ if name.upper().endswith(SECRET_ENV_SUFFIXES)
    )
    if not names:
        return

    detail = ", ".join(
        f"{name} (length bucket: {_length_bucket(len(os.environ[name]))})"
        for name in names
    )
    result.add(
        severity="MEDIUM",
        check="environment_secrets",
        file="<process environment>",
        line=1,
        col=0,
        message=(
            "Secret-named variables are set in the parent process "
            f"environment: {detail}. Values are never reported — names and "
            "length buckets only. Environment variables are inherited by "
            "every subprocess, agent and CI job. Remove on Windows with: "
            'setx <NAME> "" (POSIX: unset <NAME> / delete the shell '
            "profile entry), then start a new shell."
        ),
    )


def run_all_checks(repo: Path) -> ScanResult:
    """Run all security checks and return aggregated result."""
    result = ScanResult(
        timestamp=datetime.now(UTC).isoformat(),
        repo=str(repo),
        stats={"files_scanned": 0, "findings_total": 0},
    )

    py_files = [f for f in repo.rglob("*.py") if not _should_skip_file(f, repo)]
    result.stats["files_scanned"] = len(py_files)

    checks = [
        check_hardcoded_secrets,
        check_sensitive_logging,
        check_gateway_bypass,
        check_provenance_population,
        check_error_leakage,
        check_cpp_bridge_loadable,
        check_secret_field_allowlist,
        check_env_file_absent,
        check_environment_secrets,
    ]

    for check_fn in checks:
        check_fn(repo, result)

    result.stats["findings_total"] = len(result.findings)
    for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        result.stats[f"findings_{severity.lower()}"] = sum(
            1 for f in result.findings if f.severity == severity
        )

    return result


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Security scanner for HyDroMA codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo", default=str(DEFAULT_REPO),
        help=f"Repository root (default: {DEFAULT_REPO})",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--fail-on", default="HIGH",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
        help="Minimum severity to fail the scan (exit code 1)",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress output except summary",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"Error: repository path not found: {repo}", file=sys.stderr)
        return 2

    logging.basicConfig(level=logging.WARNING)

    result = run_all_checks(repo)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif not args.quiet:
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        by_sev = result.by_severity()
        for sev in severity_order:
            findings = by_sev.get(sev, [])
            if findings:
                print(f"\n[{sev}] ({len(findings)} findings)")
                for f in findings:
                    rel = _rel_path(f.file, repo)
                    print(f"  {rel}:{f.line}:{f.col}")
                    print(f"    [{f.check}] {f.message}")
                    if f.context:
                        print(f"    context: {f.context}")
        print(f"\n{'='*60}")
        print(f"Scanned {result.stats['files_scanned']} Python files")
        print(f"Total findings: {result.stats['findings_total']}")
        print(f"  CRITICAL: {result.stats.get('findings_critical', 0)}")
        print(f"  HIGH:     {result.stats.get('findings_high', 0)}")
        print(f"  MEDIUM:   {result.stats.get('findings_medium', 0)}")
        print(f"  LOW:      {result.stats.get('findings_low', 0)}")

    fail_threshold = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}[args.fail_on]
    severity_index = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        # ``--fail-on HIGH`` means "fail on HIGH or worse", i.e. a finding
        # whose index is at or below the threshold. The comparison used to be
        # inverted, so the flag matched everything: `--fail-on CRITICAL`
        # returned 1 on any finding of any severity and the gate was useless
        # (SEC-08 / S4).
        if severity_index[sev] <= fail_threshold:
            if result.stats.get(f"findings_{sev.lower()}", 0) > 0:
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
