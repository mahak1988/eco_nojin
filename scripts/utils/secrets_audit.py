#!/usr/bin/env python3
"""Secrets audit utility — scans all text files for hardcoded secrets.

Run this before committing to ensure no secrets are leaked.
Scans Python, TypeScript, JavaScript, JSON, YAML, TOML, shell, and env files.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|api_secret|token|secret|password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret"),
    (r'(?i)(postgresql|mysql|mongodb|redis)://[^:]+:[^@]+@', "Database credentials in URL"),
    (r'(?i)jwt[_-]?secret\s*[=:]\s*["\'][^"\']{8,}["\']', "JWT secret"),
    (r'(?i)(private[_-]?key|privatekey)\s*[=:]\s*["\'][^"\']+["\']', "Private key"),
    (r'(?i)(oauth|bearer|auth)\s*token\s*[=:]\s*["\'][^"\']{8,}["\']', "OAuth token"),
    (r'(?i)(aws_access_key|aws_secret|aws_session_token)\s*[=:]\s*["\'][^"\']+["\']', "AWS credential"),
    (r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']', "Potential base64 secret"),
    (r'(?i)bot[_-]?token\s*[=:]\s*["\'][^"\']{10,}["\']', "Bot token"),
    (r'(?i)(access[_-]?token|refresh[_-]?token)\s*[=:]\s*["\']eyJ[^"\']+["\']', "JWT token"),
    (r'(?i)service[_-]?role[_-]?key\s*[=:]\s*["\']eyJ[^"\']+["\']', "Service role key"),
]

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
    "*.md",
    "*.txt",
    "*.bak",
    "*.security.bak",
    "package-lock.json",
    "pnpm-lock.yaml",
}

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

SCAN_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".json", ".yaml", ".yml", ".toml", ".sh", ".bash",
    ".env", ".cfg", ".ini", ".xml", ".vue", ".svelte",
}


def should_skip(path: Path) -> bool:
    for skip_dir in SKIP_DIRS:
        if skip_dir in str(path):
            return True
    for skip_file in SKIP_FILES:
        if path.name == skip_file or path.match(skip_file):
            return True
    return False


def scan_file(path: Path) -> list[tuple[int, str, str]]:
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

    for file_path in PROJECT_ROOT.rglob("*"):
        if not file_path.is_file():
            continue
        if should_skip(file_path):
            continue
        if file_path.suffix not in SCAN_EXTENSIONS:
            continue

        file_findings = scan_file(file_path)
        if file_findings:
            findings.append((file_path, file_findings))

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
