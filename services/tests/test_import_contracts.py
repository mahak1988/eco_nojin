"""Import contracts for the five repaired service modules.

Each contract imports its module in a FRESH subprocess (PYTHONPATH + SECRET_KEY
set, exactly like the scan that found these defects) and asserts the module
either imports cleanly, or fails with a typed, documented error whose message
names the cause. In-process tests then pin the behaviour behind the guard.

The five contracts:

1. ``services.auth.main`` — must import without ``passlib`` (passlib 1.7.4 is
   broken on Python 3.12); hashing goes through ``services.auth.compat`` with
   legacy PBKDF2-HMAC-SHA256 verification compatibility.
2. ``services.carbon.rothc_service`` — must import even though the installed
   ``pyRothC`` is an empty namespace package; calling the service raises the
   typed ``RothCServiceUnavailable`` naming the pyRothC contract decision.
3. ``services.ecowallet.distribution`` — must import even though
   ``config/distribution_constants.yaml`` is absent; calls raise the typed
   ``ConfigurationMissing`` naming the file, the env var and the product-owner
   decision; the ``services.blockchain.service`` import chain must survive.
4. ``services.telegram_bot.main`` / ``handlers`` — must either import cleanly
   (when the optional ``python-telegram-bot`` extra is installed) or fail with
   the typed ``TelegramDependencyMissing`` whose message names the dependency
   and the install command.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import importlib.util
import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable

#: module -> import contract. ``typed_error`` = substrings that must appear in
#: the traceback when the module cannot import cleanly.
IMPORT_CONTRACTS: dict[str, dict[str, Any]] = {
    "services.auth.main": {},
    "services.carbon.rothc_service": {},
    "services.ecowallet.distribution": {},
    "services.telegram_bot.handlers": {
        "typed_error": ("TelegramDependencyMissing", "python-telegram-bot"),
    },
    "services.telegram_bot.main": {
        "typed_error": ("TelegramDependencyMissing", "python-telegram-bot"),
    },
}


def run_import(
    module: str,
    extra_env: dict[str, str] | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Import ``module`` in a fresh subprocess with the documented env."""
    env = _child_env(extra_env)
    code = f"import importlib; importlib.import_module({module!r})"
    return subprocess.run(
        [PYTHON, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


def run_python(
    code: str,
    extra_env: dict[str, str] | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Run arbitrary python in a fresh subprocess with the documented env."""
    env = _child_env(extra_env)
    return subprocess.run(
        [PYTHON, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


def _child_env(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    """Environment mirroring the documented run contract (PYTHONPATH+SECRET_KEY)."""
    env = dict(os.environ)
    parts = [str(REPO_ROOT)]
    for existing in env.get("PYTHONPATH", "").split(os.pathsep):
        if existing and existing not in parts:
            parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    if not env.get("SECRET_KEY"):
        env["SECRET_KEY"] = "test-secret-key"
    if extra_env:
        env.update(extra_env)
    return env


def telegram_installed() -> bool:
    """Whether the optional python-telegram-bot extra is present."""
    return importlib.util.find_spec("telegram") is not None


def last_exception_line(stderr: str) -> str:
    lines = [ln for ln in stderr.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ""


# --------------------------------------------------------------------------
# Contract: subprocess import, clean or typed/documented
# --------------------------------------------------------------------------


@pytest.mark.parametrize("module", sorted(IMPORT_CONTRACTS))
def test_import_contract_subprocess(module: str) -> None:
    spec = IMPORT_CONTRACTS[module]
    proc = run_import(module)

    if proc.returncode == 0:
        return  # clean import — the best outcome

    typed_error = spec.get("typed_error")
    assert typed_error, (
        f"{module} does not import and has no documented typed-error contract: "
        f"{last_exception_line(proc.stderr)}"
    )
    stderr = proc.stderr
    for expected in typed_error:
        assert expected in stderr, (
            f"{module} failed with {last_exception_line(stderr)}; expected the "
            f"typed/documented error mentioning {expected!r}"
        )


# --------------------------------------------------------------------------
# Defect 1: services.auth.main — passlib is broken on Python 3.12
# --------------------------------------------------------------------------


def test_auth_main_does_not_import_passlib() -> None:
    """Regression guard: passlib must not be touched at import time.

    passlib 1.7.4 raises SyntaxError on Python 3.12 (mid-file
    ``from __future__ import with_statement`` in passlib/context.py).
    """
    proc = run_python(
        "import importlib, sys; importlib.import_module('services.auth.main'); "
        "print('passlib' in sys.modules or 'passlib.context' in sys.modules)"
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "False"


def test_auth_main_hash_and_verify_roundtrip() -> None:
    from services.auth import main as auth_main

    hashed = auth_main.hash_password("correct-horse-battery-staple")
    assert hashed.startswith("$2b$")  # bcrypt, same format as before the fix
    assert auth_main.verify_password("correct-horse-battery-staple", hashed)
    assert not auth_main.verify_password("wrong-password", hashed)


def test_auth_main_legacy_pbkdf2_hash_compatibility() -> None:
    """Legacy ``pbkdf2:<salt>:<hex>`` hashes must still verify."""
    from services.auth import main as auth_main
    from services.auth.compat import password_hasher

    password = "legacy-farmer-password"
    salt = secrets.token_hex(16)
    legacy_hash = (
        f"pbkdf2:{salt}:"
        + hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    )

    assert auth_main.verify_password(password, legacy_hash)
    assert not auth_main.verify_password("not-the-password", legacy_hash)
    assert password_hasher.needs_migration(legacy_hash)
    assert not password_hasher.needs_migration(auth_main.hash_password(password))


# --------------------------------------------------------------------------
# Defect 2: services.carbon.rothc_service — pyRothC is an empty namespace pkg
# --------------------------------------------------------------------------


def test_rothc_service_import_contract() -> None:
    from services.carbon import rothc_service

    assert hasattr(rothc_service, "RothCService")
    assert isinstance(rothc_service.PYROTHC_AVAILABLE, bool)


def test_rothc_service_raises_typed_error_when_backend_empty() -> None:
    from services.carbon.rothc_service import (
        PYROTHC_AVAILABLE,
        RothCService,
        RothCServiceUnavailable,
    )

    if PYROTHC_AVAILABLE:
        pytest.skip("a real pyRothC backend exposing rothc.run is installed")

    soil_profile = {"initial_soc": 30.0, "climate": {}}
    with pytest.raises(RothCServiceUnavailable) as excinfo:
        asyncio.run(RothCService().forecast_sequestration(soil_profile, "cropland"))

    message = str(excinfo.value)
    for expected in ("pyRothC", "rothc.run", "rothc_real", "product owner"):
        assert expected in message, f"typed error must name {expected!r}: {message}"


# --------------------------------------------------------------------------
# Defect 3: services.ecowallet.distribution — config/ directory is absent
# --------------------------------------------------------------------------


def _distribution_module():
    return importlib.import_module("services.ecowallet.distribution")


@pytest.fixture()
def distribution(reset_config: None) -> Any:
    return _distribution_module()


@pytest.fixture(autouse=True)
def reset_config() -> Any:
    """Drop any cached constants so each test controls the config itself."""
    _distribution_module().reset_config_cache()
    yield
    _distribution_module().reset_config_cache()


def test_distribution_imports_cleanly_and_exposes_config_path() -> None:
    dist = _distribution_module()
    assert isinstance(dist.CONFIG_PATH, Path)
    assert dist.CONFIG_PATH.name == "distribution_constants.yaml"


def test_distribution_missing_config_raises_typed_error(
    distribution: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "absent" / "distribution_constants.yaml"
    monkeypatch.delenv("ECO_CONFIG_DIR", raising=False)
    monkeypatch.setattr(distribution, "CONFIG_PATH", missing)

    with pytest.raises(distribution.ConfigurationMissing) as excinfo:
        distribution.distribute(100.0)

    message = str(excinfo.value)
    assert "distribution_constants.yaml" in message
    assert str(missing) in message
    assert "ECO_CONFIG_DIR" in message
    assert "product owner" in message


def test_distribution_module_attribute_raises_typed_error(
    distribution: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reading SHARES / SHARES_BPS / BURN_RATE_BPS fails typed, not bare."""
    monkeypatch.delenv("ECO_CONFIG_DIR", raising=False)
    monkeypatch.setattr(
        distribution, "CONFIG_PATH", tmp_path / "absent" / "distribution_constants.yaml"
    )

    for name in ("SHARES", "SHARES_BPS", "BURN_RATE_BPS"):
        with pytest.raises(distribution.ConfigurationMissing):
            getattr(distribution, name)


def test_distribution_config_path_resolves_from_eco_config_dir_env(tmp_path: Path) -> None:
    """ECO_CONFIG_DIR overrides the repo-default config directory."""
    proc = run_python(
        "import services.ecowallet.distribution as d; print(d.CONFIG_PATH)",
        extra_env={"ECO_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == str(tmp_path / "distribution_constants.yaml")


def test_distribution_loads_from_resolved_config_file(
    distribution: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ECO_CONFIG_DIR", str(tmp_path))
    config_file = tmp_path / "distribution_constants.yaml"
    config_file.write_text(
        "DISTRIBUTION_PCT:\n"
        "  producer: 0.70\n"
        "  platform: 0.15\n"
        "  ecosystem: 0.10\n"
        "  governance: 0.05\n"
        "DISTRIBUTION_BPS:\n"
        "  producer: 7000\n"
        "  platform: 1500\n"
        "  ecosystem: 1000\n"
        "  governance: 500\n"
        "BURN_RATE_BPS: 250\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(distribution, "CONFIG_PATH", config_file)

    split = distribution.distribute(100.0)
    assert split["parts"] == {
        "producer": 70.0,
        "platform": 15.0,
        "ecosystem": 10.0,
        "governance": 5.0,
    }
    assert split["sum"] == 100.0  # drift fix keeps the split exact
    assert distribution.distribute_bps(10_000) == {
        "producer": 7000,
        "platform": 1500,
        "ecosystem": 1000,
        "governance": 500,
    }
    assert distribution.apply_burn(10_000) == (250, 9750)
    assert distribution.apply_burn(10_000, burn_rate_bps=100) == (100, 9900)


def test_blockchain_service_import_chain_survives_missing_config() -> None:
    """blockchain.service imports distribution lazily inside a method."""
    proc = run_import("services.blockchain.service")
    assert proc.returncode == 0, proc.stderr


# --------------------------------------------------------------------------
# Defect 4: services.telegram_bot — optional python-telegram-bot extra
# --------------------------------------------------------------------------


def test_telegram_handlers_import_when_installed() -> None:
    """Handler surface is importable only when the optional extra is present."""
    if not telegram_installed():
        pytest.skip(
            "python-telegram-bot is not installed (pyproject extra: "
            "hydroma[telegram]) and this machine has no network access to "
            "PyPI — install it to run this test"
        )

    handlers = importlib.import_module("services.telegram_bot.handlers")
    for name in (
        "start_command",
        "help_command",
        "health_command",
        "stats_command",
        "landscapes_command",
        "analyze_command",
        "error_handler",
        "TelegramDependencyMissing",
    ):
        assert hasattr(handlers, name), name


def test_telegram_dependency_error_when_absent() -> None:
    """Without the extra, the failure is typed and actionable, not bare."""
    if telegram_installed():
        pytest.skip("python-telegram-bot is installed — degradation path inactive")

    with pytest.raises(ImportError) as excinfo:  # TelegramDependencyMissing is an ImportError
        importlib.import_module("services.telegram_bot.handlers")

    message = str(excinfo.value)
    assert "python-telegram-bot" in message
    assert "hydroma[telegram]" in message or "pip install python-telegram-bot" in message
