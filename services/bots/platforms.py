"""Platform registry — one bot core, many platforms (Phase 2).

Telegram and Eitaa run through the same aiogram dispatcher (Eitaa's Bot API
is Telegram-compatible; only the API base changes). Bale uses its own
library (python-bale-bot) and Rubika's bot protocol differs enough that it
needs a live integration study — both are registered here so configuration
and diagnostics stay uniform.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import BotConfig

EITAA_API_BASE = "https://eitaayar.ir/api"


@dataclass(frozen=True)
class PlatformSpec:
    key: str
    label: str  # Persian display name
    token_env: str
    api_base: str | None  # None => official Telegram API / platform default
    enabled_env: str | None  # None => always considered (telegram)
    kind: str  # "aiogram" | "bale" | "rubika"
    verified: bool  # True only when the integration is confirmed working


PLATFORM_SPECS: dict[str, PlatformSpec] = {
    "telegram": PlatformSpec(
        key="telegram", label="تلگرام", token_env="BOT_TOKEN",
        api_base=None, enabled_env=None, kind="aiogram", verified=True,
    ),
    "eitaa": PlatformSpec(
        key="eitaa", label="ایتا", token_env="EITAA_TOKEN",
        api_base=EITAA_API_BASE, enabled_env="EITAA_ENABLED",
        kind="aiogram", verified=False,  # needs a live token check (getMe)
    ),
    "bale": PlatformSpec(
        key="bale", label="بله", token_env="BALE_TOKEN",
        api_base=None, enabled_env="BALE_ENABLED",
        kind="bale", verified=False,
    ),
    "rubika": PlatformSpec(
        key="rubika", label="روبیکا", token_env="RUBIKA_TOKEN",
        api_base=None, enabled_env="RUBIKA_ENABLED",
        kind="rubika", verified=False,
    ),
}


def token_for(spec: PlatformSpec, config: BotConfig) -> str:
    """Resolve a platform token from the environment."""
    return config.get_env(spec.token_env, "")


def enabled_platforms(config: BotConfig) -> list[PlatformSpec]:
    """Platforms that should run: telegram always, others when enabled+token."""
    result: list[PlatformSpec] = []
    for spec in PLATFORM_SPECS.values():
        if spec.key == "telegram":
            if config.has_token:
                result.append(spec)
            continue
        # non-telegram platforms require the explicit enable flag AND a token
        if spec.enabled_env is None:
            continue
        if config.get_env(spec.enabled_env, "").lower() not in ("1", "true", "yes"):
            continue
        if token_for(spec, config).strip():
            result.append(spec)
    return result
