"""Guards for the ``environment_secrets`` check in ``tools/check_security.py``.

The check reports secret-named variables (``*_KEY``, ``*_SECRET``, ``*_TOKEN``,
``*_PASSWORD``) that are set in the parent process environment. Its contract,
pinned here:

* only variable **names** and **bucketed value lengths** are reported — the
  values themselves must never appear in a finding, so the scan output stays
  safe to publish in CI logs;
* variables whose names do not end in a secret suffix are ignored;
* it is wired into ``run_all_checks`` as a MEDIUM-severity finding;
* the message names ``setx <NAME> ""`` as the Windows removal command.

The ambient machine environment is not trusted by these tests: the fixture
below deletes every secret-named variable from ``os.environ`` first (a live
API key found on 2026-10-10 is exactly the finding this check operationalises),
so assertions cannot be poisoned by the developer shell.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

# tools/ is not a package; load the scanner by path, as the sibling test does.
TOOLS_DIR = Path(__file__).resolve().parents[1]


def _load_check_security():
    spec = importlib.util.spec_from_file_location(
        "check_security", TOOLS_DIR / "check_security.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_security"] = module
    spec.loader.exec_module(module)
    return module


check_security = _load_check_security()


@pytest.fixture
def clean_secret_env(monkeypatch):
    """os.environ stripped of every secret-named variable.

    ``monkeypatch`` restores the original environment when the test ends, so a
    live developer key is hidden for the test only, never modified.
    """
    for name in [
        n for n in os.environ if n.upper().endswith(check_security.SECRET_ENV_SUFFIXES)
    ]:
        monkeypatch.delenv(name, raising=False)
    return os.environ


def _environment_findings(result):
    return [f for f in result.findings if f.check == "environment_secrets"]


def test_secret_named_vars_reported_by_name_and_length_bucket_only(
    clean_secret_env, monkeypatch
):
    monkeypatch.setenv("HYDROMA_TEST_API_KEY", "K7dQ-mZ2-pL9x")  # 13 chars -> 9-16
    monkeypatch.setenv("HYDROMA_TEST_TOKEN", "t0k")              # 3 chars  -> 1-8
    monkeypatch.setenv("HYDROMA_TEST_PASSWORD", "p" * 70)       # 70 chars -> 65+
    monkeypatch.setenv("hydroma_lowercase_secret", "lowervalue")  # 9 chars -> 9-16

    result = check_security.ScanResult(timestamp="t", repo=".")
    check_security.check_environment_secrets(Path("."), result)

    findings = _environment_findings(result)
    assert len(findings) == 1, "one aggregated MEDIUM finding is expected"
    finding = findings[0]
    assert finding.severity == "MEDIUM"

    # every secret-named variable is reported by name (case-insensitive
    # match, and case-insensitive assertion: Windows upper-cases os.environ
    # keys, so a lower-case name arrives here as e.g. HYDROMA_LOWERCASE_SECRET)
    for name in (
        "HYDROMA_TEST_API_KEY",
        "HYDROMA_TEST_TOKEN",
        "HYDROMA_TEST_PASSWORD",
        "hydroma_lowercase_secret",
    ):
        assert name.upper() in finding.message.upper()

    # lengths are bucketed
    assert "9-16" in finding.message   # API_KEY (13) and lowercase secret (9)
    assert "1-8" in finding.message    # TOKEN (3)
    assert "65+" in finding.message    # PASSWORD (70)

    # values are NEVER reported — not in the message, not in the context,
    # not anywhere in the serialised finding
    serialised = json.dumps(finding.to_dict())
    for value in ("K7dQ-mZ2-pL9x", "t0k", "p" * 70, "lowervalue"):
        assert value not in finding.message
        assert value not in finding.context
        assert value not in serialised

    # the Windows removal command is named
    assert 'setx <NAME> ""' in finding.message


def test_non_secret_vars_are_ignored(clean_secret_env, monkeypatch):
    monkeypatch.setenv("HYDROMA_REGION", "eu-west")
    monkeypatch.setenv("HYDROMA_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("HYDROMA_KEYBOARD_LAYOUT", "us")   # ends in _LAYOUT
    monkeypatch.setenv("KEYSTONE_VALUE", "x")             # starts with KEY

    result = check_security.ScanResult(timestamp="t", repo=".")
    check_security.check_environment_secrets(Path("."), result)

    assert _environment_findings(result) == []


def test_no_finding_when_environment_has_no_secret_named_vars(clean_secret_env):
    result = check_security.ScanResult(timestamp="t", repo=".")
    check_security.check_environment_secrets(Path("."), result)
    assert _environment_findings(result) == []


def test_run_all_checks_wires_in_environment_secrets(tmp_path, clean_secret_env, monkeypatch):
    monkeypatch.setenv("HYDROMA_TEST_KEY", "wire-in-check")
    result = check_security.run_all_checks(tmp_path)
    findings = _environment_findings(result)
    assert len(findings) == 1
    assert findings[0].severity == "MEDIUM"
    assert "HYDROMA_TEST_KEY" in findings[0].message
    assert "wire-in-check" not in json.dumps(findings[0].to_dict())


def test_run_all_checks_quiet_when_environment_is_clean(tmp_path, clean_secret_env):
    result = check_security.run_all_checks(tmp_path)
    assert _environment_findings(result) == []


@pytest.mark.parametrize(
    ("length", "expected"),
    [
        (0, "0 (empty)"),
        (1, "1-8"),
        (8, "1-8"),
        (9, "9-16"),
        (16, "9-16"),
        (17, "17-32"),
        (32, "17-32"),
        (33, "33-64"),
        (64, "33-64"),
        (65, "65+"),
        (500, "65+"),
    ],
)
def test_length_bucket_boundaries(length, expected):
    assert check_security._length_bucket(length) == expected
