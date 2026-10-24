"""
EcoCoin distribution engine (Phase 8) — 70/15/10/5 split.

Every carbon/eco payout is split transparently:
- 70%  producer (farmer / project owner)
- 15%  platform & operations (community fund)
- 10%  ecosystem restoration fund
-  5%  governance / reserve

``distribute`` returns the exact split — the caller decides where each
share is credited (wallet earn calls), so no fake accounting here.

Configuration
-------------
The split percentages and burn rate are *data owned by the product owner*.
They are loaded from ``<config-dir>/distribution_constants.yaml`` where the
config directory is, in priority order:

1. the ``ECO_CONFIG_DIR`` environment variable, when set;
2. ``<repo root>/config`` (the historical default).

The file is deliberately NOT hard-coded here: inventing the 70/15/10/5
constants would be fabricating data. When the file (or one of its keys) is
missing, importing this module still succeeds but every consumer call raises
the typed :class:`ConfigurationMissing`, whose message names the file, the
environment variable and the decision the product owner must supply.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

#: Basename of the distribution constants file inside the config directory.
CONFIG_FILENAME = "distribution_constants.yaml"

#: Environment variable that overrides the config directory location.
CONFIG_ENV_VAR = "ECO_CONFIG_DIR"

#: Keys the constants file must define.
REQUIRED_KEYS = ("DISTRIBUTION_PCT", "DISTRIBUTION_BPS", "BURN_RATE_BPS")

#: Repository default: <repo root>/config (the historical location).
DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _config_dir() -> Path:
    """Resolve the config directory (env var override, then repo default)."""
    override = os.environ.get(CONFIG_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser()
    return DEFAULT_CONFIG_DIR


#: Resolved path of the constants file. Importing this name never touches the
#: filesystem, so importers (e.g. ``services.wallet.retention``) keep working.
CONFIG_PATH = _config_dir() / CONFIG_FILENAME


class ConfigurationMissing(RuntimeError):
    """The EcoCoin distribution configuration file is absent or incomplete.

    The 70/15/10/5 split and the burn rate are product decisions; this module
    refuses to invent them.
    """


def _missing_message(detail: str) -> str:
    return (
        f"EcoCoin distribution configuration is missing: {detail} "
        f"Expected file: {CONFIG_PATH} "
        f"(set the {CONFIG_ENV_VAR} environment variable to the directory that "
        "contains distribution_constants.yaml). "
        "The 70/15/10/5 split (producer / platform / ecosystem restoration / "
        "governance) and the burn rate must be supplied by the product owner; "
        "they are deliberately not hard-coded because inventing them would be "
        "fabricating data."
    )


def _load_config() -> dict[str, Any]:
    """Load and validate the constants file, or raise ConfigurationMissing."""
    if not CONFIG_PATH.is_file():
        raise ConfigurationMissing(_missing_message(f"'{CONFIG_PATH}' does not exist"))
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        detail = f"'{CONFIG_PATH}' is not valid YAML: {exc}"
        raise ConfigurationMissing(_missing_message(detail)) from exc
    if not isinstance(data, dict):
        raise ConfigurationMissing(_missing_message(f"'{CONFIG_PATH}' is not a YAML mapping"))
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ConfigurationMissing(
            _missing_message(f"'{CONFIG_PATH}' is missing required keys: {', '.join(missing)}")
        )
    return data


_config_cache: dict[str, Any] | None = None


def _config() -> dict[str, Any]:
    """Return the validated constants (loaded lazily, once)."""
    global _config_cache
    if _config_cache is None:
        _config_cache = _load_config()
    return _config_cache


def reset_config_cache() -> None:
    """Drop the cached constants so a config edit takes effect in-process."""
    global _config_cache
    _config_cache = None


def __getattr__(name: str) -> Any:
    """Expose SHARES / SHARES_BPS / BURN_RATE_BPS lazily (PEP 562).

    The names keep their historical public API, but reading them without a
    configuration file raises :class:`ConfigurationMissing` instead of
    ``FileNotFoundError`` at import time.
    """
    if name == "SHARES":
        return _config()["DISTRIBUTION_PCT"]
    if name == "SHARES_BPS":
        return _config()["DISTRIBUTION_BPS"]
    if name == "BURN_RATE_BPS":
        return _config()["BURN_RATE_BPS"]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def distribute(total: float) -> dict[str, Any]:
    """Split ``total`` ECO by the 70/15/10/5 rule (sum == total, exact)."""
    if total <= 0:
        raise ValueError("total must be positive")
    shares = _config()["DISTRIBUTION_PCT"]
    parts = {name: round(total * share, 6) for name, share in shares.items()}
    # fix rounding drift so the parts sum EXACTLY to total
    drift = round(total - sum(parts.values()), 6)
    parts["governance"] = round(parts["governance"] + drift, 6)
    return {
        "total": round(total, 6),
        "shares": shares,
        "parts": parts,
        "sum": round(sum(parts.values()), 6),
        "rule": "70/15/10/5",
    }


def distribute_bps(total: int) -> dict[str, int]:
    """Split ``total`` ECO (in base units) by basis points (exact integer math)."""
    if total <= 0:
        raise ValueError("total must be positive")
    shares_bps = _config()["DISTRIBUTION_BPS"]
    parts = {name: (total * bps) // 10000 for name, bps in shares_bps.items()}
    # fix rounding drift
    drift = total - sum(parts.values())
    parts["governance"] += drift
    return parts


def apply_burn(total: int, burn_rate_bps: int | None = None) -> tuple[int, int]:
    """Apply burn rate and return (burned_amount, net_amount)."""
    if burn_rate_bps is None:
        burn_rate_bps = _config()["BURN_RATE_BPS"]
    burned = (total * burn_rate_bps) // 10000
    net = total - burned
    return burned, net
