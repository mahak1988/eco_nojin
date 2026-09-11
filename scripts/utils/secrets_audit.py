#!/usr/bin/env python3
"""Secrets audit utility - scans for hardcoded secrets in the codebase.

Run this before committing to ensure no secrets are leaked.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Patterns that indicate potential secrets
SECRET_PATTERNS = [
    # API keys and tokens
    (r'(?i)(api[_-]?key|apikey|api_secret|token|secret|password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret"),
    # Connection strings with credentials
    (r'(?i)(postgresql|mysql|mongodb|redis)://[^:]+:[^@]+@', "Database credentials in URL"),
    # JWT secrets
    (r'(?i)jwt[_-]?secret\s*[=:]\s*["\'][^"\']{8,}["\']', "JWT secret"),
    # Private keys
    (r'(?i)(private[_-]?key|privatekey)\s*[=:]\s*["\'][^"\']+["\']', "Private key"),
    # OAuth tokens
    (r'(?i)(oauth|bearer|auth)\s*token\s*[=:]\s*["\'][^"\']{8,}["\']', "OAuth token"),
    # AWS keys
    (r'(?i)(aws_access_key|aws_secret|aws_session_token)\s*[=:]\s*["\'][^"\']+["\']', "AWS credential"),
    # Generic base64-like long strings (potential keys)
    (r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']', "Potential base64 secret"),
]

# Files to skip
SKIP_FILES = {
    ".env.example",
    ".env.template",
    ".gitignore",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.json",
    "*.md",
    "*.txt",
    "*.bak",
    "*.security.bak",
}

# Directories to skip
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    ".pytest_cache",
    ".tox",
    ".nox",
    "engine/cpp_core/build",
    "backups",
    "data/maps",
    "data/motors/cache",
}


def should_skip(path: Path) -> bool:
    """Check if file should be skipped."""
    for skip_dir in SKIP_DIRS:
        if skip_dir in str(path):
            return True
    for skip_file in SKIP_FILES:
        if path.name == skip_file or path.match(skip_file):
            return True
    return False


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Scan a file for secrets. Returns list of (line, pattern_name, line_content)."""
    findings = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pattern, desc in SECRET_PATTERNS:
                if re.search(pattern, line):
                    findings.append((line_num, desc, line.strip()))
    except Exception:
        pass
    return findings


def main() -> int:
    print("🔍 Scanning for secrets in codebase...")
    findings = []

    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_skip(py_file):
            continue
        file_findings = scan_file(py_file)
        if file_findings:
            findings.append((py_file, file_findings))

    if findings:
        print(f"\n❌ Found {len(findings)} files with potential secrets:\n")
        for path, file_findings in findings:
            rel_path = path.relative_to(PROJECT_ROOT)
            for line_num, desc, line in file_findings:
                print(f"  {rel_path}:{line_num} - {desc}")
                print(f"    {line[:120]}")
        print("\n⚠️  Remove these secrets before committing!")
        return 1

    print("✅ No secrets found in codebase.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
