"""Bot configuration — loaded from environment variables (Phase 1/2).

Everything the bot needs is read here so handlers stay pure and testable.
"""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BotConfig:
    """Immutable runtime configuration for the Eco Nojin bot."""

    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://os.environ.get('HOST', 'localhost'):11434")
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    )
    ollama_timeout: float = field(
        default_factory=lambda: float(os.getenv("OLLAMA_TIMEOUT", "5.0"))
    )
    default_language: str = field(
        default_factory=lambda: os.getenv("BOT_DEFAULT_LANGUAGE", "fa")
    )

    @property
    def has_token(self) -> bool:
        return bool(self.bot_token.strip())

    def get_env(self, name: str, default: str = "") -> str:
        """Read any other environment variable (used for platform tokens)."""
        return os.getenv(name, default)

    @classmethod
    def from_env(cls) -> "BotConfig":
        return cls()
